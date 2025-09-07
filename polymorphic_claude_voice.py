#!/usr/bin/env python3
"""
polymorphic_claude_voice.py - Polymorphic Claude connection for voice
Just ask(), tell(), do() - handles everything polymorphically
"""

from typing import Any, Dict, Optional
from capability_announcer import announcer
import json

class PolymorphicClaudeVoice:
    """
    Polymorphic Claude for voice calls - accepts ANYTHING
    """
    
    def __init__(self):
        # Announce ourselves
        announcer.announce(
            "PolymorphicClaudeVoice",
            [
                "I connect voice calls to Claude polymorphically",
                "I accept any input and figure out what you want",
                "No need for specific methods or APIs",
                "Just ask(), tell(), or do()"
            ]
        )
    
    def ask(self, question: Any) -> str:
        """
        Ask Claude ANYTHING - polymorphically processes for voice
        """
        # Announce the question
        announcer.announce(
            "CLAUDE_VOICE_ASK",
            [f"Voice asked: {question}"]
        )
        
        # Convert to string polymorphically
        q = str(question).lower()
        
        # Check for tournament queries polymorphically
        if any(word in q for word in ['player', 'top', 'ranking', 'best']):
            return self._get_player_info(question)
        
        if any(word in q for word in ['tournament', 'recent', 'latest', 'event']):
            return self._get_tournament_info(question)
        
        if any(word in q for word in ['stat', 'number', 'count', 'how many']):
            return self._get_stats(question)
        
        # Default polymorphic response
        return self._process_polymorphically(question)
    
    def tell(self, format: str = "voice") -> str:
        """
        Tell Claude's status in any format
        """
        if format == "voice":
            return "Claude is ready to answer tournament questions"
        return "PolymorphicClaudeVoice: Ready"
    
    def do(self, action: Any, **kwargs) -> Any:
        """
        Do anything with Claude polymorphically
        """
        # This is where Claude processes actions
        return self.ask(action)
    
    def _get_player_info(self, query: Any) -> str:
        """Get player info polymorphically"""
        try:
            from database import get_session
            from tournament_models import Player, TournamentPlacement
            
            with get_session() as session:
                # Get top players polymorphically
                placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.placement != None
                ).all()
                
                # Calculate points
                player_points = {}
                for p in placements:
                    if p.player and p.player.name:  # Check player exists
                        if p.player_id not in player_points:
                            player_points[p.player_id] = {
                                'name': p.player.name,
                                'points': 0
                            }
                        
                        if p.placement == 1:
                            player_points[p.player_id]['points'] += 10
                        elif p.placement == 2:
                            player_points[p.player_id]['points'] += 7
                        elif p.placement == 3:
                            player_points[p.player_id]['points'] += 5
                        elif p.placement == 4:
                            player_points[p.player_id]['points'] += 3
                        elif p.placement <= 8:
                            player_points[p.player_id]['points'] += 1
                
                if not player_points:
                    return "No player data available."
                
                # Sort and return top 8 for voice
                rankings = [(data['name'].split()[0] if data['name'] else "Unknown", data['points']) 
                           for data in player_points.values()]
                rankings.sort(key=lambda x: x[1], reverse=True)
                
                # Check what was asked
                q = str(query).lower()
                if '8' in q or 'eight' in q:
                    # Return top 8
                    response = "The top 8 players are: "
                    for i, (name, points) in enumerate(rankings[:8], 1):
                        if i == 8:
                            response += f"and {name} with {points} points."
                        else:
                            response += f"{name} {points} points. "
                else:
                    # Return top 3 for brevity
                    response = "The top players are: "
                    for i, (name, points) in enumerate(rankings[:3], 1):
                        response += f"{name} with {points} points. "
                
                return response
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            announcer.announce("CLAUDE_ERROR", [f"Database error: {error_detail}"])
            return f"Database error: {str(e)}"
    
    def _get_tournament_info(self, query: Any) -> str:
        """Get tournament info polymorphically"""
        try:
            from database import get_session
            from tournament_models import Tournament
            
            with get_session() as session:
                # Get recent tournaments
                tournaments = session.query(Tournament).order_by(
                    Tournament.start_date.desc()
                ).limit(3).all()
                
                if tournaments:
                    response = "Recent tournaments: "
                    for t in tournaments:
                        name = t.name.split()[0] if t.name else "Unknown"
                        response += f"{name} with {t.num_attendees or 0} players. "
                    return response
                else:
                    return "No recent tournaments found."
                    
        except Exception as e:
            announcer.announce("CLAUDE_ERROR", [f"Database error: {e}"])
            return "I couldn't get tournament information right now."
    
    def _get_stats(self, query: Any) -> str:
        """Get stats polymorphically"""
        try:
            from database import get_session
            from tournament_models import Tournament, Player, Organization
            
            with get_session() as session:
                t_count = session.query(Tournament).count()
                p_count = session.query(Player).count()
                o_count = session.query(Organization).count()
                
                return f"We track {t_count} tournaments, {p_count} players, and {o_count} organizations."
                
        except Exception as e:
            announcer.announce("CLAUDE_ERROR", [f"Database error: {e}"])
            return "I couldn't get statistics right now."
    
    def _process_polymorphically(self, input: Any) -> str:
        """
        Process anything polymorphically
        This is the ultimate fallback - accepts ANYTHING
        """
        # Convert input to string
        input_str = str(input)
        
        # Announce processing
        announcer.announce(
            "CLAUDE_POLYMORPHIC",
            [f"Processing polymorphically: {input_str[:50]}..."]
        )
        
        # Check length for voice optimization
        if len(input_str) < 10:
            return "Could you say more about what you'd like to know?"
        
        # Default helpful response
        return (
            "I can tell you about top players, recent tournaments, or statistics. "
            "What would you like to know?"
        )

# Global instance
_claude = None

def get_claude():
    """Get or create Claude instance"""
    global _claude
    if _claude is None:
        _claude = PolymorphicClaudeVoice()
    return _claude

# The polymorphic interface - accepts ANYTHING
def claude_voice_ask(input: Any) -> str:
    """
    The ONE function that handles ALL voice queries polymorphically
    """
    claude = get_claude()
    return claude.ask(input)