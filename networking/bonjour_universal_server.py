#!/usr/bin/env python3
"""
Bonjour Universal Server - Binds to ANY ports dynamically
With CAP_NET_BIND_SERVICE, Python can bind to any port including privileged ones
"""

import asyncio
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
from pathlib import Path
from datetime import datetime
import socket
import json

# Add parent directory to path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')

from polymorphic_core import announcer

class UniversalHandler(SimpleHTTPRequestHandler):
    """Universal handler that adapts to any port"""
    
    def do_GET(self):
        port = self.server.server_port
        
        # Announce the request
        announcer.announce(
            f"Request on port {port}",
            [f"Path: {self.path}", f"From: {self.client_address[0]}"]
        )
        
        # Route based on common port patterns
        if port == 80:
            self.handle_http()
        elif port == 443:
            self.handle_https()
        elif port == 8080 or port == 8081:
            self.handle_webhook()
        elif port == 3000:
            self.handle_api()
        elif port in [8086, 8087, 8088]:
            self.handle_service()
        else:
            self.handle_generic()
    
    def handle_http(self):
        """Handle standard HTTP on port 80"""
        if self.path.startswith('/.well-known/acme-challenge/'):
            self.handle_acme()
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Bonjour Server on Port 80</h1>")
    
    def handle_https(self):
        """Handle HTTPS on port 443"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Secure Bonjour Server on Port 443</h1>")
    
    def handle_webhook(self):
        """Handle webhook requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {"status": "received", "port": self.server.server_port}
        self.wfile.write(json.dumps(response).encode())
    
    def handle_api(self):
        """Handle API requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        # Get service announcements
        announcements = []
        if hasattr(announcer, 'announcements'):
            announcements = announcer.announcements
        
        response = {
            "service": "Bonjour Universal API",
            "port": self.server.server_port,
            "announcements": len(announcements)
        }
        self.wfile.write(json.dumps(response).encode())
    
    def handle_service(self):
        """Handle service-specific requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        
        # Show all announcements
        context = announcer.get_announcements_for_claude()
        self.wfile.write(f"Service Port {self.server.server_port}\n\n{context}".encode())
    
    def handle_generic(self):
        """Handle any other port"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(f"Bonjour Universal Server on port {self.server.server_port}".encode())
    
    def handle_acme(self):
        """Handle ACME challenge for Let's Encrypt"""
        challenge_dir = Path('.well-known/acme-challenge')
        challenge_file = self.path.split('/')[-1]
        
        if (challenge_dir / challenge_file).exists():
            super().do_GET()
        else:
            self.send_error(404, "Challenge not found")
    
    def log_message(self, format, *args):
        """Custom logging"""
        message = format % args
        print(f"[Port {self.server.server_port}] {message}")


class BonjourUniversalServer:
    """Universal server that can bind to ANY ports"""
    
    def __init__(self):
        self.servers = {}
        self.threads = {}
        
        # Announce capabilities
        announcer.announce(
            "Bonjour Universal Server",
            [
                "Can bind to ANY port (including privileged)",
                "Self-announces all services",
                "Automatic port detection and routing",
                "Dynamic port allocation",
                "No sudo required (using CAP_NET_BIND_SERVICE)"
            ],
            examples=[
                "server.bind(80)  # HTTP",
                "server.bind(443) # HTTPS", 
                "server.bind(3000) # API",
                "server.bind_range(8080, 8090) # Multiple ports"
            ]
        )
    
    def bind(self, port):
        """Bind to a specific port"""
        if port in self.servers:
            print(f"⚠️  Port {port} already bound")
            return False
        
        try:
            server = HTTPServer(('0.0.0.0', port), UniversalHandler)
            
            # Start in thread
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()
            
            self.servers[port] = server
            self.threads[port] = thread
            
            announcer.announce(
                f"Port {port} bound",
                [
                    f"URL: http://64.111.98.139:{port}/",
                    f"Service: {self.get_port_description(port)}"
                ]
            )
            
            print(f"✅ Port {port} bound successfully")
            return True
            
        except OSError as e:
            if e.errno == 98:
                print(f"⚠️  Port {port} already in use")
            elif e.errno == 13:
                print(f"❌ Port {port} permission denied")
                print("   Run: sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3.12")
            else:
                print(f"❌ Port {port}: {e}")
            return False
    
    def bind_range(self, start, end):
        """Bind to a range of ports"""
        bound = []
        for port in range(start, end + 1):
            if self.bind(port):
                bound.append(port)
        return bound
    
    def bind_common(self):
        """Bind to common service ports"""
        common_ports = [80, 443, 3000, 8080, 8081, 8086, 8087, 8088]
        bound = []
        for port in common_ports:
            if self.bind(port):
                bound.append(port)
        return bound
    
    def get_port_description(self, port):
        """Get description for common ports"""
        descriptions = {
            80: "HTTP Web Server",
            443: "HTTPS Secure Server",
            3000: "Development API Server",
            8080: "Webhook/Proxy Server",
            8081: "Web Editor Service",
            8086: "TwiML Service",
            8087: "WebSocket Service",
            8088: "Monitoring Service"
        }
        return descriptions.get(port, f"Custom Service")
    
    def status(self):
        """Show status of all bound ports"""
        if not self.servers:
            print("No ports bound")
            return
        
        print("\n" + "=" * 60)
        print("🌐 BONJOUR UNIVERSAL SERVER STATUS")
        print("=" * 60)
        
        for port in sorted(self.servers.keys()):
            desc = self.get_port_description(port)
            print(f"  Port {port:5} : {desc:25} http://64.111.98.139:{port}/")
        
        print("=" * 60)
        print(f"Total: {len(self.servers)} ports bound")
        print("Python has CAP_NET_BIND_SERVICE - no sudo needed!")
        print()
    
    def shutdown(self, port=None):
        """Shutdown specific port or all"""
        if port:
            if port in self.servers:
                self.servers[port].shutdown()
                del self.servers[port]
                del self.threads[port]
                print(f"Port {port} shutdown")
        else:
            for port in list(self.servers.keys()):
                self.shutdown(port)
            print("All servers shutdown")


def main():
    """Main entry point with CLI"""
    server = BonjourUniversalServer()
    
    if len(sys.argv) > 1:
        # Bind to specific ports from command line
        for arg in sys.argv[1:]:
            if '-' in arg:
                # Range like 8080-8090
                start, end = map(int, arg.split('-'))
                ports = server.bind_range(start, end)
                print(f"Bound to {len(ports)} ports in range {start}-{end}")
            else:
                # Single port
                port = int(arg)
                server.bind(port)
    else:
        # Default: bind to common ports
        print("Binding to common service ports...")
        bound = server.bind_common()
        print(f"\nBound to {len(bound)} ports: {bound}")
    
    # Show status
    server.status()
    
    # Keep running
    try:
        print("\nPress Ctrl+C to shutdown all servers")
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()
        print("Goodbye!")


if __name__ == "__main__":
    # Import the persistent Bonjour service instead
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from persistent_bonjour_service import main
    main()