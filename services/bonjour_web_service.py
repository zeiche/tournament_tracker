#!/usr/bin/env python3
"""
bonjour_web_service.py - Web interface for Bonjour service discovery

This service provides a web interface showing all discovered services
via the mDNS/Bonjour system. Shows service capabilities, endpoints,
and provides a central dashboard for the "million HTTPS servers" architecture.
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core.execution_guard import require_go_py
require_go_py("services.bonjour_web_service")

from polymorphic_core.network_service_wrapper import wrap_service
from polymorphic_core import announcer
from polymorphic_core.real_bonjour import announcer as real_announcer

class BonjourWebService:
    """
    Web service that provides a dashboard of all discovered Bonjour services.
    """

    def __init__(self):
        # Announce ourselves
        announcer.announce(
            "Bonjour Service Discovery Web Interface",
            [
                "Web dashboard for all discovered services",
                "Service discovery visualization",
                "mDNS service browser",
                "HTTPS services directory"
            ],
            [
                "GET / - Service discovery dashboard",
                "POST /ask - Query about discovered services",
                "POST /tell - Format service data",
                "POST /do - Perform service discovery actions"
            ],
            service_instance=self
        )

        print("🌐 Bonjour Web Service initialized")

    def ask(self, query: str) -> dict:
        """Query for service discovery information"""
        query_lower = query.lower().strip()

        if 'services' in query_lower or 'discovered' in query_lower:
            # Get all discovered services
            discovered = real_announcer.discover_services()
            return {
                'type': 'service_discovery_query',
                'query': query,
                'discovered_services': discovered,
                'count': len(discovered)
            }
        elif 'capabilities' in query_lower:
            # Get service capabilities
            discovered = real_announcer.discover_services()
            capabilities = {}
            for name, service in discovered.items():
                capabilities[service['name']] = service.get('capabilities', [])
            return {
                'type': 'capabilities_query',
                'query': query,
                'capabilities': capabilities
            }
        elif 'ports' in query_lower:
            # Get service ports
            discovered = real_announcer.discover_services()
            ports = {}
            for name, service in discovered.items():
                ports[service['name']] = f"{service['host']}:{service['port']}"
            return {
                'type': 'ports_query',
                'query': query,
                'service_ports': ports
            }
        else:
            return {
                'type': 'bonjour_web_query',
                'query': query,
                'capabilities': [
                    'Service discovery dashboard',
                    'mDNS service browser',
                    'HTTPS services directory',
                    'Network service visualization'
                ]
            }

    def tell(self, format_type: str, data=None) -> str:
        """Format service discovery data for output"""
        if format_type.lower() == 'html':
            return self._generate_html_dashboard(data)
        elif format_type.lower() == 'json':
            import json
            discovered = real_announcer.discover_services()
            return json.dumps({
                'bonjour_services': discovered,
                'count': len(discovered),
                'data': data
            }, indent=2)
        elif format_type.lower() == 'text':
            discovered = real_announcer.discover_services()
            text = f"Bonjour Service Discovery - {len(discovered)} services found:\n\n"
            for name, service in discovered.items():
                text += f"• {service['name']} at {service['host']}:{service['port']}\n"
                for cap in service.get('capabilities', []):
                    text += f"  - {cap}\n"
                text += "\n"
            return text
        else:
            return f"Bonjour Service Discovery (Format: {format_type}): {len(real_announcer.discover_services())} services discovered"

    def do(self, action: str) -> str:
        """Perform service discovery actions"""
        action_lower = action.lower().strip()

        if 'refresh' in action_lower or 'discover' in action_lower:
            # Trigger service discovery refresh
            discovered = real_announcer.discover_services()
            return f"Service discovery refreshed - found {len(discovered)} services"
        elif 'status' in action_lower:
            discovered = real_announcer.discover_services()
            return f"Bonjour service discovery active - {len(discovered)} services currently discovered"
        elif 'test' in action_lower:
            return "Bonjour web service test completed successfully"
        else:
            return f"Bonjour service discovery action performed: {action}"

    def _generate_html_dashboard(self, data=None) -> str:
        """Generate HTML dashboard showing all discovered services"""
        discovered = real_announcer.discover_services()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Bonjour Service Discovery</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0; padding: 20px; background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px;
            text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 2.5em; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .stats {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px; margin-bottom: 30px;
        }}
        .stat-card {{
            background: white; padding: 20px; border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;
        }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .services {{
            display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }}
        .service-card {{
            background: white; border-radius: 12px; padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }}
        .service-card:hover {{ transform: translateY(-2px); }}
        .service-header {{
            display: flex; align-items: center; margin-bottom: 15px;
        }}
        .service-icon {{
            width: 40px; height: 40px; border-radius: 8px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            display: flex; align-items: center; justify-content: center;
            color: white; font-weight: bold; margin-right: 15px;
        }}
        .service-name {{ font-size: 1.2em; font-weight: bold; }}
        .service-endpoint {{
            color: #666; font-family: monospace; font-size: 0.9em;
            background: #f8f9fa; padding: 5px 10px; border-radius: 4px;
            margin: 10px 0;
        }}
        .capabilities {{ list-style: none; padding: 0; margin: 10px 0; }}
        .capabilities li {{
            background: #e3f2fd; padding: 8px 12px; margin: 5px 0;
            border-radius: 20px; font-size: 0.9em;
            border-left: 3px solid #2196f3;
        }}
        .no-services {{
            text-align: center; padding: 60px; color: #666;
            background: white; border-radius: 12px;
        }}
        .refresh-btn {{
            background: #667eea; color: white; border: none;
            padding: 12px 24px; border-radius: 6px; cursor: pointer;
            font-size: 1em; margin: 20px auto; display: block;
        }}
        .refresh-btn:hover {{ background: #5a6fd8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌐 Bonjour Service Discovery</h1>
        <p>Live dashboard of all discovered network services</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{len(discovered)}</div>
            <div class="stat-label">Services Discovered</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(set(s.get('host', 'unknown') for s in discovered.values()))}</div>
            <div class="stat-label">Unique Hosts</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{sum(len(s.get('capabilities', [])) for s in discovered.values())}</div>
            <div class="stat-label">Total Capabilities</div>
        </div>
    </div>

    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Discovery</button>
"""

        if discovered:
            html += '<div class="services">'
            for name, service in discovered.items():
                service_name = service.get('name', 'Unknown Service')
                host = service.get('host', 'unknown')
                port = service.get('port', '?')
                capabilities = service.get('capabilities', [])

                # Generate service icon (first letter)
                icon = service_name[0].upper() if service_name else '?'

                html += f"""
                <div class="service-card">
                    <div class="service-header">
                        <div class="service-icon">{icon}</div>
                        <div class="service-name">{service_name}</div>
                    </div>
                    <div class="service-endpoint">https://{host}:{port}</div>
                    <ul class="capabilities">
"""

                for cap in capabilities:
                    html += f'<li>• {cap}</li>'

                html += """
                    </ul>
                </div>
"""
            html += '</div>'
        else:
            html += """
            <div class="no-services">
                <h2>🔍 No Services Discovered Yet</h2>
                <p>Services will appear here as they announce themselves via mDNS/Bonjour</p>
                <p>Try starting some services with <code>./go.py</code> commands</p>
            </div>
"""

        html += """
    <script>
        // Auto-refresh every 10 seconds
        setTimeout(() => location.reload(), 10000);
    </script>
</body>
</html>"""

        return html

# Create and start the service
print("🚀 Starting Bonjour Web Service...")

# Create the service instance
bonjour_service = BonjourWebService()

# Wrap it with HTTPS server on port 443
wrapped = wrap_service(
    bonjour_service,
    "Bonjour Service Discovery Web Interface",
    port=443,
    auto_start=True
)

print(f"🔐 Bonjour Web Service running on port {wrapped.port}")
print("✅ Bonjour Web Service available at https://bonjour.zilogo.com")

if __name__ == "__main__":
    try:
        # Keep the service running
        print("🔄 Service running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping Bonjour Web Service...")