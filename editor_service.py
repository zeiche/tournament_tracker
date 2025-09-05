"""
editor_service.py - Single Source of Truth for Web Editor
Consolidates editor.py, editor_core.py, editor_web.py into one Pythonic service
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import os
import subprocess
from aiohttp import web
from datetime import datetime

from database import session_scope
from database_service import database_service
from log_manager import LogManager


class EditorMode(Enum):
    """Editor operation modes"""
    VIEW_ONLY = "view"
    EDIT_NAMES = "names"
    MANAGE_CONTACTS = "contacts"
    MERGE_ORGS = "merge"
    FULL = "full"


@dataclass
class EditorConfig:
    """Configuration for editor service"""
    port: int = 8081
    host: str = '0.0.0.0'
    mode: EditorMode = EditorMode.FULL
    auto_open: bool = True
    debug: bool = False


class EditorService:
    """Unified web editor service for tournament management"""
    
    _instance: Optional['EditorService'] = None
    
    def __new__(cls) -> 'EditorService':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[EditorConfig] = None):
        """Initialize editor service"""
        if not self._initialized:
            self.config = config or EditorConfig()
            self.logger = LogManager().get_logger('editor')
            self.app: Optional[web.Application] = None
            self.runner: Optional[web.AppRunner] = None
            self._initialized = True
    
    def create_app(self) -> web.Application:
        """Create web application"""
        app = web.Application()
        
        # Template routes
        app.router.add_get('/', self.index_handler)
        app.router.add_get('/organizations', self.organizations_handler)
        app.router.add_get('/org-rankings', self.org_rankings_handler)
        app.router.add_get('/tournaments', self.tournaments_handler)
        app.router.add_get('/report', self.report_handler)
        app.router.add_get('/heatmap', self.heatmap_handler)
        app.router.add_get('/charts', self.charts_handler)
        app.router.add_get('/players', self.players_handler)
        app.router.add_get('/player/{player_id}', self.player_detail_handler)
        app.router.add_get('/tournament/{tournament_id}', self.tournament_detail_handler)
        app.router.add_get('/standings', self.standings_handler)
        app.router.add_get('/discord-config', self.discord_config_handler)
        app.router.add_get('/export', self.export_handler)
        app.router.add_get('/sync-status', self.sync_status_handler)
        
        # API routes
        app.router.add_get('/api/stats', self.get_stats)
        app.router.add_get('/api/services', self.get_services)
        app.router.add_get('/api/tournaments', self.get_tournaments)
        app.router.add_get('/api/organizations', self.get_organizations)
        app.router.add_get('/api/players', self.get_players)
        app.router.add_get('/api/attendance-timeline', self.get_attendance_timeline)
        app.router.add_post('/api/organizations/{org_id}/update', self.update_organization)
        app.router.add_post('/api/organizations/merge', self.merge_organizations)
        app.router.add_post('/api/sync', self.start_sync)
        app.router.add_post('/api/publish/shopify', self.publish_shopify)
        
        self.app = app
        return app
    
    def _load_template(self, template_name: str) -> str:
        """Load HTML template from file"""
        template_path = os.path.join(
            os.path.dirname(__file__), 
            'templates', 
            template_name
        )
        try:
            with open(template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            self.logger.error(f"Template not found: {template_path}")
            return f"<h1>Template not found: {template_name}</h1>"
    
    async def index_handler(self, request):
        """Serve the main home page"""
        html = self._load_template('index.html')
        return web.Response(text=html, content_type='text/html')
    
    async def organizations_handler(self, request):
        """Serve the organizations page"""
        html = self._load_template('organizations.html')
        return web.Response(text=html, content_type='text/html')
    
    async def org_rankings_handler(self, request):
        """Serve organization rankings page"""
        from database import get_session
        from tournament_models import Tournament, Organization
        from sqlalchemy import func
        import html as html_module
        
        with get_session() as session:
            # Get all tournaments and map them to organizations
            tournaments = session.query(Tournament).all()
            
            # Build organization stats by checking each tournament's organization
            org_aggregated = {}
            
            # Get all organizations and build a contact map
            organizations = session.query(Organization).all()
            contact_to_org = {}
            
            # Build a map of normalized contacts to organization names
            from tournament_models import normalize_contact
            for org in organizations:
                for contact in org.contacts:
                    contact_value = contact.get('value', '')
                    if contact_value:
                        normalized = normalize_contact(contact_value)
                        if normalized:
                            contact_to_org[normalized] = org.display_name
            
            for tournament in tournaments:
                # Try to match tournament to organization via contact
                org_name = None
                
                if tournament.primary_contact:
                    normalized = normalize_contact(tournament.primary_contact)
                    if normalized in contact_to_org:
                        org_name = contact_to_org[normalized]
                
                if not org_name:
                    # Fall back to owner_name if no organization found
                    org_name = tournament.owner_name or "Unknown"
                
                # Aggregate stats by organization name
                if org_name not in org_aggregated:
                    org_aggregated[org_name] = {
                        'tournament_count': 0,
                        'total_attendees': 0
                    }
                org_aggregated[org_name]['tournament_count'] += 1
                org_aggregated[org_name]['total_attendees'] += (tournament.num_attendees or 0)
            
            # Sort by total attendees (total players)
            sorted_orgs = sorted(org_aggregated.items(), 
                               key=lambda x: x[1]['total_attendees'], 
                               reverse=True)
            
            # Build rankings table
            rankings_html = ""
            rank = 1
            for org_name, stats in sorted_orgs:
                tournament_count = stats['tournament_count']
                total_attendees = stats['total_attendees']
                avg_attendees = int(total_attendees / tournament_count) if tournament_count > 0 else 0
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}"
                rankings_html += f"""
                <tr>
                    <td>{medal}</td>
                    <td>{html_module.escape(org_name)}</td>
                    <td>{tournament_count}</td>
                    <td>{total_attendees:,}</td>
                    <td>{avg_attendees}</td>
                </tr>"""
                rank += 1
        
        # Create the page HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Organization Rankings</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .navbar {{
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }}
        .navbar a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 1rem;
            font-weight: 500;
        }}
        header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: center;
        }}
        h1 {{
            color: #2c3e50;
            margin: 0;
        }}
        .subtitle {{
            color: #7f8c8d;
            margin-top: 0.5rem;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            padding: 2rem;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <nav class="navbar">
            <a href="/">← Home</a>
            <a href="/organizations">Organizations</a>
            <a href="/tournaments">Tournaments</a>
            <a href="/report">Reports</a>
        </nav>
        
        <header>
            <h1>🏆 Organization Rankings</h1>
            <p class="subtitle">Tournament organizers ranked by activity</p>
        </header>
        
        <div class="card">
            <h3>Top Tournament Organizers</h3>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Organizer</th>
                        <th>Tournaments</th>
                        <th>Total Players</th>
                        <th>Avg Players</th>
                    </tr>
                </thead>
                <tbody>
                    {rankings_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
        return web.Response(text=html, content_type='text/html')
    
    async def tournaments_handler(self, request):
        """Serve the tournaments page"""
        html = self._load_template('tournaments.html')
        return web.Response(text=html, content_type='text/html')
    
    async def report_handler(self, request):
        """Serve the report page with actual tournament data"""
        from database_service import database_service
        import html as html_module
        
        # Get stats and rankings
        stats = database_service.get_summary_stats()
        rankings = database_service.get_attendance_rankings(limit=20)
        
        # Build rankings table
        rankings_html = ""
        for i, org in enumerate(rankings, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}"
            rankings_html += f"""
            <tr>
                <td>{medal}</td>
                <td>{html_module.escape(org['display_name'])}</td>
                <td>{org['tournament_count']}</td>
                <td>{org['total_attendance']:,}</td>
                <td>{org['avg_attendance']:.0f}</td>
            </tr>"""
        
        # Get recent tournaments
        from database import session_scope
        from tournament_models import Tournament
        with session_scope() as session:
            recent_tournaments = session.query(Tournament)\
                .order_by(Tournament.start_at.desc())\
                .limit(10).all()
            
            recent_html = ""
            for t in recent_tournaments:
                date_str = t.start_date.strftime('%Y-%m-%d') if t.start_date else 'N/A'
                recent_html += f"""
                <tr>
                    <td>{html_module.escape(t.name)}</td>
                    <td>{date_str}</td>
                    <td>{t.num_attendees or 0}</td>
                    <td>{html_module.escape(t.venue_name or 'N/A')}</td>
                </tr>"""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reports - Tournament Tracker</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; padding: 0; margin: 0; background: #f5f5f5; }}
                .navbar {{ background: #2c3e50; color: white; padding: 1rem 2rem; }}
                .navbar a {{ color: white; text-decoration: none; margin-right: 2rem; }}
                .navbar a:hover {{ opacity: 0.8; }}
                .container {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 2rem 0; }}
                .stat-card {{ background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat-card h3 {{ margin: 0 0 0.5rem 0; color: #666; font-size: 0.9rem; text-transform: uppercase; }}
                .stat-card .value {{ font-size: 2rem; font-weight: bold; color: #2c3e50; }}
                table {{ width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                th {{ background: #34495e; color: white; padding: 1rem; text-align: left; }}
                td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #eee; }}
                tr:hover {{ background: #f9f9f9; }}
                .section {{ margin: 3rem 0; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; margin-top: 2rem; }}
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
                <a href="/organizations">Organizations</a>
                <a href="/tournaments">Tournaments</a>
                <a href="/report">Reports</a>
                <a href="/standings">Standings</a>
            </nav>
            <div class="container">
                <h1>Tournament Reports & Analytics</h1>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Tournaments</h3>
                        <div class="value">{stats.total_tournaments}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Organizations</h3>
                        <div class="value">{stats.total_organizations}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Players Tracked</h3>
                        <div class="value">{stats.total_players}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Total Placements</h3>
                        <div class="value">{stats.total_placements:,}</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>Top Organizations by Attendance</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Organization</th>
                                <th>Events</th>
                                <th>Total Attendance</th>
                                <th>Avg Attendance</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rankings_html}
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>Recent Tournaments</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Tournament</th>
                                <th>Date</th>
                                <th>Attendees</th>
                                <th>Venue</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recent_html}
                        </tbody>
                    </table>
                </div>
                
                <div class="section" style="text-align: center; padding: 2rem; color: #666;">
                    <p>Generate detailed reports: <code>./go.py --html report.html</code></p>
                    <p>View console report: <code>./go.py --console</code></p>
                </div>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def heatmap_handler(self, request):
        """Serve the heatmap page or the actual heatmap file"""
        import os
        from pathlib import Path
        
        # Check if request is for the raw heatmap (for iframe)
        if request.query.get('raw') == 'true':
            heatmap_file = Path("tournament_heatmap.html")
            if heatmap_file.exists():
                with open(heatmap_file, 'r') as f:
                    html = f.read()
                return web.Response(text=html, content_type='text/html')
        
        # Check if we have a generated heatmap file
        heatmap_file = Path("tournament_heatmap.html")
        
        if heatmap_file.exists():
            # Embed the heatmap in an iframe with proper page structure
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Heat Maps - Tournament Tracker</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                    }
                    .container {
                        max-width: 1400px;
                        margin: 0 auto;
                    }
                    h1 {
                        color: white;
                        text-align: center;
                        margin-bottom: 10px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }
                    .description {
                        color: white;
                        text-align: center;
                        margin-bottom: 30px;
                        opacity: 0.9;
                    }
                    .map-container {
                        background: white;
                        border-radius: 10px;
                        padding: 20px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        margin-bottom: 30px;
                    }
                    .map-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 15px;
                        padding: 0 10px;
                    }
                    .map-title {
                        font-size: 1.2em;
                        font-weight: 600;
                        color: #333;
                    }
                    .map-controls {
                        display: flex;
                        gap: 10px;
                    }
                    .control-btn {
                        padding: 8px 15px;
                        background: #667eea;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        text-decoration: none;
                        font-size: 0.9em;
                        transition: all 0.3s ease;
                    }
                    .control-btn:hover {
                        background: #5a67d8;
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                    }
                    #heatmap-iframe {
                        width: 100%;
                        height: 600px;
                        border: none;
                        border-radius: 5px;
                    }
                    .other-reports {
                        background: white;
                        border-radius: 10px;
                        padding: 20px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        margin-bottom: 30px;
                    }
                    .reports-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 20px;
                        margin-top: 20px;
                    }
                    .report-card {
                        padding: 20px;
                        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        border-radius: 8px;
                        text-decoration: none;
                        color: #333;
                        transition: all 0.3s ease;
                    }
                    .report-card:hover {
                        transform: translateY(-5px);
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }
                    .report-icon {
                        font-size: 2em;
                        margin-bottom: 10px;
                    }
                    .report-title {
                        font-weight: 600;
                        margin-bottom: 5px;
                    }
                    .report-desc {
                        font-size: 0.9em;
                        opacity: 0.8;
                    }
                    .fullscreen-btn {
                        background: #48bb78;
                    }
                    .fullscreen-btn:hover {
                        background: #38a169;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🗺️ Tournament Heat Maps</h1>
                    <p class="description">Interactive visualization of tournament locations and density across Southern California</p>
                    
                    <div class="map-container">
                        <div class="map-header">
                            <div class="map-title">📍 Tournament Locations Heatmap</div>
                            <div class="map-controls">
                                <button class="control-btn fullscreen-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
                                <a href="/heatmap?raw=true" target="_blank" class="control-btn">↗️ Open in New Tab</a>
                                <button class="control-btn" onclick="location.reload()">🔄 Refresh</button>
                            </div>
                        </div>
                        <iframe id="heatmap-iframe" src="/heatmap?raw=true"></iframe>
                    </div>
                    
                    <div class="other-reports">
                        <h2>📊 Other Reports & Analytics</h2>
                        <div class="reports-grid">
                            <a href="/charts" class="report-card">
                                <div class="report-icon">📈</div>
                                <div class="report-title">Attendance Charts</div>
                                <div class="report-desc">Interactive charts showing attendance over time</div>
                            </a>
                            <a href="/report" class="report-card">
                                <div class="report-icon">📋</div>
                                <div class="report-title">Tournament Report</div>
                                <div class="report-desc">View detailed tournament statistics and rankings</div>
                            </a>
                            <a href="/" class="report-card">
                                <div class="report-icon">🎮</div>
                                <div class="report-title">Organization Editor</div>
                                <div class="report-desc">Edit and manage tournament organizations</div>
                            </a>
                            <a href="/api/tournaments" class="report-card" target="_blank">
                                <div class="report-icon">🔌</div>
                                <div class="report-title">API Data</div>
                                <div class="report-desc">Access raw tournament data via API</div>
                            </a>
                        </div>
                    </div>
                </div>
                
                <script>
                function toggleFullscreen() {
                    const iframe = document.getElementById('heatmap-iframe');
                    if (!document.fullscreenElement) {
                        iframe.requestFullscreen().catch(err => {
                            alert('Error attempting to enable fullscreen: ' + err.message);
                        });
                    } else {
                        document.exitFullscreen();
                    }
                }
                </script>
            </body>
            </html>
            """
            return web.Response(text=html, content_type='text/html')
        
        # Otherwise, show a page with generation instructions
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Heat Maps - Tournament Tracker</title>
            <style>
                body { 
                    font-family: -apple-system, sans-serif; 
                    padding: 0; 
                    margin: 0;
                    background: #f5f5f5;
                }
                .navbar { 
                    background: #2c3e50; 
                    color: white; 
                    padding: 1rem 2rem; 
                }
                .navbar a { 
                    color: white; 
                    text-decoration: none; 
                    margin-right: 2rem; 
                }
                .navbar a:hover { opacity: 0.8; }
                .container { 
                    padding: 2rem; 
                    max-width: 1200px; 
                    margin: 0 auto; 
                }
                .alert {
                    background: #fff3cd;
                    border: 1px solid #856404;
                    color: #856404;
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 2rem 0;
                }
                .code {
                    background: #2c3e50;
                    color: #fff;
                    padding: 1rem;
                    border-radius: 8px;
                    font-family: 'Courier New', monospace;
                    margin: 1rem 0;
                }
                h1 { color: #2c3e50; }
                .button {
                    background: #3498db;
                    color: white;
                    padding: 0.75rem 1.5rem;
                    text-decoration: none;
                    border-radius: 5px;
                    display: inline-block;
                    margin-top: 1rem;
                }
                .button:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
                <a href="/report">Reports</a>
                <a href="/organizations">Organizations</a>
                <a href="/tournaments">Tournaments</a>
            </nav>
            <div class="container">
                <h1>Tournament Heat Maps</h1>
                
                <div class="alert">
                    <strong>Heatmap not generated yet!</strong><br>
                    Generate the heatmap first using the command below.
                </div>
                
                <h2>How to Generate Heat Maps</h2>
                <p>Run this command in the terminal:</p>
                <div class="code">./go.py --heatmap --skip-sync</div>
                
                <p>This will generate:</p>
                <ul>
                    <li><strong>tournament_heatmap.html</strong> - Interactive heatmap</li>
                    <li><strong>tournament_heatmap_with_map.png</strong> - Static heatmap with map</li>
                    <li><strong>attendance_heatmap.png</strong> - Attendance-weighted heatmap</li>
                </ul>
                
                <p>After generation, refresh this page to see the interactive heatmap.</p>
                
                <a href="/report" class="button">View Reports Instead</a>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def players_handler(self, request):
        """Serve the players page"""
        html = self._load_template('players.html')
        return web.Response(text=html, content_type='text/html')
    
    async def player_detail_handler(self, request):
        """Serve individual player detail page - Pythonic way!"""
        from tournament_models import Player
        from formatters import PlayerFormatter
        
        player_id = int(request.match_info['player_id'])
        
        with session_scope() as session:
            player = session.query(Player).get(player_id)
            
            if not player:
                return web.Response(text="<h1>Player not found</h1>", status=404)
            
            # The Player object provides all the data we need
            player_data = {
                'id': player.id,
                'name': player.gamer_tag or player.name or 'Unknown',
                'rank': 1,  # TODO: Calculate rank
                'total_points': 0,
                'tournament_count': 0,
                'win_count': 0,
                'win_rate': 0,
                'podium_rate': 0,
                'avg_placement': 0,
                'recent_results': [],
                'rivals': [],
                'tournament_history': []
            }
            
            # Use the Player object's methods to get data
            try:
                if hasattr(player, 'get_stats'):
                    stats = player.get_stats()
                    if stats:
                        player_data.update({
                            'total_points': stats.get('total_points', 0),  # Use centralized points calculation
                            'tournament_count': stats.get('total_tournaments', 0),
                            'win_count': stats.get('wins', 0),
                            'win_rate': stats.get('win_rate', 0),
                            'podium_rate': stats.get('podium_rate', 0),
                            'avg_placement': stats.get('average_placement', 0)
                        })
                        
                        # Get recent results from stats
                        if 'recent_results' in stats:
                            player_data['recent_results'] = [
                                {
                                    'tournament_name': r.get('tournament', 'Unknown'),
                                    'placement': r.get('placement', 'N/A'),
                                    'date': r.get('date', 'N/A')[:10] if r.get('date') else 'N/A',  # Just date part
                                    'attendees': r.get('attendees', 'N/A')
                                }
                                for r in stats['recent_results']
                            ]
                
                # Get tournament history from placements
                if hasattr(player, 'placements'):
                    try:
                        placements = list(player.placements)
                        player_data['tournament_history'] = []
                        
                        for p in placements[-20:]:  # Last 20 tournaments
                            if hasattr(p, 'tournament') and p.tournament:
                                player_data['tournament_history'].append({
                                    'name': p.tournament.name if hasattr(p.tournament, 'name') else 'Unknown',
                                    'placement': p.placement if hasattr(p, 'placement') else 'N/A',
                                    'date': p.recorded_at.strftime('%Y-%m-%d') if hasattr(p, 'recorded_at') and p.recorded_at else 'N/A',
                                    'points': p.get_points() if hasattr(p, 'get_points') and callable(p.get_points) else 0
                                })
                    except:
                        pass
            
            except Exception as e:
                self.logger.error(f"Error getting player data: {e}")
            
            # The formatter decides how to present the data (HTML in this case)
            html = PlayerFormatter.format_html(player_data)
            return web.Response(text=html, content_type='text/html')
    
    async def tournament_detail_handler(self, request):
        """Serve individual tournament detail page - Maximum Pythonic Intelligence!"""
        from tournament_models import Tournament, TournamentPlacement, Player
        from formatters import TournamentFormatter
        
        tournament_id = int(request.match_info['tournament_id'])
        
        with session_scope() as session:
            tournament = session.query(Tournament).get(tournament_id)
            
            if not tournament:
                return web.Response(text="<h1>Tournament not found</h1>", status=404)
            
            # The Tournament object provides ALL its intelligence - with safe access
            tournament_data = {
                'id': tournament.id,
                'name': getattr(tournament, 'name', 'Unknown Tournament'),
                'date': 'Unknown',
                'location': 'Unknown',
                'venue': getattr(tournament, 'venue_name', None) or 'Unknown',
                'attendees': getattr(tournament, 'num_attendees', 0) or 0,
                'organization': 'Independent',
                'is_major': False,
                'coordinates': None,
            }
            
            # Safely get date
            try:
                start_at = getattr(tournament, 'start_at', None)
                if start_at:
                    if isinstance(start_at, int):
                        tournament_data['date'] = datetime.fromtimestamp(start_at).strftime('%Y-%m-%d')
                    else:
                        tournament_data['date'] = str(start_at)[:10]  # Take first 10 chars for date
            except:
                pass
                
            # Safely get location
            try:
                city = getattr(tournament, 'city', None)
                state = getattr(tournament, 'addr_state', None)
                if city and state:
                    tournament_data['location'] = f"{city}, {state}"
                elif city:
                    tournament_data['location'] = city
                elif hasattr(tournament, 'venue_name') and tournament.venue_name:
                    tournament_data['location'] = tournament.venue_name
            except:
                pass
                
            # Safely get organization
            try:
                if tournament.organization and hasattr(tournament.organization, 'name'):
                    tournament_data['organization'] = tournament.organization.name
            except:
                pass
                
            # Safely determine if major tournament
            try:
                attendees = tournament_data['attendees']
                tournament_data['is_major'] = attendees > 100
            except:
                pass
                
            # Safely get coordinates
            try:
                if hasattr(tournament, 'coordinates') and tournament.coordinates:
                    tournament_data['coordinates'] = tournament.coordinates
                elif hasattr(tournament, 'has_location') and tournament.has_location:
                    lat = getattr(tournament, 'lat', None)
                    lng = getattr(tournament, 'lng', None)
                    if lat and lng:
                        tournament_data['coordinates'] = (float(lat), float(lng))
            except:
                pass
            
            # Use Tournament's OOP relationships to get comprehensive data
            # IMPORTANT: All database access must stay within this session scope
            try:
                # Get all placements using Tournament intelligence within the same session
                placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.tournament_id == tournament.id
                ).join(Player).order_by(TournamentPlacement.placement.asc()).all()
                
                # Process all data while still in session scope
                placement_data = []
                for p in placements:
                    # Access all relationship data within session
                    player_name = p.player.gamer_tag or p.player.name or 'Unknown'
                    placement_data.append({
                        'placement': p.placement,
                        'player': player_name,
                        'player_id': p.player.id,
                        'points': p.prize_amount or 0,  # Use prize_amount instead of points
                        'prize_dollars': p.prize_dollars or 0
                    })
                
                # Tournament analytics using object intelligence
                tournament_data.update({
                    'total_entrants': len(placement_data),
                    'completion_rate': len(placement_data) / max(tournament.num_attendees or 1, 1) * 100,
                    'top_8': [p for p in placement_data if p['placement'] and p['placement'] <= 8][:8],
                    'all_placements': placement_data,
                    'bracket_insights': {
                        'upset_count': 0,  # Simplified for now - no session access needed
                        'veteran_count': min(len(placement_data), 3),  # Estimate 
                        'newcomer_count': min(len(placement_data), 2)  # Estimate
                    }
                })
                
                # Tournament performance metrics using intelligence
                if placement_data:
                    avg_points = sum(p['points'] for p in placement_data) / len(placement_data)
                    tournament_data['performance_metrics'] = {
                        'average_points': round(avg_points, 1),
                        'point_distribution': 'High' if avg_points > 50 else 'Medium' if avg_points > 20 else 'Low',
                        'competitive_level': 'Major' if tournament_data['is_major'] else 'Regional'
                    }
                
                # Geographic and venue intelligence - access within session
                try:
                    if getattr(tournament, 'has_location', False):
                        coords = getattr(tournament, 'coordinates', None)
                        attendees = getattr(tournament, 'num_attendees', 0) or 0
                        tournament_data['geographic_data'] = {
                            'coordinates': coords,
                            'distance_analysis': 'Available' if coords else 'Not Available',
                            'venue_quality': 'Premium' if attendees > 150 else 'Standard'
                        }
                except Exception as e:
                    self.logger.debug(f"Error accessing geographic data: {e}")
                    pass
                    
            except Exception as e:
                self.logger.error(f"Error getting tournament data: {e}")
                tournament_data['error'] = str(e)
            
            # The TournamentFormatter decides how to present the data (HTML)
            html = TournamentFormatter.format_html(tournament_data)
            return web.Response(text=html, content_type='text/html')
    
    async def standings_handler(self, request):
        """Serve the standings page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Standings - Tournament Tracker</title>
            <style>
                body { font-family: -apple-system, sans-serif; padding: 2rem; }
                .navbar { background: #2c3e50; color: white; padding: 1rem; margin: -2rem -2rem 2rem; }
                .navbar a { color: white; text-decoration: none; margin-right: 2rem; }
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
            </nav>
            <h1>Recent Tournament Standings</h1>
            <p>Tournament results and standings coming soon...</p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def discord_config_handler(self, request):
        """Serve the Discord configuration page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Discord Bot - Tournament Tracker</title>
            <style>
                body { font-family: -apple-system, sans-serif; padding: 2rem; }
                .navbar { background: #2c3e50; color: white; padding: 1rem; margin: -2rem -2rem 2rem; }
                .navbar a { color: white; text-decoration: none; margin-right: 2rem; }
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
            </nav>
            <h1>Discord Bot Configuration</h1>
            <p>Bot settings and command configuration coming soon...</p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def export_handler(self, request):
        """Serve the export page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Export - Tournament Tracker</title>
            <style>
                body { font-family: -apple-system, sans-serif; padding: 2rem; }
                .navbar { background: #2c3e50; color: white; padding: 1rem; margin: -2rem -2rem 2rem; }
                .navbar a { color: white; text-decoration: none; margin-right: 2rem; }
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
            </nav>
            <h1>Export Options</h1>
            <p>Data export functionality coming soon...</p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def sync_status_handler(self, request):
        """Serve the sync status page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sync Status - Tournament Tracker</title>
            <style>
                body { font-family: -apple-system, sans-serif; padding: 2rem; }
                .navbar { background: #2c3e50; color: white; padding: 1rem; margin: -2rem -2rem 2rem; }
                .navbar a { color: white; text-decoration: none; margin-right: 2rem; }
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
            </nav>
            <h1>Synchronization Status</h1>
            <p>Sync monitoring and control coming soon...</p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def get_stats(self, request):
        """Get database statistics"""
        stats = database_service.get_summary_stats()
        
        # Get last sync time (simplified for now)
        last_sync = "Unknown"
        
        return web.json_response({
            'tournaments': stats.total_tournaments,
            'organizations': stats.total_organizations,
            'players': stats.total_players,
            'last_sync': last_sync
        })
    
    async def get_services(self, request):
        """Get service status"""
        services = []
        
        # Check Discord bot
        try:
            result = subprocess.run(['pgrep', '-f', 'discord'], capture_output=True)
            discord_running = result.returncode == 0
        except:
            discord_running = False
            
        services.append({
            'name': 'Discord Bot',
            'running': discord_running
        })
        
        # Web editor is always running if we're here
        services.append({
            'name': 'Web Editor',
            'running': True
        })
        
        return web.json_response(services)
    
    async def start_sync(self, request):
        """Start tournament synchronization"""
        # This would normally trigger the sync process
        # For now, just return a success message
        return web.json_response({
            'success': True,
            'message': 'Sync started in background'
        })
    
    async def publish_shopify(self, request):
        """Publish to Shopify"""
        return web.json_response({
            'success': True,
            'message': 'Publishing to Shopify...'
        })
    
    async def get_tournaments(self, request):
        """API endpoint for tournaments"""
        # Use the database service which handles all the complexities
        from database_service import database_service
        
        # Get the raw tournament data using the service
        data = []
        
        try:
            # Get summary stats to verify database is working
            stats = database_service.get_summary_stats()
            
            # For now, return a simplified tournament list
            # We'll enhance this once we understand the model structure better
            from tournament_models import Tournament
            with session_scope() as session:
                tournaments = session.query(Tournament).limit(100).all()
                
                for t in tournaments:
                    try:
                        tournament_data = {
                            'id': t.id,
                            'name': t.name if hasattr(t, 'name') else 'Unknown',
                            'date': None,  # Will add date handling later
                            'attendees': t.num_attendees if hasattr(t, 'num_attendees') else 0,
                            'organization': 'TBD',  # Will add org lookup later
                            'location': 'Southern California'  # Default for now
                        }
                        
                        # Try to get date if available
                        if hasattr(t, 'start_date') and t.start_date:
                            try:
                                tournament_data['date'] = t.start_date.isoformat()
                            except:
                                pass
                        
                        data.append(tournament_data)
                    except Exception as e:
                        # Skip problematic tournaments
                        continue
                        
        except Exception as e:
            # Return empty array on error
            self.logger.error(f"Error fetching tournaments: {e}")
            return web.json_response([])
            
        return web.json_response(data)
    
    async def get_players(self, request):
        """API endpoint for player rankings"""
        player_data = []
        
        try:
            from tournament_models import Player
            
            with session_scope() as session:
                players = session.query(Player).limit(100).all()
                
                # Calculate rankings based on points - within session scope
                for player in players:
                    try:
                        # Basic player info - use gamer_tag as primary name
                        display_name = 'Unknown'
                        if hasattr(player, 'gamer_tag') and player.gamer_tag:
                            display_name = player.gamer_tag
                        elif hasattr(player, 'name') and player.name:
                            display_name = player.name
                        
                        player_info = {
                            'id': player.id,
                            'name': display_name,
                            'event_count': 0,
                            'first_places': 0,
                            'podium_finishes': 0,
                            'total_points': 0,
                            'avg_placement': None
                        }
                        
                        # Try to get placement stats if available
                        if hasattr(player, 'placements'):
                            try:
                                placements = list(player.placements)
                                player_info['event_count'] = len(placements)
                                
                                for p in placements:
                                    if hasattr(p, 'placement'):
                                        if p.placement == 1:
                                            player_info['first_places'] += 1
                                        if p.placement <= 3:
                                            player_info['podium_finishes'] += 1
                                    
                                    # Try different ways to get points
                                    if hasattr(p, 'get_points') and callable(p.get_points):
                                        try:
                                            pts = p.get_points()
                                            if pts:
                                                player_info['total_points'] += pts
                                        except:
                                            pass
                                    elif hasattr(p, 'points'):
                                        player_info['total_points'] += (p.points or 0)
                                    # Award default points based on placement
                                    elif hasattr(p, 'placement'):
                                        from points_system import PointsSystem
                                        player_info['total_points'] += PointsSystem.get_points_for_placement(p.placement)
                                
                                if player_info['event_count'] > 0:
                                    total_placement = sum(p.placement for p in placements if hasattr(p, 'placement'))
                                    player_info['avg_placement'] = total_placement / player_info['event_count']
                            except:
                                pass
                        
                        player_data.append(player_info)
                    except Exception as e:
                        # Skip problematic players
                        continue
            
            # Sort by total points
            player_data.sort(key=lambda x: x['total_points'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error fetching players: {e}")
            return web.json_response([])
        
        return web.json_response(player_data)
    
    async def get_organizations(self, request):
        """API endpoint for organizations"""
        from tournament_models import Organization
        
        with session_scope() as session:
            orgs = session.query(Organization).all()
            
            data = []
            for org in orgs:
                org_data = {
                    'id': org.id,
                    'display_name': org.display_name,
                    'tournament_count': len(org.tournaments),
                    'contacts': [
                        {
                            'type': contact.contact_type,
                            'value': contact.contact_value
                        }
                        for contact in org.contacts
                    ]
                }
                data.append(org_data)
            
        return web.json_response(data)
    
    async def update_organization(self, request):
        """Update organization details"""
        from tournament_models import Organization, OrganizationContact
        
        org_id = int(request.match_info['org_id'])
        data = await request.json()
        
        with session_scope() as session:
            org = session.query(Organization).get(org_id)
            if org:
                # Update name
                if 'name' in data:
                    org.display_name = data['name']
                
                # Update contacts
                if 'contacts' in data:
                    # Remove existing contacts
                    for contact in org.contacts:
                        session.delete(contact)
                    
                    # Add new contacts
                    for contact_data in data['contacts']:
                        contact = OrganizationContact(
                            organization_id=org.id,
                            contact_type=contact_data['type'],
                            contact_value=contact_data['value']
                        )
                        session.add(contact)
                
                session.commit()
                return web.json_response({'success': True})
            
        return web.json_response({'error': 'Organization not found'}, status=404)
    
    async def merge_organizations(self, request):
        """Merge organizations"""
        from tournament_models import Organization, Tournament
        
        data = await request.json()
        source_id = int(data.get('source_id'))
        target_id = int(data.get('target_id'))
        
        with session_scope() as session:
            source = session.query(Organization).get(source_id)
            target = session.query(Organization).get(target_id)
            
            if not source or not target:
                return web.json_response({'error': 'Organization not found'}, status=404)
            
            # Transfer tournaments
            tournaments = session.query(Tournament).filter_by(organization_id=source.id).all()
            for tournament in tournaments:
                tournament.organization_id = target.id
            
            # Transfer contacts
            for contact in source.contacts:
                # Check if contact already exists in target
                existing = any(
                    c.contact_type == contact.contact_type and 
                    c.contact_value == contact.contact_value 
                    for c in target.contacts
                )
                if not existing:
                    contact.organization_id = target.id
            
            # Delete source organization
            session.delete(source)
            session.commit()
            
        return web.json_response({'success': True})
    
    async def update_contacts(self, request):
        """Update organization contacts"""
        from tournament_models import Organization
        
        org_id = int(request.match_info['org_id'])
        data = await request.json()
        contacts = data.get('contacts', [])
        
        with session_scope() as session:
            org = session.query(Organization).get(org_id)
            if org:
                org.contacts = contacts
                session.commit()
                return web.json_response({'success': True})
            
        return web.json_response({'error': 'Organization not found'}, status=404)
    
    async def run(self):
        """Run the web server"""
        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()
        
        self.logger.info(f"Editor service running on http://{self.config.host}:{self.config.port}")
        self.runner = runner
        
        # Keep running
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()
    
    def run_blocking(self):
        """Run the web server in blocking mode"""
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            self.logger.info("Editor service stopped by user")
    
    async def stop(self):
        """Stop the web server"""
        if self.runner:
            await self.runner.cleanup()
            self.runner = None


    async def get_attendance_timeline(self, request):
        """API endpoint for attendance over time data"""
        from tournament_models import Tournament
        from datetime import datetime, timedelta
        import calendar
        
        try:
            with session_scope() as session:
                # Get all tournaments with attendance data
                tournaments = session.query(Tournament).filter(
                    Tournament.num_attendees > 0,
                    Tournament.start_at > 0
                ).order_by(Tournament.start_at).all()
                
                # Group by month
                monthly_data = {}
                for t in tournaments:
                    # Convert timestamp to date
                    date = datetime.fromtimestamp(t.start_at)
                    month_key = f"{date.year}-{date.month:02d}"
                    
                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            'month': calendar.month_name[date.month][:3],
                            'year': date.year,
                            'total_attendance': 0,
                            'tournament_count': 0,
                            'tournaments': []
                        }
                    
                    monthly_data[month_key]['total_attendance'] += t.num_attendees
                    monthly_data[month_key]['tournament_count'] += 1
                    monthly_data[month_key]['tournaments'].append({
                        'name': t.name,
                        'attendance': t.num_attendees,
                        'date': date.strftime('%Y-%m-%d')
                    })
                
                # Convert to sorted list
                timeline = []
                for month_key in sorted(monthly_data.keys()):
                    data = monthly_data[month_key]
                    timeline.append({
                        'label': f"{data['month']} {data['year']}",
                        'total_attendance': data['total_attendance'],
                        'tournament_count': data['tournament_count'],
                        'average_attendance': data['total_attendance'] / data['tournament_count'] if data['tournament_count'] > 0 else 0,
                        'tournaments': sorted(data['tournaments'], key=lambda x: x['attendance'], reverse=True)[:5]  # Top 5
                    })
                
                return web.json_response(timeline)
                
        except Exception as e:
            self.logger.error(f"Error getting attendance timeline: {e}")
            return web.json_response({'error': str(e)}, status=500)
    
    async def charts_handler(self, request):
        """Serve the charts visualization page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Charts & Analytics - Tournament Tracker</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                }
                h1 {
                    color: white;
                    text-align: center;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }
                .description {
                    color: white;
                    text-align: center;
                    margin-bottom: 30px;
                    opacity: 0.9;
                }
                .chart-container {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    margin-bottom: 30px;
                }
                .chart-wrapper {
                    position: relative;
                    height: 400px;
                }
                .chart-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }
                .chart-title {
                    font-size: 1.3em;
                    font-weight: 600;
                    color: #333;
                }
                .chart-controls {
                    display: flex;
                    gap: 10px;
                }
                .control-btn {
                    padding: 6px 12px;
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 0.9em;
                }
                .control-btn:hover {
                    background: #5a67d8;
                }
                .control-btn.active {
                    background: #48bb78;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .stat-card {
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    text-align: center;
                }
                .stat-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                    margin: 10px 0;
                }
                .stat-label {
                    color: #666;
                    font-size: 0.9em;
                }
                .loading {
                    text-align: center;
                    padding: 40px;
                    color: #666;
                }
                .tooltip-content {
                    background: rgba(0,0,0,0.8);
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 0.9em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Tournament Analytics</h1>
                <p class="description">Interactive charts and visualizations of tournament data</p>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Attendance</div>
                        <div class="stat-value" id="total-attendance">-</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Peak Month</div>
                        <div class="stat-value" id="peak-month">-</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Average per Event</div>
                        <div class="stat-value" id="avg-attendance">-</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Total Events</div>
                        <div class="stat-value" id="total-events">-</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-header">
                        <div class="chart-title">📈 Total Attendance Over Time</div>
                        <div class="chart-controls">
                            <button class="control-btn active" onclick="switchChart('line')">Line</button>
                            <button class="control-btn" onclick="switchChart('bar')">Bar</button>
                            <button class="control-btn" onclick="switchChart('area')">Area</button>
                        </div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="attendanceChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-header">
                        <div class="chart-title">📊 Average Attendance per Tournament</div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="averageChart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-header">
                        <div class="chart-title">🎮 Number of Tournaments per Month</div>
                    </div>
                    <div class="chart-wrapper">
                        <canvas id="countChart"></canvas>
                    </div>
                </div>
            </div>
            
            <script>
                let attendanceChart = null;
                let averageChart = null;
                let countChart = null;
                let timelineData = [];
                
                async function loadData() {
                    try {
                        const response = await fetch('/api/attendance-timeline');
                        timelineData = await response.json();
                        
                        // Calculate stats
                        let totalAttendance = 0;
                        let totalEvents = 0;
                        let peakMonth = '';
                        let peakAttendance = 0;
                        
                        timelineData.forEach(month => {
                            totalAttendance += month.total_attendance;
                            totalEvents += month.tournament_count;
                            if (month.total_attendance > peakAttendance) {
                                peakAttendance = month.total_attendance;
                                peakMonth = month.label;
                            }
                        });
                        
                        // Update stats
                        document.getElementById('total-attendance').textContent = totalAttendance.toLocaleString();
                        document.getElementById('peak-month').textContent = peakMonth;
                        document.getElementById('avg-attendance').textContent = Math.round(totalAttendance / totalEvents).toLocaleString();
                        document.getElementById('total-events').textContent = totalEvents.toLocaleString();
                        
                        // Create charts
                        createAttendanceChart('line');
                        createAverageChart();
                        createCountChart();
                        
                    } catch (error) {
                        console.error('Error loading data:', error);
                    }
                }
                
                function createAttendanceChart(type) {
                    const ctx = document.getElementById('attendanceChart').getContext('2d');
                    
                    if (attendanceChart) {
                        attendanceChart.destroy();
                    }
                    
                    const config = {
                        type: type === 'area' ? 'line' : type,
                        data: {
                            labels: timelineData.map(d => d.label),
                            datasets: [{
                                label: 'Total Attendance',
                                data: timelineData.map(d => d.total_attendance),
                                borderColor: 'rgb(102, 126, 234)',
                                backgroundColor: type === 'area' ? 'rgba(102, 126, 234, 0.2)' : 'rgba(102, 126, 234, 0.6)',
                                tension: 0.4,
                                fill: type === 'area'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            resizeDelay: 0,
                            plugins: {
                                legend: {
                                    display: false
                                },
                                tooltip: {
                                    callbacks: {
                                        afterLabel: function(context) {
                                            const month = timelineData[context.dataIndex];
                                            return `Tournaments: ${month.tournament_count}`;
                                        }
                                    }
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        callback: function(value) {
                                            return value.toLocaleString();
                                        }
                                    }
                                }
                            }
                        }
                    };
                    
                    attendanceChart = new Chart(ctx, config);
                }
                
                function createAverageChart() {
                    const ctx = document.getElementById('averageChart').getContext('2d');
                    
                    averageChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: timelineData.map(d => d.label),
                            datasets: [{
                                label: 'Average Attendance',
                                data: timelineData.map(d => Math.round(d.average_attendance)),
                                borderColor: 'rgb(72, 187, 120)',
                                backgroundColor: 'rgba(72, 187, 120, 0.2)',
                                tension: 0.4,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            resizeDelay: 0,
                            plugins: {
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                }
                
                function createCountChart() {
                    const ctx = document.getElementById('countChart').getContext('2d');
                    
                    countChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: timelineData.map(d => d.label),
                            datasets: [{
                                label: 'Number of Tournaments',
                                data: timelineData.map(d => d.tournament_count),
                                backgroundColor: 'rgba(245, 158, 11, 0.6)',
                                borderColor: 'rgb(245, 158, 11)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            resizeDelay: 0,
                            plugins: {
                                legend: {
                                    display: false
                                }
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        stepSize: 1
                                    }
                                }
                            }
                        }
                    });
                }
                
                function switchChart(type) {
                    document.querySelectorAll('.control-btn').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    event.target.classList.add('active');
                    createAttendanceChart(type);
                }
                
                // Load data on page load
                loadData();
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')

# Singleton instance
editor_service = EditorService()


# Helper function for compatibility
def get_unnamed_tournaments():
    """Get tournaments that don't have an organization assigned"""
    from database import session_scope
    from tournament_models import Tournament
    
    with session_scope() as session:
        tournaments = session.query(Tournament).filter(
            Tournament.organization_id.is_(None)
        ).order_by(Tournament.start_date.desc()).all()
        
        result = []
        for t in tournaments:
            result.append({
                'id': t.id,
                'name': t.name,
                'owner_name': t.owner_name,
                'contact': t.owner_name,
                'start_date': t.start_date.strftime('%Y-%m-%d') if t.start_date else 'Unknown',
                'attendees': t.num_attendees or 0
            })
        
        return result


# Convenience functions
def launch_editor(port: int = 8081, mode: str = 'full'):
    """Launch the editor service"""
    config = EditorConfig(
        port=port,
        mode=EditorMode(mode)
    )
    service = EditorService(config)
    service.run_blocking()


if __name__ == '__main__':
    launch_editor()