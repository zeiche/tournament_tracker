#!/usr/bin/env python3
"""
Twilio Media Stream WebSocket server for real-time audio processing.
Handles bidirectional audio streaming with tournament data responses.
"""

import asyncio
import websockets
import json
import base64
import struct
from datetime import datetime
from typing import Optional, Dict, Any
import os
import sys
import ssl
import pathlib

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import polymorphic components
try:
    from polymorphic_core import announcer
except ImportError:
    # Create dummy announcer if not available
    class DummyAnnouncer:
        def announce(self, *args, **kwargs):
            pass
    announcer = DummyAnnouncer()

try:
    from polymorphic_queries import query as pq
except ImportError:
    # Fallback query function
    def pq(query):
        return f"Tournament data query: {query}"

class TwilioStreamHandler:
    """Handles Twilio Media Stream WebSocket connections."""
    
    def __init__(self):
        self.call_sid = None
        self.stream_sid = None
        self.custom_params = {}
        self.audio_buffer = []
        
        # Announce ourselves
        announcer.announce(
            "Twilio Stream Handler",
            ["Handle real-time audio streams", "Process voice queries", "Send audio responses"],
            ["Stream tournament data via voice", "Real-time voice interaction"]
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
                
                # Send initial greeting
                await self.send_audio_response(
                    websocket,
                    "Welcome to the tournament tracker real-time system! Ask me about tournaments, players, or rankings."
                )
                
            elif event == 'media':
                # Incoming audio data
                media = data.get('media', {})
                audio_payload = media.get('payload')
                
                if audio_payload:
                    # Decode base64 audio
                    audio_bytes = base64.b64decode(audio_payload)
                    self.audio_buffer.append(audio_bytes)
                    
                    # Process audio every 20 chunks (approx 0.5 seconds)
                    if len(self.audio_buffer) >= 20:
                        await self.process_audio_buffer(websocket)
                
            elif event == 'stop':
                print(f"🛑 Stream stopped: {self.stream_sid}")
                
            elif event == 'mark':
                # Custom mark event
                mark = data.get('mark', {})
                print(f"📍 Mark received: {mark.get('name')}")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def process_audio_buffer(self, websocket):
        """Process accumulated audio buffer."""
        # For now, send periodic tournament updates
        # In production, this would do speech-to-text
        
        # Clear buffer
        self.audio_buffer = []
        
        # Get random tournament data
        try:
            # Query for recent tournament info
            response = pq("show recent tournament")
            if response:
                await self.send_audio_response(websocket, response)
        except Exception as e:
            print(f"Error querying data: {e}")
    
    async def send_audio_response(self, websocket, text: str):
        """Send text as audio back to Twilio."""
        print(f"📤 Sending response: {text[:50]}...")
        
        # Convert text to mulaw audio
        audio_data = self.text_to_mulaw(text)
        
        # Send audio chunks
        chunk_size = 320  # 20ms of 8kHz audio
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            
            # Base64 encode the chunk
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
            
            # Small delay between chunks
            await asyncio.sleep(0.02)
        
        # Send mark to indicate completion
        mark_message = {
            "event": "mark",
            "streamSid": self.stream_sid,
            "mark": {
                "name": "response_complete"
            }
        }
        await websocket.send(json.dumps(mark_message))
    
    def text_to_mulaw(self, text: str) -> bytes:
        """Convert text to mulaw audio format (placeholder)."""
        # In production, use TTS service to generate audio
        # For now, return silence
        
        # Generate 1 second of silence in mulaw format
        silence_duration = 1.0  # seconds
        sample_rate = 8000
        num_samples = int(sample_rate * silence_duration)
        
        # Mulaw silence is 0xFF (not 0x00)
        silence = bytes([0xFF] * num_samples)
        
        return silence
    
    async def send_clear_message(self, websocket):
        """Send clear/reset message to Twilio."""
        clear_message = {
            "event": "clear",
            "streamSid": self.stream_sid
        }
        await websocket.send(json.dumps(clear_message))


async def main():
    """Start the WebSocket server with SSL support."""
    handler = TwilioStreamHandler()
    
    port = 8087
    
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
    
    print(f"🚀 Starting Twilio Stream WebSocket server on port {port}")
    print(f"📡 WebSocket URL: {ws_url}")
    print("⏳ Waiting for Twilio streams...")
    
    # Start WebSocket server with SSL
    async with websockets.serve(
        handler.handle_websocket,
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
        print("\n👋 Shutting down stream server")