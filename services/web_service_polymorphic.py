#!/usr/bin/env python3
"""
web_service_polymorphic.py - Web service using the 3-method pattern
Shows how web services can be simplified with ask(), tell(), do()
"""
from typing import Any, Dict, List, Optional, Union
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import html
from polymorphic_core import announcer


class PolymorphicWebService:
    """
    Web service with just 3 methods instead of dozens of routes/handlers
    """
    
    def __init__(self, port: int = 8081):
        self.port = port
        self.server = None
        
        # Announce ourselves
        announcer.announce(
            "Polymorphic Web Service",
            [
                "Web interface using 3-method pattern",
                f"Running on port {port}",
                "ask() - Query any data via web",
                "tell() - Format any response (HTML, JSON, etc)",
                "do() - Perform any action from web requests"
            ],
            [
                f"http://localhost:{port}",
                "GET /ask?q=tournaments",
                "POST /do?action=update&id=123"
            ]
        )
    
    def ask(self, query: str, params: Dict = None) -> Any:
        """
        Handle any GET request/query
        Examples:
            ask("tournaments")          # List tournaments
            ask("organization 123")     # Get specific org
            ask("search west")         # Search for something
            ask("stats")              # Get statistics
        """
        query_lower = query.lower().strip()
        
        # Import database service
        from utils.database_service_polymorphic import database_service
        
        # Natural language query interpretation
        if "tournament" in query_lower:
            return database_service.ask(query)
        
        if "organization" in query_lower or "org" in query_lower:
            return database_service.ask(query)
        
        if "player" in query_lower:
            return database_service.ask(query)
        
        if "search" in query_lower:
            # Extract search term
            parts = query.split()
            if len(parts) > 1:
                search_term = ' '.join(parts[1:])
                return database_service.ask(f"search {search_term}")
        
        if "stats" in query_lower or "statistics" in query_lower:
            return database_service.ask("stats")
        
        # Default - try to interpret
        return database_service.ask(query)
    
    def tell(self, format: str, data: Any = None, **kwargs) -> str:
        """
        Format any response for web output
        Examples:
            tell("html", tournaments)      # HTML table
            tell("json", data)             # JSON response
            tell("form", organization)     # Edit form
            tell("page", content)          # Full HTML page
        """
        format_lower = format.lower().strip()
        
        if "json" in format_lower:
            return json.dumps(data, default=str, indent=2)
        
        if "html" in format_lower or "table" in format_lower:
            return self._format_as_html_table(data)
        
        if "form" in format_lower:
            return self._format_as_form(data)
        
        if "page" in format_lower:
            return self._wrap_in_page(data)
        
        if "text" in format_lower or "plain" in format_lower:
            return str(data)
        
        # Default - HTML
        return self._format_as_html(data)
    
    def do(self, action: str, data: Dict = None, **kwargs) -> Any:
        """
        Handle any POST request/action
        Examples:
            do("update organization 123", {"name": "New Name"})
            do("create tournament", data)
            do("merge org 1 into 2")
            do("delete player 456")
            do("start server")
            do("stop server")
        """
        action_lower = action.lower().strip()
        
        # Import database service
        from utils.database_service_polymorphic import database_service
        
        # Server control actions
        if "start" in action_lower and "server" in action_lower:
            return self._start_server()
        
        if "stop" in action_lower and "server" in action_lower:
            return self._stop_server()
        
        # Database actions - delegate to database service
        if any(word in action_lower for word in ["update", "create", "delete", "merge"]):
            result = database_service.do(action, **kwargs)
            announcer.announce("Web Action", [f"Performed: {action}"])
            return result
        
        # Form submission
        if "submit" in action_lower:
            return self._handle_form_submission(data)
        
        # File upload
        if "upload" in action_lower:
            return self._handle_upload(data)
        
        # Default action
        announcer.announce("Web Action", [f"Processing: {action}"])
        return f"Action performed: {action}"
    
    def _format_as_html_table(self, data: Any) -> str:
        """Format data as HTML table"""
        if not data:
            return "<p>No data</p>"
        
        html_parts = ["<table border='1'>"]
        
        # Handle list of dicts
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Header
            html_parts.append("<tr>")
            for key in data[0].keys():
                html_parts.append(f"<th>{html.escape(str(key))}</th>")
            html_parts.append("</tr>")
            
            # Rows
            for item in data:
                html_parts.append("<tr>")
                for value in item.values():
                    html_parts.append(f"<td>{html.escape(str(value))}</td>")
                html_parts.append("</tr>")
        
        # Handle list of objects
        elif isinstance(data, list):
            for item in data:
                html_parts.append(f"<tr><td>{html.escape(str(item))}</td></tr>")
        
        # Handle single dict
        elif isinstance(data, dict):
            for key, value in data.items():
                html_parts.append(f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>")
        
        else:
            html_parts.append(f"<tr><td>{html.escape(str(data))}</td></tr>")
        
        html_parts.append("</table>")
        return "".join(html_parts)
    
    def _format_as_form(self, data: Any) -> str:
        """Format data as an edit form"""
        if not isinstance(data, dict):
            data = {"value": str(data)}
        
        form_parts = ["<form method='POST' action='/do'>"]
        form_parts.append("<input type='hidden' name='action' value='update'>")
        
        for key, value in data.items():
            form_parts.append(f"<label>{html.escape(str(key))}:</label><br>")
            form_parts.append(f"<input type='text' name='{html.escape(str(key))}' value='{html.escape(str(value))}'><br><br>")
        
        form_parts.append("<button type='submit'>Save</button>")
        form_parts.append("</form>")
        
        return "".join(form_parts)
    
    def _format_as_html(self, data: Any) -> str:
        """Generic HTML formatting"""
        return f"<pre>{html.escape(str(data))}</pre>"
    
    def _wrap_in_page(self, content: Any) -> str:
        """Wrap content in full HTML page"""
        if not isinstance(content, str):
            content = str(content)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Polymorphic Web Service</title>
    <style>
        body {{ font-family: monospace; margin: 20px; }}
        table {{ border-collapse: collapse; }}
        th, td {{ padding: 5px; }}
        form {{ margin: 20px 0; }}
        input, button {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Polymorphic Web Service</h1>
    <nav>
        <a href="/ask?q=tournaments">Tournaments</a> |
        <a href="/ask?q=organizations">Organizations</a> |
        <a href="/ask?q=players">Players</a> |
        <a href="/ask?q=stats">Statistics</a>
    </nav>
    <hr>
    {content}
</body>
</html>"""
    
    def _start_server(self):
        """Start the web server"""
        if self.server:
            return "Server already running"
        
        class PolymorphicHandler(BaseHTTPRequestHandler):
            service = self
            
            def do_GET(self):
                """Handle GET requests polymorphically"""
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                
                # Route to ask() method
                if parsed.path == '/ask':
                    query = params.get('q', [''])[0]
                    result = self.service.ask(query, params)
                    response = self.service.tell("page", 
                                                self.service.tell("html", result))
                else:
                    # Default - show main page
                    result = self.service.ask("stats")
                    response = self.service.tell("page",
                                                self.service.tell("html", result))
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(response.encode())
            
            def do_POST(self):
                """Handle POST requests polymorphically"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                params = urllib.parse.parse_qs(post_data.decode())
                
                # Route to do() method
                action = params.get('action', [''])[0]
                result = self.service.do(action, params)
                response = self.service.tell("page", 
                                           self.service.tell("html", result))
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(response.encode())
        
        # Create and start server
        PolymorphicHandler.service = self
        self.server = HTTPServer(('127.0.0.1', self.port), PolymorphicHandler)
        
        announcer.announce("Web Server", [f"Started on port {self.port}"])
        
        # Run in thread
        import threading
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return f"Server started on port {self.port}"
    
    def _stop_server(self):
        """Stop the web server"""
        if not self.server:
            return "Server not running"
        
        self.server.shutdown()
        self.server = None
        announcer.announce("Web Server", ["Stopped"])
        return "Server stopped"
    
    def _handle_form_submission(self, data: Dict) -> str:
        """Handle form submission"""
        # Process form data
        announcer.announce("Form Submission", [f"Received: {len(data)} fields"])
        return "Form submitted successfully"
    
    def _handle_upload(self, data: Dict) -> str:
        """Handle file upload"""
        announcer.announce("File Upload", ["Processing upload"])
        return "Upload processed"


# Example usage
if __name__ == "__main__":
    # Create polymorphic web service
    web = PolymorphicWebService(port=8081)
    
    # Start server
    web.do("start server")
    
    # Examples of how simple it is:
    
    # Query data
    tournaments = web.ask("recent tournaments")
    print(f"Found {len(tournaments) if isinstance(tournaments, list) else 0} tournaments")
    
    # Format for display
    html_output = web.tell("html", tournaments)
    json_output = web.tell("json", tournaments)
    
    # Perform action
    result = web.do("update tournament 123", {"name": "New Name"})
    
    print("Web service running with just 3 methods!")
    print("No need for complex routing, handlers, controllers, etc.")
    
    # Keep running
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        web.do("stop server")