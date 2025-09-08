#!/usr/bin/env python3
"""
test_bonjour_updates.py - Test that all updated modules announce themselves properly
"""
from polymorphic_core import announcer

print("=" * 60)
print("TESTING BONJOUR ANNOUNCEMENTS FOR UPDATED MODULES")
print("=" * 60)

# Clear any existing announcements
announcer.announcements = []

print("\n1. Testing startgg_sync.py...")
try:
    import startgg_sync
    print("   ✅ Module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")

print("\n2. Testing database_service.py...")
try:
    import database_service
    print("   ✅ Module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")

print("\n3. Testing web_editor.py...")
try:
    import web_editor
    print("   ✅ Module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")

print("\n4. Testing tournament_operations.py...")
try:
    import tournament_operations
    print("   ✅ Module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")

print("\n5. Testing points_system.py...")
try:
    import points_system
    print("   ✅ Module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")

print("\n6. Testing visualizer.py...")
try:
    import visualizer
    print("   ✅ Module imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import: {e}")

print("\n" + "=" * 60)
print("COLLECTED ANNOUNCEMENTS:")
print("=" * 60)

if announcer.announcements:
    for i, announcement in enumerate(announcer.announcements, 1):
        print(f"\n{i}. {announcement['service']}")
        print("   Capabilities:")
        for cap in announcement['capabilities'][:3]:  # Show first 3
            print(f"   • {cap}")
        if len(announcement['capabilities']) > 3:
            print(f"   ... and {len(announcement['capabilities']) - 3} more")
else:
    print("No announcements collected!")

print("\n" + "=" * 60)
print(f"TOTAL SERVICES ANNOUNCED: {len(announcer.announcements)}")
print("=" * 60)

# Show what Claude would see
print("\nCLAUDE'S CONTEXT:")
print("-" * 40)
print(announcer.get_announcements_for_claude()[:500] + "...")