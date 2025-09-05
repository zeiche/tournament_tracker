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
            if not claude_ai.cli_available:
                print("Claude AI is not enabled. Run 'claude /login' to enable.")
                return None
            
            # Convert input to string intelligently
            question_str = _format_input(question)
            
            print(f"Asking Claude: {question_str[:200]}{'...' if len(question_str) > 200 else ''}")
            result = process_message(question_str, {'source': 'interactive'})
            
            if result['success']:
                print("\nClaude's response:")
                print("-" * 50)
                print(result['response'])
                print("-" * 50)
                return result['response']
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                return None
        
        def _format_input(obj):
            """Format any input type for Claude"""
            import json
            
            # Handle strings
            if isinstance(obj, str):
                return obj
            
            # Handle dictionaries - format as JSON
            elif isinstance(obj, dict):
                formatted = f"Analyze this data:\n{json.dumps(obj, indent=2, default=str)}"
                return formatted
            
            # Handle lists
            elif isinstance(obj, list):
                # If it's a list of objects, format nicely
                if obj and hasattr(obj[0], '__dict__'):
                    items = []
                    for item in obj[:10]:  # Limit to first 10
                        if hasattr(item, '__dict__'):
                            items.append(item.__dict__)
                        else:
                            items.append(str(item))
                    formatted = f"Analyze these items:\n{json.dumps(items, indent=2, default=str)}"
                else:
                    formatted = f"Analyze this list:\n{json.dumps(obj[:50], indent=2, default=str)}"  # Limit items
                return formatted
            
            # Handle Tournament/Organization/Player objects
            elif hasattr(obj, '__class__') and obj.__class__.__name__ in ['Tournament', 'Organization', 'Player']:
                # Special handling for our models
                attrs = {}
                for key in dir(obj):
                    if not key.startswith('_') and not callable(getattr(obj, key, None)):
                        try:
                            value = getattr(obj, key)
                            # Skip SQLAlchemy internal attributes
                            if not str(type(value)).startswith("<class 'sqlalchemy"):
                                attrs[key] = value
                        except:
                            pass
                formatted = f"Analyze this {obj.__class__.__name__}:\n{json.dumps(attrs, indent=2, default=str)}"
                return formatted
            
            # Handle any object with __dict__
            elif hasattr(obj, '__dict__'):
                formatted = f"Analyze this {obj.__class__.__name__} object:\n{json.dumps(obj.__dict__, indent=2, default=str)}"
                return formatted
            
            # Handle any object with __str__
            elif hasattr(obj, '__str__'):
                return str(obj)
            
            # Fallback
            else:
                return repr(obj)
        
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
            if not claude_ai.cli_available:
                print("Claude AI is not enabled. Run 'claude /login' to enable.")
                return
            
            print("\n" + "=" * 60)
            print("Claude AI Chat Mode")
            print("=" * 60)
            print("Type your messages below. Commands:")
            print("  'quit', 'exit', or 'bye' - Exit chat mode")
            print("  'clear' - Clear conversation history")
            print("  'stats' - Show chat statistics")
            print("=" * 60 + "\n")
            
            conversation_history = []
            
            # If initial prompt provided, process it first
            if initial_prompt is not None:
                # Format the input appropriately
                formatted_prompt = _format_input(initial_prompt)
                
                # Show what we're setting as context
                preview = formatted_prompt[:100] + '...' if len(formatted_prompt) > 100 else formatted_prompt
                print(f"Setting context: {preview}")
                conversation_history.append(f"System: {formatted_prompt}")
                
                # Get initial response
                context = {
                    'source': 'interactive_chat',
                    'system_prompt': formatted_prompt
                }
                
                response = process_message(formatted_prompt, context)
                if response and not response.startswith("Error:"):
                    print(f"Claude: {response}\n")
                    conversation_history.append(f"Claude: {response}")
                else:
                    print(f"Claude: Ready to chat!\n")
            
            while True:
                try:
                    # Get user input
                    user_input = input("You: ").strip()
                    
                    # Check for exit commands
                    if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                        print("Claude: Goodbye! Returning to interactive mode.")
                        break
                    
                    # Check for special commands
                    if user_input.lower() == 'clear':
                        conversation_history.clear()
                        print("Claude: Conversation history cleared.")
                        continue
                    
                    if user_input.lower() == 'stats':
                        ai_stats()
                        continue
                    
                    if not user_input:
                        continue
                    
                    # Add to history
                    conversation_history.append(f"User: {user_input}")
                    
                    # Build context with recent history
                    context = {
                        'source': 'interactive_chat',
                        'conversation_history': conversation_history[-10:]  # Last 10 messages
                    }
                    
                    # Get response from Claude
                    response = process_message(user_input, context)
                    
                    if response and not response.startswith("Error:"):
                        print(f"Claude: {response}")
                        conversation_history.append(f"Claude: {response}")
                    else:
                        error_msg = response if response else "Unknown error"
                        print(f"Claude: Sorry, I encountered an error: {error_msg}")
                    
                except KeyboardInterrupt:
                    print("\n\nChat interrupted. Type 'quit' to exit chat mode.")
                    continue
                except EOFError:
                    print("\nExiting chat mode.")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    continue
            
            print("\n" + "=" * 60)
            print("Exited Claude AI Chat Mode")
            print("=" * 60)
        
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
