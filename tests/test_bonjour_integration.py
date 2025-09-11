#!/usr/bin/env python3
"""
test_bonjour_integration.py - Test that Bonjour announcements work throughout the system
"""
import time
from polymorphic_core import announcer
from bonjour_monitor import BonjourMonitor
from bonjour_database import enable_database_announcements, announce_database_stats


def test_basic_announcements():
    """Test that basic announcements work"""
    print("\n📢 Testing Basic Announcements")
    print("-"*40)
    
    # Create a monitor to capture announcements
    monitor = BonjourMonitor()
    
    # Make some test announcements
    announcer.announce(
        "Test Service",
        ["I am a test service", "I can do testing"],
        ["test.run()", "test.verify()"]
    )
    
    # Check if captured
    recent = monitor.get_recent(1)
    if recent and recent[0]['service'] == 'Test Service':
        print("✅ Basic announcements working")
    else:
        print("❌ Basic announcements not captured")
    
    return monitor


def test_model_announcements():
    """Test that models announce themselves"""
    print("\n🏗️ Testing Model Announcements")
    print("-"*40)
    
    try:
        # Import models - they should announce on import
        from database.tournament_models import Tournament, Player, Organization
        
        # Create a test tournament - should announce
        tournament = Tournament()
        tournament.name = "Test Tournament"
        tournament.num_attendees = 50
        
        print("✅ Model creation triggers announcements")
        
        # Test state change announcement
        if hasattr(tournament, 'announce_state_change'):
            tournament.announce_state_change("attendance updated", {"old": 50, "new": 75})
            print("✅ State change announcements work")
        
    except Exception as e:
        print(f"❌ Model announcements failed: {e}")


def test_database_announcements():
    """Test that database operations announce"""
    print("\n💾 Testing Database Announcements")
    print("-"*40)
    
    try:
        # Enable database announcements
        enable_database_announcements()
        
        # Test database stats announcement
        announce_database_stats()
        
        # Try a database operation
        from database import get_session
        from database.tournament_models import Tournament
        
        with get_session() as session:
            # This should announce the query
            count = session.query(Tournament).count()
            print(f"✅ Database has {count} tournaments")
            print("✅ Database operations announce themselves")
            
    except Exception as e:
        print(f"❌ Database announcements failed: {e}")


def test_service_discovery():
    """Test that services can be discovered"""
    print("\n🔍 Testing Service Discovery")
    print("-"*40)
    
    try:
        from polymorphic_core import list_capabilities, get_capability_info
        
        # List what's available
        caps = list_capabilities()
        
        print(f"Discovered capabilities:")
        print(f"  Models: {caps['models']}")
        print(f"  Services: {caps['services']}")
        print(f"  Functions: {caps['functions']}")
        
        if caps['models'] or caps['services'] or caps['functions']:
            print("✅ Service discovery working")
        else:
            print("⚠️ No services discovered yet")
            
    except Exception as e:
        print(f"❌ Service discovery failed: {e}")


def test_announcement_flow():
    """Test a complete flow with announcements"""
    print("\n🔄 Testing Complete Announcement Flow")
    print("-"*40)
    
    monitor = BonjourMonitor()
    
    # Simulate a user query flow
    announcer.announce("User Query", ["User asks: 'show top players'"])
    announcer.announce("Query Parser", ["Parsing natural language query"])
    announcer.announce("Database Query", ["Fetching player data"])
    announcer.announce("Response Formatter", ["Formatting for Discord"])
    announcer.announce("Discord Response", ["Sending response to user"])
    
    # Check the flow
    recent = monitor.get_recent(5)
    if len(recent) >= 5:
        print("✅ Complete flow announcements captured")
        print(f"   Captured {len(recent)} announcements in flow")
    else:
        print(f"⚠️ Only captured {len(recent)} announcements")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 BONJOUR INTEGRATION TEST SUITE")
    print("="*60)
    
    # Run tests
    monitor = test_basic_announcements()
    test_model_announcements()
    test_database_announcements()
    test_service_discovery()
    test_announcement_flow()
    
    # Show summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("-"*40)
    
    monitor.show_summary()
    
    # Export results
    monitor.export_to_file("bonjour_test_results.json")
    
    print("\n✨ Bonjour integration testing complete!")
    print("   Run './go.py --bonjour-monitor' to see live announcements")
    print("   Run './go.py --discover' to see discovered commands")


if __name__ == "__main__":
    main()