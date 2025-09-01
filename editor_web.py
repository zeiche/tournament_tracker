#!/usr/bin/env python3
"""
editor_web.py - Web interface for the contact editor
Uses shared HTML utilities and tournament_report functions for consistency
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import html
from editor_core import (
    get_unnamed_tournaments,
    update_tournament_contact,
    get_or_create_organization
)
from tournament_models import Organization
from html_utils import (
    wrap_page, 
    get_nav_links, 
    format_table, 
    format_form,
    format_stats_box
)
from log_utils import log_info

class EditorWebHandler(BaseHTTPRequestHandler):
    """Web handler using shared HTML utilities"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/':
            self.serve_home()
        elif parsed.path == '/unnamed':
            self.serve_unnamed()
        elif parsed.path == '/organizations':
            self.serve_organizations()
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
            if update_tournament_contact(tournament_id, new_contact):
                self.send_response(303)
                self.send_header('Location', '/unnamed')
                self.end_headers()
            else:
                self.send_error(500)
        else:
            self.send_error(404)
    
    def serve_home(self):
        """Serve the home page using shared utilities"""
        nav_links = [
            ('/unnamed', 'View Unnamed Tournaments'),
            ('/organizations', 'View All Organizations')
        ]
        
        content = """
        <div class="stats-box">
            <h2>Tournament Contact Editor</h2>
            <p>This tool helps manage tournament organization names in the database.</p>
            <ul>
                <li><strong>Unnamed Tournaments:</strong> Tournaments that need proper organization names</li>
                <li><strong>All Organizations:</strong> View all organizations in the database</li>
            </ul>
        </div>
        """
        
        page = wrap_page(
            content, 
            title="Tournament Contact Editor",
            subtitle="Manage tournament organization names",
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_unnamed(self):
        """Serve list of unnamed tournaments using shared table formatter"""
        tournaments = get_unnamed_tournaments()
        
        # Navigation
        nav_links = [
            ('/', 'Home'),
            ('/organizations', 'View All Organizations')
        ]
        
        # Stats box
        stats = {
            'Total Unnamed': len(tournaments),
            'Total Attendance': sum(t.num_attendees or 0 for t in tournaments)
        }
        content = format_stats_box("Summary", stats)
        
        # Format table data
        headers = ['ID', 'Tournament Name', 'Current Contact', 'Attendance', 'City', 'Action']
        
        # Custom row formatter for action links
        def row_formatter(tournament):
            return f"""
            <tr>
                <td>{tournament.id}</td>
                <td>{html.escape(tournament.name)}</td>
                <td>{html.escape(tournament.primary_contact or '')}</td>
                <td>{tournament.num_attendees or 0}</td>
                <td>{html.escape(tournament.city or 'N/A')}</td>
                <td><a href="/edit/{tournament.id}" class="action-link">Edit</a></td>
            </tr>"""
        
        if tournaments:
            content += format_table(headers, tournaments, row_formatter)
        else:
            content += '<p>No unnamed tournaments found!</p>'
        
        page = wrap_page(
            content,
            title="Unnamed Tournaments",
            subtitle=f"{len(tournaments)} tournaments need organization names",
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_organizations(self):
        """Serve list of all organizations using shared table formatter"""
        orgs = Organization.all()
        
        # Navigation
        nav_links = [
            ('/', 'Home'),
            ('/unnamed', 'View Unnamed Tournaments')
        ]
        
        # Stats box
        stats = {
            'Total Organizations': len(orgs)
        }
        content = format_stats_box("Summary", stats)
        
        # Prepare table data
        table_data = []
        for org in orgs:
            # Get contact info from relationships
            email = ''
            discord = ''
            for contact in org.contacts:
                if contact.contact_type == 'email' and not email:
                    email = contact.contact_value
                elif contact.contact_type == 'discord' and not discord:
                    discord = contact.contact_value
            
            table_data.append([
                org.id,
                org.display_name,
                email or 'N/A',
                discord or 'N/A'
            ])
        
        # Format table
        headers = ['ID', 'Name', 'Email', 'Discord']
        if table_data:
            content += format_table(headers, table_data)
        else:
            content += '<p>No organizations found.</p>'
        
        page = wrap_page(
            content,
            title="All Organizations",
            subtitle=f"{len(orgs)} organizations in database",
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_edit_form(self, tournament_id):
        """Serve edit form for a tournament using shared form utilities"""
        tournaments = get_unnamed_tournaments()
        tournament = next((t for t in tournaments if t.id == tournament_id), None)
        
        if not tournament:
            self.send_error(404)
            return
        
        # Navigation
        nav_links = [
            ('/', 'Home'),
            ('/unnamed', 'Back to Unnamed List')
        ]
        
        # Tournament details
        content = f"""
        <div class="stats-box">
            <h2>Tournament Details</h2>
            <ul>
                <li><strong>Name:</strong> {html.escape(tournament.name)}</li>
                <li><strong>Current Contact:</strong> {html.escape(tournament.primary_contact or '')}</li>
                <li><strong>Attendance:</strong> {tournament.num_attendees or 0}</li>
                <li><strong>Venue:</strong> {html.escape(tournament.venue_name or 'N/A')}</li>
                <li><strong>City:</strong> {html.escape(tournament.city or 'N/A')}</li>
                <li><strong>Short Slug:</strong> {html.escape(tournament.short_slug or 'N/A')}</li>
            </ul>
        </div>
        """
        
        # Build organization options
        orgs = Organization.all()
        org_options = [('', '-- Select Existing Organization --')]
        for org in orgs:
            org_options.append((org.display_name, org.display_name))
        
        # Form fields
        fields = [
            {
                'type': 'text',
                'name': 'contact',
                'label': 'Organization Name',
                'value': tournament.primary_contact or ''
            },
            {
                'type': 'select',
                'name': 'contact_select',
                'label': 'Or select from existing organizations',
                'options': org_options
            },
            {
                'type': 'submit',
                'label': 'Update'
            }
        ]
        
        content += '<h2>Update Organization</h2>'
        content += format_form(f'/update/{tournament_id}', fields=fields)
        content += f'<p><a href="/unnamed" class="cancel-link">Cancel</a></p>'
        
        # Add JavaScript to sync select with text input
        content += """
        <script>
        document.querySelector('select[name="contact_select"]').addEventListener('change', function() {
            document.querySelector('input[name="contact"]').value = this.value;
        });
        </script>
        """
        
        page = wrap_page(
            content,
            title="Edit Tournament Contact",
            subtitle=tournament.name,
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())

def run_server(port=8081, host='127.0.0.1'):
    """Run the web server - to be called from go.py"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, EditorWebHandler)
    log_info(f"Starting web editor on http://{host}:{port}")
    print(f"Access with: lynx http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        log_info("Web editor stopped")

if __name__ == '__main__':
    # For testing only - production should use go.py
    from database_utils import init_db
    init_db()
    run_server()