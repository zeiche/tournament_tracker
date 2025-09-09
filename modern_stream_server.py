#!/usr/bin/env python3
"""
Modern websockets 15+ compatible Twilio Media Stream server
Uses the correct handler pattern for websockets 15.0.1
"""
import asyncio
import websockets.asyncio.server
import json
import base64
import ssl
import pathlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioHandler:
    def __init__(self):
        self.call_sid = None
        self.stream_sid = None
        self.audio_count = 0

    async def process_event(self, websocket, data):
        """Process Twilio event"""
        event = data.get('event')
        logger.info(f"📥 Event: {event}")
        
        if event == 'connected':
            logger.info("✅ Twilio connected")
            
        elif event == 'start':
            start_data = data.get('start', {})
            self.call_sid = start_data.get('callSid')
            self.stream_sid = start_data.get('streamSid')
            logger.info(f"📞 Call: {self.call_sid}")
            logger.info(f"🎙️ Stream: {self.stream_sid}")
            
            # Send response
            await self.send_response(websocket, "Tournament tracker ready!")
            
        elif event == 'media':
            self.audio_count += 1
            if self.audio_count % 10 == 0:
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

async def main():
    """Start the server using modern websockets API"""
    port = 8094
    
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
        logger.info(f"📡 Server running on wss://0-page.com:{port}/")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Stopped")