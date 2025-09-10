#!/usr/bin/env python3
"""
Web-based tournament organization editor
Replaces the curses TUI with a web interface accessible via lynx
Self-manages web editor process.

NOW USING POLYMORPHIC ask/tell/do PATTERN:
- ask(query) - Get data: "unnamed tournaments", "organizations", "rankings"
- tell(format, data) - Format output: "html", "json", "text"
- do(action) - Perform actions: "update tournament 123 contact='Org Name'"
"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import re
from typing import Any, Optional, Union, Dict, List
import html
import csv
import io

# Import after path setup
from models.tournament_models import Tournament, Organization, BaseModel, normalize_contact
from utils.database_service import database_service
from polymorphic_core import announcer

try:
    from polymorphic_core.process_management import BaseProcessManager
except ImportError:
    BaseProcessManager = object

class WebEditorProcessManager(BaseProcessManager):
    """Process manager for Web Editor service"""
    
    SERVICE_NAME = "WebEditor"
    PROCESSES = ['services/web_editor.py']
    PORTS = [8081]

# Announce module capabilities on import
announcer.announce(
    "Web Editor Service (Polymorphic)",
    [
        "Web interface for editing organizations on port 8081",
        "Edit organization names and merge duplicates",
        "Manage organization contact information",
        "Assign tournaments to organizations",
        "Browse and search organizations",
        "Accessible via lynx or any web browser",
        "NOW WITH ask/tell/do PATTERN!"
    ],
    [
        "editor.ask('unnamed tournaments')",
        "editor.tell('html', data)",
        "editor.do('update tournament 123 contact=OrgName')",
        "./go.py --edit-contacts",
        "http://localhost:8081"
    ]
)

# Service handler for bonjour signals
class WebEditorServiceHandler:
    def __init__(self):
        self.port = 8081
        self.status = "running"
        
    def handle_signal(self, signal_type: str, data: dict = None):
        """Handle bonjour signals"""
        if signal_type == 'status':
            return {
                'status': self.status,
                'port': self.port,
                'url': f'http://localhost:{self.port}',
                'uptime': 'unknown'  # Could track this if needed
            }
        elif signal_type == 'ping':
            return 'pong'
        elif signal_type == 'info':
            return {
                'service': 'Web Editor',
                'version': '2.0',
                'polymorphic': True,
                'methods': ['ask', 'tell', 'do']
            }
        else:
            return f'Unknown signal: {signal_type}'

# Register with bonjour
service_handler = WebEditorServiceHandler()
announcer.register_service('Web Editor Service', service_handler)

class OrganizationEditor:
    """Web editor service with ONLY 3 public methods: ask, tell, do
    
    Everything else is private implementation details.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Initialize database
            self.db_session = None
            self.tournaments = []
            self.changes = {}
            self._initialized = True
            
            # Announce ourselves
            announcer.announce(
                "OrganizationEditor",
                [
                    "ask('unnamed tournaments') - Get tournaments needing names",
                    "ask('organizations') - Get all organizations",
                    "ask('rankings') - Get organization rankings",
                    "tell('html', data) - Format as HTML",
                    "do('update tournament 123 contact=Name') - Update contact"
                ]
            )
    
    def ask(self, query: str, **kwargs) -> Any:
        """Ask for data about organizations and tournaments.
        
        Examples:
            ask('unnamed tournaments') - Get tournaments with unnamed contacts
            ask('organizations') - Get all organizations
            ask('rankings') - Get organization rankings by tournament count
            ask('tournament 123') - Get specific tournament details
        """
        query_lower = query.lower().strip()
        
        # Parse query intent
        if 'unnamed' in query_lower:
            return self._get_unnamed_tournaments()
        
        elif 'ranking' in query_lower:
            return self._get_organization_rankings()
        
        elif 'organization' in query_lower:
            return self._get_organizations()
        
        elif 'tournament' in query_lower:
            # Check for specific ID
            match = re.search(r'\d+', query)
            if match:
                tournament_id = int(match.group())
                return self._get_tournament(tournament_id)
            # Otherwise get all tournaments
            return self._get_all_tournaments()
        
        # Default - return summary
        return {
            'unnamed_count': len(self._get_unnamed_tournaments()),
            'organization_count': len(self._get_organizations()),
            'total_tournaments': len(self._get_all_tournaments())
        }
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format data for output in various formats.
        
        Examples:
            tell('html', unnamed_list) - Format as HTML table
            tell('json', organizations) - Format as JSON
            tell('text', rankings) - Format as plain text
        """
        format_lower = format.lower().strip()
        
        # If no data provided, get default data
        if data is None:
            data = self.ask('summary')
        
        if format_lower == 'html':
            return self._format_html(data)
        
        elif format_lower == 'json':
            return json.dumps(data, default=str, indent=2)
        
        elif format_lower in ['text', 'plain']:
            return self._format_text(data)
        
        elif format_lower == 'csv':
            return self._format_csv(data)
        
        # Default - string representation
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform actions on organizations and tournaments.
        
        Examples:
            do('update tournament 123 contact="Org Name"')
            do('create organization name="New Org" email="email@example.com"')
            do('merge organization 1 into 2')
        """
        action_lower = action.lower().strip()
        
        # Update tournament contact
        if 'update tournament' in action_lower:
            return self._do_update_tournament(action, **kwargs)
        
        # Create organization
        elif 'create organization' in action_lower:
            return self._do_create_organization(action, **kwargs)
        
        # Merge organizations
        elif 'merge' in action_lower:
            return self._do_merge_organizations(action, **kwargs)
        
        # Unknown action
        return f"Unknown action: {action}"
    
    # ============= PRIVATE METHODS =============
    
    def _get_session(self):
        """Get database session"""
        return database_service.get_session()
        
    def _is_contact_unnamed(self, primary_contact):
        """Determine if a primary contact needs naming"""
        if not primary_contact:
            return False
            
        contact = primary_contact.strip().lower()
        
        # Check for patterns that indicate un-named contacts
        patterns = [
            r'.*@.*\.(com|org|net|edu)',    # Email addresses
            r'.*discord\.gg/.*',            # Discord invite links
            r'.*discord\.com/invite/.*',    # Discord invite links
            r'.*twitter\.com/.*',           # Twitter handles
            r'.*facebook\.com/.*',          # Facebook URLs
            r'.*instagram\.com/.*',         # Instagram handles
            r'^https?://.*',                # Any HTTP URL
            r'.*\.com$',                    # Ends with .com (likely URL)
            r'.*\d{10,}.*',                 # Contains long numbers (phone, ID)
        ]
        
        # If contact matches any pattern, it's considered un-named
        for pattern in patterns:
            if re.match(pattern, contact):
                return True
                
        # Additional checks for single word contacts that look like usernames
        if len(contact.split()) == 1 and len(contact) < 20:
            # Single word under 20 chars might be username/handle
            return True
            
        return False
    
    def _get_unnamed_tournaments(self):
        """Get all tournaments with unnamed contacts"""
        all_tournaments = Tournament.all()
        unnamed = []
        
        for tournament in all_tournaments:
            if self._is_contact_unnamed(tournament.primary_contact):
                unnamed.append({
                    'id': tournament.id,
                    'name': tournament.name,
                    'primary_contact': tournament.primary_contact,
                    'num_attendees': tournament.num_attendees or 0,
                    'venue_name': tournament.venue_name,
                    'city': tournament.city,
                    'short_slug': tournament.short_slug,
                    'normalized_contact': tournament.normalized_contact
                })
        
        # Sort by attendance (highest first)
        unnamed.sort(key=lambda x: x['num_attendees'], reverse=True)
        return unnamed
    
    def _get_organizations(self):
        """Get all organizations"""
        orgs = Organization.all()
        return [{
            'id': org.id,
            'name': org.name,
            'contact_email': org.contact_email,
            'contact_discord': org.contact_discord
        } for org in orgs]
    
    def _update_tournament_contact(self, tournament_id, new_contact):
        """Update a tournament's primary contact"""
        tournament = Tournament.get(tournament_id)
        if tournament:
            tournament.primary_contact = new_contact
            tournament.normalized_contact = normalize_contact(new_contact)
            tournament.save()
            return True
        return False
    
    def _create_organization(self, name, contact_email=None, contact_discord=None):
        """Create a new organization"""
        org = Organization()
        org.name = name
        org.contact_email = contact_email
        org.contact_discord = contact_discord
        org.save()
        return org.id
    
    def _get_all_tournaments(self):
        """Get all tournaments"""
        return Tournament.all()
    
    def _get_tournament(self, tournament_id: int):
        """Get specific tournament"""
        return Tournament.get(tournament_id)
    
    def _get_organization_rankings(self):
        """Get organization rankings by tournament count"""
        from sqlalchemy import func
        
        with self._get_session() as session:
            # Query for organization rankings
            org_stats = session.query(
                Tournament.owner_name,
                func.count(Tournament.id).label('tournament_count'),
                func.sum(Tournament.num_attendees).label('total_attendees')
            ).filter(
                Tournament.owner_name.isnot(None)
            ).group_by(
                Tournament.owner_name
            ).order_by(
                func.count(Tournament.id).desc()
            ).all()
            
            rankings = []
            rank = 1
            for owner_name, tournament_count, total_attendees in org_stats:
                if owner_name and tournament_count > 0:
                    avg_attendees = int(total_attendees / tournament_count) if tournament_count > 0 and total_attendees else 0
                    rankings.append({
                        'rank': rank,
                        'name': owner_name,
                        'tournament_count': tournament_count,
                        'total_attendees': total_attendees or 0,
                        'avg_attendees': avg_attendees
                    })
                    rank += 1
            
            return rankings
    
    def _format_html(self, data: Any) -> str:
        """Format data as HTML"""
        if isinstance(data, list):
            if not data:
                return "<p>No data</p>"
            
            # Create HTML table from list
            first_item = data[0]
            if isinstance(first_item, dict):
                headers = list(first_item.keys())
                rows = []
                for item in data:
                    row_cells = [f"<td>{html.escape(str(item.get(h, '')))}</td>" for h in headers]
                    rows.append(f"<tr>{''.join(row_cells)}</tr>")
                
                header_row = ''.join([f"<th>{h}</th>" for h in headers])
                return f"""<table border="1">
                    <tr>{header_row}</tr>
                    {''.join(rows)}
                </table>"""
        
        elif isinstance(data, dict):
            items = [f"<li><strong>{k}:</strong> {v}</li>" for k, v in data.items()]
            return f"<ul>{''.join(items)}</ul>"
        
        return f"<p>{html.escape(str(data))}</p>"
    
    def _format_text(self, data: Any) -> str:
        """Format data as plain text"""
        if isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, dict):
                    line = ' | '.join([f"{k}: {v}" for k, v in item.items()])
                    lines.append(line)
                else:
                    lines.append(str(item))
            return '\n'.join(lines)
        
        elif isinstance(data, dict):
            return '\n'.join([f"{k}: {v}" for k, v in data.items()])
        
        return str(data)
    
    def _format_csv(self, data: Any) -> str:
        """Format data as CSV"""
        
        if isinstance(data, list) and data and isinstance(data[0], dict):
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return output.getvalue()
        
        return str(data)
    
    def _do_update_tournament(self, action: str, **kwargs) -> str:
        """Update tournament contact"""
        
        # Parse tournament ID
        id_match = re.search(r'tournament\s+(\d+)', action)
        if not id_match:
            return "Error: No tournament ID found"
        
        tournament_id = int(id_match.group(1))
        
        # Parse new contact
        contact_match = re.search(r'contact\s*=\s*["\']?([^"\'\n]+)["\']?', action)
        if not contact_match:
            # Check kwargs
            if 'contact' not in kwargs:
                return "Error: No contact specified"
            new_contact = kwargs['contact']
        else:
            new_contact = contact_match.group(1).strip()
        
        # Update
        if self._update_tournament_contact(tournament_id, new_contact):
            return f"Updated tournament {tournament_id} contact to: {new_contact}"
        return f"Failed to update tournament {tournament_id}"
    
    def _do_create_organization(self, action: str, **kwargs) -> str:
        """Create new organization"""
        
        # Parse name
        name_match = re.search(r'name\s*=\s*["\']?([^"\'\n]+)["\']?', action)
        if not name_match:
            if 'name' not in kwargs:
                return "Error: No organization name specified"
            name = kwargs['name']
        else:
            name = name_match.group(1).strip()
        
        # Parse optional email
        email_match = re.search(r'email\s*=\s*["\']?([^"\'\n]+)["\']?', action)
        email = email_match.group(1).strip() if email_match else kwargs.get('email')
        
        # Parse optional discord
        discord_match = re.search(r'discord\s*=\s*["\']?([^"\'\n]+)["\']?', action)
        discord = discord_match.group(1).strip() if discord_match else kwargs.get('discord')
        
        # Create
        org_id = self._create_organization(name, email, discord)
        return f"Created organization '{name}' with ID {org_id}"
    
    def _do_merge_organizations(self, action: str, **kwargs) -> str:
        """Merge organizations"""
        
        # Parse IDs
        match = re.search(r'(\d+)\s+into\s+(\d+)', action)
        if not match:
            return "Error: Use format 'merge organization SOURCE_ID into TARGET_ID'"
        
        source_id = int(match.group(1))
        target_id = int(match.group(2))
        
        # Merge functionality not yet implemented
        return f"Would merge organization {source_id} into {target_id} (not implemented)"

