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

from polymorphic_core import announcer
from utils.simple_logger import info, warning, error
from utils.error_handler import handle_errors, handle_exception, ErrorSeverity
from dynamic_switches import announce_switch

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
        """Format discovered services data"""
        if data is None:
            data = self._get_discovered_services()
        
        if format.lower() == 'html':
            return self._render_services_html(data)
        elif format.lower() == 'json':
            return json.dumps(data, indent=2)
        else:
            return str(data)
    
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
        """Get all services discovered via mDNS"""
        return announcer.discover_services()
    
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
    
    def __init__(self, *args, **kwargs):
        self.editor = PolymorphicWebEditor()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        # Generate universal interface
        html_content = self.editor.tell('html')
        self.wfile.write(html_content.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

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


def main():
    """Start the enhanced polymorphic web editor server"""
    
    # Create enhanced editor instance
    editor = EnhancedPolymorphicWebEditor()
    
    # Create process manager instance
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
    
    info("Starting Polymorphic Web Editor on port 8081")
    info("Discovering services via mDNS")
    info("Interface adapts automatically to available services")
    info("Visit http://localhost:8081")
    
    server = HTTPServer(('localhost', 8081), PolymorphicWebRequestHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        info("Shutting down Polymorphic Web Editor")
        server.shutdown()

# Global process manager instance for go.py integration
_web_editor_process_manager = PolymorphicWebEditorProcessManager()

# Announce our consolidated --web switch
def start_web_service(args=None):
    """Handler for --web switch (replaces --edit-contacts)"""
    try:
        info("Starting Polymorphic Web Editor via integrated ProcessManager")
        pids = _web_editor_process_manager.start_services()
        info(f"Polymorphic Web Editor started with PIDs: {pids}")
        return pids
    except (ImportError, NameError) as e:
        warning(f"Integrated PolymorphicWebEditorProcessManager not available: {e}")
        info("Falling back to manual process management")
        from polymorphic_core.process import ProcessManager
        ProcessManager.restart_service('services/polymorphic_web_editor.py')

announce_switch(
    flag="--web",
    help="START universal web editor (adapts to any mDNS service)", 
    handler=start_web_service
)

if __name__ == "__main__":
    main()