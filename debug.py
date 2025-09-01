#!/usr/bin/env python3
"""
debug.py - Session Cache Issue Testing
Creates fresh database, tests save/reload cycle, proves fix works
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_fresh_database():
    """Create fresh database or wipe existing one"""
    db_path = 'tournament_tracker.db'
    
    if os.path.exists(db_path):
        print(f"Database exists - removing {db_path}")
        os.remove(db_path)
    
    print(f"Creating fresh database: {db_path}")
    
    # Initialize database_utils (single source of truth)
    from database_utils import init_db
    engine, Session = init_db(f'sqlite:///{db_path}')
    
    print("✅ Fresh database initialized")
    return engine, Session

def create_test_organizations():
    """Create test organizations with problematic names"""
    print("\nCreating test organizations...")
    
    from models import Organization, OrganizationContact
    
    test_orgs = [
        {
            'normalized_key': 'user@email.com',
            'display_name': 'user@email.com',
            'contacts': ['user@email.com']
        },
        {
            'normalized_key': 'discord:abc123',
            'display_name': 'https://discord.gg/abc123',
            'contacts': ['https://discord.gg/abc123']
        },
        {
            'normalized_key': 'fgc@gmail.com',
            'display_name': 'fgc@gmail.com',
            'contacts': ['fgc@gmail.com']
        },
        {
            'normalized_key': 'team_liquid',
            'display_name': 'Team Liquid',
            'contacts': ['Team Liquid']
        }
    ]
    
    for org_data in test_orgs:
        # Create organization
        org = Organization(
            normalized_key=org_data['normalized_key'],
            display_name=org_data['display_name']
        )
        org.save()
        
        # Add contacts
        for contact in org_data['contacts']:
            contact_obj = OrganizationContact(
                organization_id=org.id,
                contact_value=contact,
                contact_type='email' if '@' in contact else 'discord' if 'discord' in contact else 'name'
            )
            contact_obj.save()
        
        print(f"   Created: {org_data['display_name']}")
    
    print(f"✅ Created {len(test_orgs)} test organizations")

def test_session_cache_issue():
    """Test the session cache issue and fix"""
    print("\n" + "="*60)
    print("SESSION CACHE TESTING")
    print("="*60)
    
    from database_utils import get_all_organizations, save_organization_name
    from models import Organization
    
    # Test Case 1: Show current state
    print("\n--- TEST 1: Initial State ---")
    orgs = get_all_organizations()
    test_org = next(org for org in orgs if org['normalized_key'] == 'user@email.com')
    print(f"Current display name: '{test_org['display_name']}'")
    
    # Test Case 2: Use database_utils save function (should work with our fix)
    print("\n--- TEST 2: Database Utils Save ---")
    print("Saving via database_utils.save_organization_name()...")
    success = save_organization_name('user@email.com', 'Test Organization Fixed')
    print(f"Save result: {success}")
    
    # Reload and check if change is visible
    orgs_after = get_all_organizations()
    test_org_after = next(org for org in orgs_after if org['normalized_key'] == 'user@email.com')
    print(f"Display name after save: '{test_org_after['display_name']}'")
    
    if test_org_after['display_name'] == 'Test Organization Fixed':
        print("✅ PASS: database_utils save + reload works correctly")
    else:
        print("❌ FAIL: Session cache issue persists")
    
    # Test Case 3: Simulate editor's current approach (using models directly)
    print("\n--- TEST 3: Simulate Editor Approach ---")
    print("Using Organization.find_by() + org.save() like editor does...")
    
    org_direct = Organization.find_by(normalized_key='discord:abc123')
    print(f"Current name: '{org_direct.display_name}'")
    
    org_direct.display_name = 'Discord Gaming Community'
    org_direct.save()
    print("Saved via org.save()")
    
    # Reload using same method editor uses
    org_reloaded = Organization.find_by(normalized_key='discord:abc123')
    print(f"Reloaded name: '{org_reloaded.display_name}'")
    
    if org_reloaded.display_name == 'Discord Gaming Community':
        print("✅ PASS: Direct model approach works")
    else:
        print("❌ FAIL: Direct model approach has cache issues")
    
    # Test Case 4: Load all organizations like editor does
    print("\n--- TEST 4: Load All Organizations ---")
    all_orgs = Organization.all()
    discord_org = next(org for org in all_orgs if org.normalized_key == 'discord:abc123')
    print(f"Organization.all() shows: '{discord_org.display_name}'")
    
    if discord_org.display_name == 'Discord Gaming Community':
        print("✅ PASS: Organization.all() sees updated data")
    else:
        print("❌ FAIL: Organization.all() shows stale data")

def test_multiple_changes():
    """Test multiple rapid changes like editor workflow"""
    print("\n--- TEST 5: Multiple Rapid Changes ---")
    
    from database_utils import save_organization_name, get_all_organizations
    
    changes = [
        ('user@email.com', 'Email User Gaming'),
        ('fgc@gmail.com', 'FGC Gmail Community'),
        ('discord:abc123', 'Discord Community Final')
    ]
    
    print("Making multiple changes...")
    for normalized_key, new_name in changes:
        save_organization_name(normalized_key, new_name)
        print(f"   Changed {normalized_key} -> {new_name}")
    
    # Load all and verify
    print("Verifying all changes...")
    all_orgs = get_all_organizations()
    
    all_correct = True
    for normalized_key, expected_name in changes:
        org = next(org for org in all_orgs if org['normalized_key'] == normalized_key)
        actual_name = org['display_name']
        if actual_name == expected_name:
            print(f"   ✅ {normalized_key}: '{actual_name}'")
        else:
            print(f"   ❌ {normalized_key}: got '{actual_name}', expected '{expected_name}'")
            all_correct = False
    
    if all_correct:
        print("✅ PASS: All multiple changes persisted correctly")
    else:
        print("❌ FAIL: Some changes lost or cached incorrectly")

def main():
    """Run all session cache tests"""
    print("🧪 SESSION CACHE DEBUGGING SCRIPT")
    print("This script tests the session cache fix in database_utils.py")
    
    try:
        # Setup fresh environment
        engine, Session = setup_fresh_database()
        create_test_organizations()
        
        # Run tests
        test_session_cache_issue()
        test_multiple_changes()
        
        print("\n" + "="*60)
        print("🎯 SUMMARY:")
        print("If all tests pass, database_utils.py session cache fix works")
        print("Next step: Update editor.py to use save_organization_name()")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test script failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

