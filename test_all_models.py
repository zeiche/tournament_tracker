#!/usr/bin/env python3
"""
test_all_models.py - Comprehensive test of enhanced ORM models
Tests all new methods and properties
"""

import sys
import json
from datetime import datetime, timedelta
from database_utils import init_db, get_session
from tournament_models import Tournament, Organization, Player, TournamentPlacement
from log_utils import init_logging, log_info, log_error, LogLevel

def test_tournament_model():
    """Test all Tournament model enhancements"""
    print("\n" + "="*60)
    print("TESTING TOURNAMENT MODEL")
    print("="*60)
    
    with get_session() as session:
        # Get a sample tournament
        tournament = session.query(Tournament).first()
        if not tournament:
            print("No tournaments found")
            return
        
        print(f"\nTesting with: {tournament.name}")
        print("-" * 40)
        
        # Test date/time methods
        print("\n1. DATE/TIME METHODS:")
        print(f"   start_date: {tournament.start_date}")
        print(f"   end_date: {tournament.end_date}")
        print(f"   duration_days: {tournament.duration_days}")
        print(f"   duration_hours: {tournament.duration_hours}")
        print(f"   is_active: {tournament.is_active}")
        print(f"   is_upcoming: {tournament.is_upcoming}")
        print(f"   is_past: {tournament.is_past}")
        print(f"   days_until: {tournament.days_until()}")
        print(f"   days_since: {tournament.days_since()}")
        print(f"   get_month: {tournament.get_month()}")
        print(f"   get_weekday: {tournament.get_weekday()}")
        
        # Test state methods
        print("\n2. STATE METHODS:")
        print(f"   is_finished: {tournament.is_finished()}")
        print(f"   is_cancelled: {tournament.is_cancelled()}")
        print(f"   get_state_name: {tournament.get_state_name()}")
        print(f"   get_status: {tournament.get_status()}")
        
        # Test size methods
        print("\n3. SIZE METHODS:")
        print(f"   get_size_category: {tournament.get_size_category()}")
        print(f"   is_major: {tournament.is_major()}")
        print(f"   is_premier: {tournament.is_premier()}")
        print(f"   get_heatmap_weight: {tournament.get_heatmap_weight():.2f}")
        
        # Test location methods (from mixin)
        print("\n4. LOCATION METHODS:")
        print(f"   has_location: {tournament.has_location}")
        print(f"   has_full_address: {tournament.has_full_address}")
        print(f"   coordinates: {tournament.coordinates}")
        print(f"   city_state: {tournament.city_state}")
        print(f"   full_address: {tournament.full_address}")
        print(f"   is_in_socal: {tournament.is_in_socal()}")
        print(f"   is_in_california: {tournament.is_in_california()}")
        
        # Test placement methods
        print("\n5. PLACEMENT METHODS:")
        print(f"   winner: {tournament.winner.gamer_tag if tournament.winner else 'None'}")
        print(f"   top_8 count: {len(tournament.top_8)}")
        print(f"   has_player check: {tournament.has_player(1)}")
        
        # Test organization relationship
        print("\n6. ORGANIZATION:")
        org = tournament.organization
        print(f"   organization: {org.display_name if org else 'None'}")
        print(f"   contact_type: {tournament.get_contact_type()}")
        
        # Test URLs
        print("\n7. URLs:")
        print(f"   startgg_url: {tournament.get_startgg_url()}")
        print(f"   registration_url: {tournament.get_registration_url()}")
        
        # Test stats
        print("\n8. STATS:")
        stats = tournament.get_stats()
        print(f"   status: {stats['status']}")
        print(f"   size_category: {stats['size_category']}")
        print(f"   has_location: {stats['has_location']}")
        print(f"   placement_count: {stats['placement_count']}")
        print(f"   total_prize_pool: ${stats['total_prize_pool']}")
        
        # Test class methods
        print("\n9. CLASS METHODS:")
        print(f"   upcoming(30): {len(Tournament.upcoming(30))} tournaments")
        print(f"   recent(30): {len(Tournament.recent(30))} tournaments")
        print(f"   active(): {len(Tournament.active())} tournaments")
        print(f"   majors(): {len(Tournament.majors())} tournaments")
        print(f"   by_year(2024): {len(Tournament.by_year(2024))} tournaments")
        print(f"   search('smash'): {len(Tournament.search('smash'))} tournaments")

