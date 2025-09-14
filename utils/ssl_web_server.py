#!/usr/bin/env python3
"""
SSL Web Server Wrapper - Universal HTTP + HTTPS server

Automatically wraps any HTTP service with SSL support:
- HTTP on original port  
- HTTPS on port+1000 (e.g., 8088 -> 9088)
- Auto-generates self-signed certificates
- Zero configuration required
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ssl
import socket
import threading
import time
from http.server import HTTPServer
from typing import Optional, Callable, Any
import tempfile
import subprocess
from polymorphic_core import announcer

class SSLWebServer:
    """Universal SSL wrapper for any HTTP service"""
    
    def __init__(self, handler_class, http_port: int = 8088, hostname: str = "vpn.zilogo.com"):
        self.handler_class = handler_class
        self.http_port = http_port
        self.https_port = http_port + 1000  # HTTPS always +1000 from HTTP
        self.hostname = hostname
        
        self.http_server = None
        self.https_server = None
        self.http_thread = None
        self.https_thread = None
        
        # Generate SSL certificate
        self.cert_file, self.key_file = self._generate_ssl_cert()
        
        announcer.announce(
            f"SSL Web Server ({http_port})",
            [
                f"HTTP server on port {self.http_port}",
                f"HTTPS server on port {self.https_port}",
                f"Auto-generated SSL certificate for {hostname}",
                "Zero configuration SSL support",
                "Both protocols available simultaneously"
            ],
            [
                f"http://{hostname}:{http_port}/",
                f"https://{hostname}:{self.https_port}/",
                f"curl -k https://{hostname}:{self.https_port}/",
                f"curl http://{hostname}:{http_port}/"
            ]
        )
    
    def _generate_ssl_cert(self) -> tuple[str, str]:
        """Use Let's Encrypt certificates or fallback to self-signed"""
        # Try Let's Encrypt certificates first
        letsencrypt_cert = "/etc/letsencrypt/live/zilogo.com/fullchain.pem"
        letsencrypt_key = "/etc/letsencrypt/live/zilogo.com/privkey.pem"
        
        if os.path.exists(letsencrypt_cert) and os.path.exists(letsencrypt_key):
            print(f"🔐 Using Let's Encrypt certificates for {self.hostname}")
            print(f"📜 Certificate: {letsencrypt_cert}")
            print(f"🗝️  Private key: {letsencrypt_key}")
            return letsencrypt_cert, letsencrypt_key
        
        # Fallback to self-signed certificates
        cert_file = f"/tmp/ssl_cert_{self.http_port}.pem"
        key_file = f"/tmp/ssl_key_{self.http_port}.pem"
        
        # Generate certificate if it doesn't exist
        if not os.path.exists(cert_file):
            cmd = [
                "openssl", "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", key_file, "-out", cert_file,
                "-days", "365", "-nodes",
                "-subj", f"/CN={self.hostname}"
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"🔐 Generated self-signed SSL certificate for {self.hostname}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to generate SSL certificate: {e}")
                # Create dummy files as fallback
                with open(cert_file, 'w') as f:
                    f.write("# Dummy cert file\n")
                with open(key_file, 'w') as f:
                    f.write("# Dummy key file\n")
        
        return cert_file, key_file
    
    def start(self) -> bool:
        """Start both HTTP and HTTPS servers"""
        try:
            # Start HTTP server
            self.http_server = HTTPServer(('0.0.0.0', self.http_port), self.handler_class)
            self.http_thread = threading.Thread(
                target=self.http_server.serve_forever, 
                daemon=True,
                name=f"HTTP-{self.http_port}"
            )
            self.http_thread.start()
            
            # Start HTTPS server
            try:
                self.https_server = HTTPServer(('0.0.0.0', self.https_port), self.handler_class)
                
                # Wrap with SSL
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(self.cert_file, self.key_file)
                self.https_server.socket = context.wrap_socket(
                    self.https_server.socket, 
                    server_side=True
                )
                
                self.https_thread = threading.Thread(
                    target=self.https_server.serve_forever,
                    daemon=True, 
                    name=f"HTTPS-{self.https_port}"
                )
                self.https_thread.start()
                
                print(f"🌐 HTTP  server: http://{self.hostname}:{self.http_port}")
                print(f"🔒 HTTPS server: https://{self.hostname}:{self.https_port}")
                print(f"🔐 SSL certificate: {self.cert_file}")
                
                return True
                
            except Exception as e:
                print(f"⚠️  HTTPS failed ({e}), HTTP-only mode")
                print(f"🌐 HTTP server: http://{self.hostname}:{self.http_port}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to start servers: {e}")
            return False
    
    def stop(self):
        """Stop both servers"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
        
        if self.https_server:
            self.https_server.shutdown()
            self.https_server.server_close()
        
        print(f"🛑 Stopped HTTP/HTTPS servers ({self.http_port}/{self.https_port})")
    
    def wait(self):
        """Wait for servers to finish"""
        try:
            print("Press Ctrl+C to stop servers")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.stop()


def create_ssl_server(handler_class, port: int = 8088, hostname: str = "vpn.zilogo.com") -> SSLWebServer:
    """Create SSL-enabled web server with both HTTP and HTTPS"""
    return SSLWebServer(handler_class, port, hostname)


# Example usage
if __name__ == "__main__":
    from http.server import BaseHTTPRequestHandler
    
    class TestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {
                "message": "SSL Web Server Test",
                "protocol": "HTTPS" if self.server.socket.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) else "HTTP",
                "port": self.server.server_port,
                "path": self.path
            }
            
            import json
            self.wfile.write(json.dumps(response, indent=2).encode())
        
        def log_message(self, format, *args):
            pass  # Suppress logs
    
    # Test server
    server = create_ssl_server(TestHandler, 8088, "vpn.zilogo.com")
    
    if server.start():
        server.wait()
    else:
        print("❌ Failed to start test server")