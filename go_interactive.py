#!/usr/bin/env python3
"""
go_interactive.py - Interactive Mode for Tournament Tracker
Provides REPL interface for debugging and manual operations
"""
import sys
import os
import code

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tournament_tracker import TournamentTracker
from database_queue import commit_queue

def start_interactive_mode(database_url=None):
    """Start interactive REPL mode"""
    print("Starting Tournament Tracker Interactive Mode...")
    
    try:
        # Initialize database first
        print("Initializing database...")
        from database_utils import init_db
        engine, Session = init_db(database_url)
        print("Database initialized successfully")
        
        # Initialize tracker
        tracker = TournamentTracker(database_url=database_url)
        
        print("Tournament Tracker Interactive Mode")
        print("Available objects: Tournament, Organization, tracker")
        print("Type 'help()' for commands, 'exit()' to quit")
        
        # Import models for interactive use
        from tournament_models import Tournament, Organization
        
        # Define helper functions
        def help():
            """Interactive mode help"""
            print("""
Interactive Mode Commands:

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
            """)
        
        # Make objects available in local scope
        local_vars = {
            'Tournament': Tournament,
            'Organization': Organization,
            'tracker': tracker,
            'sync': lambda: tracker.sync_tournaments(),
            'stats': lambda: tracker.show_statistics(),
            'report': lambda limit=20: tracker.show_console_report(limit),
            'commit': commit_queue,
            'help': help
        }
        
        # Start interactive console
        code.interact(local=local_vars)
        
    except KeyboardInterrupt:
        print("\nInteractive mode interrupted")
    except Exception as e:
        print(f"Interactive mode error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run interactive mode directly
    start_interactive_mode()
