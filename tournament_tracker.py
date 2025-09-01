#!/usr/bin/python3
"""
tournament_tracker.py - Main Tournament Tracker Application
Fixed to use centralized session management and logging with cleaned up imports
"""
import sys
import os
import argparse
from datetime import datetime

# Import centralized systems
from log_utils import log_info, log_debug, log_error, LogContext, init_logging, LogLevel
from database_utils import init_db, get_summary_stats
from startgg_sync import sync_from_startgg
from tournament_report import format_html_table, format_console_table, get_legacy_attendance_data
from database_queue import commit_queue, queue_stats
from tournament_operations import TournamentOperationTracker

class TournamentTracker:
    """Main tournament tracker application with centralized architecture"""
    
    def __init__(self, database_url=None):
        """Initialize the tracker"""
        log_info("Starting Tournament Tracker", "tracker")
        
        # Store database URL but don't initialize yet (lazy loading)
        self.database_url = database_url
        self._initialized = False
        
        # Initialize operation tracking
        self.operation_tracker = TournamentOperationTracker("tournament_tracker_session")
        self.operation_tracker.start_operation()
        
        # Session stats
        self.session_stats = {
            'start_time': datetime.now(),
            'operations_performed': [],
            'errors_encountered': []
        }
    
    def _ensure_db_initialized(self):
        """Lazy database initialization - only when actually needed"""
        if not self._initialized:
            log_info("Initializing database connection", "tracker")
            init_db(self.database_url)
            self._initialized = True
            log_debug("Database initialization completed", "tracker")
    
    def sync_tournaments(self, page_size=250, fetch_standings=False, standings_limit=5):
        """Sync tournaments from start.gg"""
        self._ensure_db_initialized()
        
        with LogContext(f"Sync tournaments from start.gg"):
            log_info(f"Starting tournament sync (page_size: {page_size})", "tracker")
            
            try:
                stats = sync_from_startgg(
                    page_size=page_size, 
                    fetch_standings=fetch_standings, 
                    standings_limit=standings_limit
                )
                
                if stats:
                    self.operation_tracker.record_tournament_success(stats['summary']['tournaments_processed'])
                    
                    log_info("Sync completed successfully!", "tracker")
                    log_info(f"   API calls: {stats['api_stats']['api_calls']}", "tracker")
                    log_info(f"   Tournaments processed: {stats['summary']['tournaments_processed']}", "tracker")
                    log_info(f"   Organizations created: {stats['summary']['organizations_created']}", "tracker")
                    log_info(f"   Processing time: {stats['summary']['total_processing_time']:.2f}s", "tracker")
                    log_info(f"   Success rate: {stats['summary']['success_rate']:.1f}%", "tracker")
                    
                    self.session_stats['operations_performed'].append(('sync', stats))
                    return True
                else:
                    self.operation_tracker.record_failure("Sync returned no stats", "sync")
                    return False
                    
            except Exception as e:
                error_msg = f"Sync failed: {e}"
                self.operation_tracker.record_failure(error_msg, "sync")
                self.session_stats['errors_encountered'].append(('sync', error_msg))
                return False
    
    def generate_html_report(self, limit=None, output_file=None):
        """Generate HTML attendance report"""
        self._ensure_db_initialized()
        
        with LogContext("Generate HTML report"):
            log_info("Generating HTML tournament report", "tracker")
            
            try:
                html = format_html_table(limit=limit)
                
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(html)
                    log_info(f"HTML report saved to {output_file}", "tracker")
                else:
                    log_debug("HTML report generated (console output)", "tracker")
                    print("HTML Report Generated:")
                    print("-" * 80)
                    print(html)
                    print("-" * 80)
                
                return html
                
            except Exception as e:
                error_msg = f"HTML generation failed: {e}"
                self.operation_tracker.record_failure(error_msg, "html")
                self.session_stats['errors_encountered'].append(('html', error_msg))
                return None
    
    def show_console_report(self, limit=20):
        """Show console attendance report"""
        self._ensure_db_initialized()
        
        with LogContext("Show console report"):
            log_info(f"Displaying console report (top {limit})", "tracker")
            format_console_table(limit=limit)
    
    def publish_to_shopify(self):
        """Publish to Shopify using legacy compatibility"""
        self._ensure_db_initialized()
        
        with LogContext("Publish to Shopify"):
            log_info("Publishing tournament data to Shopify", "tracker")
            
            try:
                # Convert to legacy format for existing Shopify code
                attendance_tracker, org_names = get_legacy_attendance_data()
                
                # Import and use existing Shopify publisher
                try:
                    from shopify_publish import publish_table
                    success = publish_table(attendance_tracker, org_names)
                    
                    if success:
                        log_info("Successfully published to Shopify", "tracker")
                        return True
                    else:
                        log_error("Shopify publishing failed", "tracker")
                        return False
                        
                except ImportError:
                    log_error("Shopify publisher module not available", "tracker")
                    log_error("Check shopify_publish.py or ACCESS_TOKEN configuration", "tracker")
                    return False
                    
            except Exception as e:
                error_msg = f"Shopify publishing failed: {e}"
                self.operation_tracker.record_failure(error_msg, "shopify")
                self.session_stats['errors_encountered'].append(('shopify', error_msg))
                return False
    
    def show_statistics(self):
        """Show detailed statistics"""
        self._ensure_db_initialized()
        
        with LogContext("Show statistics"):
            log_info("Generating system statistics", "tracker")
            
            print("Tournament Tracker Statistics")
            print("=" * 60)
            
            # Database stats
            stats = get_summary_stats()
            print("Database Statistics:")
            print(f"   Organizations: {stats['total_organizations']}")
            print(f"   Tournaments: {stats['total_tournaments']}")
            print(f"   Total Attendance: {stats['total_attendance']:,}")
            
            # Queue stats
            q_stats = queue_stats()
            if q_stats['total_operations'] > 0:
                print("Queue Statistics:")
                print(f"   Pages processed: {q_stats['pages_processed']}")
                print(f"   Operations successful: {q_stats['operations_successful']}")
                print(f"   Operations failed: {q_stats['operations_failed']}")
                print(f"   Success rate: {q_stats['success_rate']:.1f}%")
                print(f"   Average page time: {q_stats['avg_page_time']:.2f}s")
            
            # Operation tracker stats
            tracker_stats = self.operation_tracker.get_stats()
            if tracker_stats['total_operations'] > 0:
                print("Operation Tracker Statistics:")
                print(f"   Total operations: {tracker_stats['total_operations']}")
                print(f"   Success rate: {tracker_stats['success_rate']:.1f}%")
                print(f"   Tournaments processed: {tracker_stats['tournaments_processed']}")
                print(f"   Organizations processed: {tracker_stats['organizations_processed']}")
            
            # Session stats
            session_time = datetime.now() - self.session_stats['start_time']
            print("Session Statistics:")
            print(f"   Session duration: {session_time}")
            print(f"   Operations performed: {len(self.session_stats['operations_performed'])}")
            print(f"   Errors encountered: {len(self.session_stats['errors_encountered'])}")
            
            if self.session_stats['errors_encountered']:
                print("Errors:")
                for operation, error in self.session_stats['errors_encountered']:
                    print(f"   {operation}: {error}")
            
            log_debug("Statistics display completed", "tracker")
    
    def interactive_mode(self):
        """Start interactive REPL mode"""
        self._ensure_db_initialized()
        
        log_info("Entering interactive mode", "tracker")
        print("Tournament Tracker Interactive Mode")
        print("Available objects: Tournament, Organization, tracker")
        print("Type 'help()' for commands, 'exit()' to quit")
        
        # Make models and functions available in local scope
        import code
        from tournament_models import Tournament, Organization
        
        local_vars = {
            'Tournament': Tournament,
            'Organization': Organization,
            'tracker': self,
            'sync': lambda: self.sync_tournaments(),
            'stats': lambda: self.show_statistics(),
            'report': lambda limit=20: self.show_console_report(limit),
            'commit': commit_queue,
            'help': self._interactive_help
        }
        
        code.interact(local=local_vars)
    
    def _interactive_help(self):
        """Help for interactive mode"""
        help_text = """
Tournament Tracker Interactive Mode Commands:
  
  Basic Operations:
    sync()              - Sync from start.gg
    report(limit=20)    - Show console report  
    stats()             - Show statistics
    commit()            - Commit queued operations
  
  Model Operations:
    Tournament.all()    - Get all tournaments
    Tournament.find(id) - Find tournament by ID
    Organization.all()  - Get all organizations
    Organization.top_by_attendance(10) - Top orgs
  
  Examples:
    t = Tournament.find('12345')
    t.name = 'Updated Name'
    t.save()
    
    orgs = Organization.top_by_attendance(5)
    for org in orgs:
        print(f'{org.display_name}: {org.total_attendance}')
        """
        print(help_text)
        log_debug("Interactive help displayed", "tracker")

