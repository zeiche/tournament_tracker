#!/usr/bin/env python3
"""
SSL Proxy Service - Handles SSL/TLS termination for WebSocket connections.
Accepts secure wss:// connections and forwards to internal ws:// services.
Announces itself via Bonjour pattern.
"""

import asyncio
import websockets
import ssl
import pathlib
import sys
import os

# Bonjour-style announcements
try:
    from polymorphic_core import announcer
except ImportError:
    class DummyAnnouncer:
        def announce(self, *args, **kwargs):
            print(f"📢 ANNOUNCE: {args[0] if args else ''}")
    announcer = DummyAnnouncer()

class SSLProxyService:
    """SSL termination proxy for WebSocket connections."""
    
    def __init__(self, listen_port=8443, forward_host='localhost', forward_port=8087):
        self.listen_port = listen_port
        self.forward_host = forward_host
        self.forward_port = forward_port
        self.forward_url = f"ws://{forward_host}:{forward_port}"
        self.public_url = f"wss://64.111.98.139:{listen_port}/"
        
        # Announce what we are
        announcer.announce(
            "SSL Proxy Service",
            [
                f"I provide SSL/TLS termination for WebSocket connections",
                f"I listen on port {listen_port} with SSL",
                f"I forward to {self.forward_url} without SSL",
                f"Twilio can connect to me at {self.public_url}"
            ],
            [
                "Use me to enable secure WebSocket connections",
                "I handle SSL so backend services don't have to"
            ]
        )
        
        # SSL setup - Use Let's Encrypt certificates
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Try Let's Encrypt certificates first
        le_cert_path = pathlib.Path(__file__).parent / "fullchain.pem"
        le_key_path = pathlib.Path(__file__).parent / "privkey.pem"
        
        # Fallback to self-signed if Let's Encrypt not available
        cert_path = pathlib.Path(__file__).parent / "server.crt"
        key_path = pathlib.Path(__file__).parent / "server.key"
        
        if le_cert_path.exists() and le_key_path.exists():
            self.ssl_context.load_cert_chain(le_cert_path, le_key_path)
            announcer.announce(
                "SSL_CERTIFICATES_LOADED",
                [f"Let's Encrypt certificates loaded from {le_cert_path}"],
                ["Ready for secure connections with valid SSL"]
            )
        elif cert_path.exists() and key_path.exists():
            self.ssl_context.load_cert_chain(cert_path, key_path)
            announcer.announce(
                "SSL_CERTIFICATES_LOADED",
                [f"Self-signed certificates loaded from {cert_path}"],
                ["Ready for secure connections (self-signed)"]
            )
        else:
            announcer.announce(
                "SSL_CERTIFICATES_MISSING",
                [f"No certificates found at {le_cert_path} or {cert_path}"],
                ["Cannot provide SSL without certificates"]
            )
            raise FileNotFoundError(f"SSL certificates not found")
    
    async def handle_client(self, client_ws, path):
        """Handle incoming SSL WebSocket and forward to backend."""
        print(f"🔌 New SSL connection from {client_ws.remote_address}")
        
        # Connect to backend WebSocket server (without SSL)
        try:
            async with websockets.connect(self.forward_url) as backend_ws:
                print(f"↔️ Connected to backend: {self.forward_url}")
                
                # Create tasks for bidirectional forwarding
                client_to_backend = asyncio.create_task(
                    self.forward_messages(client_ws, backend_ws, "client→backend")
                )
                backend_to_client = asyncio.create_task(
                    self.forward_messages(backend_ws, client_ws, "backend→client")
                )
                
                # Wait for either connection to close
                done, pending = await asyncio.wait(
                    [client_to_backend, backend_to_client],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                
        except Exception as e:
            print(f"❌ Backend connection error: {e}")
            await client_ws.close()
    
    async def forward_messages(self, source_ws, dest_ws, direction):
        """Forward messages from source to destination WebSocket."""
        try:
            async for message in source_ws:
                # Forward the message
                if isinstance(message, str):
                    await dest_ws.send(message)
                    if len(message) < 200:
                        print(f"📨 {direction}: {message[:100]}...")
                    else:
                        print(f"📨 {direction}: {len(message)} bytes")
                else:
                    # Binary message
                    await dest_ws.send(message)
                    print(f"📨 {direction}: binary {len(message)} bytes")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔚 Connection closed: {direction}")
        except Exception as e:
            print(f"❌ Forward error {direction}: {e}")
    
    async def start(self):
        """Start the SSL proxy server."""
        print(f"🚀 Starting SSL Proxy Service")
        print(f"📥 Listening on wss://0.0.0.0:{self.listen_port} (SSL/TLS)")
        print(f"📤 Forwarding to {self.forward_url} (plain WebSocket)")
        print(f"🔗 Public URL: wss://64.111.98.139:{self.listen_port}/")
        
        async with websockets.serve(
            self.handle_client,
            "0.0.0.0",
            self.listen_port,
            ssl=self.ssl_context,
            compression=None,  # Twilio doesn't use compression
            max_size=10 * 1024 * 1024,
            ping_interval=None,
            ping_timeout=None
        ):
            print("✅ SSL Proxy running - Twilio can now connect securely")
            await asyncio.Future()  # Run forever


async def main():
    """Main entry point."""
    # Parse arguments if needed
    listen_port = int(os.environ.get('SSL_PROXY_PORT', '8443'))
    forward_port = int(os.environ.get('FORWARD_PORT', '8087'))
    
    proxy = SSLProxyService(
        listen_port=listen_port,
        forward_host='localhost',
        forward_port=forward_port
    )
    
    await proxy.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 SSL Proxy shutting down")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)