#!/usr/bin/env python3
"""
Dynamic proxy server for zilogo.com subdomains
Discovers services via mDNS and routes requests to appropriate services
"""

import subprocess
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import requests
import time

class DynamicProxyHandler(BaseHTTPRequestHandler):
    def get_discovered_services(self):
        """Get current services discovered via mDNS"""
        services = {}
        try:
            # Run service discovery
            result = subprocess.run(['./go.py', '--service-status'],
                                  capture_output=True, text=True, timeout=5)

            # Service mappings for subdomains
            service_mappings = {
                'ProcessManagementGuide': 'admin',
                'NextService_WebEditor': 'tournaments',
                'Player Model Service': 'players',
                'NextService_Discord': 'discord',
                'Database Service': 'database',
                'Tournament Models (Enhanced OOP)': 'analytics',
                'ValidationCommands': 'api',
                'Organization Model Service': 'orgs',
                'Tournament Management Dashboard': 'dashboard',
                'mDNS Dynamic DNS Service': 'dns',
                'Bonjour Service Discovery Web Interface': 'bonjour'
            }

            # Parse discovered services to get latest ports (take most recent)
            latest_services = {}
            for line in result.stdout.split('\n'):
                if '🔍 Discovered:' in line and ' at 10.0.0.1:' in line:
                    parts = line.split('🔍 Discovered: ')[1].split(' at 10.0.0.1:')
                    service_name = parts[0].strip()
                    port = parts[1].strip()

                    # Find matching subdomain
                    for key, subdomain in service_mappings.items():
                        if key in service_name:
                            latest_services[subdomain] = port
                            break

            services = latest_services

        except Exception as e:
            print(f"Error discovering services: {e}")

        return services

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def do_PROPFIND(self):
        self.handle_webdav_request()

    def do_OPTIONS(self):
        self.handle_webdav_options()

    def handle_request(self):
        """Handle incoming request by routing to appropriate service"""

        # Extract subdomain from Host header
        host = self.headers.get('Host', '')
        subdomain = None

        if '.zilogo.com' in host:
            subdomain = host.split('.zilogo.com')[0]

        print(f"Request for subdomain: {subdomain}")

        # Get current services
        services = self.get_discovered_services()
        print(f"Available services: {services}")

        # Handle specific services with real data
        if subdomain == 'players':
            # Check if this is a request for a specific player file (WebDAV)
            if self.path.endswith('.txt') and self.path != '/':
                self.handle_individual_player()
            else:
                self.handle_players_service()
            return
        elif subdomain == 'tournaments':
            # Check if this is a request for a specific tournament file (WebDAV)
            if self.path.endswith('.txt') and self.path != '/':
                self.handle_individual_tournament()
            else:
                self.handle_tournaments_service()
            return
        elif subdomain == 'orgs' or subdomain == 'organizations':
            # Check if this is a request for a specific org file (WebDAV)
            if self.path.endswith('.txt') and self.path != '/':
                self.handle_individual_org()
            else:
                self.handle_organizations_service()
            return
        elif subdomain == 'admin':
            self.handle_admin_service()
            return
        elif subdomain and subdomain in services:
            # Route to specific service
            target_port = services[subdomain]
            target_url = f"http://10.0.0.1:{target_port}{self.path}"

            try:
                # Proxy the request
                response = requests.get(target_url, timeout=5)

                # Return the response
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f"<h1>{subdomain.title()} Service</h1>".encode())
                self.wfile.write(f"<p>Proxied to: {target_url}</p>".encode())
                self.wfile.write(f"<p>Service response: {response.status_code}</p>".encode())
                return

            except Exception as e:
                print(f"Error proxying to {target_url}: {e}")

        # Default response
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()

        html = f"""
        <html>
        <head><title>ZiLogo Dynamic Services</title></head>
        <body>
        <h1>ZiLogo Services</h1>
        <h2>Subdomain: {subdomain or 'none'}</h2>
        <h3>Available Services:</h3>
        <ul>
        """

        for service, port in services.items():
            html += f"<li><a href='https://{service}.zilogo.com'>{service}.zilogo.com</a> → port {port}</li>"

        html += """
        </ul>
        <p>DNS is working! All *.zilogo.com domains resolve to 10.0.0.1</p>
        </body>
        </html>
        """

        self.wfile.write(html.encode())

    def handle_players_service(self):
        """Handle players.zilogo.com - show simple list of players"""
        try:
            # Connect directly to the Player Model Service
            import requests
            try:
                # Try to get data from the player service directly
                response = requests.get('http://10.0.0.1:60757', timeout=5)
                result_text = response.text
            except:
                # Fallback to service discovery to find current port
                result = subprocess.run(['./go.py', '--service-status'],
                                      capture_output=True, text=True, timeout=10)
                result_text = result.stdout

            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            # Extract player names from the service response
            lines = result_text.split('\n')
            players = []
            for line in lines:
                # Skip service announcement lines and other noise
                if any(x in line for x in ['🌐', '🏠', '🗂️', '⚠️', '🚀', '🔧', '🧹', 'Bonjour', 'mDNS', 'Local:', 'announcement', 'service', 'No service', 'Use --help', 'Global exception', 'Real Bonjour', 'Shutting down', 'Discovered:']):
                    continue
                # Look for lines that appear to be player data
                clean_line = line.strip()
                if clean_line and len(clean_line) > 3 and not any(char in clean_line for char in [':', '=', '>', '<', '{', '}', '[', ']']):
                    players.append(clean_line)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Players - ZiLogo</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    .player-list {{ max-width: 800px; }}
                    .player-item {{
                        padding: 10px;
                        margin: 5px 0;
                        background: #f5f5f5;
                        border-left: 4px solid #007bff;
                        cursor: pointer;
                    }}
                    .player-item:hover {{ background: #e9ecef; }}
                    .nav-links {{ margin: 20px 0; }}
                    .nav-links a {{ margin-right: 15px; color: #007bff; }}
                </style>
            </head>
            <body>
                <h1>🏆 Players</h1>
                <div class="nav-links">
                    <a href="https://tournaments.zilogo.com">Tournaments</a>
                    <a href="https://admin.zilogo.com">Admin</a>
                </div>

                <div class="player-list">
                    {chr(10).join(f'<div class="player-item" onclick="alert(\'Player #{player[0]}: {player[1]} - {player[2]} pts\')">#<strong>{player[0]}</strong> - {player[1]} <span style="color: #666; font-size: 14px;">({player[2]} pts, {player[3]} tournaments)</span></div>' for player in players if isinstance(player, tuple) and len(player) >= 4)}
                </div>

                <p><em>Showing all players. Click on a player for details.</em></p>
            </body>
            </html>
            """

            self.wfile.write(html.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error loading players</h1><p>{e}</p>".encode())

    def handle_tournaments_service(self):
        """Handle tournaments.zilogo.com - show all tournaments"""
        try:
            # Get tournament data from database
            import sqlite3
            tournaments = []
            try:
                conn = sqlite3.connect('tournament_tracker.db')
                cursor = conn.cursor()
                cursor.execute("SELECT name, start_at, venue_name, num_attendees FROM tournaments WHERE name IS NOT NULL ORDER BY start_at DESC")
                tournaments = cursor.fetchall()
                conn.close()
            except Exception as e:
                tournaments = [("Database error", str(e), "", "")]

            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Tournaments - ZiLogo</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    .tournament-list {{ max-width: 800px; }}
                    .tournament-item {{
                        padding: 15px;
                        margin: 10px 0;
                        background: #f8f9fa;
                        border-left: 4px solid #28a745;
                        cursor: pointer;
                    }}
                    .tournament-item:hover {{ background: #e9ecef; }}
                    .tournament-name {{ font-weight: bold; font-size: 16px; }}
                    .tournament-details {{ color: #666; margin-top: 5px; }}
                    .nav-links {{ margin: 20px 0; }}
                    .nav-links a {{ margin-right: 15px; color: #007bff; }}
                </style>
            </head>
            <body>
                <h1>🎯 Tournaments</h1>
                <div class="nav-links">
                    <a href="https://players.zilogo.com">Players</a>
                    <a href="https://admin.zilogo.com">Admin</a>
                </div>

                <div class="tournament-list">"""

            for tournament in tournaments:
                name, start_at, venue_name, attendees = tournament
                safe_name = str(name).replace('"', '&quot;').replace("'", "&#39;") if name else "Unknown Tournament"
                location_str = str(venue_name) if venue_name else "Unknown Location"
                attendees_str = str(attendees) if attendees else "Unknown"

                # Convert timestamp to readable date
                if start_at:
                    from datetime import datetime
                    try:
                        date_str = datetime.fromtimestamp(start_at).strftime("%Y-%m-%d")
                    except:
                        date_str = str(start_at)
                else:
                    date_str = "Unknown Date"

                html += f"""
                    <div class="tournament-item" onclick="alert('Tournament details: {safe_name}')">
                        <div class="tournament-name">{safe_name}</div>
                        <div class="tournament-details">
                            📅 {date_str} | 📍 {location_str} | 👥 {attendees_str} attendees
                        </div>
                    </div>"""

            html += """
                </div>
                <p><em>Showing all tournaments. Click on a tournament for details.</em></p>
            </body>
            </html>
            """

            self.wfile.write(html.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error loading tournaments</h1><p>{e}</p>".encode())

    def handle_admin_service(self):
        """Handle admin.zilogo.com - show admin interface"""
        try:
            # Use go.py to get stats and status
            result = subprocess.run(['./go.py', '--stats'],
                                  capture_output=True, text=True, timeout=10)

            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = f"""
            <html>
            <head><title>Admin - ZiLogo</title></head>
            <body>
            <h1>⚙️ Admin Dashboard</h1>
            <h2>System Statistics</h2>
            <pre>{result.stdout}</pre>
            <hr>
            <p><a href="https://tournaments.zilogo.com">View Tournaments</a> | <a href="https://players.zilogo.com">View Players</a></p>
            </body>
            </html>
            """

            self.wfile.write(html.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error loading admin</h1><p>{e}</p>".encode())

    def handle_webdav_options(self):
        """Handle WebDAV OPTIONS request"""
        self.send_response(200)
        self.send_header('DAV', '1, 2')
        self.send_header('Allow', 'GET, HEAD, POST, PUT, DELETE, OPTIONS, PROPFIND, PROPPATCH, MKCOL, COPY, MOVE, LOCK, UNLOCK')
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'')

    def handle_webdav_request(self):
        """Handle WebDAV PROPFIND requests"""
        # Extract subdomain from Host header
        host = self.headers.get('Host', '')
        subdomain = None

        if '.zilogo.com' in host:
            subdomain = host.split('.zilogo.com')[0]

        if subdomain == 'players':
            self.handle_players_webdav()
        elif subdomain == 'tournaments':
            self.handle_tournaments_webdav()
        elif subdomain == 'orgs' or subdomain == 'organizations':
            self.handle_organizations_webdav()
        else:
            # Default WebDAV response for other subdomains
            self.send_response(404)
            self.end_headers()

    def handle_players_webdav(self):
        """Handle WebDAV for players.zilogo.com - present players as directory"""
        try:
            # Get player data from database (same as HTML version)
            import sqlite3
            players = []
            try:
                conn = sqlite3.connect('tournament_tracker.db')
                cursor = conn.cursor()
                # Get ALL players ranked by tournament performance
                cursor.execute("""
                    SELECT p.gamer_tag,
                           COUNT(tp.id) as tournament_count,
                           SUM(CASE WHEN tp.placement = 1 THEN 10
                                   WHEN tp.placement = 2 THEN 7
                                   WHEN tp.placement = 3 THEN 5
                                   WHEN tp.placement <= 8 THEN 3
                                   ELSE 1 END) as points
                    FROM players p
                    LEFT JOIN tournament_placements tp ON p.id = tp.player_id
                    WHERE p.gamer_tag IS NOT NULL
                    GROUP BY p.id, p.gamer_tag
                    ORDER BY points DESC, tournament_count DESC, p.gamer_tag
                """)
                players_data = cursor.fetchall()
                players = []
                for rank, (gamer_tag, tourney_count, points) in enumerate(players_data, 1):
                    points = points or 0
                    tourney_count = tourney_count or 0
                    players.append((rank, gamer_tag, points, tourney_count))
                conn.close()
            except Exception as e:
                import traceback
                error_msg = f"Database error: {e}\nTraceback: {traceback.format_exc()}"
                players = [(1, error_msg, 0, 0)]

            # Generate WebDAV XML response
            self.send_response(207, 'Multi-Status')
            self.send_header('Content-Type', 'application/xml; charset=utf-8')
            self.end_headers()

            # WebDAV XML response showing players as directory entries
            xml_response = '''<?xml version="1.0" encoding="utf-8"?>
<D:multistatus xmlns:D="DAV:">
    <D:response>
        <D:href>/</D:href>
        <D:propstat>
            <D:prop>
                <D:resourcetype><D:collection/></D:resourcetype>
                <D:displayname>Players</D:displayname>
            </D:prop>
            <D:status>HTTP/1.1 200 OK</D:status>
        </D:propstat>
    </D:response>'''

            # Add each player as a file entry
            for player in players:
                if isinstance(player, tuple) and len(player) >= 4:
                    rank, gamer_tag, points, tourney_count = player
                    safe_name = gamer_tag.replace('"', '&quot;').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                else:
                    safe_name = str(player).replace('"', '&quot;').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                xml_response += f'''
    <D:response>
        <D:href>/{safe_name}.txt</D:href>
        <D:propstat>
            <D:prop>
                <D:resourcetype/>
                <D:displayname>{safe_name}</D:displayname>
                <D:getcontenttype>text/plain</D:getcontenttype>
                <D:getcontentlength>100</D:getcontentlength>
            </D:prop>
            <D:status>HTTP/1.1 200 OK</D:status>
        </D:propstat>
    </D:response>'''

            xml_response += '\n</D:multistatus>'
            self.wfile.write(xml_response.encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"WebDAV error: {e}".encode())

    def handle_individual_player(self):
        """Handle requests for individual player files"""
        try:
            # Extract player name from path
            player_name = self.path[1:-4]  # Remove leading '/' and trailing '.txt'
            player_name = player_name.replace('%20', ' ')  # URL decode spaces

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()

            # Return player details
            content = f"Player: {player_name}\n"
            content += f"Profile: Details for {player_name}\n"
            content += f"Stats: Tournament history and rankings\n"
            content += f"Contact: Player contact information\n"

            self.wfile.write(content.encode('utf-8'))

        except Exception as e:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Player not found: {e}".encode())

    def handle_organizations_service(self):
        """Handle orgs.zilogo.com - show all organizations"""
        try:
            # Get organization data from database
            import sqlite3
            organizations = []
            try:
                conn = sqlite3.connect('tournament_tracker.db')
                cursor = conn.cursor()
                cursor.execute("SELECT display_name, contacts_json FROM organizations WHERE display_name IS NOT NULL ORDER BY display_name")
                organizations = cursor.fetchall()
                conn.close()
            except Exception as e:
                organizations = [("Database error", str(e))]

            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Organizations - ZiLogo</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #333; }}
                    .org-list {{ max-width: 800px; }}
                    .org-item {{
                        padding: 15px;
                        margin: 10px 0;
                        background: #f0f8ff;
                        border-left: 4px solid #6f42c1;
                        cursor: pointer;
                    }}
                    .org-item:hover {{ background: #e9ecef; }}
                    .org-name {{ font-weight: bold; font-size: 16px; }}
                    .org-details {{ color: #666; margin-top: 5px; }}
                    .nav-links {{ margin: 20px 0; }}
                    .nav-links a {{ margin-right: 15px; color: #007bff; }}
                </style>
            </head>
            <body>
                <h1>🏢 Organizations</h1>
                <div class="nav-links">
                    <a href="https://players.zilogo.com">Players</a>
                    <a href="https://tournaments.zilogo.com">Tournaments</a>
                    <a href="https://admin.zilogo.com">Admin</a>
                </div>

                <div class="org-list">"""

            for org in organizations:
                name, contacts_json = org
                safe_name = str(name).replace('"', '&quot;').replace("'", "&#39;") if name else "Unknown Organization"

                # Parse JSON contacts
                contact_str = "No contact info"
                try:
                    import json
                    contacts = json.loads(contacts_json) if contacts_json else []
                    if contacts:
                        contact_parts = []
                        for contact in contacts:
                            if isinstance(contact, dict):
                                contact_type = contact.get('type', 'contact')
                                contact_value = contact.get('value', '')
                                if contact_value:
                                    contact_parts.append(f"{contact_type}: {contact_value}")
                        contact_str = " | ".join(contact_parts) if contact_parts else "No contact info"
                except:
                    contact_str = str(contacts_json) if contacts_json else "No contact info"

                html += f"""
                    <div class="org-item" onclick="alert('Organization details: {safe_name}')">
                        <div class="org-name">{safe_name}</div>
                        <div class="org-details">
                            📧 {contact_str}
                        </div>
                    </div>"""

            html += """
                </div>
                <p><em>Showing all organizations. Click on an organization for details.</em></p>
            </body>
            </html>
            """

            self.wfile.write(html.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>Error loading organizations</h1><p>{e}</p>".encode())

    def handle_individual_tournament(self):
        """Handle requests for individual tournament files"""
        try:
            # Extract tournament name from path
            tournament_name = self.path[1:-4]  # Remove leading '/' and trailing '.txt'
            tournament_name = tournament_name.replace('%20', ' ')  # URL decode spaces

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()

            # Return tournament details
            content = f"Tournament: {tournament_name}\n"
            content += f"Details: Information for {tournament_name}\n"
            content += f"Schedule: Tournament schedule and brackets\n"
            content += f"Results: Tournament results and standings\n"

            self.wfile.write(content.encode('utf-8'))

        except Exception as e:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Tournament not found: {e}".encode())

    def handle_individual_org(self):
        """Handle requests for individual organization files"""
        try:
            # Extract org name from path
            org_name = self.path[1:-4]  # Remove leading '/' and trailing '.txt'
            org_name = org_name.replace('%20', ' ')  # URL decode spaces

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()

            # Return org details
            content = f"Organization: {org_name}\n"
            content += f"Profile: Details for {org_name}\n"
            content += f"Events: Tournaments organized by {org_name}\n"
            content += f"Contact: Organization contact information\n"

            self.wfile.write(content.encode('utf-8'))

        except Exception as e:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Organization not found: {e}".encode())

    def handle_tournaments_webdav(self):
        """Handle WebDAV for tournaments.zilogo.com - present tournaments as directory"""
        try:
            # Get tournament data from database (same as HTML version)
            import sqlite3
            tournaments = []
            try:
                conn = sqlite3.connect('tournament_tracker.db')
                cursor = conn.cursor()
                cursor.execute("SELECT name, start_at, venue_name, num_attendees FROM tournaments WHERE name IS NOT NULL ORDER BY start_at DESC")
                tournaments = cursor.fetchall()
                conn.close()
            except Exception as e:
                tournaments = [("Database error", str(e), "", "")]

            # Generate WebDAV XML response
            self.send_response(207, 'Multi-Status')
            self.send_header('Content-Type', 'application/xml; charset=utf-8')
            self.end_headers()

            # WebDAV XML response showing tournaments as directory entries
            xml_response = '''<?xml version="1.0" encoding="utf-8"?>
<D:multistatus xmlns:D="DAV:">
    <D:response>
        <D:href>/</D:href>
        <D:propstat>
            <D:prop>
                <D:resourcetype><D:collection/></D:resourcetype>
                <D:displayname>Tournaments</D:displayname>
            </D:prop>
            <D:status>HTTP/1.1 200 OK</D:status>
        </D:propstat>
    </D:response>'''

            # Add each tournament as a file entry
            for tournament in tournaments:
                name, start_at, venue_name, attendees = tournament
                safe_name = str(name).replace('"', '&quot;').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if name else "Unknown Tournament"
                xml_response += f'''
    <D:response>
        <D:href>/{safe_name}.txt</D:href>
        <D:propstat>
            <D:prop>
                <D:resourcetype/>
                <D:displayname>{safe_name}</D:displayname>
                <D:getcontenttype>text/plain</D:getcontenttype>
                <D:getcontentlength>200</D:getcontentlength>
            </D:prop>
            <D:status>HTTP/1.1 200 OK</D:status>
        </D:propstat>
    </D:response>'''

            xml_response += '\n</D:multistatus>'
            self.wfile.write(xml_response.encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"WebDAV error: {e}".encode())

    def handle_organizations_webdav(self):
        """Handle WebDAV for orgs.zilogo.com - present organizations as directory"""
        try:
            # Get organization data from database (same as HTML version)
            import sqlite3
            organizations = []
            try:
                conn = sqlite3.connect('tournament_tracker.db')
                cursor = conn.cursor()
                cursor.execute("SELECT display_name, contacts_json FROM organizations WHERE display_name IS NOT NULL ORDER BY display_name")
                organizations = cursor.fetchall()
                conn.close()
            except Exception as e:
                organizations = [("Database error", str(e))]

            # Generate WebDAV XML response
            self.send_response(207, 'Multi-Status')
            self.send_header('Content-Type', 'application/xml; charset=utf-8')
            self.end_headers()

            # WebDAV XML response showing organizations as directory entries
            xml_response = '''<?xml version="1.0" encoding="utf-8"?>
<D:multistatus xmlns:D="DAV:">
    <D:response>
        <D:href>/</D:href>
        <D:propstat>
            <D:prop>
                <D:resourcetype><D:collection/></D:resourcetype>
                <D:displayname>Organizations</D:displayname>
            </D:prop>
            <D:status>HTTP/1.1 200 OK</D:status>
        </D:propstat>
    </D:response>'''

            # Add each organization as a file entry
            for org in organizations:
                name, contact = org
                safe_name = str(name).replace('"', '&quot;').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') if name else "Unknown Organization"
                xml_response += f'''
    <D:response>
        <D:href>/{safe_name}.txt</D:href>
        <D:propstat>
            <D:prop>
                <D:resourcetype/>
                <D:displayname>{safe_name}</D:displayname>
                <D:getcontenttype>text/plain</D:getcontenttype>
                <D:getcontentlength>150</D:getcontentlength>
            </D:prop>
            <D:status>HTTP/1.1 200 OK</D:status>
        </D:propstat>
    </D:response>'''

            xml_response += '\n</D:multistatus>'
            self.wfile.write(xml_response.encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"WebDAV error: {e}".encode())

def run_server():
    server_address = ('127.0.0.1', 8000)
    httpd = HTTPServer(server_address, DynamicProxyHandler)
    print(f"🌐 Dynamic proxy server running on {server_address[0]}:{server_address[1]}")
    print("🔧 Handling *.zilogo.com routing via mDNS discovery")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()