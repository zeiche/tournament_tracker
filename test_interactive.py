#!/usr/bin/env python3
"""
test_interactive.py - Test the async interactive mode without user input
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from claude.interactive import AsyncClaudeInteractive
from polymorphic_core import announcer


async def test_interactive():
    """Test interactive mode programmatically"""
    print("Testing Async Interactive Claude")
    print("=" * 60)
    
    # Create interactive instance
    interactive = AsyncClaudeInteractive()
    
    # Simulate some service announcements
    print("\n1. Simulating service announcements...")
    
    announcer.announce(
        "Test Database Service",
        ["Query data", "Get rankings", "Find organizations"],
        ["db.ask('top players')", "db.tell('json', data)"]
    )
    
    announcer.announce(
        "Test Editor Service", 
        ["Edit organizations", "Merge duplicates"],
        ["editor.do('update org 123')"]
    )
    
    # Give time for announcements to process
    await asyncio.sleep(0.1)
    
    # Test command processing
    print("\n2. Testing command processing...")
    
    test_commands = [
        "/help",
        "/services",
        "/capabilities",
        "/context"
    ]
    
    for cmd in test_commands:
        print(f"\nCommand: {cmd}")
        result = await interactive.process_command(cmd)
        if result:
            print(result[:200] + "..." if len(result) > 200 else result)
    
    # Test Claude interaction (without API key)
    print("\n3. Testing Claude interaction...")
    
    test_queries = [
        "What services are available?",
        "Show me top players"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        # This will fail without API key but shows the flow
        try:
            response = await interactive.ask_claude_async(query)
            print(f"Response: {response[:100]}...")
        except Exception as e:
            print(f"Expected error (no API key): {e}")
    
    # Show final capabilities
    caps = interactive.claude.get_conversation_capabilities()
    print(f"\n4. Final capabilities:")
    print(f"   • Services discovered: {caps['discovered_services']}")
    print(f"   • Active services: {caps['active_services']}")
    print(f"   • Available patterns: {caps['available_patterns']}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_interactive())