def create_sample_data():
    """Create sample data for testing"""
    log_info("Creating sample tournament data", "sample")
    
    with LogContext("Create sample data"):
        from database_queue import batch_operations
        from database_utils import normalize_contact
        from tournament_models import Tournament, Organization, OrganizationContact, AttendanceRecord
        
        sample_tournaments = [
            {
                'id': 'sample001',
                'name': 'SoCal Regionals 2024',
                'num_attendees': 250,
                'primary_contact': 'socal@fgc.com',
                'tournament_state': 3
            },
            {
                'id': 'sample002', 
                'name': 'Wednesday Night Fights',
                'num_attendees': 85,
                'primary_contact': 'levelup@discord.gg/levelup',
                'tournament_state': 3
            },
            {
                'id': 'sample003',
                'name': 'Combo Breaker Qualifier',
                'num_attendees': 120,
                'primary_contact': 'socal@fgc.com',
                'tournament_state': 3
            },
            {
                'id': 'sample004',
                'name': 'FGC Local Weekly',
                'num_attendees': 45,
                'primary_contact': 'weeklyfgc@gmail.com',
                'tournament_state': 3
            },
            {
                'id': 'sample005',
                'name': 'Major Tournament',
                'num_attendees': 300,
                'primary_contact': 'major.tournament@events.com',
                'tournament_state': 3
            }
        ]
        
        try:
            with batch_operations(page_size=10) as queue:
                for tournament_data in sample_tournaments:
                    # Normalize contact
                    tournament_data['normalized_contact'] = normalize_contact(tournament_data['primary_contact'])
                    tournament_data['sync_timestamp'] = int(time.time())
                    tournament_data['end_at'] = int(time.time()) - 86400  # Yesterday
                    
                    # Create tournament
                    queue.create(Tournament, **tournament_data)
                    
                    # Create organization and attendance
                    normalized_key = tournament_data['normalized_contact']
                    if normalized_key:
                        def create_org_and_attendance(session, norm_key, raw_contact, tourney_id, attendance):
                            # Get or create organization
                            org = session.query(Organization).filter_by(normalized_key=norm_key).first()
                            if not org:
                                display_name = raw_contact if '@' not in raw_contact and 'discord' not in raw_contact.lower() else raw_contact
                                org = Organization(
                                    normalized_key=norm_key,
                                    display_name=display_name
                                )
                                session.add(org)
                                session.flush()
                            
                            # Add contact
                            existing_contact = session.query(OrganizationContact).filter_by(
                                organization_id=org.id,
                                contact_value=raw_contact
                            ).first()
                            
                            if not existing_contact:
                                contact_type = 'email' if '@' in raw_contact else 'discord' if 'discord' in raw_contact.lower() else 'name'
                                contact = OrganizationContact(
                                    organization_id=org.id,
                                    contact_value=raw_contact,
                                    contact_type=contact_type
                                )
                                session.add(contact)
                            
                            # Record attendance
                            existing_attendance = session.query(AttendanceRecord).filter_by(
                                tournament_id=tourney_id,
                                organization_id=org.id
                            ).first()
                            
                            if not existing_attendance:
                                attendance_record = AttendanceRecord(
                                    tournament_id=tourney_id,
                                    organization_id=org.id,
                                    attendance=attendance
                                )
                                session.add(attendance_record)
                        
                        queue.custom(
                            create_org_and_attendance,
                            norm_key=normalized_key,
                            raw_contact=tournament_data['primary_contact'],
                            tourney_id=tournament_data['id'],
                            attendance=tournament_data['num_attendees']
                        )
            
            log_info("Sample data created successfully", "sample")
            
            # Show what was created
            stats = get_summary_stats()
            log_info(f"Sample data summary:", "sample")
            log_info(f"   {stats['total_tournaments']} tournaments", "sample")
            log_info(f"   {stats['total_organizations']} organizations", "sample") 
            log_info(f"   {stats['total_attendance']:,} total attendance", "sample")
            
            # Show sample report
            print("\nSample Tournament Report:")
            format_console_table(limit=10)
            
        except Exception as e:
            log_error(f"Failed to create sample data: {e}", "sample")
            import traceback
            traceback.print_exc()