# Singleton instance
editor = OrganizationEditor()


class EditorWebHandler(BaseHTTPRequestHandler):
    """Web request handler for the editor - now uses ask/tell/do pattern"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/':
            self.serve_home()
        elif parsed.path == '/unnamed':
            # Use ask() to get data
            data = editor.ask('unnamed tournaments')
            self.serve_unnamed_with_data(data)
        elif parsed.path == '/organizations':
            # Use ask() to get data
            data = editor.ask('organizations')
            self.serve_organizations_with_data(data)
        elif parsed.path == '/rankings':
            # Use ask() to get data
            data = editor.ask('rankings')
            self.serve_rankings_with_data(data)
        elif parsed.path.startswith('/edit/'):
            tournament_id = int(parsed.path.split('/')[-1])
            self.serve_edit_form(tournament_id)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path.startswith('/update/'):
            tournament_id = int(parsed.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            new_contact = params.get('contact', [''])[0]
            # Use do() to update
            result = editor.do(f'update tournament {tournament_id} contact="{new_contact}"')
            if 'Updated' in result:
                self.send_response(303)
                self.send_header('Location', '/unnamed')
                self.end_headers()
            else:
                self.send_error(500)
        else:
            self.send_error(404)
    
    def serve_unnamed(self):
        """Legacy method - redirects to new method"""
        data = editor.ask('unnamed tournaments')
        self.serve_unnamed_with_data(data)
    
    def serve_organizations(self):
        """Legacy method - redirects to new method"""
        data = editor.ask('organizations')
        self.serve_organizations_with_data(data)
    
    def serve_rankings(self):
        """Legacy method - redirects to new method"""
        data = editor.ask('rankings')
        self.serve_rankings_with_data(data)
    
    def serve_home(self):
        """Serve the home page"""
        content = """<!DOCTYPE html>
