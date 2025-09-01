#!/usr/bin/env python3
"""
editor_web.py - Web interface for the contact editor and reports
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
    format_stats_box,
    get_timestamp
)
from log_utils import log_info
from shopify_query import get_legacy_attendance_data
from tournament_report import get_display_name
from database_utils import get_summary_stats

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
        elif parsed.path == '/attendance':
            self.serve_attendance_report()
        elif parsed.path.startswith('/edit/'):
            tournament_id = int(parsed.path.split('/')[-1])
            self.serve_edit_form(tournament_id)
        elif parsed.path.startswith('/edit_org/'):
            org_id = int(parsed.path.split('/')[-1])
            self.serve_edit_org_form(org_id)
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
        elif parsed.path.startswith('/update_org/'):
            org_id = int(parsed.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            if self.update_organization(org_id, params):
                self.send_response(303)
                self.send_header('Location', '/organizations')
                self.end_headers()
            else:
                self.send_error(500)
        else:
            self.send_error(404)
    
    def serve_home(self):
        """Serve the home page using shared utilities"""
        nav_links = [
            ('/attendance', 'Attendance Report'),
            ('/unnamed', 'View Unnamed Tournaments'),
            ('/organizations', 'View All Organizations')
        ]
        
        # Get summary stats
        stats = get_summary_stats()
        
        content = f"""
        <div class="stats-box">
            <h2>Tournament Tracker Dashboard</h2>
            <p>SoCal FGC Tournament Management System</p>
            <ul>
                <li><strong>Total Tournaments:</strong> {stats.get('total_tournaments', 0):,}</li>
                <li><strong>Total Organizations:</strong> {stats.get('total_organizations', 0):,}</li>
                <li><strong>Total Attendance:</strong> {stats.get('total_attendance', 0):,}</li>
            </ul>
        </div>
        
        <div class="stats-box">
            <h3>Available Tools</h3>
            <ul>
                <li><strong>Attendance Report:</strong> View tournament attendance rankings by organization</li>
                <li><strong>Unnamed Tournaments:</strong> Edit tournaments that need proper organization names</li>
                <li><strong>All Organizations:</strong> View all organizations in the database</li>
            </ul>
        </div>
        """
        
        page = wrap_page(
            content, 
            title="Tournament Tracker",
            subtitle="SoCal FGC Management System",
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
            'Total Attendance': sum(t['num_attendees'] for t in tournaments)
        }
        content = format_stats_box("Summary", stats)
        
        # Format table data
        headers = ['ID', 'Tournament Name', 'Current Contact', 'Attendance', 'City', 'Action']
        
        # Custom row formatter for action links
        def row_formatter(tournament):
            return f"""
            <tr>
                <td>{tournament['id']}</td>
                <td>{html.escape(tournament['name'])}</td>
                <td>{html.escape(tournament['primary_contact'] or '')}</td>
                <td>{tournament['num_attendees']}</td>
                <td>{html.escape(tournament['city'] or 'N/A')}</td>
                <td><a href="/edit/{tournament['id']}" class="action-link">Edit</a></td>
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
        
        # Format table with custom row formatter for action links
        headers = ['ID', 'Name', 'Email', 'Discord', 'Action']
        
        # Custom row formatter for action links
        def org_row_formatter(org):
            # Get contact info from relationships
            email = ''
            discord = ''
            for contact in org.contacts:
                if contact.contact_type == 'email' and not email:
                    email = contact.contact_value
                elif contact.contact_type == 'discord' and not discord:
                    discord = contact.contact_value
            
            return f"""
            <tr>
                <td>{org.id}</td>
                <td>{html.escape(org.display_name)}</td>
                <td>{html.escape(email or 'N/A')}</td>
                <td>{html.escape(discord or 'N/A')}</td>
                <td><a href="/edit_org/{org.id}" class="action-link">Edit</a></td>
            </tr>"""
        
        if orgs:
            content += format_table(headers, orgs, org_row_formatter)
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
        tournament = next((t for t in tournaments if t['id'] == tournament_id), None)
        
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
                <li><strong>Name:</strong> {html.escape(tournament['name'])}</li>
                <li><strong>Current Contact:</strong> {html.escape(tournament['primary_contact'] or '')}</li>
                <li><strong>Attendance:</strong> {tournament['num_attendees']}</li>
                <li><strong>Venue:</strong> {html.escape(tournament.get('venue_name') or 'N/A')}</li>
                <li><strong>City:</strong> {html.escape(tournament.get('city') or 'N/A')}</li>
                <li><strong>Short Slug:</strong> {html.escape(tournament.get('short_slug') or 'N/A')}</li>
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
                'value': tournament['primary_contact'] or ''
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
            subtitle=tournament['name'],
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_attendance_report(self):
        """Serve the tournament attendance report"""
        # Get attendance data
        attendance_tracker, org_names = get_legacy_attendance_data()
        
        # Navigation
        nav_links = [
            ('/', 'Home'),
            ('/unnamed', 'View Unnamed Tournaments'),
            ('/organizations', 'View All Organizations')
        ]
        
        if not attendance_tracker:
            content = '<p>No attendance data available.</p>'
        else:
            # Sort by attendance
            sorted_orgs = sorted(attendance_tracker.items(), 
                               key=lambda x: x[1]["total_attendance"], 
                               reverse=True)
            
            # Summary stats
            total_orgs = len(sorted_orgs)
            grand_total_attendance = sum(org[1]["total_attendance"] for org in sorted_orgs)
            total_tournaments = sum(len(org[1]["tournaments"]) for org in sorted_orgs)
            
            stats = {
                'Total Organizations': total_orgs,
                'Total Tournaments': total_tournaments,
                'Total Attendance': f'{grand_total_attendance:,}'
            }
            content = format_stats_box("Summary", stats)
            
            # Create table data
            table_data = []
            for rank, (primary_contact, data) in enumerate(sorted_orgs, 1):
                org_name = get_display_name(primary_contact, data, org_names)
                num_tournaments = len(data["tournaments"])
                total_attendance = data["total_attendance"]
                
                # Format rank with special styling for top 3
                if rank <= 3:
                    rank_display = f'<span class="rank-highlight">{rank}</span>'
                else:
                    rank_display = str(rank)
                
                table_data.append([
                    rank_display,
                    org_name,
                    num_tournaments,
                    f'{total_attendance:,}'
                ])
            
            # Custom row formatter to handle HTML in rank
            def attendance_row_formatter(row):
                return f"""
                <tr>
                    <td class="center">{row[0]}</td>
                    <td>{html.escape(row[1])}</td>
                    <td class="center">{row[2]}</td>
                    <td class="center"><strong>{row[3]}</strong></td>
                </tr>"""
            
            headers = ['Rank', 'Organization', 'Tournaments', 'Total Attendance']
            content += format_table(headers, table_data, attendance_row_formatter)
            
            # Add footer
            content += f'<p class="footer-text">Last updated: {get_timestamp()}<br><small>Data courtesy of start.gg</small></p>'
        
        page = wrap_page(
            content,
            title="Tournament Attendance Report",
            subtitle="SoCal FGC Rankings",
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_edit_org_form(self, org_id):
        """Serve edit form for an organization"""
        from database_utils import get_session
        
        with get_session() as session:
            org = session.query(Organization).get(org_id)
            if not org:
                self.send_error(404)
                return
            
            # Get existing contacts
            email = ''
            discord = ''
            for contact in org.contacts:
                if contact.contact_type == 'email':
                    email = contact.contact_value
                elif contact.contact_type == 'discord':
                    discord = contact.contact_value
            
            # Navigation
            nav_links = [
                ('/', 'Home'),
                ('/organizations', 'Back to Organizations')
            ]
            
            # Organization details
            content = f"""
            <div class="stats-box">
                <h2>Organization Details</h2>
                <ul>
                    <li><strong>ID:</strong> {org.id}</li>
                    <li><strong>Display Name:</strong> {html.escape(org.display_name)}</li>
                    <li><strong>Created:</strong> {org.created_at.strftime('%Y-%m-%d %H:%M:%S') if org.created_at else 'Unknown'}</li>
                </ul>
            </div>
            """
            
            # Form fields
            fields = [
                {
                    'type': 'text',
                    'name': 'display_name',
                    'label': 'Display Name',
                    'value': org.display_name,
                    'required': True
                },
                {
                    'type': 'text',
                    'name': 'email',
                    'label': 'Email',
                    'value': email,
                    'placeholder': 'organizer@example.com'
                },
                {
                    'type': 'text',
                    'name': 'discord',
                    'label': 'Discord',
                    'value': discord,
                    'placeholder': 'username#1234 or @username'
                },
                {
                    'type': 'submit',
                    'label': 'Update Organization'
                }
            ]
            
            content += '<h2>Edit Organization</h2>'
            content += format_form(f'/update_org/{org_id}', fields=fields)
            content += f'<p><a href="/organizations" class="cancel-link">Cancel</a></p>'
            
            page = wrap_page(
                content,
                title="Edit Organization",
                subtitle=org.display_name,
                nav_links=nav_links
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(page.encode())
    
    def update_organization(self, org_id, params):
        """Update organization and its contacts"""
        from database_utils import get_session
        from tournament_models import Contact
        
        try:
            with get_session() as session:
                org = session.query(Organization).get(org_id)
                if not org:
                    return False
                
                # Update display name
                new_name = params.get('display_name', [''])[0]
                if new_name:
                    org.display_name = new_name
                
                # Update or create email contact
                email = params.get('email', [''])[0]
                email_contact = None
                for contact in org.contacts:
                    if contact.contact_type == 'email':
                        email_contact = contact
                        break
                
                if email:
                    if email_contact:
                        email_contact.contact_value = email
                    else:
                        new_contact = Contact(
                            organization_id=org.id,
                            contact_type='email',
                            contact_value=email
                        )
                        session.add(new_contact)
                elif email_contact:
                    session.delete(email_contact)
                
                # Update or create discord contact
                discord = params.get('discord', [''])[0]
                discord_contact = None
                for contact in org.contacts:
                    if contact.contact_type == 'discord':
                        discord_contact = contact
                        break
                
                if discord:
                    if discord_contact:
                        discord_contact.contact_value = discord
                    else:
                        new_contact = Contact(
                            organization_id=org.id,
                            contact_type='discord',
                            contact_value=discord
                        )
                        session.add(new_contact)
                elif discord_contact:
                    session.delete(discord_contact)
                
                session.commit()
                log_info(f"Updated organization {org_id}: {new_name}")
                return True
        except Exception as e:
            log_info(f"Error updating organization {org_id}: {e}")
            return False

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