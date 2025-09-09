#!/usr/bin/env python3
"""Ultra-simple TwiML responder for testing"""

from http.server import HTTPServer, BaseHTTPRequestHandler

class TwiMLHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Send response immediately
        self.send_response(200)
        self.send_header('Content-Type', 'text/xml')
        self.end_headers()
        
        # Minimal TwiML
        twiml = b'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hello from tournament tracker</Say>
</Response>'''
        
        self.wfile.write(twiml)
        print(f"✅ Received POST from {self.client_address[0]}")
    
    def do_GET(self):
        self.do_POST()  # Same response for GET
    
    def log_message(self, format, *args):
        print(f"{self.client_address[0]} - {format % args}")

if __name__ == "__main__":
    port = 8089
    server = HTTPServer(('0.0.0.0', port), TwiMLHandler)
    print(f"🚀 Simple TwiML server on port {port}")
    print(f"📍 Configure Twilio: http://64.111.98.139:{port}/")
    server.serve_forever()