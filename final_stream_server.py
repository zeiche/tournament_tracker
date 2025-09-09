#!/usr/bin/env python3
"""
Final working Twilio Media Stream WebSocket server
Uses the correct websockets library pattern
"""
import asyncio
import websockets
import json
import base64
import ssl
import pathlib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioStreamProcessor:
    def __init__(self):
        self.call_sid = None
        self.stream_sid = None
        self.audio_count = 0

    async def handle_message(self, websocket, message):
        """Process incoming Twilio message"""
        try:
            data = json.loads(message)
            event = data.get('event')
            
            logger.info(f"📥 Received: {event}")
            
            if event == 'connected':
                logger.info("✅ Twilio stream connected")
                
            elif event == 'start':
                start_data = data.get('start', {})
                self.call_sid = start_data.get('callSid')
                self.stream_sid = start_data.get('streamSid')
                logger.info(f"📞 Call: {self.call_sid}")
                logger.info(f"🎙️ Stream: {self.stream_sid}")
                
                # Send welcome response
                await self.send_audio_response(websocket, "Tournament tracker connected!")
                
            elif event == 'media':
                media = data.get('media', {})
                payload = media.get('payload', '')
                self.audio_count += 1
                logger.info(f"🎤 Audio packet {self.audio_count}: {len(payload)} bytes")
                
                # Respond every 20 packets
                if self.audio_count % 20 == 0:
                    await self.send_audio_response(websocket, f"Received {self.audio_count} audio packets")
                    
            elif event == 'stop':
                logger.info("🛑 Stream ended")
                
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")

    async def send_audio_response(self, websocket, text):
        """Send audio response back to Twilio"""
        if not self.stream_sid:
            return
            
        logger.info(f"📤 Sending: {text}")
        
        # Generate silence (in production, use TTS)
        silence_duration_ms = 20
        samples_per_ms = 8  # 8kHz
        silence_samples = silence_duration_ms * samples_per_ms
        silence_bytes = bytes([0xFF] * silence_samples)
        
        # Send as media event
        media_message = {
            "event": "media",
            "streamSid": self.stream_sid,
            "media": {
                "payload": base64.b64encode(silence_bytes).decode('utf-8')
            }
        }
        
        await websocket.send(json.dumps(media_message))

# Create processor instance
processor = TwilioStreamProcessor()

async def handle_websocket(websocket, path):
    """Handle WebSocket connection - CORRECT SIGNATURE"""
    logger.info(f"🔌 New connection from {websocket.remote_address} path: {path}")
    
    try:
        async for message in websocket:
            await processor.handle_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        logger.info("📴 Connection closed normally")
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")

def main():
    """Start the server with correct SSL setup"""
    port = 8093
    
    logger.info(f"🚀 Starting final Twilio stream server on port {port}")
    
    # SSL setup
    cert_path = pathlib.Path(__file__).parent / "server.crt"
    key_path = pathlib.Path(__file__).parent / "server.key"
    
    if not (cert_path.exists() and key_path.exists()):
        logger.error("❌ SSL certificates not found")
        return
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_path, key_path)
    logger.info("🔐 SSL context created")
    
    # Start server with correct parameters
    logger.info(f"📡 Starting server on wss://0-page.com:{port}/")
    
    # Use proper asyncio event loop
    async def run_server():
        async with websockets.serve(
            handle_websocket,  # Function, not method
            "0.0.0.0",
            port,
            ssl=ssl_context,
            # Twilio-specific settings
            compression=None,
            max_size=10 * 1024 * 1024,
            ping_interval=None,
            ping_timeout=None
        ):
            logger.info("✅ Server started successfully")
            await asyncio.Future()  # Run forever
    
    # Run the server
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped")

if __name__ == "__main__":
    main()