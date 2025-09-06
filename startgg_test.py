"""
startgg_test.py - Start.gg Testing Module
Isolated testing functions for start.gg synchronization
"""
from log_manager import LogManager

# Initialize logger for this module
logger = LogManager().get_logger('startgg_test')
from database_utils import init_db, get_summary_stats
from startgg_service import startgg_service StartGGSyncClient, TournamentSyncProcessor

def test_startgg_sync():
    """Test start.gg synchronization"""
    logger.info("=" * 60)
    logger.info("TESTING START.GG SYNC")
    logger.info("=" * 60)
    
    try:
        # Test API client
        logger.info("TEST 1: Initialize API client")
        client = StartGGSyncClient()
        logger.info("API client initialized")
        
        # Test tournament fetch (small batch for testing)
        logger.info("TEST 2: Fetch tournaments")
        tournaments = client.fetch_tournaments(year_filter=True)
        
        if tournaments:
            logger.info(f"Fetched {len(tournaments)} tournaments")
            
            # Show sample tournament
            sample = tournaments[0]
            logger.info(f"Sample tournament: {sample.get('name')} ({sample.get('numAttendees')} attendees)")
        else:
            logger.error("No tournaments fetched")
            return
        
        # Test processing (just first few tournaments)
        logger.info("TEST 3: Process sample tournaments")
        processor = TournamentSyncProcessor(page_size=10)
        
        # Process just first 3 tournaments for testing
        test_tournaments = tournaments[:3]
        processor.process_tournaments(test_tournaments)
        
        stats = processor.sync_stats
        if stats['tournaments_processed'] > 0:
            logger.info(f"Processed {stats['tournaments_processed']} test tournaments")
        else:
            logger.error("No tournaments processed")
        
        # Test database state
        logger.info("TEST 4: Verify database state")
        db_stats = get_summary_stats()
        logger.info(f"Database now has: {db_stats['total_organizations']} orgs, {db_stats['total_tournaments']} tournaments")
        
        logger.info("start.gg sync test completed successfully")
        
    except Exception as e:
        logger.error(f"start.gg sync test failed: {e}")
        import traceback
        traceback.print_exc()

def test_api_client_only():
    """Test just the API client without database operations"""
    logger.info("Testing API client only")
    
    try:
        client = StartGGSyncClient()
        tournaments = client.fetch_tournaments(year_filter=True)
        
        if tournaments:
            logger.info(f"API test successful: {len(tournaments)} tournaments fetched")
            print(f"Sample tournament data:")
            sample = tournaments[0]
            print(f"  ID: {sample.get('id')} (type: {type(sample.get('id'))})")
            print(f"  Name: {sample.get('name')}")
            print(f"  Attendees: {sample.get('numAttendees')}")
            print(f"  Contact: {sample.get('primaryContact')}")
            return tournaments
        else:
            logger.error("API test failed: No tournaments returned")
            return None
            
    except Exception as e:
        logger.error(f"API test failed: {e}")
        return None

def test_processor_only(sample_data):
    """Test just the processor with sample data"""
    logger.info("Testing processor only")
    
    try:
        processor = TournamentSyncProcessor(page_size=5)
        processor.process_tournaments(sample_data)
        
        stats = processor.sync_stats
        logger.info(f"Processor test: {stats['tournaments_processed']} processed")
        return stats
        
    except Exception as e:
        logger.error(f"Processor test failed: {e}")
        return None

def debug_tournament_id_types():
    """Debug tournament ID data types from start.gg"""
    logger.info("Debugging tournament ID types from start.gg")
    
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
            logger.error("No tournaments to analyze")
            return None
            
    except Exception as e:
        logger.error(f"ID type debug failed: {e}")
        return None

if __name__ == "__main__":
    # Logger is initialized at module level
    
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

