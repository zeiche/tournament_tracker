#!/usr/bin/env python3
"""
Simple streaming media server with JSON metadata for testing
"""

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polymorphic_core.execution_guard import require_go_py
require_go_py("test_streaming_server")

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class StreamingHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler that streams JSON data with media metadata"""
    
    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            # Simulate streaming media metadata
            for i in range(10):
                data = {
                    'timestamp': time.time(),
                    'frame': i,
                    'duration': i + 1,
                    'media_type': 'video/mp4',
                    'size_bytes': 1024 * (i + 1),
                    'status': 'streaming'
                }
                
                json_data = json.dumps(data) + '\n'
                self.wfile.write(json_data.encode())
                self.wfile.flush()
                time.sleep(1)
            
            # Final metadata
            final_data = {
                'timestamp': time.time(),
                'status': 'complete',
                'total_duration': 10,
                'total_size': 10240,
                'media_type': 'video/mp4'
            }
            
            json_data = json.dumps(final_data) + '\n'
            self.wfile.write(json_data.encode())
            
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            status = {
                'server': 'test_streaming_server',
                'status': 'active',
                'endpoints': ['/stream', '/status'],
                'description': 'Simple streaming server for testing JSON media metadata'
            }
            
            self.wfile.write(json.dumps(status, indent=2).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

def start_server():
    """Start the streaming server in background"""
    server = HTTPServer(('localhost', 8090), StreamingHandler)
    print(f"🎬 Test streaming server started on http://localhost:8090")
    print(f"📡 Endpoints: /stream (streaming JSON), /status (server info)")
    server.serve_forever()

if __name__ == '__main__':
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    print("🎬 Test Streaming Server")
    print("📡 Visit http://localhost:8090/stream for streaming JSON metadata")
    print("📊 Visit http://localhost:8090/status for server status")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")