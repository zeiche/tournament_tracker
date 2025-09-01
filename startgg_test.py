"""
startgg_test.py - Start.gg Testing Module
Isolated testing functions for start.gg synchronization
"""
from log_utils import log_info, log_debug, log_error, init_logging, LogLevel
from database_utils import init_db, get_summary_stats
from startgg_sync import StartGGSyncClient, TournamentSyncProcessor

def test_startgg_sync():
    """Test start.gg synchronization"""
    log_info("=" * 60, "test")
    log_info("TESTING START.GG SYNC", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test API client
        log_info("TEST 1: Initialize API client", "test")
        client = StartGGSyncClient()
        log_info("API client initialized", "test")
        
        # Test tournament fetch (small batch for testing)
        log_info("TEST 2: Fetch tournaments", "test")
        tournaments = client.fetch_tournaments(year_filter=True)
        
        if tournaments:
            log_info(f"Fetched {len(tournaments)} tournaments", "test")
            
            # Show sample tournament
            sample = tournaments[0]
            log_info(f"Sample tournament: {sample.get('name')} ({sample.get('numAttendees')} attendees)", "test")
        else:
            log_error("No tournaments fetched", "test")
            return
        
        # Test processing (just first few tournaments)
        log_info("TEST 3: Process sample tournaments", "test")
        processor = TournamentSyncProcessor(page_size=10)
        
        # Process just first 3 tournaments for testing
        test_tournaments = tournaments[:3]
        processor.process_tournaments(test_tournaments)
        
        stats = processor.sync_stats
        if stats['tournaments_processed'] > 0:
            log_info(f"Processed {stats['tournaments_processed']} test tournaments", "test")
        else:
            log_error("No tournaments processed", "test")
        
        # Test database state
        log_info("TEST 4: Verify database state", "test")
        db_stats = get_summary_stats()
        log_info(f"Database now has: {db_stats['total_organizations']} orgs, {db_stats['total_tournaments']} tournaments", "test")
        
        log_info("start.gg sync test completed successfully", "test")
        
    except Exception as e:
        log_error(f"start.gg sync test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_api_client_only():
    """Test just the API client without database operations"""
    log_info("Testing API client only", "test")
    
    try:
        client = StartGGSyncClient()
        tournaments = client.fetch_tournaments(year_filter=True)
        
        if tournaments:
            log_info(f"API test successful: {len(tournaments)} tournaments fetched", "test")
            print(f"Sample tournament data:")
            sample = tournaments[0]
            print(f"  ID: {sample.get('id')} (type: {type(sample.get('id'))})")
            print(f"  Name: {sample.get('name')}")
            print(f"  Attendees: {sample.get('numAttendees')}")
            print(f"  Contact: {sample.get('primaryContact')}")
            return tournaments
        else:
            log_error("API test failed: No tournaments returned", "test")
            return None
            
    except Exception as e:
        log_error(f"API test failed: {e}", "test")
        return None

def test_processor_only(sample_data):
    """Test just the processor with sample data"""
    log_info("Testing processor only", "test")
    
    try:
        processor = TournamentSyncProcessor(page_size=5)
        processor.process_tournaments(sample_data)
        
        stats = processor.sync_stats
        log_info(f"Processor test: {stats['tournaments_processed']} processed", "test")
        return stats
        
    except Exception as e:
        log_error(f"Processor test failed: {e}", "test")
        return None

def debug_tournament_id_types():
    """Debug tournament ID data types from start.gg"""
    log_info("Debugging tournament ID types from start.gg", "test")
    
    try:
        client = StartGGSyncClient()
        tournaments = client.fetch_tournaments(year_filter=True)
        
        if tournaments:
            print("Tournament ID Type Analysis:")
            for i, tournament in enumerate(tournaments[:5]):  # Check first 5
                tournament_id = tournament.get('id')
                print(f"  Tournament {i+1}: {tournament_id} (type: {type(tournament_id)})")
            
            # Check if we can convert to string safely
            print("\nID Conversion Test:")
            test_id = tournaments[0].get('id')
            print(f"  Original: {test_id} (type: {type(test_id)})")
            print(f"  As String: '{str(test_id)}' (type: {type(str(test_id))})")
            
            return tournaments
        else:
            log_error("No tournaments to analyze", "test")
            return None
            
    except Exception as e:
        log_error(f"ID type debug failed: {e}", "test")
        return None

if __name__ == "__main__":
    # Initialize logging
    init_logging(console=True, level=LogLevel.DEBUG, debug_file="sync_test.txt")
    
    # Initialize database
    init_db()
    
    # Run tests
    print("Testing start.gg synchronization...")
    
    # First test API only
    print("\n1. Testing API Client:")
    tournaments = test_api_client_only()
    
    if tournaments:
        print("\n2. Debugging ID Types:")
        debug_tournament_id_types()
        
        print("\n3. Testing Full Sync:")
        test_startgg_sync()

