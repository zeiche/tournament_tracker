#!/usr/bin/env python3
"""
Test script for Claude integration with tournament tracker
"""

import os
from claude_service import claude_service, is_claude_enabled

def test_claude_service():
    """Test the Claude service functionality"""
    
    print("=" * 60)
    print("CLAUDE SERVICE TEST")
    print("=" * 60)
    
    # Check if Claude is enabled
    if not is_claude_enabled():
        print("\n❌ Claude service is NOT enabled")
        print("   To enable, set ANTHROPIC_API_KEY environment variable:")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\n   Or add it to a .env file:")
        print("   echo 'ANTHROPIC_API_KEY=your-api-key-here' >> .env")
        return
    
    print("\n✅ Claude service is enabled")
    
    # Get service statistics
    stats = claude_service.get_statistics()
    print(f"\nService Configuration:")
    print(f"   Model: {stats['config']['model']}")
    print(f"   Max Tokens: {stats['config']['max_tokens']}")
    print(f"   Temperature: {stats['config']['temperature']}")
    
    # Test a simple question
    print("\n" + "=" * 60)
    print("TEST 1: Simple Question")
    print("=" * 60)
    
    result = claude_service.ask_question("What is a tournament tracker?")
    if result.success:
        print(f"✅ Response received:")
        print(f"   {result.response[:200]}...")
    else:
        print(f"❌ Error: {result.error}")
    
    # Test a tournament-specific question
    print("\n" + "=" * 60)
    print("TEST 2: Tournament Context Question")
    print("=" * 60)
    
    result = claude_service.ask_about_tournaments(
        "What are the most recent tournaments?"
    )
    if result.success:
        print(f"✅ Response received:")
        print(f"   {result.response[:200]}...")
    else:
        print(f"❌ Error: {result.error}")
    
    # Test player question
    print("\n" + "=" * 60)
    print("TEST 3: Player Question")
    print("=" * 60)
    
    result = claude_service.ask_about_players(
        "Tell me about top players",
        player_name="Punk"
    )
    if result.success:
        print(f"✅ Response received:")
        print(f"   {result.response[:200]}...")
    else:
        print(f"❌ Error: {result.error}")
    
    # Show updated statistics
    print("\n" + "=" * 60)
    print("SERVICE STATISTICS")
    print("=" * 60)
    
    stats = claude_service.get_statistics()
    print(f"Total Questions: {stats['usage']['total_questions']}")
    print(f"Total Responses: {stats['usage']['total_responses']}")
    print(f"API Calls: {stats['usage']['api_calls']}")
    print(f"Errors: {stats['usage']['errors']}")
    print(f"History Size: {stats['history_size']}")

if __name__ == "__main__":
    test_claude_service()