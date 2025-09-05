#!/usr/bin/env python3
"""
Test the enhanced database context
"""

from enhanced_database_context import EnhancedDatabaseContext
import json

def test_enhanced_context():
    # Test query about top-8
    query = "show me the top 8 for singles"
    context = EnhancedDatabaseContext.get_comprehensive_context(query)
    
    print("=" * 70)
    print("ENHANCED DATABASE CONTEXT TEST")
    print("=" * 70)
    print(f"Query: {query}\n")
    
    info = context['database_info']
    
    # Show statistics
    print("STATISTICS:")
    print(f"  Total Tournaments: {info['statistics']['total_tournaments']}")
    print(f"  Total Players: {info['statistics']['total_players']}")
    print(f"  Tournaments with Standings: {info['statistics']['tournaments_with_standings']}")
    print(f"  Total Placements Recorded: {info['statistics']['total_placements_recorded']}")
    
    # Show recent tournaments with standings
    print("\nRECENT TOURNAMENTS WITH TOP 8:")
    for t in info.get('tournaments_with_standings', [])[:3]:
        print(f"\n  {t['tournament_name']} ({t['date']})")
        for s in t.get('standings', []):
            print(f"    {s['placement']}. {s['player']} ({s['event']})")
    
    # Show top players
    print("\nTOP PLAYERS BY WINS:")
    for p in info.get('top_players_by_wins', [])[:5]:
        print(f"  {p['player']}: {p['first_place_finishes']} wins")
    
    # Show games/events
    print("\nGAMES/EVENTS IN DATABASE:")
    for e in info.get('games_and_events', [])[:5]:
        print(f"  {e['event_name']}: {e['tournaments_with_event']} tournaments, {e['unique_players']} players")
    
    print("\n" + "=" * 70)
    print("Claude now has access to ALL this comprehensive data!")
    print("It can answer questions about:")
    print("- Top 8 standings for any tournament")
    print("- Player rankings and performance")
    print("- Tournament history and attendance")
    print("- Organizations and venues")
    print("- Games and events")
    print("- Monthly trends and statistics")

if __name__ == "__main__":
    test_enhanced_context()