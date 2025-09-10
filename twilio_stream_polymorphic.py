#!/usr/bin/env python3
"""
Twilio Stream handler with polymorphic transcription integration.
Connects Twilio media streams to the polymorphic transcription system.
"""

import asyncio
import websockets
import json
import base64
import struct
import ssl
import pathlib
from datetime import datetime
from typing import Optional, Dict, Any
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import polymorphic components
try:
    from polymorphic_core import announcer, discover_capability
except ImportError:
    class DummyAnnouncer:
        def announce(self, *args, **kwargs):
            pass
    announcer = DummyAnnouncer()
    def discover_capability(name):
        return None

try:
    from polymorphic_queries import query as pq
except ImportError:
    def pq(query):
        return f"Tournament data query: {query}"

# Import the transcription bridge
try:
    from twilio_transcription_bridge import get_twilio_bridge
    twilio_bridge = get_twilio_bridge()
except ImportError:
    print("⚠️ Twilio transcription bridge not available")
    twilio_bridge = None

# Import the audio mixer
try:
    from experimental.audio.bonjour_audio_mixer import get_mixer
    audio_mixer = get_mixer()
except ImportError:
    print("⚠️ Bonjour audio mixer not available")
    audio_mixer = None

class TwilioStreamPolymorphic:
    """Handles Twilio streams with polymorphic transcription integration."""
    
    def __init__(self):
        self.call_sid = None
        self.stream_sid = None
        self.custom_params = {}
        self.audio_buffer = bytearray()
        self.transcription_service = None
        self.tts_service = None
        
        # Discover polymorphic services
        self.transcription_service = discover_capability('transcription')
        self.tts_service = discover_capability('tts')
        
        # Listen for transcription results
        self.transcription_results = {}
        
        # Announce ourselves
        announcer.announce(
            "Twilio Stream Polymorphic",
            [
                "I connect Twilio streams to polymorphic services",
                "I forward audio to polymorphic transcription",
                "I handle TTS responses via audio mixer",
                "I integrate with the Bonjour ecosystem",
                "I use AUDIO_AVAILABLE announcements",
                "I listen for TRANSCRIPTION_COMPLETE",
                "I listen for AUDIO_MIXED from the mixer"
            ]
        )
        
        # Register for transcription results
        self.register_for_announcements()
    
    def register_for_announcements(self):
        """Register to receive transcription and audio announcements"""
        # In a full implementation, this would register with the announcement system
        # For now, we'll poll or check directly
        announcer.announce(
            "TwilioStreamPolymorphic",
            [
                "Registered for TRANSCRIPTION_COMPLETE announcements",
                "Registered for AUDIO_MIXED announcements from mixer"
            ]
        )
    
    async def handle_websocket(self, websocket, path):
        """Handle incoming WebSocket connection from Twilio."""
        print(f"🔌 WebSocket connected from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print("📴 WebSocket connection closed")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    async def process_message(self, websocket, message: str):
        """Process incoming WebSocket messages from Twilio."""
        try:
            data = json.loads(message)
            event = data.get('event')
            
            if event == 'connected':
                print("✅ Twilio connected")
                print(f"Protocol: {data.get('protocol')}")
                
            elif event == 'start':
                # Stream metadata
                start_data = data.get('start', {})
                self.call_sid = start_data.get('callSid')
                self.stream_sid = start_data.get('streamSid')
                self.custom_params = start_data.get('customParameters', {})
                
                print(f"📞 Call started: {self.call_sid}")
                print(f"🎙️ Stream: {self.stream_sid}")
                print(f"📝 Custom params: {self.custom_params}")
                
                # Register with transcription bridge
                if twilio_bridge:
                    twilio_bridge.register_twilio_handler(self.call_sid, websocket, self)
                    print(f"🌉 Registered with transcription bridge: {self.call_sid}")
                
                # Connect audio mixer for music playback
                if audio_mixer:
                    print("🎚️ Connecting audio mixer with music playback")
                    audio_mixer.start_continuous_music()
                    
                    # Stream mixer output directly to Twilio
                    asyncio.create_task(self.stream_mixer_to_twilio(websocket))
                    print("🎵 Background music streaming enabled")
                else:
                    print("⚠️ Audio mixer not available")
                
                # Send initial greeting
                await self.send_tts_response(
                    websocket,
                    "Welcome to Try Hard Tournament Tracker! Ask me about tournaments, players, or rankings."
                )
                
            elif event == 'media':
                # Incoming audio data
                media = data.get('media', {})
                audio_payload = media.get('payload')
                
                if audio_payload:
                    # Decode base64 audio
                    audio_bytes = base64.b64decode(audio_payload)
                    self.audio_buffer.extend(audio_bytes)
                    
                    # Process audio every ~2 seconds worth of data
                    if len(self.audio_buffer) >= 16000:  # 2 sec at 8kHz mulaw
                        await self.process_audio_buffer(websocket)
                
            elif event == 'stop':
                print(f"🛑 Stream stopped: {self.stream_sid}")
                
                # Stop mixer output stream
                if hasattr(self, 'mixer_task'):
                    self.mixer_task.cancel()
                    print("🎚️ Mixer output task cancelled")
                
                # Unregister from transcription bridge
                if twilio_bridge and self.call_sid:
                    twilio_bridge.unregister_twilio_handler(self.call_sid)
                    print(f"🌉 Unregistered from transcription bridge: {self.call_sid}")
                
            elif event == 'mark':
                # Custom mark event
                mark = data.get('mark', {})
                print(f"📍 Mark received: {mark.get('name')}")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def process_audio_buffer(self, websocket):
        """Process accumulated audio buffer via polymorphic transcription bridge."""
        if len(self.audio_buffer) < 8000:  # Need at least 1 second
            return
        
        # Copy buffer and clear it
        audio_data = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        
        # Send to transcription bridge if available
        if twilio_bridge and self.call_sid:
            try:
                # Create metadata for the audio
                metadata = {
                    'type': 'twilio_stream',
                    'format': 'mulaw',
                    'sample_rate': 8000,
                    'channels': 1,
                    'call_sid': self.call_sid,
                    'stream_sid': self.stream_sid
                }
                
                # Send to transcription bridge (it will handle polymorphic transcription)
                await twilio_bridge.process_twilio_audio(self.call_sid, audio_data, metadata)
                
                print(f"📤 Sent {len(audio_data)} bytes to transcription bridge for {self.call_sid}")
                
            except Exception as e:
                print(f"❌ Error sending to transcription bridge: {e}")
        else:
            print("⚠️ No transcription bridge available")
    
    async def get_transcription_result(self) -> Optional[str]:
        """Check for transcription results (simplified implementation)."""
        # In a real implementation, this would be event-driven via announcements
        # For now, we'll return None and let the transcription service handle it
        return None
    
    async def handle_transcription(self, websocket, text: str):
        """Handle transcription result and generate response."""
        print(f"🎤 Transcribed: {text}")
        
        # Check for hangup keywords
        hangup_keywords = ["goodbye", "bye", "hang up", "end call", "thank you goodbye", "thanks bye"]
        text_lower = text.lower().strip()
        
        if any(keyword in text_lower for keyword in hangup_keywords):
            print("📞 Hangup detected, ending call")
            await self.send_tts_response(websocket, "Goodbye! Thanks for calling Try Hard Tournament Tracker.")
            
            # Send hangup after TTS completes
            await asyncio.sleep(3)  # Wait for TTS to finish
            await self.hangup_call(websocket)
            return
        
        # Query the tournament system
        try:
            response = pq(text)
            if response:
                print(f"🤖 Response: {response[:100]}...")
                await self.send_tts_response(websocket, response)
            else:
                await self.send_tts_response(
                    websocket, 
                    "I didn't understand that. Can you ask about tournaments, players, or rankings?"
                )
        except Exception as e:
            print(f"❌ Error querying system: {e}")
            await self.send_tts_response(
                websocket,
                "Sorry, I had trouble processing that request."
            )
    
    async def send_tts_response(self, websocket, text: str):
        """Convert text to speech via audio mixer and send via Twilio stream."""
        print(f"📤 TTS Response (via mixer): {text[:50]}...")
        
        # Announce text for TTS - the mixer will listen for this
        announcer.announce(
            "TEXT_TO_SPEECH",
            [
                f"TEXT: {text}",
                "VOICE: normal",
                "FORMAT: mulaw_8khz",
                "TARGET: twilio_stream_via_mixer"
            ]
        )
        
        # Send placeholder audio only - NO MIXER to prevent hangup
        await self.send_placeholder_audio(websocket, text)
    
    async def stream_mixer_to_twilio(self, websocket):
        """Simple direct connection: mixer output → Twilio. That's it."""
        try:
            print("🎚️ Direct mixer-to-Twilio connection starting")
            
            while True:
                # Get audio from mixer
                chunk = audio_mixer.get_music_chunk(160)
                if chunk:
                    # Send to Twilio
                    encoded = base64.b64encode(chunk).decode('utf-8')
                    await websocket.send(json.dumps({
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {"payload": encoded}
                    }))
                
                await asyncio.sleep(0.02)  # 20ms
                
        except Exception as e:
            print(f"🎚️ Mixer connection ended: {e}")
    
    async def send_placeholder_audio(self, websocket, text: str):
        """Send placeholder audio (silence) for text response."""
        # Generate silence in mulaw format
        # In production, this would be real TTS audio
        
        # Calculate duration based on text length (rough estimate)
        duration_seconds = max(2, len(text.split()) * 0.3)  # ~300ms per word
        samples = int(8000 * duration_seconds)  # 8kHz sample rate
        
        # Mulaw silence is 0xFF
        silence_audio = bytes([0xFF] * samples)
        
        # Send in 20ms chunks (160 samples at 8kHz)
        chunk_size = 160
        
        for i in range(0, len(silence_audio), chunk_size):
            chunk = silence_audio[i:i+chunk_size]
            
            # Pad last chunk if needed
            if len(chunk) < chunk_size:
                chunk += bytes([0xFF] * (chunk_size - len(chunk)))
            
            # Base64 encode
            encoded_chunk = base64.b64encode(chunk).decode('utf-8')
            
            # Create media message
            media_message = {
                "event": "media",
                "streamSid": self.stream_sid,
                "media": {
                    "payload": encoded_chunk
                }
            }
            
            # Send to Twilio
            await websocket.send(json.dumps(media_message))
            
            # 20ms delay between chunks
            await asyncio.sleep(0.02)
        
        # Send completion mark
        mark_message = {
            "event": "mark",
            "streamSid": self.stream_sid,
            "mark": {
                "name": "tts_complete"
            }
        }
        await websocket.send(json.dumps(mark_message))
        
        print(f"📤 Sent placeholder audio for: {text[:30]}...")
    
    async def stream_mixed_audio_to_twilio(self, websocket, mixer, text: str):
        """Stream mixed audio from mixer directly to Twilio."""
        try:
            print(f"🎚️ Streaming mixed audio to Twilio: {text[:30]}...")
            
            # Get continuous mixed audio chunks from mixer
            duration_seconds = max(2, len(text.split()) * 0.3)  # Estimate duration
            total_chunks = int(duration_seconds / 0.02)  # 20ms chunks
            
            for chunk_num in range(total_chunks):
                # Get audio chunk from mixer (this includes background music + TTS)
                audio_chunk = mixer.get_music_chunk(160)  # 160 bytes = 20ms at 8kHz mulaw
                
                if not audio_chunk:
                    break
                
                # Base64 encode for Twilio
                encoded_chunk = base64.b64encode(audio_chunk).decode('utf-8')
                
                # Create media message
                media_message = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {
                        "payload": encoded_chunk
                    }
                }
                
                # Send to Twilio
                await websocket.send(json.dumps(media_message))
                
                # 20ms delay between chunks for real-time streaming
                await asyncio.sleep(0.02)
            
            # Send completion mark
            mark_message = {
                "event": "mark",
                "streamSid": self.stream_sid,
                "mark": {
                    "name": "mixed_audio_complete"
                }
            }
            await websocket.send(json.dumps(mark_message))
            
            print(f"🎚️ Completed streaming mixed audio for: {text[:30]}...")
            
        except Exception as e:
            print(f"❌ Error streaming mixed audio: {e}")
            # Fallback to placeholder audio
            await self.send_placeholder_audio(websocket, text)
    
    async def stream_mixer_output(self, websocket):
        """Stream the mixer's combined audio output (music + TTS) to Twilio."""
        try:
            print("🎚️ Starting mixer output stream - this is the main audio sink!")
            
            if not audio_mixer:
                print("⚠️ No audio mixer available")
                return
            
            chunk_count = 0
            # Stream the mixer's combined output
            while True:
                try:
                    # Get mixed audio chunk (music + any TTS in queue)
                    audio_chunk = audio_mixer.get_music_chunk(160)  # This should be the MIXED output
                    
                    if not audio_chunk:
                        print(f"🎚️ Mixer output empty after {chunk_count} chunks, restarting...")
                        audio_mixer.start_continuous_music()
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Base64 encode for Twilio
                    encoded_chunk = base64.b64encode(audio_chunk).decode('utf-8')
                    
                    # Create media message
                    media_message = {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {
                            "payload": encoded_chunk
                        }
                    }
                    
                    # Send mixed audio to Twilio
                    try:
                        await websocket.send(json.dumps(media_message))
                        chunk_count += 1
                        
                        # Log progress every 5 seconds (250 chunks)
                        if chunk_count % 250 == 0:
                            print(f"🎚️ Mixed audio streaming: {chunk_count} chunks sent")
                            
                    except Exception as send_error:
                        print(f"❌ Websocket send failed: {send_error}")
                        break
                    
                    # 20ms delay for real-time streaming
                    await asyncio.sleep(0.02)
                    
                except Exception as e:
                    print(f"❌ Error in mixer output processing: {e}")
                    await asyncio.sleep(1)
                    
        except asyncio.CancelledError:
            print("🎚️ Mixer output streaming cancelled (call ended)")
        except Exception as e:
            print(f"❌ Fatal error in mixer output streaming: {e}")
        finally:
            print(f"🎚️ Mixer output stream ended after {chunk_count} chunks")
    
    async def stream_background_music_safely(self, websocket):
        """Safely stream background music without hanging up the call."""
        try:
            print("🎵 Starting SAFE background music stream")
            
            if not audio_mixer or not audio_mixer.background_music:
                print("⚠️ No background music available")
                return
            
            chunk_count = 0
            # Stream music but with error handling to prevent hangups
            while True:
                try:
                    # Get music chunk from mixer
                    audio_chunk = audio_mixer.get_music_chunk(160)  # 20ms chunks
                    
                    if not audio_chunk:
                        print(f"🎵 Music chunk empty after {chunk_count} chunks, restarting...")
                        audio_mixer.start_continuous_music()
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Base64 encode for Twilio
                    encoded_chunk = base64.b64encode(audio_chunk).decode('utf-8')
                    
                    # Create media message
                    media_message = {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {
                            "payload": encoded_chunk
                        }
                    }
                    
                    # Send to Twilio safely
                    try:
                        await websocket.send(json.dumps(media_message))
                        chunk_count += 1
                        
                        # Log progress every 5 seconds (250 chunks)
                        if chunk_count % 250 == 0:
                            print(f"🎵 Music streaming: {chunk_count} chunks sent")
                            
                    except Exception as send_error:
                        print(f"❌ Websocket send failed: {send_error}")
                        break  # Exit music loop if websocket is dead
                    
                    # 20ms delay for real-time streaming
                    await asyncio.sleep(0.02)
                    
                except Exception as e:
                    print(f"❌ Error in music chunk processing: {e}")
                    await asyncio.sleep(1)  # Wait before retrying
                    
        except asyncio.CancelledError:
            print("🎵 Background music streaming cancelled (call ended)")
        except Exception as e:
            print(f"❌ Fatal error in background music streaming: {e}")
        finally:
            print(f"🎵 Background music stream ended after {chunk_count} chunks")
    
    async def stream_background_music_continuously(self, websocket):
        """Continuously stream background music to Twilio - this is the 'play' button!"""
        try:
            print("🎵 Starting continuous background music stream to Twilio")
            
            if not audio_mixer or not audio_mixer.background_music:
                print("⚠️ No background music available")
                return
            
            # Stream background music continuously until call ends
            while True:
                try:
                    # Get music chunk from mixer - this is the actual "play" action
                    audio_chunk = audio_mixer.get_music_chunk(160)  # 20ms chunks
                    
                    if not audio_chunk:
                        print("🎵 Music chunk empty, restarting...")
                        audio_mixer.start_continuous_music()
                        continue
                    
                    # Base64 encode for Twilio
                    encoded_chunk = base64.b64encode(audio_chunk).decode('utf-8')
                    
                    # Create media message
                    media_message = {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {
                            "payload": encoded_chunk
                        }
                    }
                    
                    # Send to Twilio - this is where caller hears the music!
                    await websocket.send(json.dumps(media_message))
                    
                    # 20ms delay for real-time streaming
                    await asyncio.sleep(0.02)
                    
                except Exception as e:
                    print(f"❌ Error in background music streaming: {e}")
                    await asyncio.sleep(1)  # Wait before retrying
                    
        except asyncio.CancelledError:
            print("🎵 Background music streaming cancelled")
        except Exception as e:
            print(f"❌ Fatal error in background music streaming: {e}")
    
    async def hangup_call(self, websocket):
        """Send hangup command to Twilio to end the call."""
        try:
            # Stop the stream first
            stop_message = {
                "event": "stop",
                "streamSid": self.stream_sid
            }
            await websocket.send(json.dumps(stop_message))
            print("📞 Sent stop message to Twilio")
            
            # Close the websocket connection
            await websocket.close()
            print("📞 WebSocket connection closed")
            
            # Stop background music via announcer
            announcer.announce(
                "STOP_CONTINUOUS_MUSIC",
                [
                    "Call ended, stopping background music",
                    "Mixer should stop streaming",
                    "Audio resources released"
                ]
            )
            
        except Exception as e:
            print(f"❌ Error hanging up call: {e}")


