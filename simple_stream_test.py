#!/usr/bin/env python3
"""
Simple WebSocket server to test Twilio Stream functionality
"""
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_twilio_stream(websocket, path):
    """Handle Twilio Media Stream WebSocket connection"""
    logger.info(f"🔌 New connection from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                event = data.get('event')
                
                logger.info(f"📥 Received event: {event}")
                
                if event == 'connected':
                    logger.info("✅ Twilio connected")
                    
                elif event == 'start':
                    start_data = data.get('start', {})
                    call_sid = start_data.get('callSid')
                    stream_sid = start_data.get('streamSid')
                    logger.info(f"📞 Stream started - Call: {call_sid}, Stream: {stream_sid}")
                    
                elif event == 'media':
                    media = data.get('media', {})
                    logger.info(f"🎤 Audio received: {len(media.get('payload', ''))} bytes")
                    
                elif event == 'stop':
                    logger.info("🛑 Stream stopped")
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON decode error: {e}")
            except Exception as e:
                logger.error(f"❌ Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("📴 Connection closed")
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")

async def main():
    """Start the WebSocket server"""
    port = 8089  # Use different port to avoid conflicts
    
    logger.info(f"🚀 Starting simple Twilio stream test server on port {port}")
    logger.info(f"📡 WebSocket URL: ws://localhost:{port}/")
    
    # Create proper handler wrapper
    def websocket_handler(websocket):
        return handle_twilio_stream(websocket, websocket.path)
    
    # Start server without SSL first
    async with websockets.serve(websocket_handler, "0.0.0.0", port):
        logger.info("⏳ Waiting for connections...")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down")