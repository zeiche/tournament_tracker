#!/usr/bin/env python3
"""
persistent_bonjour_service.py - Minimal persistent Bonjour universal server

This service:
1. Runs persistently (doesn't exit)
2. Serves multiple protocols on different ports
3. Advertises as bonjour.local via mDNS
4. Provides universal service discovery
"""

import http.server
import socketserver
import ssl
import json
import threading
import time
from polymorphic_core import announcer

class PersistentBonjourService:
    """Persistent Bonjour universal service"""

    def __init__(self, port=8083):
        self.port = port
        self.server = None
        self.running = False
        self.cert_file = "/home/ubuntu/claude/tournament_tracker/services/wildcard_certificate.pem"
        self.key_file = "/home/ubuntu/claude/tournament_tracker/services/wildcard_private.key"

    def start(self):
        """Start the persistent Bonjour service"""
        print(f"🏠 Starting persistent Bonjour universal service on port {self.port}")

        # Announce via mDNS as bonjour.local
        announcer.announce(
            "bonjour.local",
            [
                "Bonjour Universal Server",
                "Service Discovery Hub",
                "mDNS Management Interface",
                f"Serves bonjour.local on port {self.port}"
            ],
            examples=[
                f"curl http://bonjour.local:{self.port}/",
                f"curl http://bonjour.local:{self.port}/services",
                "View service discovery dashboard"
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
                "bonjour._http._tcp.local.",
                addresses=[socket.inet_aton("10.0.0.1")],
                port=self.port,
                properties={
                    'hostname': 'bonjour.local',
                    'path': '/',
                    'description': 'Bonjour Universal Server'
                },
                server="bonjour.local."
            )

            # Get or create zeroconf instance
            if hasattr(announcer, 'zeroconf') and announcer.zeroconf:
                announcer.zeroconf.register_service(hostname_info)
                print(f"🏠 Registered bonjour.local hostname via mDNS")
            else:
                print("⚠️  Could not register hostname - using service announcement only")

        except Exception as e:
            print(f"⚠️  Hostname registration failed: {e}")

        # Start HTTPS server
        try:
            # Import the existing Bonjour handler
            from networking.bonjour_universal_server import BonjourHandler

            self.server = socketserver.TCPServer(("10.0.0.1", self.port), BonjourHandler)

            # Wrap with SSL
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.cert_file, self.key_file)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)

            self.running = True

            print(f"✅ Bonjour service running on https://10.0.0.1:{self.port}")
            print(f"🔒 Using SSL certificates: {self.cert_file}")
            print(f"🏠 Advertised as bonjour.local via mDNS")
            print("🏃 Service running persistently - press Ctrl+C to stop")

            # Run server forever
            self.server.serve_forever()

        except Exception as e:
            print(f"❌ Failed to start Bonjour service: {e}")
            self.running = False

    def stop(self):
        """Stop the Bonjour service"""
        if self.server:
            print("🛑 Stopping Bonjour service...")
            self.server.shutdown()
            self.server.server_close()
            self.running = False

def main():
    """Main entry point"""
    service = PersistentBonjourService(port=8083)

    try:
        service.start()
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
        service.stop()
        print("✅ Bonjour service stopped")

if __name__ == "__main__":
    main()