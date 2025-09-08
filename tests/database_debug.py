#!/usr/bin/env python3
"""
database_debug.py - Database Test Environment Setup
Initialize database and populate with January 2025 start.gg data
"""
import os
import sys
import calendar
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database(force_recreate=False):
    """Initialize database with proper schema"""
    from models import init_db
    
    db_path = 'tournament_tracker.db'
    
    if force_recreate and os.path.exists(db_path):
        print(f"Force recreate - removing existing database: {db_path}")
        os.remove(db_path)
    
    if os.path.exists(db_path):
        print(f"Database already exists: {db_path}")
    else:
        print(f"Creating new database: {db_path}")
    
    try:
        # Use models.init_db() - models own the database structure
        engine, Session = init_db()
        print("✅ Database initialization successful")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def populate_january_data():
    """Populate database with limited start.gg tournament data for testing"""
    try:
        # Check if startgg_sync exists and import it
        import importlib.util
        spec = importlib.util.find_spec('startgg_sync')
        if spec is None:
            print("❌ startgg_sync module not found")
            print("   Available modules to check:")
            
            # List available .py files
            import glob
            py_files = glob.glob("*.py")
            for f in py_files:
                if 'sync' in f or 'startgg' in f:
                    print(f"   - {f}")
            return False
        
        from startgg_service import startgg_service sync_from_startgg
        print("Syncing limited tournament data from start.gg for testing...")
        
        # Use existing sync function with limited scope for testing
        stats = sync_from_startgg(
            page_size=50,  # Smaller page size
            fetch_standings=False,  # Skip standings for faster setup
            standings_limit=0,
            limit_tournaments=10  # NEW: Limit to 10 tournaments
        )
        
        if stats:
            print("✅ start.gg sync completed successfully")
            print(f"   API calls: {stats['api_stats']['api_calls']}")
            print(f"   Tournaments processed: {stats['summary']['tournaments_processed']}")
            print(f"   Organizations created: {stats['summary']['organizations_created']}")
            print(f"   Processing time: {stats['summary']['total_processing_time']:.2f}s")
            return True
        else:
            print("❌ start.gg sync failed - trying fallback approach")
            
            # Fallback: try direct API call
            return try_direct_startgg_sync()
            
    except ImportError as e:
        print(f"❌ Cannot import sync_startgg: {e}")
        print("   Trying direct start.gg API approach...")
        return try_direct_startgg_sync()
    except Exception as e:
        print(f"❌ start.gg sync error: {e}")
        import traceback
        traceback.print_exc()
        return False

def try_direct_startgg_sync():
    """Fallback: Direct start.gg API call for 10 tournaments"""
    try:
        print("Attempting direct start.gg API call...")
        
        # Check if we can import startgg_query
        try:
            from startgg_service import startgg_service StartGGQueryClient
            client = StartGGQueryClient()
            
            tournaments, api_time, year_info = client.fetch_socal_tournaments(year_filter=True)
            print(f"✅ Fetched {len(tournaments)} tournaments{year_info} in {api_time:.2f}s")
            
            if tournaments:
                # Limit to first 10 for testing
                limited_tournaments = tournaments[:10]
                print(f"Using first {len(limited_tournaments)} tournaments for testing")
                
                # Process tournaments into database
                return process_tournaments_into_database(limited_tournaments)
            else:
                print("❌ No tournaments returned from API")
                return False
                
        except ImportError:
            print("❌ Cannot import startgg_query either")
            print("   Please check that start.gg integration modules exist")
            return False
            
    except Exception as e:
        print(f"❌ Direct API sync failed: {e}")
        return False

def process_tournaments_into_database(tournaments):
    """Process tournament data into database"""
    try:
        from models import init_db, Tournament, Organization, AttendanceRecord, OrganizationContact, normalize_contact
        import time
        
        processed = 0
        organizations_created = 0
        
        for tournament_data in tournaments:
            try:
                # Extract tournament info
                tournament_id = str(tournament_data.get('id', ''))
                name = tournament_data.get('name', 'Unknown Tournament')
                num_attendees = tournament_data.get('numAttendees', 0)
                primary_contact = tournament_data.get('primaryContact', '')
                
                if not tournament_id or not primary_contact:
                    continue
                
                # Create tournament
                existing_tournament = Tournament.find(tournament_id)
                if not existing_tournament:
                    normalized_contact = normalize_contact(primary_contact)
                    
                    tournament = Tournament(
                        id=tournament_id,
                        name=name,
                        num_attendees=num_attendees,
                        primary_contact=primary_contact,
                        normalized_contact=normalized_contact,
                        tournament_state=tournament_data.get('state', 3),
                        start_at=tournament_data.get('startAt'),
                        end_at=tournament_data.get('endAt'),
                        city=tournament_data.get('city'),
                        addr_state=tournament_data.get('addrState'),
                        venue_name=tournament_data.get('venueName'),
                        short_slug=tournament_data.get('shortSlug'),
                        url=tournament_data.get('url'),
                        sync_timestamp=int(time.time())
                    )
                    tournament.save()
                    processed += 1
                    
                    # Create organization if needed
                    org = Organization.find_by(normalized_key=normalized_contact)
                    if not org:
                        org = Organization(
                            normalized_key=normalized_contact,
                            display_name=primary_contact  # Keep original for testing
                        )
                        org.save()
                        organizations_created += 1
                        
                        # Add contact
                        contact_type = 'email' if '@' in primary_contact else 'discord' if 'discord' in primary_contact.lower() else 'name'
                        contact = OrganizationContact(
                            organization_id=org.id,
                            contact_value=primary_contact,
                            contact_type=contact_type,
                            is_primary=1
                        )
                        contact.save()
                    
                    # Create attendance record
                    if num_attendees > 0:
                        attendance_record = AttendanceRecord(
                            tournament_id=tournament.id,
                            organization_id=org.id,
                            attendance=num_attendees
                        )
                        attendance_record.save()
                    
                    print(f"   ✅ {name} ({num_attendees} attendees) - {primary_contact}")
                
            except Exception as e:
                print(f"   ❌ Error processing tournament {name}: {e}")
                continue
        
        print(f"✅ Processed {processed} tournaments, created {organizations_created} organizations")
        return processed > 0
        
    except Exception as e:
        print(f"❌ Error processing tournaments: {e}")
        return False

