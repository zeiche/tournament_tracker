#!/usr/bin/env python3
"""
Polymorphic Web Editor - Universal mDNS-Driven Admin Panel

Instead of being hardcoded for tournaments/organizations, this editor:
1. Discovers services via mDNS announcements
2. Generates dynamic UI based on service capabilities  
3. Routes requests to discovered services
4. Creates a universal admin interface for any announced service

This is the future - the web editor adapts to whatever services are available!
"""

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.polymorphic_web_editor")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from http.server import HTTPServer, BaseHTTPRequestHandler
from http.server import BaseHTTPRequestHandler
import ssl
from socketserver import ThreadingTCPServer
import html
import urllib.parse
import json
import re
import socket
import hashlib
import base64
import struct
import threading
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET

from polymorphic_core import announcer
from polymorphic_core.service_identity import ManagedService
from logging_services.polymorphic_log_manager import PolymorphicLogManager
from utils.error_handler import handle_errors, handle_exception, ErrorSeverity

# Initialize logger at module level
log_manager = PolymorphicLogManager()
def info(message): log_manager.do(f"log info {message}")
def warning(message): log_manager.do(f"log warning {message}")
def error(message): log_manager.do(f"log error {message}")
from polymorphic_core import announcer

try:
    from polymorphic_core.process_management import BaseProcessManager
except ImportError:
    BaseProcessManager = object

class PolymorphicWebEditorProcessManager(BaseProcessManager):
    """Process manager for Polymorphic Web Editor"""
    
    SERVICE_NAME = "PolymorphicWebEditor"
    PROCESSES = ["services/polymorphic_web_editor.py"]
    PORTS = [8081]
    
    def get_process_patterns(self) -> List[str]:
        return ["polymorphic_web_editor.py"]

class PolymorphicWebEditor:
    """
    Universal web editor that discovers services via mDNS and creates interfaces dynamically.
    No hardcoded knowledge of tournaments, organizations, or any specific domain.
    """
    
    def __init__(self):
        # Announce ourselves
        announcer.announce(
            "Universal Web Editor Service",
            [
                "Universal web interface that adapts to any mDNS service",
                "Discovers services dynamically via Bonjour announcements", 
                "Generates UI automatically based on service capabilities",
                "No hardcoded domain knowledge - works with any service",
                "Self-updating admin panel for the entire ecosystem"
            ],
            [
                "Visit http://localhost:8081 for universal admin interface",
                "Services appear/disappear automatically as they announce",
                "Forms generated from mDNS capability descriptions",
                "Works with tournaments, players, audio, Twilio, anything!"
            ]
        )
    
    def ask(self, query: str) -> Any:
        """Ask about discovered services or generate interface data"""
        query_lower = query.lower().strip()
        
        if query_lower in ['services', 'discovered services', 'available services']:
            return self._get_discovered_services()
        elif query_lower in ['interface', 'ui', 'generate interface']:
            return self._generate_interface_data()
        elif query_lower.startswith('service '):
            service_name = query[8:].strip()
            return self._get_service_info(service_name)
        else:
            # Try to route query to appropriate discovered service
            return self._route_query(query)
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format tournament data instead of services"""
        if format.lower() == 'html':
            return self._render_tournament_html()
        elif format.lower() == 'json':
            return self._get_tournament_json()
        else:
            return self._get_tournament_summary()
    
    def _render_tournament_html(self) -> str:
        """Render tournament data using the pre-made tournament tracker template"""
        try:
            with open('templates/index.html', 'r') as f:
                return f.read()
        except Exception as e:
            return f"<h1>Error loading tournament template: {e}</h1>"
    
    def _generate_tournament_interface_data(self, tournament_data: Dict) -> Dict:
        """Convert tournament data to interface format"""
        interface_data = {
            'services': [],
            'categories': {},
            'total_services': len(tournament_data)
        }
        
        for service_name, service_data in tournament_data.items():
            service_info = {
                'name': service_name,
                'host': '🏆 tournament-data',
                'port': 0,
                'capabilities': service_data.get('capabilities', []),
                'examples': service_data.get('examples', []),
                'category': self._categorize_tournament_service(service_name)
            }
            
            interface_data['services'].append(service_info)
            
            # Group by category
            category = service_info['category']
            if category not in interface_data['categories']:
                interface_data['categories'][category] = []
            interface_data['categories'][category].append(service_info)
        
        return interface_data
    
    def _categorize_tournament_service(self, name: str) -> str:
        """Categorize tournament services"""
        name_lower = name.lower()
        if 'tournament' in name_lower:
            return 'Tournaments'
        elif 'player' in name_lower:
            return 'Players'
        elif 'organization' in name_lower:
            return 'Organizations'
        else:
            return 'Tournament Data'
    
    def _get_tournament_json(self) -> str:
        """Get tournament data as JSON"""
        return json.dumps(self._get_tournament_data(), indent=2)
    
    def _get_tournament_summary(self) -> str:
        """Get tournament data summary"""
        data = self._get_tournament_data()
        summary = []
        for name, info in data.items():
            capabilities = info.get('capabilities', [])
            summary.append(f"{name}: {', '.join(capabilities[:2])}")
        return "\n".join(summary)
    
    def do(self, action: str) -> Any:
        """Route actions to discovered services"""
        action_lower = action.lower().strip()
        
        if action_lower in ['refresh', 'discover', 'scan']:
            # Force rediscovery of services
            return self._refresh_services()
        elif action_lower.startswith('call '):
            # Direct service call: "call Database Service ask top 10 players"
            return self._call_service(action[5:])
        else:
            # Try to route to appropriate service
            return self._route_action(action)
    
    def _get_discovered_services(self) -> Dict:
        """Get tournament data instead of services"""
        return self._get_tournament_data()
    
    def _get_tournament_data(self) -> Dict:
        """Get tournament, player, and organization data"""
        try:
            from utils.database_service_refactored import database_service
            
            # Get recent tournaments
            recent_tournaments = database_service.ask("SELECT * FROM tournaments ORDER BY date DESC LIMIT 10")
            
            # Get top players
            top_players = database_service.ask("""
                SELECT name, SUM(points) as total_points, COUNT(*) as events
                FROM tournament_results tr 
                JOIN tournaments t ON tr.tournament_id = t.id 
                GROUP BY name 
                ORDER BY total_points DESC 
                LIMIT 10
            """)
            
            # Get organizations
            organizations = database_service.ask("SELECT * FROM organizations LIMIT 10")
            
            # Format as service-like data for the existing UI
            tournament_services = {
                'RecentTournaments': {
                    'capabilities': [f"{len(recent_tournaments) if recent_tournaments else 0} recent tournaments"],
                    'data': recent_tournaments or [],
                    'examples': ['View tournament details', 'Check attendance']
                },
                'TopPlayers': {
                    'capabilities': [f"Top {len(top_players) if top_players else 0} players by points"],
                    'data': top_players or [],
                    'examples': ['View player stats', 'Tournament history'] 
                },
                'Organizations': {
                    'capabilities': [f"{len(organizations) if organizations else 0} tournament organizers"],
                    'data': organizations or [],
                    'examples': ['Contact info', 'Tournament history']
                }
            }
            
            return tournament_services
            
        except Exception as e:
            return {
                'TournamentError': {
                    'capabilities': [f'Error loading tournament data: {str(e)}'],
                    'data': [],
                    'examples': ['Check database connection']
                }
            }
    
    def _get_service_info(self, service_name: str) -> Optional[Dict]:
        """Get info about a specific service"""
        services = self._get_discovered_services()
        
        # Try exact match first
        for name, data in services.items():
            if service_name.lower() in name.lower():
                return data
        
        return None
    
    def _generate_interface_data(self) -> Dict:
        """Generate data needed to create dynamic web interface"""
        services = self._get_discovered_services()
        interface_data = {
            'services': [],
            'categories': {},
            'total_services': len(services)
        }
        
        for service_name, service_data in services.items():
            service_info = {
                'name': service_name,
                'host': service_data.get('host', 'unknown'),
                'port': service_data.get('port', 0),
                'capabilities': service_data.get('capabilities', []),
                'examples': service_data.get('examples', []),
                'category': self._categorize_service(service_name, service_data)
            }
            
            interface_data['services'].append(service_info)
            
            # Group by category
            category = service_info['category']
            if category not in interface_data['categories']:
                interface_data['categories'][category] = []
            interface_data['categories'][category].append(service_info)
        
        return interface_data
    
    def _categorize_service(self, name: str, data: Dict) -> str:
        """Automatically categorize services for better UI organization"""
        name_lower = name.lower()
        
        if 'audio' in name_lower or 'tts' in name_lower or 'transcription' in name_lower:
            return 'Audio Services'
        elif 'twilio' in name_lower or 'phone' in name_lower or 'sms' in name_lower:
            return 'Telephony Services'
        elif 'discord' in name_lower:
            return 'Chat Services' 
        elif 'database' in name_lower or 'model' in name_lower:
            return 'Data Services'
        elif 'process' in name_lower or 'manager' in name_lower:
            return 'System Services'
        elif 'web' in name_lower or 'editor' in name_lower:
            return 'Web Services'
        else:
            return 'Other Services'
    
    def _render_services_html(self, services_data: Dict) -> str:
        """Generate dynamic HTML interface based on discovered services"""
        interface_data = self._generate_interface_data()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Polymorphic Web Editor - Universal Admin</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #e0e0e0; }}
                h1 {{ color: #4CAF50; }}
                h2 {{ color: #2196F3; border-bottom: 1px solid #444; padding-bottom: 5px; }}
                .service-card {{ 
                    background: #2d2d2d; border-radius: 8px; padding: 15px; margin: 10px 0;
                    border-left: 4px solid #4CAF50;
                }}
                .service-name {{ font-size: 18px; font-weight: bold; color: #4CAF50; }}
                .service-host {{ color: #888; font-size: 12px; }}
                .capabilities {{ margin: 10px 0; }}
                .capability {{ 
                    background: #1e1e1e; padding: 5px 10px; margin: 2px 5px; 
                    border-radius: 15px; display: inline-block; font-size: 12px;
                }}
                .examples {{ margin-top: 10px; }}
                .example {{ 
                    background: #0d47a1; color: white; padding: 3px 8px; 
                    border-radius: 12px; font-family: monospace; font-size: 11px;
                    display: inline-block; margin: 2px;
                }}
                .category {{ margin: 20px 0; }}
                .stats {{ 
                    background: #333; padding: 10px; border-radius: 5px; 
                    text-align: center; margin: 20px 0;
                }}
                .refresh-btn {{ 
                    background: #4CAF50; color: white; padding: 10px 20px; 
                    border: none; border-radius: 5px; cursor: pointer;
                }}
            </style>
        </head>
        <body>
            <h1>🌐 Polymorphic Web Editor</h1>
            <p><em>Universal Admin Panel - Automatically adapts to any mDNS service</em></p>
            
            <div class="stats">
                <strong>{interface_data['total_services']} Services Discovered</strong> via mDNS
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Discovery</button>
            </div>
        """
        
        # Render services by category
        for category, services in interface_data['categories'].items():
            html_content += f'<div class="category"><h2>{category} ({len(services)})</h2>'
            
            for service in services:
                html_content += f"""
                <div class="service-card">
                    <div class="service-name">{html.escape(service['name'])}</div>
                    <div class="service-host">📡 {service['host']}:{service['port']}</div>
                    
                    <div class="capabilities">
                        <strong>Capabilities:</strong><br>
                """
                
                for capability in service['capabilities']:
                    html_content += f'<span class="capability">{html.escape(capability)}</span>'
                
                if service['examples']:
                    html_content += '</div><div class="examples"><strong>Examples:</strong><br>'
                    for example in service['examples']:
                        html_content += f'<code class="example">{html.escape(example)}</code>'
                
                html_content += '</div></div>'
            
            html_content += '</div>'
        
        html_content += """
            <hr style="margin: 30px 0; border-color: #444;">
            <p><em>This interface automatically updates as services announce/leave via mDNS. 
            No hardcoded knowledge of tournaments, players, or any specific domain.</em></p>
            </body>
            </html>
        """
        
        return html_content
    
    def _route_query(self, query: str) -> Any:
        """Route query to the most appropriate discovered service"""
        services = self._get_discovered_services()
        
        # Simple routing based on query keywords
        query_lower = query.lower()
        
        for service_name, service_data in services.items():
            for capability in service_data.get('capabilities', []):
                if any(word in capability.lower() for word in query_lower.split()):
                    # Found matching service, try to route
                    service = announcer.find_service(service_name)
                    if service and hasattr(service, 'ask'):
                        try:
                            return service.ask(query)
                        except:
                            pass
        
        return f"No suitable service found for query: {query}"
    
    def _route_action(self, action: str) -> Any:
        """Route action to the most appropriate discovered service"""
        services = self._get_discovered_services()
        
        # Try to find service that can handle this action
        for service_name, service_data in services.items():
            service = announcer.find_service(service_name)
            if service and hasattr(service, 'do'):
                try:
                    return service.do(action)
                except:
                    continue
        
        return f"No service could handle action: {action}"
    
    def _call_service(self, call_string: str) -> Any:
        """Direct service call: 'Database Service ask top 10 players'"""
        parts = call_string.split(' ', 2)
        if len(parts) < 3:
            return "Usage: call <ServiceName> <method> <args>"
        
        service_name, method, args = parts[0], parts[1], parts[2]
        
        service = announcer.find_service(service_name)
        if not service:
            return f"Service not found: {service_name}"
        
        if method == 'ask' and hasattr(service, 'ask'):
            return service.ask(args)
        elif method == 'do' and hasattr(service, 'do'):
            return service.do(args)
        elif method == 'tell' and hasattr(service, 'tell'):
            return service.tell(args)
        else:
            return f"Method {method} not available on {service_name}"
    
    def _refresh_services(self) -> str:
        """Force rediscovery of services"""
        # The announcer will automatically discover new services
        services = self._get_discovered_services()
        return f"Refreshed - found {len(services)} services"

class PolymorphicWebRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for polymorphic web interface"""
    
    # Shared editor instance to avoid expensive re-initialization
    _shared_editor = None
    
    def __init__(self, *args, **kwargs):
        if PolymorphicWebRequestHandler._shared_editor is None:
            PolymorphicWebRequestHandler._shared_editor = PolymorphicWebEditor()
        self.editor = PolymorphicWebRequestHandler._shared_editor
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests and WebSocket upgrades"""
        url_path = self.path.split('?')[0]  # Remove query params

        # Debug: log all requests
        upgrade = self.headers.get('Upgrade', '')
        connection = self.headers.get('Connection', '')
        info(f"HTTP Request: {self.command} {url_path} - Upgrade: '{upgrade}' Connection: '{connection}'")

        # Check for WebSocket upgrade
        if self._is_websocket_request():
            info("Detected WebSocket upgrade request!")
            self._handle_websocket_upgrade()
            return

        if url_path == '/logs':
            self._handle_logs_page()
        elif url_path.startswith('/api/'):
            self._handle_api_request()
        elif url_path.startswith('/webdav/'):
            self._handle_webdav_get()
        elif url_path.startswith('/database'):
            self._handle_database_browser()
        else:
            # Default tournament tracker page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = self.editor.tell('html')
            self.wfile.write(html_content.encode())
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        url_path = self.path.split('?')[0]  # Remove query params
        
        if url_path.startswith('/api/logs/delete/'):
            log_id = url_path.split('/')[-1]
            self._handle_api_logs_delete(log_id)
        else:
            self.send_response(405)  # Method Not Allowed
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "DELETE method not allowed for this endpoint"}')
    
    def do_POST(self):
        """Handle POST requests"""
        url_path = self.path.split('?')[0]  # Remove query params
        info(f"HTTP POST Request: {url_path}")

        if url_path.startswith('/api/'):
            self._handle_api_request()
        elif url_path.startswith('/webdav/'):
            self._handle_webdav_post()
        else:
            self.send_response(405)  # Method Not Allowed
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "POST method not allowed for this endpoint"}')

    def do_OPTIONS(self):
        """Handle WebDAV OPTIONS requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('DAV', '1')
        self.send_header('Allow', 'GET, POST, PUT, DELETE, PROPFIND, OPTIONS')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PROPFIND, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Depth, Authorization')
        self.end_headers()

    def do_PROPFIND(self):
        """Handle WebDAV PROPFIND requests"""
        url_path = self.path.split('?')[0]  # Remove query params
        info(f"HTTP PROPFIND Request: {url_path}")

        if url_path.startswith('/webdav/'):
            self._handle_webdav_propfind()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'PROPFIND only supported on /webdav/ paths')

    def _handle_logs_page(self):
        """Handle /logs page request"""
        try:
            from logging_services.polymorphic_log_manager import log_manager
            recent_logs = log_manager.ask("recent 50")
            
            logs_html = self._render_logs_html(recent_logs)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(logs_html.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_html = f"<h1>Error loading logs: {e}</h1>"
            self.wfile.write(error_html.encode())
    
    def _handle_api_request(self):
        """Handle API requests"""
        url_path = self.path
        
        if url_path == '/api/logs/recent':
            self._handle_api_logs_recent()
        elif url_path == '/api/logs/create':
            self._handle_api_logs_create()
        elif url_path.startswith('/api/logs/more'):
            self._handle_api_logs_more()
        elif url_path.startswith('/api/logs/visualize/'):
            log_id = url_path.split('/')[-1]
            self._handle_api_logs_visualize(log_id)
        elif url_path.startswith('/api/logs/delete/'):
            log_id = url_path.split('/')[-1]
            self._handle_api_logs_delete(log_id)
        elif url_path.startswith('/api/media/'):
            file_path = urllib.parse.unquote(url_path[11:])  # Remove /api/media/
            self._handle_media_file(file_path)
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "API endpoint not implemented"}')
    
    def _handle_api_logs_recent(self):
        """Handle /api/logs/recent request"""
        try:
            # Get recent logs from the polymorphic log manager
            from logging_services.polymorphic_log_manager import log_manager
            
            # Ask for recent logs with IDs for deletion functionality
            logs_data = log_manager.ask("recent logs with ids limit 50")
            
            if isinstance(logs_data, list):
                response = {
                    "logs": logs_data,
                    "count": len(logs_data)
                }
            else:
                # Fallback if there's an issue with the log manager
                response = {
                    "logs": [],
                    "count": 0,
                    "error": "Unable to fetch logs from database"
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": f"Failed to fetch logs: {e}"}
            self.wfile.write(json.dumps(error_response).encode())
    
    def _handle_api_logs_visualize(self, log_id):
        """Handle /api/logs/visualize/{id} request"""
        try:
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Get visualization data from log manager
            from logging_services.polymorphic_log_manager import log_manager
            viz_data = log_manager.do(f"visualize {log_id}")
            
            if isinstance(viz_data, dict) and viz_data.get('error'):
                response = viz_data
            else:
                response = viz_data
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": f"Failed to get visualization data: {e}"}
            self.wfile.write(json.dumps(error_response).encode())
    
    def _handle_media_file(self, file_path):
        """Handle /api/media/{file_path} request - serve media files"""
        try:
            import mimetypes
            import os
            
            # Security check - ensure file exists and is readable
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'File not found')
                return
            
            # Additional security - prevent directory traversal
            if '..' in file_path or file_path.startswith('/'):
                abs_file_path = os.path.abspath(file_path)
            else:
                abs_file_path = os.path.abspath(file_path)
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(abs_file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # Send file
            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.send_header('Content-Length', str(os.path.getsize(abs_file_path)))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with open(abs_file_path, 'rb') as f:
                chunk_size = 8192
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            error_msg = f'Error serving file: {e}'.encode()
            self.wfile.write(error_msg)
    
    def _handle_api_logs_delete(self, log_id):
        """Handle /api/logs/delete/{id} request"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Delete log entry from database via log manager
            from logging_services.polymorphic_log_manager import log_manager
            result = log_manager.do(f"delete {log_id}")
            
            if result:
                response = {"success": True, "message": f"Log entry {log_id} deleted successfully"}
            else:
                response = {"success": False, "error": "Failed to delete log entry"}
            
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": f"Failed to delete log entry: {e}"}
            self.wfile.write(json.dumps(error_response).encode())
    
    def _handle_api_logs_create(self):
        """Handle /api/logs/create POST request"""
        try:
            # Read POST data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Validate required fields
            if not data.get('message'):
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"success": False, "error": "Message is required"}
                self.wfile.write(json.dumps(error_response).encode())
                return
            
            # Create log entry
            from logging_services.polymorphic_log_manager import log_manager
            level = data.get('level', 'INFO')
            source = data.get('source', 'manual_entry')
            message = data.get('message')
            log_data = data.get('data')
            
            # Use appropriate log level method
            if level == 'ERROR':
                log_manager.error(message, data=log_data, source=source)
            elif level == 'WARN':
                log_manager.warning(message, data=log_data, source=source)
            elif level == 'DEBUG':
                log_manager.debug(message, data=log_data, source=source)
            else:
                log_manager.info(message, data=log_data, source=source)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"success": True, "message": "Log entry created successfully"}
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"success": False, "error": f"Failed to create log entry: {e}"}
            self.wfile.write(json.dumps(error_response).encode())
    
    def _handle_api_logs_more(self):
        """Handle /api/logs/more?offset=X&limit=Y request"""
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            
            offset = int(params.get('offset', [0])[0])
            limit = int(params.get('limit', [50])[0])
            
            # Clamp limit to prevent abuse
            limit = min(limit, 1000)
            
            from logging_services.polymorphic_log_manager import log_manager
            # Ask for more logs with offset
            logs = log_manager.ask(f"recent {offset + limit} logs")
            
            # Slice to get only the new logs
            if logs and len(logs) > offset:
                more_logs = logs[offset:]
            else:
                more_logs = []
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(more_logs).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": f"Failed to load more logs: {e}"}
            self.wfile.write(json.dumps(error_response).encode())
    
    def _render_logs_html(self, logs_data):
        """Render logs as HTML table"""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Database Logs - Tournament Tracker</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 20px; background: #1a1a1a; color: #e0e0e0; 
                }
                .header { 
                    background: rgba(255,255,255,0.95); color: #333; padding: 20px; 
                    border-radius: 10px; margin-bottom: 20px;
                }
                .logs-table {
                    width: 100%; border-collapse: collapse; background: #2d2d2d;
                    border-radius: 8px; overflow: hidden;
                }
                .logs-table th, .logs-table td {
                    padding: 12px; text-align: left; border-bottom: 1px solid #444;
                }
                .logs-table th { background: #333; font-weight: bold; }
                .clickable-log { cursor: pointer; }
                .clickable-log:hover { background: #444; }
                
                /* Modal styles for media viewer */
                .media-modal {
                    display: none;
                    position: fixed;
                    z-index: 1000;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0,0,0,0.8);
                }
                .media-modal-content {
                    position: relative;
                    background-color: #222;
                    margin: 2% auto;
                    padding: 20px;
                    border-radius: 8px;
                    width: 80%;
                    max-width: 800px;
                    max-height: 90%;
                    overflow: auto;
                    color: white;
                }
                .media-close {
                    position: absolute;
                    top: 10px;
                    right: 20px;
                    font-size: 24px;
                    font-weight: bold;
                    cursor: pointer;
                    color: #fff;
                }
                .media-close:hover { color: #ccc; }
                
                /* Single rotating hourglass */
                .spinner {
                    display: inline-block;
                    font-size: 48px;
                    margin: 20px auto;
                    animation: hourglass-rotate 3s ease-in-out infinite;
                }
                @keyframes hourglass-rotate {
                    0% { transform: rotate(0deg); }
                    20% { transform: rotate(180deg); }
                    40% { transform: rotate(180deg); }
                    60% { transform: rotate(360deg); }
                    100% { transform: rotate(360deg); }
                }
                
                .level-ERROR { color: #ff6b6b; }
                .level-WARNING { color: #ffa726; }
                .level-INFO { color: #4fc3f7; }
                .level-DEBUG { color: #81c784; }
                .timestamp { font-family: monospace; font-size: 0.9em; }
                .back-btn {
                    display: inline-block; padding: 10px 20px; background: #667eea;
                    color: white; text-decoration: none; border-radius: 5px; margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🗂️ Database Logs</h1>
                <p>System activity and error logs from the polymorphic log manager</p>
                <a href="/" class="back-btn">← Back to Dashboard</a>
                <button id="auto-refresh-btn" onclick="toggleAutoRefresh()" 
                        style="background: #48bb78; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-left: 20px;">
                    ⏸️ Pause Auto-Refresh
                </button>
                <button onclick="toggleDebug()" 
                        style="background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">
                    🔍 Debug
                </button>
            </div>
            
            <!-- Debug Panel -->
            <div id="debugPanel" style="display: none; background: #222; color: #0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto;">
                <div style="color: #fff; font-weight: bold; margin-bottom: 10px;">WebSocket Debug Log:</div>
                <div id="debugLog"></div>
            </div>
            
            <!-- Manual Log Entry Form -->
            <div id="logEntryForm" style="background: #2d2d2d; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #444;">
                <h3 style="margin-top: 0; color: #e0e0e0;">📝 Create Manual Log Entry</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                    <div>
                        <label style="display: block; margin-bottom: 5px; color: #ccc;">Level:</label>
                        <select id="logLevel" style="width: 100%; padding: 8px; background: #333; color: white; border: 1px solid #555; border-radius: 4px;">
                            <option value="INFO">INFO</option>
                            <option value="WARN">WARN</option>
                            <option value="ERROR">ERROR</option>
                            <option value="DEBUG">DEBUG</option>
                        </select>
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 5px; color: #ccc;">Source:</label>
                        <input type="text" id="logSource" placeholder="manual_entry" value="manual_entry" 
                               style="width: 100%; padding: 8px; background: #333; color: white; border: 1px solid #555; border-radius: 4px;">
                    </div>
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: #ccc;">Message:</label>
                    <input type="text" id="logMessage" placeholder="Enter log message..." 
                           style="width: 100%; padding: 8px; background: #333; color: white; border: 1px solid #555; border-radius: 4px;">
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: #ccc;">Data (optional JSON):</label>
                    <textarea id="logData" placeholder='{"key": "value"}' rows="3"
                              style="width: 100%; padding: 8px; background: #333; color: white; border: 1px solid #555; border-radius: 4px; font-family: monospace;"></textarea>
                    <small style="color: #888;">Enter valid JSON or leave empty</small>
                </div>
                <button onclick="createLogEntry()" 
                        style="background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
                    ✅ Create Log Entry
                </button>
                <button onclick="toggleLogForm()" 
                        style="background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px;">
                    📦 Collapse
                </button>
            </div>
            
            <!-- Load More Controls -->
            <div style="background: #2d2d2d; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; border: 1px solid #444;">
                <span style="color: #ccc; margin-right: 15px;">Showing <span id="logCount">50</span> logs</span>
                <button onclick="loadMoreLogs()" id="loadMoreBtn"
                        style="background: #17a2b8; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px;">
                    📜 Load More (50)
                </button>
                <button onclick="loadAllLogs()" id="loadAllBtn"
                        style="background: #ffc107; color: black; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                    🌊 Load ALL Logs
                </button>
                <span style="color: #888; margin-left: 15px;">Auto-scroll: 
                    <label><input type="checkbox" id="autoScroll" checked> Enabled</label>
                </span>
            </div>
            
            <!-- Media Viewer Modal -->
            <div id="mediaModal" class="media-modal">
                <div class="media-modal-content">
                    <span class="media-close">&times;</span>
                    <div id="mediaViewer"></div>
                </div>
            </div>
            
            <table class="logs-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Level</th>
                        <th>Source</th>
                        <th>Message</th>
                        <th>Data</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        if logs_data and isinstance(logs_data, list):
            for log in logs_data:
                if isinstance(log, dict):
                    timestamp = log.get('timestamp', '')[:19]  # YYYY-MM-DD HH:MM:SS
                    level = log.get('level', 'INFO')
                    source = log.get('source', 'unknown')[:30]
                    message = html.escape(str(log.get('message', '')))[:100]
                    data_raw = log.get('data', '')
                    log_id = log.get('id', '')
                    
                    # Check if this log entry contains visualizable content
                    is_clickable = False
                    click_icon = ""
                    try:
                        if isinstance(data_raw, str) and data_raw.startswith('{'):
                            import json
                            data_json = json.loads(data_raw)
                            if isinstance(data_json, dict) and data_json.get('visualizable'):
                                is_clickable = True
                                viz_type = data_json['visualization_data']['type']
                                if viz_type == 'image':
                                    click_icon = " 🖼️"
                                elif viz_type == 'audio':
                                    click_icon = " 🔊"
                                elif viz_type == 'video':
                                    click_icon = " 🎥"
                                else:
                                    click_icon = " 👁️"
                    except:
                        pass
                    
                    data_display = html.escape(str(data_raw))[:50] + click_icon
                    
                    # Add clickable class and data attributes if visualizable
                    row_class = "clickable-log" if is_clickable else ""
                    row_attrs = f'data-log-id="{log_id}"' if is_clickable else ""
                    
                    html_content += f"""
                    <tr class="{row_class}" {row_attrs}>
                        <td class="timestamp">{timestamp}</td>
                        <td class="level-{level}">{level}</td>
                        <td>{source}</td>
                        <td>{message}</td>
                        <td>{data_display}</td>
                    </tr>
                    """
        else:
            html_content += '<tr><td colspan="5">No logs found or error loading logs</td></tr>'
        
        html_content += """
                </tbody>
            </table>
            
            <script>
                // WebSocket connection for real-time log streaming
                let ws = null;
                let isConnected = false;
                let reconnectAttempts = 0;
                let maxReconnectAttempts = 5;
                let connectionStartTime = null;
                let messageCount = 0;
                let debugEnabled = false;
                
                function debugLog(message) {
                    if (!debugEnabled) return;
                    
                    const timestamp = new Date().toTimeString().split(' ')[0];
                    const debugDiv = document.getElementById('debugLog');
                    const entry = document.createElement('div');
                    entry.innerHTML = `[${timestamp}] ${message}`;
                    debugDiv.appendChild(entry);
                    debugDiv.scrollTop = debugDiv.scrollHeight;
                    
                    // Keep only last 50 entries
                    while (debugDiv.children.length > 50) {
                        debugDiv.removeChild(debugDiv.firstChild);
                    }
                }
                
                function toggleDebug() {
                    debugEnabled = !debugEnabled;
                    const panel = document.getElementById('debugPanel');
                    panel.style.display = debugEnabled ? 'block' : 'none';
                    debugLog(`Debug ${debugEnabled ? 'enabled' : 'disabled'}`);
                }
                
                function connectWebSocket() {
                    try {
                        // Force secure websocket if we're using the encryption proxy
                        const protocol = window.location.port === '8443' || window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
                        
                        debugLog(`Connecting to ${wsUrl}`);
                        ws = new WebSocket(wsUrl);
                        connectionStartTime = Date.now();
                        
                        ws.onopen = function(event) {
                            const connectTime = Date.now() - connectionStartTime;
                            console.log('WebSocket connected');
                            isConnected = true;
                            reconnectAttempts = 0;
                            messageCount = 0;
                            document.title = '🟢 Database Logs (WebSocket Live)';
                            updateConnectionStatus('Connected', '#48bb78');
                            debugLog(`✅ Connected in ${connectTime}ms - ReadyState: ${ws.readyState}`);
                        };
                        
                        ws.onmessage = function(event) {
                            try {
                                messageCount++;
                                const uptime = Math.floor((Date.now() - connectionStartTime) / 1000);
                                debugLog(`📨 Message #${messageCount} received (${event.data.length} bytes, uptime: ${uptime}s)`);
                                
                                const message = JSON.parse(event.data);
                                
                                if (message.type === 'logs') {
                                    // Initial log data
                                    debugLog(`📊 Initial logs: ${message.data.length} entries`);
                                    updateLogsTable(message.data);
                                } else if (message.type === 'new_log') {
                                    // New log entry
                                    debugLog(`🆕 New log: ${message.data.message.substring(0, 50)}...`);
                                    addNewLogEntry(message.data);
                                }
                            } catch (e) {
                                console.error('Failed to parse WebSocket message:', e);
                                debugLog(`❌ Parse error: ${e.message}`);
                            }
                        };
                        
                        ws.onclose = function(event) {
                            const uptime = connectionStartTime ? Math.floor((Date.now() - connectionStartTime) / 1000) : 0;
                            console.log('WebSocket disconnected');
                            isConnected = false;
                            document.title = '🔴 Database Logs (Disconnected)';
                            updateConnectionStatus('Disconnected', '#e53e3e');
                            debugLog(`🔴 Disconnected - Code: ${event.code}, Reason: "${event.reason}", Uptime: ${uptime}s, Messages: ${messageCount}`);
                            
                            // Attempt to reconnect
                            if (reconnectAttempts < maxReconnectAttempts) {
                                reconnectAttempts++;
                                debugLog(`🔄 Reconnect attempt ${reconnectAttempts}/${maxReconnectAttempts} in 2s`);
                                console.log(`Attempting to reconnect... (${reconnectAttempts}/${maxReconnectAttempts})`);
                                setTimeout(connectWebSocket, 2000);
                            } else {
                                debugLog(`❌ Max reconnection attempts reached`);
                            }
                        };
                        
                        ws.onerror = function(error) {
                            console.error('WebSocket error:', error);
                            document.title = '🔴 Database Logs (Error)';
                            updateConnectionStatus('Error', '#e53e3e');
                            debugLog(`💥 Error event: ${error.message || 'Unknown error'} - ReadyState: ${ws.readyState}`);
                        };
                        
                    } catch (e) {
                        console.error('Failed to connect WebSocket:', e);
                        document.title = '🔴 Database Logs (Connection Failed)';
                        updateConnectionStatus('Failed', '#e53e3e');
                        debugLog(`💥 Connection failed: ${e.message}`);
                    }
                }
                
                // Enhanced status updates with debug info
                function updateConnectionStatus(status, color) {
                    const btn = document.getElementById('auto-refresh-btn');
                    if (btn) {
                        const uptime = connectionStartTime ? Math.floor((Date.now() - connectionStartTime) / 1000) : 0;
                        btn.textContent = `📡 ${status} (${uptime}s)`;
                        btn.style.background = color;
                        
                        if (status === 'Connected') {
                            debugLog(`📡 Status: ${status} - Ready for messages`);
                        }
                    }
                }
                
                
                function updateLogsTable(logs) {
                    const tbody = document.querySelector('.logs-table tbody');
                    tbody.innerHTML = '';
                    
                    logs.forEach((entry, index) => {
                        addLogRow(entry, index < 3); // Highlight first 3 as new
                    });
                }
                
                function addNewLogEntry(logEntry) {
                    const tbody = document.querySelector('.logs-table tbody');
                    const row = addLogRow(logEntry, true); // Highlight as new
                    
                    // Insert at top
                    tbody.insertBefore(row, tbody.firstChild);
                    
                    // Remove old entries (keep last 50)
                    while (tbody.children.length > 50) {
                        tbody.removeChild(tbody.lastChild);
                    }
                }
                
                function addLogRow(entry, highlight = false) {
                    const row = document.createElement('tr');
                    
                    const timestamp = entry.timestamp ? entry.timestamp.substring(0, 19) : '';
                    const level = entry.level || 'INFO';
                    const source = (entry.source || 'unknown').substring(0, 30);
                    const message = (entry.message || '').substring(0, 100);
                    const data = (entry.data || '').substring(0, 50);
                    
                    row.innerHTML = `
                        <td class="timestamp">${timestamp}</td>
                        <td class="level-${level}">${level}</td>
                        <td>${source}</td>
                        <td>${message}</td>
                        <td>${data}</td>
                    `;
                    
                    if (highlight) {
                        row.style.backgroundColor = '#4a5568';
                        setTimeout(() => {
                            row.style.backgroundColor = '';
                        }, 3000);
                    }
                    
                    return row;
                }
                
                function toggleAutoRefresh() {
                    if (isConnected) {
                        ws.close();
                        updateConnectionStatus('Disconnected', '#667eea');
                    } else {
                        connectWebSocket();
                    }
                }
                
                // Media viewer functionality
                const mediaModal = document.getElementById('mediaModal');
                const mediaViewer = document.getElementById('mediaViewer');
                const mediaClose = document.querySelector('.media-close');
                let currentFetchController = null;
                let currentDeleteController = null;
                let isClosing = false;
                
                function getMessageHTML(message, subtext = '') {
                    return `
                        <div style="text-align: center; padding: 40px;">
                            <div class="spinner">⏳</div>
                            <h3>${message}</h3>
                            ${subtext ? `<p style="color: #888;">${subtext}</p>` : ''}
                        </div>
                    `;
                }
                
                function stopAllMedia() {
                    // Stop all audio elements in modal
                    const modalAudioElements = mediaViewer.querySelectorAll('audio');
                    console.log(`Found ${modalAudioElements.length} audio elements in modal`);
                    modalAudioElements.forEach((audio, index) => {
                        console.log(`Stopping modal audio element ${index}: paused=${audio.paused}, currentTime=${audio.currentTime}`);
                        if (!audio.paused) {
                            audio.pause();
                        }
                        audio.currentTime = 0;
                        // Clear all sources
                        const sources = audio.querySelectorAll('source');
                        sources.forEach(source => source.src = '');
                        audio.src = ''; // Clear main source
                        audio.load(); // Reload to clear everything
                        console.log(`Modal audio element ${index} stopped`);
                    });
                    
                    // ALSO stop ALL audio elements in the entire document (failsafe)
                    const allAudioElements = document.querySelectorAll('audio');
                    console.log(`Found ${allAudioElements.length} total audio elements in document`);
                    allAudioElements.forEach((audio, index) => {
                        console.log(`Stopping global audio element ${index}: paused=${audio.paused}, currentTime=${audio.currentTime}`);
                        if (!audio.paused) {
                            audio.pause();
                        }
                        audio.currentTime = 0;
                        // Clear all sources
                        const sources = audio.querySelectorAll('source');
                        sources.forEach(source => source.src = '');
                        audio.src = ''; // Clear main source
                        audio.load(); // Reload to clear everything
                        console.log(`Global audio element ${index} stopped`);
                    });
                    
                    // Stop all video elements
                    const videoElements = mediaViewer.querySelectorAll('video');
                    console.log(`Found ${videoElements.length} video elements`);
                    videoElements.forEach((video, index) => {
                        console.log(`Stopping video element ${index}: paused=${video.paused}, currentTime=${video.currentTime}`);
                        if (!video.paused) {
                            video.pause();
                        }
                        video.currentTime = 0;
                        // Clear all sources
                        const sources = video.querySelectorAll('source');
                        sources.forEach(source => source.src = '');
                        video.src = ''; // Clear main source
                        video.load(); // Reload to clear everything
                        console.log(`Video element ${index} stopped`);
                    });
                    
                    // Stop any iframes that might have media
                    const iframeElements = mediaViewer.querySelectorAll('iframe');
                    console.log(`Found ${iframeElements.length} iframe elements`);
                    iframeElements.forEach((iframe, index) => {
                        iframe.src = 'about:blank'; // Clear iframe content
                        console.log(`Iframe element ${index} cleared`);
                    });
                    
                    console.log('All media elements stopped');
                }
                
                function closeModal() {
                    if (isClosing) return; // Prevent multiple close attempts
                    isClosing = true;
                    
                    // Stop all media elements FIRST - don't replace content yet
                    console.log('=== CLOSING MODAL - STOPPING MEDIA FIRST ===');
                    stopAllMedia();
                    
                    // Small delay to ensure media stopping completes
                    setTimeout(() => {
                        // Now show closing state after media is stopped
                        mediaViewer.innerHTML = getMessageHTML('Closing...', 'Media stopped, cleaning up...');
                    }, 200); // 200ms delay
                    
                    // Cancel all ongoing operations
                    const cleanup = [];
                    
                    if (currentFetchController) {
                        currentFetchController.abort();
                        cleanup.push(new Promise(resolve => {
                            setTimeout(resolve, 100); // Give time for abort to complete
                        }));
                        currentFetchController = null;
                    }
                    
                    if (currentDeleteController) {
                        currentDeleteController.abort();
                        cleanup.push(new Promise(resolve => {
                            setTimeout(resolve, 100); // Give time for abort to complete
                        }));
                        currentDeleteController = null;
                    }
                    
                    // Wait for all cleanup to complete, then close
                    Promise.all(cleanup).then(() => {
                        mediaModal.style.display = 'none';
                        isClosing = false;
                        // Don't restore original content since it may contain playing media
                        mediaViewer.innerHTML = '';
                    }).catch(() => {
                        // Even if cleanup fails, close the modal
                        mediaModal.style.display = 'none';
                        isClosing = false;
                        mediaViewer.innerHTML = '';
                    });
                }
                
                // Close modal when clicking the X
                mediaClose.onclick = closeModal;
                
                // Close modal when clicking outside
                window.onclick = function(event) {
                    if (event.target == mediaModal) {
                        closeModal();
                    }
                };
                
                // Handle clicks on visualizable log entries
                document.addEventListener('click', function(event) {
                    const row = event.target.closest('tr.clickable-log');
                    if (row) {
                        const logId = row.dataset.logId;
                        if (logId) {
                            openMediaViewer(logId);
                        }
                    }
                });
                
                function openMediaViewer(logId) {
                    // Cancel any previous request
                    if (currentFetchController) {
                        currentFetchController.abort();
                    }
                    
                    // Show modal immediately with loading state
                    mediaViewer.innerHTML = getMessageHTML('Loading content...', 'Fetching visualization data') + `
                        <button onclick="closeModal()" 
                                style="background: #dc3545; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 15px;">
                            Cancel
                        </button>
                    `;
                    mediaModal.style.display = 'block';
                    
                    // Create new AbortController for this request
                    currentFetchController = new AbortController();
                    
                    // Then fetch visualization data with cancellation support
                    fetch(`/api/logs/visualize/${logId}`, {
                        signal: currentFetchController.signal
                    })
                        .then(response => response.json())
                        .then(data => {
                            // Clear the controller since request completed
                            currentFetchController = null;
                            
                            if (data.error) {
                                mediaViewer.innerHTML = `
                                    <div style="text-align: center; padding: 40px;">
                                        <div style="font-size: 24px; margin-bottom: 20px; color: red;">❌</div>
                                        <h3 style="color: red;">Error</h3>
                                        <p>${data.error}</p>
                                        <button onclick="mediaModal.style.display='none'" 
                                                style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 15px;">
                                            Close
                                        </button>
                                    </div>
                                `;
                            } else {
                                renderVisualization(data, logId);
                            }
                        })
                        .catch(error => {
                            // Clear the controller
                            currentFetchController = null;
                            
                            // Don't show error for aborted requests
                            if (error.name === 'AbortError') {
                                console.log('Request was cancelled');
                                return;
                            }
                            
                            console.error('Error fetching visualization data:', error);
                            mediaViewer.innerHTML = `
                                <div style="text-align: center; padding: 40px;">
                                    <div style="font-size: 24px; margin-bottom: 20px; color: red;">🚫</div>
                                    <h3 style="color: red;">Failed to Load</h3>
                                    <p>Unable to fetch content. Please try again.</p>
                                    <button onclick="mediaModal.style.display='none'" 
                                            style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 15px;">
                                        Close
                                    </button>
                                </div>
                            `;
                        });
                }
                
                function deleteLogEntry(logId) {
                    if (confirm('Are you sure you want to delete this log entry? This action cannot be undone.')) {
                        // Show deleting state
                        mediaViewer.innerHTML = getMessageHTML('<span style="color: #dc3545;">Deleting...</span>', 'Removing log entry from database<br><small style="font-size: 12px; color: #666;">Please wait, do not close this dialog</small>');
                        
                        // Create delete controller
                        currentDeleteController = new AbortController();
                        
                        fetch(`/api/logs/delete/${logId}`, {
                            method: 'DELETE',
                            signal: currentDeleteController.signal
                        })
                        .then(response => response.json())
                        .then(data => {
                            // Clear delete controller
                            currentDeleteController = null;
                            
                            if (data.success) {
                                // Show success state briefly
                                mediaViewer.innerHTML = `
                                    <div style="text-align: center; padding: 40px;">
                                        <div style="font-size: 24px; margin-bottom: 20px; color: #28a745;">✅</div>
                                        <h3 style="color: #28a745;">Deleted Successfully</h3>
                                        <p style="color: #888;">Log entry has been removed</p>
                                    </div>
                                `;
                                
                                // Remove the row from the table
                                const row = document.querySelector(`tr[data-log-id="${logId}"]`);
                                if (row) {
                                    row.style.background = '#ff4444';
                                    row.style.transition = 'all 0.3s ease';
                                    setTimeout(() => {
                                        row.remove();
                                    }, 300);
                                }
                                
                                // Close modal after brief success display
                                setTimeout(() => {
                                    mediaModal.style.display = 'none';
                                }, 1500);
                                
                            } else {
                                mediaViewer.innerHTML = `
                                    <div style="text-align: center; padding: 40px;">
                                        <div style="font-size: 24px; margin-bottom: 20px; color: red;">❌</div>
                                        <h3 style="color: red;">Delete Failed</h3>
                                        <p>${data.error || 'Unknown error occurred'}</p>
                                        <button onclick="closeModal()" 
                                                style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 15px;">
                                            Close
                                        </button>
                                    </div>
                                `;
                            }
                        })
                        .catch(error => {
                            // Clear delete controller
                            currentDeleteController = null;
                            
                            // Don't show error for aborted requests
                            if (error.name === 'AbortError') {
                                console.log('Delete request was cancelled');
                                return;
                            }
                            
                            console.error('Error deleting log entry:', error);
                            mediaViewer.innerHTML = `
                                <div style="text-align: center; padding: 40px;">
                                    <div style="font-size: 24px; margin-bottom: 20px; color: red;">🚫</div>
                                    <h3 style="color: red;">Delete Failed</h3>
                                    <p>Network error occurred. Please try again.</p>
                                    <button onclick="closeModal()" 
                                            style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 15px;">
                                        Close
                                    </button>
                                </div>
                            `;
                        });
                    }
                }
                
                function renderVisualization(vizData, logId) {
                    const type = vizData.type;
                    const content = vizData.content;
                    const metadata = vizData.metadata || {};
                    
                    let html = '';
                    
                    if (type === 'image') {
                        html = `
                            <h3>📷 Image Viewer</h3>
                            <p>${metadata.description || 'Image from log entry'}</p>
                            <img src="/api/media/${encodeURIComponent(content)}" 
                                 alt="Log image" 
                                 style="max-width: 100%; height: auto; border-radius: 4px;">
                            <p style="font-size: 12px; color: #888; margin-top: 10px;">
                                File: ${metadata.file_name || content}<br>
                                Size: ${metadata.file_size ? (metadata.file_size/1024/1024).toFixed(2) + ' MB' : 'Unknown'}
                            </p>
                        `;
                    } else if (type === 'audio') {
                        html = `
                            <h3>🔊 Audio Player</h3>
                            <p>${metadata.description || 'Audio from log entry'}</p>
                            <audio controls style="width: 100%;">
                                <source src="/api/media/${encodeURIComponent(content)}" type="${vizData.mime_type}">
                                Your browser does not support the audio element.
                            </audio>
                            <p style="font-size: 12px; color: #888; margin-top: 10px;">
                                File: ${metadata.file_name || content}<br>
                                Size: ${metadata.file_size ? (metadata.file_size/1024/1024).toFixed(2) + ' MB' : 'Unknown'}
                            </p>
                        `;
                    } else if (type === 'video') {
                        // Handle data URLs directly, otherwise use media API
                        const videoSrc = content.startsWith('data:') ? content : `/api/media/${encodeURIComponent(content)}`;
                        
                        html = `
                            <h3>🎥 Video Player</h3>
                            <p>${metadata.description || 'Video from log entry'}</p>
                            <video controls style="width: 100%; max-height: 400px;">
                                <source src="${videoSrc}" type="${vizData.mime_type}">
                                Your browser does not support the video element.
                            </video>
                            <p style="font-size: 12px; color: #888; margin-top: 10px;">
                                File: ${metadata.file_name || 'video'}<br>
                                Size: ${metadata.file_size ? (metadata.file_size/1024/1024).toFixed(2) + ' MB' : 'Unknown'}<br>
                                ${metadata.duration ? `Duration: ${metadata.duration} seconds` : ''}
                            </p>
                        `;
                    } else if (type === 'html') {
                        html = `
                            <h3>📄 HTML Content</h3>
                            <p>${metadata.description || 'Interactive content from log entry'}</p>
                            <div style="border: 1px solid #444; padding: 10px; background: #111;">
                                ${content}
                            </div>
                        `;
                    } else if (type === 'json') {
                        html = `
                            <h3>📊 Data Viewer</h3>
                            <p>${metadata.description || 'Data from log entry'}</p>
                            <pre style="background: #111; padding: 10px; border-radius: 4px; overflow: auto; max-height: 400px;">${JSON.stringify(content, null, 2)}</pre>
                        `;
                    } else {
                        html = `
                            <h3>📄 Content</h3>
                            <p>${metadata.description || 'Content from log entry'}</p>
                            <pre style="background: #111; padding: 10px; border-radius: 4px; overflow: auto; max-height: 400px;">${content}</pre>
                        `;
                    }
                    
                    // Add delete button and actions section
                    html += `
                        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #444;">
                            <h4 style="margin-bottom: 10px;">Actions</h4>
                            <button 
                                onclick="deleteLogEntry(${logId})" 
                                style="
                                    background: #dc3545; 
                                    color: white; 
                                    border: none; 
                                    padding: 8px 16px; 
                                    border-radius: 4px; 
                                    cursor: pointer;
                                    font-size: 14px;
                                    margin-right: 10px;
                                "
                                onmouseover="this.style.background='#c82333'"
                                onmouseout="this.style.background='#dc3545'">
                                🗑️ Delete Log Entry
                            </button>
                            <button 
                                onclick="closeModal()" 
                                style="
                                    background: #6c757d; 
                                    color: white; 
                                    border: none; 
                                    padding: 8px 16px; 
                                    border-radius: 4px; 
                                    cursor: pointer;
                                    font-size: 14px;
                                "
                                onmouseover="this.style.background='#5a6268'"
                                onmouseout="this.style.background='#6c757d'">
                                Close
                            </button>
                        </div>
                    `;
                    
                    mediaViewer.innerHTML = html;
                }
                
                // Manual log entry functions
                function createLogEntry() {
                    const level = document.getElementById('logLevel').value;
                    const source = document.getElementById('logSource').value || 'manual_entry';
                    const message = document.getElementById('logMessage').value;
                    const dataText = document.getElementById('logData').value;
                    
                    if (!message.trim()) {
                        alert('Message is required');
                        return;
                    }
                    
                    let data = null;
                    if (dataText.trim()) {
                        try {
                            data = JSON.parse(dataText);
                        } catch (e) {
                            alert('Invalid JSON in data field: ' + e.message);
                            return;
                        }
                    }
                    
                    // Create log entry via API
                    fetch('/api/logs/create', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            level: level,
                            source: source,
                            message: message,
                            data: data
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Clear form
                            document.getElementById('logMessage').value = '';
                            document.getElementById('logData').value = '';
                            // Refresh logs
                            setTimeout(() => location.reload(), 500);
                        } else {
                            alert('Failed to create log entry: ' + (data.error || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        alert('Network error: ' + error);
                    });
                }
                
                function toggleLogForm() {
                    const form = document.getElementById('logEntryForm');
                    const button = event.target;
                    if (form.style.display === 'none') {
                        form.style.display = 'block';
                        button.textContent = '📦 Collapse';
                    } else {
                        form.style.display = 'none';
                        button.textContent = '📝 Show Log Form';
                    }
                }
                
                // Infinite scroll variables
                let currentLogOffset = 50;
                let isLoadingLogs = false;
                let allLogsLoaded = false;
                
                function loadMoreLogs(count = 50) {
                    if (isLoadingLogs || allLogsLoaded) return;
                    
                    isLoadingLogs = true;
                    const loadBtn = document.getElementById('loadMoreBtn');
                    const originalText = loadBtn.textContent;
                    loadBtn.textContent = '⏳ Loading...';
                    loadBtn.disabled = true;
                    
                    fetch(`/api/logs/more?offset=${currentLogOffset}&limit=${count}`)
                        .then(response => response.json())
                        .then(logs => {
                            if (logs.length === 0) {
                                allLogsLoaded = true;
                                loadBtn.textContent = '✅ All Logs Loaded';
                                return;
                            }
                            
                            // Append new logs to table
                            const tbody = document.querySelector('.logs-table tbody');
                            logs.forEach(log => {
                                const row = createLogRow(log);
                                tbody.appendChild(row);
                            });
                            
                            currentLogOffset += logs.length;
                            document.getElementById('logCount').textContent = currentLogOffset;
                            
                            // Auto-scroll if enabled
                            if (document.getElementById('autoScroll').checked) {
                                window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                            }
                        })
                        .catch(error => {
                            console.error('Error loading more logs:', error);
                            alert('Failed to load more logs');
                        })
                        .finally(() => {
                            isLoadingLogs = false;
                            loadBtn.textContent = originalText;
                            loadBtn.disabled = false;
                        });
                }
                
                function loadAllLogs() {
                    if (confirm('Load ALL logs? This might take a while and use significant memory.')) {
                        loadMoreLogs(10000); // Load a large batch
                    }
                }
                
                function createLogRow(log) {
                    const row = document.createElement('tr');
                    const timestamp = (log.timestamp || '').substring(0, 19);
                    const level = log.level || 'INFO';
                    const source = (log.source || 'unknown').substring(0, 30);
                    const message = (log.message || '').substring(0, 100);
                    const dataRaw = log.data || '';
                    
                    // Check for visualizable content
                    let isClickable = false;
                    let clickIcon = "";
                    try {
                        if (typeof dataRaw === 'string' && dataRaw.startsWith('{')) {
                            const dataJson = JSON.parse(dataRaw);
                            if (dataJson && dataJson.visualizable) {
                                isClickable = true;
                                const vizType = dataJson.visualization_data?.type;
                                if (vizType === 'image') clickIcon = " 🖼️";
                                else if (vizType === 'audio') clickIcon = " 🔊";
                                else if (vizType === 'video') clickIcon = " 🎥";
                                else clickIcon = " 👁️";
                            }
                        }
                    } catch (e) {}
                    
                    const dataDisplay = String(dataRaw).substring(0, 50) + clickIcon;
                    
                    if (isClickable) {
                        row.className = 'clickable-log';
                        row.dataset.logId = log.id;
                    }
                    
                    row.innerHTML = `
                        <td class="timestamp">${timestamp}</td>
                        <td class="level-${level}">${level}</td>
                        <td>${source}</td>
                        <td>${message}</td>
                        <td>${dataDisplay}</td>
                    `;
                    
                    return row;
                }
                
                // Infinite scroll detection
                window.addEventListener('scroll', () => {
                    if (document.getElementById('autoScroll').checked && 
                        window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
                        loadMoreLogs(25); // Load smaller batches on scroll
                    }
                });
                
                // Start WebSocket connection
                connectWebSocket();
            </script>
        </body>
        </html>
        """
        return html_content
    
    def _is_websocket_request(self):
        """Check if this is a WebSocket upgrade request"""
        upgrade = self.headers.get('Upgrade', '').lower()
        connection = self.headers.get('Connection', '').lower()
        return upgrade == 'websocket' and 'upgrade' in connection
    
    def _handle_websocket_upgrade(self):
        """Handle WebSocket upgrade handshake"""
        try:
            info(f"WebSocket upgrade request for {self.path}")
            # Get WebSocket key for handshake
            websocket_key = self.headers.get('Sec-WebSocket-Key')
            if not websocket_key:
                warning("No WebSocket key found in headers")
                self.send_response(400)
                self.end_headers()
                return
            
            # Generate accept key
            magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept_key = base64.b64encode(
                hashlib.sha1((websocket_key + magic_string).encode()).digest()
            ).decode()
            
            # Send handshake response
            info(f"WebSocket handshake successful, starting connection thread")
            self.send_response(101, "Switching Protocols")
            self.send_header('Upgrade', 'websocket')
            self.send_header('Connection', 'Upgrade')
            self.send_header('Sec-WebSocket-Accept', accept_key)
            self.send_header('Sec-WebSocket-Version', '13')
            # Add CORS headers for websockets
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Headers', '*')
            self.end_headers()
            
            # Handle WebSocket connection directly (not in a separate thread)
            info("Starting WebSocket connection handling")
            self._handle_websocket_connection()
            
        except Exception as e:
            error(f"WebSocket upgrade error: {e}")
            self.send_response(500)
            self.end_headers()
    
    
    def _handle_websocket_connection(self):
        """Handle WebSocket connection directly"""
        try:
            info(f"WebSocket: Handler for {self.path}")
            url_path = self.path.split('?')[0]
            
            if url_path == '/ws/logs':
                info("WebSocket: Starting logs streaming")
                self._stream_logs()
            else:
                warning(f"WebSocket: Unknown endpoint: {url_path}")
                self._send_websocket_text('{"error": "Unknown WebSocket endpoint"}')
                
        except Exception as e:
            error(f"WebSocket: Handler error: {e}")
        finally:
            info("WebSocket: Handler ending")
            try:
                self.connection.close()
            except:
                pass
    
    def _stream_logs(self):
        """Stream log entries via WebSocket - simplified for browser compatibility"""
        try:
            info("WebSocket: Starting log streaming")
            
            # Send initial logs immediately
            logs = [
                {"timestamp": "2025-09-11T19:00:00", "level": "INFO", "source": "websocket", "message": "WebSocket connection established!", "data": "{}"},
                {"timestamp": "2025-09-11T19:00:01", "level": "DEBUG", "source": "websocket", "message": "Streaming logs in real-time", "data": "{}"},
                {"timestamp": "2025-09-11T19:00:02", "level": "SUCCESS", "source": "websocket", "message": "Cool kids are indeed using WebSockets! 🚀", "data": "{}"}
            ]
            
            self._send_websocket_text(json.dumps({"type": "logs", "data": logs}))
            info("WebSocket: Initial logs sent successfully")
            
            # Set socket timeout for frame reading (longer for browser compatibility)
            self.connection.settimeout(5.0)
            
            counter = 0
            last_update = time.time()
            last_ping = time.time()
            
            while True:
                current_time = time.time()
                
                # Check for incoming frames (especially ping frames)
                try:
                    data = self.connection.recv(1024)
                    if not data:
                        # Empty data means client disconnected
                        info("WebSocket: Client disconnected (empty recv)")
                        break
                    elif len(data) >= 2:
                        opcode = data[0] & 0x0F
                        info(f"WebSocket: Received frame, opcode: {opcode}, length: {len(data)}")
                        
                        if opcode == 0x8:  # Close frame
                            info("WebSocket: Client sent close frame")
                            break
                        elif opcode == 0x9:  # Ping frame  
                            info("WebSocket: Received ping, sending pong")
                            # Send pong with empty payload
                            self._send_websocket_pong()
                        elif opcode == 0xA:  # Pong frame
                            info("WebSocket: Received pong from client")
                        elif opcode == 0x1:  # Text frame
                            info("WebSocket: Received text frame from client")
                    else:
                        info(f"WebSocket: Received incomplete frame ({len(data)} bytes)")
                            
                except socket.timeout:
                    # Normal - no data available, continue
                    pass
                except socket.error as e:
                    if e.errno == 104:  # Connection reset by peer
                        info("WebSocket: Connection reset by peer")
                        break
                    elif e.errno == 9:  # Bad file descriptor
                        info("WebSocket: Connection closed (bad fd)")
                        break
                    else:
                        warning(f"WebSocket: Socket error: {e}")
                        break
                
                # Send periodic ping every 30 seconds to keep connection alive
                if current_time - last_ping >= 30:
                    try:
                        self._send_websocket_ping()
                        last_ping = current_time
                        info("WebSocket: Sent keepalive ping")
                    except Exception as ping_e:
                        error(f"WebSocket: Failed to send ping: {ping_e}")
                        break
                
                # Send periodic updates every 5 seconds
                if current_time - last_update >= 5:
                    counter += 1
                    
                    # Test if connection is still alive
                    try:
                        # More comprehensive connection test
                        peer = self.connection.getpeername()
                        sock = self.connection.getsockname()
                        # If we can get peer info, connection is still alive
                    except (OSError, socket.error):
                        info("WebSocket: Connection closed by client (peer check failed)")
                        break
                    
                    new_log = {
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO", 
                        "source": "websocket_demo",
                        "message": f"Live update #{counter} - WebSocket is working!",
                        "data": "{}"
                    }
                    
                    try:
                        self._send_websocket_text(json.dumps({"type": "new_log", "data": new_log}))
                        info(f"WebSocket: Sent periodic update #{counter}")
                        last_update = current_time
                    except Exception as send_e:
                        error(f"WebSocket: Failed to send update: {send_e}")
                        break
                
                # Small sleep to prevent busy waiting
                time.sleep(0.1)
                
        except Exception as e:
            error(f"WebSocket: Log streaming error: {e}")
        finally:
            info("WebSocket: Streaming ended, closing connection")
            try:
                self.connection.close()
            except:
                pass
    
    def _send_websocket_text(self, text):
        """Send text message over WebSocket"""
        try:
            message = text.encode('utf-8')
            frame = bytearray()
            
            # FIN + opcode (text frame)
            frame.append(0x81)
            
            # Payload length
            length = len(message)
            if length < 126:
                frame.append(length)
            elif length < 65536:
                frame.append(126)
                frame.extend(struct.pack('>H', length))
            else:
                frame.append(127)
                frame.extend(struct.pack('>Q', length))
            
            # Payload
            frame.extend(message)
            
            self.wfile.write(frame)
            self.wfile.flush()
            
        except Exception as e:
            error(f"WebSocket send error: {e}")
            raise
    
    def _send_websocket_pong(self, payload=b''):
        """Send pong frame over WebSocket"""
        try:
            frame = bytearray()
            
            # FIN + opcode (pong frame)
            frame.append(0x8A)
            
            # Payload length
            length = len(payload)
            if length < 126:
                frame.append(length)
            elif length < 65516:
                frame.append(126)
                frame.extend(struct.pack('>H', length))
            else:
                frame.append(127)
                frame.extend(struct.pack('>Q', length))
            
            # Payload
            if payload:
                frame.extend(payload)
            
            self.wfile.write(frame)
            self.wfile.flush()
            info(f"WebSocket: Sent pong frame ({len(payload)} bytes)")
            
        except Exception as e:
            error(f"WebSocket pong send error: {e}")
            raise
    
    def _send_websocket_ping(self, payload=b''):
        """Send ping frame over WebSocket to keep connection alive"""
        try:
            frame = bytearray()
            
            # FIN + opcode (ping frame)
            frame.append(0x89)
            
            # Payload length
            length = len(payload)
            if length < 126:
                frame.append(length)
            elif length < 65516:
                frame.append(126)
                frame.extend(struct.pack('>H', length))
            else:
                frame.append(127)
                frame.extend(struct.pack('>Q', length))
            
            # Payload
            if payload:
                frame.extend(payload)
            
            self.wfile.write(frame)
            self.wfile.flush()
            info(f"WebSocket: Sent ping frame ({len(payload)} bytes)")
            
        except Exception as e:
            error(f"WebSocket ping send error: {e}")
            raise
    
    def log_message(self, format, *args):
        """Log HTTP requests to polymorphic logger"""
        try:
            message = format % args
            info(f"HTTP: {message}")
        except:
            # Fallback in case formatting fails
            info(f"HTTP request: {self.command} {self.path}")

    def _handle_webdav_get(self):
        """Handle WebDAV GET requests"""
        try:
            from polymorphic_core.service_locator import get_service
            path_parts = self.path.strip('/').split('/')

            if len(path_parts) < 2:
                self._send_webdav_error(400, "Invalid WebDAV path")
                return

            # Extract data type from path: /webdav/data/players -> 'players'
            if path_parts[1] == 'data' and len(path_parts) > 2:
                data_type = path_parts[2]
                database = get_service("database")

                if database:
                    if data_type == 'stats':
                        result = database.ask('stats')
                    elif data_type == 'players':
                        result = database.ask('top 50 players')
                    else:
                        result = database.ask(f'all {data_type} limit 100')

                    formatted = database.tell('json', result)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(formatted.encode('utf-8'))
                else:
                    self._send_webdav_error(503, "Database service not available")
            else:
                self._send_webdav_error(404, "WebDAV resource not found")

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            error(f"WebDAV GET error: {e}")
            error(f"WebDAV GET traceback:\n{tb}")
            self._send_webdav_error(500, f"Internal error: {str(e)}")

    def _handle_webdav_propfind(self):
        """Handle WebDAV PROPFIND requests"""
        try:
            from polymorphic_core.service_locator import get_service

            path = self.path.strip('/').replace('webdav/', '')
            resources = []

            if not path or path == 'webdav':
                # Root level - show data and bonjour directories
                resources = [
                    {'name': 'data', 'type': 'collection', 'description': 'Tournament data'},
                    {'name': 'bonjour', 'type': 'collection', 'description': 'Bonjour services'}
                ]
            elif path == 'data':
                # Data directory - show available tables
                database = get_service("database")
                if database:
                    tables = ['players', 'tournaments', 'organizations', 'stats', 'logs']
                    resources = [{'name': table, 'type': 'collection', 'description': f'{table.title()} data'}
                               for table in tables]
            elif path == 'bonjour':
                # Bonjour directory - show services
                from polymorphic_core.local_bonjour import local_announcer
                services = local_announcer.services
                resources = [{'name': name, 'type': 'service', 'description': ', '.join(info.get('capabilities', [])[:2])}
                           for name, info in services.items()]

            # Generate WebDAV XML response
            multistatus = ET.Element('D:multistatus')
            multistatus.set('xmlns:D', 'DAV:')

            for resource in resources:
                response = ET.SubElement(multistatus, 'D:response')
                href = ET.SubElement(response, 'D:href')
                href.text = f"/webdav/{resource['name']}"

                propstat = ET.SubElement(response, 'D:propstat')
                prop = ET.SubElement(propstat, 'D:prop')

                displayname = ET.SubElement(prop, 'D:displayname')
                displayname.text = resource['name']

                if resource['type'] == 'collection':
                    ET.SubElement(prop, 'D:resourcetype').append(ET.Element('D:collection'))
                else:
                    ET.SubElement(prop, 'D:resourcetype')

                desc = ET.SubElement(prop, 'description')
                desc.text = resource.get('description', '')

                status = ET.SubElement(propstat, 'D:status')
                status.text = 'HTTP/1.1 200 OK'

            response_xml = ET.tostring(multistatus, encoding='unicode')

            self.send_response(207, 'Multi-Status')
            self.send_header('Content-Type', 'application/xml')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_xml.encode('utf-8'))

        except Exception as e:
            error(f"WebDAV PROPFIND error: {e}")
            self._send_webdav_error(500, f"PROPFIND error: {str(e)}")

    def _handle_webdav_post(self):
        """Handle WebDAV POST requests for service actions"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data) if post_data else {}

            path_parts = self.path.strip('/').split('/')
            if len(path_parts) < 3:
                self._send_webdav_error(400, "Invalid service path")
                return

            service_name = path_parts[2]  # /webdav/services/database -> 'database'
            action = data.get('action', '')

            from polymorphic_core.service_locator import get_service
            service = get_service(service_name)

            if service:
                result = service.do(action)
                response_data = {'result': result, 'service': service_name, 'action': action}

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, indent=2, default=str).encode('utf-8'))
            else:
                self._send_webdav_error(404, f"Service '{service_name}' not found")

        except Exception as e:
            error(f"WebDAV POST error: {e}")
            self._send_webdav_error(500, f"POST error: {str(e)}")

    def _handle_database_browser(self):
        """Handle database browser web interface"""
        try:
            import traceback
            from polymorphic_core.service_locator import get_service

            # Generate database browser HTML
            database = get_service("database")
            if not database:
                error("Database service not available via service locator")
                self.send_response(503)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>Database service not available</h1>')
                return

            info("Database browser: attempting to get stats")
            stats = database.ask('stats')
            info(f"Database browser: got stats: {stats}")

            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Tournament Tracker - Database Browser</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .panel {{ border: 1px solid #ccc; margin: 10px 0; padding: 15px; }}
        .stats {{ background: #f0f8ff; }}
        .tables {{ background: #f8f8f0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .webdav-links {{ background: #fff0f8; }}
        a {{ color: #0066cc; text-decoration: none; margin-right: 15px; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>🏆 Tournament Tracker - Database Browser</h1>

    <div class="panel stats">
        <h2>📊 Database Statistics</h2>
        <p>Total Records: <strong>{stats.get('total_records', 'N/A')}</strong></p>
    </div>

    <div class="panel webdav-links">
        <h2>🌐 WebDAV & API Access</h2>
        <p><strong>WebDAV Endpoints:</strong></p>
        <a href="/webdav/data/players">📊 Player Rankings</a>
        <a href="/webdav/data/tournaments">🏆 Tournaments</a>
        <a href="/webdav/data/stats">📈 Statistics</a>
        <a href="/webdav/bonjour/">🏠 Bonjour Services</a>

        <p><strong>PROPFIND Discovery:</strong></p>
        <p><code>curl -X PROPFIND http://localhost:8081/webdav/</code></p>
        <p><code>curl -X PROPFIND http://localhost:8081/webdav/data/</code></p>
    </div>

    <div class="panel tables">
        <h2>📋 Available Data Tables</h2>
        <ul>
            <li><a href="/webdav/data/players">Players</a> - Player rankings and statistics</li>
            <li><a href="/webdav/data/tournaments">Tournaments</a> - Tournament information</li>
            <li><a href="/webdav/data/organizations">Organizations</a> - Tournament organizers</li>
            <li><a href="/webdav/data/logs">Logs</a> - System logs</li>
        </ul>
    </div>

    <p><a href="/">← Back to Tournament Tracker</a></p>
</body>
</html>"""

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        except Exception as e:
            tb = traceback.format_exc()
            error(f"Database browser error: {e}")
            error(f"Full traceback:\n{tb}")
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'<h1>Error: {str(e)}</h1><pre>{html.escape(tb)}</pre>'.encode('utf-8'))

    def _send_webdav_error(self, code, message):
        """Send WebDAV error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = {'error': message, 'code': code, 'timestamp': datetime.now().isoformat()}
        self.wfile.write(json.dumps(error_data, indent=2).encode('utf-8'))

class EnhancedPolymorphicWebEditor(PolymorphicWebEditor):
    """
    Enhanced universal web editor with advanced features:
    - Real-time service discovery updates
    - Interactive service testing
    - Advanced UI generation with forms
    - Service health monitoring integration
    - Error handling and recovery
    """
    
    def __init__(self):
        super().__init__()
        self._service_cache = {}
        self._last_discovery = None
        
        # Enhanced announcement
        announcer.announce(
            "Enhanced Universal Web Editor",
            [
                "Real-time service discovery with live updates",
                "Interactive testing interface for any discovered service", 
                "Dynamic form generation from service capabilities",
                "Integrated health monitoring and error handling",
                "Advanced UI with service categories and search",
                "WebSocket support for live service updates",
                "Service performance monitoring and analytics"
            ],
            [
                "Visit http://localhost:8081 for enhanced admin interface",
                "Test any service live with auto-generated forms",
                "Monitor service health and performance in real-time",
                "Search and filter services by capabilities"
            ]
        )
    
    @handle_errors(severity=ErrorSeverity.MEDIUM, context={"operation": "enhanced_service_discovery"})
    def ask(self, query: str) -> Any:
        """Enhanced ask with caching and advanced queries"""
        query_lower = query.lower().strip()
        
        if query_lower in ['enhanced services', 'all services with health']:
            return self._get_services_with_health()
        elif query_lower.startswith('search '):
            search_term = query[7:].strip()
            return self._search_services(search_term)
        elif query_lower in ['service stats', 'analytics']:
            return self._get_service_analytics()
        elif query_lower in ['health dashboard', 'system health']:
            return self._get_health_dashboard()
        else:
            return super().ask(query)
    
    @handle_errors(severity=ErrorSeverity.LOW, context={"operation": "enhanced_ui_generation"})
    def tell(self, format: str, data: Any = None) -> str:
        """Enhanced tell with advanced UI rendering"""
        if format.lower() == 'enhanced_html':
            return self._render_enhanced_html(data)
        elif format.lower() == 'dashboard':
            return self._render_dashboard_html(data)
        elif format.lower() == 'service_form':
            return self._render_service_form_html(data)
        else:
            return super().tell(format, data)
    
    @handle_errors(severity=ErrorSeverity.MEDIUM, context={"operation": "enhanced_service_actions"})
    def do(self, action: str) -> Any:
        """Enhanced do with advanced service interaction"""
        action_lower = action.lower().strip()
        
        if action_lower.startswith('test service '):
            service_name = action[13:].strip()
            return self._test_service_interactively(service_name)
        elif action_lower.startswith('benchmark '):
            service_name = action[10:].strip()
            return self._benchmark_service(service_name)
        elif action_lower in ['live update', 'websocket update']:
            return self._get_live_service_update()
        else:
            return super().do(action)
    
    def _get_services_with_health(self) -> Dict:
        """Get services with integrated health information"""
        try:
            # Try to get health monitor if available
            from utils.health_monitor import health_monitor
            services = self._get_discovered_services()
            health_data = health_monitor.ask("all services")
            
            enhanced_services = {}
            for name, service_data in services.items():
                enhanced_services[name] = {
                    **service_data,
                    'health': health_data.get(name, {'status': 'unknown'}),
                    'last_seen': service_data.get('last_announced', 'unknown')
                }
            
            return enhanced_services
        except Exception as e:
            handle_exception(e, {"operation": "get_services_with_health"})
            return self._get_discovered_services()
    
    def _search_services(self, search_term: str) -> Dict:
        """Search services by name, capabilities, or category"""
        services = self._get_discovered_services()
        matches = {}
        
        for name, data in services.items():
            # Search in service name
            if search_term.lower() in name.lower():
                matches[name] = data
                continue
            
            # Search in capabilities
            capabilities = data.get('capabilities', [])
            for capability in capabilities:
                if search_term.lower() in capability.lower():
                    matches[name] = data
                    break
            
            # Search in examples
            examples = data.get('examples', [])
            for example in examples:
                if search_term.lower() in example.lower():
                    matches[name] = data
                    break
        
        return matches
    
    def _get_service_analytics(self) -> Dict:
        """Get analytics about discovered services"""
        services = self._get_discovered_services()
        
        analytics = {
            'total_services': len(services),
            'categories': {},
            'capability_frequency': {},
            'health_summary': {'healthy': 0, 'unhealthy': 0, 'unknown': 0}
        }
        
        for name, data in services.items():
            # Category analysis
            category = self._categorize_service(name, data)
            analytics['categories'][category] = analytics['categories'].get(category, 0) + 1
            
            # Capability analysis
            for capability in data.get('capabilities', []):
                # Extract key words from capabilities
                words = capability.lower().split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        analytics['capability_frequency'][word] = analytics['capability_frequency'].get(word, 0) + 1
        
        return analytics
    
    def _get_health_dashboard(self) -> Dict:
        """Get comprehensive health dashboard data"""
        try:
            from utils.health_monitor import health_monitor
            from utils.error_handler import error_handler
            
            return {
                'services': self._get_services_with_health(),
                'system_health': health_monitor.ask("system health"),
                'recent_errors': error_handler.ask("recent errors"),
                'error_stats': error_handler.ask("error stats"),
                'timestamp': str(datetime.now())
            }
        except Exception as e:
            handle_exception(e, {"operation": "get_health_dashboard"})
            return {'error': 'Health dashboard unavailable'}
    
    def _test_service_interactively(self, service_name: str) -> Dict:
        """Test a service with common operations"""
        service_info = self._get_service_info(service_name)
        if not service_info:
            return {'error': f'Service {service_name} not found'}
        
        test_results = {
            'service': service_name,
            'timestamp': str(datetime.now()),
            'tests': []
        }
        
        # Try common ask operations
        common_asks = ['status', 'info', 'help', 'statistics']
        for ask_query in common_asks:
            try:
                result = self._call_service(f"{service_name} ask {ask_query}")
                test_results['tests'].append({
                    'operation': f'ask("{ask_query}")',
                    'success': True,
                    'result': str(result)[:200] + '...' if len(str(result)) > 200 else str(result)
                })
            except Exception as e:
                test_results['tests'].append({
                    'operation': f'ask("{ask_query}")',
                    'success': False,
                    'error': str(e)
                })
        
        return test_results
    
    def _get_live_service_update(self) -> Dict:
        """Get live update data for WebSocket or polling"""
        return {
            'timestamp': str(datetime.now()),
            'services': self._get_services_with_health(),
            'system_status': 'operational',
            'active_services': len(self._get_discovered_services())
        }
    
    def _render_enhanced_html(self, data: Any = None) -> str:
        """Render enhanced HTML interface with modern UI"""
        if data is None:
            data = self._get_services_with_health()
        
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Universal Web Editor</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
        .header h1 {{ margin: 0; }}
        .header p {{ margin: 5px 0 0 0; opacity: 0.8; }}
        .dashboard {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ margin-top: 0; color: #2c3e50; }}
        .service-list {{ list-style: none; padding: 0; }}
        .service-item {{ padding: 10px; border-left: 4px solid #3498db; margin: 10px 0; background: #f8f9fa; }}
        .service-healthy {{ border-left-color: #27ae60; }}
        .service-unhealthy {{ border-left-color: #e74c3c; }}
        .service-unknown {{ border-left-color: #95a5a6; }}
        .search-box {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 20px; }}
        .btn {{ background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
        .btn:hover {{ background: #2980b9; }}
        .status-indicator {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }}
        .status-healthy {{ background: #27ae60; }}
        .status-unhealthy {{ background: #e74c3c; }}
        .status-unknown {{ background: #95a5a6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌐 Enhanced Universal Web Editor</h1>
        <p>Real-time service discovery and management | {total_services} services discovered</p>
    </div>
    
    <div class="dashboard">
        <div class="card">
            <h3>🔍 Service Discovery</h3>
            <input type="text" class="search-box" placeholder="Search services, capabilities, or categories..." onkeyup="filterServices(this.value)">
            <ul class="service-list" id="serviceList">
                {service_items}
            </ul>
        </div>
        
        <div class="card">
            <h3>📊 System Health</h3>
            <div>Services: {total_services}</div>
            <div>Categories: {total_categories}</div>
            <button class="btn" onclick="refreshServices()">🔄 Refresh</button>
        </div>
    </div>
    
    <script>
        function filterServices(searchTerm) {{
            const items = document.querySelectorAll('.service-item');
            items.forEach(item => {{
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(searchTerm.toLowerCase()) ? 'block' : 'none';
            }});
        }}
        
        function refreshServices() {{
            window.location.reload();
        }}
        
        // Auto-refresh every 30 seconds
        setInterval(refreshServices, 30000);
    </script>
</body>
</html>"""
        
        # Generate service items
        service_items = ""
        total_categories = len(set(self._categorize_service(name, data) for name, data in data.items()))
        
        for name, service_data in data.items():
            health = service_data.get('health', {})
            health_status = health.get('status', 'unknown')
            health_class = f"service-{health_status}"
            status_class = f"status-{health_status}"
            
            capabilities = service_data.get('capabilities', [])[:3]  # Show first 3
            capability_text = ', '.join(capabilities)
            if len(service_data.get('capabilities', [])) > 3:
                capability_text += f" (+{len(service_data.get('capabilities', [])) - 3} more)"
            
            service_items += f"""
                <li class="service-item {health_class}">
                    <div><strong><span class="status-indicator {status_class}"></span>{name}</strong></div>
                    <div style="font-size: 0.9em; color: #666; margin-top: 5px;">{capability_text}</div>
                    <div style="font-size: 0.8em; color: #999; margin-top: 3px;">
                        Host: {service_data.get('host', 'unknown')} | Port: {service_data.get('port', 'N/A')}
                    </div>
                </li>
            """
        
        return html.format(
            total_services=len(data),
            total_categories=total_categories,
            service_items=service_items
        )


class ManagedWebEditorService(ManagedService):
    """Managed service wrapper for the Polymorphic Web Editor"""
    
    def __init__(self):
        super().__init__("web-editor", "tournament-web-editor")
        self.editor = EnhancedPolymorphicWebEditor()
        self.server = None
    
    def _advertise_mdns_service(self):
        """Advertise this service via mDNS with available switches"""
        try:
            from zeroconf import ServiceInfo, Zeroconf
            import socket

            # Create service info with switches in TXT record
            service_info = ServiceInfo(
                "_tournament._tcp.local.",
                "web-editor._tournament._tcp.local.",
                addresses=[socket.inet_aton("10.0.0.1")],
                port=8081,
                properties={
                    'switches': '--web,--edit-contacts',
                    'service': 'web-editor',
                    'description': 'Tournament Web Editor - HTTPS only'
                }
            )

            # Register the service
            zeroconf = Zeroconf()
            zeroconf.register_service(service_info)
            info("📡 Service advertised via mDNS: web-editor with switches --web, --edit-contacts")

        except Exception as e:
            warning(f"Failed to advertise service via mDNS: {e}")

    def run(self):
        """Run the web editor server"""
        info("Starting Polymorphic Web Editor on port 8081")
        info("Discovering services via mDNS")
        info("Interface adapts automatically to available services")

        # Create HTTPS-only server
        try:
            import ssl
            import pathlib

            # Use letsencrypt certificates
            cert_file = pathlib.Path("/etc/letsencrypt/live/zilogo.com/fullchain.pem")
            key_file = pathlib.Path("/etc/letsencrypt/live/zilogo.com/privkey.pem")

            if cert_file.exists() and key_file.exists():
                # Create HTTPS server
                self.server = ThreadingTCPServer(('10.0.0.1', 8081), PolymorphicWebRequestHandler)

                # Create SSL context
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(cert_file, key_file)
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                # Wrap server socket with SSL
                self.server.socket = ssl_context.wrap_socket(self.server.socket, server_side=True)

                info("🔒 HTTPS enabled with LetsEncrypt certificates")
                info("📍 Visit https://vpn.zilogo.com")
                info("🔌 WebSocket will use WSS (secure)")

                # Advertise service via mDNS with available switches
                self._advertise_mdns_service()
            else:
                error("⚠️  SSL certificates not found - HTTPS-only mode requires certificates")
                error("⚠️  Cannot start server without SSL certificates")
                return

        except Exception as e:
            error(f"HTTPS setup failed: {e}")
            error("⚠️  Cannot start server in HTTPS-only mode")
            return
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            info("Shutting down Polymorphic Web Editor")
            if self.server:
                self.server.shutdown()


def main():
    """Start the enhanced polymorphic web editor server with service management"""
    
    # Create process manager instance for compatibility
    _web_editor_process_manager = PolymorphicWebEditorProcessManager()
    
    # Announce the process manager
    announcer.announce(
        "PolymorphicWebEditorProcessManager", 
        [
            "I manage processes: services/polymorphic_web_editor.py",
            "I use ports: 8081", 
            "Call cleanup_processes to clean shutdown",
            "I am a PROCESS_MANAGER service"
        ]
    )
    
    # Start managed service
    with ManagedWebEditorService() as service:
        service.run()

# Global process manager instance for go.py integration
_web_editor_process_manager = PolymorphicWebEditorProcessManager()

# Announce our consolidated --web switch
def start_web_service(args=None):
    """Handler for --web switch - now starts persistent tournaments.local"""
    try:
        import subprocess
        import sys
        import os

        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'persistent_web_service.py')
        info(f"Starting persistent tournaments.local web service: {script_path}")

        # Start the persistent service in background
        process = subprocess.Popen([sys.executable, script_path],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        info(f"Persistent web service started with PID: {process.pid}")
        return [process.pid]

    except Exception as e:
        warning(f"Failed to start persistent web service: {e}")
        return []

# Service now advertises switches via mDNS
announcer.announce(
    "GoSwitch__web",
    [
        "Provides go.py flag: --web",
        "Help: START universal web editor (adapts to any mDNS service)",
        "Handler: start_web_service"
    ],
    examples=["./go.py --web"]
)

if __name__ == "__main__":
    # Import the persistent web service instead
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from persistent_web_service import main
    main()