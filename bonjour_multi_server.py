#!/usr/bin/env python3
"""
Bonjour Multi-Port Server
Serves multiple services on different ports with self-announcement
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
try:
    from polymorphic_core import announcer
except ImportError:
    from capability_announcer import CapabilityAnnouncer
    announcer = CapabilityAnnouncer("bonjour_multi_server")

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
        if port == 80:
            # ACME challenge handling
            if self.path.startswith('/.well-known/acme-challenge/'):
                self.handle_acme_challenge()
            else:
                self.handle_general_http()
        elif port == 8080:
            # TwiML or webhook handling
            self.handle_webhook()
        elif port == 8081:
            # Status/monitoring endpoint
            self.handle_status()
        else:
            # Default handling
            super().do_GET()
    
    def do_POST(self):
        # Similar to GET but for POST requests
        port = self.server.server_port
        
        # Read POST data
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length else b''
        
        announcer.announce(
            f"POST on port {port}",
            [f"Path: {self.path}", f"Data length: {content_length}"]
        )
        
        if port == 8080:
            # Handle TwiML POST
            self.handle_twiml_post(post_data)
        else:
            self.do_GET()  # Fallback to GET handling
    
    def handle_acme_challenge(self):
        """Handle ACME challenge requests on port 80"""
        token = self.path.split('/')[-1]
        
        announcer.announce(
            "ACME challenge requested",
            [f"Token: {token}"]
        )
        
        challenge_dir = Path('/home/ubuntu/claude/tournament_tracker/.well-known/acme-challenge')
        challenge_dir.mkdir(parents=True, exist_ok=True)
        challenge_file = challenge_dir / token
        
        if challenge_file.exists():
            announcer.announce(
                "ACME challenge served",
                [f"Token: {token}"]
            )
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            
            with open(challenge_file, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"Challenge not found: {token}")
    
    def handle_webhook(self):
        """Handle webhook requests on port 8080"""
        announcer.announce(
            "Webhook request",
            [f"Path: {self.path}"]
        )
        
        # Simple webhook response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "service": "bonjour"}')
    
    def handle_twiml_post(self, post_data):
        """Handle TwiML POST requests"""
        announcer.announce(
            "TwiML POST received",
            [f"Data: {post_data[:100]}..."]
        )
        
        # Return TwiML response
        twiml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Bonjour multi-port server responding</Say>
</Response>'''
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/xml')
        self.end_headers()
        self.wfile.write(twiml)
    
    def handle_status(self):
        """Handle status requests on port 8081"""
        status = {
            "service": "bonjour_multi_server",
            "ports": [80, 8080, 8081],
            "status": "running"
        }
        
        import json
        response = json.dumps(status).encode()
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response)
    
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
            ports = [80, 8080, 8081]
        
        self.ports = ports
        self.servers = {}
        
        # Announce what we are
        announcer.announce(
            "Bonjour Multi-Port Server",
            [
                f"I serve on multiple ports: {ports}",
                "Port 80: ACME challenges for Let's Encrypt",
                "Port 8080: Webhooks and TwiML",
                "Port 8081: Status and monitoring",
                "I announce all activity across all ports"
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
            
        except PermissionError:
            announcer.announce(
                f"Permission denied for port {port}",
                ["Need sudo for ports below 1024"]
            )
            print(f"❌ Port {port}: Permission denied (need sudo)")
            
        except OSError as e:
            if e.errno == 98:  # Address already in use
                announcer.announce(
                    f"Port {port} already in use",
                    ["Another service is using this port"]
                )
                print(f"⚠️  Port {port}: Already in use")
            else:
                print(f"❌ Port {port}: {e}")
    
    def start_all(self):
        """Start servers on all configured ports"""
        os.chdir('/home/ubuntu/claude/tournament_tracker')
        
        announcer.announce(
            "Starting multi-port servers",
            [f"Ports: {self.ports}"]
        )
        
        for port in self.ports:
            self.start_server_on_port(port)
        
        # Summary
        active_ports = list(self.servers.keys())
        if active_ports:
            announcer.announce(
                "Multi-port server ready",
                [f"Active ports: {active_ports}"]
            )
            
            print(f"\n🚀 Bonjour Multi-Port Server")
            print(f"📢 Self-announcing on {len(active_ports)} ports")
            for port in active_ports:
                print(f"   Port {port}: http://64.111.98.139:{port}/")
            
            # Keep running
            try:
                while True:
                    threading.Event().wait(60)
                    # Periodic health announcement
                    announcer.announce(
                        "Multi-port server healthy",
                        [f"Active ports: {active_ports}"]
                    )
            except KeyboardInterrupt:
                print("\n👋 Shutting down multi-port server")
                for server, thread in self.servers.values():
                    server.shutdown()
        else:
            print("❌ No servers could be started")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Bonjour Multi-Port Server')
    parser.add_argument('--ports', nargs='+', type=int, 
                       default=[80, 8080, 8081],
                       help='Ports to listen on')
    
    args = parser.parse_args()
    
    server = BonjourMultiServer(ports=args.ports)
    server.start_all()