async def main():
    """Start the polymorphic Twilio stream server."""
    handler = TwilioStreamPolymorphic()
    
    port = 8088  # Different port from other stream servers
    
    # Create proper handler function that matches websockets.serve expectations
    def websocket_handler(websocket):
        path = getattr(websocket, 'path', '/') if hasattr(websocket, 'path') else '/'
        return handler.handle_websocket(websocket, path)
    
    # SSL context setup
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert_path = pathlib.Path(__file__).parent / "server.crt"
    key_path = pathlib.Path(__file__).parent / "server.key"
    
    if cert_path.exists() and key_path.exists():
        ssl_context.load_cert_chain(cert_path, key_path)
        print(f"🔐 SSL enabled with certificate: {cert_path}")
        ws_url = f"wss://64.111.98.139:{port}/"
    else:
        print("⚠️ SSL certificates not found, running without SSL")
        ssl_context = None
        ws_url = f"ws://64.111.98.139:{port}/"
    
    print(f"🚀 Starting Polymorphic Twilio Stream Server on port {port}")
    print(f"📡 WebSocket URL: {ws_url}")
    print("🔗 Integrated with polymorphic transcription and TTS")
    print("⏳ Waiting for Twilio streams...")
    
    # Start WebSocket server
    async with websockets.serve(
        websocket_handler,
        "0.0.0.0",
        port,
        ssl=ssl_context,
        # Twilio-specific settings
        compression=None,  # Twilio doesn't support compression
        max_size=10 * 1024 * 1024,  # 10MB max message size
        ping_interval=None,  # Twilio handles keepalive
        ping_timeout=None
    ):
        # Keep server running
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down polymorphic stream server")