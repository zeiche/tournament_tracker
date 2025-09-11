#!/usr/bin/env python3
"""
ACME Challenge Server for Let's Encrypt domain validation
Serves .well-known/acme-challenge/ files on port 80
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
from pathlib import Path

class ACMEHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Log the request
        print(f"📥 Request for: {self.path}")
        
        # Check if this is an ACME challenge request
        if self.path.startswith('/.well-known/acme-challenge/'):
            # Get the token from the path
            token = self.path.split('/')[-1]
            
            # Look for the challenge file
            challenge_dir = Path('/home/ubuntu/claude/tournament_tracker/.well-known/acme-challenge')
            challenge_dir.mkdir(parents=True, exist_ok=True)
            
            challenge_file = challenge_dir / token
            
            if challenge_file.exists():
                # Serve the challenge file
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                
                with open(challenge_file, 'rb') as f:
                    self.wfile.write(f.read())
                
                print(f"✅ Served challenge: {token}")
            else:
                # File not found
                self.send_error(404, f"Challenge not found: {token}")
                print(f"❌ Challenge not found: {token}")
        else:
            # For other requests, serve normally
            super().do_GET()

if __name__ == "__main__":
    # Must run on port 80 for Let's Encrypt
    PORT = 80
    
    # Change to the directory to serve
    os.chdir('/home/ubuntu/claude/tournament_tracker')
    
    print(f"🚀 ACME Challenge Server starting on port {PORT}")
    print(f"📁 Serving from: {os.getcwd()}")
    print(f"🔗 Challenge URL: http://64.111.98.139/.well-known/acme-challenge/")
    print(f"⚠️  Note: May need sudo for port 80")
    
    try:
        server = HTTPServer(('0.0.0.0', PORT), ACMEHandler)
        print(f"✅ Server ready for Let's Encrypt challenges")
        server.serve_forever()
    except PermissionError:
        print(f"❌ Permission denied for port 80. Try: sudo python3 {__file__}")
    except Exception as e:
        print(f"❌ Error: {e}")