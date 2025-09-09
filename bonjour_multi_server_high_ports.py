#!/usr/bin/env python3
"""
Bonjour Multi-Port Server - High Ports Version
Uses ports above 1024 to avoid sudo requirement
"""

import asyncio
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
from pathlib import Path
from datetime import datetime
import socket

# Add parent directory to path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')

# Import the announcer
from polymorphic_core import announcer

class BonjourMultiHandler(SimpleHTTPRequestHandler):
    """Universal handler that announces and routes based on port"""
    
    def do_GET(self):
        # Get the port we're serving on
        port = self.server.server_port
        
        # Announce the request
        announcer.announce(
            f"Request on port {port}",
            [f"Path: {self.path}", f"From: {self.client_address[0]}"]
        )
        
        # Route based on port and path
        if port == 8880:  # Was 80
            # ACME challenge handling
            if self.path.startswith('/.well-known/acme-challenge/'):
                self.handle_acme_challenge()
            else:
                self.handle_general_http()
        elif port == 8888:  # Was 8080
            # TwiML or webhook handling
            self.handle_webhook()
        elif port == 8889:  # Was 8081
            # Status/monitoring endpoint
            self.handle_status()
        else:
            self.handle_general_http()
    
    def handle_acme_challenge(self):
        """Handle ACME challenge requests"""
        challenge_dir = Path('.well-known/acme-challenge')
        challenge_file = self.path.split('/')[-1]
        
        announcer.announce(
            "ACME Challenge Request",
            [f"Token: {challenge_file}"]
        )
        
        # Serve the challenge file if it exists
        if (challenge_dir / challenge_file).exists():
            super().do_GET()
        else:
            self.send_error(404, "Challenge not found")
    
    def handle_webhook(self):
        """Handle webhook requests"""
        announcer.announce(
            "Webhook received",
            [f"Path: {self.path}", f"Method: GET"]
        )
        
        # Return success
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Webhook received on port 8888')
    
    def handle_status(self):
        """Handle status/monitoring requests"""
        announcer.announce(
            "Status check",
            [f"From: {self.client_address[0]}"]
        )
        
        # Get all announcements for status
        context = announcer.get_announcements_for_claude()
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(f"Bonjour Status Page\n\n{context}".encode())
    
    def handle_general_http(self):
        """Handle general HTTP requests"""
        announcer.announce(
            "General HTTP request",
            [f"Path: {self.path}"]
        )
        
        # Serve files from current directory
        super().do_GET()
    
    def log_message(self, format, *args):
        """Override to use announcer for logging"""
        message = format % args
        print(f"[Port {self.server.server_port}] {self.client_address[0]} - {message}")


class BonjourMultiServer:
    """Multi-port server with Bonjour announcements"""
    
    def __init__(self, ports=None):
        if ports is None:
            # Use higher ports that don't require sudo
            ports = [8880, 8888, 8889]
        
        self.ports = ports
        self.servers = {}
        
        # Announce what we are
        announcer.announce(
            "Bonjour Multi-Port Server (High Ports)",
            [
                f"I serve on multiple ports: {ports}",
                "Port 8880: General HTTP & ACME challenges",
                "Port 8888: Webhooks and TwiML",
                "Port 8889: Status and monitoring",
                "I announce all activity across all ports",
                "No sudo required!"
            ]
        )
    
    def start_server_on_port(self, port):
        """Start a server on a specific port"""
        try:
            server = HTTPServer(('0.0.0.0', port), BonjourMultiHandler)
            
            announcer.announce(
                f"Server started on port {port}",
                [f"Ready at http://64.111.98.139:{port}/"]
            )
            
            print(f"✅ Port {port} ready")
            
            # Run in thread
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()
            
            self.servers[port] = (server, thread)
            return True
            
        except PermissionError:
            announcer.announce(
                f"Permission denied for port {port}",
                ["Need sudo for ports below 1024"]
            )
            print(f"❌ Port {port}: Permission denied (need sudo)")
            return False
            
        except OSError as e:
            if e.errno == 98:  # Address already in use
                announcer.announce(
                    f"Port {port} already in use",
                    ["Another service is using this port"]
                )
                print(f"⚠️  Port {port}: Already in use")
            else:
                print(f"❌ Port {port}: {e}")
            return False
    
    def start_all(self):
        """Start servers on all configured ports"""
        os.chdir('/home/ubuntu/claude/tournament_tracker')
        
        announcer.announce(
            "Starting multi-port servers",
            [f"Attempting ports: {self.ports}"]
        )
        
        success_count = 0
        for port in self.ports:
            if self.start_server_on_port(port):
                success_count += 1
        
        if success_count == 0:
            print("❌ No servers could be started")
            return False
        
        print(f"\n✅ {success_count}/{len(self.ports)} servers running")
        print("Press Ctrl+C to stop all servers")
        
        # Keep main thread alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down servers...")
            self.shutdown_all()
    
    def shutdown_all(self):
        """Shutdown all running servers"""
        for port, (server, thread) in self.servers.items():
            print(f"Stopping server on port {port}...")
            server.shutdown()
        
        announcer.announce(
            "All servers stopped",
            ["Bonjour Multi-Port Server shutdown complete"]
        )


if __name__ == "__main__":
    # Check for custom ports from command line
    if len(sys.argv) > 1:
        ports = [int(p) for p in sys.argv[1:]]
        server = BonjourMultiServer(ports)
    else:
        server = BonjourMultiServer()  # Uses default high ports
    
    server.start_all()