def test_organization_model():
    """Test all Organization model enhancements"""
    print("\n" + "="*60)
    print("TESTING ORGANIZATION MODEL")
    print("="*60)
    
    with get_session() as session:
        # Get a sample organization
        org = session.query(Organization).first()
        if not org:
            print("No organizations found")
            return
        
        print(f"\nTesting with: {org.display_name}")
        print("-" * 40)
        
        # Test contact methods
        print("\n1. CONTACT METHODS:")
        print(f"   contacts count: {len(org.contacts)}")
        print(f"   contact_types: {org.get_contact_types()}")
        print(f"   primary_contact: {org.get_primary_contact()}")
        
        # Test tournament relationships
        print("\n2. TOURNAMENT RELATIONSHIPS:")
        print(f"   tournament_count: {org.tournament_count}")
        print(f"   total_attendance: {org.total_attendance}")
        print(f"   average_attendance: {org.average_attendance:.1f}")
        print(f"   upcoming_tournaments: {len(org.get_upcoming_tournaments())}")
        print(f"   recent_tournaments: {len(org.get_recent_tournaments())}")
        print(f"   active_tournaments: {len(org.get_active_tournaments())}")
        
        largest = org.get_largest_tournament()
        if largest:
            print(f"   largest_tournament: {largest.name} ({largest.num_attendees} attendees)")
        
        # Test location analytics
        print("\n3. LOCATION ANALYTICS:")
        print(f"   unique_cities: {len(org.get_unique_cities())}")
        print(f"   unique_venues: {len(org.get_unique_venues())}")
        print(f"   is_local_org: {org.is_local_org()}")
        print(f"   is_regional_org: {org.is_regional_org()}")
        
        spread = org.get_geographic_spread()
        if spread:
            print(f"   geographic_spread: {spread:.1f} km")
        
        coverage = org.get_location_coverage()
        if coverage:
            print(f"   top_location: {list(coverage.keys())[0] if coverage else 'None'}")
        
        # Test temporal analytics
        print("\n4. TEMPORAL ANALYTICS:")
        print(f"   activity_span_days: {org.get_activity_span_days()}")
        freq = org.get_frequency()
        if freq:
            print(f"   frequency_per_month: {freq:.2f}")
        print(f"   consistency_score: {org.get_consistency_score():.1f}")
        
        monthly = org.get_monthly_distribution()
        if monthly:
            print(f"   busiest_month: {max(monthly, key=monthly.get) if monthly else 'None'}")
        
        # Test performance metrics
        print("\n5. PERFORMANCE METRICS:")
        growth = org.get_growth_rate()
        if growth:
            print(f"   growth_rate: {growth:.1f}%")
        
        retention = org.get_retention_metrics()
        print(f"   unique_players: {retention['total_unique_players']}")
        print(f"   retention_rate: {retention['retention_rate']}%")
        print(f"   loyal_players: {retention['loyal_players']}")
        
        # Test comprehensive stats
        print("\n6. COMPREHENSIVE STATS:")
        stats = org.get_stats()
        print(f"   total_tournaments: {stats['total_tournaments']}")
        print(f"   socal_tournaments: {stats['socal_tournaments']}")
        print(f"   major_tournaments: {stats['major_tournaments']}")
        print(f"   consistency_score: {stats['consistency_score']}")
        
        # Test class methods
        print("\n7. CLASS METHODS:")
        print(f"   search('gaming'): {len(Organization.search('gaming'))} orgs")
        print(f"   active(): {len(Organization.active())} orgs")
        print(f"   local(): {len(Organization.local())} orgs")
        print(f"   regional(): {len(Organization.regional())} orgs")

