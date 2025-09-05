#!/usr/bin/env python3
"""
db.py - Simple, intuitive database interface with method chaining

Usage:
    from db import players, tournaments, organizations, p, t, o
    
    # Get a player and their tournaments
    west = players("west")
    west_tournaments = west.tournaments()
    west_wins = west.wins()
    west_stats = west.stats()
    
    # Get recent tournaments and their players  
    recent = tournaments("recent")
    recent_players = recent.players()
    recent_winners = recent.winners()
    
    # Chain methods intuitively
    top_players_recent_wins = players("top 10").recent(30).wins()
    
    # Use shortcuts
    p("west").tournaments()  # Same as players("west").tournaments()
    t("recent").top_8()       # Same as tournaments("recent").top_8()
    o("shark").stats()        # Same as organizations("shark").stats()
"""

# Import everything from query_wrappers for a clean interface
from query_wrappers import (
    players, tournaments, organizations,
    p, t, o,
    PlayerWrapper, TournamentWrapper, OrganizationWrapper
)

# Additional convenience imports
from database import session_scope
from tournament_models import Player, Tournament, Organization, TournamentPlacement

__all__ = [
    # Main query functions
    'players', 'tournaments', 'organizations',
    # Shortcuts
    'p', 't', 'o',
    # Wrapper classes
    'PlayerWrapper', 'TournamentWrapper', 'OrganizationWrapper',
    # Database utilities
    'session_scope',
    # Models
    'Player', 'Tournament', 'Organization', 'TournamentPlacement'
]

# Quick test function
def test():
    """Quick test of the wrapper system"""
    print("Testing database wrapper system...")
    
    # Test player query
    west = players("west")
    if west:
        print(f"✓ Found player: {west.first().gamer_tag}")
        tournaments = west.tournaments()
        print(f"  - Played in {tournaments.count()} tournaments")
        wins = west.wins()
        print(f"  - Won {wins.count()} tournaments")
    else:
        print("✗ Player 'west' not found")
    
    # Test tournament query
    recent = tournaments("recent")
    print(f"\n✓ Found {recent.count()} recent tournaments")
    if recent:
        recent_players = recent.players()
        print(f"  - {recent_players.count()} unique players participated")
    
    # Test organization query
    orgs = organizations()
    print(f"\n✓ Found {orgs.count()} organizations")
    
    print("\nWrapper system is working! ✓")


if __name__ == "__main__":
    test()