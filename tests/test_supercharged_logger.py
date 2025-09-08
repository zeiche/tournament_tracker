#!/usr/bin/env python3
"""
test_supercharged_logger.py - Demonstrate the power of database-backed object logging
"""
import time
from datetime import datetime, timedelta
from supercharged_logger import logger, log, log_object, log_performance, with_context, with_correlation


def demo_basic_logging():
    """Show basic logging capabilities"""
    print("\n📝 Basic Logging Demo")
    print("-"*40)
    
    logger.debug("Debug message - normally hidden")
    logger.info("Information message")
    logger.warning("Warning: Something might be wrong")
    logger.error("Error occurred!", category='demo')
    
    print("✅ Basic logs written to database (not files!)")


def demo_object_logging():
    """Show how we can log full Python objects"""
    print("\n🎯 Object Logging Demo")
    print("-"*40)
    
    # Log a complex object
    complex_data = {
        'tournament': {
            'name': 'SoCal Regionals',
            'players': 256,
            'date': datetime.now(),
            'brackets': ['pools', 'top64', 'top8'],
            'venue': {'name': 'Convention Center', 'capacity': 5000}
        },
        'results': [
            {'player': 'WEST', 'placement': 1},
            {'player': 'Alex', 'placement': 2}
        ]
    }
    
    log_object("tournament_data", complex_data, category='tournament')
    
    # Log a custom class instance
    class Player:
        def __init__(self, name, wins):
            self.name = name
            self.wins = wins
            self.stats = {'kd_ratio': 2.5, 'games': 100}
    
    player = Player("WEST", 50)
    log_object("player_instance", player, category='player')
    
    print("✅ Complex Python objects stored in database!")


def demo_context_logging():
    """Show context-aware logging"""
    print("\n🔍 Context Logging Demo")
    print("-"*40)
    
    with with_context("tournament_sync"):
        logger.info("Starting tournament sync")
        
        with with_context("fetch_data"):
            logger.info("Fetching from API")
            time.sleep(0.1)  # Simulate work
            
        with with_context("process_results"):
            logger.info("Processing results")
            
            with with_context("calculate_rankings"):
                logger.info("Calculating new rankings")
                log_performance("ranking_calculation", 0.05)
        
        logger.info("Sync complete")
    
    print("✅ Nested contexts tracked in database!")


def demo_correlation():
    """Show correlated logging for tracking related operations"""
    print("\n🔗 Correlation Demo")
    print("-"*40)
    
    with with_correlation() as correlation_id:
        logger.info("User request received", category='request')
        logger.info("Validating input", category='validation')
        logger.info("Querying database", category='database')
        logger.info("Formatting response", category='response')
        
        print(f"✅ All logs correlated with ID: {correlation_id}")
        
        # Show how to retrieve correlated logs
        correlated_logs = logger.get_by_correlation(correlation_id)
        print(f"   Found {len(correlated_logs)} correlated log entries")


def demo_performance_logging():
    """Show performance tracking"""
    print("\n⚡ Performance Logging Demo")
    print("-"*40)
    
    operations = [
        ("database_query", 0.023),
        ("api_call", 0.156),
        ("data_processing", 0.045),
        ("cache_lookup", 0.002),
        ("render_response", 0.012)
    ]
    
    for op, duration in operations:
        log_performance(op, duration, 
                       rows_processed=100,
                       cache_hit=op == "cache_lookup")
    
    print("✅ Performance metrics stored with full context!")


def demo_exception_logging():
    """Show exception logging with full traceback"""
    print("\n🔥 Exception Logging Demo")
    print("-"*40)
    
    try:
        # Intentionally cause an error
        result = 1 / 0
    except Exception as e:
        logger.exception("Division by zero caught!", e, 
                        category='math_error',
                        user_input=0)
    
    try:
        # Another type of error
        data = {'key': 'value'}
        value = data['missing_key']
    except KeyError as e:
        logger.exception("Key error in data processing", e,
                        category='data_error',
                        available_keys=list(data.keys()))
    
    print("✅ Exceptions logged with full traceback and context!")


def demo_querying():
    """Show how to query logs from the database"""
    print("\n🔎 Query Demo")
    print("-"*40)
    
    # Query recent errors
    errors = logger.get_errors(limit=5)
    print(f"Recent errors: {len(errors)} found")
    for error in errors[:2]:
        print(f"  - {error['message']}")
    
    # Search logs
    results = logger.search("tournament", limit=5)
    print(f"\nSearch for 'tournament': {len(results)} results")
    
    # Get statistics
    stats = logger.get_statistics(since=datetime.now() - timedelta(minutes=5))
    print(f"\nStatistics (last 5 minutes):")
    print(f"  Total logs: {stats['total_logs']}")
    print(f"  Log levels: {stats['level_counts']}")
    if stats['top_modules']:
        print(f"  Top module: {stats['top_modules'][0]}")


def demo_snapshot():
    """Show system snapshot capability"""
    print("\n📸 System Snapshot Demo")
    print("-"*40)
    
    # Take a snapshot of current system state
    logger.take_snapshot("demo_snapshot")
    
    print("✅ System snapshot saved to database!")
    print("   Includes memory usage, active modules, etc.")


def show_benefits():
    """Show the benefits over file-based logging"""
    print("\n✨ BENEFITS OF DATABASE LOGGING")
    print("="*50)
    
    benefits = [
        "🚀 No more stupid files cluttering the filesystem",
        "🎯 Store entire Python objects, not just strings",
        "🔍 Full SQL querying capabilities",
        "📊 Instant analytics and statistics",
        "🔗 Correlation IDs to track related operations",
        "📸 System snapshots for debugging",
        "⚡ Performance metrics built-in",
        "🧹 Easy cleanup of old logs",
        "🎨 Rich context and metadata",
        "🔥 Full exception tracking with objects"
    ]
    
    for benefit in benefits:
        print(f"  {benefit}")
    
    print("\n📈 Database tables created:")
    print("  • log_entries - Main log storage")
    print("  • log_aggregations - Pre-computed analytics")
    print("  • log_snapshots - System state captures")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("🚀 SUPERCHARGED DATABASE LOGGER DEMO")
    print("="*60)
    
    # Run demos
    demo_basic_logging()
    demo_object_logging()
    demo_context_logging()
    demo_correlation()
    demo_performance_logging()
    demo_exception_logging()
    demo_querying()
    demo_snapshot()
    
    # Show benefits
    show_benefits()
    
    # Final statistics
    print("\n📊 FINAL STATISTICS")
    print("-"*40)
    stats = logger.get_statistics()
    print(f"Total logs created in this demo: {stats['total_logs']}")
    print(f"Log breakdown: {stats['level_counts']}")
    
    print("\n✅ Supercharged logger demo complete!")
    print("   All logs are in the database, ready to query!")
    print("   No files were harmed in the making of this demo 😄")


if __name__ == "__main__":
    main()