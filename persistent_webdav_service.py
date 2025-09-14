#!/usr/bin/env python3
"""
persistent_webdav_service.py - Minimal persistent WebDAV service

This service:
1. Runs persistently (doesn't exit)
2. Serves WebDAV on port 8082
3. Advertises as webdav.local via mDNS
4. Provides database access via WebDAV
"""

import http.server
import socketserver
import ssl
import json
import threading
import time
from polymorphic_core import announcer

class PersistentWebDAVService:
    """Persistent WebDAV service"""

    def __init__(self, port=8082):
        self.port = port
        self.server = None
        self.running = False
        self.cert_file = "/home/ubuntu/claude/tournament_tracker/services/wildcard_certificate.pem"
        self.key_file = "/home/ubuntu/claude/tournament_tracker/services/wildcard_private.key"

    def start(self):
        """Start the persistent WebDAV service"""
        print(f"🗂️ Starting persistent WebDAV service on port {self.port}")

        # Announce via mDNS as webdav.local
        announcer.announce(
            "webdav.local",
            [
                "WebDAV Database Service",
                "Tournament Data Access",
                "PROPFIND and GET support",
                f"Serves webdav.local on port {self.port}"
            ],
            examples=[
                f"curl -X PROPFIND http://webdav.local:{self.port}/",
                f"curl http://webdav.local:{self.port}/data/players",
                "Mount webdav.local in file manager"
            ],
            port=self.port
        )

        # Also advertise the hostname directly via zeroconf
        try:
            from zeroconf import ServiceInfo, Zeroconf
            import socket

            # Create hostname service info
            hostname_info = ServiceInfo(
                "_http._tcp.local.",
                "webdav._http._tcp.local.",
                addresses=[socket.inet_aton("10.0.0.1")],
                port=self.port,
                properties={
                    'hostname': 'webdav.local',
                    'path': '/',
                    'description': 'WebDAV Database Service'
                },
                server="webdav.local."
            )

            # Get or create zeroconf instance
            if hasattr(announcer, 'zeroconf') and announcer.zeroconf:
                announcer.zeroconf.register_service(hostname_info)
                print(f"🗂️ Registered webdav.local hostname via mDNS")
            else:
                print("⚠️  Could not register hostname - using service announcement only")

        except Exception as e:
            print(f"⚠️  Hostname registration failed: {e}")

        # Start HTTPS server
        try:
            # Import the existing WebDAV handler
            from services.webdav_service_refactored import WebDAVRequestHandler

            self.server = socketserver.TCPServer(("10.0.0.1", self.port), WebDAVRequestHandler)

            # Wrap with SSL
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.cert_file, self.key_file)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)

            self.running = True

            print(f"✅ WebDAV service running on https://10.0.0.1:{self.port}")
            print(f"🔒 Using SSL certificates: {self.cert_file}")
            print(f"🗂️ Advertised as webdav.local via mDNS")
            print("🏃 Service running persistently - press Ctrl+C to stop")

            # Run server forever
            self.server.serve_forever()

        except Exception as e:
            print(f"❌ Failed to start WebDAV service: {e}")
            self.running = False

    def stop(self):
        """Stop the WebDAV service"""
        if self.server:
            print("🛑 Stopping WebDAV service...")
            self.server.shutdown()
            self.server.server_close()
            self.running = False

def main():
    """Main entry point"""
    service = PersistentWebDAVService(port=8082)

    try:
        service.start()
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
        service.stop()
        print("✅ WebDAV service stopped")

if __name__ == "__main__":
    main()