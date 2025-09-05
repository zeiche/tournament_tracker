#!/usr/bin/env python3
"""
Demo script showing the power of the query wrapper system
Run: python3 demo_wrappers.py
"""

from db import players, tournaments, organizations, p, t, o

def demo():
    """Demonstrate the wrapper system capabilities"""
    
    print("=" * 60)
    print("TOURNAMENT TRACKER - Query Wrapper Demo")
    print("=" * 60)
    
    # Example 1: Natural language player queries
    print("\n📊 PLAYER QUERIES")
    print("-" * 40)
    
    # Find specific player
    west = players("west")
    if west:
        print(f"✓ Found player: {west.first().gamer_tag}")
        
        # Chain methods intuitively
        print(f"  • Tournaments played: {west.tournaments().count()}")
        print(f"  • Tournaments won: {west.wins().count()}")
        
        # Get detailed stats
        stats = west.stats()
        print(f"  • Total points: {stats['total_points']}")
        print(f"  • Win rate: {stats['win_rate']:.1f}%")
    
    # Top players
    print("\n🏆 Top 3 Players by Points:")
    for i, player in enumerate(players("top 3"), 1):
        print(f"  {i}. {player.gamer_tag}")
    
    # Example 2: Tournament queries
    print("\n📅 TOURNAMENT QUERIES")
    print("-" * 40)
    
    # Recent tournaments
    recent = tournaments("recent")
    print(f"✓ {recent.count()} recent tournaments")
    
    # Get stats
    stats = recent.stats()
    print(f"  • Total attendance: {stats['total_attendance']}")
    print(f"  • Average attendance: {stats['average_attendance']:.1f}")
    
    # Chain to get players
    recent_players = recent.players()
    print(f"  • Unique players: {recent_players.count()}")
    
    # Get winners
    recent_winners = recent.winners()
    print(f"  • Unique winners: {recent_winners.count()}")
    
    # Example 3: Organization queries
    print("\n🏢 ORGANIZATION QUERIES")
    print("-" * 40)
    
    # Find organization
    shark = organizations("shark")
    if shark:
        org = shark.first()
        if org:
            print(f"✓ Found: {org.display_name}")
            
            # Get their tournaments
            shark_tournaments = shark.tournaments()
            print(f"  • Runs {shark_tournaments.count()} tournaments")
            
            # Get stats
            org_stats = shark.stats()
            print(f"  • Total attendance: {org_stats.get('total_attendance', 0)}")
    
    # Example 4: Complex chaining
    print("\n🔗 ADVANCED CHAINING")
    print("-" * 40)
    
    # Top players' recent tournament wins
    print("Top 5 players' recent wins (last 60 days):")
    top5_recent_wins = players("top 5").recent(60).wins()
    print(f"  • {top5_recent_wins.count()} tournament wins")
    
    # Recent tournaments' top 8 finishers
    print("\nRecent tournaments' top 8:")
    recent_top8 = tournaments("recent").top_8()
    print(f"  • {len(recent_top8)} total top 8 placements")
    
    # Example 5: Using shortcuts
    print("\n⚡ SHORTCUTS")
    print("-" * 40)
    
    print("Using p(), t(), o() shortcuts:")
    print(f"  • p('west'): {p('west').count()} result(s)")
    print(f"  • t('recent'): {t('recent').count()} result(s)")
    print(f"  • o(): {o().count()} total organizations")
    
    # Example 6: Filtering and display
    print("\n📋 FILTERING & DISPLAY")
    print("-" * 40)
    
    # Get recent active players
    recent_active = players().recent(30)
    print(f"✓ {recent_active.count()} players active in last 30 days")
    
    # Display formatted output
    print("\nFormatted player display:")
    west_display = players("west").display()
    for line in west_display.strip().split('\n')[:3]:
        print(f"  {line}")
    
    print("\n" + "=" * 60)
    print("✅ Demo complete! The wrapper system provides:")
    print("  • Natural language queries: players('west')")
    print("  • Chainable methods: .tournaments().winners()")
    print("  • Statistics: .stats()")
    print("  • Filtering: .recent(30)")
    print("  • Shortcuts: p(), t(), o()")
    print("=" * 60)


if __name__ == "__main__":
    demo()