#!/usr/bin/env python3
"""
test_unified_tabulator.py - Test the unified tabulation system
"""
import sys
from database import get_session
from unified_tabulator import UnifiedTabulator, RankingType
from database_service import database_service

print("=" * 60)
print("TESTING UNIFIED TABULATION SYSTEM")
print("=" * 60)

# Test 1: Basic tabulation with ties
print("\n1. Testing basic tabulation with tie handling:")
print("-" * 40)
test_data = [
    {'name': 'Player A', 'score': 100},
    {'name': 'Player B', 'score': 85},
    {'name': 'Player C', 'score': 85},  # Tie with B
    {'name': 'Player D', 'score': 70},
    {'name': 'Player E', 'score': 70},  # Tie with D
    {'name': 'Player F', 'score': 50},
]

ranked = UnifiedTabulator.tabulate(
    items=test_data,
    score_func=lambda x: x['score'],
    metadata_func=lambda x: {'name': x['name']}
)

for item in ranked:
    tie_marker = " (TIE)" if item.tie else ""
    print(f"Rank {item.rank}: {item.metadata['name']} - {item.score} points{tie_marker}")

# Test 2: Player rankings from database
print("\n2. Testing player rankings from database:")
print("-" * 40)
try:
    with get_session() as session:
        player_rankings = UnifiedTabulator.tabulate_player_points(session, limit=10)
        
        if player_rankings:
            print(f"Top {len(player_rankings)} players:")
            for item in player_rankings[:5]:
                tie = " (TIE)" if item.tie else ""
                print(f"  Rank {item.rank}: {item.metadata['gamer_tag']} - "
                      f"{int(item.score)} pts from {item.metadata['tournament_count']} events{tie}")
        else:
            print("  No player data found")
except Exception as e:
    print(f"  Error: {e}")

# Test 3: Organization rankings
print("\n3. Testing organization rankings by attendance:")
print("-" * 40)
try:
    with get_session() as session:
        org_rankings = UnifiedTabulator.tabulate_org_attendance(session, limit=10)
        
        if org_rankings:
            print(f"Top {len(org_rankings)} organizations by attendance:")
            for item in org_rankings[:5]:
                tie = " (TIE)" if item.tie else ""
                print(f"  Rank {item.rank}: {item.metadata['display_name']} - "
                      f"{int(item.score)} total attendance{tie}")
        else:
            print("  No organization data found")
except Exception as e:
    print(f"  Error: {e}")

# Test 4: Compare with old database_service methods
print("\n4. Testing backward compatibility with database_service:")
print("-" * 40)
try:
    # Old method (now using unified tabulator internally)
    old_player_rankings = database_service.get_player_rankings(limit=5)
    
    if old_player_rankings:
        print("Player rankings via database_service:")
        for r in old_player_rankings[:3]:
            print(f"  Rank {r['rank']}: {r.get('gamer_tag', r.get('name', 'Unknown'))} - "
                  f"{r['points']} pts")
    
    # Old org rankings method
    old_org_rankings = database_service.get_attendance_rankings(limit=5)
    
    if old_org_rankings:
        print("\nOrg rankings via database_service:")
        for r in old_org_rankings[:3]:
            print(f"  Rank {r['rank']}: {r['display_name']} - "
                  f"{r['total_attendance']} attendance")
except Exception as e:
    print(f"  Error: {e}")

# Test 5: Format output
print("\n5. Testing different output formats:")
print("-" * 40)
sample_ranked = ranked[:3]  # Use first 3 from test 1

print("Text format:")
print(UnifiedTabulator.format_rankings(sample_ranked, "text"))

print("\nMarkdown format:")
print(UnifiedTabulator.format_rankings(sample_ranked, "markdown"))

print("\nJSON format:")
print(UnifiedTabulator.format_rankings(sample_ranked, "json"))

print("\n" + "=" * 60)
print("UNIFIED TABULATION TEST COMPLETE")
print("=" * 60)