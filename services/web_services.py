#!/usr/bin/env python3
"""
web_services.py - Unified web services with Bonjour self-announcement
Consolidates all web serving functionality with the 3-method polymorphic pattern
Now uses ManagedService for unified service identity.

This module provides:
- HTML serving for web interfaces
- REST API endpoints
- WebSocket support
- Static file serving
- Bonjour service discovery

Uses the polymorphic pattern:
- ask(query) - Handle GET requests and queries
- tell(format, data) - Format responses (HTML, JSON, XML, etc.)
- do(action) - Handle POST/PUT/DELETE actions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('/home/ubuntu/claude/tournament_tracker')

from polymorphic_core.service_identity import ManagedService

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.web_services")

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import html
import mimetypes
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from polymorphic_core import announcer
import threading
import traceback

# Import database and models
from utils.database_service import database_service
from utils.error_handler import handle_errors, handle_exception, ErrorSeverity
from database.tournament_models import Tournament, Organization, Player


class WebServicesManaged(ManagedService):
    """
    Unified web services with Bonjour announcement and polymorphic pattern.
    Handles all HTTP/web serving needs for the tournament tracker.
    Now inherits from ManagedService for unified service identity.
    """
    
    def __init__(self, port: int = 8081):
        super().__init__("web-services", "tournament-web-server")
        self.port = port
        self.server = None
        self.running = False
        self.db = database_service
        
        # Announce our capabilities
        self._announce_capabilities()
    
    def _announce_capabilities(self):
        """Announce what this service can do - Bonjour style"""
        announcer.announce(
            "WebServices",
            [
                f"Unified web services on port {self.port}",
                "HTML interfaces for tournament management",
                "REST API for data access",
                "Organization editor interface",
                "Tournament data viewer",
                "Player statistics dashboard",
                "Polymorphic ask/tell/do pattern",
                "Self-documenting endpoints"
            ],
            [
                f"http://localhost:{self.port}/",
                f"http://localhost:{self.port}/organizations",
                f"http://localhost:{self.port}/tournaments",
                f"http://localhost:{self.port}/api/players",
                "webservices.ask('organizations')",
                "webservices.tell('html', tournament_data)",
                "webservices.do('update org 123 name=NewName')"
            ]
        )
    
    # ========== POLYMORPHIC INTERFACE ==========
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Handle any query/GET request using natural language
        
        Examples:
            ask("organizations")          # List all organizations
            ask("tournaments recent")     # Recent tournaments
            ask("player WEST")           # Get player info
            ask("stats")                # System statistics
            ask("unnamed tournaments")   # Tournaments without organizers
        """
        query_lower = query.lower().strip()
        
        # Route to appropriate handler based on query
        if "organization" in query_lower or "org" in query_lower:
            return self._get_organizations(query_lower)
        elif "tournament" in query_lower:
            return self._get_tournaments(query_lower)
        elif "player" in query_lower:
            return self._get_players(query_lower)
        elif "stat" in query_lower:
            return self._get_statistics()
        elif "help" in query_lower or "capabilities" in query_lower:
            return self._get_capabilities()
        else:
            # Try to be smart about it
            return self._smart_query(query_lower)
    
    def tell(self, format: str, data: Any = None, **kwargs) -> str:
        """
        Format data for output in various formats
        
        Formats:
            - "html" - Full HTML page
            - "json" - JSON response
            - "text" - Plain text
            - "csv" - CSV format
            - "markdown" - Markdown table
            - "api" - REST API response
        """
        format_lower = format.lower().strip()
        
        if format_lower == "html":
            return self._format_html(data, **kwargs)
        elif format_lower == "json":
            return self._format_json(data)
        elif format_lower == "text":
            return self._format_text(data)
        elif format_lower == "csv":
            return self._format_csv(data)
        elif format_lower == "markdown":
            return self._format_markdown(data)
        elif format_lower == "api":
            return self._format_api_response(data)
        else:
            # Default to JSON
            return self._format_json(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform actions using natural language
        
        Examples:
            do("start server")
            do("stop server")
            do("update organization 123 name='New Name'")
            do("merge org 123 into 456")
            do("assign tournament 789 to org 123")
            do("delete contact 555")
        """
        action_lower = action.lower().strip()
        
        # Announce the action
        announcer.announce(
            "WebServices.do",
            [f"Performing action: {action}"]
        )
        
        # Route to appropriate handler
        if "start" in action_lower:
            return self._start_server()
        elif "stop" in action_lower:
            return self._stop_server()
        elif "update" in action_lower:
            return self._handle_update(action_lower, **kwargs)
        elif "merge" in action_lower:
            return self._handle_merge(action_lower)
        elif "assign" in action_lower:
            return self._handle_assign(action_lower)
        elif "delete" in action_lower:
            return self._handle_delete(action_lower)
        else:
            return {"error": f"Unknown action: {action}"}
    
    # ========== PRIVATE IMPLEMENTATION ==========
    
    def _get_organizations(self, query: str) -> List[Dict]:
        """Get organizations from database"""
        try:
            # Use database service's polymorphic interface
            orgs_data = self.db.ask("organizations")
            
            # Filter if needed
            if "unnamed" in query:
                orgs_data = [o for o in orgs_data if not o.get('name') or o['name'] == 'Unknown']
            
            return orgs_data
        except Exception as e:
            announcer.announce("WebServices.Error", [f"Failed to get organizations: {e}"])
            return []
    
    def _get_tournaments(self, query: str) -> List[Dict]:
        """Get tournaments from database"""
        try:
            tournaments = self.db.ask("tournaments")
            
            # Filter based on query
            if "recent" in query:
                # Get last 30 days
                tournaments = [t for t in tournaments if t.get('days_ago', 999) <= 30]
            elif "unnamed" in query:
                tournaments = [t for t in tournaments if not t.get('organization')]
            elif "major" in query:
                tournaments = [t for t in tournaments if t.get('num_attendees', 0) > 100]
            
            return tournaments
        except Exception as e:
            announcer.announce("WebServices.Error", [f"Failed to get tournaments: {e}"])
            return []
    
    def _get_players(self, query: str) -> List[Dict]:
        """Get players from database"""
        try:
            players = self.db.ask("players")
            
            # Check for specific player
            parts = query.split()
            for part in parts:
                if part.upper() != "PLAYER":
                    # Try to find player by name
                    matching = [p for p in players if part.upper() in p.get('name', '').upper()]
                    if matching:
                        return matching
            
            return players
        except Exception as e:
            announcer.announce("WebServices.Error", [f"Failed to get players: {e}"])
            return []
    
    def _get_statistics(self) -> Dict:
        """Get system statistics"""
        try:
            stats = self.db.ask("stats")
            stats['service'] = 'WebServices'
            stats['port'] = self.port
            stats['status'] = 'running' if self.running else 'stopped'
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    def _get_capabilities(self) -> Dict:
        """Return service capabilities for self-documentation"""
        return {
            "service": "WebServices",
            "version": "2.0",
            "port": self.port,
            "endpoints": [
                "/organizations - View and edit organizations",
                "/tournaments - Browse tournaments",
                "/players - Player rankings and stats",
                "/api/* - REST API endpoints"
            ],
            "methods": [
                "ask(query) - Query for any data",
                "tell(format, data) - Format any response",
                "do(action) - Perform any action"
            ],
            "formats": ["html", "json", "text", "csv", "markdown", "api"]
        }
    
    def _smart_query(self, query: str) -> Any:
        """Try to intelligently handle unknown queries"""
        # Just try the database
        try:
            result = self.db.ask(query)
            return result
        except:
            return {"error": f"Could not understand query: {query}"}
    
    def _format_html(self, data: Any, title: str = "Tournament Tracker", **kwargs) -> str:
        """Format data as HTML page"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{html.escape(title)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border: 1px solid #ddd; }}
        th {{ background: #007bff; color: white; }}
        tr:hover {{ background: #f1f1f1; }}
        .actions {{ margin: 20px 0; }}
        .btn {{ padding: 10px 20px; margin: 5px; background: #007bff; color: white; 
                text-decoration: none; border-radius: 4px; display: inline-block; }}
        .btn:hover {{ background: #0056b3; }}
        .stats {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .announcement {{ background: #d4edda; border: 1px solid #c3e6cb; 
                         padding: 10px; border-radius: 4px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>{html.escape(title)}</h1>
    <div class="announcement">
        🔊 WebServices is self-announcing via Bonjour pattern!
    </div>
"""
        
        if isinstance(data, list) and len(data) > 0:
            # Create table for list data
            html_content += "<table><thead><tr>"
            
            # Get headers from first item
            headers = list(data[0].keys()) if isinstance(data[0], dict) else ["Value"]
            for header in headers:
                html_content += f"<th>{html.escape(str(header))}</th>"
            html_content += "</tr></thead><tbody>"
            
            # Add rows
            for item in data:
                html_content += "<tr>"
                if isinstance(item, dict):
                    for header in headers:
                        value = item.get(header, "")
                        html_content += f"<td>{html.escape(str(value))}</td>"
                else:
                    html_content += f"<td>{html.escape(str(item))}</td>"
                html_content += "</tr>"
            
            html_content += "</tbody></table>"
        
        elif isinstance(data, dict):
            # Format dict as definition list
            html_content += '<div class="stats"><dl>'
            for key, value in data.items():
                html_content += f"<dt><strong>{html.escape(str(key))}:</strong></dt>"
                html_content += f"<dd>{html.escape(str(value))}</dd>"
            html_content += "</dl></div>"
        
        else:
            # Just show the data
            html_content += f"<p>{html.escape(str(data))}</p>"
        
        html_content += """
    <div class="actions">
        <a href="/" class="btn">Home</a>
        <a href="/organizations" class="btn">Organizations</a>
        <a href="/tournaments" class="btn">Tournaments</a>
        <a href="/players" class="btn">Players</a>
    </div>
</body>
</html>"""
        
        return html_content
    
    def _format_json(self, data: Any) -> str:
        """Format data as JSON"""
        try:
            return json.dumps(data, indent=2, default=str)
        except:
            return json.dumps({"error": "Could not serialize data"})
    
    def _format_text(self, data: Any) -> str:
        """Format data as plain text"""
        if isinstance(data, (list, tuple)):
            return "\n".join(str(item) for item in data)
        elif isinstance(data, dict):
            return "\n".join(f"{k}: {v}" for k, v in data.items())
        else:
            return str(data)
    
    def _format_csv(self, data: Any) -> str:
        """Format data as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        else:
            writer = csv.writer(output)
            if isinstance(data, list):
                for row in data:
                    writer.writerow([row] if not isinstance(row, (list, tuple)) else row)
            else:
                writer.writerow([data])
        
        return output.getvalue()
    
    def _format_markdown(self, data: Any) -> str:
        """Format data as Markdown table"""
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            headers = list(data[0].keys())
            md = "| " + " | ".join(headers) + " |\n"
            md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            
            for item in data:
                row = [str(item.get(h, "")) for h in headers]
                md += "| " + " | ".join(row) + " |\n"
            
            return md
        else:
            return f"```\n{self._format_text(data)}\n```"
    
    def _format_api_response(self, data: Any) -> str:
        """Format as API response with metadata"""
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "service": "WebServices",
            "data": data
        }
        return self._format_json(response)
    
    def _start_server(self) -> Dict:
        """Start the web server"""
        if self.running:
            return {"status": "already running", "port": self.port}
        
        try:
            # Create request handler with reference to self
            service = self
            
            class RequestHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    """Handle GET requests"""
                    try:
                        parsed = urllib.parse.urlparse(self.path)
                        path = parsed.path
                        params = urllib.parse.parse_qs(parsed.query)
                        
                        # Route based on path
                        if path == "/" or path == "/index":
                            data = service._get_capabilities()
                            response = service.tell("html", data, title="WebServices Home")
                        elif path == "/organizations":
                            data = service.ask("organizations")
                            response = service.tell("html", data, title="Organizations")
                        elif path == "/tournaments":
                            data = service.ask("tournaments")
                            response = service.tell("html", data, title="Tournaments")
                        elif path == "/players":
                            data = service.ask("players")
                            response = service.tell("html", data, title="Players")
                        elif path.startswith("/api/"):
                            # API endpoint - return JSON
                            query = path[5:]  # Remove /api/
                            data = service.ask(query)
                            response = service.tell("api", data)
                            self.send_response(200)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(response.encode())
                            return
                        else:
                            self.send_error(404, "Not Found")
                            return
                        
                        # Send HTML response
                        self.send_response(200)
                        self.send_header("Content-Type", "text/html")
                        self.end_headers()
                        self.wfile.write(response.encode())
                        
                    except Exception as e:
                        self.send_error(500, str(e))
                
                def do_POST(self):
                    """Handle POST requests for actions"""
                    try:
                        content_length = int(self.headers.get('Content-Length', 0))
                        post_data = self.rfile.read(content_length)
                        
                        # Parse data
                        if self.headers.get('Content-Type') == 'application/json':
                            data = json.loads(post_data)
                            action = data.get('action', '')
                            result = service.do(action, **data)
                        else:
                            # Form data
                            params = urllib.parse.parse_qs(post_data.decode())
                            action = params.get('action', [''])[0]
                            result = service.do(action, **params)
                        
                        # Send response
                        response = service.tell("json", result)
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(response.encode())
                        
                    except Exception as e:
                        self.send_error(500, str(e))
                
                def log_message(self, format, *args):
                    """Override to reduce logging noise"""
                    pass
            
            # Start server in thread
            self.server = HTTPServer(("", self.port), RequestHandler)
            
            def serve():
                announcer.announce(
                    "WebServices.Started",
                    [f"Server running on port {self.port}"]
                )
                self.running = True
                self.server.serve_forever()
            
            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            
            return {"status": "started", "port": self.port}
            
        except Exception as e:
            announcer.announce(
                "WebServices.Error",
                [f"Failed to start server: {e}"]
            )
            return {"status": "error", "error": str(e)}
    
    def _stop_server(self) -> Dict:
        """Stop the web server"""
        if not self.running:
            return {"status": "not running"}
        
        try:
            if self.server:
                self.server.shutdown()
                self.server = None
            self.running = False
            
            announcer.announce(
                "WebServices.Stopped",
                ["Server stopped"]
            )
            
            return {"status": "stopped"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def run(self):
        """
        Service run method required by ManagedService.
        Starts the web server and keeps it running.
        """
        start_result = self._start_server()
        if start_result.get('status') == 'started':
            announcer.announce("WebServices", [f"Running on port {self.port}"])
            try:
                # Keep the service running
                while self.running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                announcer.announce("WebServices", ["Shutdown requested"])
            finally:
                self._stop_server()
        else:
            raise Exception(f"Failed to start web server: {start_result}")
    
    def _handle_update(self, action: str, **kwargs) -> Dict:
        """Handle update actions"""
        try:
            # Parse action like "update organization 123 name='New Name'"
            parts = action.split()
            
            if "organization" in action or "org" in action:
                # Extract org ID
                org_id = None
                for i, part in enumerate(parts):
                    if part.isdigit():
                        org_id = int(part)
                        break
                
                if not org_id:
                    return {"error": "No organization ID provided"}
                
                # Extract updates
                updates = {}
                for key, value in kwargs.items():
                    if key not in ['action']:
                        updates[key] = value[0] if isinstance(value, list) else value
                
                # Perform update
                result = self.db.do(f"update organization {org_id}", **updates)
                return {"status": "success", "updated": org_id, "changes": updates}
            
            return {"error": "Unknown update target"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_merge(self, action: str) -> Dict:
        """Handle merge actions"""
        try:
            # Parse "merge org 123 into 456"
            import re
            match = re.search(r'(\d+)\s+into\s+(\d+)', action)
            if match:
                source_id = int(match.group(1))
                target_id = int(match.group(2))
                
                result = self.db.do(f"merge organization {source_id} into {target_id}")
                return {"status": "success", "merged": source_id, "into": target_id}
            
            return {"error": "Invalid merge syntax"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_assign(self, action: str) -> Dict:
        """Handle assignment actions"""
        try:
            # Parse "assign tournament 789 to org 123"
            import re
            match = re.search(r'tournament\s+(\d+)\s+to\s+org\s+(\d+)', action)
            if match:
                tournament_id = int(match.group(1))
                org_id = int(match.group(2))
                
                result = self.db.do(f"assign tournament {tournament_id} to organization {org_id}")
                return {"status": "success", "tournament": tournament_id, "organization": org_id}
            
            return {"error": "Invalid assignment syntax"}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _handle_delete(self, action: str) -> Dict:
        """Handle delete actions"""
        try:
            # Parse what to delete
            if "contact" in action:
                import re
                match = re.search(r'contact\s+(\d+)', action)
                if match:
                    contact_id = int(match.group(1))
                    result = self.db.do(f"delete contact {contact_id}")
                    return {"status": "success", "deleted": "contact", "id": contact_id}
            
            return {"error": "Unknown delete target"}
            
        except Exception as e:
            return {"error": str(e)}


# Create global instance
web_services = WebServicesManaged()


# Simple CLI interface for testing
if __name__ == "__main__":
    import sys
    
    print("🌐 WebServices - Bonjour-enabled web server")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        
        if command == "start":
            result = web_services.do("start server")
            print(f"Result: {result}")
            
            if result.get('status') in ['started', 'already running']:
                print(f"\n✅ Server running at http://localhost:{web_services.port}")
                print("\nEndpoints:")
                print(f"  http://localhost:{web_services.port}/ - Home")
                print(f"  http://localhost:{web_services.port}/organizations - Organizations")
                print(f"  http://localhost:{web_services.port}/tournaments - Tournaments")
                print(f"  http://localhost:{web_services.port}/players - Players")
                print(f"  http://localhost:{web_services.port}/api/stats - API Stats")
                print("\nPress Ctrl+C to stop...")
                
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nStopping server...")
                    web_services.do("stop server")
        
        elif command == "test":
            # Test the polymorphic interface
            print("Testing polymorphic interface...")
            
            # Test ask
            print("\n1. Testing ask('stats'):")
            result = web_services.ask("stats")
            print(json.dumps(result, indent=2))
            
            # Test tell
            print("\n2. Testing tell('text', data):")
            result = web_services.tell("text", {"test": "data", "number": 42})
            print(result)
            
            # Test capabilities
            print("\n3. Testing ask('capabilities'):")
            result = web_services.ask("capabilities")
            print(json.dumps(result, indent=2))
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: python web_services.py [start|test]")
    
    else:
        print("Usage: python web_services.py [start|test]")
        print("\nCommands:")
        print("  start - Start the web server")
        print("  test  - Test the polymorphic interface")