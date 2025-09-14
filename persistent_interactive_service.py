#!/usr/bin/env python3
"""
persistent_interactive_service.py - Minimal persistent interactive web service

This service:
1. Runs persistently (doesn't exit)
2. Serves interactive interface on port 8084
3. Advertises as interactive.local via mDNS
4. Provides real-time tournament management
"""

import http.server
import socketserver
import ssl
import json
import threading
import time
from polymorphic_core import announcer

class PersistentInteractiveService:
    """Persistent interactive web service"""

    def __init__(self, port=8084):
        self.port = port
        self.server = None
        self.running = False
        self.cert_file = "/home/ubuntu/claude/tournament_tracker/services/wildcard_certificate.pem"
        self.key_file = "/home/ubuntu/claude/tournament_tracker/services/wildcard_private.key"

    def start(self):
        """Start the persistent interactive service"""
        print(f"⚡ Starting persistent interactive service on port {self.port}")

        # Announce via mDNS as interactive.local
        announcer.announce(
            "interactive.local",
            [
                "Interactive Tournament Interface",
                "Real-time Management Dashboard",
                "Live Tournament Updates",
                f"Serves interactive.local on port {self.port}"
            ],
            examples=[
                f"curl http://interactive.local:{self.port}/",
                f"curl http://interactive.local:{self.port}/dashboard",
                "Real-time tournament management"
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
                "interactive._http._tcp.local.",
                addresses=[socket.inet_aton("10.0.0.1")],
                port=self.port,
                properties={
                    'hostname': 'interactive.local',
                    'path': '/',
                    'description': 'Interactive Tournament Interface'
                },
                server="interactive.local."
            )

            # Get or create zeroconf instance
            if hasattr(announcer, 'zeroconf') and announcer.zeroconf:
                announcer.zeroconf.register_service(hostname_info)
                print(f"⚡ Registered interactive.local hostname via mDNS")
            else:
                print("⚠️  Could not register hostname - using service announcement only")

        except Exception as e:
            print(f"⚠️  Hostname registration failed: {e}")

        # Start HTTPS server
        try:
            # Import the existing interactive handler
            from services.interactive_web_service_daemon import InteractiveWebHandler

            self.server = socketserver.TCPServer(("10.0.0.1", self.port), InteractiveWebHandler)

            # Wrap with SSL
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.cert_file, self.key_file)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)

            self.running = True

            print(f"✅ Interactive service running on https://10.0.0.1:{self.port}")
            print(f"🔒 Using SSL certificates: {self.cert_file}")
            print(f"⚡ Advertised as interactive.local via mDNS")
            print("🏃 Service running persistently - press Ctrl+C to stop")

            # Run server forever
            self.server.serve_forever()

        except Exception as e:
            print(f"❌ Failed to start interactive service: {e}")
            self.running = False

    def stop(self):
        """Stop the interactive service"""
        if self.server:
            print("🛑 Stopping interactive service...")
            self.server.shutdown()
            self.server.server_close()
            self.running = False

def main():
    """Main entry point"""
    service = PersistentInteractiveService(port=8084)

    try:
        service.start()
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
        service.stop()
        print("✅ Interactive service stopped")

if __name__ == "__main__":
    main()