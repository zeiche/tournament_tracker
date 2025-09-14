#!/usr/bin/env python3
"""
WebDAV Database Browser Service - Refactored with Full Process Management

Complete refactor of WebDAV service using:
- BaseProcessManager for proper process lifecycle
- 3-method pattern: ask(), tell(), do()  
- Service locator for dependencies
- ManagedService for service identity
- Comprehensive error handling
- Port management and health monitoring
"""
import sys
import os
import json
import threading
import time
import socket
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.webdav_service_refactored")

from polymorphic_core.process_management import BaseProcessManager
from polymorphic_core.service_identity import ManagedService
from polymorphic_core.service_locator import get_service
from polymorphic_core import announcer, announces_capability
from utils.simple_logger import info, warning, error
from utils.error_handler import handle_errors, handle_exception, ErrorSeverity

try:
    from services.webdav_database_browser import create_webdav_app
    from wsgiref.simple_server import make_server
    WEBDAV_AVAILABLE = True
except ImportError as e:
    WEBDAV_AVAILABLE = False
    warning(f"WebDAV dependencies not available: {e}")


@announces_capability("WebDAV Database Browser (Refactored)")
class WebDAVServiceRefactored(ManagedService):
    """
    Refactored WebDAV Database Browser Service
    
    Implements full service patterns:
    - ask(), tell(), do() methods only
    - Service locator for dependencies  
    - Process management with lifecycle control
    - Health monitoring and automatic recovery
    """
    
    def __init__(self, prefer_network: bool = False):
        super().__init__("WebDAV Database Browser", prefer_network)
        
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.port = 8443
        self.host = "0.0.0.0"
        self.prefer_network = False
        
        # Service locator dependencies
        self._logger = None
        self._error_handler = None
        self._database = None
        
        # Announce capabilities
        announcer.announce(
            "WebDAV Database Browser Service (Refactored)",
            [
                "Virtual filesystem interface to tournament database",
                "Exposes model intelligence as browseable files",  
                "ask() - Query service status, stats, configurations",
                "tell() - Format service info, health reports, logs",
                "do() - Start/stop server, change ports, health checks",
                "Tournament analytics via /tournaments/tournament_123/analytics.html",
                "Player stats via /players/player_west/stats.html", 
                "Organization data via /organizations/org_runback/contacts.json",
                "Compatible with any WebDAV client or file manager",
                "Self-managing with automatic port conflict resolution"
            ],
            examples=[
                "service.ask('status') - Get server status",
                "service.tell('json') - Format status as JSON",
                "service.do('start port=8084') - Start on specific port",
                "service.do('restart') - Restart with current config",
                "service.do('stop') - Graceful shutdown"
            ]
        )
    
    # Service locator properties
    @property
    def logger(self):
        if self._logger is None:
            self._logger = get_service("logger", self.prefer_network)
        return self._logger
    
    @property 
    def error_handler(self):
        if self._error_handler is None:
            self._error_handler = get_service("error_handler", self.prefer_network)
        return self._error_handler
    
    @property
    def database(self):
        if self._database is None:
            self._database = get_service("database", self.prefer_network)  
        return self._database
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query WebDAV service for data using natural language"""
        query_lower = query.lower().strip()
        
        try:
            if query_lower in ['status', 'health', 'state']:
                return self._get_service_status()
            
            elif query_lower in ['stats', 'statistics', 'metrics']:
                return self._get_service_stats()
            
            elif query_lower in ['config', 'configuration', 'settings']:
                return self._get_service_config()
            
            elif query_lower in ['logs', 'log', 'history']:
                return self._get_service_logs()
            
            elif 'port' in query_lower:
                return {'current_port': self.port, 'is_available': self._is_port_available(self.port)}
            
            elif 'clients' in query_lower or 'connections' in query_lower:
                return self._get_client_info()
            
            elif 'database' in query_lower:
                return self._get_database_info()
            
            else:
                return {
                    'error': 'Unknown query',
                    'available_queries': ['status', 'stats', 'config', 'logs', 'port', 'clients', 'database'],
                    'examples': [
                        'ask("status") - Get service status',
                        'ask("stats") - Get usage statistics',
                        'ask("config") - Get configuration'
                    ]
                }
                
        except Exception as e:
            self.error_handler.handle_exception(e, ErrorSeverity.MEDIUM, f"WebDAV ask({query})")
            return {'error': str(e), 'query': query}
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format WebDAV service data for output"""
        if data is None:
            data = self.ask("status")
        
        try:
            if format.lower() == 'json':
                return json.dumps(data, indent=2, default=str)
            
            elif format.lower() in ['text', 'string', 'str']:
                return self._format_as_text(data)
            
            elif format.lower() == 'html':
                return self._format_as_html(data)
            
            elif format.lower() == 'markdown':
                return self._format_as_markdown(data)
            
            elif format.lower() in ['discord', 'slack']:
                return self._format_for_chat(data)
            
            else:
                return f"Unknown format '{format}'. Available: json, text, html, markdown, discord"
                
        except Exception as e:
            self.error_handler.handle_exception(e, ErrorSeverity.LOW, f"WebDAV tell({format})")
            return f"Error formatting data: {e}"
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform WebDAV service actions using natural language"""
        action_lower = action.lower().strip()
        
        try:
            if action_lower in ['start', 'startup', 'run'] or ('start' in action_lower):
                port = kwargs.get('port', self.port)
                if 'port=' in action:
                    try:
                        port = int(action.split('port=')[1].split()[0])
                    except:
                        pass
                return self._start_server(port)
            
            elif action_lower in ['stop', 'shutdown', 'halt']:
                return self._stop_server()
            
            elif action_lower in ['restart', 'reload', 'refresh']:
                self._stop_server()
                time.sleep(1)
                return self._start_server(self.port)
            
            elif action_lower in ['health', 'healthcheck', 'check']:
                return self._perform_health_check()
            
            elif 'port' in action_lower and any(word in action_lower for word in ['change', 'set', 'update']):
                try:
                    port = int(''.join(filter(str.isdigit, action)))
                    return self._change_port(port)
                except ValueError:
                    return {'error': 'Could not extract port number from action', 'action': action}
            
            elif action_lower in ['reset', 'initialize', 'init']:
                return self._reset_service()
            
            else:
                return {
                    'error': 'Unknown action',
                    'available_actions': ['start', 'stop', 'restart', 'health', 'change port', 'reset'],
                    'examples': [
                        'do("start") - Start WebDAV server',
                        'do("start port=8084") - Start on specific port', 
                        'do("stop") - Stop server',
                        'do("restart") - Restart server',
                        'do("health") - Perform health check'
                    ],
                    'action': action
                }
                
        except Exception as e:
            self.error_handler.handle_exception(e, ErrorSeverity.HIGH, context=f"WebDAV do({action})")
            return {'error': str(e), 'action': action}
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        return {
            'service': 'WebDAV Database Browser',
            'is_running': self.is_running,
            'port': self.port,
            'host': self.host,
            'process_id': os.getpid(),
            'uptime_seconds': time.time() - getattr(self, 'start_time', time.time()),
            'server_thread_active': self.server_thread and self.server_thread.is_alive() if self.server_thread else False,
            'port_available': self._is_port_available(self.port) if not self.is_running else True,
            'webdav_dependencies': WEBDAV_AVAILABLE,
            'last_health_check': getattr(self, 'last_health_check', None),
            'error_count': getattr(self, 'error_count', 0)
        }
    
    def _get_service_stats(self) -> Dict[str, Any]:
        """Get service usage statistics"""
        return {
            'requests_served': getattr(self, 'requests_served', 0),
            'errors_encountered': getattr(self, 'error_count', 0),
            'uptime_seconds': time.time() - getattr(self, 'start_time', time.time()),
            'database_queries': getattr(self, 'db_queries', 0),
            'virtual_files_served': getattr(self, 'files_served', 0),
            'active_connections': getattr(self, 'active_connections', 0),
            'port_conflicts_resolved': getattr(self, 'port_conflicts', 0)
        }
    
    def _get_service_config(self) -> Dict[str, Any]:
        """Get service configuration"""
        return {
            'host': self.host,
            'port': self.port,
            'webdav_enabled': WEBDAV_AVAILABLE,
            'readonly_mode': True,
            'virtual_filesystem': {
                'tournaments': 'Tournament data and analytics',
                'players': 'Player statistics and performance',
                'organizations': 'Organization info and contacts'
            },
            'authentication': 'anonymous',
            'service_locator_enabled': True,
            'bonjour_announcements': True
        }
    
    def _get_service_logs(self) -> List[Dict[str, Any]]:
        """Get recent service logs"""
        return getattr(self, 'recent_logs', [
            {'timestamp': datetime.now().isoformat(), 'level': 'info', 'message': 'Service initialized'},
            {'timestamp': datetime.now().isoformat(), 'level': 'info', 'message': 'Bonjour announcements active'}
        ])
    
    def _get_client_info(self) -> Dict[str, Any]:
        """Get WebDAV client information"""
        return {
            'active_connections': getattr(self, 'active_connections', 0),
            'total_clients_served': getattr(self, 'total_clients', 0),
            'supported_clients': [
                'Any WebDAV client',
                'File managers (Nautilus, Finder, Explorer)',
                'WebDAV mounting tools',
                'Web browsers (limited functionality)',
                'Command line tools (cadaver, curl)'
            ]
        }
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get database connection info"""
        try:
            if self.database:
                db_stats = self.database.ask("stats")
                return {
                    'database_available': True,
                    'database_stats': db_stats,
                    'virtual_structure_ready': True
                }
            else:
                return {'database_available': False, 'error': 'Database service not accessible'}
        except Exception as e:
            return {'database_available': False, 'error': str(e)}
    
    def _start_server(self, port: int = None) -> Dict[str, Any]:
        """Start WebDAV server with port conflict resolution"""
        if not WEBDAV_AVAILABLE:
            return {'error': 'WebDAV dependencies not available', 'success': False}
        
        if self.is_running:
            return {'error': 'Server already running', 'port': self.port, 'success': False}
        
        if port is None:
            port = self.port
        
        # Use BaseProcessManager port resolution pattern
        original_port = port
        if not self._is_port_available(port):
            port = 8444  # Fallback port like other web services
            if not self._is_port_available(port):
                return {'error': f'Both ports {original_port} and {port} unavailable', 'success': False}
        
        try:
            self.port = port
            self.start_time = time.time()
            
            # Create WebDAV app
            self.logger.info("Creating WebDAV app...")
            app = create_webdav_app()
            self.logger.info("WebDAV app created successfully")

            self.logger.info(f"Creating HTTP server on {self.host}:{self.port}...")
            self.server = make_server(self.host, self.port, app)
            self.logger.info(f"HTTP server created, binding to port {self.port}...")

            # Start server in separate thread (non-daemon so it keeps process alive)
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=False,
                name=f"WebDAV-Server-{self.port}"
            )
            self.logger.info("Starting server thread...")
            self.server_thread.start()

            # Give server a moment to start up
            time.sleep(0.1)
            self.logger.info(f"Server thread started, WebDAV listening on port {self.port}")
            self.is_running = True
            
            # Update announcements
            announcer.announce(
                f"WebDAV Database Browser (Running on Port {self.port})",
                [
                    f"🗂️  WebDAV server running on {self.host}:{self.port}",
                    f"🌐 Access via: http://localhost:{self.port}",
                    "Virtual filesystem interface to database",
                    "Compatible with any WebDAV client",
                    "Read-only access for data safety",
                    "Status: running"
                ]
            )
            
            self.logger.info(f"WebDAV server started on port {self.port}")
            
            return {
                'success': True,
                'port': self.port,
                'url': f"http://localhost:{self.port}",
                'port_changed': port != original_port,
                'message': f'WebDAV server started on port {self.port}'
            }
            
        except Exception as e:
            self.is_running = False
            self.error_handler.handle_exception(e, ErrorSeverity.HIGH, context="WebDAV server start")
            return {'error': str(e), 'success': False}
    
    def _stop_server(self) -> Dict[str, Any]:
        """Stop WebDAV server gracefully"""
        if not self.is_running:
            return {'error': 'Server not running', 'success': False}
        
        try:
            self.is_running = False
            
            if self.server:
                self.server.shutdown()
                self.server = None
            
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5)
                
            announcer.announce(
                "WebDAV Database Browser (Stopped)", 
                ["WebDAV server stopped"],
                status="stopped"
            )
            
            self.logger.info("WebDAV server stopped")
            
            return {'success': True, 'message': 'WebDAV server stopped gracefully'}
            
        except Exception as e:
            self.error_handler.handle_exception(e, ErrorSeverity.MEDIUM, "WebDAV server stop")
            return {'error': str(e), 'success': False}
    
    def _run_server(self):
        """Run server loop in separate thread"""
        try:
            self.logger.info(f"WebDAV server thread starting on port {self.port}")
            self.logger.info(f"Server listening on {self.server.server_address}")
            self.server.serve_forever()
        except Exception as e:
            self.logger.error(f"WebDAV server error: {e}")
            self.is_running = False
            self.error_handler.handle_exception(e, ErrorSeverity.HIGH, context="WebDAV server loop")
    
    def _is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.host, port))
                return True
            except OSError:
                return False

    
    def _change_port(self, new_port: int) -> Dict[str, Any]:
        """Change server port with automatic restart"""
        was_running = self.is_running
        
        if was_running:
            stop_result = self._stop_server()
            if not stop_result['success']:
                return stop_result
        
        old_port = self.port
        self.port = new_port
        
        if was_running:
            start_result = self._start_server(new_port)
            return {
                **start_result,
                'old_port': old_port,
                'message': f'Port changed from {old_port} to {new_port}'
            }
        else:
            return {
                'success': True,
                'old_port': old_port,
                'new_port': new_port,
                'message': f'Port changed to {new_port} (server was not running)'
            }
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        self.last_health_check = datetime.now().isoformat()
        
        health = {
            'timestamp': self.last_health_check,
            'overall_health': 'healthy',
            'checks': {}
        }
        
        # Check server status
        if self.is_running:
            health['checks']['server_running'] = {'status': 'pass', 'message': 'Server is running'}
        else:
            health['checks']['server_running'] = {'status': 'fail', 'message': 'Server is not running'}
            health['overall_health'] = 'unhealthy'
        
        # Check port availability
        if not self.is_running and not self._is_port_available(self.port):
            health['checks']['port_available'] = {'status': 'fail', 'message': f'Port {self.port} is not available'}
            health['overall_health'] = 'degraded'
        else:
            health['checks']['port_available'] = {'status': 'pass', 'message': f'Port {self.port} is available'}
        
        # Check dependencies
        health['checks']['webdav_dependencies'] = {
            'status': 'pass' if WEBDAV_AVAILABLE else 'fail',
            'message': 'WebDAV dependencies available' if WEBDAV_AVAILABLE else 'WebDAV dependencies missing'
        }
        
        # Check database connection
        try:
            db_status = self.database.ask("health") if self.database else None
            health['checks']['database_connection'] = {
                'status': 'pass' if db_status else 'fail',
                'message': 'Database accessible' if db_status else 'Database not accessible'
            }
        except:
            health['checks']['database_connection'] = {'status': 'fail', 'message': 'Database connection error'}
            health['overall_health'] = 'degraded'
        
        return health
    
    def _reset_service(self) -> Dict[str, Any]:
        """Reset service to initial state"""
        try:
            if self.is_running:
                self._stop_server()
            
            # Reset internal state
            self.error_count = 0
            self.requests_served = 0
            self.db_queries = 0
            self.files_served = 0
            
            return {'success': True, 'message': 'Service reset to initial state'}
            
        except Exception as e:
            return {'error': str(e), 'success': False}
    
    def _format_as_text(self, data: Any) -> str:
        """Format data as human-readable text"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
            return '\n'.join(lines)
        else:
            return str(data)
    
    def _format_as_html(self, data: Any) -> str:
        """Format data as HTML"""
        if isinstance(data, dict):
            html = "<table>\n"
            for key, value in data.items():
                html += f"  <tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>\n"
            html += "</table>"
            return html
        else:
            return f"<p>{data}</p>"
    
    def _format_as_markdown(self, data: Any) -> str:
        """Format data as Markdown"""
        if isinstance(data, dict):
            lines = ["| Field | Value |", "|-------|-------|"]
            for key, value in data.items():
                lines.append(f"| {key.replace('_', ' ').title()} | {value} |")
            return '\n'.join(lines)
        else:
            return f"```\n{data}\n```"
    
    def _format_for_chat(self, data: Any) -> str:
        """Format data for Discord/Slack"""
        if isinstance(data, dict):
            lines = ["**WebDAV Status:**"]
            for key, value in data.items():
                emoji = "✅" if key == 'is_running' and value else "❌" if key == 'is_running' else "🔹"
                lines.append(f"{emoji} **{key.replace('_', ' ').title()}:** {value}")
            return '\n'.join(lines)
        else:
            return f"📋 {data}"
    
    def run(self):
        """Run method required by ManagedService - no-op for context manager usage"""
        pass


class WebDAVProcessManager(BaseProcessManager):
    """Process manager for WebDAV service - integrated with web services"""

    SERVICE_NAME = "WebDAVDatabaseBrowser"
    PROCESSES = ["webdav_service_refactored.py"]
    PORTS = [8443, 8444]  # WebDAV ports (HTTP + auto-HTTPS)
    
    def __init__(self):
        super().__init__()
        self.webdav_service = None
    
    def get_process_patterns(self) -> List[str]:
        return ["webdav_service", "webdav_launcher", "webdav"]
    
    def start_services(self):
        """Start WebDAV service"""
        if not self.webdav_service:
            self.webdav_service = WebDAVServiceRefactored()
        
        result = self.webdav_service.do("start")
        return result.get('success', False)
    
    def cleanup_processes(self):
        """Clean shutdown of WebDAV service"""
        if self.webdav_service:
            result = self.webdav_service.do("stop")
            return result.get('success', False)
        return True


# Global service instance for easy access
webdav_service = None
webdav_process_manager = WebDAVProcessManager()


def get_webdav_service() -> WebDAVServiceRefactored:
    """Get global WebDAV service instance"""
    global webdav_service
    if webdav_service is None:
        webdav_service = WebDAVServiceRefactored()
    return webdav_service


if __name__ == "__main__":
    # This should never run due to execution guard
    print("ERROR: This module should be run through go.py")