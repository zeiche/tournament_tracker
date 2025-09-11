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
# Add parent directory for Claude AI service
sys.path.insert(0, '/home/ubuntu/claude')

from tournament_tracker import TournamentTracker
from database_queue import commit_queue
from claude_cli_service import claude_cli as claude_ai, ask_claude as process_message

def start_interactive_mode(database_url=None):
    """Start interactive REPL mode"""
    print("Starting Tournament Tracker Interactive Mode...")
    
    try:
        # Initialize database first
        print("Initializing database...")
        from database import init_database, get_session
        init_database()
        print("Database initialized successfully")
        
        # Initialize tracker
        tracker = TournamentTracker(database_url=database_url)
        
        print("\n" + "=" * 60)
        print("Tournament Tracker Interactive Mode")
        print("=" * 60)
        
        # Check Claude AI status (using CLI)
        if claude_ai.cli_available:
            print(f"✅ Claude AI: ENABLED (using Claude CLI)")
            print("   Use ask('question') or claude('question') to query AI")
        else:
            print("⚠️  Claude AI: DISABLED (run 'claude /login' to enable)")
        
        print("\nAvailable objects: Tournament, Organization, tracker")
        print("Type 'help()' for commands, 'exit()' to quit")
        print("=" * 60)
        
        # Import models for interactive use
        from database.tournament_models import Tournament, Organization
        
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

Claude AI Operations:
  chat()              - Start conversational chat mode with Claude
  chat("context")     - Start chat with initial context/personality
  ask("question")     - Ask a one-shot question (returns to prompt)
  ai_stats()          - Show Claude AI statistics
  ai_enabled()        - Check if Claude is enabled

Examples:
  # Database operations
  t = Tournament.find('12345')
  t.name = 'Updated Name'
  t.save()
  
  # Claude AI queries (all accept objects/lists/dicts!)
  chat()                              # Start conversational chat mode
  chat("You are a tournament analyst") # Chat with specific context
  chat(tournament)                    # Chat about a specific tournament object
  ask("Show me the top 5 players")   # Quick question
  ask(Tournament.all()[:5])          # Analyze first 5 tournaments
  ask({'stats': stats, 'data': data}) # Analyze dictionary data
  
  # Organization queries
  orgs = Organization.top_by_attendance(5)
  for org in orgs:
      print(f'{org.display_name}: {org.total_attendance}')
            """)
        
        def ask(question):
            """Ask Claude a one-shot question - accepts string, object, list, or dict"""
            from claude_chat import ask_one_shot
            return ask_one_shot(question)
        
        def ai_stats():
            """Show Claude AI statistics"""
            stats = claude_ai.get_statistics()
            print("\nClaude AI Statistics:")
            print("-" * 50)
            print(f"Enabled: {stats['enabled']}")
            print(f"Model: {stats['model']}")
            print(f"Database-only mode: {stats['database_only']}")
            
            if 'statistics' in stats:
                st = stats['statistics']
                print(f"\nUsage:")
                print(f"  Total queries: {st['total_queries']}")
                print(f"  Successful: {st['successful_queries']}")
                print(f"  Failed: {st['failed_queries']}")
                print(f"  Success rate: {st['success_rate']:.1f}%")
                print(f"\nQuery types:")
                for qtype, count in st['query_types'].items():
                    print(f"  {qtype}: {count}")
            print("-" * 50)
        
        def ai_enabled():
            """Check if Claude AI is enabled"""
            if claude_ai.cli_available:
                print(f"✅ Claude AI is ENABLED (using Claude CLI)")
                return True
            else:
                print("❌ Claude AI is DISABLED (Run 'claude /login' to enable)")
                return False
        
        def chat(initial_prompt=None):
            """Start interactive chat with Claude - accepts string, object, list, or dict as context"""
            from claude_chat import start_chat
            start_chat(initial_context=initial_prompt)
        
        # Make objects available in local scope
        local_vars = {
            'Tournament': Tournament,
            'Organization': Organization,
            'tracker': tracker,
            'sync': lambda: tracker.sync_tournaments(),
            'stats': lambda: tracker.show_statistics(),
            'report': lambda limit=20: tracker.show_console_report(limit),
            'commit': commit_queue,
            'help': help,
            # Claude AI functions
            'chat': chat,       # Conversational mode
            'ask': ask,         # One-shot questions
            'ai_stats': ai_stats,
            'ai_enabled': ai_enabled,
            'claude_ai': claude_ai  # Direct access to service
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
