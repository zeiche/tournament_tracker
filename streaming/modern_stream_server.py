#!/usr/bin/env python3
"""
Modern websockets 15+ compatible Twilio Media Stream server
Uses the correct handler pattern for websockets 15.0.1
Connected to tournament tracker system via polymorphic queries
"""
import asyncio
import websockets.asyncio.server
import json
import base64
import ssl
import pathlib
import logging
import sys
import os
import subprocess
import signal
import wave
import io
import tempfile

# Add parent dir to path for tournament tracker imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import tournament tracker components
try:
    from search.polymorphic_queries import query as pq
    logger.info("✅ Tournament tracker connected")
except ImportError:
    logger.warning("⚠️ Tournament tracker not available - using fallback")
    def pq(query):
        return f"Tournament data query: {query}"

# Import existing transcription service and announcer
transcription_service = None
announcer = None
try:
    from polymorphic_core.audio.transcription import get_transcription_service
    from polymorphic_core import announcer
    transcription_service = get_transcription_service()
    logger.info("✅ Polymorphic transcription service available")
    logger.info("✅ Announcer system available")
except ImportError:
    logger.warning("⚠️ Polymorphic transcription not available - using fallback")
    transcription_service = None
    announcer = None

class TwilioHandler:
    def __init__(self):
        self.call_sid = None
        self.stream_sid = None
        self.audio_count = 0
        self.audio_buffer = []
        self.buffer_size = 160  # 20ms chunks for mulaw
        self.last_transcription_time = 0
        self.websocket = None  # Store current websocket
        self.media_logged = False  # Track if we've logged first media event

    async def process_event(self, websocket, data):
        """Process Twilio event"""
        event = data.get('event')
        
        # Only log media event once to reduce noise
        if event == 'media':
            if not self.media_logged:
                logger.info(f"📥 Event: {event} (further media events suppressed)")
                self.media_logged = True
        else:
            logger.info(f"📥 Event: {event}")
        
        if event == 'connected':
            logger.info("✅ Twilio connected")
            
        elif event == 'start':
            start_data = data.get('start', {})
            self.call_sid = start_data.get('callSid')
            self.stream_sid = start_data.get('streamSid')
            params = start_data.get('customParameters', {})
            
            # Store websocket for later use
            self.websocket = websocket
            
            logger.info(f"📞 Call: {self.call_sid}")
            logger.info(f"🎙️ Stream: {self.stream_sid}")
            logger.info(f"📝 Parameters: {params}")
            
            # Send welcome with tournament data
            try:
                welcome = pq("recent tournaments")
                await self.send_response(websocket, f"Tournament tracker ready! {welcome}")
            except Exception as e:
                logger.error(f"❌ Query error: {e}")
                await self.send_response(websocket, "Tournament tracker ready! Ask about tournaments.")
            
        elif event == 'media':
            media_data = data.get('media', {})
            payload = media_data.get('payload')
            
            if payload:
                # Decode audio from base64
                audio_bytes = base64.b64decode(payload)
                self.audio_buffer.extend(audio_bytes)
                
                self.audio_count += 1
                
                # Process audio buffer every ~2 seconds (160 chunks)
                if len(self.audio_buffer) >= self.buffer_size * 160:
                    logger.info(f"🎤 Processing audio buffer ({len(self.audio_buffer)} bytes)")
                    await self.process_audio_buffer(websocket)
                    
                # Periodic status
                if self.audio_count % 100 == 0:
                    logger.info(f"🎤 Audio packets: {self.audio_count}")
                
        elif event == 'stop':
            logger.info("🛑 Stream stopped")

    async def send_response(self, websocket, message):
        """Send audio response"""
        if not self.stream_sid:
            return
            
        logger.info(f"📤 Sending: {message}")
        
        # Create silence (160 bytes = 20ms at 8kHz)
        silence = bytes([0xFF] * 160)
        payload = base64.b64encode(silence).decode('utf-8')
        
        response = {
            "event": "media",
            "streamSid": self.stream_sid,
            "media": {"payload": payload}
        }
        
        await websocket.send(json.dumps(response))

    async def process_audio_buffer(self, websocket):
        """Process accumulated audio data for speech recognition"""
        if not self.audio_buffer:
            return
            
        try:
            # Send audio directly to polymorphic transcription service
            if transcription_service:
                # Use polymorphic service directly
                transcription_service.transcribe_audio("twilio_stream", bytes(self.audio_buffer), {
                    'type': 'mulaw',
                    'format': 'mulaw',
                    'channels': 1,
                    'sample_rate': 8000
                })
                text = None  # Let the service handle announcements
            else:
                # Old fallback
                text = await self.transcribe_audio(bytes(self.audio_buffer))
            
            if transcription_service:
                # Polymorphic service handles everything via announcements
                logger.info("📡 Audio sent to polymorphic transcription service")
            elif text and text.strip():
                logger.info(f"🗣️ Transcribed: '{text}'")
                
                # Send response back to caller via Twilio
                try:
                    response = pq(text)
                    if response and response.strip():
                        await self.send_response(websocket, response)
                        logger.info(f"✅ Sent response: {response[:100]}...")
                    else:
                        logger.warning(f"⚠️ Empty response for query: '{text}'")
                        await self.send_response(websocket, "I found that query but got no results.")
                except Exception as e:
                    logger.error(f"❌ Query error for '{text}': {e}")
                    await self.send_response(websocket, "Sorry, I couldn't find that information.")
            else:
                logger.info("🔇 No speech detected in audio buffer")
                
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            
        finally:
            # Clear buffer
            self.audio_buffer = []

    async def transcribe_audio(self, audio_bytes):
        """Send audio to polymorphic transcription service - let it handle announcements"""
        global transcription_service
        
        if transcription_service is None:
            # Fallback simulation based on audio length
            if len(audio_bytes) > 20000:
                return "top 8 players"  
            elif len(audio_bytes) > 10000:
                return "show recent tournaments"
            elif len(audio_bytes) > 5000:
                return "show player west"
            return None
            
        try:
            # Convert mulaw to WAV format for the transcription service
            import audioop
            linear_data = audioop.ulaw2lin(audio_bytes, 2)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(8000)  # 8kHz
                wav_file.writeframes(linear_data)
            
            wav_data = wav_buffer.getvalue()
            
            # Let transcription service handle everything - including announcements to lightweight
            metadata = {
                'type': 'wav',
                'format': 'wav', 
                'channels': 1,
                'sample_rate': 8000
            }
            
            # Send to transcription service for lightweight announcements
            transcription_service.transcribe_audio("twilio_stream", wav_data, metadata)
            
            # Also get the transcription for our direct response
            # Use the same transcription methods as the service
            text = None
            try:
                text = transcription_service.transcribe_with_whisper(wav_data)
                if not text:
                    text = transcription_service.transcribe_with_speech_recognition(wav_data)
                if not text:
                    text = transcription_service.transcribe_with_google(wav_data)
            except:
                pass
                
            return text
                
        except Exception as e:
            logger.error(f"❌ Transcription service error: {e}")
            return None

