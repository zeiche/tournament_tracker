#!/usr/bin/env python3
import http.server
import sqlite3
import json
import urllib.parse

class DynamicProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.headers.get('Host', '')
        subdomain = host.split('.')[0] if '.' in host else ''

        if subdomain == 'players':
            self.handle_players()
        elif subdomain == 'tournaments':
            self.handle_tournaments()
        elif subdomain == 'orgs' or subdomain == 'organizations':
            self.handle_organizations()
        elif subdomain == 'bonjour':
            self.handle_bonjour()
        elif subdomain == 'db' or subdomain == 'database':
            self.handle_database()
        elif subdomain == 'editor':
            if not self.check_service_port(8081):
                self.start_subprocess(['python3', 'functional_web_editor.py'], "Advanced Web Editor")
            self.handle_editor()
        else:
            self.send_404()

    def do_POST(self):
        host = self.headers.get('Host', '')
        subdomain = host.split('.')[0] if '.' in host else ''

        if subdomain == 'editor':
            self.handle_editor()
        else:
            self.send_404()

    def do_PROPFIND(self):
        self.do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('DAV', '1')
        self.send_header('Allow', 'GET, PROPFIND, OPTIONS')
        self.end_headers()

    def handle_players(self):
        """Show ALL players ranked #1 to last"""
        try:
            conn = sqlite3.connect('tournament_tracker.db')
            cursor = conn.cursor()
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

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Players - ZiLogo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .player-list {{ max-width: 800px; }}
        .player-item {{
            padding: 10px; margin: 5px 0; background: #f5f5f5;
            border-left: 4px solid #007bff; cursor: pointer;
        }}
        .player-item:hover {{ background: #e9ecef; }}
        .nav-links {{ margin: 20px 0; }}
        .nav-links a {{ margin-right: 15px; color: #007bff; }}
    </style>
</head>
<body>
    <h1>🏆 Players Ranked #1 to #{len(players)}</h1>
    <div class="nav-links">
        <a href="https://tournaments.zilogo.com">Tournaments</a>
        <a href="https://orgs.zilogo.com">Organizations</a>
    </div>
    <div class="player-list">
        {chr(10).join(f'<div class="player-item"><strong>#{player[0]}</strong> - {player[1]} <span style="color: #666;">({player[2]} pts, {player[3]} tournaments)</span></div>' for player in players)}
    </div>
    <p><em>Showing ALL {len(players)} players ranked by tournament performance.</em></p>
</body>
</html>"""
            self.wfile.write(html.encode())
        except Exception as e:
            self.send_error(500, f"Database error: {e}")

    def handle_tournaments(self):
        """Show all tournaments"""
        try:
            conn = sqlite3.connect('tournament_tracker.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, start_at, venue_name, num_attendees FROM tournaments WHERE name IS NOT NULL ORDER BY start_at DESC")
            tournaments = cursor.fetchall()
            conn.close()

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tournaments - ZiLogo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .tournament-item {{ padding: 15px; margin: 10px 0; background: #f8f9fa; border-left: 4px solid #28a745; }}
        .nav-links {{ margin: 20px 0; }}
        .nav-links a {{ margin-right: 15px; color: #007bff; }}
    </style>
</head>
<body>
    <h1>🎯 Tournaments</h1>
    <div class="nav-links">
        <a href="https://players.zilogo.com">Players</a>
        <a href="https://orgs.zilogo.com">Organizations</a>
    </div>
    <div>
        {chr(10).join(f'<div class="tournament-item"><strong>{t[0] or "Unknown"}</strong><br>📅 {t[1] or "Unknown Date"} | 📍 {t[2] or "Unknown Location"} | 👥 {t[3] or 0} attendees</div>' for t in tournaments)}
    </div>
    <p><em>Showing {len(tournaments)} tournaments.</em></p>
</body>
</html>"""
            self.wfile.write(html.encode())
        except Exception as e:
            self.send_error(500, f"Database error: {e}")

    def handle_organizations(self):
        """Show ALL organizations ranked by activity"""
        try:
            conn = sqlite3.connect('tournament_tracker.db')
            cursor = conn.cursor()

            # Rank organizations by total activity (number of tournaments they appear in venue names)
            cursor.execute("""
                SELECT o.display_name, o.contacts_json,
                       COUNT(t.id) as tournament_count,
                       COALESCE(SUM(t.num_attendees), 0) as total_attendance
                FROM organizations o
                LEFT JOIN tournaments t ON (
                    LOWER(t.venue_name) LIKE '%' || LOWER(o.display_name) || '%' OR
                    LOWER(t.name) LIKE '%' || LOWER(o.display_name) || '%'
                )
                WHERE o.display_name IS NOT NULL
                GROUP BY o.id, o.display_name, o.contacts_json
                ORDER BY tournament_count DESC, total_attendance DESC, o.display_name
            """)
            orgs_data = cursor.fetchall()
            orgs = []
            for rank, (name, contacts, tourney_count, attendance) in enumerate(orgs_data, 1):
                orgs.append((rank, name, contacts, tourney_count or 0, attendance or 0))
            conn.close()

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Organizations - ZiLogo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .org-item {{ padding: 15px; margin: 10px 0; background: #f0f8ff; border-left: 4px solid #6f42c1; cursor: pointer; }}
        .org-item:hover {{ background: #e9ecef; }}
        .nav-links {{ margin: 20px 0; }}
        .nav-links a {{ margin-right: 15px; color: #007bff; }}
    </style>
</head>
<body>
    <h1>🏢 Organizations Ranked #1 to #{len(orgs)}</h1>
    <div class="nav-links">
        <a href="https://players.zilogo.com">Players</a>
        <a href="https://tournaments.zilogo.com">Tournaments</a>
    </div>
    <div>
        {chr(10).join(f'<div class="org-item"><strong>#{org[0]}</strong> - {org[1]} <span style="color: #666;">({org[3]} tournaments, {org[4]} total attendance)</span><br>📧 {self.format_contacts(org[2])}</div>' for org in orgs)}
    </div>
    <p><em>Showing ALL {len(orgs)} organizations ranked by tournament activity.</em></p>
</body>
</html>"""
            self.wfile.write(html.encode())
        except Exception as e:
            self.send_error(500, f"Database error: {e}")

    def handle_bonjour(self):
        """Show enhanced Bonjour service discovery dashboard"""
        try:
            # Import the enhanced bonjour module
            import enhanced_bonjour

            # Generate the enhanced HTML
            html = enhanced_bonjour.generate_enhanced_bonjour_html()

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode())
            return

            # Check running services
            services = []

            # Check for running go.py services
            try:
                result = subprocess.run(['pgrep', '-f', 'go.py'], capture_output=True, text=True)
                go_processes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                services.append(f"go.py processes: {go_processes}")
            except:
                services.append("go.py processes: unknown")

            # Check for specific ports
            service_ports = [
                (8000, "Dynamic Proxy"),
                (54269, "Web Editor"),
                (8082, "AI Web Interface"),
                (443, "HTTPS/SSL"),
                (80, "HTTP")
            ]

            for port, name in service_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    status = "🟢 Active" if result == 0 else "🔴 Inactive"
                    services.append(f"{name} (:{port}): {status}")
                except:
                    services.append(f"{name} (:{port}): 🔴 Error")

            # Available subdomains
            subdomains = [
                ("players", "All players ranked #1-242 by tournament performance"),
                ("tournaments", "Complete tournament listing with dates and venues"),
                ("orgs", "Organizations ranked by tournament activity"),
                ("editor", "Web editor for managing organizations and contacts"),
                ("bonjour", "Service discovery dashboard (you are here)")
            ]

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()

            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bonjour Service Discovery - ZiLogo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f8f9fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .services-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .service-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .service-item {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .service-item:last-child {{ border-bottom: none; }}
        .subdomain-item {{
            padding: 15px; margin: 10px 0; background: #e3f2fd;
            border-left: 4px solid #2196f3; cursor: pointer; border-radius: 4px;
        }}
        .subdomain-item:hover {{ background: #bbdefb; }}
        .nav-links {{ text-align: center; margin: 20px 0; }}
        .nav-links a {{
            margin: 0 10px; padding: 10px 20px; background: #007bff; color: white;
            text-decoration: none; border-radius: 4px; display: inline-block;
        }}
        .nav-links a:hover {{ background: #0056b3; }}
        .status {{ font-size: 0.9em; color: #666; }}
        .refresh {{
            background: #28a745; color: white; padding: 8px 16px;
            border: none; border-radius: 4px; cursor: pointer; margin: 10px 0;
        }}
        .refresh:hover {{ background: #218838; }}
    </style>
    <script>
        function refreshPage() {{ window.location.reload(); }}
        // Auto-refresh every 30 seconds
        setTimeout(refreshPage, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Bonjour Service Discovery</h1>
            <p class="status">Host: {hostname} | Updated: {current_time}</p>
            <button class="refresh" onclick="refreshPage()">🔄 Refresh Services</button>
        </div>

        <div class="services-grid">
            <div class="service-box">
                <h3>🚀 Active Services</h3>
                {chr(10).join(f'<div class="service-item">{service}</div>' for service in services)}
            </div>

            <div class="service-box">
                <h3>📡 Available Subdomains</h3>
                {chr(10).join(f'<div class="subdomain-item" onclick="window.open(\'https://{sub}.zilogo.com\', \'_blank\')"><strong>{sub}.zilogo.com</strong><br><small>{desc}</small></div>' for sub, desc in subdomains)}
            </div>
        </div>

        <div class="nav-links">
            <a href="https://players.zilogo.com">🏆 Players</a>
            <a href="https://tournaments.zilogo.com">🎯 Tournaments</a>
            <a href="https://orgs.zilogo.com">🏢 Organizations</a>
            <a href="https://editor.zilogo.com">✏️ Editor</a>
        </div>

        <div class="service-box">
            <h3>🔧 System Information</h3>
            <div class="service-item">SSL Dynamic Routing: ✅ Active</div>
            <div class="service-item">WebDAV Support: ✅ Enabled</div>
            <div class="service-item">UTF-8 Encoding: ✅ System-wide</div>
            <div class="service-item">Database: tournament_tracker.db</div>
            <div class="service-item">Auto-refresh: Every 30 seconds</div>
        </div>

        <p style="text-align: center; color: #666; margin-top: 30px;">
            <em>This page automatically refreshes every 30 seconds to show current service status.</em>
        </p>
    </div>
</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Service discovery error: {e}")

    def discover_editor_port(self):
        """Dynamically discover web editor service port"""
        import socket
        import subprocess

        # Try to discover via Bonjour first
        try:
            result = subprocess.run(['./go.py', '--service-status'],
                                  capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if 'NextService_WebEditor' in line and ' at 10.0.0.1:' in line:
                    port = line.split(' at 10.0.0.1:')[1].strip()
                    return int(port)
        except:
            pass

        # Fallback: scan common ports for web editor
        editor_ports = [8081, 8082, 54269, 38317, 42951, 57975]
        for port in editor_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('10.0.0.1', port))
                sock.close()
                if result == 0:
                    # Test if it's actually a web service
                    try:
                        import urllib.request
                        urllib.request.urlopen(f'http://10.0.0.1:{port}/', timeout=2)
                        return port
                    except:
                        pass
            except:
                pass
        return None

    def send_editor_offline(self):
        """Send editor offline page"""
        self.send_response(500)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Web Editor Offline - ZiLogo</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               margin: 0; padding: 40px; background: #1a1a1a; color: #fff; }
        .error-box { background: #2d1b69; padding: 30px; border-radius: 10px;
                     border-left: 5px solid #ff6b6b; max-width: 600px; margin: 0 auto; }
        h1 { color: #ff6b6b; margin-top: 0; }
        code { background: #000; padding: 5px 10px; border-radius: 5px; }
        .nav-links a { color: #4ecdc4; text-decoration: none; margin: 0 15px; font-size: 18px; }
        .nav-links a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="error-box">
        <h1>⚠️ Web Editor Offline</h1>
        <p>The web editor service could not be discovered dynamically.</p>
        <p>To start the web editor:</p>
        <code>./go.py --edit-contacts</code>
        <br><br>
        <div class="nav-links">
            <a href="https://players.zilogo.com">🏆 Players</a>
            <a href="https://tournaments.zilogo.com">🎯 Tournaments</a>
            <a href="https://orgs.zilogo.com">🏢 Organizations</a>
            <a href="https://bonjour.zilogo.com">🔍 Services</a>
        </div>
    </div>
</body>
</html>"""
        self.wfile.write(html.encode())

    def handle_editor(self):
        """Proxy requests to web editor (dynamically discovered)"""
        try:
            import urllib.request
            import urllib.parse

            # Get request body for POST requests
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length else None

            # Build target URL
            # Discover editor port dynamically
            editor_port = self.discover_editor_port()
            if not editor_port:
                self.send_editor_offline()
                return

            target_url = f"http://10.0.0.1:{editor_port}{self.path}"

            # Create request
            if self.command == 'POST' and post_data:
                req = urllib.request.Request(target_url, data=post_data, method='POST')
            else:
                req = urllib.request.Request(target_url, method=self.command)

            # Copy headers (except Host)
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'content-length']:
                    req.add_header(header, value)

            # Make request to web editor
            try:
                with urllib.request.urlopen(req) as response:
                    # Copy response
                    self.send_response(response.getcode())

                    # Copy response headers
                    for header, value in response.headers.items():
                        self.send_header(header, value)
                    self.end_headers()

                    # Copy response body
                    self.wfile.write(response.read())

            except urllib.error.URLError:
                # Web editor not running, show helpful message
                self.send_response(503)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()

                html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Web Editor Offline - ZiLogo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
        .error-box { background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; max-width: 600px; margin: 0 auto; }
        .start-btn { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 10px; }
        .nav-links a { margin: 0 10px; color: #007bff; }
    </style>
</head>
<body>
    <div class="error-box">
        <h1>⚠️ Web Editor Offline</h1>
        <p>The web editor service could not be discovered dynamically.</p>
        <p>To start the web editor:</p>
        <code>./go.py --edit-contacts</code>
        <br><br>
        <div class="nav-links">
            <a href="https://players.zilogo.com">🏆 Players</a>
            <a href="https://tournaments.zilogo.com">🎯 Tournaments</a>
            <a href="https://orgs.zilogo.com">🏢 Organizations</a>
            <a href="https://bonjour.zilogo.com">🔍 Services</a>
        </div>
    </div>
</body>
</html>"""
                self.wfile.write(html.encode('utf-8'))

        except Exception as e:
            self.send_error(500, f"Editor proxy error: {e}")

    def format_contacts(self, contacts_json):
        """Format contact JSON for display"""
        try:
            if not contacts_json:
                return "No contact info"
            contacts = json.loads(contacts_json)
            if not contacts:
                return "No contact info"
            parts = []
            for contact in contacts:
                if isinstance(contact, dict):
                    contact_type = contact.get('type', 'contact')
                    contact_value = contact.get('value', '')
                    if contact_value:
                        parts.append(f"{contact_type}: {contact_value}")
            return " | ".join(parts) if parts else "No contact info"
        except:
            return str(contacts_json) if contacts_json else "No contact info"

    def handle_database(self):
        """Show interactive database explorer"""
        try:
            # Import the database viewer module
            import database_web_viewer
            from urllib.parse import parse_qs, urlparse

            # Parse query parameters
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            table_name = params.get('table', [None])[0]
            query = params.get('query', [None])[0]
            offset = int(params.get('offset', [0])[0])

            # Generate the database explorer HTML
            html = database_web_viewer.generate_database_explorer_html(
                table_name=table_name,
                query=query,
                offset=offset
            )

            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode())

        except Exception as e:
            self.send_error(500, f"Database explorer error: {e}")

    def send_404(self):
        self.send_response(404)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("<!DOCTYPE html><html><head><meta charset='UTF-8'></head><body><h1>404 Not Found</h1></body></html>".encode('utf-8'))

if __name__ == '__main__':
    server = http.server.HTTPServer(('', 8000), DynamicProxyHandler)
    print("Starting clean dynamic proxy server on port 8000...")
    server.serve_forever()