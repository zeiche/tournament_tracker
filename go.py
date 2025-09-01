#!/usr/bin/python3
"""
go - Tournament Tracker Entry Point
CLI interface for the tournament tracker system
"""
import sys
import os
import argparse
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import tracker modules
from tournament_tracker import TournamentTracker

def main():
    """Main CLI entry point"""
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
    
    # Editor options
    parser.add_argument('--edit-contacts', action='store_true', help='Launch web editor for contact management')
    parser.add_argument('--editor-port', type=int, default=8081, help='Port for web editor (default: 8081)')
    
    # Service management options
    parser.add_argument('--setup-discord', metavar='TOKEN', help='Setup Discord bot service with token')
    parser.add_argument('--setup-services', metavar='TOKEN', help='Setup both web and Discord services')
    parser.add_argument('--service-status', action='store_true', help='Check status of services')
    
    args = parser.parse_args()
    
    # Handle help case FIRST - before any database operations
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Handle service management first (before database operations)
    if args.setup_discord:
        import subprocess
        result = subprocess.run(['/home/ubuntu/claude/setup_services.sh', 'setup-discord', args.setup_discord])
        return result.returncode
    
    if args.setup_services:
        import subprocess
        result = subprocess.run(['/home/ubuntu/claude/setup_services.sh', 'setup-all', args.setup_services])
        return result.returncode
    
    if args.service_status:
        import subprocess
        result = subprocess.run(['/home/ubuntu/claude/setup_services.sh', 'status'])
        return result.returncode
    
    try:
        # Create TournamentTracker for database operations
        tracker = TournamentTracker(database_url=args.database_url)
        
        # Sync unless skipped
        if not args.skip_sync and (args.sync or args.fetch_standings or args.publish or not any([args.console, args.html, args.stats, args.interactive])):
            success = tracker.sync_tournaments(
                page_size=args.page_size, 
                fetch_standings=args.fetch_standings,
                standings_limit=args.standings_limit
            )
            if not success and not args.interactive:
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
            from go_interactive import start_interactive_mode
            start_interactive_mode(database_url=args.database_url)
        
        if args.edit_contacts:
            # Ensure database is initialized
            tracker._ensure_db_initialized()
            from editor_web import run_server
            run_server(port=args.editor_port)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

