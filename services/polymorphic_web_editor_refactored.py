#!/usr/bin/env python3
"""
polymorphic_web_editor_refactored.py - REFACTORED Universal mDNS-Driven Admin Panel

BEFORE: Direct imports of logger and error handler
AFTER: Uses service locator for all dependencies

Key changes:
1. Uses service locator for logger, error handler, config dependencies
2. Enhanced with 3-method pattern (ask/tell/do)
3. Works with local OR network services transparently
4. Can be distributed for scalable web editing
5. Same universal admin functionality as original

This demonstrates refactoring a complex user-facing service.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import html
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import threading
import time

from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service
from dynamic_switches import announce_switch

try:
    from polymorphic_core.process_management import BaseProcessManager
except ImportError:
    BaseProcessManager = object

class RefactoredPolymorphicWebEditorProcessManager(BaseProcessManager):
    """Process manager for Refactored Polymorphic Web Editor"""
    
    SERVICE_NAME = "PolymorphicWebEditor (Refactored)"
    PROCESSES = ["services/polymorphic_web_editor_refactored.py"]
    PORTS = [8081]
    
    def get_process_patterns(self) -> List[str]:
        return ["polymorphic_web_editor_refactored.py"]

class RefactoredPolymorphicWebEditor:
    """
    REFACTORED Universal web editor using service locator pattern.
    
    This version:
    - Uses service locator for all dependencies (logger, error handler, config)
    - Enhanced with 3-method pattern for queries and operations
    - Can operate over network for distributed web editing
    - Same universal admin functionality as original
    """
    
    def __init__(self, prefer_network: bool = False, port: int = 8081):
        self.prefer_network = prefer_network
        self.port = port
        self._logger = None
        self._error_handler = None
        self._config = None
        self._database = None
        
        self.server = None
        self.discovered_services = {}
        self.last_discovery = 0
        self.running = False
        
        # Announce capabilities
        announcer.announce(
            "Polymorphic Web Editor (Refactored)",
            [
                "REFACTORED: Uses service locator for dependencies",
                "Universal web interface with 3-method pattern",
                "ask('discovered services') - query available services",
                "tell('html', service_data) - generate dynamic UI",
                "do('start server') - manage web server operations",
                "Distributed web editing with service discovery"
            ],
            [
                "web_editor.ask('service capabilities')",
                "web_editor.tell('html', service_list)",
                "web_editor.do('refresh services')",
                "Works with local OR network logger/database services"
            ]
        )
        
        # Announce as a switch
        announce_switch("web", "START universal web editor (adapts to any mDNS service)", self._handle_switch)
    
    @property
    def logger(self):
        """Lazy-loaded logger service via service locator"""
        if self._logger is None:
            self._logger = get_service("logger", self.prefer_network)
        return self._logger
    
    @property
    def error_handler(self):
        """Lazy-loaded error handler service via service locator"""
        if self._error_handler is None:
            self._error_handler = get_service("error_handler", self.prefer_network)
        return self._error_handler
    
    @property
    def config(self):
        """Lazy-loaded config service via service locator"""
        if self._config is None:
            self._config = get_service("config", self.prefer_network)
        return self._config
    
    @property
    def database(self):
        """Lazy-loaded database service via service locator"""
        if self._database is None:
            self._database = get_service("database", self.prefer_network)
        return self._database
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query web editor using natural language.
        
        Examples:
            ask("discovered services")
            ask("service capabilities")
            ask("server status")
            ask("active connections")
        """
        query_lower = query.lower().strip()
        
        # Log the query
        if self.logger:
            try:
                self.logger.info(f"Web editor query: {query}")
            except:
                pass
        
        try:
            if "discovered services" in query_lower or "services" in query_lower:
                return self._get_discovered_services()
            
            elif "capabilities" in query_lower:
                return self._get_service_capabilities()
            
            elif "server status" in query_lower or "status" in query_lower:
                return self._get_server_status()
            
            elif "connections" in query_lower:
                return self._get_active_connections()
            
            elif "stats" in query_lower:
                return self._get_web_stats()
            
            else:
                return {"error": f"Don't know how to handle query: {query}"}
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "MEDIUM")
                except:
                    pass
            return {"error": f"Web editor query failed: {str(e)}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """
        Format web editor data for output.
        
        Formats: html, json, text, dashboard, service_list
        """
        if data is None:
            data = {}
        
        try:
            if format_type == "html":
                return self._generate_html(data)
            
            elif format_type == "json":
                return json.dumps(data, indent=2, default=str)
            
            elif format_type == "text":
                return self._format_text(data)
            
            elif format_type == "dashboard":
                return self._generate_dashboard_html(data)
            
            elif format_type == "service_list":
                return self._generate_service_list_html(data)
            
            else:
                return str(data)
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "LOW")
                except:
                    pass
            return f"Format error: {e}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform web editor operations using natural language.
        
        Examples:
            do("start server")
            do("stop server")
            do("refresh services")
            do("clear cache")
        """
        action_lower = action.lower().strip()
        
        # Log the action
        if self.logger:
            try:
                self.logger.info(f"Web editor action: {action}")
            except:
                pass
        
        try:
            if "start server" in action_lower:
                return self._start_server()
            
            elif "stop server" in action_lower:
                return self._stop_server()
            
            elif "refresh services" in action_lower or "discover" in action_lower:
                return self._refresh_services()
            
            elif "clear cache" in action_lower:
                return self._clear_cache()
            
            elif "restart server" in action_lower:
                return self._restart_server()
            
            else:
                return {"error": f"Don't know how to: {action}"}
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "HIGH")
                except:
                    pass
            return {"error": f"Web editor action failed: {str(e)}"}
    
    # Service discovery methods
    def _get_discovered_services(self) -> Dict:
        """Get currently discovered services"""
        # Refresh if stale
        if time.time() - self.last_discovery > 30:  # 30 seconds
            self._refresh_services()
        
        return {
            "services": self.discovered_services,
            "count": len(self.discovered_services),
            "last_updated": self.last_discovery
        }
    
    def _get_service_capabilities(self) -> Dict:
        """Get capabilities of all discovered services"""
        capabilities = {}
        
        for service_name, service_data in self.discovered_services.items():
            capabilities[service_name] = service_data.get('capabilities', [])
        
        return {
            "capabilities": capabilities,
            "total_services": len(capabilities)
        }
    
    def _get_server_status(self) -> Dict:
        """Get web server status"""
        return {
            "running": self.running,
            "port": self.port,
            "server_active": self.server is not None,
            "discovered_services": len(self.discovered_services)
        }
    
    def _get_active_connections(self) -> Dict:
        """Get active connections (simplified)"""
        return {
            "active_connections": 0,  # Would track actual connections
            "total_requests": 0,      # Would track request count
            "uptime": time.time() - self.last_discovery if self.running else 0
        }
    
    def _get_web_stats(self) -> Dict:
        """Get web editor statistics"""
        return {
            "port": self.port,
            "running": self.running,
            "services_discovered": len(self.discovered_services),
            "last_discovery": self.last_discovery,
            "prefer_network": self.prefer_network
        }
    
    # Action implementation methods
    def _start_server(self) -> Dict:
        """Start the web server"""
        if self.running:
            return {"action": "start_server", "status": "already_running", "port": self.port}
        
        try:
            # Create HTTP server
            self.server = HTTPServer(('0.0.0.0', self.port), self._create_request_handler())
            
            # Start in background thread
            server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            server_thread.start()
            
            self.running = True
            
            if self.logger:
                try:
                    self.logger.info(f"Web editor server started on port {self.port}")
                except:
                    pass
            
            return {
                "action": "start_server",
                "status": "started",
                "port": self.port,
                "url": f"http://localhost:{self.port}"
            }
            
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "HIGH")
                except:
                    pass
            return {"action": "start_server", "status": "failed", "error": str(e)}
    
    def _stop_server(self) -> Dict:
        """Stop the web server"""
        if not self.running:
            return {"action": "stop_server", "status": "not_running"}
        
        try:
            if self.server:
                self.server.shutdown()
                self.server = None
            
            self.running = False
            
            if self.logger:
                try:
                    self.logger.info("Web editor server stopped")
                except:
                    pass
            
            return {"action": "stop_server", "status": "stopped"}
            
        except Exception as e:
            return {"action": "stop_server", "status": "failed", "error": str(e)}
    
    def _refresh_services(self) -> Dict:
        """Refresh discovered services"""
        try:
            # Use the announcer to discover services
            self.discovered_services = announcer.discover_services()
            self.last_discovery = time.time()
            
            if self.logger:
                try:
                    self.logger.info(f"Refreshed services: {len(self.discovered_services)} found")
                except:
                    pass
            
            return {
                "action": "refresh_services",
                "status": "success",
                "services_found": len(self.discovered_services),
                "services": list(self.discovered_services.keys())
            }
            
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "MEDIUM")
                except:
                    pass
            return {"action": "refresh_services", "status": "failed", "error": str(e)}
    
    def _clear_cache(self) -> Dict:
        """Clear service discovery cache"""
        old_count = len(self.discovered_services)
        self.discovered_services.clear()
        self.last_discovery = 0
        
        return {
            "action": "clear_cache",
            "cleared_services": old_count
        }
    
    def _restart_server(self) -> Dict:
        """Restart the web server"""
        stop_result = self._stop_server()
        time.sleep(1)  # Brief pause
        start_result = self._start_server()
        
        return {
            "action": "restart_server",
            "stop_result": stop_result,
            "start_result": start_result
        }
    
    # HTML generation methods
    def _generate_html(self, data: Dict) -> str:
        """Generate HTML for data"""
        if "services" in data:
            return self._generate_service_list_html(data)
        else:
            return self._generate_dashboard_html(data)
    
    def _generate_dashboard_html(self, data: Dict) -> str:
        """Generate dashboard HTML"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Polymorphic Web Editor (Refactored)</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .services {{ margin-top: 20px; }}
                .service {{ border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .capability {{ background: #e7f3ff; padding: 2px 5px; margin: 2px; border-radius: 3px; display: inline-block; }}
                .refactored {{ color: #007acc; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌐 Polymorphic Web Editor <span class="refactored">(Refactored)</span></h1>
                <p>Universal admin interface that adapts to any mDNS service</p>
                <p><strong>Enhancement:</strong> Now uses service locator for distributed operation</p>
                <p>Running on port {self.port} | Services: {len(self.discovered_services)} | 
                   Mode: {'Network-first' if self.prefer_network else 'Local-first'}</p>
            </div>
            
            <div class="services">
                <h2>Discovered Services</h2>
                {self._generate_services_html()}
            </div>
            
            <div style="margin-top: 20px;">
                <button onclick="location.reload()">Refresh</button>
                <button onclick="fetch('/api/refresh-services')">Discover Services</button>
            </div>
        </body>
        </html>
        """
        return html_content
    
    def _generate_service_list_html(self, data: Dict) -> str:
        """Generate service list HTML"""
        services_html = ""
        
        for service_name, service_data in data.get("services", {}).items():
            capabilities_html = ""
            for cap in service_data.get('capabilities', []):
                capabilities_html += f'<span class="capability">{html.escape(cap)}</span>'
            
            host_info = f"{service_data.get('host', 'unknown')}:{service_data.get('port', 'unknown')}"
            
            services_html += f"""
            <div class="service">
                <h3>{html.escape(service_name)}</h3>
                <p><strong>Host:</strong> {html.escape(host_info)}</p>
                <p><strong>Capabilities:</strong></p>
                <div>{capabilities_html}</div>
            </div>
            """
        
        return services_html or "<p>No services discovered yet. Click 'Discover Services' to refresh.</p>"
    
    def _generate_services_html(self) -> str:
        """Generate HTML for discovered services"""
        return self._generate_service_list_html({"services": self.discovered_services})
    
    def _format_text(self, data: Dict) -> str:
        """Format as plain text"""
        if "services" in data:
            lines = [f"Discovered Services ({len(data['services'])}):", "=" * 40]
            for service_name, service_data in data["services"].items():
                lines.append(f"• {service_name} at {service_data.get('host', 'unknown')}:{service_data.get('port', 'unknown')}")
                for cap in service_data.get('capabilities', [])[:3]:  # First 3 capabilities
                    lines.append(f"  - {cap}")
            return "\n".join(lines)
        
        return str(data)
    
    # HTTP Request Handler
    def _create_request_handler(self):
        """Create HTTP request handler class"""
        web_editor = self
        
        class RefactoredWebEditorHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                try:
                    if self.path == '/':
                        # Main dashboard
                        services_data = web_editor._get_discovered_services()
                        html_content = web_editor.tell("dashboard", services_data)
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(html_content.encode())
                    
                    elif self.path == '/api/services':
                        # API endpoint for services
                        services_data = web_editor._get_discovered_services()
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(services_data, default=str).encode())
                    
                    elif self.path == '/api/refresh-services':
                        # Refresh services
                        result = web_editor._refresh_services()
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(result).encode())
                    
                    else:
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write(b'Not Found')
                        
                except Exception as e:
                    if web_editor.error_handler:
                        try:
                            web_editor.error_handler.handle_exception(e, "MEDIUM")
                        except:
                            pass
                    
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(f'Server Error: {e}'.encode())
            
            def log_message(self, format, *args):
                # Suppress default logging, use our logger instead
                if web_editor.logger:
                    try:
                        web_editor.logger.info(f"Web request: {format % args}")
                    except:
                        pass
        
        return RefactoredWebEditorHandler
    
    def _handle_switch(self) -> Dict:
        """Handle switch command"""
        if not self.running:
            start_result = self._start_server()
            return {
                "switch": "web",
                "action": "started",
                "result": start_result
            }
        else:
            return {
                "switch": "web", 
                "status": "already_running",
                "port": self.port
            }

