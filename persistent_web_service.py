#!/usr/bin/env python3
"""
persistent_web_service.py - Minimal persistent web service for tournaments.local

This service:
1. Runs persistently (doesn't exit)
2. Serves HTTP on port 80 (or 8080)
3. Advertises as tournaments.local via mDNS
4. Provides basic tournament data endpoints
"""

import http.server
import socketserver
import ssl
import json
import threading
import time
from polymorphic_core import announcer
from polymorphic_core.wireguard_mdns_bridge import wireguard_mdns_bridge

class TournamentWebHandler(http.server.SimpleHTTPRequestHandler):
    """Simple HTTP handler for tournament data"""

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = '''
<!DOCTYPE html>
<html>
<head><title>Tournament Tracker</title></head>
<body>
    <h1>Tournament Tracker</h1>
    <p>Welcome to the Southern California FGC Tournament Tracker</p>
    <ul>
        <li><a href="/api/tournaments">Recent Tournaments</a></li>
        <li><a href="/api/players">Top Players</a></li>
        <li><a href="/api/stats">Statistics</a></li>
    </ul>
</body>
</html>
            '''
            self.wfile.write(html_content.encode())
        elif self.path == '/api/tournaments':
            self.send_json({'message': 'Tournament API endpoint', 'status': 'active'})
        elif self.path == '/api/players':
            self.send_json({'message': 'Player API endpoint', 'status': 'active'})
        elif self.path == '/api/stats':
            self.send_json({'message': 'Stats API endpoint', 'status': 'active'})
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

class PersistentTournamentWebService:
    """Persistent web service for tournaments"""

    def __init__(self, port=8081):
        self.port = port
        self.server = None
        self.running = False
        self.cert_file = "/home/ubuntu/claude/tournament_tracker/services/wildcard_certificate.pem"
        self.key_file = "/home/ubuntu/claude/tournament_tracker/services/wildcard_private.key"

        # Setup WireGuard bridge
        self.bridge_info = wireguard_mdns_bridge.do("setup")

    def start(self):
        """Start the persistent web service"""
        print(f"🌐 Starting persistent tournament web service on port {self.port}")

        # Announce via mDNS with tournaments.local hostname
        announcer.announce(
            "tournaments.local",
            [
                "HTTP Web Server",
                "Tournament Data API",
                "Southern California FGC",
                f"Serves tournaments.local on port {self.port}"
            ],
            examples=[
                f"curl http://tournaments.local:{self.port}/",
                f"curl http://tournaments.local:{self.port}/api/tournaments",
                "Visit http://tournaments.local in browser"
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
                "tournaments._http._tcp.local.",
                addresses=[socket.inet_aton("10.0.0.1")],
                port=self.port,
                properties={
                    'hostname': 'tournaments.local',
                    'path': '/',
                    'description': 'Tournament Tracker Web Interface'
                },
                server="tournaments.local."
            )

            # Get or create zeroconf instance
            if hasattr(announcer, 'zeroconf') and announcer.zeroconf:
                announcer.zeroconf.register_service(hostname_info)
                print(f"🌐 Registered tournaments.local hostname via mDNS")
            else:
                print("⚠️  Could not register hostname - using service announcement only")

        except Exception as e:
            print(f"⚠️  Hostname registration failed: {e}")

        # Start HTTPS server - bind to all interfaces for both local and WireGuard access
        try:
            print(f"🔗 WireGuard bridge: {wireguard_mdns_bridge.tell('text')}")

            # Bind to 0.0.0.0 to accept connections on ALL interfaces
            # This allows both local (127.0.0.1) and WireGuard (10.0.0.1) access
            self.server = socketserver.TCPServer(("0.0.0.0", self.port), TournamentWebHandler)

            # Wrap with SSL
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.cert_file, self.key_file)
            self.server.socket = context.wrap_socket(self.server.socket, server_side=True)

            self.running = True

            bridge_status = wireguard_mdns_bridge.ask("status")
            wg_ip = bridge_status.get('wg_ip', 'N/A')
            local_ip = bridge_status.get('local_ip', '127.0.0.1')

            print(f"✅ Tournament web service running on ALL interfaces:")
            print(f"   🌍 Local access: https://{local_ip}:{self.port}")
            print(f"   🔗 WireGuard access: https://{wg_ip}:{self.port}")
            print(f"   🏠 Localhost access: https://127.0.0.1:{self.port}")
            print(f"   🌐 mDNS access: https://tournaments.local:{self.port}")
            print(f"🔒 Using SSL certificates: {self.cert_file}")
            print("🏃 Service running persistently - press Ctrl+C to stop")

            # Run server forever
            self.server.serve_forever()

        except Exception as e:
            print(f"❌ Failed to start web service: {e}")
            self.running = False

    def stop(self):
        """Stop the web service"""
        if self.server:
            print("🛑 Stopping tournament web service...")
            self.server.shutdown()
            self.server.server_close()
            self.running = False

def main():
    """Main entry point"""
    service = PersistentTournamentWebService(port=8081)

    try:
        service.start()
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
        service.stop()
        print("✅ Tournament web service stopped")

if __name__ == "__main__":
    main()