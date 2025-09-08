#!/usr/bin/env python3
"""
test_bonjour_models.py - Test that models now announce their operations
"""
from initialize_bonjour import initialize_all_bonjour
from polymorphic_core import announcer
from bonjour_monitor import BonjourMonitor
from database import session_scope
from tournament_models import Tournament, Player, Organization

# Initialize Bonjour first
initialize_all_bonjour()


def test_model_announcements():
    """Test that models announce their operations"""
    print("\n🎯 Testing Model Bonjour Announcements")
    print("="*50)
    
    # Create a monitor to capture announcements
    monitor = BonjourMonitor()
    
    # Test creating and saving a tournament
    print("\n1. Creating Tournament...")
    import uuid
    tournament = Tournament()
    tournament.id = f"test_{uuid.uuid4().hex[:8]}"
    tournament.name = "Test Tournament"
    tournament.num_attendees = 50
    
    print("2. Saving Tournament...")
    # Use the model's save() method which has announcements
    tournament.save()
    
    # Test creating and saving a player
    print("\n3. Creating Player...")
    player = Player()
    player.gamer_tag = "TestPlayer"
    
    print("4. Saving Player...")
    # Use the model's save() method which has announcements
    player.save()
    
    # Check announcements
    print("\n📊 Announcements captured:")
    recent = monitor.get_recent(20)
    
    for announcement in recent:
        service = announcement['service']
        if 'Database' in service or 'Tournament' in service or 'Player' in service:
            print(f"  • {service}: {announcement['capabilities'][0] if announcement['capabilities'] else 'announced'}")
    
    # Show summary
    print(f"\n✅ Total announcements: {sum(monitor.service_stats.values())}")
    print(f"✅ Unique services: {len(monitor.service_stats)}")
    
    # Top announcers
    if monitor.service_stats:
        print("\nTop announcers:")
        for service, count in monitor.service_stats.most_common(5):
            print(f"  • {service}: {count}")


if __name__ == "__main__":
    test_model_announcements()