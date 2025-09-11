#!/usr/bin/env python3
"""
bot_cli.py - CLI Interface for Testing Bot Functionality
Tests the bot's message handling without needing Discord
"""
import sys
import os

# Add path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')

from message_handler import handle_message


def main():
    """Interactive CLI for testing bot responses"""
    print("=" * 50)
    print("Tournament Bot CLI Test Interface")
    print("=" * 50)
    print("This tests the bot's message handling without Discord")
    print("Type 'help' for available commands")
    print("Type 'quit' or 'exit' to stop")
    print("-" * 50)
    
    while True:
        try:
            # Get input
            message = input("You> ").strip()
            
            # Check for exit
            if message.lower() in ('quit', 'exit'):
                print("Goodbye!")
                break
            
            # Skip empty messages
            if not message:
                continue
            
            # Process message
            response = handle_message(message, {'source': 'cli', 'user': 'test_user'})
            
            # Display response
            print("\nBot>", response)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("-" * 50)


if __name__ == "__main__":
    main()