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
        elif parsed.path == '/create_org':
            self.serve_create_org_form()
        elif parsed.path == '/attendance':
            self.serve_attendance_report()
        elif parsed.path == '/players':
            self.serve_player_rankings()
        elif parsed.path == '/events':
            self.serve_event_statistics()
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
        elif parsed.path.startswith('/edit_contact_group'):
            # Parse tournament IDs from query string
            query = urllib.parse.parse_qs(parsed.query)
            ids = query.get('ids', [''])[0]
            if ids:
                tournament_ids = [int(id) for id in ids.split(',')]
                self.serve_edit_contact_group(tournament_ids)
            else:
                self.send_error(400, "No tournament IDs provided")
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
        elif parsed.path == '/create_org':
            # Handle organization creation
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            if self.create_organization(params):
                self.send_response(303)
                self.send_header('Location', '/organizations')
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
                self.send_header('Location', f'/edit_org/{org_id}')
                self.end_headers()
            else:
                self.send_error(500)
        elif parsed.path.startswith('/add_contact/'):
            org_id = int(parsed.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            if self.add_organization_contact(org_id, params):
                self.send_response(303)
                self.send_header('Location', f'/edit_org/{org_id}')
                self.end_headers()
            else:
                self.send_error(500)
        elif parsed.path.startswith('/remove_contact/'):
            parts = parsed.path.split('/')
            org_id = int(parts[-2])
            contact_index = int(parts[-1])
            
            if self.remove_organization_contact(org_id, contact_index):
                self.send_response(303)
                self.send_header('Location', f'/edit_org/{org_id}')
                self.end_headers()
            else:
                self.send_error(500)
        elif parsed.path.startswith('/delete_org/'):
            org_id = int(parsed.path.split('/')[-1])
            
            if self.delete_organization(org_id):
                self.send_response(303)
                self.send_header('Location', '/organizations')
                self.end_headers()
            else:
                self.send_error(500)
        elif parsed.path == '/update_contact_group':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            ids = params.get('ids', [''])[0]
            new_contact = params.get('new_contact', [''])[0]
            
            if ids and new_contact:
                tournament_ids = [int(id) for id in ids.split(',')]
                if self.update_contact_group(tournament_ids, new_contact):
                    self.send_response(303)
                    self.send_header('Location', '/unnamed')
                    self.end_headers()
                else:
                    self.send_error(500)
            else:
                self.send_error(400, "Missing required parameters")
        elif parsed.path == '/assign_to_organization':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            
            tournament_ids = params.get('tournament_ids', [''])[0]
            org_id = params.get('org_id', [''])[0]
            
            if tournament_ids and org_id:
                # Parse all tournament IDs from comma-separated groups
                all_ids = []
                for group in tournament_ids.split(','):
                    if ',' in group:  # Multiple IDs in a group
                        all_ids.extend([int(id) for id in group.split(',')])
                    else:
                        all_ids.append(int(group))
                
                if self.assign_to_organization(all_ids, int(org_id)):
                    self.send_response(303)
                    self.send_header('Location', '/unnamed')
                    self.end_headers()
                else:
                    self.send_error(500)
            else:
                self.send_error(400, "Missing required parameters")
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
            ('/players', '🏆 Player Rankings'),
            ('/attendance', 'Attendance Report'),
            ('/unnamed', 'View Unnamed Tournaments'),
            ('/organizations', 'View All Organizations'),
            ('/heatmap', '🗺️ Heat Map')
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
                <li><strong>Player Rankings:</strong> Power rankings based on tournament placements</li>
                <li><strong>Attendance Report:</strong> View tournament attendance rankings by organization</li>
                <li><strong>Unnamed Tournaments:</strong> Edit tournaments that need proper organization names</li>
                <li><strong>All Organizations:</strong> View all organizations in the database</li>
                <li><strong>Heat Map:</strong> Interactive geographic visualization of tournament locations</li>
                <li><strong>Universal Search:</strong> Search across all tournaments, organizations, and data</li>
            </ul>
        </div>
        
        <div class="stats-box">
            <h3>Visualizations</h3>
            <ul>
                <li><a href="/heatmap">🗺️ Interactive Heat Map</a> - Live zoomable map of tournament locations</li>
                <li><a href="/heatmap/tournament_heatmap.html">📊 Full Interactive Map</a> - Detailed tournament map with popups</li>
                <li><a href="/heatmap/tournament_heatmap.png">📈 Density Heat Map</a> - Static tournament density visualization</li>
                <li><a href="/heatmap/tournament_heatmap_with_map.png">🌍 Density with Street Map</a> - Heat map overlaid on street map</li>
                <li><a href="/heatmap/attendance_heatmap.png">👥 Attendance Heat Map</a> - Attendance-weighted map with street background</li>
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
        """Serve list of unnamed tournaments grouped by contact"""
        tournaments = get_unnamed_tournaments()
        
        # Group tournaments by primary_contact
        grouped = {}
        for t in tournaments:
            contact = t['primary_contact'] or 'No Contact'
            if contact not in grouped:
                grouped[contact] = {
                    'contact': contact,
                    'tournaments': [],
                    'total_attendance': 0,
                    'count': 0,
                    'cities': set(),
                    'slugs': [],  # Collect all slugs
                    'tournament_ids': []  # Collect all IDs for editing
                }
            grouped[contact]['tournaments'].append(t)
            grouped[contact]['total_attendance'] += t['num_attendees']
            grouped[contact]['count'] += 1
            grouped[contact]['tournament_ids'].append(t['id'])
            if t['city']:
                grouped[contact]['cities'].add(t['city'])
            if t.get('short_slug'):
                grouped[contact]['slugs'].append(t['short_slug'])
        
        # Convert to list and sort by total attendance
        contact_groups = list(grouped.values())
        contact_groups.sort(key=lambda x: x['total_attendance'], reverse=True)
        
        # Navigation
        nav_links = [
            ('/', 'Home'),
            ('/organizations', 'View All Organizations')
        ]
        
        # Stats box
        stats = {
            'Unique Contacts': len(contact_groups),
            'Total Tournaments': len(tournaments),
            'Total Attendance': sum(t['num_attendees'] for t in tournaments)
        }
        content = format_stats_box("Summary", stats)
        
        # Add JavaScript for checkbox handling
        content += '''
        <script>
        function toggleAllCheckboxes() {
            var selectAll = document.getElementById('selectAll');
            var checkboxes = document.getElementsByClassName('contact-checkbox');
            for (var i = 0; i < checkboxes.length; i++) {
                checkboxes[i].checked = selectAll.checked;
            }
        }
        
        function assignToOrganization() {
            var checkboxes = document.getElementsByClassName('contact-checkbox');
            var selectedIds = [];
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i].checked) {
                    selectedIds.push(checkboxes[i].value);
                }
            }
            
            if (selectedIds.length === 0) {
                alert('Please select at least one contact group');
                return;
            }
            
            var orgSelect = document.getElementById('org-select');
            var orgId = orgSelect.value;
            
            if (!orgId) {
                alert('Please select an organization');
                return;
            }
            
            // Submit form
            document.getElementById('ids-input').value = selectedIds.join(',');
            document.getElementById('assign-form').submit();
        }
        </script>
        '''
        
        # Format table data with checkboxes - we'll build the table manually to avoid escaping
        # headers = ['Select All', 'Contact', 'Tournaments', 'Total Attendance', 'Start.gg Slugs', 'Cities', 'Action']
        
        # Custom row formatter for grouped data with checkboxes
        def row_formatter(group):
            cities = ', '.join(sorted(group['cities'])) if group['cities'] else 'N/A'
            # Truncate cities if too long
            if len(cities) > 40:
                cities = cities[:37] + '...'
            
            # Format slugs as links
            slug_links = []
            for slug in group['slugs'][:3]:  # Show first 3 slugs
                slug_links.append(f'<a href="https://start.gg/{slug}" target="_blank" style="color: #667eea;">{slug}</a>')
            if len(group['slugs']) > 3:
                slug_links.append(f'+{len(group["slugs"]) - 3} more')
            slugs_html = ', '.join(slug_links) if slug_links else 'N/A'
            
            # Create edit link that passes all tournament IDs
            ids_param = ','.join(str(id) for id in group['tournament_ids'])
            
            return f"""
            <tr>
                <td><input type="checkbox" class="contact-checkbox" value="{ids_param}"></td>
                <td>{html.escape(group['contact'])}</td>
                <td>{group['count']}</td>
                <td>{group['total_attendance']:,}</td>
                <td>{slugs_html}</td>
                <td>{html.escape(cities)}</td>
                <td><a href="/edit_contact_group?ids={ids_param}" class="action-link">Edit</a></td>
            </tr>"""
        
        if contact_groups:
            # Build table manually to avoid HTML escaping in headers
            content += '''
            <table>
            <thead>
                <tr>
                    <th><input type="checkbox" id="selectAll" onclick="toggleAllCheckboxes()"></th>
                    <th>Contact</th>
                    <th>Tournaments</th>
                    <th>Total Attendance</th>
                    <th>Start.gg Slugs</th>
                    <th>Cities</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
            '''
            
            # Add rows using the formatter
            for group in contact_groups:
                content += row_formatter(group)
            
            content += '</tbody></table>'
            
            # Add organization dropdown and assign button
            content += '''
            <div style="margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3>Bulk Assign to Organization</h3>
                <form id="assign-form" method="POST" action="/assign_to_organization">
                    <input type="hidden" id="ids-input" name="tournament_ids">
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <select id="org-select" name="org_id" style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                            <option value="">-- Select Organization --</option>
            '''
            
            # Get organizations for dropdown
            from database_utils import get_session
            from tournament_models import Organization
            with get_session() as session:
                orgs = session.query(Organization).order_by(Organization.display_name).all()
                for org in orgs:
                    content += f'<option value="{org.id}">{html.escape(org.display_name)}</option>'
            
            content += '''
                        </select>
                        <button type="button" onclick="assignToOrganization()" 
                                style="background: #667eea; color: white; padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer;">
                            Assign Selected
                        </button>
                    </div>
                </form>
            </div>
            '''
        else:
            content += '<p>No unnamed tournaments found!</p>'
        
        page = wrap_page(
            content,
            title="Unnamed Tournaments by Contact",
            subtitle=f"{len(contact_groups)} unique contacts need organization names",
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_create_org_form(self):
        """Serve the create organization form"""
        nav_links = [
            ('/', 'Home'),
            ('/organizations', 'Back to Organizations')
        ]
        
        content = '''
        <h2>Create New Organization</h2>
        <form method="POST" action="/create_org">
            <div style="margin-bottom: 15px;">
                <label for="display_name" style="display: block; margin-bottom: 5px;">Organization Name:</label>
                <input type="text" id="display_name" name="display_name" required 
                       style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                <small style="color: #666;">The name to show in reports</small>
            </div>
            
            <div style="margin-top: 20px;">
                <input type="submit" value="Create Organization" 
                       style="background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer;">
                <a href="/organizations" style="margin-left: 10px; color: #666;">Cancel</a>
            </div>
        </form>
        '''
        
        page = wrap_page(
            content,
            title="Create Organization",
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def create_organization(self, params):
        """Create a new organization"""
        try:
            from tournament_models import Organization
            from database_utils import get_session
            
            display_name = params.get('display_name', [''])[0]
            
            if not display_name:
                return False
            
            with get_session() as session:
                # Check if organization with same name already exists
                existing = session.query(Organization).filter_by(display_name=display_name).first()
                if existing:
                    return False
                
                # Create new organization
                org = Organization(
                    display_name=display_name
                )
                session.add(org)
                session.commit()
                
            return True
        except Exception as e:
            log_info(f"Error creating organization: {e}")
            return False
    
    def serve_organizations(self):
        """Serve list of all organizations using shared table formatter"""
        from database_utils import get_session
        from tournament_models import Organization
        
        # Get organizations with session
        with get_session() as session:
            from tournament_models import Tournament
            from database_utils import normalize_contact
            
            orgs = session.query(Organization).all()
            
            # Extract data while session is active
            org_data = []
            for org in orgs:
                # Get contact summary
                contacts = org.contacts
                email_count = sum(1 for c in contacts if c.get('type') == 'email')
                discord_count = sum(1 for c in contacts if c.get('type') == 'discord')
                
                # Calculate tournament count manually within session
                # Collect normalized contacts for this org
                org_contacts_normalized = set()
                for contact in contacts:
                    value = contact.get('value', '')
                    if value:
                        org_contacts_normalized.add(normalize_contact(value))
                
                # Count tournaments that match
                tournament_count = 0
                if org_contacts_normalized:
                    tournaments = session.query(Tournament).all()
                    for t in tournaments:
                        if t.primary_contact:
                            t_normalized = normalize_contact(t.primary_contact)
                            if t_normalized in org_contacts_normalized:
                                tournament_count += 1
                
                org_data.append({
                    'id': org.id,
                    'display_name': org.display_name,
                    'email_count': email_count,
                    'discord_count': discord_count,
                    'tournament_count': tournament_count
                })
        
        # Navigation
        nav_links = [
            ('/', 'Home'),
            ('/unnamed', 'View Unnamed Tournaments'),
            ('/attendance', 'Attendance Report')
        ]
        
        # Stats box with create button
        stats = {
            'Total Organizations': len(org_data)
        }
        content = format_stats_box("Summary", stats)
        
        # Add create organization button
        content += '''
        <div style="margin: 20px 0;">
            <a href="/create_org" class="nav-links" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; display: inline-block;">
                + Create New Organization
            </a>
        </div>
        '''
        
        # Format table with organization info
        headers = ['ID', 'Display Name', 'Contacts', 'Tournaments', 'Actions']
        
        # Custom row formatter for action links
        def org_row_formatter(org):
            # Build contact summary
            contact_summary = []
            if org['email_count'] > 0:
                contact_summary.append(f"{org['email_count']} email")
            if org['discord_count'] > 0:
                contact_summary.append(f"{org['discord_count']} discord")
            contact_str = ', '.join(contact_summary) if contact_summary else 'No contacts'
            
            return f"""
            <tr>
                <td>{org['id']}</td>
                <td>{html.escape(org['display_name'])}</td>
                <td>{contact_str}</td>
                <td>{org['tournament_count']}</td>
                <td>
                    <a href="/edit_org/{org['id']}" class="action-link">Edit</a>
                    <form method="POST" action="/delete_org/{org['id']}" style="display: inline-block; margin-left: 10px;"
                          onsubmit="return confirm('Are you sure you want to delete {html.escape(org['display_name'])}?');">
                        <input type="submit" value="Delete" 
                               style="background: #dc3545; color: white; padding: 5px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                    </form>
                </td>
            </tr>"""
        
        if org_data:
            content += format_table(headers, org_data, org_row_formatter)
        else:
            content += '<p>No organizations found. <a href="/create_org">Create one</a>!</p>'
        
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
    
    def serve_player_rankings(self):
        """Serve player rankings page"""
        from database_utils import get_player_rankings, get_session
        from tournament_models import Player, TournamentPlacement
        from sqlalchemy import distinct, func
        
        nav_links = [
            ('/', 'Home'),
            ('/events', 'Event Statistics'),
            ('/players', 'Player Rankings'),
            ('/organizations', 'Organizations'),
            ('/attendance', 'Attendance Report')
        ]
        
        # Get available event types for filtering
        with get_session() as session:
            event_types = session.query(
                distinct(TournamentPlacement.event_name)
            ).filter(
                TournamentPlacement.event_name.isnot(None)
            ).order_by(
                TournamentPlacement.event_name
            ).all()
            event_types = [e[0] for e in event_types if e[0]]
        
        # Get parameters from query string
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        event_filter = params.get('event', ['all'])[0]
        limit = int(params.get('limit', ['50'])[0])
        
        # Get player rankings with proper filtering
        if event_filter != 'all':
            # Filter by specific event
            rankings = get_player_rankings(limit=limit, event_filter=event_filter)
        else:
            rankings = get_player_rankings(limit=limit)
        
        # Get total player count
        with get_session() as session:
            total_players = session.query(Player).count()
            if event_filter != 'all':
                total_placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.event_name == event_filter
                ).count()
            else:
                total_placements = session.query(TournamentPlacement).count()
        
        # Build page content
        content = f'''
        <div class="stats-box">
            <h2>Player Rankings</h2>
            <p>Power rankings based on tournament placements (Top 8 finishes)</p>
            <ul>
                <li><strong>Total Players:</strong> {total_players:,}</li>
                <li><strong>Total Placements:</strong> {total_placements:,} {f"({event_filter})" if event_filter != "all" else ""}</li>
                <li><strong>Ranking System:</strong> 1st=8pts, 2nd=7pts, 3rd=6pts, ..., 8th=1pt</li>
            </ul>
        </div>
        
        <div class="filter-box" style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
            <form method="get" action="/players">
                <label style="margin-right: 15px;">
                    Event Type:
                    <select name="event" onchange="this.form.submit()" style="padding: 5px;">
                        <option value="all" {'selected' if event_filter == 'all' else ''}>All Events</option>
                        <optgroup label="Main Events">
                            <option value="Ultimate Singles" {'selected' if event_filter == 'Ultimate Singles' else ''}>Ultimate Singles</option>
                            <option value="Ultimate Doubles" {'selected' if event_filter == 'Ultimate Doubles' else ''}>Ultimate Doubles</option>
                        </optgroup>
                        <optgroup label="Special Events">
        '''
        
        # Add other available event types
        special_events = [e for e in event_types if 'Special' in e]
        other_events = [e for e in event_types if e not in ['Ultimate Singles', 'Ultimate Doubles'] and 'Special' not in e]
        
        for event in special_events:
            selected = 'selected' if event_filter == event else ''
            content += f'                    <option value="{html.escape(event)}" {selected}>{html.escape(event)}</option>\n'
        
        if other_events:
            content += '                </optgroup>\n                <optgroup label="Other Events">\n'
            for event in other_events:
                selected = 'selected' if event_filter == event else ''
                content += f'                    <option value="{html.escape(event)}" {selected}>{html.escape(event)}</option>\n'
        
        content += f'''
                        </optgroup>
                    </select>
                </label>
                <label>
                    Show Top:
                    <select name="limit" onchange="this.form.submit()">
                        <option value="25" {'selected' if limit == 25 else ''}>25</option>
                        <option value="50" {'selected' if limit == 50 else ''}>50</option>
                        <option value="100" {'selected' if limit == 100 else ''}>100</option>
                        <option value="200" {'selected' if limit == 200 else ''}>200</option>
                    </select>
                </label>
            </form>
        </div>
        '''
        
        if rankings:
            # Format player data for table
            table_data = []
            for player in rankings:
                table_data.append({
                    'rank': player['rank'],
                    'gamer_tag': player['gamer_tag'],
                    'points': player['total_points'],
                    'tournaments': player['tournament_count'],
                    'avg_points': player['avg_points'],
                    'first': player['first_places'],
                    'second': player['second_places'],
                    'third': player['third_places']
                })
            
            # Custom formatter for player rows
            def player_row_formatter(row):
                medal_html = ''
                if row['first'] > 0:
                    medal_html += f'<span style="color: gold;">🥇{row["first"]}</span> '
                if row['second'] > 0:
                    medal_html += f'<span style="color: silver;">🥈{row["second"]}</span> '
                if row['third'] > 0:
                    medal_html += f'<span style="color: #CD7F32;">🥉{row["third"]}</span>'
                
                return f'''
                <tr>
                    <td style="text-align: center; font-weight: bold;">#{row["rank"]}</td>
                    <td style="font-weight: bold;">{html.escape(row["gamer_tag"])}</td>
                    <td style="text-align: center;">{row["points"]}</td>
                    <td style="text-align: center;">{row["tournaments"]}</td>
                    <td style="text-align: center;">{row["avg_points"]}</td>
                    <td>{medal_html}</td>
                </tr>
                '''
            
            headers = ['Rank', 'Player', 'Points', 'Events', 'Avg', 'Podiums']
            content += format_table(headers, table_data, player_row_formatter)
            
            # Add legend
            content += '''
            <div style="margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                <strong>Legend:</strong> 
                🥇 First Place (8pts) &nbsp;
                🥈 Second Place (7pts) &nbsp;
                🥉 Third Place (6pts)
            </div>
            '''
        else:
            content += '<p>No player data available. Run <code>--fetch-standings</code> to import tournament results.</p>'
        
        content += f'<p class="footer-text">Last updated: {get_timestamp()}</p>'
        
        page = wrap_page(
            content,
            title="Player Power Rankings",
            subtitle=f"SoCal FGC - {event_filter}" if event_filter != 'all' else "SoCal FGC - All Events",
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_event_statistics(self):
        """Serve event statistics page showing normalized event distribution"""
        from database_utils import get_session
        from tournament_models import TournamentPlacement, Player, Tournament
        from sqlalchemy import func, distinct
        from collections import defaultdict
        import json
        
        nav_links = [
            ('/', 'Home'),
            ('/events', 'Event Statistics'),
            ('/players', 'Player Rankings'),
            ('/organizations', 'Organizations'),
            ('/attendance', 'Attendance Report')
        ]
        
        with get_session() as session:
            # Get event distribution
            event_stats = session.query(
                TournamentPlacement.event_name,
                func.count(distinct(TournamentPlacement.player_id)).label('unique_players'),
                func.count(TournamentPlacement.id).label('total_placements'),
                func.count(distinct(TournamentPlacement.tournament_id)).label('tournament_count')
            ).group_by(
                TournamentPlacement.event_name
            ).order_by(
                func.count(TournamentPlacement.id).desc()
            ).all()
            
            # Get top players by event
            top_players_by_event = {}
            for event_name, _, _, _ in event_stats:
                if event_name:
                    # Get top 3 players for this event
                    placements = session.query(
                        Player.gamer_tag,
                        func.sum(9 - TournamentPlacement.placement).label('points'),
                        func.count(TournamentPlacement.id).label('count')
                    ).join(
                        TournamentPlacement
                    ).filter(
                        TournamentPlacement.event_name == event_name
                    ).group_by(
                        Player.gamer_tag
                    ).order_by(
                        func.sum(9 - TournamentPlacement.placement).desc()
                    ).limit(3).all()
                    
                    top_players_by_event[event_name] = [
                        {'gamer_tag': p[0], 'points': p[1], 'count': p[2]} 
                        for p in placements
                    ]
            
            # Calculate totals
            total_placements = sum(stat[2] for stat in event_stats if stat[0])
            total_unique_players = session.query(
                func.count(distinct(TournamentPlacement.player_id))
            ).scalar()
            
            # Group events by category
            singles_events = [s for s in event_stats if s[0] and 'Singles' in s[0] and 'Special' not in s[0]]
            doubles_events = [s for s in event_stats if s[0] and 'Doubles' in s[0]]
            special_events = [s for s in event_stats if s[0] and 'Special' in s[0]]
            other_events = [s for s in event_stats if s[0] and s not in singles_events + doubles_events + special_events]
        
        # Build content
        content = f'''
        <div class="stats-box">
            <h2>Event Statistics</h2>
            <p>Distribution of normalized event types across all tournaments</p>
            <ul>
                <li><strong>Total Event Types:</strong> {len([s for s in event_stats if s[0]])}</li>
                <li><strong>Total Placements:</strong> {total_placements:,}</li>
                <li><strong>Unique Players:</strong> {total_unique_players:,}</li>
            </ul>
        </div>
        
        <style>
            .event-category {{
                margin: 30px 0;
                background: #f8f9fa;
                border-radius: 12px;
                padding: 20px;
                border-left: 4px solid #007bff;
            }}
            .event-category h3 {{
                margin-top: 0;
                color: #333;
            }}
            .event-card {{
                background: white;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .event-card:hover {{
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }}
            .event-stats {{
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                flex-wrap: wrap;
            }}
            .event-stat {{
                flex: 1;
                min-width: 100px;
                text-align: center;
                padding: 5px;
            }}
            .event-stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #007bff;
            }}
            .event-stat-label {{
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
            }}
            .top-players {{
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #eee;
            }}
            .player-badge {{
                display: inline-block;
                background: #e9ecef;
                padding: 4px 8px;
                border-radius: 4px;
                margin: 2px;
                font-size: 14px;
            }}
            .medal {{
                margin-right: 5px;
            }}
        </style>
        '''
        
        # Function to render event category
        def render_category(title, events, color="#007bff"):
            if not events:
                return ""
            
            total = sum(e[2] for e in events)
            output = f'''
            <div class="event-category" style="border-left-color: {color};">
                <h3>{title} ({len(events)} types, {total:,} placements)</h3>
            '''
            
            for event_name, unique_players, total_placements, tournament_count in events:
                top_players = top_players_by_event.get(event_name, [])
                
                output += f'''
                <div class="event-card">
                    <h4>{html.escape(event_name)}</h4>
                    <div class="event-stats">
                        <div class="event-stat">
                            <div class="event-stat-value">{total_placements}</div>
                            <div class="event-stat-label">Placements</div>
                        </div>
                        <div class="event-stat">
                            <div class="event-stat-value">{unique_players}</div>
                            <div class="event-stat-label">Players</div>
                        </div>
                        <div class="event-stat">
                            <div class="event-stat-value">{tournament_count}</div>
                            <div class="event-stat-label">Tournaments</div>
                        </div>
                    </div>
                '''
                
                if top_players:
                    output += '<div class="top-players"><strong>Top Players:</strong> '
                    medals = ['🥇', '🥈', '🥉']
                    for i, player in enumerate(top_players):
                        output += f'''
                        <span class="player-badge">
                            <span class="medal">{medals[i]}</span>
                            {html.escape(player['gamer_tag'])} ({player['points']} pts)
                        </span>
                        '''
                    output += '</div>'
                
                output += '</div>'
            
            output += '</div>'
            return output
        
        # Add event categories
        content += render_category("Singles Events", singles_events, "#28a745")
        content += render_category("Doubles/Teams Events", doubles_events, "#17a2b8")
        content += render_category("Special Events", special_events, "#ffc107")
        if other_events:
            content += render_category("Other Events", other_events, "#6c757d")
        
        # Add chart visualization
        chart_data = [
            {'name': s[0], 'placements': s[2], 'players': s[1]} 
            for s in event_stats if s[0]
        ]
        
        content += f'''
        <div class="stats-box" style="margin-top: 30px;">
            <h3>Event Distribution Chart</h3>
            <canvas id="eventChart" width="400" height="200"></canvas>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
        const ctx = document.getElementById('eventChart').getContext('2d');
        const chartData = {json.dumps(chart_data[:10])};  // Top 10 events
        
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: chartData.map(d => d.name),
                datasets: [{{
                    label: 'Placements',
                    data: chartData.map(d => d.placements),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}, {{
                    label: 'Unique Players',
                    data: chartData.map(d => d.players),
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        </script>
        '''
        
        # Wrap in page
        page = wrap_page(
            "Event Statistics",
            content,
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_heatmap(self, year=2025):
        """Serve an interactive heat map of tournaments for a specific year"""
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
        
        # Get tournament data for the specified year
        heat_data = []
        with get_session() as session:
            tournaments = session.query(Tournament).filter(
                Tournament.lat.isnot(None),
                Tournament.lng.isnot(None),
                Tournament.start_at.like(f'{year}%')
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
        
        // Add light tile layer (same as attendance heat map)
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
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
            title=f"{year} Tournament Heat Map",
            subtitle=f"Interactive visualization of SoCal FGC tournaments in {year}",
            nav_links=nav_links
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(page.encode())
    
    def serve_edit_contact_group(self, tournament_ids):
        """Serve edit form for a group of tournaments with same contact"""
        from database_utils import get_session
        from tournament_models import Tournament
        
        with get_session() as session:
            tournaments = []
            contact = None
            
            # Get all tournaments
            for tid in tournament_ids:
                t = session.get(Tournament, tid)
                if t:
                    if contact is None:
                        contact = t.primary_contact
                    tournaments.append({
                        'id': t.id,
                        'name': t.name,
                        'primary_contact': t.primary_contact,
                        'num_attendees': t.num_attendees or 0,
                        'venue_name': t.venue_name,
                        'city': t.city,
                        'short_slug': t.short_slug
                    })
            
            if not tournaments:
                self.send_error(404, "No tournaments found")
                return
            
            # Navigation
            nav_links = [
                ('/', 'Home'),
                ('/unnamed', 'Back to Unnamed List')
            ]
            
            # Summary box
            total_attendance = sum(t['num_attendees'] for t in tournaments)
            cities = sorted(set(t['city'] for t in tournaments if t['city']))
            
            content = f"""
            <div class="stats-box">
                <h2>Edit Contact Group</h2>
                <p><strong>Current Contact:</strong> {html.escape(contact or 'No Contact')}</p>
                <p><strong>Total Tournaments:</strong> {len(tournaments)}</p>
                <p><strong>Total Attendance:</strong> {total_attendance:,}</p>
                <p><strong>Cities:</strong> {', '.join(cities) if cities else 'N/A'}</p>
            </div>
            
            <!-- Update All Form -->
            <div class="stats-box">
                <h3>Update All Tournaments</h3>
                <form method="POST" action="/update_contact_group" style="margin-bottom: 20px;">
                    <input type="hidden" name="ids" value="{','.join(str(tid) for tid in tournament_ids)}">
                    <div style="margin-bottom: 15px;">
                        <label for="new_contact">New Organization Name (for all {len(tournaments)} tournaments):</label>
                        <input type="text" name="new_contact" 
                               value="{html.escape(contact or '')}"
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <input type="submit" value="Update All Tournaments" 
                           style="background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer;">
                </form>
            </div>
            
            <!-- Tournament List -->
            <div class="stats-box">
                <h3>Tournaments in this Group</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #f0f0f0;">
                            <th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd;">Tournament</th>
                            <th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd;">Attendance</th>
                            <th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd;">City</th>
                            <th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd;">Start.gg</th>
                            <th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for i, t in enumerate(tournaments):
                row_style = 'background-color: #f9f9f9;' if i % 2 == 0 else ''
                slug_link = f'<a href="https://start.gg/{t["short_slug"]}" target="_blank">{t["short_slug"]}</a>' if t['short_slug'] else 'N/A'
                content += f"""
                    <tr style="{row_style}">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{html.escape(t['name'])}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{t['num_attendees']:,}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{html.escape(t['city'] or 'N/A')}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{slug_link}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">
                            <a href="/edit/{t['id']}" class="action-link">Edit Individual</a>
                        </td>
                    </tr>
                """
            
            content += """
                    </tbody>
                </table>
            </div>
            """
            
            page = wrap_page(
                content,
                title="Edit Contact Group",
                subtitle=f"Managing {len(tournaments)} tournaments for {html.escape(contact or 'Unknown Contact')}",
                nav_links=nav_links
            )
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(page.encode())
    
    def serve_edit_org_form(self, org_id):
        """Serve edit form for an organization"""
        from database_utils import get_session
        import json
        
        with get_session() as session:
            org = session.query(Organization).get(org_id)
            if not org:
                self.send_error(404)
                return
            
            # Get existing contacts list
            contacts = org.contacts
            
            # Navigation
            nav_links = [
                ('/', 'Home'),
                ('/organizations', 'Back to Organizations')
            ]
            
            # Organization details and edit form
            content = f"""
            <div class="stats-box">
                <h2>Edit Organization</h2>
                
                <!-- Basic Info Form -->
                <form method="POST" action="/update_org/{org_id}" style="margin-bottom: 20px;">
                    <div style="margin-bottom: 15px;">
                        <label for="display_name">Display Name:</label>
                        <input type="text" name="display_name" value="{html.escape(org.display_name)}" 
                               required style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    <input type="submit" value="Update Name" 
                           style="background: #667eea; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                </form>
            </div>
            
            <!-- Contacts Management -->
            <div class="stats-box">
                <h3>Contacts</h3>
                
                <!-- List existing contacts -->
                <div style="margin-bottom: 20px;">
            """
            
            if contacts:
                content += '''<table style="width: 100%; margin-bottom: 20px; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #f0f0f0;">
                        <th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd; width: 20%;">Type</th>
                        <th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd; width: 60%;">Value</th>
                        <th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd; width: 20%;">Actions</th>
                    </tr>
                </thead>
                <tbody>'''
                for i, contact in enumerate(contacts):
                    contact_type = contact.get('type', '')
                    contact_value = contact.get('value', '')
                    # Alternate row colors
                    row_style = 'background-color: #f9f9f9;' if i % 2 == 0 else ''
                    content += f'''
                    <tr style="{row_style}">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{html.escape(contact_type.title())}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;">{html.escape(contact_value)}</td>
                        <td style="border-bottom: 1px solid #eee;">
                            <form method="POST" action="/remove_contact/{org_id}/{i}" style="display: inline-block; margin: 0;">
                                <input type="submit" value="Remove" 
                                       style="background: #dc3545; color: white; padding: 5px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500;">
                            </form>
                        </td>
                    </tr>
                    '''
                content += '</tbody></table>'
            else:
                content += '<p style="color: #666;">No contacts added yet.</p>'
            
            # Add new contact form
            content += f'''
                </div>
                
                <!-- Add new contact form -->
                <h4>Add New Contact</h4>
                <form method="POST" action="/add_contact/{org_id}">
                    <div style="display: flex; gap: 10px; align-items: flex-end;">
                        <div style="flex: 0 0 150px;">
                            <label for="contact_type">Type:</label>
                            <select name="contact_type" required 
                                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="email">Email</option>
                                <option value="discord">Discord</option>
                            </select>
                        </div>
                        <div style="flex: 1;">
                            <label for="contact_value">Value:</label>
                            <input type="text" name="contact_value" required 
                                   placeholder="Enter email or discord" 
                                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        </div>
                        <div>
                            <input type="submit" value="Add Contact" 
                                   style="background: #28a745; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                        </div>
                    </div>
                </form>
            </div>
            '''
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
        """Update organization display name"""
        from database_utils import get_session
        
        try:
            with get_session() as session:
                org = session.get(Organization, org_id)
                if not org:
                    return False
                
                # Update display name
                new_name = params.get('display_name', [''])[0]
                if new_name:
                    org.display_name = new_name
                    session.commit()
                
                return True
        except Exception as e:
            log_info(f"Error updating organization: {e}")
            return False
    
    def add_organization_contact(self, org_id, params):
        """Add a contact to an organization"""
        from database_utils import get_session
        
        try:
            with get_session() as session:
                org = session.get(Organization, org_id)
                if not org:
                    return False
                
                contact_type = params.get('contact_type', [''])[0]
                contact_value = params.get('contact_value', [''])[0]
                
                if contact_type and contact_value:
                    org.add_contact(contact_type, contact_value)
                    session.commit()
                    return True
                
                return False
        except Exception as e:
            log_info(f"Error adding contact: {e}")
            return False
    
    def remove_organization_contact(self, org_id, contact_index):
        """Remove a contact from an organization"""
        from database_utils import get_session
        
        try:
            with get_session() as session:
                org = session.get(Organization, org_id)
                if not org:
                    return False
                
                org.remove_contact(contact_index)
                session.commit()
                return True
        except Exception as e:
            log_info(f"Error removing contact: {e}")
            return False
    
    def update_contact_group(self, tournament_ids, new_contact):
        """Update contact for multiple tournaments"""
        from database_utils import get_session
        from tournament_models import Tournament
        
        try:
            with get_session() as session:
                updated = 0
                for tid in tournament_ids:
                    tournament = session.get(Tournament, tid)
                    if tournament:
                        tournament.primary_contact = new_contact
                        updated += 1
                
                if updated > 0:
                    session.commit()
                    log_info(f"Updated contact for {updated} tournaments to: {new_contact}")
                    return True
                return False
        except Exception as e:
            log_info(f"Error updating contact group: {e}")
            return False
    
    def delete_organization(self, org_id):
        """Delete an organization from the database"""
        from database_utils import get_session
        from tournament_models import Organization
        
        try:
            with get_session() as session:
                org = session.get(Organization, org_id)
                if not org:
                    log_info(f"Organization {org_id} not found for deletion")
                    return False
                
                org_name = org.display_name
                session.delete(org)
                session.commit()
                log_info(f"Deleted organization: {org_name} (ID: {org_id})")
                return True
        except Exception as e:
            log_info(f"Error deleting organization: {e}")
            return False
    
    def assign_to_organization(self, tournament_ids, org_id):
        """Add contacts from selected tournament groups to the organization's contact list"""
        from database_utils import get_session, normalize_contact
        from tournament_models import Tournament, Organization
        
        try:
            with get_session() as session:
                # Get the organization
                org = session.get(Organization, org_id)
                if not org:
                    log_info(f"Organization {org_id} not found")
                    return False
                
                # Get current contacts and their normalized forms to avoid duplicates
                existing_contacts = org.contacts
                existing_normalized = set()
                for contact in existing_contacts:
                    value = contact.get('value', '')
                    if value:
                        existing_normalized.add(normalize_contact(value))
                
                # Collect unique contacts from all selected tournaments
                contacts_to_add = {}  # Use dict to track unique normalized -> (type, value)
                for tid in tournament_ids:
                    tournament = session.get(Tournament, tid)
                    if tournament and tournament.primary_contact:
                        contact_value = tournament.primary_contact
                        normalized = normalize_contact(contact_value)
                        
                        # Skip if already exists in organization
                        if normalized not in existing_normalized:
                            # Determine contact type
                            if '@' in contact_value and '.' in contact_value:
                                contact_type = 'email'
                            elif 'discord:' in contact_value.lower() or '#' in contact_value:
                                contact_type = 'discord'
                            else:
                                contact_type = 'email'  # Default to email
                            
                            contacts_to_add[normalized] = (contact_type, contact_value)
                
                # Add new contacts to organization
                added_count = 0
                for normalized, (contact_type, contact_value) in contacts_to_add.items():
                    org.add_contact(contact_type, contact_value)
                    added_count += 1
                
                if added_count > 0:
                    session.commit()
                    log_info(f"Added {added_count} contacts to organization '{org.display_name}'")
                    return True
                else:
                    log_info(f"No new contacts to add (all already exist in organization)")
                    return True  # Still success, just nothing to add
        except Exception as e:
            log_info(f"Error assigning to organization: {e}")
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