def main():
    """Main application entry point with centralized logging"""
    # Initialize logging first
    init_logging(console=True, level=LogLevel.INFO, debug_file="tracker.txt")
    
    parser = argparse.ArgumentParser(description='Tournament Tracker - SoCal FGC Edition')
    
    # Sync options
    parser.add_argument('--sync', action='store_true', help='Sync tournaments from start.gg')
    parser.add_argument('--skip-sync', action='store_true', help='Skip start.gg sync')
    parser.add_argument('--fetch-standings', action='store_true', help='Fetch top 8 standings for major tournaments')
    parser.add_argument('--standings-limit', type=int, default=5, help='Limit standings fetch to N major tournaments (default: 5)')
    parser.add_argument('--page-size', type=int, default=250, help='Queue page size (default: 250)')
    
    # Output options
    parser.add_argument('--console', action='store_true', help='Show console report')
    parser.add_argument('--html', metavar='FILE', help='Generate HTML report to file')
    parser.add_argument('--publish', action='store_true', help='Publish to Shopify')
    parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Utility options
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--interactive', '-i', action='store_true', help='Start interactive mode')
    parser.add_argument('--database-url', help='Database URL (default: SQLite)')
    
    # Sample data
    parser.add_argument('--create-sample', action='store_true', help='Create sample data for testing')
    
    # Debug options
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Handle help case FIRST - before any database operations
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Set debug logging level if requested
    if args.debug:
        init_logging(console=True, level=LogLevel.DEBUG, debug_file="tracker_debug.txt")
        log_debug("Debug logging enabled", "tracker")
    
    # Handle sample data creation (standalone operation)
    if args.create_sample:
        # Initialize database for sample data
        init_db(args.database_url)
        create_sample_data()
        return
    
    try:
        # Create main tracker instance
        tracker = TournamentTracker(database_url=args.database_url)
        
        # Sync unless skipped (default behavior for most operations)
        should_sync = (
            args.sync or 
            args.fetch_standings or 
            args.publish or 
            not any([args.console, args.html, args.stats, args.interactive])
        )
        
        if not args.skip_sync and should_sync:
            log_debug("Auto-sync triggered", "tracker")
            success = tracker.sync_tournaments(
                page_size=args.page_size, 
                fetch_standings=args.fetch_standings,
                standings_limit=args.standings_limit
            )
            if not success and not args.interactive:
                log_error("Sync failed, exiting", "tracker")
                sys.exit(1)
        
        # Generate outputs
        if args.console:
           tracker.show_console_report(limit=args.limit)
        
        if args.html:
            tracker.generate_html_report(limit=args.limit, output_file=args.html)
        
        if args.publish:
            tracker.publish_to_shopify()
        
        if args.stats:
            tracker.show_statistics()
        
        if args.interactive:
            tracker.interactive_mode()
        
        # End operation tracking
        tracker.operation_tracker.end_operation()
        
    except KeyboardInterrupt:
        log_info("Interrupted by user", "tracker")
        sys.exit(130)
    except Exception as e:
        log_error(f"Fatal error: {e}", "tracker")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Test functions for tournament tracker
