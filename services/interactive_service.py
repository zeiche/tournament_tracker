#!/usr/bin/env python3
"""
interactive_service.py - Central hub for ALL interactive features
This module has graduated from go_interactive to become the single source
of truth for all interactive operations in the tournament tracker.
Now uses ManagedService for unified service identity.
"""
import sys
import os
import code
from typing import Optional, Any

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/ubuntu/claude')
sys.path.append('/home/ubuntu/claude/tournament_tracker')

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.interactive_service")

from polymorphic_core.service_identity import ManagedService

# Import database and models
from database import init_database, get_session
from database.tournament_models import Tournament, Organization
from database_queue import commit_queue

# Import Claude chat functionality
from claude_chat import start_chat, ask_one_shot
from claude_cli_service import claude_cli as claude_ai


class InteractiveServiceManaged(ManagedService):
    """
    Central service for ALL interactive features.
    This includes REPL, AI chat, web editors, and any other interactive modes.
    Now inherits from ManagedService for unified service identity.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the interactive service"""
        super().__init__("interactive-repl", "tournament-interactive")
        self.database_url = database_url
        self.tracker = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            print("Initializing database...")
            init_database()
            print("Database initialized successfully")
            
            # Initialize tracker
            from tournament_tracker import TournamentTracker
            self.tracker = TournamentTracker(database_url=self.database_url)
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
    
    def start_repl(self) -> bool:
        """
        Start the full REPL interactive mode with all features.
        This is the original interactive mode with full access to models and functions.
        """
        try:
            print("\n" + "=" * 60)
            print("Tournament Tracker Interactive Mode")
            print("=" * 60)
            
            # Check Claude AI status
            if claude_ai.cli_available:
                print(f"✅ Claude AI: ENABLED (using Claude CLI)")
                print("   Use ask('question') or chat() to interact with AI")
            else:
                print("⚠️  Claude AI: DISABLED (run 'claude /login' to enable)")
            
            print("\nAvailable objects: Tournament, Organization, tracker")
            print("Type 'help()' for commands, 'exit()' to quit")
            print("=" * 60)
            
            # Define helper functions for REPL
            def help():
                """Interactive mode help"""
                print("""
Interactive Mode Commands:

🌟 NEW! Polymorphic 3-Method Pattern:
  t = Tournament.find('12345')
  t.ask("who won")           - Ask anything about the object
  t.tell("discord")          - Format for any output
  t.do("sync")               - Perform any action

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

Examples with Polymorphic Pattern:
  # OLD WAY (200+ methods):
  t.get_winner()
  t.format_for_discord()
  
  # NEW WAY (just 3 methods):
  t.ask("winner")
  t.tell("discord")
  t.save()
  
  # Claude AI queries
  chat()                              # Start conversational chat
  chat("You are a tournament analyst") # Chat with specific context
  ask("Show me the top 5 players")   # Quick question
  
  # Organization queries
  orgs = Organization.top_by_attendance(5)
  for org in orgs:
      print(f'{org.display_name}: {org.total_attendance}')
                """)
            
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
            
            # Wrapper functions for claude_chat
            def chat(initial_prompt=None):
                """Start interactive chat with Claude"""
                return start_chat(initial_context=initial_prompt)
            
            def ask(question):
                """Ask Claude a one-shot question"""
                return ask_one_shot(question)
            
            # Initialize polymorphic models
            try:
                from database.tournament_models_simplified import simplify_existing_models
                if simplify_existing_models():
                    print("\n✨ Polymorphic models enabled! Use ask(), tell(), do()")
            except Exception as e:
                print(f"Note: Polymorphic models not available: {e}")
            
            # Make objects available in local scope
            local_vars = {
                'Tournament': Tournament,
                'Organization': Organization,
                'tracker': self.tracker,
                'sync': lambda: self.tracker.sync_tournaments() if self.tracker else print("Tracker not initialized"),
                'stats': lambda: self.tracker.show_statistics() if self.tracker else print("Tracker not initialized"),
                'report': lambda limit=20: self.tracker.show_console_report(limit) if self.tracker else print("Tracker not initialized"),
                'commit': commit_queue,
                'help': help,
                # Claude AI functions
                'chat': chat,
                'ask': ask,
                'ai_stats': ai_stats,
                'ai_enabled': ai_enabled,
                'claude_ai': claude_ai,
                # Add get_session for easy database access
                'get_session': get_session
            }
            
            # Start interactive console
            code.interact(local=local_vars)
            return True
            
        except KeyboardInterrupt:
            print("\nInteractive mode interrupted")
            return False
        except Exception as e:
            print(f"Interactive mode error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def start_ai_chat(self, initial_context: Optional[Any] = None) -> bool:
        """
        Start AI chat mode directly.
        This is a focused chat interface without the full REPL.
        """
        return start_chat(initial_context=initial_context)
    
    def ask_ai(self, question: Any) -> Optional[str]:
        """
        Ask Claude a one-shot question.
        Returns the response or None if error.
        """
        return ask_one_shot(question)
    
    def launch_web_editor(self, port: int = 8081) -> bool:
        """
        Launch the web editor for contacts/organizations.
        This should be moved here from go.py eventually.
        """
        try:
            import subprocess
            import time
            
            print(f"Starting web editor on port {port}...")
            process = subprocess.Popen(
                ['python3', 'web_editor.py', str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to start
            time.sleep(2)
            
            if process.poll() is None:
                print(f"✅ Web editor running at http://localhost:{port}")
                print("Press Ctrl+C to stop the editor")
                process.wait()
                return True
            else:
                stderr = process.stderr.read().decode() if process.stderr else "Unknown error"
                print(f"❌ Failed to start web editor: {stderr}")
                return False
                
        except KeyboardInterrupt:
            print("\nStopping web editor...")
            if process:
                process.terminate()
            return True
        except Exception as e:
            print(f"Error launching web editor: {e}")
            return False
    
    def get_ai_stats(self) -> dict:
        """Get Claude AI statistics"""
        return claude_ai.get_statistics()
    
    def is_ai_enabled(self) -> bool:
        """Check if Claude AI is enabled"""
        return claude_ai.cli_available
    
    def run(self):
        """
        Service run method required by ManagedService.
        Runs the interactive REPL mode.
        """
        return self.start_repl()


# Singleton instance
_interactive_service = None


def get_interactive_service(database_url: Optional[str] = None) -> InteractiveServiceManaged:
    """Get or create the interactive service singleton"""
    global _interactive_service
    if _interactive_service is None:
        _interactive_service = InteractiveServiceManaged(database_url)
    return _interactive_service


# Convenience functions for backward compatibility
def start_interactive_mode(database_url: Optional[str] = None):
    """Start interactive REPL mode (backward compatibility)"""
    service = get_interactive_service(database_url)
    return service.start_repl()


def start_ai_chat(initial_context: Optional[Any] = None):
    """Start AI chat mode"""
    service = get_interactive_service()
    return service.start_ai_chat(initial_context)


def ask_ai(question: Any) -> Optional[str]:
    """Ask AI a one-shot question"""
    service = get_interactive_service()
    return service.ask_ai(question)


def main():
    """Main function for running as a managed service"""
    with InteractiveServiceManaged() as service:
        service.run()


if __name__ == "__main__":
    # Default to REPL mode when run directly as managed service
    main()