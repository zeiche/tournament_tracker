#!/usr/bin/env python3
"""
Interactive Web Service Daemon - Background service for persistent browser sessions
Now uses ManagedService for unified service identity.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.interactive_web_service_daemon")

import asyncio
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

from polymorphic_core.service_identity import ManagedService
from services.interactive_web_service import interactive_web_service
from logging_services.polymorphic_log_manager import PolymorphicLogManager
from polymorphic_core.visualizable import MediaFile
from polymorphic_core import announcer

class InteractiveWebRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler for Interactive Web Service API"""
    
    def do_POST(self):
        """Handle POST requests for web automation tasks"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            action = request_data.get('action')
            params = request_data.get('params', {})
            
            if action == 'bogus_email_test':
                # Run the bogus email test in background
                threading.Thread(target=self._run_bogus_email_test, args=(params,), daemon=True).start()
                response = {'status': 'started', 'message': 'Bogus email test started in background'}
            
            elif action == 'create_session':
                url = params.get('url', 'https://example.com')
                result = interactive_web_service.ask(f'create session for {url}')
                response = result
            
            elif action == 'screenshot':
                handle = params.get('handle')
                if handle:
                    result = interactive_web_service.ask(f'screenshot handle {handle}')
                    if 'screenshot' in result:
                        # Save screenshot and return path instead of bytes
                        path = f'screenshot_{handle}.png'
                        interactive_web_service.tell('file', result, path=path)
                        result['screenshot_path'] = path
                        del result['screenshot']  # Remove binary data for JSON response
                    response = result
                else:
                    response = {'error': 'Handle required'}
            
            elif action == 'list_sessions':
                response = interactive_web_service.ask('list sessions')
            
            else:
                response = {'error': f'Unknown action: {action}'}
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def _run_bogus_email_test(self, params):
        """Run the bogus email test in background thread"""
        try:
            print('📧 Starting bogus email test...')
            
            # Create session
            result = interactive_web_service.ask('create session for https://www.twilio.com/login')
            if 'handle' not in result:
                print(f'❌ Session failed: {result}')
                return
            
            handle = result['handle']
            print(f'✅ Handle: {handle}')
            
            # Enter bogus email
            email_result = interactive_web_service.do(f'type "grinful@giggles.com" in input[type=email] in handle {handle}')
            print(f'📧 Email entry: {email_result.get("status", email_result.get("error"))}')
            
            time.sleep(2)
            
            # Try alternative selectors if first fails
            if 'error' in email_result:
                selectors = ['input[name=email]', 'input[id=email]', '#email', '[placeholder*=email]']
                for selector in selectors:
                    email_result = interactive_web_service.do(f'type "grinful@giggles.com" in {selector} in handle {handle}')
                    if 'status' in email_result:
                        print(f'✅ Email entered with {selector}')
                        break
            
            # Click continue
            click_result = interactive_web_service.do(f'click button with text Continue in handle {handle}')
            print(f'🖱️ Continue click: {click_result.get("status", click_result.get("error"))}')
            
            # Try alternatives if first fails
            if 'error' in click_result:
                alternatives = ['CONTINUE', 'Next', 'Submit', 'Log in']
                for alt in alternatives:
                    click_result = interactive_web_service.do(f'click button with text {alt} in handle {handle}')
                    if 'status' in click_result:
                        print(f'✅ Clicked {alt}')
                        break
            
            time.sleep(4)  # Wait for page load
            
            # Get final page info
            info = interactive_web_service.ask(f'info for handle {handle}')
            print(f'📍 Final URL: {info["url"]}')
            print(f'📄 Final Title: {info["title"]}')
            
            # Screenshot
            screenshot = interactive_web_service.ask(f'screenshot handle {handle}')
            if 'screenshot' in screenshot:
                path = f'twilio_bogus_email_result.png'
                interactive_web_service.tell('file', screenshot, path=path)
                
                log_manager = PolymorphicLogManager()
                media = MediaFile(path, f'Twilio response to bogus email grinful@giggles.com')
                log_manager.log('INFO', f'📧❌ Twilio bogus email response (handle: {handle})', media, source='bogus_email_test')
                
                print(f'✅ Screenshot saved and logged: {len(screenshot["screenshot"])} bytes')
                print('✅ Viewable at http://10.0.0.1:8081/logs')
            else:
                print(f'❌ Screenshot failed: {screenshot}')
                
        except Exception as e:
            print(f'❌ Bogus email test error: {e}')
    
    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass

class InteractiveWebServiceDaemonManaged(ManagedService):
    """
    Daemon service for Interactive Web automation with unified service identity.
    Provides background web automation services with process tracking.
    """
    
    def __init__(self, port=8083):
        super().__init__("interactive-web-daemon", "tournament-interactive-web-daemon")
        self.port = port
        self.httpd = None
        
        # Announce this daemon service
        announcer.announce(
            "Interactive Web Service Daemon",
            [
                "HTTP API for non-blocking browser automation",
                "Persistent browser sessions with REST interface",
                f"Running on port {port}",
                "Supports background automation tasks"
            ]
        )
    
    def run(self):
        """Run the HTTP server daemon"""
        print(f"🚀 Starting Interactive Web Service Daemon on port {self.port}")
        
        server_address = ('', self.port)
        self.httpd = HTTPServer(server_address, InteractiveWebRequestHandler)
        
        print(f"✅ Interactive Web Service Daemon listening on http://localhost:{self.port}")
        print("📋 Available endpoints:")
        print("   POST /  - Action API (JSON)")
        print("     Actions: create_session, screenshot, list_sessions, bogus_email_test")
        
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Interactive Web Service Daemon")
            if self.httpd:
                self.httpd.shutdown()


def main():
    """Main function for running as a managed service"""
    import argparse
    parser = argparse.ArgumentParser(description='Interactive Web Service Daemon')
    parser.add_argument('--port', type=int, default=8083, help='Port to run on (default: 8083)')
    args = parser.parse_args()
    
    with InteractiveWebServiceDaemonManaged(args.port) as daemon:
        daemon.run()


if __name__ == '__main__':
    # Import the persistent interactive service instead
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from persistent_interactive_service import main
    main()