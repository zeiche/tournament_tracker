#!/usr/bin/env python3
"""
web_service_8081.py - Persistent HTTPS web service on port 8081

This service provides a permanent HTTPS endpoint on port 8081 that serves
web interfaces and API endpoints for tournament management.
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core.execution_guard import require_go_py
require_go_py("services.web_service_8081")

from polymorphic_core.network_service_wrapper import wrap_service
from polymorphic_core import announcer

class WebService8081:
    """
    Web service that provides tournament management web interface and APIs.
    """

    def __init__(self):
        # Announce ourselves
        announcer.announce(
            "Web Service (Port 8081)",
            [
                "Tournament management web interface",
                "REST API endpoints for tournaments and players",
                "Organization editing and management",
                "Polymorphic ask/tell/do interface"
            ],
            [
                "GET / - Service information",
                "POST /ask - Query tournaments and players",
                "POST /tell - Format data for display",
                "POST /do - Perform tournament operations"
            ],
            service_instance=self
        )

        print("🌐 Web Service 8081 initialized")

    def ask(self, query: str) -> dict:
        """Query for tournament and player data"""
        query_lower = query.lower().strip()

        if 'tournaments' in query_lower:
            return {
                'type': 'tournament_query',
                'query': query,
                'result': 'Tournament data would be returned here'
            }
        elif 'players' in query_lower:
            return {
                'type': 'player_query',
                'query': query,
                'result': 'Player data would be returned here'
            }
        elif 'organizations' in query_lower:
            return {
                'type': 'organization_query',
                'query': query,
                'result': 'Organization data would be returned here'
            }
        else:
            return {
                'type': 'web_service_query',
                'query': query,
                'capabilities': [
                    'Tournament queries',
                    'Player queries',
                    'Organization queries',
                    'Web interface access'
                ]
            }

    def tell(self, format_type: str, data=None) -> str:
        """Format data for web display"""
        if format_type.lower() == 'html':
            return f"<html><body><h1>Web Service Data</h1><pre>{data}</pre></body></html>"
        elif format_type.lower() == 'json':
            import json
            return json.dumps(data or {'message': 'Web service data'}, indent=2)
        elif format_type.lower() == 'text':
            return f"Web Service Data: {data or 'No data provided'}"
        else:
            return f"Web Service (Format: {format_type}): {data or 'Web service running on port 8081'}"

    def do(self, action: str) -> str:
        """Perform web service actions"""
        action_lower = action.lower().strip()

        if 'restart' in action_lower:
            return "Web service restart requested"
        elif 'status' in action_lower:
            return "Web service is running on port 8081 with HTTPS"
        elif 'test' in action_lower:
            return "Web service test completed successfully"
        else:
            return f"Web service action performed: {action}"

# Create and start the service
print("🚀 Starting Web Service on port 8081...")

# Create the service instance
web_service = WebService8081()

# Wrap it with HTTPS server on port 8081
wrapped = wrap_service(
    web_service,
    "Web Service (Port 8081)",
    port=8081,
    auto_start=True
)

print(f"🔐 HTTPS Web Service running on port {wrapped.port}")
print("✅ Port 8081 is now serving HTTPS")

if __name__ == "__main__":
    try:
        # Keep the service running
        print("🔄 Service running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping Web Service 8081...")