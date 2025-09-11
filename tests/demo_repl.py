#!/usr/bin/env python3
"""
demo_repl.py - Demonstration of the enhanced models in a REPL environment
Run with: python3 -i demo_repl.py
"""

from database_utils import init_db, get_session
from database.tournament_models import Tournament, Organization, Player, TournamentPlacement
from datetime import datetime

# Initialize database
init_db()
session = get_session().__enter__()

print("\n" + "="*60)
print("TOURNAMENT TRACKER - ENHANCED MODELS REPL")
print("="*60)
print("\nAvailable models: Tournament, Organization, Player, TournamentPlacement")
print("\n--- EXAMPLE QUERIES ---")
print()

# Quick examples
print("# Get upcoming tournaments:")
print(">>> upcoming = Tournament.upcoming(30)")
print(f">>> len(upcoming)")
print(f"{len(Tournament.upcoming(30))}")
print()

print("# Find a specific tournament:")
print(">>> t = Tournament.search('smash')[0]")
t = Tournament.search('smash')[0] if Tournament.search('smash') else None
if t:
    print(f">>> t.name")
    print(f"'{t.name}'")
    print(f">>> t.get_status()")
    print(f"'{t.get_status()}'")
    print(f">>> t.get_size_category()")
    print(f"'{t.get_size_category()}'")
    print(f">>> t.full_address")
    print(f"'{t.full_address}'")
    print()

print("# Get top organizations:")
print(">>> orgs = Organization.top_by_attendance(3)")
orgs = Organization.top_by_attendance(3)
print(f">>> for org in orgs:")
print(f"...     print(f'{{org.display_name}}: {{org.total_attendance}} attendees')")
for org in orgs:
    print(f"{org.display_name}: {org.total_attendance} attendees")
print()

print("# Find top players:")
print(">>> winners = Player.most_wins(3)")
winners = Player.most_wins(3)
print(f">>> for p in winners:")
print(f"...     print(f'{{p.gamer_tag}}: {{p.win_count}} wins ({{p.win_rate:.1f}}% rate)')")
for p in winners:
    print(f"{p.gamer_tag}: {p.win_count} wins ({p.win_rate:.1f}% rate)")
print()

print("# Get comprehensive stats:")
print(">>> org = orgs[0]")
org = orgs[0] if orgs else None
if org:
    print(f">>> stats = org.get_stats()")
    print(f">>> stats.keys()")
    stats = org.get_stats()
    print(list(stats.keys())[:10])
    print()

print("\n--- USEFUL QUERIES TO TRY ---")
print()
print("# Tournament queries:")
print("Tournament.upcoming(30)              # Next 30 days")
print("Tournament.recent(30)                 # Last 30 days")
print("Tournament.active()                   # Currently running")
print("Tournament.majors()                   # 100+ attendees")
print("Tournament.by_year(2024)              # Specific year")
print("Tournament.in_socal().all()           # SoCal tournaments")
print("Tournament.search('tekken')           # Search by name")
print()

print("# Organization queries:")
print("Organization.active()                 # Active organizations")
print("Organization.local()                  # Single-city orgs")
print("Organization.regional()               # Multi-city orgs")
print("Organization.search('gaming')        # Search by name")
print()

print("# Player queries:")
print("Player.top_earners(10)                # By prize money")
print("Player.most_wins(10)                  # By victories")
print("Player.active_players(30)             # Recently active")
print("Player.search('leo')                  # Search by tag/name")
print()

print("# For any tournament 't':")
print("t.get_status()                        # Current status")
print("t.get_size_category()                 # Size classification")
print("t.days_until()                        # Days until start")
print("t.is_in_socal()                       # Location check")
print("t.winner                              # Tournament winner")
print("t.top_8                               # Top 8 placements")
print("t.get_stats()                         # All statistics")
print("t.to_dict()                           # JSON-ready dict")
print()

print("# For any organization 'org':")
print("org.tournaments                       # All tournaments")
print("org.get_upcoming_tournaments()        # Upcoming events")
print("org.get_location_coverage()           # Cities breakdown")
print("org.get_retention_metrics()           # Player retention")
print("org.get_growth_rate()                 # YoY growth")
print("org.get_stats()                       # All statistics")
print()

print("# For any player 'p':")
print("p.tournaments_won                     # Victories")
print("p.get_recent_results(10)              # Recent placements")
print("p.get_head_to_head(other_player.id)   # H2H stats")
print("p.get_rivals()                        # Rival players")
print("p.get_improvement_trend()             # Performance trend")
print("p.get_stats()                         # All statistics")
print()

print("="*60)
print("You are now in interactive Python mode.")
print("Try any of the queries above!")
print("="*60)