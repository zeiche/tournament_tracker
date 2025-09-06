#!/usr/bin/env python3
"""
test_enhanced_models.py - Test the enhanced ORM architecture with location mixins and methods
"""

import sys
from database_utils import init_db, get_session
from tournament_models import Tournament, Organization, Player, TournamentPlacement
from log_manager import LogManager

# Initialize logger for this module
logger = LogManager().get_logger('test_enhanced_models')

def test_location_features():
    """Test the new LocationMixin features"""
    print("\n" + "="*60)
    print("TESTING LOCATION FEATURES")
    print("="*60)
    
    with get_session() as session:
        # Test 1: Get tournaments with location data
        print("\n1. Testing Tournament.with_location():")
        tournaments_with_loc = Tournament.with_location().limit(5).all()
        print(f"   Found {len(tournaments_with_loc)} tournaments with location data")
        
        if tournaments_with_loc:
            t = tournaments_with_loc[0]
            print(f"   Example: {t.name}")
            print(f"   - Has location: {t.has_location}")
            print(f"   - Coordinates: {t.coordinates}")
            print(f"   - Full address: {t.full_address}")
            print(f"   - Is in SoCal: {t.is_in_socal()}")
            print(f"   - Heatmap weight: {t.get_heatmap_weight():.2f}")
        
        # Test 2: Get SoCal tournaments
        print("\n2. Testing Tournament.in_socal():")
        socal_tournaments = Tournament.in_socal().limit(5).all()
        print(f"   Found {len(socal_tournaments)} SoCal tournaments")
        
        # Test 3: Test region filtering
        print("\n3. Testing Tournament.in_region():")
        la_area = Tournament.in_region(33.5, 34.5, -118.5, -117.5).limit(5).all()
        print(f"   Found {len(la_area)} tournaments in LA area")
        
        # Test 4: Distance calculation
        if len(socal_tournaments) >= 2:
            print("\n4. Testing distance calculation:")
            t1 = socal_tournaments[0]
            t2 = socal_tournaments[1]
            if t1.coordinates and t2.coordinates:
                lat2, lng2 = t2.coordinates
                distance = t1.distance_to(lat2, lng2)
                if distance:
                    print(f"   Distance between {t1.city} and {t2.city}: {distance:.1f} km")

def test_tournament_methods():
    """Test new Tournament methods"""
    print("\n" + "="*60)
    print("TESTING TOURNAMENT METHODS")
    print("="*60)
    
    with get_session() as session:
        # Test 1: Upcoming tournaments
        print("\n1. Testing Tournament.upcoming():")
        upcoming = Tournament.upcoming(days=365)
        print(f"   Found {len(upcoming)} upcoming tournaments in next year")
        
        if upcoming:
            t = upcoming[0]
            print(f"   Next tournament: {t.name}")
            print(f"   - Days until: {t.days_until()}")
            print(f"   - Start date: {t.start_date}")
            print(f"   - Is upcoming: {t.is_upcoming}")
        
        # Test 2: Recent tournaments
        print("\n2. Testing Tournament.recent():")
        recent = Tournament.recent(days=90)
        print(f"   Found {len(recent)} recent tournaments (last 90 days)")
        
        # Test 3: By year
        print("\n3. Testing Tournament.by_year():")
        year_2024 = Tournament.by_year(2024)
        print(f"   Found {len(year_2024)} tournaments in 2024")
        
        # Test 4: Tournament dictionary conversion
        print("\n4. Testing Tournament.to_dict():")
        if recent:
            t = recent[0]
            t_dict = t.to_dict()
            print(f"   Tournament: {t_dict['name']}")
            print(f"   - Location data included: {'location' in t_dict}")
            print(f"   - Has coordinates: {t_dict['location']['has_location']}")
            print(f"   - Top 8 included: {len(t_dict.get('top_8', []))} placements")

