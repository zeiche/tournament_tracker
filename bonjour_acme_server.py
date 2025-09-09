#!/usr/bin/env python3
"""
Bonjour-style ACME Challenge Server
Self-announces capabilities and serves Let's Encrypt challenges
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')

# Import the announcer
try:
    from polymorphic_core import announcer
except ImportError:
    from capability_announcer import CapabilityAnnouncer
    announcer = CapabilityAnnouncer("bonjour_acme_server")

class BonjourACMEHandler(SimpleHTTPRequestHandler):
    """Self-announcing ACME challenge handler"""
    
    def do_GET(self):
        # Announce the request
        announcer.announce(
            f"HTTP GET request received",
            [f"Path: {self.path}", f"From: {self.client_address[0]}"]
        )
        
        # Check if this is an ACME challenge request
        if self.path.startswith('/.well-known/acme-challenge/'):
            token = self.path.split('/')[-1]
            
            # Announce what we're looking for
            announcer.announce(
                "ACME challenge requested",
                [f"Token: {token}", "Searching for challenge file"]
            )
            
            # Look for the challenge file
            challenge_dir = Path('/home/ubuntu/claude/tournament_tracker/.well-known/acme-challenge')
            challenge_dir.mkdir(parents=True, exist_ok=True)
            challenge_file = challenge_dir / token
            
            if challenge_file.exists():
                # Announce success
                announcer.announce(
                    "ACME challenge found",
                    [f"Serving challenge for token: {token}"]
                )
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                
                with open(challenge_file, 'rb') as f:
                    content = f.read()
                    self.wfile.write(content)
                    
                print(f"✅ Served ACME challenge: {token}")
            else:
                # Announce failure
                announcer.announce(
                    "ACME challenge not found",
                    [f"No file for token: {token}"]
                )
                
                self.send_error(404, f"Challenge not found: {token}")
                print(f"❌ Challenge not found: {token}")
        else:
            # For other requests
            announcer.announce(
                "Non-ACME request",
                [f"Path: {self.path}"]
            )
            super().do_GET()
    
    def log_message(self, format, *args):
        """Override to use announcer for logging"""
        message = format % args
        announcer.announce(
            "HTTP request log",
            [message]
        )
        print(f"{self.client_address[0]} - {message}")

class BonjourACMEServer:
    """Self-announcing ACME challenge server"""
    
    def __init__(self, port=80):
        self.port = port
        self.server = None
        
        # Announce what we are
        announcer.announce(
            "Bonjour ACME Server",
            [
                "I serve ACME challenges for Let's Encrypt",
                f"I listen on port {port}",
                "I announce all requests and responses",
                "I help you get SSL certificates",
                "Place challenge files in .well-known/acme-challenge/",
                "I'll serve them at http://YOUR_IP/.well-known/acme-challenge/TOKEN",
                "Let's Encrypt will validate your domain ownership"
            ]
        )
    
    def start(self):
        """Start the server"""
        os.chdir('/home/ubuntu/claude/tournament_tracker')
        
        # Announce startup
        announcer.announce(
            "ACME server starting",
            [
                f"Port: {self.port}",
                f"Directory: {os.getcwd()}",
                f"URL: http://64.111.98.139/.well-known/acme-challenge/"
            ]
        )
        
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), BonjourACMEHandler)
            
            # Announce success
            announcer.announce(
                "ACME server ready",
                [
                    f"✅ Listening on port {self.port}",
                    "Ready for Let's Encrypt challenges",
                    "Place challenge files in .well-known/acme-challenge/"
                ]
            )
            
            print(f"🚀 Bonjour ACME Server ready on port {self.port}")
            print(f"📢 Self-announcing all activity")
            print(f"🔗 Challenge URL: http://64.111.98.139/.well-known/acme-challenge/")
            
            # Serve forever
            self.server.serve_forever()
            
        except PermissionError:
            # Announce permission error
            announcer.announce(
                "Permission denied",
                [
                    f"Cannot bind to port {self.port}",
                    "Try running with sudo",
                    f"sudo python3 {__file__}"
                ]
            )
            print(f"❌ Permission denied for port {self.port}")
            print(f"   Try: sudo python3 {__file__}")
            
        except Exception as e:
            # Announce other errors
            announcer.announce(
                "Server error",
                [f"Error: {e}"]
            )
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Create and start the Bonjour ACME server
    server = BonjourACMEServer(port=80)
    server.start()