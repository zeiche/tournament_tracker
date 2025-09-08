#!/usr/bin/env python3
"""
Web-based tournament organization editor
Replaces the curses TUI with a web interface accessible via lynx
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import re
from tournament_models import Tournament, Organization, BaseModel, normalize_contact
from database_service import database_service
from polymorphic_core import announcer
import html

# Announce module capabilities on import
announcer.announce(
    "Web Editor Service",
    [
        "Web interface for editing organizations on port 8081",
        "Edit organization names and merge duplicates",
        "Manage organization contact information",
        "Assign tournaments to organizations",
        "Browse and search organizations",
        "Accessible via lynx or any web browser"
    ],
    [
        "./go.py --edit-contacts",
        "http://localhost:8081",
        "lynx http://localhost:8081"
    ]
)

class OrganizationEditor:
    """Business logic extracted from editor.py"""
    
    def __init__(self):
        # Initialize database
        self.db_session = None
        self.tournaments = []
        self.changes = {}
    
    def get_session(self):
        """Get database session"""
        return get_session()
        
    def is_contact_unnamed(self, primary_contact):
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
    
    def get_unnamed_tournaments(self):
        """Get all tournaments with unnamed contacts"""
        all_tournaments = Tournament.all()
        unnamed = []
        
        for tournament in all_tournaments:
            if self.is_contact_unnamed(tournament.primary_contact):
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
    
    def get_organizations(self):
        """Get all organizations"""
        orgs = Organization.all()
        return [{
            'id': org.id,
            'name': org.name,
            'contact_email': org.contact_email,
            'contact_discord': org.contact_discord
        } for org in orgs]
    
    def update_tournament_contact(self, tournament_id, new_contact):
        """Update a tournament's primary contact"""
        tournament = Tournament.get(tournament_id)
        if tournament:
            tournament.primary_contact = new_contact
            tournament.normalized_contact = normalize_contact(new_contact)
            tournament.save()
            return True
        return False
    
    def create_organization(self, name, contact_email=None, contact_discord=None):
        """Create a new organization"""
        org = Organization()
        org.name = name
        org.contact_email = contact_email
        org.contact_discord = contact_discord
        org.save()
        return org.id

class EditorWebHandler(BaseHTTPRequestHandler):
    """Web request handler for the editor"""
    
    editor = OrganizationEditor()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/':
            self.serve_home()
        elif parsed.path == '/unnamed':
            self.serve_unnamed()
        elif parsed.path == '/organizations':
            self.serve_organizations()
        elif parsed.path == '/rankings':
            self.serve_rankings()
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
            if self.editor.update_tournament_contact(tournament_id, new_contact):
                self.send_response(303)
                self.send_header('Location', '/unnamed')
                self.end_headers()
            else:
                self.send_error(500)
        else:
            self.send_error(404)
    
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
    
    def serve_unnamed(self):
        """Serve list of unnamed tournaments"""
        tournaments = self.editor.get_unnamed_tournaments()
        
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
    
    def serve_organizations(self):
        """Serve list of all organizations"""
        orgs = self.editor.get_organizations()
        
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
    
    def serve_rankings(self):
        """Serve organization rankings by tournament count"""
        from sqlalchemy import func
        from tournament_models import Tournament
        
        # Get session
        with self.editor.get_session() as session:
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
        
        rows = []
        rank = 1
        for owner_name, tournament_count, total_attendees in org_stats:
            if owner_name and tournament_count > 0:
                avg_attendees = int(total_attendees / tournament_count) if tournament_count > 0 and total_attendees else 0
                rows.append(f"""
                <tr>
                    <td>{rank}</td>
                    <td>{html.escape(owner_name)}</td>
                    <td>{tournament_count}</td>
                    <td>{total_attendees or 0}</td>
                    <td>{avg_attendees}</td>
                </tr>""")
                rank += 1
        
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
        tournaments = self.editor.get_unnamed_tournaments()
        tournament = next((t for t in tournaments if t['id'] == tournament_id), None)
        
        if not tournament:
            self.send_error(404)
            return
        
        orgs = self.editor.get_organizations()
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

if __name__ == '__main__':
    run_server()