#!/usr/bin/env python3
"""
webdav_bonjour_service.py - WebDAV interface using only Bonjour-discovered services

This service creates a WebDAV-compatible interface by:
1. Discovering services via Bonjour announcements
2. Using only advertised capabilities (ask/tell/do pattern)
3. Mapping WebDAV operations to service method calls
4. Providing RESTful access to tournament data

Key principle: Uses ONLY what's advertised via mDNS, no filesystem access
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import threading
import time

# Use Bonjour service discovery
from polymorphic_core.service_locator import ServiceLocator
from polymorphic_core import announcer
from utils.ssl_web_server import create_ssl_server

class BonjourWebDAVHandler(BaseHTTPRequestHandler):
    """WebDAV handler that uses only Bonjour-discovered services"""
    
    def __init__(self, *args, **kwargs):
        self.service_locator = ServiceLocator()
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Override to prevent spam"""
        pass
    
    def do_OPTIONS(self):
        """Handle WebDAV OPTIONS request"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('DAV', '1')
        self.send_header('Allow', 'GET, POST, PUT, DELETE, PROPFIND, OPTIONS')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PROPFIND, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Depth, Authorization')
        self.end_headers()
    
    def do_PROPFIND(self):
        """Handle WebDAV PROPFIND - discover available services and capabilities"""
        try:
            # Get discovered services
            database = self.service_locator.get_service('database')
            
            # Parse the path to determine what to discover
            path = self.path.strip('/')
            
            if not path or path == '/':
                # Root level - show available service categories
                resources = self._get_root_resources()
            elif path == 'services':
                # Show available services
                resources = self._get_service_resources()
            elif path == 'data':
                # Show available data endpoints
                resources = self._get_data_resources()
            elif path.startswith('data/'):
                # Show specific data collections
                data_type = path.split('/', 1)[1]
                resources = self._get_collection_resources(data_type)
            else:
                resources = []
            
            # Generate WebDAV PROPFIND response
            response_xml = self._generate_propfind_response(resources)
            
            self.send_response(207, 'Multi-Status')
            self.send_header('Content-Type', 'application/xml')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_xml.encode('utf-8'))
            
        except Exception as e:
            self._send_error_response(500, f"PROPFIND error: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests for data access"""
        try:
            path = self.path.strip('/')
            query_params = parse_qs(urlparse(self.path).query)
            
            # Route based on path
            if not path or path == '/':
                # Root - show API documentation
                self._send_api_documentation()
            elif path == 'services':
                # List discovered services
                self._send_service_list()
            elif path == 'data':
                # List available data types
                self._send_data_types()
            elif path.startswith('data/'):
                # Access specific data
                self._send_data_response(path, query_params)
            else:
                self._send_error_response(404, "Resource not found")
                
        except Exception as e:
            self._send_error_response(500, f"GET error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests for service actions"""
        try:
            path = self.path.strip('/')
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            if path.startswith('services/'):
                # Execute service action
                service_name = path.split('/', 1)[1]
                self._execute_service_action(service_name, post_data)
            else:
                self._send_error_response(404, "Service not found")
                
        except Exception as e:
            self._send_error_response(500, f"POST error: {str(e)}")
    
    def _get_root_resources(self) -> List[Dict]:
        """Get root level WebDAV resources"""
        return [
            {
                'name': 'services',
                'type': 'collection',
                'description': 'Discovered Bonjour services'
            },
            {
                'name': 'data', 
                'type': 'collection',
                'description': 'Tournament data via service APIs'
            }
        ]
    
    def _get_service_resources(self) -> List[Dict]:
        """Get available services via service locator"""
        resources = []
        
        # Try to access services through the locator
        try:
            database = self.service_locator.get_service('database')
            if database:
                resources.append({
                    'name': 'database',
                    'type': 'service',
                    'description': 'Database service with ask/tell/do interface',
                    'capabilities': [
                        'ask("top 10 players")',
                        'ask("stats")', 
                        'ask("player <name>")',
                        'tell("json", data)',
                        'do("update ...")'
                    ]
                })
        except:
            pass
            
        try:
            logger = self.service_locator.get_service('logger')
            if logger:
                resources.append({
                    'name': 'logger',
                    'type': 'service', 
                    'description': 'Logging service',
                    'capabilities': ['info()', 'warn()', 'error()']
                })
        except:
            pass
            
        return resources
    
    def _get_data_resources(self) -> List[Dict]:
        """Get available data endpoints - dynamically discover all database tables"""
        resources = []
        
        # Get database service to discover tables
        database = self.service_locator.get_service('database')
        if database:
            try:
                # Ask database for list of tables
                tables_result = database.ask("tables")
                if isinstance(tables_result, list):
                    for table in tables_result:
                        if table != 'sqlite_sequence':  # Skip SQLite internal table
                            resources.append({
                                'name': table,
                                'type': 'collection',
                                'description': f'Data from {table} table'
                            })
                else:
                    # Fallback - hardcoded list of known tables
                    known_tables = [
                        'tournaments', 'players', 'organizations', 'tournament_placements',
                        'organization_contacts', 'attendance_records', 'storage_content',
                        'log_entries', 'log_aggregations', 'log_snapshots', 'service_cache',
                        'service_cache_entries', 'log', 'service_state'
                    ]
                    for table in known_tables:
                        resources.append({
                            'name': table,
                            'type': 'collection', 
                            'description': f'Data from {table} table'
                        })
            except:
                # Final fallback
                pass
        
        # Add special endpoints
        resources.extend([
            {
                'name': 'stats',
                'type': 'resource',
                'description': 'Database statistics and summary'
            },
            {
                'name': 'logs',
                'type': 'collection',
                'description': 'System logs and events'
            }
        ])
        
        return resources
    
    def _get_collection_resources(self, data_type: str) -> List[Dict]:
        """Get resources for a specific data collection"""
        database = self.service_locator.get_service('database')
        resources = []
        
        try:
            if data_type == 'players':
                # Get player rankings to show available players
                rankings = database.ask('top 10 players')
                if isinstance(rankings, dict) and 'rankings' in rankings:
                    for player in rankings['rankings']:
                        resources.append({
                            'name': player['gamer_tag'],
                            'type': 'resource',
                            'description': f"Player {player['gamer_tag']} - {player['tournaments']} tournaments"
                        })
            elif data_type == 'stats':
                resources.append({
                    'name': 'summary',
                    'type': 'resource', 
                    'description': 'Database summary statistics'
                })
            elif data_type == 'logs':
                # Get log entries from logger service
                logger = self.service_locator.get_service('logger')
                if logger:
                    try:
                        # Try to get recent logs
                        recent_logs = logger.ask('recent logs')
                        if isinstance(recent_logs, list):
                            for i, log_entry in enumerate(recent_logs[:20]):  # Show last 20 logs
                                resources.append({
                                    'name': f'log_{i+1:03d}.txt',
                                    'type': 'resource',
                                    'description': f'Log entry: {log_entry.get("message", "Unknown")[:50]}...'
                                })
                        else:
                            # Fallback - create some default log views
                            resources.extend([
                                {
                                    'name': 'recent.txt',
                                    'type': 'resource',
                                    'description': 'Recent log entries'
                                },
                                {
                                    'name': 'errors.txt', 
                                    'type': 'resource',
                                    'description': 'Error log entries'
                                },
                                {
                                    'name': 'warnings.txt',
                                    'type': 'resource', 
                                    'description': 'Warning log entries'
                                }
                            ])
                    except:
                        # Fallback if logger doesn't support ask()
                        resources.append({
                            'name': 'system.txt',
                            'type': 'resource',
                            'description': 'System log output'
                        })
        except:
            pass
            
        return resources
    
    def _generate_propfind_response(self, resources: List[Dict]) -> str:
        """Generate WebDAV PROPFIND XML response"""
        multistatus = ET.Element('D:multistatus')
        multistatus.set('xmlns:D', 'DAV:')
        
        for resource in resources:
            response = ET.SubElement(multistatus, 'D:response')
            
            href = ET.SubElement(response, 'D:href')
            href.text = f"/{resource['name']}"
            
            propstat = ET.SubElement(response, 'D:propstat')
            prop = ET.SubElement(propstat, 'D:prop')
            
            # Add resource properties
            displayname = ET.SubElement(prop, 'D:displayname')
            displayname.text = resource['name']
            
            if resource['type'] == 'collection':
                ET.SubElement(prop, 'D:resourcetype').append(ET.Element('D:collection'))
            else:
                ET.SubElement(prop, 'D:resourcetype')
            
            # Add custom properties
            description = ET.SubElement(prop, 'description')
            description.text = resource.get('description', '')
            
            if 'capabilities' in resource:
                capabilities = ET.SubElement(prop, 'capabilities')
                capabilities.text = ', '.join(resource['capabilities'])
            
            status = ET.SubElement(propstat, 'D:status')
            status.text = 'HTTP/1.1 200 OK'
        
        return ET.tostring(multistatus, encoding='unicode')
    
    def _send_api_documentation(self):
        """Send API documentation"""
        docs = {
            'name': 'Tournament Tracker WebDAV API',
            'description': 'WebDAV interface using Bonjour-discovered services',
            'endpoints': {
                '/services': 'List discovered services',
                '/data': 'List available data types',
                '/data/players': 'Player rankings and data',
                '/data/tournaments': 'Tournament information',
                '/data/stats': 'Database statistics'
            },
            'examples': {
                'Get player rankings': 'GET /data/players',
                'Get specific player': 'GET /data/players?name=MkLeo',
                'Get stats': 'GET /data/stats',
                'Discover services': 'PROPFIND /services'
            }
        }
        
        self._send_json_response(docs)
    
    def _send_service_list(self):
        """Send list of discovered services"""
        services = self._get_service_resources()
        self._send_json_response({
            'services': services,
            'discovery_method': 'Bonjour service locator',
            'timestamp': datetime.now().isoformat()
        })
    
    def _send_data_types(self):
        """Send available data types"""
        data_types = self._get_data_resources()
        self._send_json_response({
            'data_types': data_types,
            'access_method': 'Service ask/tell/do pattern',
            'timestamp': datetime.now().isoformat()
        })
    
    def _send_data_response(self, path: str, query_params: Dict):
        """Send data response using service APIs"""
        database = self.service_locator.get_service('database')
        path_parts = path.split('/')
        
        if len(path_parts) < 2:
            self._send_error_response(400, "Invalid data path")
            return
            
        data_type = path_parts[1]
        
        try:
            if data_type == 'stats':
                result = database.ask('stats')
            elif data_type == 'logs':
                # Handle logs via logger service
                logger = self.service_locator.get_service('logger')
                if logger:
                    result = logger.ask('recent logs')
                else:
                    result = {"error": "Logger service not available"}
            else:
                # Generic table access - ask database for table data
                if 'id' in query_params:
                    # Get specific record by ID
                    record_id = query_params['id'][0]
                    result = database.ask(f'{data_type} {record_id}')
                elif 'limit' in query_params:
                    # Get limited records
                    limit = int(query_params['limit'][0])
                    result = database.ask(f'all {data_type} limit {limit}')
                else:
                    # Get all records from table by default
                    result = database.ask(f'all {data_type}')
            
            # Format response
            if isinstance(result, dict) and 'error' in result:
                self._send_error_response(404, result['error'])
            else:
                # Use service tell() method to format response
                formatted = database.tell('json', result)
                if isinstance(formatted, str):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(formatted.encode('utf-8'))
                else:
                    self._send_json_response(result)
                    
        except Exception as e:
            self._send_error_response(500, f"Data access error: {str(e)}")
    
    def _execute_service_action(self, service_name: str, post_data: str):
        """Execute action on a service using do() method"""
        try:
            data = json.loads(post_data)
            action = data.get('action', '')
            
            if service_name == 'database':
                database = self.service_locator.get_service('database')
                result = database.do(action)
                self._send_json_response(result)
            else:
                self._send_error_response(404, f"Service {service_name} not found")
                
        except Exception as e:
            self._send_error_response(500, f"Action execution error: {str(e)}")
    
    def _send_json_response(self, data: Any):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode('utf-8'))
    
    def _send_error_response(self, code: int, message: str):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = {
            'error': message,
            'code': code,
            'timestamp': datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(error_data, indent=2).encode('utf-8'))