def test_organization_methods():
    """Test new Organization methods"""
    print("\n" + "="*60)
    print("TESTING ORGANIZATION METHODS")
    print("="*60)
    
    with get_session() as session:
        # Test 1: Organization search
        print("\n1. Testing Organization.search():")
        results = Organization.search("FGC")
        print(f"   Found {len(results)} organizations matching 'FGC'")
        
        # Test 2: Organization stats
        print("\n2. Testing Organization.get_stats():")
        orgs = session.query(Organization).limit(3).all()
        for org in orgs:
            stats = org.get_stats()
            print(f"   {org.display_name}:")
            print(f"   - Total tournaments: {stats['total_tournaments']}")
            print(f"   - Total attendance: {stats['total_attendance']}")
            print(f"   - Average attendance: {stats['average_attendance']}")
            print(f"   - SoCal tournaments: {stats['socal_tournaments']}")
            print(f"   - Unique cities: {stats['unique_cities']}")
        
        # Test 3: Location coverage
        if orgs:
            print("\n3. Testing Organization.get_location_coverage():")
            org = orgs[0]
            coverage = org.get_location_coverage()
            if coverage:
                print(f"   {org.display_name} location breakdown:")
                for location, count in list(coverage.items())[:3]:
                    print(f"   - {location}: {count} tournaments")

def test_player_methods():
    """Test new Player methods"""
    print("\n" + "="*60)
    print("TESTING PLAYER METHODS")
    print("="*60)
    
    with get_session() as session:
        # Test 1: Player search
        print("\n1. Testing Player.search():")
        results = Player.search("a")  # Common letter to get some results
        print(f"   Found {len(results[:10])} players (showing first 10)")
        
        # Test 2: Top earners
        print("\n2. Testing Player.top_earners():")
        top_earners = Player.top_earners(5)
        for i, player in enumerate(top_earners, 1):
            earnings = player.total_winnings
            print(f"   {i}. {player.gamer_tag}: ${earnings/100:.2f}")
        
        # Test 3: Most wins
        print("\n3. Testing Player.most_wins():")
        most_wins = Player.most_wins(5)
        for i, player in enumerate(most_wins, 1):
            wins = len([p for p in player.placements if p.placement == 1])
            print(f"   {i}. {player.gamer_tag}: {wins} wins")
        
        # Test 4: Player stats
        if top_earners:
            print("\n4. Testing Player.get_stats():")
            player = top_earners[0]
            stats = player.get_stats()
            print(f"   {player.gamer_tag} stats:")
            print(f"   - Total placements: {stats['total_placements']}")
            print(f"   - Wins: {stats['wins']}")
            print(f"   - Win rate: {stats['win_rate']}%")
            print(f"   - Total earnings: ${stats['total_earnings_dollars']:.2f}")
            
            # Test recent results
            print("\n5. Testing Player.get_recent_results():")
            recent = player.get_recent_results(3)
            for result in recent:
                print(f"   - {result['tournament']}: #{result['placement']} ({result.get('event', 'Singles')})")

def test_heatmap_integration():
    """Test that models work with heatmap generation"""
    print("\n" + "="*60)
    print("TESTING HEATMAP INTEGRATION")
    print("="*60)
    
    # Import heatmap module
    from tournament_heatmap import get_location_data
    
    # Test getting location data with new methods
    print("\n1. Testing get_location_data() with enhanced models:")
    locations = get_location_data(limit=10, region='socal')
    print(f"   Got {len(locations)} SoCal tournament locations")
    
    if locations:
        loc = locations[0]
        print(f"   Example location data:")
        print(f"   - Name: {loc['name']}")
        print(f"   - Address: {loc.get('address', 'N/A')}")
        print(f"   - Weight: {loc.get('weight', 0):.2f}")
        print(f"   - Days until: {loc.get('days_until', 'N/A')}")
    
    # Test getting all locations
    print("\n2. Testing get_location_data() for all regions:")
    all_locations = get_location_data(limit=10, region='all')
    print(f"   Got {len(all_locations)} tournament locations (all regions)")

def main():
    """Run all tests"""
    # Initialize database
    init_db()
    
    print("\n" + "="*60)
    print("ENHANCED ORM ARCHITECTURE TEST SUITE")
    print("="*60)
    
    try:
        # Run test suites
        test_location_features()
        test_tournament_methods()
        test_organization_methods()
        test_player_methods()
        test_heatmap_integration()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nThe enhanced architecture provides:")
        print("- LocationMixin for any model with geographic data")
        print("- Rich methods on Tournament, Organization, and Player models")
        print("- Query builders for filtering by location, time, etc.")
        print("- JSON serialization with to_dict() methods")
        print("- Statistical analysis methods")
        print("- Integration with heatmap generation")
        print("\nModels now properly leverage SQLAlchemy's ORM capabilities!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()