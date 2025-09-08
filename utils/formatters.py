"""
formatters.py - Format data from models for different output types
The models return data, formatters decide how to present it
"""
from typing import Dict, Any, Optional
from datetime import datetime


class PlayerFormatter:
    """Format player data for different output types"""
    
    @staticmethod
    def format_html(player_data: Dict[str, Any]) -> str:
        """Format player data as HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{player_data['name']} - Player Profile</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
                .navbar {{ background: #2c3e50; color: white; padding: 1rem 2rem; }}
                .navbar a {{ color: white; text-decoration: none; margin-right: 2rem; }}
                .container {{ max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }}
                .player-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                 color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                              gap: 1rem; margin-bottom: 2rem; }}
                .stat-card {{ background: white; padding: 1.5rem; border-radius: 8px; 
                             box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }}
                .stat-value {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
                .stat-label {{ color: #666; font-size: 0.9rem; margin-top: 0.5rem; }}
                .section {{ background: white; padding: 1.5rem; border-radius: 8px; 
                           margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #f5f5f5; padding: 0.75rem; text-align: left; }}
                td {{ padding: 0.75rem; border-bottom: 1px solid #f0f0f0; }}
                .placement-1 {{ background: #ffd700; color: #333; padding: 0.2rem 0.5rem; border-radius: 4px; }}
                .placement-2 {{ background: #c0c0c0; color: #333; padding: 0.2rem 0.5rem; border-radius: 4px; }}
                .placement-3 {{ background: #cd7f32; color: #333; padding: 0.2rem 0.5rem; border-radius: 4px; }}
                .placement-other {{ background: #e0e0e0; color: #333; padding: 0.2rem 0.5rem; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
                <a href="/players">All Players</a>
                <a href="/tournaments">Tournaments</a>
            </nav>
            
            <div class="container">
                <div class="player-header">
                    <h1>{player_data['name']}</h1>
                    <p>Ranked #{player_data.get('rank', 'N/A')} overall</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{player_data.get('total_points', 0)}</div>
                        <div class="stat-label">Total Points</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{player_data.get('tournament_count', 0)}</div>
                        <div class="stat-label">Tournaments</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{player_data.get('win_count', 0)}</div>
                        <div class="stat-label">Wins</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{player_data.get('win_rate', 0):.1f}%</div>
                        <div class="stat-label">Win Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{player_data.get('podium_rate', 0):.1f}%</div>
                        <div class="stat-label">Podium Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{player_data.get('avg_placement', 0):.1f}</div>
                        <div class="stat-label">Avg Placement</div>
                    </div>
                </div>
                
                {PlayerFormatter._format_recent_results_html(player_data.get('recent_results', []))}
                {PlayerFormatter._format_rivals_html(player_data.get('rivals', []))}
                {PlayerFormatter._format_tournament_history_html(player_data.get('tournament_history', []))}
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def _format_recent_results_html(results: list) -> str:
        """Format recent tournament results as HTML"""
        if not results:
            return ""
        
        html = '<div class="section"><h2>Recent Results</h2><table>'
        html += '<thead><tr><th>Tournament</th><th>Date</th><th>Placement</th><th>Attendees</th></tr></thead><tbody>'
        
        for result in results[:10]:  # Show last 10
            placement = result.get('placement', 'N/A')
            placement_class = 'placement-1' if placement == 1 else \
                            'placement-2' if placement == 2 else \
                            'placement-3' if placement == 3 else 'placement-other'
            
            html += f"""
            <tr>
                <td><strong>{result.get('tournament_name', 'Unknown')}</strong></td>
                <td>{result.get('date', 'N/A')}</td>
                <td><span class="{placement_class}">{placement}</span></td>
                <td>{result.get('attendees', 'N/A')}</td>
            </tr>
            """
        
        html += '</tbody></table></div>'
        return html
    
    @staticmethod
    def _format_rivals_html(rivals: list) -> str:
        """Format rivals section as HTML"""
        if not rivals:
            return ""
        
        html = '<div class="section"><h2>Main Rivals</h2><table>'
        html += '<thead><tr><th>Player</th><th>H2H Record</th><th>Meetings</th></tr></thead><tbody>'
        
        for rival in rivals[:5]:  # Top 5 rivals
            html += f"""
            <tr>
                <td><a href="/player/{rival.get('player_id', '')}">{rival.get('name', 'Unknown')}</a></td>
                <td>{rival.get('wins', 0)}-{rival.get('losses', 0)}</td>
                <td>{rival.get('meetings', 0)}</td>
            </tr>
            """
        
        html += '</tbody></table></div>'
        return html
    
    @staticmethod
    def _format_tournament_history_html(history: list) -> str:
        """Format full tournament history as HTML"""
        if not history:
            return ""
        
        html = '<div class="section"><h2>Tournament History</h2><table>'
        html += '<thead><tr><th>Tournament</th><th>Date</th><th>Placement</th><th>Points</th></tr></thead><tbody>'
        
        for tourney in history:
            placement = tourney.get('placement', 'N/A')
            placement_class = 'placement-1' if placement == 1 else \
                            'placement-2' if placement == 2 else \
                            'placement-3' if placement == 3 else 'placement-other'
            
            html += f"""
            <tr>
                <td>{tourney.get('name', 'Unknown')}</td>
                <td>{tourney.get('date', 'N/A')}</td>
                <td><span class="{placement_class}">{placement}</span></td>
                <td>{tourney.get('points', 0)}</td>
            </tr>
            """
        
        html += '</tbody></table></div>'
        return html
    
    @staticmethod
    def format_discord(player_data: Dict[str, Any]) -> str:
        """Format player data for Discord"""
        msg = f"**{player_data['name']}** - Player Profile\n"
        msg += f"Rank: #{player_data.get('rank', 'N/A')}\n"
        msg += f"```"
        msg += f"Total Points: {player_data.get('total_points', 0)}\n"
        msg += f"Tournaments: {player_data.get('tournament_count', 0)}\n"
        msg += f"Wins: {player_data.get('win_count', 0)}\n"
        msg += f"Win Rate: {player_data.get('win_rate', 0):.1f}%\n"
        msg += f"Avg Place: {player_data.get('avg_placement', 0):.1f}\n"
        msg += f"```"
        
        if player_data.get('recent_results'):
            msg += "\n**Recent Results:**\n"
            for r in player_data['recent_results'][:5]:
                msg += f"• {r.get('tournament_name', 'Unknown')}: {r.get('placement', 'N/A')}\n"
        
        return msg
    
    @staticmethod
    def format_json(player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return player data as JSON-ready dict"""
        return player_data