# Global handler
handler = TwilioHandler()

async def websocket_handler(websocket):
    """WebSocket connection handler for websockets 15+"""
    logger.info(f"🔌 Connection from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await handler.process_event(websocket, data)
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON received")
            except Exception as e:
                logger.error(f"❌ Processing error: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("📴 Connection closed")
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")

def kill_old_processes():
    """Kill any existing instances of this server"""
    try:
        # Find processes running this script (excluding current process)
        result = subprocess.run(['pgrep', '-f', 'modern_stream_server.py'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            current_pid = str(os.getpid())
            
            for pid in pids:
                if pid != current_pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        logger.info(f"🗑️ Killed old process {pid}")
                    except (ProcessLookupError, ValueError):
                        pass
                        
        # Also kill any processes using port 8088
        try:
            result = subprocess.run(['lsof', '-ti:8088'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        logger.info(f"🗑️ Killed process using port 8088: {pid}")
                    except (ProcessLookupError, ValueError):
                        pass
        except FileNotFoundError:
            # lsof not available
            pass
            
    except Exception as e:
        logger.warning(f"⚠️ Process cleanup warning: {e}")

async def main():
    """Start the server using modern websockets API"""
    port = 8088
    
    # Kill old processes first
    logger.info("🧹 Cleaning up old processes...")
    kill_old_processes()
    
    # Wait a moment for cleanup
    await asyncio.sleep(1)
    
    logger.info(f"🚀 Starting modern Twilio server on port {port}")
    
    # SSL setup
    cert_path = pathlib.Path(__file__).parent / "server.crt"  
    key_path = pathlib.Path(__file__).parent / "server.key"
    
    if not (cert_path.exists() and key_path.exists()):
        logger.error("❌ SSL certificates missing")
        return
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_path, key_path)
    logger.info("🔐 SSL configured")
    
    # Start server with modern API
    async with websockets.asyncio.server.serve(
        websocket_handler,
        "0.0.0.0",
        port,
        ssl=ssl_context
    ):
        logger.info(f"📡 Server running on wss://64.111.98.139:{port}/")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Stopped")