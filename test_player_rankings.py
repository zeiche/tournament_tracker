#!/usr/bin/env python3
"""Test the updated player rankings without min_tournaments filter"""

from database_utils import get_player_rankings, get_session
from tournament_models import TournamentPlacement
from sqlalchemy import func, distinct

# Test that the function works without min_tournaments
print("Testing player rankings (no min_tournaments filter)...")
print("=" * 60)

# Get rankings for all events
rankings = get_player_rankings(limit=5)
print(f"\nTop 5 Players (All Events):")
for r in rankings:
    print(f"  {r['rank']}. {r['gamer_tag']}: {r['total_points']} pts ({r['tournament_count']} events)")

# Get rankings for Ultimate Singles only
rankings_singles = get_player_rankings(limit=5, event_filter='Ultimate Singles')
print(f"\nTop 5 Players (Ultimate Singles only):")
for r in rankings_singles:
    print(f"  {r['rank']}. {r['gamer_tag']}: {r['total_points']} pts ({r['tournament_count']} events)")

# Check how many events have 4+ players
print("\n" + "=" * 60)
print("Checking event player counts...")

with get_session() as session:
    # Count players per event
    event_counts = session.query(
        TournamentPlacement.event_name,
        TournamentPlacement.tournament_id,
        func.count(distinct(TournamentPlacement.player_id)).label('player_count')
    ).group_by(
        TournamentPlacement.event_name,
        TournamentPlacement.tournament_id
    ).all()
    
    # Analyze results
    total_events = len(event_counts)
    valid_events = len([e for e in event_counts if e[2] >= 4])
    invalid_events = len([e for e in event_counts if e[2] < 4])
    
    print(f"\nEvent Statistics:")
    print(f"  Total event instances: {total_events}")
    print(f"  Events with 4+ players: {valid_events}")
    print(f"  Events with <4 players: {invalid_events}")
    
    if invalid_events > 0:
        print(f"\nEvents with less than 4 players (excluded from rankings):")
        for event_name, tournament_id, player_count in event_counts:
            if player_count < 4:
                print(f"  - {event_name} in tournament {tournament_id}: {player_count} players")

print("\n✅ Test completed successfully!")