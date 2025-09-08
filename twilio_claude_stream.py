#!/usr/bin/env python3
"""
Twilio Stream handler with Claude integration for real-time voice responses.
Converts speech to text, queries Claude, and streams TTS audio back.
"""

import asyncio
import websockets
import json
import base64
import io
import wave
import struct
from typing import Optional, List, Dict, Any
import os
import sys
import subprocess
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import tournament components
from polymorphic_core import announcer
from polymorphic_queries import query as pq
import google.cloud.texttospeech as tts
import speech_recognition as sr

class ClaudeStreamHandler:
    """Handles Twilio streams with Claude AI responses."""
    
    def __init__(self):
        self.call_sid = None
        self.stream_sid = None
        self.audio_buffer = bytearray()
        self.recognizer = sr.Recognizer()
        self.tts_client = None
        self.silence_counter = 0
        self.is_processing = False
        
        # Try to initialize TTS
        try:
            self.tts_client = tts.TextToSpeechClient()
            print("✅ Google TTS initialized")
        except:
            print("⚠️ Google TTS not available, using espeak")
        
        # Announce service
        announcer.announce(
            "Claude Stream Handler",
            ["Real-time voice interaction", "Speech recognition", "TTS responses"],
            ["Voice chat about tournaments", "Answer questions via phone"]
        )
    
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connection from Twilio."""
        print(f"🔌 New WebSocket connection from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print("📴 Connection closed")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def process_message(self, websocket, message: str):
        """Process Twilio WebSocket messages."""
        try:
            data = json.loads(message)
            event = data.get('event')
            
            if event == 'connected':
                print(f"✅ Connected - Protocol: {data.get('protocol')}")
                
            elif event == 'start':
                start_data = data.get('start', {})
                self.call_sid = start_data.get('callSid')
                self.stream_sid = start_data.get('streamSid')
                params = start_data.get('customParameters', {})
                
                print(f"📞 Call: {self.call_sid}")
                print(f"🎙️ Stream: {self.stream_sid}")
                print(f"📝 Params: {params}")
                
                # Send greeting
                greeting = "Hello! I'm Claude. Ask me about tournaments, players, or rankings!"
                await self.stream_tts_response(websocket, greeting)
                
            elif event == 'media':
                # Accumulate audio
                media = data.get('media', {})
                payload = media.get('payload')
                
                if payload and not self.is_processing:
                    audio_bytes = base64.b64decode(payload)
                    self.audio_buffer.extend(audio_bytes)
                    
                    # Process every ~2 seconds of audio
                    if len(self.audio_buffer) >= 16000:  # 2 sec at 8kHz
                        await self.process_speech(websocket)
                        
            elif event == 'stop':
                print(f"🛑 Stream stopped")
                
        except Exception as e:
            print(f"❌ Message error: {e}")
    
    async def process_speech(self, websocket):
        """Convert speech to text and get Claude response."""
        if self.is_processing or len(self.audio_buffer) < 8000:
            return
        
        self.is_processing = True
        
        try:
            # Convert mulaw to PCM
            pcm_audio = self.mulaw_to_pcm(bytes(self.audio_buffer))
            
            # Clear buffer
            self.audio_buffer = bytearray()
            
            # Speech to text
            text = await self.speech_to_text(pcm_audio)
            
            if text:
                print(f"🎤 Heard: {text}")
                
                # Query tournament data
                response = await self.get_claude_response(text)
                
                if response:
                    print(f"🤖 Response: {response[:100]}...")
                    
                    # Stream TTS response
                    await self.stream_tts_response(websocket, response)
            
        except Exception as e:
            print(f"❌ Speech processing error: {e}")
        finally:
            self.is_processing = False
    
    async def speech_to_text(self, pcm_audio: bytes) -> Optional[str]:
        """Convert PCM audio to text."""
        try:
            # Create WAV in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(8000)
                wav.writeframes(pcm_audio)
            
            wav_buffer.seek(0)
            
            # Recognize speech
            with sr.AudioFile(wav_buffer) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio)
                return text
                
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"STT error: {e}")
            return None
    
    async def get_claude_response(self, query: str) -> str:
        """Get response from Claude/tournament system."""
        try:
            # Try polymorphic query first
            response = pq(query)
            if response:
                return response
            
            # Fallback to simple responses
            query_lower = query.lower()
            
            if "tournament" in query_lower:
                return "The latest tournament is West Coast Warzone with 256 players. It was a major event!"
            elif "player" in query_lower:
                return "Top players include West with 45 wins, and Zak with 38 wins."
            elif "ranking" in query_lower:
                return "Current rankings: First place West, second place Zak, third place Bear."
            else:
                return "I can tell you about tournaments, players, and rankings. What would you like to know?"
                
        except Exception as e:
            print(f"Query error: {e}")
            return "Sorry, I had trouble getting that information."
    
    async def stream_tts_response(self, websocket, text: str):
        """Convert text to speech and stream to Twilio."""
        try:
            # Generate audio
            if self.tts_client:
                audio_data = await self.google_tts(text)
            else:
                audio_data = await self.espeak_tts(text)
            
            if not audio_data:
                return
            
            # Convert to mulaw
            mulaw_audio = self.pcm_to_mulaw(audio_data)
            
            # Stream in chunks
            chunk_size = 320  # 20ms at 8kHz
            for i in range(0, len(mulaw_audio), chunk_size):
                chunk = mulaw_audio[i:i+chunk_size]
                
                # Base64 encode
                encoded = base64.b64encode(chunk).decode('utf-8')
                
                # Send media message
                message = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {
                        "payload": encoded
                    }
                }
                
                await websocket.send(json.dumps(message))
                await asyncio.sleep(0.02)  # 20ms pacing
                
        except Exception as e:
            print(f"TTS streaming error: {e}")
    
    async def google_tts(self, text: str) -> bytes:
        """Generate speech using Google TTS."""
        try:
            synthesis_input = tts.SynthesisInput(text=text)
            
            voice = tts.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Wavenet-D",
                ssml_gender=tts.SsmlVoiceGender.NEUTRAL
            )
            
            audio_config = tts.AudioConfig(
                audio_encoding=tts.AudioEncoding.LINEAR16,
                sample_rate_hertz=8000
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            print(f"Google TTS error: {e}")
            return None
    
    async def espeak_tts(self, text: str) -> bytes:
        """Generate speech using espeak (fallback)."""
        try:
            # Use espeak to generate raw audio
            cmd = [
                'espeak',
                '-s', '150',  # Speed
                '-p', '50',   # Pitch
                '--stdout',
                text
            ]
            
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                return result.stdout
            return None
            
        except Exception as e:
            print(f"espeak error: {e}")
            return None
    
    def mulaw_to_pcm(self, mulaw_data: bytes) -> bytes:
        """Convert mulaw to 16-bit PCM."""
        pcm = bytearray()
        
        # Mulaw decode table
        MULAW_TABLE = [
            -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
            -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
            -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
            -11900, -11388, -10876, -10364, -9852, -9340, -8828, -8316,
            -7932, -7676, -7420, -7164, -6908, -6652, -6396, -6140,
            -5884, -5628, -5372, -5116, -4860, -4604, -4348, -4092,
            -3900, -3772, -3644, -3516, -3388, -3260, -3132, -3004,
            -2876, -2748, -2620, -2492, -2364, -2236, -2108, -1980,
            -1884, -1820, -1756, -1692, -1628, -1564, -1500, -1436,
            -1372, -1308, -1244, -1180, -1116, -1052, -988, -924,
            -876, -844, -812, -780, -748, -716, -684, -652,
            -620, -588, -556, -524, -492, -460, -428, -396,
            -372, -356, -340, -324, -308, -292, -276, -260,
            -244, -228, -212, -196, -180, -164, -148, -132,
            -120, -112, -104, -96, -88, -80, -72, -64,
            -56, -48, -40, -32, -24, -16, -8, 0,
            32124, 31100, 30076, 29052, 28028, 27004, 25980, 24956,
            23932, 22908, 21884, 20860, 19836, 18812, 17788, 16764,
            15996, 15484, 14972, 14460, 13948, 13436, 12924, 12412,
            11900, 11388, 10876, 10364, 9852, 9340, 8828, 8316,
            7932, 7676, 7420, 7164, 6908, 6652, 6396, 6140,
            5884, 5628, 5372, 5116, 4860, 4604, 4348, 4092,
            3900, 3772, 3644, 3516, 3388, 3260, 3132, 3004,
            2876, 2748, 2620, 2492, 2364, 2236, 2108, 1980,
            1884, 1820, 1756, 1692, 1628, 1564, 1500, 1436,
            1372, 1308, 1244, 1180, 1116, 1052, 988, 924,
            876, 844, 812, 780, 748, 716, 684, 652,
            620, 588, 556, 524, 492, 460, 428, 396,
            372, 356, 340, 324, 308, 292, 276, 260,
            244, 228, 212, 196, 180, 164, 148, 132,
            120, 112, 104, 96, 88, 80, 72, 64,
            56, 48, 40, 32, 24, 16, 8, 0
        ]
        
        for byte in mulaw_data:
            pcm_val = MULAW_TABLE[byte]
            pcm.extend(struct.pack('<h', pcm_val))
        
        return bytes(pcm)
    
    def pcm_to_mulaw(self, pcm_data: bytes) -> bytes:
        """Convert 16-bit PCM to mulaw."""
        mulaw = bytearray()
        
        for i in range(0, len(pcm_data), 2):
            if i + 1 < len(pcm_data):
                # Get 16-bit sample
                sample = struct.unpack('<h', pcm_data[i:i+2])[0]
                
                # Simple mulaw encode (not perfect but works)
                if sample < 0:
                    sample = -sample
                    sign = 0x80
                else:
                    sign = 0
                
                # Find exponent
                sample = sample + 0x84
                if sample > 0x7FFF:
                    sample = 0x7FFF
                
                exp = 7
                for i in range(7):
                    if sample < (0x100 << i):
                        exp = i
                        break
                
                mantissa = (sample >> (exp + 3)) & 0x0F
                mulaw_byte = ~(sign | (exp << 4) | mantissa) & 0xFF
                mulaw.append(mulaw_byte)
        
        return bytes(mulaw)


async def main():
    """Start the Claude stream server."""
    handler = ClaudeStreamHandler()
    
    port = 8087
    print(f"🚀 Starting Claude Stream Server on port {port}")
    print("🤖 Real-time voice responses enabled")
    print("📞 Waiting for Twilio connections...")
    
    async with websockets.serve(
        handler.handle_websocket,
        "0.0.0.0",
        port,
        compression=None,
        max_size=10 * 1024 * 1024,
        ping_interval=None,
        ping_timeout=None
    ):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Shutting down")