def test_player_model():
    """Test all Player model enhancements"""
    print("\n" + "="*60)
    print("TESTING PLAYER MODEL")
    print("="*60)
    
    with get_session() as session:
        # Get a sample player with placements
        player = session.query(Player).join(TournamentPlacement).first()
        if not player:
            print("No players with placements found")
            return
        
        print(f"\nTesting with: {player.gamer_tag}")
        print("-" * 40)
        
        # Test basic properties
        print("\n1. BASIC PROPERTIES:")
        print(f"   display_name: {player.display_name}")
        print(f"   has_real_name: {player.has_real_name}")
        print(f"   tournament_count: {player.tournament_count}")
        print(f"   total_placements: {player.total_placements}")
        
        # Test placement methods
        print("\n2. PLACEMENT METHODS:")
        print(f"   win_count: {player.win_count}")
        print(f"   podium_finishes: {player.podium_finishes}")
        print(f"   top_8_finishes: {player.top_8_finishes}")
        print(f"   best_placement: {player.get_best_placement()}")
        print(f"   worst_placement: {player.get_worst_placement()}")
        print(f"   average_placement: {player.get_average_placement():.2f}")
        print(f"   median_placement: {player.get_median_placement()}")
        
        dist = player.get_placement_distribution()
        if dist:
            print(f"   placement_distribution: {dict(list(dist.items())[:3])}")
        
        # Test earnings
        print("\n3. EARNINGS:")
        print(f"   total_earnings: ${player.total_earnings:.2f}")
        
        earnings_by_year = player.get_earnings_by_year()
        if earnings_by_year:
            recent_year = max(earnings_by_year.keys())
            print(f"   {recent_year} earnings: ${earnings_by_year[recent_year]:.2f}")
        
        highest = player.get_highest_earning()
        if highest:
            print(f"   highest_earning: {highest[0]} (${highest[1]:.2f})")
        
        # Test performance metrics
        print("\n4. PERFORMANCE METRICS:")
        print(f"   win_rate: {player.win_rate:.1f}%")
        print(f"   podium_rate: {player.podium_rate:.1f}%")
        print(f"   top_8_rate: {player.top_8_rate:.1f}%")
        print(f"   consistency_score: {player.get_consistency_score():.1f}")
        print(f"   improvement_trend: {player.get_improvement_trend()}")
        
        # Test event analysis
        print("\n5. EVENT ANALYSIS:")
        print(f"   singles_placements: {len(player.get_singles_placements())}")
        print(f"   doubles_placements: {len(player.get_doubles_placements())}")
        print(f"   best_event: {player.get_best_event()}")
        
        # Test temporal analysis
        print("\n6. TEMPORAL ANALYSIS:")
        print(f"   is_active (90 days): {player.is_active_player(90)}")
        print(f"   career_span_years: {player.get_career_span_years()}")
        print(f"   active_years: {player.get_active_years()}")
        
        recent = player.get_recent_results(3)
        if recent:
            print(f"   recent_results: {len(recent)} results")
            for r in recent[:2]:
                print(f"     - {r['tournament']}: #{r['placement']}")
        
        # Test location analysis
        print("\n7. LOCATION ANALYSIS:")
        locations = player.get_tournament_locations()
        print(f"   locations_played: {len(locations)} unique locations")
        print(f"   home_region: {player.get_home_region()}")
        
        travel = player.get_travel_distance()
        if travel:
            print(f"   travel_distance: {travel:.1f} km")
        
        # Test opponent analysis
        print("\n8. OPPONENT ANALYSIS:")
        opponents = player.get_common_opponents(min_encounters=2)
        print(f"   common_opponents: {len(opponents)} players")
        
        rivals = player.get_rivals(min_encounters=2)
        if rivals:
            print(f"   rivals: {len(rivals)} rivals")
            if rivals:
                rival = rivals[0]
                print(f"     - vs {rival['gamer_tag']}: {rival['wins']}-{rival['losses']}")
        
        # Test comprehensive stats
        print("\n9. COMPREHENSIVE STATS:")
        stats = player.get_stats()
        print(f"   total_tournaments: {stats['total_tournaments']}")
        print(f"   career_span_years: {stats['career_span_years']}")
        print(f"   improvement_trend: {stats['improvement_trend']}")
        
        # Test class methods
        print("\n10. CLASS METHODS:")
        print(f"   search('a'): {len(Player.search('a')[:10])} players")
        print(f"   top_earners(5): {len(Player.top_earners(5))} players")
        print(f"   most_wins(5): {len(Player.most_wins(5))} players")
        print(f"   active_players(90): {len(Player.active_players(90))} players")