# Create service instances
web_editor = RefactoredPolymorphicWebEditor(prefer_network=False)  # Local-first
web_editor_network = RefactoredPolymorphicWebEditor(prefer_network=True)  # Network-first

# Process manager instance
web_editor_process_manager = RefactoredPolymorphicWebEditorProcessManager()

if __name__ == "__main__":
    # Test the refactored web editor service
    print("🧪 Testing Refactored Polymorphic Web Editor")
    
    # Test local-first service
    print("\n1. Testing local-first web editor:")
    editor_local = RefactoredPolymorphicWebEditor(prefer_network=False, port=8082)
    
    # Test service discovery
    services = editor_local.ask("discovered services")
    print(f"Services: {editor_local.tell('text', services)}")
    
    # Test server operations
    start_result = editor_local.do("start server")
    print(f"Start server: {start_result}")
    
    # Test capabilities
    capabilities = editor_local.ask("service capabilities")
    print(f"Capabilities: {len(capabilities.get('capabilities', {}))} services with capabilities")
    
    # Test network-first service
    print("\n2. Testing network-first web editor:")
    editor_network = RefactoredPolymorphicWebEditor(prefer_network=True, port=8083)
    
    status = editor_network.ask("server status")
    print(f"Status: {editor_network.tell('json', status)}")
    
    print("\n✅ Refactored web editor test complete!")
    print("💡 Same universal admin interface, but now with service locator and distributed capabilities!")
    
    # Keep servers running briefly for testing
    time.sleep(2)
    
    # Clean up
    editor_local.do("stop server")
    editor_network.do("stop server")