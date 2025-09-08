#!/usr/bin/env python3
"""
claude_chat_polymorphic.py - Claude AI Chat with just ask/tell/do

Replaces functions with 3 universal methods that understand intent.

Examples:
    # Instead of: start_chat()
    chat.do("start")
    
    # Instead of: ask_one_shot(question)
    chat.ask(question)
    
    # Instead of: format_input(obj)
    chat.tell("format", data=obj)
"""

import sys
import json
from typing import Optional, Any, List, Dict
import os

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from universal_polymorphic import UniversalPolymorphic
from polymorphic_core import announcer
from claude_cli_service import claude_cli as claude_ai, ask_claude as process_message


class ClaudeChatPolymorphic(UniversalPolymorphic):
    """
    Claude AI chat service with polymorphic ask/tell/do pattern.
    
    Examples:
        chat = ClaudeChatPolymorphic()
        
        # Ask Claude questions directly
        chat.ask("What is polymorphism?")
        chat.ask({"data": [1,2,3]})           # Ask about data
        chat.ask(tournament_object)            # Ask about an object
        
        # Tell in different formats
        chat.tell("format", data=obj)         # Format an object for Claude
        chat.tell("status")                   # Get chat status
        chat.tell("history")                  # Get conversation history
        
        # Do actions
        chat.do("start")                      # Start interactive chat
        chat.do("clear")                      # Clear conversation
        chat.do("chat", message="Hello")      # Send a chat message
    """
    
    _instance: Optional['ClaudeChatPolymorphic'] = None
    
    def __new__(cls) -> 'ClaudeChatPolymorphic':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize chat service"""
        if not self._initialized:
            self.conversation_history: List[str] = []
            self.stats = {
                'messages_sent': 0,
                'messages_received': 0,
                'sessions_started': 0,
                'errors': 0
            }
            self.chat_active = False
            self._initialized = True
            
            # Call parent init (announces via UniversalPolymorphic)
            super().__init__()
            
            # Also announce via Bonjour
            announcer.announce(
                "ClaudeChatPolymorphic",
                [
                    "Claude AI chat with ask/tell/do pattern",
                    "Use chat.ask(question) for one-shot questions",
                    "Use chat.do('start') for interactive chat",
                    "Use chat.tell('format', data=obj) to format objects",
                    "Replaces 3 functions with polymorphic pattern"
                ]
            )
    
    # =========================================================================
    # POLYMORPHIC HANDLERS
    # =========================================================================
    
    def _handle_ask(self, question: Any, **kwargs) -> Any:
        """
        Handle ask() - Direct questions to Claude.
        
        This is the ONE-SHOT question interface.
        Replaces: ask_one_shot(question)
        """
        # Check if asking about the service itself
        q_str = str(question).lower() if isinstance(question, str) else ""
        
        if any(word in q_str for word in ['available', 'enabled', 'connected']):
            return claude_ai.cli_available
        
        if 'history' in q_str:
            return self.conversation_history
        
        if any(word in q_str for word in ['stats', 'statistics']):
            return {
                'chat_stats': self.stats,
                'claude_stats': claude_ai.get_statistics() if hasattr(claude_ai, 'get_statistics') else {}
            }
        
        if 'active' in q_str or 'chatting' in q_str:
            return self.chat_active
        
        # Otherwise, this is a question FOR Claude
        if not claude_ai.cli_available:
            return {'error': "Claude AI is not enabled. Run 'claude /login' to enable."}
        
        # Format the question appropriately
        formatted_question = self._format_input(question)
        
        # Send to Claude
        self.stats['messages_sent'] += 1
        
        announcer.announce(
            "ClaudeChatPolymorphic.ask",
            [f"Asking Claude: {formatted_question[:100]}..."]
        )
        
        result = process_message(formatted_question, {'source': 'polymorphic_one_shot'})
        
        if result['success']:
            self.stats['messages_received'] += 1
            response = result['response']
            
            # Add to history
            self.conversation_history.append(f"User: {formatted_question[:200]}")
            self.conversation_history.append(f"Claude: {response[:200]}")
            
            return response
        else:
            self.stats['errors'] += 1
            return {'error': result.get('error', 'Unknown error')}
    
    def _handle_tell(self, format: str = "default", **kwargs) -> Any:
        """
        Format information about the chat or format data for Claude.
        
        Replaces: format_input(obj) when data is provided
        """
        fmt = format.lower()
        
        # Format data for Claude
        if fmt == 'format' and 'data' in kwargs:
            return self._format_input(kwargs['data'])
        
        # Status formats
        if fmt in ['status', 'state']:
            enabled = '✅' if claude_ai.cli_available else '❌'
            return f"Claude Chat: {enabled} | Messages: {self.stats['messages_sent']} sent, " \
                   f"{self.stats['messages_received']} received | Active: {self.chat_active}"
        
        if fmt in ['brief', 'summary']:
            return f"Claude {'enabled' if claude_ai.cli_available else 'disabled'}, " \
                   f"{len(self.conversation_history)//2} exchanges"
        
        if fmt == 'history':
            if not self.conversation_history:
                return "No conversation history"
            return "\n".join(self.conversation_history[-10:])  # Last 10 messages
        
        if fmt == 'discord':
            enabled = '🟢' if claude_ai.cli_available else '🔴'
            active = '💬' if self.chat_active else '💤'
            return f"**Claude Chat** {enabled} {active}\n" \
                   f"Messages: {self.stats['messages_sent']}/{self.stats['messages_received']}\n" \
                   f"Sessions: {self.stats['sessions_started']}"
        
        if fmt in ['detailed', 'full']:
            return {
                'service': 'Claude Chat (Polymorphic)',
                'available': claude_ai.cli_available,
                'chat_active': self.chat_active,
                'stats': self.stats,
                'history_length': len(self.conversation_history),
                'last_messages': self.conversation_history[-4:] if self.conversation_history else []
            }
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: Any, **kwargs) -> Any:
        """
        Perform chat actions.
        
        Replaces:
        - start_chat()
        - Clear conversation
        - Send messages
        """
        act = str(action).lower()
        
        # Announce the action
        announcer.announce(
            "ClaudeChatPolymorphic.do",
            [f"Executing action: {action}"]
        )
        
        # Start interactive chat
        if 'start' in act:
            return self._start_chat(kwargs.get('context'))
        
        # Clear conversation
        if 'clear' in act:
            self.conversation_history = []
            announcer.announce(
                "ClaudeChatPolymorphic.clear",
                ["Conversation history cleared"]
            )
            return {'cleared': True, 'history_length': 0}
        
        # Send a chat message (for programmatic chat)
        if 'chat' in act or 'send' in act:
            message = kwargs.get('message') or kwargs.get('text', '')
            if not message:
                return {'error': 'No message provided'}
            
            return self._send_message(message)
        
        # Stop chat
        if 'stop' in act or 'end' in act:
            self.chat_active = False
            return {'chat_ended': True}
        
        # Show stats
        if 'stats' in act:
            return {
                'chat_stats': self.stats,
                'claude_stats': claude_ai.get_statistics() if hasattr(claude_ai, 'get_statistics') else {}
            }
        
        return super()._handle_do(action, **kwargs)
    
    # =========================================================================
    # INTERNAL METHODS (prefixed with _)
    # =========================================================================
    
    def _format_input(self, obj: Any) -> str:
        """Format any input type for Claude"""
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
                formatted = f"Analyze this list:\n{json.dumps(obj[:50], indent=2, default=str)}"
            return formatted
        
        # Handle Tournament/Organization/Player objects
        elif hasattr(obj, '__class__') and obj.__class__.__name__ in ['Tournament', 'Organization', 'Player']:
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
    
    def _start_chat(self, initial_context: Optional[Any] = None) -> bool:
        """Start interactive chat with Claude"""
        if not claude_ai.cli_available:
            print("Claude AI is not enabled. Run 'claude /login' to enable.")
            return False
        
        self.chat_active = True
        self.stats['sessions_started'] += 1
        
        print("\n" + "=" * 60)
        print("Claude AI Chat Mode (Polymorphic)")
        print("=" * 60)
        print("Type your messages below. Commands:")
        print("  'quit', 'exit', or 'bye' - Exit chat mode")
        print("  'clear' - Clear conversation history")
        print("  'stats' - Show chat statistics")
        print("=" * 60 + "\n")
        
        # If initial context provided, process it first
        if initial_context is not None:
            formatted_prompt = self._format_input(initial_context)
            preview = formatted_prompt[:100] + '...' if len(formatted_prompt) > 100 else formatted_prompt
            print(f"Setting context: {preview}")
            
            self.conversation_history.append(f"System: {formatted_prompt}")
            
            context = {
                'source': 'polymorphic_interactive_chat',
                'system_prompt': formatted_prompt
            }
            
            result = process_message(formatted_prompt, context)
            if result['success']:
                response = result['response']
                print(f"Claude: {response}\n")
                self.conversation_history.append(f"Claude: {response}")
                self.stats['messages_sent'] += 1
                self.stats['messages_received'] += 1
        
        while self.chat_active:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nExiting chat mode...")
                    break
                
                # Check for clear command
                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("Conversation history cleared.\n")
                    continue
                
                # Check for stats command
                if user_input.lower() == 'stats':
                    stats = self.tell("detailed")
                    print(f"\nChat Statistics:")
                    print(f"  Messages sent: {stats['stats']['messages_sent']}")
                    print(f"  Messages received: {stats['stats']['messages_received']}")
                    print(f"  Sessions: {stats['stats']['sessions_started']}")
                    print(f"  History length: {stats['history_length']}")
                    print()
                    continue
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Send message
                response = self._send_message(user_input)
                if isinstance(response, dict) and 'error' in response:
                    print(f"Error: {response['error']}\n")
                else:
                    print(f"Claude: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nChat interrupted. Type 'exit' to quit or continue chatting.")
                continue
            except EOFError:
                print("\nExiting chat mode...")
                break
            except Exception as e:
                print(f"Error: {e}\n")
                continue
        
        self.chat_active = False
        return True
    
    def _send_message(self, message: str) -> Any:
        """Send a message to Claude"""
        self.conversation_history.append(f"User: {message}")
        self.stats['messages_sent'] += 1
        
        context = {
            'source': 'polymorphic_chat',
            'conversation_history': self.conversation_history[-10:]  # Keep last 10 messages
        }
        
        result = process_message(message, context)
        
        if result['success']:
            response = result['response']
            self.conversation_history.append(f"Claude: {response}")
            self.stats['messages_received'] += 1
            return response
        else:
            self.stats['errors'] += 1
            return {'error': result.get('error', 'Unknown error')}
    
    # =========================================================================
    # OVERRIDES FOR BASE CLASS
    # =========================================================================
    
    def _get_capabilities(self) -> List[str]:
        """Return capabilities for discovery"""
        return [
            "Interactive chat with Claude AI",
            "One-shot questions to Claude",
            "Format any object for Claude",
            "Conversation history tracking",
            "Session statistics",
            "Use ask(question) for one-shot",
            "Use do('start') for interactive chat",
            "Use tell('format', data=obj) to format"
        ]
    
    def _get_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            'service': 'Claude Chat (Polymorphic)',
            'pattern': 'ask/tell/do',
            'functions_replaced': 3,
            'methods_now': 3,
            'examples': [
                "chat.ask('What is polymorphism?')",
                "chat.do('start')",
                "chat.tell('format', data=my_object)",
                "chat.do('clear')",
                "chat.tell('history')"
            ]
        }


# Singleton instance
claude_chat_polymorphic = ClaudeChatPolymorphic()

# For backward compatibility
claude_chat = claude_chat_polymorphic

# Convenience functions for backward compatibility
def start_chat(initial_context=None):
    """Backward compatibility wrapper"""
    return claude_chat.do("start", context=initial_context)

def ask_one_shot(question):
    """Backward compatibility wrapper"""
    return claude_chat.ask(question)

def format_input(obj):
    """Backward compatibility wrapper"""
    return claude_chat.tell("format", data=obj)