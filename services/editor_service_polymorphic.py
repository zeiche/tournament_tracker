#!/usr/bin/env python3
"""
editor_service_polymorphic.py - Web Editor with just ask/tell/do

Replaces route handlers and methods with 3 universal methods.

Examples:
    # Instead of: editor.start()
    editor.do("start")
    
    # Instead of: editor.get_stats()
    editor.ask("stats")
    
    # Instead of: editor.shutdown()
    editor.do("shutdown")
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import os
import sys
from aiohttp import web
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils'))

from universal_polymorphic import UniversalPolymorphic
from polymorphic_core import announcer
from database_service import database_service
from log_manager import LogManager
from shutdown_coordinator import on_shutdown


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


class EditorServicePolymorphic(UniversalPolymorphic):
    """
    Web editor service with polymorphic ask/tell/do pattern.
    
    Examples:
        editor = EditorServicePolymorphic()
        
        # Ask for information
        editor.ask("running")          # Check if server running
        editor.ask("port")             # Get port number
        editor.ask("stats")            # Get statistics
        editor.ask("routes")           # List available routes
        
        # Tell in different formats
        editor.tell("status")          # Current status
        editor.tell("json")            # Full config as JSON
        editor.tell("discord")         # Discord-formatted status
        
        # Do actions
        editor.do("start")             # Start web server
        editor.do("stop")              # Stop web server
        editor.do("restart")           # Restart server
        editor.do("open browser")      # Open in browser
    """
    
    _instance: Optional['EditorServicePolymorphic'] = None
    
    def __new__(cls) -> 'EditorServicePolymorphic':
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
            self.site: Optional[web.TCPSite] = None
            self.running = False
            self._initialized = True
            
            # Stats tracking
            self.stats = {
                'requests_served': 0,
                'uptime_seconds': 0,
                'start_time': None
            }
            
            # Call parent init (announces via UniversalPolymorphic)
            super().__init__()
            
            # Also announce via Bonjour
            announcer.announce(
                "EditorServicePolymorphic",
                [
                    "Web editor with ask/tell/do pattern",
                    f"Use editor.do('start') to launch on port {self.config.port}",
                    "Use editor.ask('running') to check status",
                    "Use editor.do('stop') to shutdown",
                    "Replaces route handlers with polymorphic pattern"
                ]
            )
            
            # Register for shutdown
            @on_shutdown
            async def shutdown_editor():
                await self._shutdown()
                
            self.shutdown_handler = shutdown_editor
    
    # =========================================================================
    # POLYMORPHIC HANDLERS
    # =========================================================================
    
    def _handle_ask(self, question: Any, **kwargs) -> Any:
        """
        Handle ask() queries about the editor service.
        
        Replaces property getters and status methods.
        """
        q = str(question).lower()
        
        # Server status queries
        if any(word in q for word in ['running', 'active', 'up']):
            return self.running
        
        if 'port' in q:
            return self.config.port
        
        if 'host' in q:
            return self.config.host
        
        if 'url' in q or 'address' in q:
            return f"http://{self.config.host}:{self.config.port}"
        
        if 'mode' in q:
            return self.config.mode.value
        
        # Statistics
        if any(word in q for word in ['stats', 'statistics']):
            if self.stats['start_time']:
                uptime = (datetime.now() - self.stats['start_time']).total_seconds()
                self.stats['uptime_seconds'] = int(uptime)
            
            return {
                'running': self.running,
                'port': self.config.port,
                'requests_served': self.stats['requests_served'],
                'uptime_seconds': self.stats['uptime_seconds']
            }
        
        # Routes information
        if 'routes' in q:
            if self.app and self.app.router:
                routes = []
                for route in self.app.router.routes():
                    if hasattr(route, 'method') and hasattr(route, 'resource'):
                        routes.append({
                            'method': route.method,
                            'path': str(route.resource.canonical)
                        })
                return routes
            return []
        
        # Database stats (delegate to database service)
        if 'database' in q or 'tournaments' in q or 'players' in q:
            return database_service.ask(question)
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str = "default", **kwargs) -> Any:
        """
        Format editor service information.
        
        Provides different views of the service state.
        """
        fmt = format.lower()
        
        if fmt in ['status', 'state']:
            status = 'Running' if self.running else 'Stopped'
            return f"Web Editor: {status} on port {self.config.port} | " \
                   f"Requests: {self.stats['requests_served']}"
        
        if fmt in ['brief', 'summary']:
            return f"Web editor {'running' if self.running else 'stopped'} on :{self.config.port}"
        
        if fmt in ['detailed', 'full']:
            uptime = 0
            if self.stats['start_time']:
                uptime = int((datetime.now() - self.stats['start_time']).total_seconds())
            
            return {
                'service': 'Web Editor (Polymorphic)',
                'status': 'Running' if self.running else 'Stopped',
                'config': {
                    'port': self.config.port,
                    'host': self.config.host,
                    'mode': self.config.mode.value,
                    'auto_open': self.config.auto_open
                },
                'stats': {
                    'requests_served': self.stats['requests_served'],
                    'uptime_seconds': uptime
                },
                'url': f"http://{self.config.host}:{self.config.port}" if self.running else None
            }
        
        if fmt == 'discord':
            status_emoji = '🟢' if self.running else '🔴'
            return f"**Web Editor** {status_emoji}\n" \
                   f"Port: {self.config.port}\n" \
                   f"Requests: {self.stats['requests_served']}\n" \
                   f"Mode: {self.config.mode.value}"
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: Any, **kwargs) -> Any:
        """
        Perform editor actions.
        
        Replaces:
        - start()
        - stop() / shutdown()
        - restart()
        - create_app()
        - Various route handlers
        """
        act = str(action).lower()
        
        # Announce the action
        announcer.announce(
            "EditorServicePolymorphic.do",
            [f"Executing action: {action}"]
        )
        
        # Server control
        if 'start' in act:
            return asyncio.run(self._start())
        
        if 'stop' in act or 'shutdown' in act:
            return asyncio.run(self._shutdown())
        
        if 'restart' in act:
            asyncio.run(self._shutdown())
            return asyncio.run(self._start())
        
        # Browser control
        if 'open' in act and 'browser' in act:
            if self.running:
                import webbrowser
                url = f"http://localhost:{self.config.port}"
                webbrowser.open(url)
                return {'opened': url}
            return {'error': 'Server not running'}
        
        # Route handling - delegate to specific handlers
        if 'handle' in act:
            route = kwargs.get('route', '/')
            request = kwargs.get('request')
            return asyncio.run(self._handle_route(route, request))
        
        # Database operations (delegate to database service)
        if any(word in act for word in ['sync', 'merge', 'update']):
            return database_service.do(action, **kwargs)
        
        return super()._handle_do(action, **kwargs)
    
    # =========================================================================
    # INTERNAL METHODS (prefixed with _)
    # =========================================================================
    
    async def _start(self) -> Dict[str, Any]:
        """Start the web server"""
        if self.running:
            return {'already_running': True, 'port': self.config.port}
        
        try:
            # Create application
            self.app = self._create_app()
            
            # Create and start runner
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            # Create site and start
            self.site = web.TCPSite(
                self.runner,
                self.config.host,
                self.config.port
            )
            await self.site.start()
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            self.logger.info(f"Web editor started on {self.config.host}:{self.config.port}")
            
            announcer.announce(
                "EditorServicePolymorphic.start",
                [
                    f"Web editor started on port {self.config.port}",
                    f"URL: http://{self.config.host}:{self.config.port}"
                ]
            )
            
            # Auto-open browser if configured
            if self.config.auto_open:
                import webbrowser
                webbrowser.open(f"http://localhost:{self.config.port}")
            
            return {
                'started': True,
                'port': self.config.port,
                'url': f"http://{self.config.host}:{self.config.port}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start web editor: {e}")
            return {'error': str(e)}
    
    async def _shutdown(self) -> Dict[str, Any]:
        """Stop the web server"""
        if not self.running:
            return {'already_stopped': True}
        
        try:
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
            
            self.running = False
            self.app = None
            self.runner = None
            self.site = None
            
            self.logger.info("Web editor stopped")
            
            announcer.announce(
                "EditorServicePolymorphic.stop",
                ["Web editor stopped"]
            )
            
            return {'stopped': True}
            
        except Exception as e:
            self.logger.error(f"Error stopping web editor: {e}")
            return {'error': str(e)}
    
    def _create_app(self) -> web.Application:
        """Create the web application with routes"""
        app = web.Application()
        
        # Universal polymorphic route handler
        async def polymorphic_handler(request):
            """Handle all routes polymorphically"""
            self.stats['requests_served'] += 1
            
            # Extract route info
            path = request.path
            method = request.method
            
            # Determine what's being requested
            if path == '/':
                html = self._generate_index_html()
            elif path == '/api/stats':
                data = database_service.ask("statistics")
                return web.json_response(data)
            elif path == '/api/tournaments':
                data = database_service.ask("tournaments")
                return web.json_response(data)
            elif path == '/api/organizations':
                data = database_service.ask("organizations") 
                return web.json_response(data)
            elif path == '/api/players':
                data = database_service.ask("players")
                return web.json_response(data)
            elif '/api/' in path:
                # Generic API handler
                query = path.replace('/api/', '')
                data = database_service.ask(query)
                return web.json_response(data)
            else:
                # Generate page based on path
                html = self._generate_page_html(path)
            
            return web.Response(text=html, content_type='text/html')
        
        # Add routes - all handled polymorphically
        app.router.add_get('/', polymorphic_handler)
        app.router.add_get('/api/{tail:.*}', polymorphic_handler)
        app.router.add_get('/{tail:.*}', polymorphic_handler)
        app.router.add_post('/api/{tail:.*}', polymorphic_handler)
        
        return app
    
    def _generate_index_html(self) -> str:
        """Generate the index page HTML"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Tournament Editor (Polymorphic)</title>
    <style>
        body {{
            font-family: -apple-system, system-ui, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2d3748;
            margin-bottom: 2rem;
        }}
        .status {{
            background: #f7fafc;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
        }}
        .links a {{
            display: inline-block;
            margin: 0.5rem;
            padding: 0.75rem 1.5rem;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            transition: transform 0.2s;
        }}
        .links a:hover {{
            transform: translateY(-2px);
            background: #5a67d8;
        }}
        .info {{
            margin-top: 2rem;
            padding: 1rem;
            background: #edf2f7;
            border-radius: 0.5rem;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 Tournament Editor (Polymorphic)</h1>
        
        <div class="status">
            <h2>Service Status</h2>
            <p>✅ Running on port {self.config.port}</p>
            <p>📊 Requests served: {self.stats['requests_served']}</p>
            <p>🔧 Mode: {self.config.mode.value}</p>
        </div>
        
        <div class="links">
            <h2>Quick Links</h2>
            <a href="/api/stats">Statistics</a>
            <a href="/api/tournaments">Tournaments</a>
            <a href="/api/organizations">Organizations</a>
            <a href="/api/players">Players</a>
        </div>
        
        <div class="info">
            <h3>Polymorphic Pattern</h3>
            <p>This service uses just 3 methods:</p>
            <ul>
                <li>editor.ask("stats") - Get information</li>
                <li>editor.tell("discord") - Format output</li>
                <li>editor.do("restart") - Perform actions</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    
    def _generate_page_html(self, path: str) -> str:
        """Generate HTML for any page"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{path.title()} - Tournament Editor</title>
    <style>
        body {{
            font-family: -apple-system, system-ui, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
    </style>
</head>
<body>
    <h1>{path.replace('/', ' ').title()}</h1>
    <p>This page is handled polymorphically.</p>
    <p>Path: {path}</p>
    <a href="/">Back to Home</a>
</body>
</html>"""
    
    async def _handle_route(self, route: str, request: Any) -> Any:
        """Handle a specific route request"""
        self.stats['requests_served'] += 1
        
        # This would be called when using: editor.do("handle", route="/api/stats")
        if '/api/' in route:
            query = route.replace('/api/', '')
            data = database_service.ask(query)
            return data
        
        return {'route': route, 'handled': True}
    
    # =========================================================================
    # OVERRIDES FOR BASE CLASS
    # =========================================================================
    
    def _get_capabilities(self) -> List[str]:
        """Return capabilities for discovery"""
        return [
            "Web-based tournament editor",
            f"Runs on port {self.config.port}",
            "Organization management",
            "Tournament viewing",
            "Player statistics",
            "RESTful API endpoints",
            "Polymorphic route handling",
            "Use do('start') to launch",
            "Use ask('running') to check status"
        ]
    
    def _get_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            'service': 'Web Editor (Polymorphic)',
            'pattern': 'ask/tell/do',
            'methods_replaced': 'All route handlers',
            'routes_now': 'Polymorphic handler',
            'examples': [
                "editor.do('start')",
                "editor.ask('running')",
                "editor.ask('stats')",
                "editor.tell('discord')",
                "editor.do('stop')"
            ]
        }


# Singleton instance
editor_polymorphic = EditorServicePolymorphic()

# For backward compatibility
editor_service = editor_polymorphic