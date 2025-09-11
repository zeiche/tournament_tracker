#!/usr/bin/env python3
"""
test_interactive.py - Interactive test of the enhanced models
"""

from database_utils import init_db, get_session
from database.tournament_models import Tournament, Organization, Player, TournamentPlacement

# Initialize database
init_db()

print("\n" + "="*60)
print("INTERACTIVE MODEL TESTING")
print("="*60)

with get_session() as session:
    # Test 1: Find upcoming tournaments in SoCal
    print("\n1. UPCOMING SOCAL TOURNAMENTS:")
    upcoming = Tournament.upcoming(30)
    socal_upcoming = [t for t in upcoming if t.is_in_socal()]
    print(f"   Found {len(socal_upcoming)} upcoming SoCal tournaments")
    for t in socal_upcoming[:3]:
        print(f"   - {t.name}")
        print(f"     {t.city_state}, {t.days_until()} days away")
        print(f"     Status: {t.get_status()}, Size: {t.get_size_category()}")
    
    # Test 2: Top organizations by various metrics
    print("\n2. TOP ORGANIZATIONS:")
    top_orgs = Organization.top_by_attendance(5)
    for i, org in enumerate(top_orgs, 1):
        stats = org.get_stats()
        print(f"   {i}. {org.display_name}")
        print(f"      Tournaments: {stats['total_tournaments']}, Attendance: {stats['total_attendance']}")
        print(f"      Cities: {stats['unique_cities']}, Consistency: {stats['consistency_score']:.1f}")
        print(f"      Growth: {stats['growth_rate']:.1f}%" if stats['growth_rate'] else "      Growth: N/A")
    
    # Test 3: Player analytics
    print("\n3. TOP PLAYERS BY WINS:")
    top_winners = Player.most_wins(5)
    for i, player in enumerate(top_winners, 1):
        stats = player.get_stats()
        print(f"   {i}. {player.gamer_tag}")
        print(f"      Wins: {stats['wins']}, Win Rate: {stats['win_rate']:.1f}%")
        print(f"      Tournaments: {stats['total_tournaments']}, Trend: {stats['improvement_trend']}")
    
    # Test 4: Major tournament analysis
    print("\n4. MAJOR TOURNAMENTS:")
    majors = Tournament.majors()
    print(f"   Found {len(majors)} major tournaments (100+ attendees)")
    
    recent_majors = [t for t in majors if t.is_past and t.days_since() and t.days_since() < 90]
    print(f"   Recent majors (last 90 days): {len(recent_majors)}")
    
    for t in recent_majors[:3]:
        print(f"   - {t.name}")
        print(f"     {t.num_attendees} attendees, {t.city_state}")
        winner = t.winner
        if winner:
            print(f"     Winner: {winner.gamer_tag}")
    
    # Test 5: Location-based queries
    print("\n5. LOCATION ANALYTICS:")
    la_tournaments = Tournament.in_city('Los Angeles', 'CA').all()
    print(f"   LA tournaments: {len(la_tournaments)}")
    
    socal_all = Tournament.in_socal().all()
    print(f"   Total SoCal tournaments: {len(socal_all)}")
    
    # Get a tournament with location and test distance
    t1 = Tournament.with_location().first()
    t2 = Tournament.with_location().offset(10).first()
    if t1 and t2 and t1.coordinates and t2.coordinates:
        distance = t1.distance_to(*t2.coordinates)
        print(f"   Distance between {t1.city} and {t2.city}: {distance:.1f} km")
    
    # Test 6: Find active players
    print("\n6. ACTIVE PLAYERS (last 30 days):")
    active = Player.active_players(30)
    print(f"   Found {len(active)} active players")
    
    for p in active[:3]:
        recent = p.get_recent_results(1)
        if recent:
            r = recent[0]
            print(f"   - {p.gamer_tag}: {r['tournament']} (#{r['placement']})")
    
    # Test 7: Organization retention metrics
    print("\n7. PLAYER RETENTION ANALYSIS:")
    for org in top_orgs[:2]:
        retention = org.get_retention_metrics()
        print(f"   {org.display_name}:")
        print(f"     Unique players: {retention['total_unique_players']}")
        print(f"     Retention rate: {retention['retention_rate']:.1f}%")
        print(f"     Loyal players (5+ events): {retention['loyal_players']}")
    
    # Test 8: Search functionality
    print("\n8. SEARCH TESTS:")
    smash_tournaments = Tournament.search('smash')
    print(f"   'smash' tournaments: {len(smash_tournaments)}")
    
    sf_tournaments = Tournament.search('street fighter')
    print(f"   'street fighter' tournaments: {len(sf_tournaments)}")
    
    gaming_orgs = Organization.search('gaming')
    print(f"   'gaming' organizations: {len(gaming_orgs)}")

print("\n" + "="*60)
print("✅ ALL INTERACTIVE TESTS COMPLETED")
print("="*60)