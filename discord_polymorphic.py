#!/usr/bin/env python3
"""
discord_polymorphic.py - Polymorphic Discord command handler
Shows how Discord commands can use the 3-method pattern
"""
from typing import Any, Optional
from database import get_session
from tournament_models import Tournament, Player, Organization
from tournament_models_simplified import simplify_existing_models
from capability_announcer import announcer


class PolymorphicDiscordHandler:
    """
    Handles Discord commands using the 3-method polymorphic pattern.
    Instead of hundreds of specific commands, we interpret intent.
    """
    
    def __init__(self):
        """Initialize and enable polymorphic models"""
        simplify_existing_models()
        announcer.announce(
            "Discord Polymorphic Handler",
            [
                "I understand natural language queries",
                "I use the 3-method pattern (ask/tell/do)",
                "I interpret intent, not rigid syntax"
            ],
            [
                "show tournament <name>",
                "who won <tournament>",
                "format <thing> for discord",
                "calculate <player> stats"
            ]
        )
    
    def process_command(self, message: str, context: dict = None) -> str:
        """
        Process a Discord command polymorphically.
        This is the magic - we interpret what the user wants.
        """
        msg = message.lower().strip()
        
        # Try to understand intent
        with get_session() as session:
            # Looking for tournament info?
            if any(word in msg for word in ['tournament', 'event', 'major']):
                return self._handle_tournament_query(msg, session)
            
            # Looking for player info?
            if any(word in msg for word in ['player', 'rank', 'win rate']):
                return self._handle_player_query(msg, session)
            
            # Looking for organization info?
            if any(word in msg for word in ['org', 'organization', 'host']):
                return self._handle_org_query(msg, session)
            
            # Asking about winners?
            if any(word in msg for word in ['won', 'winner', 'first', 'champion']):
                return self._handle_winner_query(msg, session)
            
            # Want something formatted?
            if any(word in msg for word in ['show', 'display', 'format']):
                return self._handle_format_query(msg, session)
            
            # Want to do something?
            if any(word in msg for word in ['sync', 'update', 'calculate']):
                return self._handle_action_query(msg, session)
            
            # Default: explain capabilities
            return self._explain_capabilities()
    
    def _handle_tournament_query(self, msg: str, session) -> str:
        """Handle tournament-related queries using polymorphic methods"""
        # Find a tournament (simplified - would use better matching)
        tournament = session.query(Tournament).first()
        if not tournament:
            return "No tournaments found in database"
        
        # Use the 3-method pattern!
        if 'attendance' in msg:
            result = tournament.ask('attendance')
            return f"{tournament.name}: {result} players"
        
        if 'winner' in msg or 'won' in msg:
            winner = tournament.ask('winner', session)
            if winner:
                return f"{tournament.name} winner: {winner.gamertag if hasattr(winner, 'gamertag') else winner}"
            return f"No winner recorded for {tournament.name}"
        
        if 'discord' in msg or 'format' in msg:
            return tournament.tell('discord')
        
        # Default: show brief info
        return tournament.tell('brief')
    
    def _handle_player_query(self, msg: str, session) -> str:
        """Handle player queries polymorphically"""
        player = session.query(Player).first()
        if not player:
            return "No players found"
        
        if 'stats' in msg or 'statistics' in msg:
            stats = player.ask('statistics')
            return player.tell('discord') + f"\nStats: {stats}"
        
        if 'recent' in msg:
            recent = player.ask('recent', session)
            return f"{player.gamertag}'s recent tournaments: {', '.join([t.name for t in recent[:3]])}"
        
        return player.tell('discord')
    
    def _handle_org_query(self, msg: str, session) -> str:
        """Handle organization queries polymorphically"""
        org = session.query(Organization).first()
        if not org:
            return "No organizations found"
        
        if 'attendance' in msg:
            attendance = org.ask('total attendance')
            return f"{org.display_name}: {attendance} total attendance"
        
        return org.tell('discord')
    
    def _handle_winner_query(self, msg: str, session) -> str:
        """Find winners polymorphically"""
        # Get most recent tournament
        tournament = session.query(Tournament).order_by(
            Tournament.start_date.desc()
        ).first()
        
        if tournament:
            winner = tournament.ask('winner', session)
            if winner:
                return f"🏆 {tournament.name} winner: {winner.gamertag if hasattr(winner, 'gamertag') else winner}"
        
        return "No tournament winners found"
    
    def _handle_format_query(self, msg: str, session) -> str:
        """Format things for Discord"""
        # Find what to format
        if 'tournament' in msg:
            t = session.query(Tournament).first()
            if t:
                return t.tell('discord')
        
        if 'player' in msg:
            p = session.query(Player).first()
            if p:
                return p.tell('discord')
        
        return "Specify what to format: tournament, player, or organization"
    
    def _handle_action_query(self, msg: str, session) -> str:
        """Perform actions polymorphically"""
        if 'sync' in msg:
            # Would call tournament.do('sync')
            return "Sync functionality would be triggered via tournament.do('sync')"
        
        if 'calculate' in msg:
            t = session.query(Tournament).first()
            if t:
                stats = t.do('calculate')
                return f"Calculated stats for {t.name}: {list(stats.keys())}"
        
        return "Action not recognized"
    
    def _explain_capabilities(self) -> str:
        """Explain the polymorphic system"""
        return """**Polymorphic Discord Commands**
        
Instead of memorizing commands, just ask naturally:
• "show tournament <name>" - Get tournament info
• "who won <tournament>" - Find winners  
• "player <name> stats" - Get player statistics
• "format <thing> for discord" - Get Discord formatting

The system uses 3 polymorphic methods:
• **ask()** - Query anything
• **tell()** - Format for output
• **do()** - Perform actions

Just describe what you want!"""


def demonstrate_polymorphic_discord():
    """Show how Discord would use polymorphic models"""
    handler = PolymorphicDiscordHandler()
    
    # Test various natural language queries
    test_queries = [
        "show tournament attendance",
        "who won the last tournament",
        "format player for discord",
        "calculate tournament stats"
    ]
    
    print("=" * 60)
    print("Polymorphic Discord Handler Demo")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        response = handler.process_command(query)
        print(response)


if __name__ == "__main__":
    # Initialize database
    from database import init_database
    init_database()
    
    demonstrate_polymorphic_discord()