<html>
<head>
    <title>Tournament Organization Editor</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Tournament Organization Editor</h1>
    <p>Web-based editor for managing tournament organizations</p>
    
    <h2>Menu</h2>
    <ul>
        <li><a href="/unnamed">View Unnamed Tournaments</a> - Tournaments needing organization names</li>
        <li><a href="/organizations">View All Organizations</a> - List of all organizations</li>
        <li><a href="/rankings">View Organization Rankings</a> - Organizations ranked by tournament count</li>
    </ul>
    
    <hr>
    <p>Use arrow keys to navigate in lynx. Press Enter to follow links.</p>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def serve_unnamed_with_data(self, tournaments):
        """Serve list of unnamed tournaments using provided data"""
        
        rows = []
        for t in tournaments:
            contact = html.escape(t['primary_contact'])
            name = html.escape(t['name'])
            rows.append(f"""
            <tr>
                <td>{t['id']}</td>
                <td>{name}</td>
                <td>{contact}</td>
                <td>{t['num_attendees']}</td>
                <td><a href="/edit/{t['id']}">Edit</a></td>
            </tr>""")
        
        content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Unnamed Tournaments</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Tournaments with Unnamed Contacts</h1>
    <p><a href="/">Back to Home</a></p>
    
    <p>Total: {len(tournaments)} tournaments need organization names</p>
    
    <table border="1">
        <tr>
            <th>ID</th>
            <th>Tournament Name</th>
            <th>Current Contact</th>
            <th>Attendance</th>
            <th>Action</th>
        </tr>
        {''.join(rows)}
    </table>
    
    <p><a href="/">Back to Home</a></p>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def serve_organizations_with_data(self, orgs):
        """Serve list of all organizations using provided data"""
        
        rows = []
        for org in orgs:
            name = html.escape(org['name'])
            email = html.escape(org.get('contact_email', '') or '')
            discord = html.escape(org.get('contact_discord', '') or '')
            rows.append(f"""
            <tr>
                <td>{org['id']}</td>
                <td>{name}</td>
                <td>{email}</td>
                <td>{discord}</td>
            </tr>""")
        
        content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Organizations</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>All Organizations</h1>
    <p><a href="/">Back to Home</a></p>
    
    <p>Total: {len(orgs)} organizations</p>
    
    <table border="1">
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Discord</th>
        </tr>
        {''.join(rows)}
    </table>
    
    <p><a href="/">Back to Home</a></p>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def serve_rankings_with_data(self, rankings):
        """Serve organization rankings using provided data"""
        rows = []
        for item in rankings:
            rows.append(f"""
            <tr>
                <td>{item['rank']}</td>
                <td>{html.escape(item['name'])}</td>
                <td>{item['tournament_count']}</td>
                <td>{item['total_attendees']}</td>
                <td>{item['avg_attendees']}</td>
            </tr>""")
        
        content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Organization Rankings</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Organization Rankings</h1>
    <p><a href="/">Back to Home</a></p>
    
    <p>Total: {len(rows)} organizations with tournaments</p>
    
    <table border="1">
        <tr>
            <th>Rank</th>
            <th>Organization</th>
            <th>Tournaments</th>
            <th>Total Players</th>
            <th>Avg Players</th>
        </tr>
        {''.join(rows)}
    </table>
    
    <hr>
    <p><a href="/">Back to Home</a></p>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def serve_edit_form(self, tournament_id):
        """Serve edit form for a tournament"""
        # Use ask() to get data
        tournament = editor.ask(f'tournament {tournament_id}')
        
        if not tournament:
            self.send_error(404)
            return
        
        # Convert to expected format if needed
        if not isinstance(tournament, dict) or 'id' not in tournament:
            # Try to get from unnamed list
            tournaments = editor.ask('unnamed tournaments')
            tournament = next((t for t in tournaments if t['id'] == tournament_id), None)
            if not tournament:
                self.send_error(404)
                return
        
        orgs = editor.ask('organizations')
        org_options = ['<option value="">-- Select Organization --</option>']
        for org in orgs:
            name = html.escape(org['name'])
            org_options.append(f'<option value="{name}">{name}</option>')
        
        content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Edit Tournament Contact</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Edit Tournament Contact</h1>
    <p><a href="/unnamed">Back to Unnamed List</a></p>
    
    <h2>Tournament Details</h2>
    <ul>
        <li><strong>Name:</strong> {html.escape(tournament['name'])}</li>
        <li><strong>Current Contact:</strong> {html.escape(tournament['primary_contact'])}</li>
        <li><strong>Attendance:</strong> {tournament['num_attendees']}</li>
        <li><strong>Venue:</strong> {html.escape(tournament.get('venue_name', '') or 'N/A')}</li>
        <li><strong>City:</strong> {html.escape(tournament.get('city', '') or 'N/A')}</li>
    </ul>
    
    <h2>Update Organization</h2>
    <form method="POST" action="/update/{tournament_id}">
        <p>
            <label for="contact">Organization Name:</label><br>
            <input type="text" id="contact" name="contact" size="50" value="{html.escape(tournament['primary_contact'])}"><br>
            <small>Enter the proper organization name (e.g., "BACKYARD TRY-HARDS")</small>
        </p>
        
        <p>Or select from existing organizations:</p>
        <select name="contact_select" onchange="document.getElementById('contact').value=this.value">
            {''.join(org_options)}
        </select>
        
        <p>
            <input type="submit" value="Update">
            <a href="/unnamed">Cancel</a>
        </p>
    </form>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())

def run_server(port=8081, host='127.0.0.1'):
    """Run the web server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, EditorWebHandler)
    print(f"Starting web editor on port {port}")
    print(f"Access with: lynx http://localhost:{port}")
    httpd.serve_forever()

# Create global process manager instance to announce capabilities
if BaseProcessManager != object:  # Only if we have the real class
    _web_editor_process_manager = WebEditorProcessManager()

if __name__ == '__main__':
    run_server()