#!/usr/bin/env python3
"""
claude_chat.py - Unified Claude chat implementation
Used by both --interactive mode and --ai-chat command
"""
import sys
import json
from typing import Optional, Any

# Import Claude CLI service
from claude_cli_service import claude_cli as claude_ai, ask_claude as process_message


def format_input(obj: Any) -> str:
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


def start_chat(initial_context: Optional[Any] = None) -> bool:
    """
    Start interactive chat with Claude
    
    Args:
        initial_context: Optional initial context (string, object, list, or dict)
    
    Returns:
        True if chat completed normally, False if error
    """
    # Check if Claude CLI is available
    if not claude_ai.cli_available:
        print("Claude AI is not enabled. Run 'claude /login' to enable.")
        return False
    
    print("\n" + "=" * 60)
    print("Claude AI Chat Mode")
    print("=" * 60)
    print("Type your messages below. Commands:")
    print("  'quit', 'exit', or 'bye' - Exit chat mode")
    print("  'clear' - Clear conversation history")
    print("  'stats' - Show chat statistics")
    print("=" * 60 + "\n")
    
    conversation_history = []
    
    # If initial context provided, process it first
    if initial_context is not None:
        # Format the input appropriately
        formatted_prompt = format_input(initial_context)
        
        # Show what we're setting as context
        preview = formatted_prompt[:100] + '...' if len(formatted_prompt) > 100 else formatted_prompt
        print(f"Setting context: {preview}")
        conversation_history.append(f"System: {formatted_prompt}")
        
        # Get initial response
        context = {
            'source': 'interactive_chat',
            'system_prompt': formatted_prompt
        }
        
        result = process_message(formatted_prompt, context)
        if result['success']:
            response = result['response']
            print(f"Claude: {response}\n")
            conversation_history.append(f"Claude: {response}")
        else:
            print(f"Claude: Ready to chat!\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nExiting chat mode...")
                break
            
            # Check for clear command
            if user_input.lower() == 'clear':
                conversation_history = []
                print("Conversation history cleared.\n")
                continue
            
            # Check for stats command
            if user_input.lower() == 'stats':
                stats = claude_ai.get_statistics()
                print(f"\nChat Statistics:")
                print(f"  Messages sent: {len(conversation_history) // 2}")
                if 'statistics' in stats:
                    st = stats['statistics']
                    print(f"  Total queries: {st.get('total_queries', 0)}")
                    print(f"  Success rate: {st.get('success_rate', 0):.1f}%")
                print()
                continue
            
            # Skip empty input
            if not user_input:
                continue
            
            # Add to history
            conversation_history.append(f"User: {user_input}")
            
            # Build context with history
            context = {
                'source': 'interactive_chat',
                'conversation_history': conversation_history[-10:]  # Keep last 10 messages
            }
            
            # Process with Claude
            result = process_message(user_input, context)
            
            if result['success']:
                response = result['response']
                print(f"Claude: {response}\n")
                conversation_history.append(f"Claude: {response}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}\n")
        
        except KeyboardInterrupt:
            print("\n\nChat interrupted. Type 'exit' to quit or continue chatting.")
            continue
        except EOFError:
            print("\nExiting chat mode...")
            break
        except Exception as e:
            print(f"Error: {e}\n")
            continue
    
    return True


def ask_one_shot(question: Any) -> Optional[str]:
    """
    Ask Claude a one-shot question
    
    Args:
        question: Question (string, object, list, or dict)
    
    Returns:
        Response string or None if error
    """
    if not claude_ai.cli_available:
        print("Claude AI is not enabled. Run 'claude /login' to enable.")
        return None
    
    # Convert input to string intelligently
    question_str = format_input(question)
    
    print(f"Asking Claude: {question_str[:200]}{'...' if len(question_str) > 200 else ''}")
    result = process_message(question_str, {'source': 'one_shot'})
    
    if result['success']:
        response = result['response']
        print("\nClaude's response:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        return response
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        return None


if __name__ == "__main__":
    # Test the chat
    start_chat()