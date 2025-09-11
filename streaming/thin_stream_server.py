#!/usr/bin/env python3
"""
Thin WebSocket bridge for Twilio Media Streams
Just passes messages between Twilio and Bonjour services
"""
import asyncio
import websockets.asyncio.server
import json
import ssl
import pathlib
import logging
import os
import subprocess
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import announcer only
try:
    from polymorphic_core import announcer
    logger.info("✅ Announcer available")
except ImportError:
    class DummyAnnouncer:
        def announce(self, *args, **kwargs):
            pass
    announcer = DummyAnnouncer()

class TwilioHandler:
    def __init__(self):
        self.call_sid = None
        self.stream_sid = None
        
    async def process_event(self, websocket, data):
        """Process Twilio event - just announce it"""
        event = data.get('event')
        logger.info(f"📥 Event: {event}")
        
        if event == 'start':
            start_data = data.get('start', {})
            self.call_sid = start_data.get('callSid')
            self.stream_sid = start_data.get('streamSid')
            
            announcer.announce(
                "TWILIO_CALL_START",
                [
                    f"Call: {self.call_sid}",
                    f"Stream: {self.stream_sid}"
                ]
            )
            
        elif event == 'media':
            # Just announce media received - let other services handle it
            media_data = data.get('media', {})
            announcer.announce(
                "TWILIO_MEDIA",
                [
                    f"Stream: {self.stream_sid}",
                    f"Payload: {media_data.get('payload', '')[:50]}..."
                ]
            )
            
        elif event == 'stop':
            announcer.announce(
                "TWILIO_CALL_STOP",
                [f"Stream: {self.stream_sid}"]
            )

# Global handler
handler = TwilioHandler()

async def websocket_handler(websocket):
    """Pure WebSocket bridge - no audio processing"""
    logger.info(f"🔌 Connection from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await handler.process_event(websocket, data)
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON")
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("📴 Connection closed")
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")

def kill_old_processes():
    """Kill existing servers"""
    try:
        subprocess.run(['pkill', '-f', 'stream_server'], check=False)
        logger.info("🗑️ Killed old servers")
    except:
        pass

async def main():
    port = 8088
    
    kill_old_processes()
    await asyncio.sleep(1)
    
    logger.info(f"🚀 Starting thin WebSocket bridge on port {port}")
    
    # SSL setup
    cert_path = pathlib.Path(__file__).parent / "server.crt"
    key_path = pathlib.Path(__file__).parent / "server.key"
    
    if not (cert_path.exists() and key_path.exists()):
        logger.error("❌ SSL certificates missing")
        return
    
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(cert_path, key_path)
    
    async with websockets.asyncio.server.serve(
        websocket_handler,
        "0.0.0.0", 
        port,
        ssl=ssl_context
    ):
        logger.info(f"📡 Thin bridge running on wss://0-page.com:{port}/")
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Stopped")