def test_tournament_tracker():
    """Test main tournament tracker functionality"""
    log_info("=" * 60, "test")
    log_info("TESTING TOURNAMENT TRACKER", "test")
    log_info("=" * 60, "test")
    
    try:
        # Initialize logging for tests
        init_logging(console=True, level=LogLevel.DEBUG, debug_file="tracker_test.txt")
        
        # Test 1: Tracker initialization
        log_info("TEST 1: Tracker initialization", "test")
        tracker = TournamentTracker()
        log_info("✅ Tracker initialized", "test")
        
        # Test 2: Database initialization (lazy loading)
        log_info("TEST 2: Database lazy loading", "test")
        tracker._ensure_db_initialized()
        if tracker._initialized:
            log_info("✅ Database lazy loading works", "test")
        else:
            log_error("❌ Database lazy loading failed", "test")
        
        # Test 3: Statistics display
        log_info("TEST 3: Statistics display", "test")
        tracker.show_statistics()
        log_info("✅ Statistics displayed", "test")
        
        # Test 4: Console report
        log_info("TEST 4: Console report", "test")
        tracker.show_console_report(limit=5)
        log_info("✅ Console report displayed", "test")
        
        # Test 5: HTML report generation  
        log_info("TEST 5: HTML report generation", "test")
        html = tracker.generate_html_report(limit=3)
        if html and len(html) > 100:
            log_info("✅ HTML report generated", "test")
        else:
            log_error("❌ HTML report failed", "test")
        
        log_info("✅ Tournament tracker tests completed", "test")
        
    except Exception as e:
        log_error(f"Tournament tracker test failed: {e}", "test")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

