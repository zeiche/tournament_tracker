#!/usr/bin/env python3
"""
Web Search Interface for Tournament Tracker
Simple web UI that provides the same search functionality as Discord bot
Uses the unified Claude AI service as a bridge
Now uses ManagedService for unified service identity.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import html
import sys
import os
from typing import Dict, Any, List, Optional

# Add parent directory to path for claude_ai_service
sys.path.insert(0, '/home/ubuntu/claude')
sys.path.append('/home/ubuntu/claude/tournament_tracker')

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.web_search")

from polymorphic_core.service_identity import ManagedService
from claude_ai_service import claude_ai, process_message

# Import database and models
from database import session_scope
from database.tournament_models import Tournament, Player, Organization, TournamentPlacement
from search.conversational_search import ConversationalSearch
from formatters import PlayerFormatter, TournamentFormatter


class SearchWebHandler(BaseHTTPRequestHandler):
    """Web request handler for search interface"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/':
            self.serve_home()
        elif parsed.path == '/search':
            query_params = urllib.parse.parse_qs(parsed.query)
            search_query = query_params.get('q', [''])[0]
            if search_query:
                self.serve_search_results(search_query)
            else:
                self.serve_home()
        elif parsed.path == '/api/search':
            # JSON API endpoint
            query_params = urllib.parse.parse_qs(parsed.query)
            search_query = query_params.get('q', [''])[0]
            self.serve_api_search(search_query)
        else:
            self.send_error(404)
    
    def serve_home(self):
        """Serve the search home page"""
        content = """<!DOCTYPE html>
<html>
<head>
    <title>Tournament Tracker Search</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 { color: #333; }
        .search-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: 70%;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            padding: 12px 24px;
            font-size: 16px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 10px;
        }
        button:hover { background: #0056b3; }
        .examples {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .examples h2 { color: #555; }
        .examples ul { line-height: 1.8; }
        .examples code {
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }
        .features {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        .feature-box {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .feature-box h3 { color: #007bff; margin-top: 0; }
    </style>
</head>
<body>
    <h1>🔍 Tournament Tracker Search</h1>
    
    <div class="search-box">
        <form action="/search" method="get">
            <input type="text" name="q" placeholder="Search tournaments, players, organizations..." autofocus>
            <button type="submit">Search</button>
        </form>
        <p style="color: #666; margin-top: 10px;">
            Natural language search powered by the same engine as our Discord bot
        </p>
    </div>
    
    <div class="examples">
        <h2>What can you search for?</h2>
        
        <div class="features">
            <div class="feature-box">
                <h3>🏆 Tournaments</h3>
                <ul style="list-style: none; padding: 0;">
                    <li>• <code>recent tournaments</code></li>
                    <li>• <code>tournaments in August</code></li>
                    <li>• <code>events with over 50 attendance</code></li>
                    <li>• <code>smash tournaments</code></li>
                </ul>
            </div>
            
            <div class="feature-box">
                <h3>👤 Players</h3>
                <ul style="list-style: none; padding: 0;">
                    <li>• <code>top 10 players</code></li>
                    <li>• <code>stats for Monte</code></li>
                    <li>• <code>player rankings</code></li>
                    <li>• <code>show West</code></li>
                </ul>
            </div>
            
            <div class="feature-box">
                <h3>🏢 Organizations</h3>
                <ul style="list-style: none; padding: 0;">
                    <li>• <code>top organizations</code></li>
                    <li>• <code>Try-Hards events</code></li>
                    <li>• <code>organizations by attendance</code></li>
                    <li>• <code>venues in Riverside</code></li>
                </ul>
            </div>
            
            <div class="feature-box">
                <h3>📊 Analytics</h3>
                <ul style="list-style: none; padding: 0;">
                    <li>• <code>growth trends</code></li>
                    <li>• <code>tournament statistics</code></li>
                    <li>• <code>monthly attendance</code></li>
                    <li>• <code>venue analysis</code></li>
                </ul>
            </div>
        </div>
        
        <p style="margin-top: 20px; color: #666;">
            💡 <strong>Tip:</strong> This search uses the same natural language processing as our Discord bot. 
            Just type what you're looking for in plain English!
        </p>
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def serve_search_results(self, query: str):
        """Serve search results page"""
        # Perform the search
        results = self.perform_search(query)
        
        # Build HTML for results
        results_html = self.format_results_html(results, query)
        
        content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Search Results - Tournament Tracker</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .search-header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .search-header form {{
            display: flex;
            gap: 10px;
        }}
        input[type="text"] {{
            flex: 1;
            padding: 10px;
            font-size: 14px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        button {{
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        .results {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .result-section {{
            margin-bottom: 30px;
        }}
        .result-section h2 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .result-item {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        .result-item:last-child {{
            border-bottom: none;
        }}
        .result-title {{
            font-size: 18px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 5px;
        }}
        .result-meta {{
            color: #666;
            font-size: 14px;
        }}
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 10px;
            color: #007bff;
            text-decoration: none;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="search-header">
        <a href="/" class="back-link">← Back to Search</a>
        <form action="/search" method="get">
            <input type="text" name="q" value="{html.escape(query)}" placeholder="Search again...">
            <button type="submit">Search</button>
        </form>
    </div>
    
    <div class="results">
        {results_html}
    </div>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())
    
    def perform_search(self, query: str) -> Dict[str, Any]:
        """
        Perform search using same logic as Discord bot
        Returns structured results
        """
        results = {
            'query': query,
            'tournaments': [],
            'players': [],
            'organizations': [],
            'ai_response': None
        }
        
        try:
            # First try AI-powered search if available
            if claude_ai.is_enabled:
                ai_context = {
                    'source': 'web_search',
                    'query_type': 'search'
                }
                ai_result = process_message(query, ai_context)
                if ai_result['success']:
                    results['ai_response'] = ai_result['response']
            
            # Also do direct database search (same as Discord bot)
            with session_scope() as session:
                # Search tournaments
                tournaments = session.query(Tournament).filter(
                    Tournament.name.ilike(f"%{query}%")
                ).limit(10).all()
                
                for t in tournaments:
                    results['tournaments'].append({
                        'id': t.id,
                        'name': t.name,
                        'date': t.start_at_date if hasattr(t, 'start_at_date') else 'Unknown',
                        'attendees': t.num_attendees or 0,
                        'venue': t.venue_name,
                        'city': t.city
                    })
                
                # Search players
                players = session.query(Player).filter(
                    (Player.gamer_tag.ilike(f"%{query}%")) |
                    (Player.name.ilike(f"%{query}%"))
                ).limit(10).all()
                
                for p in players:
                    # Get basic stats
                    placement_count = session.query(TournamentPlacement).filter(
                        TournamentPlacement.player_id == p.id
                    ).count()
                    
                    results['players'].append({
                        'id': p.id,
                        'name': p.gamer_tag or p.name or 'Unknown',
                        'tournaments': placement_count
                    })
                
                # Search organizations
                orgs = session.query(Organization).filter(
                    Organization.display_name.ilike(f"%{query}%")
                ).limit(10).all()
                
                for o in orgs:
                    # Count tournaments
                    tournament_count = session.query(Tournament).filter(
                        Tournament.normalized_contact == o.normalized_key
                    ).count()
                    
                    results['organizations'].append({
                        'id': o.id,
                        'name': o.display_name,
                        'tournaments': tournament_count
                    })
                
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def format_results_html(self, results: Dict[str, Any], query: str) -> str:
        """Format search results as HTML"""
        html_parts = []
        
        # Show AI response if available
        if results.get('ai_response'):
            html_parts.append(f"""
                <div class="result-section">
                    <h2>🤖 AI Analysis</h2>
                    <div class="result-item">
                        <pre style="white-space: pre-wrap; font-family: inherit;">{html.escape(results['ai_response'][:1000])}</pre>
                    </div>
                </div>
            """)
        
        # Show tournaments
        if results['tournaments']:
            html_parts.append('<div class="result-section"><h2>🏆 Tournaments</h2>')
            for t in results['tournaments']:
                html_parts.append(f"""
                    <div class="result-item">
                        <div class="result-title">{html.escape(t['name'])}</div>
                        <div class="result-meta">
                            📅 {t['date']} | 
                            👥 {t['attendees']} attendees | 
                            📍 {html.escape(t.get('venue', 'Unknown venue') or 'Unknown venue')}
                            {', ' + html.escape(t['city']) if t.get('city') else ''}
                        </div>
                    </div>
                """)
            html_parts.append('</div>')
        
        # Show players
        if results['players']:
            html_parts.append('<div class="result-section"><h2>👤 Players</h2>')
            for p in results['players']:
                html_parts.append(f"""
                    <div class="result-item">
                        <div class="result-title">{html.escape(p['name'])}</div>
                        <div class="result-meta">
                            🎮 {p['tournaments']} tournament{'s' if p['tournaments'] != 1 else ''} played
                        </div>
                    </div>
                """)
            html_parts.append('</div>')
        
        # Show organizations
        if results['organizations']:
            html_parts.append('<div class="result-section"><h2>🏢 Organizations</h2>')
            for o in results['organizations']:
                html_parts.append(f"""
                    <div class="result-item">
                        <div class="result-title">{html.escape(o['name'])}</div>
                        <div class="result-meta">
                            🎯 {o['tournaments']} tournament{'s' if o['tournaments'] != 1 else ''} hosted
                        </div>
                    </div>
                """)
            html_parts.append('</div>')
        
        # No results message
        if not any([results['tournaments'], results['players'], results['organizations'], results.get('ai_response')]):
            html_parts.append(f"""
                <div class="no-results">
                    <h2>No results found</h2>
                    <p>No results found for "{html.escape(query)}"</p>
                    <p>Try using different keywords or check the spelling</p>
                </div>
            """)
        
        return ''.join(html_parts)
    
    def serve_api_search(self, query: str):
        """Serve JSON API search results"""
        results = self.perform_search(query)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(results, default=str).encode())


class WebSearchServiceManaged(ManagedService):
    """
    Web Search Service with unified service identity.
    Provides web UI for tournament tracker search functionality.
    """
    
    def __init__(self, port: int = 8083, host: str = '0.0.0.0'):
        super().__init__("web-search", "tournament-web-search")
        self.port = port
        self.host = host
        self.server = None
    
    def run(self):
        """Run the web search server"""
        server_address = (self.host, self.port)
        self.server = HTTPServer(server_address, SearchWebHandler)
        
        print(f"🔍 Starting Tournament Tracker Search Web UI on port {self.port}")
        print(f"🌐 Access at: http://localhost:{self.port}")
        print("📋 This provides the same search functionality as the Discord bot")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down search server...")
            if self.server:
                self.server.shutdown()


def run_search_server(port: int = 8083, host: str = '0.0.0.0'):
    """Legacy function for backward compatibility"""
    with WebSearchServiceManaged(port, host) as service:
        service.run()


def main():
    """Main function for running as a managed service"""
    import argparse
    parser = argparse.ArgumentParser(description='Tournament Tracker Web Search')
    parser.add_argument('--port', type=int, default=8083, help='Port to run on (default: 8083)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()
    
    with WebSearchServiceManaged(args.port, args.host) as service:
        service.run()


if __name__ == '__main__':
    main()