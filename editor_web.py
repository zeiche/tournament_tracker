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
from conversational_search import search as conversational_search, get_suggestions
import json

class EditorWebHandler(BaseHTTPRequestHandler):
    """Web handler using shared HTML utilities"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/':
            self.serve_home()
        elif parsed.path == '/search':
            self.serve_search()
        elif parsed.path == '/api/search':
            query_params = urllib.parse.parse_qs(parsed.query)
            query = query_params.get('q', [''])[0]
            self.serve_search_api(query)
        elif parsed.path == '/api/suggestions':
            query_params = urllib.parse.parse_qs(parsed.query)
            partial = query_params.get('q', [''])[0]
            self.serve_suggestions_api(partial)
        elif parsed.path == '/unnamed':
            self.serve_unnamed()
        elif parsed.path == '/organizations':
            self.serve_organizations()
        elif parsed.path == '/attendance':
            self.serve_attendance_report()
        elif parsed.path == '/heatmap' or parsed.path.startswith('/heatmap/'):
            # Check if it's a specific file request
            if parsed.path.startswith('/heatmap/') and parsed.path.count('/') == 2:
                filename = parsed.path.split('/')[-1]
                # Serve the actual heatmap file
                self.serve_heatmap_file(filename)
            else:
                # Original year-based heatmap
                if parsed.path == '/heatmap' or parsed.path == '/heatmap/':
                    year = 2025
                else:
                    try:
                        year = int(parsed.path.split('/')[-1])
                    except ValueError:
                        year = 2025
                self.serve_heatmap(year)
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
    
    def serve_heatmap_file(self, filename):
        """Serve a specific heatmap file"""
        import os
        import mimetypes
        
        # Security: only allow specific files
        allowed_files = [
            'tournament_heatmap.png',
            'tournament_heatmap_with_map.png', 
            'attendance_heatmap.png',
            'tournament_heatmap.html'
        ]
        
        if filename not in allowed_files:
            self.send_error(404, "File not found")
            return
        
        filepath = f'/home/ubuntu/claude/tournament_tracker/{filename}'
        
        if not os.path.exists(filepath):
            self.send_error(404, "File not found")
            return
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Send file
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Content-length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error serving file: {e}")
    
    def serve_home(self):
        """Serve the home page using shared utilities"""
        nav_links = [
            ('/search', '🚀 Universal Search'),
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
    
    def serve_heatmap(self):
        """Serve an interactive heat map of 2025 tournaments"""
        from database_utils import get_session
        from tournament_models import Tournament
        import json
        from datetime import datetime
        
        nav_links = [
            ('/', 'Home'),
            ('/unnamed', 'Edit Unnamed'),
            ('/organizations', 'Organizations'),
            ('/attendance', 'Attendance Report'),
            ('/heatmap', 'Heat Map')
        ]
        
        # Get 2025 tournament data
        heat_data = []
        with get_session() as session:
            tournaments = session.query(Tournament).filter(
                Tournament.lat.isnot(None),
                Tournament.lng.isnot(None),
                Tournament.start_at.like('2025%')
            ).all()
            
            for t in tournaments:
                try:
                    lat = float(t.lat)
                    lng = float(t.lng)
                    heat_data.append({
                        'lat': lat,
                        'lng': lng,
                        'name': t.name or 'Unknown',
                        'venue': t.venue_name or 'Unknown',
                        'city': t.city or 'Unknown',
                        'attendance': t.num_attendees or 0,
                        'date': t.start_at or 'Unknown'
                    })
                except (ValueError, TypeError):
                    continue
        
        # Generate the interactive map HTML
        content = f'''
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
        
        <div id="map" style="height: 600px; width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"></div>
        
        <div class="stats-grid" style="margin-top: 20px;">
            <div class="stat-card">
                <h3>Total Tournaments</h3>
                <p class="stat-value">{len(heat_data)}</p>
            </div>
            <div class="stat-card">
                <h3>Total Attendance</h3>
                <p class="stat-value">{sum(t["attendance"] for t in heat_data):,}</p>
            </div>
            <div class="stat-card">
                <h3>Unique Venues</h3>
                <p class="stat-value">{len(set(t["venue"] for t in heat_data))}</p>
            </div>
        </div>
        
        <script>
        var heatData = {json.dumps(heat_data)};
        
        // Initialize map centered on SoCal
        var map = L.map('map').setView([33.8, -117.9], 9);
        
        // Add dark tile layer
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }}).addTo(map);
        
        // Add heat layer
        var heatPoints = heatData.map(function(t) {{
            return [t.lat, t.lng, Math.log10(Math.max(t.attendance, 1))];
        }});
        
        if (heatPoints.length > 0) {{
            L.heatLayer(heatPoints, {{
                radius: 20,
                blur: 15,
                gradient: {{
                    0.0: 'blue',
                    0.25: 'cyan',
                    0.5: 'lime',
                    0.75: 'yellow',
                    1.0: 'red'
                }}
            }}).addTo(map);
        }}
        
        // Add markers for each tournament
        heatData.forEach(function(t) {{
            var color = t.attendance > 100 ? 'red' : 
                       t.attendance > 50 ? 'orange' : 'blue';
            
            var marker = L.circleMarker([t.lat, t.lng], {{
                radius: Math.sqrt(t.attendance) / 2,
                fillColor: color,
                color: 'white',
                weight: 1,
                opacity: 0.8,
                fillOpacity: 0.4
            }}).addTo(map);
            
            marker.bindPopup(
                '<b>' + t.name + '</b><br>' +
                'Venue: ' + t.venue + '<br>' +
                'City: ' + t.city + '<br>' +
                'Attendance: ' + t.attendance + '<br>' +
                'Date: ' + t.date
            );
        }});
        </script>
        
        <style>
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 14px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #212529;
            margin: 0;
        }}
        </style>
        '''
        
        page = wrap_page(
            content,
            title="2025 Tournament Heat Map",
            subtitle="Interactive visualization of SoCal FGC tournaments",
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
    
    def serve_search(self):
        """Serve the conversational search page"""
        # Space-age search interface
        content = """
        <style>
            .search-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 20px;
                padding: 40px;
                margin: 20px 0;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            
            .search-title {
                color: white;
                text-align: center;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .search-subtitle {
                color: rgba(255,255,255,0.9);
                text-align: center;
                font-size: 1.2em;
                margin-bottom: 30px;
            }
            
            .search-box {
                position: relative;
                max-width: 800px;
                margin: 0 auto;
            }
            
            #searchInput {
                width: 100%;
                padding: 20px 60px 20px 25px;
                font-size: 1.3em;
                border: none;
                border-radius: 50px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                transition: all 0.3s;
            }
            
            #searchInput:focus {
                outline: none;
                box-shadow: 0 10px 50px rgba(0,0,0,0.4);
                transform: translateY(-2px);
            }
            
            .search-button {
                position: absolute;
                right: 5px;
                top: 50%;
                transform: translateY(-50%);
                background: linear-gradient(135deg, #ff6b6b, #ee5a52);
                border: none;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                cursor: pointer;
                transition: all 0.3s;
                color: white;
                font-size: 1.5em;
            }
            
            .search-button:hover {
                transform: translateY(-50%) scale(1.1);
                box-shadow: 0 5px 20px rgba(238,90,82,0.4);
            }
            
            .suggestions {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border-radius: 15px;
                margin-top: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                display: none;
                z-index: 1000;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .suggestion-item {
                padding: 15px 25px;
                cursor: pointer;
                transition: background 0.2s;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .suggestion-item:hover {
                background: #f8f9fa;
            }
            
            .suggestion-item:last-child {
                border-bottom: none;
            }
            
            .example-queries {
                text-align: center;
                margin-top: 30px;
                color: rgba(255,255,255,0.9);
            }
            
            .example-chip {
                display: inline-block;
                background: rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 20px;
                margin: 5px;
                cursor: pointer;
                transition: all 0.3s;
                backdrop-filter: blur(10px);
            }
            
            .example-chip:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }
            
            #results {
                margin-top: 30px;
            }
            
            .result-card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin: 15px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                transition: all 0.3s;
            }
            
            .result-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            .result-type {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.85em;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .type-organization {
                background: #e3f2fd;
                color: #1976d2;
            }
            
            .type-tournament {
                background: #f3e5f5;
                color: #7b1fa2;
            }
            
            .type-venue {
                background: #e8f5e9;
                color: #388e3c;
            }
            
            .result-title {
                font-size: 1.3em;
                font-weight: bold;
                margin: 10px 0;
            }
            
            .result-details {
                color: #666;
                line-height: 1.6;
            }
            
            .search-stats {
                text-align: center;
                color: #666;
                margin: 20px 0;
                font-style: italic;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: #999;
            }
            
            .loading::after {
                content: '';
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #667eea;
                border-radius: 50%;
                border-top-color: transparent;
                animation: spin 0.8s linear infinite;
                margin-left: 10px;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
        
        <div class="search-container">
            <h2 class="search-title">🚀 Universal Search</h2>
            <p class="search-subtitle">Just type what you're looking for - I understand natural language!</p>
            
            <div class="search-box">
                <input 
                    type="text" 
                    id="searchInput" 
                    placeholder="Try: tournaments with over 100 people, or SoCal FGC, or recent events..."
                    autocomplete="off"
                >
                <button class="search-button" onclick="performSearch()">🔍</button>
                <div class="suggestions" id="suggestions"></div>
            </div>
            
            <div class="example-queries">
                <div class="example-chip" onclick="setQuery('tournaments with over 100 attendees')">
                    tournaments with over 100 attendees
                </div>
                <div class="example-chip" onclick="setQuery('top organizations by attendance')">
                    top organizations by attendance
                </div>
                <div class="example-chip" onclick="setQuery('venues with most events')">
                    venues with most events
                </div>
                <div class="example-chip" onclick="setQuery('recent tournaments in 2025')">
                    recent tournaments in 2025
                </div>
            </div>
        </div>
        
        <div id="results"></div>
        
        <script>
            let searchTimeout;
            let suggestTimeout;
            
            function setQuery(query) {
                document.getElementById('searchInput').value = query;
                performSearch();
            }
            
            function performSearch() {
                const query = document.getElementById('searchInput').value;
                if (!query) return;
                
                document.getElementById('results').innerHTML = '<div class="loading">Searching the universe</div>';
                document.getElementById('suggestions').style.display = 'none';
                
                fetch('/api/search?q=' + encodeURIComponent(query))
                    .then(response => response.json())
                    .then(data => {
                        displayResults(data);
                    })
                    .catch(error => {
                        document.getElementById('results').innerHTML = 
                            '<div class="result-card">Error: ' + error + '</div>';
                    });
            }
            
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                
                if (data.count === 0) {
                    resultsDiv.innerHTML = '<div class="result-card">No results found. Try a different query!</div>';
                    return;
                }
                
                let html = '<div class="search-stats">Found ' + data.count + ' results for "' + 
                          data.query + '"</div>';
                
                data.results.forEach(result => {
                    html += '<div class="result-card">';
                    html += '<span class="result-type type-' + result.type + '">' + 
                           result.type.toUpperCase() + '</span>';
                    
                    if (result.type === 'visualization' || result.type === 'resource') {
                        html += '<div class="result-title">' + result.title + '</div>';
                        html += '<div class="result-details">';
                        html += result.description + '<br><br>';
                        if (result.filename && result.filename.endsWith('.png')) {
                            html += '<a href="' + result.url + '" target="_blank">';
                            html += '<img src="' + result.url + '" style="max-width: 500px; border: 2px solid #333; border-radius: 8px; margin-top: 10px;">';
                            html += '</a>';
                        } else if (result.filename && result.filename.endsWith('.html')) {
                            html += '<a href="' + result.url + '" target="_blank" style="display: inline-block; padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 4px;">Open Interactive View</a>';
                        }
                        html += '</div>';
                    } else if (result.type === 'organization') {
                        html += '<div class="result-title">' + result.name + '</div>';
                        html += '<div class="result-details">';
                        html += 'Total Attendance: <strong>' + result.total_attendance.toLocaleString() + '</strong><br>';
                        html += 'Tournaments: <strong>' + result.tournament_count + '</strong><br>';
                        html += 'Average: <strong>' + Math.round(result.avg_attendance) + '</strong> per event';
                        html += ' <a href="/edit_org/' + result.id + '" style="margin-left: 20px;">Edit</a>';
                        html += '</div>';
                    } else if (result.type === 'tournament') {
                        html += '<div class="result-title">' + result.name + '</div>';
                        html += '<div class="result-details">';
                        html += 'Attendance: <strong>' + result.attendance + '</strong><br>';
                        html += 'Venue: ' + result.venue + '<br>';
                        if (result.date !== 'Unknown') {
                            html += 'Date: ' + new Date(result.date).toLocaleDateString();
                        }
                        html += '</div>';
                    } else if (result.type === 'venue') {
                        html += '<div class="result-title">' + result.name + '</div>';
                        html += '<div class="result-details">';
                        html += 'Total Events: <strong>' + result.event_count + '</strong><br>';
                        html += 'Total Attendance: <strong>' + result.total_attendance.toLocaleString() + '</strong><br>';
                        html += 'Average: <strong>' + Math.round(result.avg_attendance) + '</strong> per event';
                        html += '</div>';
                    }
                    
                    html += '</div>';
                });
                
                resultsDiv.innerHTML = html;
            }
            
            // Auto-suggestions as you type
            document.getElementById('searchInput').addEventListener('input', function(e) {
                clearTimeout(suggestTimeout);
                const query = e.target.value;
                
                if (query.length < 2) {
                    document.getElementById('suggestions').style.display = 'none';
                    return;
                }
                
                suggestTimeout = setTimeout(() => {
                    fetch('/api/suggestions?q=' + encodeURIComponent(query))
                        .then(response => response.json())
                        .then(suggestions => {
                            displaySuggestions(suggestions);
                        });
                }, 300);
            });
            
            function displaySuggestions(suggestions) {
                const suggestDiv = document.getElementById('suggestions');
                
                if (suggestions.length === 0) {
                    suggestDiv.style.display = 'none';
                    return;
                }
                
                let html = '';
                suggestions.forEach(suggestion => {
                    html += '<div class="suggestion-item" onclick="setQuery(\\'' + 
                           suggestion.replace(/'/g, "\\\\'") + '\\')">' + suggestion + '</div>';
                });
                
                suggestDiv.innerHTML = html;
                suggestDiv.style.display = 'block';
            }
            
            // Enter key to search
            document.getElementById('searchInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
            
            // Click outside to hide suggestions
            document.addEventListener('click', function(e) {
                if (!e.target.closest('.search-box')) {
                    document.getElementById('suggestions').style.display = 'none';
                }
            });
        </script>
        """
        
        page = wrap_page(
            content,
            'Universal Search',
            nav_links=[
                ('/', 'Home'),
                ('/attendance', 'Attendance Report'),
                ('/organizations', 'Organizations')
            ]
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_search_api(self, query):
        """API endpoint for search"""
        try:
            results = conversational_search(query)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def serve_suggestions_api(self, partial):
        """API endpoint for search suggestions"""
        try:
            suggestions = get_suggestions(partial)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(suggestions).encode())
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps([]).encode())

def run_server(port=8081, host='0.0.0.0'):
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