class TournamentFormatter:
    """Format tournament data for different output types"""
    
    @staticmethod
    def format_html(tournament_data: Dict[str, Any]) -> str:
        """Format tournament data as comprehensive HTML page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{tournament_data['name']} - Tournament Details</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 0; }}
                .navbar {{ background: #2c3e50; color: white; padding: 1rem 2rem; }}
                .navbar a {{ color: white; text-decoration: none; margin-right: 2rem; }}
                .container {{ max-width: 1400px; margin: 2rem auto; padding: 0 1rem; }}
                .tournament-header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                     color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                              gap: 1rem; margin-bottom: 2rem; }}
                .stat-card {{ background: white; padding: 1.5rem; border-radius: 8px; 
                             box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }}
                .stat-value {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
                .stat-label {{ color: #666; font-size: 0.9rem; margin-top: 0.5rem; }}
                .section {{ background: white; padding: 1.5rem; border-radius: 8px; 
                           margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .top-8-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }}
                .placement-card {{ background: #f8f9fa; padding: 1rem; border-radius: 6px; border-left: 4px solid #667eea; }}
                .placement-1 {{ border-left-color: #ffd700 !important; background: #fffef0 !important; }}
                .placement-2 {{ border-left-color: #c0c0c0 !important; background: #f8f8f8 !important; }}
                .placement-3 {{ border-left-color: #cd7f32 !important; background: #fff8f0 !important; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #f5f5f5; padding: 0.75rem; text-align: left; }}
                td {{ padding: 0.75rem; border-bottom: 1px solid #f0f0f0; }}
                .insights-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }}
                .insight-card {{ background: #e8f4fd; padding: 1rem; border-radius: 6px; }}
                .trophy {{ font-size: 2rem; }}
                .map-container {{ height: 300px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; }}
            </style>
        </head>
        <body>
            <nav class="navbar">
                <a href="/">← Home</a>
                <a href="/tournaments">Tournaments</a>
                <a href="/players">Players</a>
                <a href="/organizations">Organizations</a>
            </nav>
            
            <div class="container">
                <div class="tournament-header">
                    <h1><span class="trophy">🏆</span> {tournament_data['name']}</h1>
                    <p style="font-size: 1.2rem; margin: 0.5rem 0;">
                        📅 {tournament_data['date']} • 📍 {tournament_data['location']} • 
                        👥 {tournament_data['attendees']} attendees
                    </p>
                    <p style="opacity: 0.9;">Organized by {tournament_data['organization']}</p>
                    {f'<p style="background: rgba(255,215,0,0.2); padding: 0.5rem 1rem; border-radius: 20px; display: inline-block;">⭐ Major Tournament</p>' if tournament_data.get('is_major') else ''}
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{tournament_data.get('total_entrants', 0)}</div>
                        <div class="stat-label">Total Entrants</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{tournament_data.get('completion_rate', 0):.1f}%</div>
                        <div class="stat-label">Completion Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{tournament_data.get('performance_metrics', {}).get('competitive_level', 'Regional')}</div>
                        <div class="stat-label">Tournament Level</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{tournament_data.get('performance_metrics', {}).get('average_points', 0)}</div>
                        <div class="stat-label">Avg Points</div>
                    </div>
                </div>
                
                {TournamentFormatter._format_top_8_html(tournament_data.get('top_8', []))}
                {TournamentFormatter._format_bracket_insights_html(tournament_data.get('bracket_insights', {}))}
                {TournamentFormatter._format_all_results_html(tournament_data.get('all_placements', []))}
                {TournamentFormatter._format_geographic_data_html(tournament_data.get('geographic_data', {}))}
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def _format_top_8_html(top_8: list) -> str:
        """Format top 8 results as beautiful cards"""
        if not top_8:
            return '''<div class="section">
                <h2>🏅 Top 8</h2>
                <p style="color: #666; text-align: center; padding: 2rem;">
                    No top 8 placement data available for this tournament yet.<br>
                    This tournament may not have been fully processed or completed.
                </p>
            </div>'''
        
        html = '<div class="section"><h2>🏅 Tournament Top 8</h2><div class="top-8-grid">'
        
        for result in top_8:
            placement = result.get('placement', 'N/A')
            player = result.get('player', 'Unknown')
            player_id = result.get('player_id', '')
            points = result.get('points', 0)
            
            card_class = f'placement-card placement-{placement}' if placement <= 3 else 'placement-card'
            
            trophy_emoji = "🥇" if placement == 1 else "🥈" if placement == 2 else "🥉" if placement == 3 else f"#{placement}"
            
            html += f'''
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 1.5rem; font-weight: bold;">{trophy_emoji}</div>
                        <div style="font-size: 1.2rem; margin: 0.5rem 0;">
                            <a href="/player/{player_id}" style="color: inherit; text-decoration: none; font-weight: bold;">{player}</a>
                        </div>
                        <div style="color: #666;">
                            {f"${points}" if points > 0 else "No prize"}
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        html += '</div></div>'
        return html
    
    @staticmethod
    def _format_bracket_insights_html(insights: dict) -> str:
        """Format tournament analytics and insights"""
        if not insights:
            return ""
        
        html = '<div class="section"><h2>🧠 Tournament Analytics</h2><div class="insights-grid">'
        
        html += f'''
        <div class="insight-card">
            <h4>🎯 Competitive Dynamics</h4>
            <p><strong>Upsets:</strong> {insights.get('upset_count', 0)} surprising results</p>
            <p><strong>Veterans:</strong> {insights.get('veteran_count', 0)} experienced players in top 8</p>
            <p><strong>Newcomers:</strong> {insights.get('newcomer_count', 0)} fresh faces made top 8</p>
        </div>
        <div class="insight-card">
            <h4>📊 Tournament Health</h4>
            <p>Mix of veteran experience and new talent indicates a healthy competitive scene</p>
        </div>
        '''
        
        html += '</div></div>'
        return html
    
    @staticmethod
    def _format_all_results_html(all_results: list) -> str:
        """Format complete tournament results"""
        if not all_results:
            return ""
        
        html = '<div class="section"><h2>📋 Complete Results</h2>'
        
        if len(all_results) > 20:
            html += '<p style="color: #666; margin-bottom: 1rem;">Showing top 20 results. Tournament had excellent participation!</p>'
        
        html += '<table><thead><tr><th>Place</th><th>Player</th><th>Prize</th></tr></thead><tbody>'
        
        for result in all_results[:20]:  # Limit to top 20 for page performance
            placement = result.get('placement', 'N/A')
            player = result.get('player', 'Unknown')
            player_id = result.get('player_id', '')
            points = result.get('points', 0)
            
            html += f'''
            <tr>
                <td><strong>#{placement}</strong></td>
                <td><a href="/player/{player_id}" style="color: inherit; text-decoration: none;">{player}</a></td>
                <td>{f"${points}" if points > 0 else "No prize"}</td>
            </tr>
            '''
        
        html += '</tbody></table></div>'
        return html
    
    @staticmethod
    def _format_geographic_data_html(geo_data: dict) -> str:
        """Format geographic and venue information"""
        if not geo_data:
            return ""
        
        coords = geo_data.get('coordinates')
        
        html = '<div class="section"><h2>📍 Location & Venue Info</h2>'
        
        if coords:
            lat, lng = coords
            html += f'''
            <div class="map-container">
                <p>🗺️ Tournament Location: {lat:.3f}, {lng:.3f}</p>
                <p>Venue Quality: {geo_data.get('venue_quality', 'Standard')}</p>
            </div>
            '''
        else:
            html += '<p>Geographic data not available for this tournament.</p>'
        
        html += '</div>'
        return html
    
    @staticmethod
    def format_discord(tournament_data: Dict[str, Any]) -> str:
        """Format tournament data for Discord"""
        msg = f"**{tournament_data['name']}** - Tournament Details\\n"
        msg += f"📅 {tournament_data['date']} • 📍 {tournament_data['location']}\\n"
        msg += f"👥 {tournament_data['attendees']} attendees\\n"
        msg += f"```"
        msg += f"Entrants: {tournament_data.get('total_entrants', 0)}\\n"
        msg += f"Completion: {tournament_data.get('completion_rate', 0):.1f}%\\n"
        msg += f"Level: {tournament_data.get('performance_metrics', {}).get('competitive_level', 'Regional')}\\n"
        msg += f"```"
        
        if tournament_data.get('top_8'):
            msg += "\\n**Top 8:**\\n"
            for result in tournament_data['top_8'][:4]:  # Show top 4 in Discord
                trophy = "🥇" if result['placement'] == 1 else "🥈" if result['placement'] == 2 else "🥉" if result['placement'] == 3 else f"#{result['placement']}"
                msg += f"{trophy} {result['player']} ({result['points']} pts)\\n"
        
        return msg