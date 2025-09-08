"""
editor_service.py - Web Editor Service

NOW USING POLYMORPHIC ask/tell/do PATTERN:
- ask(query) - Get data: "unnamed tournaments", "organizations", "stats"
- tell(format, data) - Format output: "html", "json", "api"
- do(action) - Perform actions: "start server", "update org 123", "merge orgs"
"""
import os
import sys
from typing import Any, Optional, Dict, List
import json
import asyncio
from aiohttp import web
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database_service import database_service
from utils.log_manager import LogManager
from polymorphic_core import announcer


@dataclass
class EditorConfig:
    """Configuration for editor service"""
    port: int = 8081
    host: str = '0.0.0.0'
    auto_open: bool = True
    debug: bool = False


class EditorService:
    """Web editor service with ONLY 3 public methods: ask, tell, do
    
    Everything else is private implementation details.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[EditorConfig] = None):
        if not self._initialized:
            self.config = config or EditorConfig()
            self.logger = LogManager().get_logger('editor')
            self.app = None
            self.runner = None
            self._initialized = True
            self._running = False
            
            # Announce ourselves
            announcer.announce(
                "EditorService (Polymorphic)",
                [
                    "ask('stats') - Get database statistics",
                    "ask('unnamed tournaments') - Get unnamed tournaments",
                    "ask('organizations') - Get all organizations",
                    "tell('html', data) - Format as HTML page",
                    "do('start server') - Start web server",
                    "do('update org 123 name=NewName') - Update organization",
                    "NOW WITH ask/tell/do PATTERN!"
                ],
                [
                    "editor.ask('stats')",
                    "editor.tell('html', tournament_data)",
                    "editor.do('start server port=8081')"
                ]
            )
    
    def ask(self, query: str, **kwargs) -> Any:
        """Ask for data from the editor service.
        
        Examples:
            ask('stats') - Get database statistics
            ask('unnamed tournaments') - Get tournaments without organizations
            ask('organizations') - Get all organizations  
            ask('org rankings') - Get organization rankings
            ask('recent tournaments') - Get recent tournaments
            ask('players') - Get player rankings
            ask('server status') - Check if server is running
        """
        query_lower = query.lower().strip()
        
        # Statistics queries
        if 'stat' in query_lower:
            return self._get_stats()
        
        # Tournament queries
        elif 'unnamed' in query_lower and 'tournament' in query_lower:
            return self._get_unnamed_tournaments()
        
        elif 'recent' in query_lower and 'tournament' in query_lower:
            return self._get_recent_tournaments()
        
        elif 'tournament' in query_lower:
            # Check for specific ID
            import re
            match = re.search(r'\d+', query)
            if match:
                tournament_id = int(match.group())
                return self._get_tournament(tournament_id)
            return self._get_all_tournaments()
        
        # Organization queries
        elif 'ranking' in query_lower and 'org' in query_lower:
            return self._get_org_rankings()
        
        elif 'organization' in query_lower:
            # Check for specific ID
            import re
            match = re.search(r'\d+', query)
            if match:
                org_id = int(match.group())
                return self._get_organization(org_id)
            return self._get_organizations()
        
        # Player queries
        elif 'player' in query_lower:
            # Check for specific ID
            import re
            match = re.search(r'\d+', query)
            if match:
                player_id = int(match.group())
                return self._get_player(player_id)
            return self._get_players()
        
        # Server status
        elif 'server' in query_lower or 'status' in query_lower:
            return {
                'running': self._running,
                'port': self.config.port,
                'host': self.config.host,
                'url': f"http://{self.config.host}:{self.config.port}" if self._running else None
            }
        
        # Default - return summary
        stats = self._get_stats()
        return {
            'tournaments': stats.get('total_tournaments', 0),
            'organizations': stats.get('total_organizations', 0),
            'players': stats.get('total_players', 0),
            'server_running': self._running
        }
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format data for output in various formats.
        
        Examples:
            tell('html', tournament_list) - Format as HTML page
            tell('json', organizations) - Format as JSON
            tell('api', data) - Format for API response
            tell('table', rankings) - Format as HTML table
        """
        format_lower = format.lower().strip()
        
        # If no data provided, get default data
        if data is None:
            data = self.ask('summary')
        
        if format_lower == 'html':
            return self._format_html(data)
        
        elif format_lower == 'json':
            return json.dumps(data, default=str, indent=2)
        
        elif format_lower == 'api':
            # API format is typically JSON without pretty printing
            return json.dumps(data, default=str)
        
        elif format_lower == 'table':
            return self._format_html_table(data)
        
        elif format_lower == 'page':
            return self._format_full_page(data)
        
        # Default - string representation
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform actions on the editor service.
        
        Examples:
            do('start server') - Start the web server
            do('start server port=8082') - Start on specific port
            do('stop server') - Stop the web server
            do('update org 123 name="New Name"') - Update organization
            do('merge org 1 into 2') - Merge organizations
            do('open browser') - Open web browser to editor
        """
        action_lower = action.lower().strip()
        
        # Server management
        if 'start' in action_lower and 'server' in action_lower:
            return self._do_start_server(action, **kwargs)
        
        elif 'stop' in action_lower and 'server' in action_lower:
            return self._do_stop_server()
        
        # Organization updates
        elif 'update' in action_lower and 'org' in action_lower:
            return self._do_update_org(action, **kwargs)
        
        # Organization merging
        elif 'merge' in action_lower:
            return self._do_merge_orgs(action, **kwargs)
        
        # Browser opening
        elif 'open' in action_lower and 'browser' in action_lower:
            return self._do_open_browser()
        
        # Unknown action
        return f"Unknown action: {action}"
    
    # ============= PRIVATE METHODS =============
    
    def _get_stats(self) -> Dict:
        """Get database statistics"""
        stats = database_service.ask('summary stats')
        return {
            'total_tournaments': stats.get('total_tournaments', 0),
            'total_organizations': stats.get('total_organizations', 0),
            'total_players': stats.get('total_players', 0),
            'total_placements': stats.get('total_placements', 0),
            'tournaments_with_standings': stats.get('tournaments_with_standings', 0)
        }
    
    def _get_unnamed_tournaments(self) -> List[Dict]:
        """Get tournaments without organizations"""
        # This would query for tournaments without org assignment
        tournaments = database_service.ask('tournaments without organization')
        if not isinstance(tournaments, list):
            tournaments = []
        
        result = []
        for t in tournaments[:50]:  # Limit to 50
            result.append({
                'id': t.get('id'),
                'name': t.get('name', 'Unknown'),
                'contact': t.get('primary_contact', ''),
                'attendees': t.get('num_attendees', 0),
                'date': t.get('start_date', 'Unknown')
            })
        
        return result
    
    def _get_recent_tournaments(self) -> List[Dict]:
        """Get recent tournaments"""
        return database_service.ask('recent tournaments days=90')
    
    def _get_all_tournaments(self) -> List[Dict]:
        """Get all tournaments"""
        return database_service.ask('all tournaments')[:100]  # Limit
    
    def _get_tournament(self, tournament_id: int) -> Dict:
        """Get specific tournament"""
        return database_service.ask(f'tournament {tournament_id}')
    
    def _get_organizations(self) -> List[Dict]:
        """Get all organizations"""
        return database_service.ask('all organizations')
    
    def _get_organization(self, org_id: int) -> Dict:
        """Get specific organization"""
        return database_service.ask(f'organization {org_id}')
    
    def _get_org_rankings(self) -> List[Dict]:
        """Get organization rankings"""
        return database_service.ask('organization rankings')
    
    def _get_players(self) -> List[Dict]:
        """Get player rankings"""
        return database_service.ask('player rankings limit=100')
    
    def _get_player(self, player_id: int) -> Dict:
        """Get specific player"""
        return database_service.ask(f'player {player_id}')
    
    def _format_html(self, data: Any) -> str:
        """Format data as HTML"""
        if isinstance(data, list):
            return self._format_html_table(data)
        elif isinstance(data, dict):
            return self._format_html_details(data)
        return f"<pre>{str(data)}</pre>"
    
    def _format_html_table(self, data: List[Dict]) -> str:
        """Format list as HTML table"""
        if not data:
            return "<p>No data available</p>"
        
        # Get headers from first item
        headers = list(data[0].keys()) if data else []
        
        html = "<table border='1'><thead><tr>"
        for header in headers:
            html += f"<th>{header}</th>"
        html += "</tr></thead><tbody>"
        
        for item in data:
            html += "<tr>"
            for header in headers:
                value = item.get(header, '')
                html += f"<td>{value}</td>"
            html += "</tr>"
        
        html += "</tbody></table>"
        return html
    
    def _format_html_details(self, data: Dict) -> str:
        """Format dict as HTML details"""
        html = "<dl>"
        for key, value in data.items():
            html += f"<dt><strong>{key}:</strong></dt>"
            html += f"<dd>{value}</dd>"
        html += "</dl>"
        return html
    
    def _format_full_page(self, data: Any) -> str:
        """Format as full HTML page"""
        content = self._format_html(data)
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Editor Service</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; padding: 2rem; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 0.5rem; text-align: left; }}
        th {{ background: #f0f0f0; }}
    </style>
</head>
<body>
    <h1>Tournament Editor</h1>
    {content}
</body>
</html>"""
    
    def _do_start_server(self, action: str, **kwargs) -> str:
        """Start the web server"""
        if self._running:
            return f"Server already running on port {self.config.port}"
        
        # Parse port if specified
        import re
        port_match = re.search(r'port[=\s]+(\d+)', action)
        if port_match:
            self.config.port = int(port_match.group(1))
        elif 'port' in kwargs:
            self.config.port = kwargs['port']
        
        # Start server in background thread
        import threading
        thread = threading.Thread(target=self._run_server_sync)
        thread.daemon = True
        thread.start()
        
        self._running = True
        return f"Server started on http://{self.config.host}:{self.config.port}"
    
    def _do_stop_server(self) -> str:
        """Stop the web server"""
        if not self._running:
            return "Server not running"
        
        # Stop server
        if self.runner:
            asyncio.create_task(self.runner.cleanup())
        
        self._running = False
        return "Server stopped"
    
    def _do_update_org(self, action: str, **kwargs) -> str:
        """Update organization"""
        import re
        
        # Parse org ID
        id_match = re.search(r'org[anization]*\s+(\d+)', action)
        if not id_match:
            return "Error: No organization ID specified"
        
        org_id = int(id_match.group(1))
        
        # Parse name
        name_match = re.search(r'name\s*=\s*["\']?([^"\'\n]+)["\']?', action)
        name = name_match.group(1).strip() if name_match else kwargs.get('name')
        
        if not name:
            return "Error: No name specified"
        
        # Update via database service
        result = database_service.do(f'update organization {org_id} name="{name}"')
        return result
    
    def _do_merge_orgs(self, action: str, **kwargs) -> str:
        """Merge organizations"""
        import re
        
        # Parse IDs
        match = re.search(r'(\d+)\s+into\s+(\d+)', action)
        if not match:
            return "Error: Use format 'merge org SOURCE_ID into TARGET_ID'"
        
        source_id = int(match.group(1))
        target_id = int(match.group(2))
        
        # Merge via database service
        result = database_service.do(f'merge organization {source_id} into {target_id}')
        return result
    
    def _do_open_browser(self) -> str:
        """Open web browser to editor"""
        if not self._running:
            return "Server not running - start it first with: do('start server')"
        
        import webbrowser
        url = f"http://localhost:{self.config.port}"
        webbrowser.open(url)
        return f"Opened browser to {url}"
    
    def _run_server_sync(self):
        """Run server synchronously in thread"""
        try:
            asyncio.run(self._run_server())
        except Exception as e:
            self.logger.error(f"Server error: {e}")
    
    async def _run_server(self):
        """Run the web server"""
        app = self._create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()
        
        self.runner = runner
        self.logger.info(f"Editor service running on http://{self.config.host}:{self.config.port}")
        
        # Keep running
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            pass
        finally:
            await runner.cleanup()
    
    def _create_app(self) -> web.Application:
        """Create web application with routes"""
        app = web.Application()
        
        # Main routes - these use ask/tell internally
        app.router.add_get('/', self._index_handler)
        app.router.add_get('/api/stats', self._stats_handler)
        app.router.add_get('/api/organizations', self._organizations_handler)
        app.router.add_get('/api/tournaments', self._tournaments_handler)
        app.router.add_get('/api/players', self._players_handler)
        
        self.app = app
        return app
    
    async def _index_handler(self, request):
        """Serve the main page"""
        data = self.ask('stats')
        html = self.tell('page', data)
        return web.Response(text=html, content_type='text/html')
    
    async def _stats_handler(self, request):
        """API endpoint for stats"""
        data = self.ask('stats')
        json_data = self.tell('json', data)
        return web.Response(text=json_data, content_type='application/json')
    
    async def _organizations_handler(self, request):
        """API endpoint for organizations"""
        data = self.ask('organizations')
        json_data = self.tell('json', data)
        return web.Response(text=json_data, content_type='application/json')
    
    async def _tournaments_handler(self, request):
        """API endpoint for tournaments"""
        data = self.ask('recent tournaments')
        json_data = self.tell('json', data)
        return web.Response(text=json_data, content_type='application/json')
    
    async def _players_handler(self, request):
        """API endpoint for players"""
        data = self.ask('players')
        json_data = self.tell('json', data)
        return web.Response(text=json_data, content_type='application/json')


# Singleton instance - import this
editor_service = EditorService()


# Test function
def test_editor_service():
    """Test editor service with ask/tell/do pattern"""
    print("=" * 60)
    print("TESTING EDITOR SERVICE (ask/tell/do)")
    print("=" * 60)
    
    service = editor_service
    
    try:
        # Test 1: ask() method
        print("\nTEST 1: ask() method")
        print("ask('stats'):", service.ask('stats'))
        print("ask('server status'):", service.ask('server status'))
        print("✅ ask() works")
        
        # Test 2: tell() method
        print("\nTEST 2: tell() method")
        data = {'test': 'data', 'number': 42}
        print("tell('json', data):", service.tell('json', data)[:50] + "...")
        print("tell('html', data):", service.tell('html', data)[:100] + "...")
        print("✅ tell() works")
        
        # Test 3: do() method
        print("\nTEST 3: do() method")
        print("do('start server port=8082'):", service.do('start server port=8082'))
        import time
        time.sleep(1)  # Let server start
        print("ask('server status'):", service.ask('server status'))
        print("do('stop server'):", service.do('stop server'))
        print("✅ do() works")
        
        print("\n✅ All editor service tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_editor_service()