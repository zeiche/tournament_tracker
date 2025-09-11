#!/usr/bin/env python3
"""
Working Twilio Media Stream WebSocket server
"""
import asyncio
import websockets
import json
import base64
import ssl
import pathlib
from typing import Optional

class WorkingTwilioHandler:
    def __init__(self):
        self.call_sid = None
        self.stream_sid = None

    async def process_message(self, websocket, message: str):
        """Process incoming WebSocket message from Twilio"""
        try:
            data = json.loads(message)
            event = data.get('event')
            
            print(f"📥 Event: {event}")
            
            if event == 'connected':
                print("✅ Twilio connected to stream")
                
            elif event == 'start':
                start_data = data.get('start', {})
                self.call_sid = start_data.get('callSid')
                self.stream_sid = start_data.get('streamSid')
                print(f"📞 Stream started - Call: {self.call_sid}")
                print(f"🎙️ Stream ID: {self.stream_sid}")
                
                # Send initial response
                await self.send_response(websocket, "Welcome to tournament tracker!")
                
            elif event == 'media':
                media = data.get('media', {})
                payload = media.get('payload', '')
                print(f"🎤 Received audio: {len(payload)} bytes")
                
                # Process every 10 audio packets
                if hasattr(self, 'audio_count'):
                    self.audio_count += 1
                else:
                    self.audio_count = 1
                    
                if self.audio_count % 10 == 0:
                    await self.send_response(websocket, "I hear you!")
                    
            elif event == 'stop':
                print("🛑 Stream stopped")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")

    async def send_response(self, websocket, text: str):
        """Send audio response back to Twilio"""
        if not self.stream_sid:
            return
            
        print(f"📤 Sending: {text}")
        
        # Create silence for now (in production would use TTS)
        silence_bytes = bytes([0xFF] * 320)  # 20ms of mulaw silence
        payload = base64.b64encode(silence_bytes).decode('utf-8')
        
        media_message = {
            "event": "media",
            "streamSid": self.stream_sid,
            "media": {
                "payload": payload
            }
        }
        
        await websocket.send(json.dumps(media_message))

# Global handler instance
handler = WorkingTwilioHandler()

async def websocket_handler(websocket, path):
    """WebSocket connection handler"""
    print(f"🔌 Connection from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            await handler.process_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        print("📴 Connection closed")
    except Exception as e:
        print(f"❌ Connection error: {e}")

async def main():
    """Start the server"""
    port = 8092  # New SSL port
    
    print(f"🚀 Starting working Twilio stream server with SSL on port {port}")
    
    # Check for SSL certificates
    cert_path = pathlib.Path(__file__).parent / "server.crt"
    key_path = pathlib.Path(__file__).parent / "server.key"
    
    ssl_context = None
    if cert_path.exists() and key_path.exists():
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_path, key_path)
        print("🔐 SSL enabled with domain certificate")
    else:
        print("⚠️ SSL certificates not found")
        return
    
    async with websockets.serve(
        websocket_handler,
        "0.0.0.0", 
        port,
        ssl=ssl_context
    ):
        print(f"📡 Listening on wss://0-page.com:{port}/")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("👋 Shutting down")