def test_placement_model():
    """Test all TournamentPlacement model enhancements"""
    print("\n" + "="*60)
    print("TESTING TOURNAMENTPLACEMENT MODEL")
    print("="*60)
    
    with get_session() as session:
        # Get a sample placement
        placement = session.query(TournamentPlacement).first()
        if not placement:
            print("No placements found")
            return
        
        print(f"\nTesting with: {placement}")
        print("-" * 40)
        
        # Test basic properties
        print("\n1. BASIC PROPERTIES:")
        print(f"   prize_dollars: ${placement.prize_dollars:.2f}")
        print(f"   is_singles: {placement.is_singles}")
        print(f"   is_win: {placement.is_win}")
        print(f"   is_podium: {placement.is_podium}")
        print(f"   is_top_8: {placement.is_top_8}")
        print(f"   placement_name: {placement.get_placement_name()}")
        
        # Test points systems
        print("\n2. POINTS SYSTEMS:")
        print(f"   points_standard: {placement.get_points('standard')}")
        print(f"   points_evo: {placement.get_points('evo')}")
        print(f"   points_linear: {placement.get_points('linear')}")
        
        # Test tournament context
        print("\n3. TOURNAMENT CONTEXT:")
        print(f"   tournament_size: {placement.get_tournament_size()}")
        print(f"   placement_percentage: {placement.get_placement_percentage():.1f}%" if placement.get_placement_percentage() else "   placement_percentage: N/A")
        print(f"   players_beaten: {placement.get_players_beaten()}")
        print(f"   is_major_placement: {placement.is_major_placement()}")
        print(f"   is_premier_placement: {placement.is_premier_placement()}")
        
        # Test quality metrics
        print("\n4. QUALITY METRICS:")
        print(f"   quality_score: {placement.get_quality_score():.2f}")
        print(f"   relative_performance: {placement.get_relative_performance()}")
        
        prize_pct = placement.get_prize_percentage()
        if prize_pct:
            print(f"   prize_percentage: {prize_pct:.1f}%")
        
        # Test opponent analysis
        print("\n5. OPPONENT ANALYSIS:")
        others = placement.get_other_placements()
        print(f"   other_placements_count: {len(others)}")
        print(f"   players_above: {len(placement.get_players_above())}")
        print(f"   players_below: {len(placement.get_players_below())}")
        print(f"   closest_rivals: {len(placement.get_closest_rivals())}")
        
        # Test stats
        print("\n6. STATS:")
        stats = placement.get_stats()
        print(f"   placement: {stats['placement']}")
        print(f"   placement_name: {stats['placement_name']}")
        print(f"   quality_score: {stats['quality_score']}")
        print(f"   relative_performance: {stats['relative_performance']}")
        
        # Test class methods
        print("\n7. CLASS METHODS:")
        print(f"   wins(): {len(TournamentPlacement.wins())} wins")
        print(f"   podiums(): {len(TournamentPlacement.podiums())} podiums")
        print(f"   top_8s(): {len(TournamentPlacement.top_8s())} top 8s")
        print(f"   recent(30): {len(TournamentPlacement.recent(30))} recent")
        print(f"   at_majors(): {len(TournamentPlacement.at_majors())} at majors")
        print(f"   singles_only(): {len(TournamentPlacement.singles_only())} singles")

def test_json_serialization():
    """Test JSON serialization for all models"""
    print("\n" + "="*60)
    print("TESTING JSON SERIALIZATION")
    print("="*60)
    
    with get_session() as session:
        # Test Tournament
        tournament = session.query(Tournament).first()
        if tournament:
            t_dict = tournament.to_dict()
            t_json = tournament.to_json()
            print(f"\n1. Tournament to_dict keys: {len(t_dict.keys())} fields")
            print(f"   JSON length: {len(t_json)} chars")
            print(f"   Sample fields: {list(t_dict.keys())[:5]}")
        
        # Test Organization
        org = session.query(Organization).first()
        if org:
            o_dict = org.to_dict()
            o_json = org.to_json()
            print(f"\n2. Organization to_dict keys: {len(o_dict.keys())} fields")
            print(f"   JSON length: {len(o_json)} chars")
            print(f"   Has nested stats: {'stats' in o_dict}")
        
        # Test Player
        player = session.query(Player).first()
        if player:
            p_dict = player.to_dict()
            p_json = player.to_json()
            print(f"\n3. Player to_dict keys: {len(p_dict.keys())} fields")
            print(f"   JSON length: {len(p_json)} chars")
            print(f"   Has nested stats: {'stats' in p_dict}")
        
        # Test TournamentPlacement
        placement = session.query(TournamentPlacement).first()
        if placement:
            pl_dict = placement.to_dict()
            pl_json = placement.to_json()
            print(f"\n4. TournamentPlacement to_dict keys: {len(pl_dict.keys())} fields")
            print(f"   JSON length: {len(pl_json)} chars")

def main():
    """Run all tests"""
    # Initialize database and logging
    init_logging(console=True, level=LogLevel.INFO)
    init_db()
    
    print("\n" + "="*60)
    print("COMPREHENSIVE MODEL TEST SUITE")
    print("="*60)
    
    try:
        # Run all test suites
        test_tournament_model()
        test_organization_model()
        test_player_model()
        test_placement_model()
        test_json_serialization()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nThe enhanced models provide:")
        print("- Complete data access through Python methods")
        print("- Rich analytics and statistics")
        print("- Comprehensive relationship handling")
        print("- Full JSON serialization")
        print("- Intelligent query builders")
        print("\nEvery piece of data is now accessible through intuitive methods!")
        
    except Exception as e:
        log_error(f"Test failed: {e}", "test")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()