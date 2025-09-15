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
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = f"""<!DOCTYPE html>
<html>
<head>
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
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = f"""<!DOCTYPE html>
<html>
<head>
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
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = f"""<!DOCTYPE html>
<html>
<head>
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

    def send_404(self):
        self.send_response(404)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>404 Not Found</h1>")

if __name__ == '__main__':
    server = http.server.HTTPServer(('', 8000), DynamicProxyHandler)
    print("Starting clean dynamic proxy server on port 8000...")
    server.serve_forever()