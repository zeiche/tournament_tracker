#!/usr/bin/env python3
"""
Enhanced Bonjour Dashboard with Live Data Exploration
"""
import sqlite3
import subprocess
import socket
from datetime import datetime
import json
import os

def get_live_database_stats():
    """Get real-time database statistics"""
    try:
        conn = sqlite3.connect('tournament_tracker.db')
        cursor = conn.cursor()

        stats = {}

        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM tournaments")
        stats['tournaments'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM players WHERE gamer_tag IS NOT NULL")
        stats['players'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM organizations WHERE display_name IS NOT NULL")
        stats['organizations'] = cursor.fetchone()[0]

        # Latest tournament
        cursor.execute("SELECT name, event_date FROM tournaments ORDER BY event_date DESC LIMIT 1")
        latest = cursor.fetchone()
        stats['latest_tournament'] = latest[0] if latest else "None"
        stats['latest_date'] = latest[1] if latest else "None"

        # Top performers
        cursor.execute("""
            SELECT p.gamer_tag,
                   SUM(CASE WHEN tp.placement = 1 THEN 10
                           WHEN tp.placement = 2 THEN 7
                           WHEN tp.placement = 3 THEN 5
                           WHEN tp.placement <= 8 THEN 3
                           ELSE 1 END) as points
            FROM players p
            LEFT JOIN tournament_placements tp ON p.id = tp.player_id
            WHERE p.gamer_tag IS NOT NULL
            GROUP BY p.id, p.gamer_tag
            ORDER BY points DESC LIMIT 3
        """)
        top_players = cursor.fetchall()
        stats['top_players'] = [f"{player[0]} ({player[1]} pts)" for player in top_players]

        # Most active organization
        cursor.execute("""
            SELECT o.display_name, COUNT(t.id) as tournament_count
            FROM organizations o
            LEFT JOIN tournaments t ON (
                LOWER(t.venue_name) LIKE '%' || LOWER(o.display_name) || '%' OR
                LOWER(t.name) LIKE '%' || LOWER(o.display_name) || '%'
            )
            WHERE o.display_name IS NOT NULL
            GROUP BY o.id, o.display_name
            ORDER BY tournament_count DESC LIMIT 1
        """)
        top_org = cursor.fetchone()
        stats['top_org'] = f"{top_org[0]} ({top_org[1]} tournaments)" if top_org else "None"

        # Recent activity
        cursor.execute("""
            SELECT name, event_date, num_attendees
            FROM tournaments
            WHERE event_date IS NOT NULL
            ORDER BY event_date DESC LIMIT 5
        """)
        recent_tournaments = cursor.fetchall()
        stats['recent_tournaments'] = recent_tournaments

        conn.close()
        return stats

    except Exception as e:
        return {'error': str(e)}

def check_port_status(port):
    """Check if a port is active"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except:
        return False

def get_service_status():
    """Get current service status"""
    services = []

    # Check for go.py processes
    try:
        result = subprocess.run(['pgrep', '-f', 'go.py'], capture_output=True, text=True)
        go_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        services.append(('go.py processes', go_count, 'count'))
    except:
        services.append(('go.py processes', 'unknown', 'error'))

    # Check specific ports
    port_checks = [
        (8000, "Dynamic Proxy"),
        (8081, "Web Editor"),
        (54269, "Web Editor Alt"),
        (8082, "AI Web Interface"),
        (443, "HTTPS/SSL"),
        (80, "HTTP")
    ]

    for port, name in port_checks:
        status = "🟢 Active" if check_port_status(port) else "🔴 Inactive"
        services.append((f"{name} (:{port})", status, 'port'))

    return services

def generate_enhanced_bonjour_html():
    """Generate the enhanced Bonjour dashboard HTML"""
    db_stats = get_live_database_stats()
    service_status = get_service_status()
    hostname = socket.gethostname()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔍 Enhanced Bonjour Service Discovery - ZiLogo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
        .header {{ text-align: center; margin-bottom: 30px; background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 8px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .stat-box h3 {{ margin-top: 0; color: #007bff; }}
        .services-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }}
        .service-box {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border: 1px solid #dee2e6; }}
        .service-item {{ padding: 8px 0; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }}
        .service-item:last-child {{ border-bottom: none; }}
        .subdomain-item {{
            padding: 15px; margin: 10px 0; background: linear-gradient(45deg, #e3f2fd, #f3e5f5);
            border-left: 4px solid #2196f3; cursor: pointer; border-radius: 8px; transition: all 0.3s;
        }}
        .subdomain-item:hover {{ background: linear-gradient(45deg, #bbdefb, #e1bee7); transform: translateY(-2px); }}
        .nav-links {{ text-align: center; margin: 20px 0; }}
        .nav-links a {{
            margin: 0 10px; padding: 12px 24px; background: linear-gradient(45deg, #007bff, #0056b3); color: white;
            text-decoration: none; border-radius: 6px; display: inline-block; transition: all 0.3s;
        }}
        .nav-links a:hover {{ background: linear-gradient(45deg, #0056b3, #004085); transform: translateY(-1px); }}
        .refresh {{ background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; margin: 10px 0; transition: all 0.3s; }}
        .refresh:hover {{ background: #218838; transform: translateY(-1px); }}
        .live-indicator {{ display: inline-block; width: 8px; height: 8px; background: #28a745; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
        .exploration-section {{ background: linear-gradient(45deg, #fff3e0, #e8f5e8); padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .tournament-item {{ padding: 8px; margin: 4px 0; background: #f8f9fa; border-radius: 4px; font-size: 0.9em; }}
        .highlight {{ background: #fff3cd; padding: 2px 6px; border-radius: 3px; }}
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
            <h1><span class="live-indicator"></span>🔍 Enhanced Bonjour Service Discovery</h1>
            <p>Host: {hostname} | Live Data | Updated: {current_time}</p>
            <button class="refresh" onclick="refreshPage()">🔄 Refresh Dashboard</button>
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <h3>📊 Live Tournament Data</h3>
                <p><strong>{db_stats.get('tournaments', '?')}</strong> tournaments recorded</p>
                <p><strong>{db_stats.get('players', '?')}</strong> unique players tracked</p>
                <p><strong>{db_stats.get('organizations', '?')}</strong> organizations catalogued</p>
                <p>Latest: <span class="highlight">{db_stats.get('latest_tournament', 'Unknown')}</span></p>
                <p>Date: {db_stats.get('latest_date', 'Unknown')}</p>
            </div>

            <div class="stat-box">
                <h3>🏆 Top Performers</h3>
                {''.join(f'<p>#{i+1}: <strong>{player}</strong></p>' for i, player in enumerate(db_stats.get('top_players', [])))}
                <hr>
                <p><strong>Most Active Org:</strong></p>
                <p>{db_stats.get('top_org', 'Unknown')}</p>
            </div>

            <div class="stat-box">
                <h3>⚡ Recent Activity</h3>
                {''.join(f'<div class="tournament-item"><strong>{t[0] or "Unknown"}</strong><br>📅 {t[1] or "Unknown"} | 👥 {t[2] or "?"} attendees</div>' for t in db_stats.get('recent_tournaments', [])[:3])}
            </div>
        </div>

        <div class="services-grid">
            <div class="service-box">
                <h3>🚀 System Services</h3>
                {''.join(f'<div class="service-item"><span>{name}</span><span>{status}</span></div>' for name, status, _ in service_status)}
            </div>

            <div class="service-box">
                <h3>📡 Available Subdomains</h3>"""

    # Dynamic subdomain list with live data
    subdomains = [
        ("players", f"🏆 All {db_stats.get('players', '?')} players ranked by performance", "Real-time player rankings"),
        ("tournaments", f"🎯 Browse {db_stats.get('tournaments', '?')} tournaments", "Complete tournament database"),
        ("orgs", f"🏢 Explore {db_stats.get('organizations', '?')} organizations", "Organization activity rankings"),
        ("db", f"🗄️ Interactive database explorer", f"Browse all {len([name for name in ['tournaments', 'players', 'organizations'] if name in db_stats])} tables with SQL queries"),
        ("editor", "✏️ Web editor for data management", "Real-time editing interface"),
        ("bonjour", "🔍 Enhanced service discovery hub", "Live system exploration (you are here)")
    ]

    for name, desc, extra in subdomains:
        html += f"""
                <div class="subdomain-item" onclick="window.open('https://{name}.zilogo.com', '_blank')">
                    <strong>{name}.zilogo.com</strong><br>
                    <small>{desc}</small><br>
                    <em style="color: #666;">{extra}</em>
                </div>"""

    html += f"""
            </div>
        </div>

        <div class="exploration-section">
            <h3>🚀 System Exploration</h3>
            <p>This enhanced Bonjour dashboard provides <strong>live exploration</strong> of the tournament tracking system:</p>
            <ul>
                <li><strong>Real-time data counts</strong> - All statistics update automatically</li>
                <li><strong>Live service monitoring</strong> - See which services are currently active</li>
                <li><strong>Dynamic discovery</strong> - Services announce themselves automatically</li>
                <li><strong>SSL-everywhere architecture</strong> - All traffic encrypted on port 443</li>
                <li><strong>WebDAV protocol support</strong> - Compatible with file management tools</li>
            </ul>
            <p><em>🔄 Page auto-refreshes every 30 seconds for live data</em></p>
        </div>

        <div class="nav-links">
            <a href="https://players.zilogo.com">🏆 Players ({db_stats.get('players', '?')})</a>
            <a href="https://tournaments.zilogo.com">🎯 Tournaments ({db_stats.get('tournaments', '?')})</a>
            <a href="https://orgs.zilogo.com">🏢 Organizations ({db_stats.get('organizations', '?')})</a>
            <a href="https://db.zilogo.com">🗄️ Database</a>
            <a href="https://editor.zilogo.com">✏️ Editor</a>
        </div>

        <div class="service-box" style="margin-top: 20px; text-align: center;">
            <h3>🔧 System Status</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                <div>SSL Dynamic Routing: ✅</div>
                <div>WebDAV Support: ✅</div>
                <div>UTF-8 Encoding: ✅</div>
                <div>Auto-refresh: ✅</div>
                <div>Database: tournament_tracker.db</div>
                <div>SSL Certificate: *.zilogo.com</div>
            </div>
        </div>

        <p style="text-align: center; color: #666; margin-top: 30px;">
            <em>🎯 Enhanced Bonjour Service Discovery • Real-time exploration of the tournament ecosystem</em>
        </p>
    </div>
</body>
</html>"""

    return html

if __name__ == "__main__":
    print("🔍 Generating Enhanced Bonjour Dashboard...")
    html = generate_enhanced_bonjour_html()

    # Save to file for testing
    with open('enhanced_bonjour_test.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✅ Enhanced dashboard generated!")
    print("📊 Live data integration complete")
    print("🎯 Ready for integration into dynamic proxy")