class BonjourWebDAVService:
    """WebDAV service using Bonjour-discovered capabilities"""
    
    def __init__(self, port: int = 8088):
        self.port = port
        self.ssl_server = None
        
        # Announce ourselves
        announcer.announce(
            "WebDAV Bonjour Service",
            [
                "WebDAV interface using ONLY Bonjour-discovered services",
                "PROPFIND for service discovery",
                "GET /data/players - player rankings via ask()",
                "GET /data/stats - database stats via ask()",
                "Uses service tell() for formatting",
                "Uses service do() for actions",
                "No filesystem access - pure service calls"
            ],
            [
                f"curl -X PROPFIND http://localhost:{port}/services",
                f"curl http://localhost:{port}/data/players",
                f"curl http://localhost:{port}/data/stats",
                f'curl -X POST http://localhost:{port}/services/database -d \'{{\"action\":\"list capabilities\"}}\''
            ]
        )
    
    def start(self):
        """Start the WebDAV server with SSL support"""
        try:
            # Create SSL-enabled server (HTTP + HTTPS)
            self.ssl_server = create_ssl_server(
                BonjourWebDAVHandler, 
                self.port, 
                "vpn.zilogo.com"
            )
            
            if self.ssl_server.start():
                print(f"📋 PROPFIND endpoints:")
                print(f"   http://vpn.zilogo.com:{self.port}/services")
                print(f"   https://vpn.zilogo.com:{self.port + 1000}/services") 
                print(f"📊 Data endpoints:")
                print(f"   http://vpn.zilogo.com:{self.port}/data/players")
                print(f"   https://vpn.zilogo.com:{self.port + 1000}/data/players")
                return True
            else:
                return False
            
        except Exception as e:
            print(f"❌ Failed to start WebDAV service: {e}")
            return False
    
    def stop(self):
        """Stop the WebDAV server"""
        if self.ssl_server:
            self.ssl_server.stop()
            print("🛑 WebDAV Bonjour Service stopped")


# Service instance for import
webdav_bonjour_service = BonjourWebDAVService()

def main():
    """Run the WebDAV service"""
    service = BonjourWebDAVService()
    
    if service.start():
        try:
            print("Press Ctrl+C to stop the service")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            service.stop()
    else:
        print("❌ Failed to start service")

if __name__ == "__main__":
    main()