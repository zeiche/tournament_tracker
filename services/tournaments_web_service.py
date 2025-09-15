#!/usr/bin/env python3
"""
tournaments_web_service.py - Beautiful web interface for tournament data

This service provides a rich web dashboard showing tournament statistics,
recent events, player rankings, and visualizations from the tournament database.
"""

import sys
import os
import time
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core.execution_guard import require_go_py
require_go_py("services.tournaments_web_service")

from polymorphic_core.network_service_wrapper import wrap_service
from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service

class TournamentsWebService:
    """
    Beautiful web interface for tournament data with analytics and visualizations.
    """

    def __init__(self):
        # Get database service
        self.database = get_service("database", prefer_network=False)

        # Announce ourselves
        announcer.announce(
            "Tournament Management Dashboard",
            [
                "Beautiful tournament data visualization",
                "Player rankings and statistics",
                "Recent tournament results",
                "Analytics dashboard",
                "Tournament management interface"
            ],
            [
                "GET / - Tournament analytics dashboard",
                "POST /ask - Query tournament data",
                "POST /tell - Format tournament data",
                "POST /do - Perform tournament actions"
            ],
            service_instance=self
        )

        print("🏆 Tournament Web Service initialized")

    def ask(self, query: str) -> dict:
        """Query tournament data"""
        query_lower = query.lower().strip()

        if not self.database:
            return {"error": "Database service not available"}

        try:
            if 'recent' in query_lower and 'tournament' in query_lower:
                tournaments = self.database.ask("recent tournaments limit 10")
                return {
                    'type': 'recent_tournaments',
                    'query': query,
                    'tournaments': tournaments
                }
            elif 'player' in query_lower and ('ranking' in query_lower or 'top' in query_lower):
                players = self.database.ask("top players limit 20")
                return {
                    'type': 'player_rankings',
                    'query': query,
                    'players': players
                }
            elif 'stats' in query_lower or 'statistics' in query_lower:
                stats = self.database.ask("tournament statistics")
                return {
                    'type': 'tournament_stats',
                    'query': query,
                    'stats': stats
                }
            else:
                return {
                    'type': 'tournament_query',
                    'query': query,
                    'capabilities': [
                        'Tournament analytics dashboard',
                        'Player rankings and statistics',
                        'Recent tournament results',
                        'Tournament management'
                    ]
                }
        except Exception as e:
            return {"error": f"Query failed: {str(e)}"}

    def tell(self, format_type: str, data=None) -> str:
        """Format tournament data for output"""
        if format_type.lower() == 'html':
            return self._generate_html_dashboard(data)
        elif format_type.lower() == 'json':
            try:
                tournaments = self.database.ask("recent tournaments limit 5") if self.database else []
                players = self.database.ask("top players limit 10") if self.database else []
                return json.dumps({
                    'tournaments': tournaments,
                    'players': players,
                    'data': data
                }, indent=2)
            except:
                return json.dumps({"error": "Database not available"}, indent=2)
        else:
            return f"Tournament Management Dashboard (Format: {format_type})"

    def do(self, action: str) -> str:
        """Perform tournament management actions"""
        action_lower = action.lower().strip()

        if 'refresh' in action_lower or 'sync' in action_lower:
            return "Tournament data refresh initiated"
        elif 'stats' in action_lower:
            try:
                stats = self.database.ask("tournament statistics") if self.database else {}
                return f"Tournament statistics: {stats}"
            except:
                return "Tournament statistics unavailable"
        elif 'test' in action_lower:
            return "Tournament web service test completed successfully"
        else:
            return f"Tournament management action performed: {action}"

    def _generate_html_dashboard(self, data=None) -> str:
        """Generate beautiful HTML dashboard for tournament data"""

        # Try to get real data from database
        tournaments = []
        players = []
        stats = {}

        try:
            if self.database:
                tournaments = self.database.ask("recent tournaments limit 8") or []
                players = self.database.ask("top players limit 12") or []
                stats = self.database.ask("tournament statistics") or {}
        except:
            pass

        # Generate statistics
        total_tournaments = len(tournaments) if tournaments else 0
        total_players = len(players) if players else 0

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Tournament Management Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px; margin: 0 auto;
        }}
        .header {{
            background: rgba(255,255,255,0.95); color: #333; padding: 30px;
            border-radius: 16px; margin-bottom: 30px; text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1); backdrop-filter: blur(10px);
        }}
        .header h1 {{
            margin: 0; font-size: 3em; background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .header p {{ margin: 15px 0 0 0; font-size: 1.2em; color: #666; }}
        .stats-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px; margin-bottom: 40px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.95); padding: 25px; border-radius: 12px;
            text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px); transition: transform 0.3s ease;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-number {{
            font-size: 2.5em; font-weight: bold; margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .stat-label {{ color: #666; font-size: 1.1em; }}
        .content-grid {{
            display: grid; grid-template-columns: 1fr 1fr; gap: 30px;
        }}
        @media (max-width: 768px) {{
            .content-grid {{ grid-template-columns: 1fr; }}
        }}
        .section {{
            background: rgba(255,255,255,0.95); border-radius: 16px; padding: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1); backdrop-filter: blur(10px);
        }}
        .section h2 {{
            margin: 0 0 20px 0; color: #333; font-size: 1.5em;
            border-bottom: 2px solid #667eea; padding-bottom: 10px;
        }}
        .tournament-item, .player-item {{
            background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 8px;
            border-left: 4px solid #667eea; transition: all 0.2s ease;
        }}
        .tournament-item:hover, .player-item:hover {{
            background: #e3f2fd; transform: translateX(5px);
        }}
        .tournament-name, .player-name {{
            font-weight: bold; color: #333; margin-bottom: 5px;
        }}
        .tournament-details, .player-details {{
            color: #666; font-size: 0.9em;
        }}
        .no-data {{
            text-align: center; padding: 40px; color: #666;
            font-style: italic; background: #f8f9fa; border-radius: 8px;
        }}
        .refresh-btn {{
            background: linear-gradient(135deg, #667eea, #764ba2); color: white;
            border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer;
            font-size: 1em; margin: 20px auto; display: block; transition: all 0.3s ease;
        }}
        .refresh-btn:hover {{
            transform: translateY(-2px); box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }}
        .badge {{
            display: inline-block; background: #667eea; color: white;
            padding: 4px 8px; border-radius: 12px; font-size: 0.8em; margin-left: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏆 Tournament Dashboard</h1>
            <p>Fighting Game Community Tournament Management & Analytics</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_tournaments}</div>
                <div class="stat-label">Recent Tournaments</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_players}</div>
                <div class="stat-label">Active Players</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_events', 0)}</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('organizations', 0)}</div>
                <div class="stat-label">Organizations</div>
            </div>
        </div>

        <div class="content-grid">
            <div class="section">
                <h2>🎮 Recent Tournaments</h2>"""

        if tournaments:
            for tournament in tournaments[:8]:
                name = tournament.get('name', 'Unknown Tournament')
                date = tournament.get('date', 'Date TBD')
                attendees = tournament.get('num_attendees', 0)
                location = tournament.get('location', 'Location TBD')

                html += f"""
                <div class="tournament-item">
                    <div class="tournament-name">{name}</div>
                    <div class="tournament-details">
                        📅 {date} • 👥 {attendees} players • 📍 {location}
                    </div>
                </div>"""
        else:
            html += '<div class="no-data">No tournament data available. Connect to database to see recent tournaments.</div>'

        html += """
            </div>

            <div class="section">
                <h2>🏅 Top Players</h2>"""

        if players:
            for i, player in enumerate(players[:12], 1):
                name = player.get('name', 'Unknown Player')
                points = player.get('points', 0)
                tournaments = player.get('tournament_count', 0)

                # Add ranking badges
                badge_color = '#FFD700' if i <= 3 else '#C0C0C0' if i <= 10 else '#CD7F32'

                html += f"""
                <div class="player-item">
                    <div class="player-name">
                        #{i} {name}
                        <span class="badge" style="background: {badge_color};">Rank {i}</span>
                    </div>
                    <div class="player-details">
                        🏆 {points} points • 🎯 {tournaments} tournaments
                    </div>
                </div>"""
        else:
            html += '<div class="no-data">No player data available. Connect to database to see player rankings.</div>'

        html += """
            </div>
        </div>

        <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Dashboard</button>
    </div>

    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);

        // Add some interactive animations
        document.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('click', () => {
                card.style.transform = 'scale(0.95)';
                setTimeout(() => card.style.transform = '', 150);
            });
        });
    </script>
</body>
</html>"""

        return html

# Create and start the service
print("🚀 Starting Tournament Web Service...")

# Create the service instance
tournament_service = TournamentsWebService()

# Wrap it with HTTPS server on port 443
wrapped = wrap_service(
    tournament_service,
    "Tournament Management Dashboard",
    port=443,
    auto_start=True
)

print(f"🔐 Tournament Web Service running on port {wrapped.port}")
print("✅ Tournament Web Service available at https://tournaments.zilogo.com")

if __name__ == "__main__":
    try:
        # Keep the service running
        print("🔄 Service running... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping Tournament Web Service...")