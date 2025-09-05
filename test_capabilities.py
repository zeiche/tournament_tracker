#!/usr/bin/env python3
"""
Test that Claude now knows its capabilities
"""

from enhanced_database_context import EnhancedDatabaseContext

def show_capabilities():
    context = EnhancedDatabaseContext.get_comprehensive_context("test")
    db_info = context['database_info']
    
    print("=" * 70)
    print("CLAUDE NOW KNOWS IT CAN:")
    print("=" * 70)
    
    print(f"\n1. COUNT ORGANIZATIONS:")
    print(f"   Total: {db_info['statistics']['total_organizations']} organizations")
    print(f"   Has list of: {len(db_info.get('top_organizations', []))} organizations with details")
    
    print(f"\n2. SHOW TOURNAMENT STANDINGS:")
    print(f"   Has standings for: {db_info['statistics']['tournaments_with_standings']} tournaments")
    print(f"   Most recent {len(db_info.get('tournaments_with_standings', []))} tournaments with full top 8")
    
    print(f"\n3. PLAYER STATISTICS:")
    print(f"   Total players: {db_info['statistics']['total_players']}")
    print(f"   Top winners: {len(db_info.get('top_players_by_wins', []))} players")
    print(f"   Top podium finishers: {len(db_info.get('top_players_by_podiums', []))} players")
    
    print(f"\n4. TOURNAMENT INFO:")
    print(f"   Total tournaments: {db_info['statistics']['total_tournaments']}")
    print(f"   Recent tournaments with details: {len(db_info.get('recent_tournaments', []))}")
    
    print(f"\n5. VENUE STATISTICS:")
    print(f"   Top venues: {len(db_info.get('top_venues', []))} venues with event counts")
    
    print(f"\n6. GAMES/EVENTS:")
    print(f"   Different games/events: {len(db_info.get('games_and_events', []))}")
    
    print(f"\n7. TRENDS:")
    print(f"   Monthly data points: {len(db_info.get('monthly_trends', []))}")
    
    print("\n" + "=" * 70)
    print("Claude is explicitly told where to find each type of data!")

if __name__ == "__main__":
    show_capabilities()