def show_database_stats():
    """Display current database statistics"""
    from database_utils import get_summary_stats, get_attendance_rankings
    
    try:
        stats = get_summary_stats()
        
        print("\n" + "="*50)
        print("DATABASE STATISTICS")
        print("="*50)
        print(f"Organizations: {stats['total_organizations']}")
        print(f"Tournaments: {stats['total_tournaments']}")
        print(f"Total Attendance: {stats['total_attendance']:,}")
        
        # Show top organizations
        print(f"\nTop 10 Organizations:")
        rankings = get_attendance_rankings(limit=10)
        
        for i, org in enumerate(rankings, 1):
            print(f"   {i:2d}. {org['display_name'][:40]:<40} {org['total_attendance']:>6,} attendance")
        
        print("="*50)
        
        return stats
        
    except Exception as e:
        print(f"❌ Failed to get database stats: {e}")
        return None

def identify_problematic_names():
    """Show organizations with email/Discord names that need cleaning"""
    from database_utils import get_all_organizations
    
    try:
        all_orgs = get_all_organizations()
        
        email_orgs = []
        discord_orgs = []
        clean_orgs = []
        
        for org in all_orgs:
            name = org['display_name']
            if '@' in name:
                email_orgs.append(org)
            elif 'discord' in name.lower():
                discord_orgs.append(org)
            else:
                clean_orgs.append(org)
        
        print(f"\n" + "="*50)
        print("ORGANIZATION NAME ANALYSIS")
        print("="*50)
        print(f"Total organizations: {len(all_orgs)}")
        print(f"Email addresses: {len(email_orgs)}")
        print(f"Discord handles: {len(discord_orgs)}")
        print(f"Clean names: {len(clean_orgs)}")
        
        print(f"\nProblematic email names (sample):")
        for org in email_orgs[:5]:
            print(f"   - {org['display_name']} ({org['total_attendance']} attendance)")
        
        print(f"\nProblematic Discord names (sample):")
        for org in discord_orgs[:5]:
            print(f"   - {org['display_name'][:50]} ({org['total_attendance']} attendance)")
        
        print("="*50)
        
        return {
            'total': len(all_orgs),
            'email': len(email_orgs),
            'discord': len(discord_orgs),
            'clean': len(clean_orgs)
        }
        
    except Exception as e:
        print(f"❌ Failed to analyze organization names: {e}")
        return None

def setup_test_environment(force_recreate=False):
    """Complete test environment setup"""
    print("🧪 SETTING UP DATABASE TEST ENVIRONMENT")
    print("="*60)
    
    # Step 1: Initialize database
    if not init_database(force_recreate=force_recreate):
        return False
    
    # Step 2: Check if we already have data
    stats = show_database_stats()
    
    if stats and stats['total_tournaments'] > 0:
        print(f"\nDatabase already has {stats['total_tournaments']} tournaments")
        response = input("Skip data sync and use existing data? (y/N): ")
        if response.lower() == 'y':
            print("Using existing tournament data")
            identify_problematic_names()
            return True
    
    # Step 3: Populate with January data
    if not populate_january_data():
        return False
    
    # Step 4: Show final stats
    show_database_stats()
    identify_problematic_names()
    
    print("\n✅ Test environment setup complete!")
    print("Ready for session cache testing and editor development")
    
    return True

def main():
    """Main function for database debug operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Debug Environment Setup')
    parser.add_argument('--force-recreate', action='store_true', 
                       help='Force recreate database (deletes existing)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Show database statistics only')
    parser.add_argument('--analyze-names', action='store_true',
                       help='Analyze organization names only')
    
    args = parser.parse_args()
    
    try:
        if args.stats_only:
            show_database_stats()
        elif args.analyze_names:
            identify_problematic_names()
        else:
            success = setup_test_environment(force_recreate=args.force_recreate)
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        print(f"\nSetup interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

