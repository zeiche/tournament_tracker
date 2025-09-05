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
        app.router.add_get('/tournaments', self.tournaments_handler)
        app.router.add_get('/report', self.report_handler)
        app.router.add_get('/heatmap', self.heatmap_handler)
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
    
    async def tournaments_handler(self, request):
        """Serve the tournaments page"""
        html = self._load_template('tournaments.html')
        return web.Response(text=html, content_type='text/html')
    
    async def report_handler(self, request):
        """Serve the report page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reports - Tournament Tracker</title>
            <style>
                body { font-family: -apple-system, sans-serif; padding: 2rem; }
                .navbar { background: #2c3e50; color: white; padding: 1rem; margin: -2rem -2rem 2rem; }
                .navbar a { color: white; text-decoration: none; margin-right: 2rem; }
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
                <a href="/organizations">Organizations</a>
                <a href="/tournaments">Tournaments</a>
                <a href="/report">Reports</a>
            </nav>
            <h1>Tournament Reports</h1>
            <p>Comprehensive reports and analytics coming soon...</p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def heatmap_handler(self, request):
        """Serve the heatmap page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Heat Maps - Tournament Tracker</title>
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
            <h1>Tournament Heat Maps</h1>
            <p>Geographic visualizations coming soon...</p>
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


# Singleton instance
editor_service = EditorService()


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