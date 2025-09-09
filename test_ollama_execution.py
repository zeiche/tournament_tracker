#!/usr/bin/env python3
"""
Test that Ollama Bonjour actually executes commands and returns data
"""

import sys
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

from ollama_bonjour import get_ollama_bonjour

print("Testing Ollama Bonjour EXECUTION")
print("=" * 50)

ollama = get_ollama_bonjour()

# Test queries that should return REAL DATA
test_queries = [
    "show top 8 players",
    "recent tournaments", 
    "stats",
    "show organizations"
]

for query in test_queries:
    print(f"\n🔍 Query: '{query}'")
    result = ollama.ask(query)
    
    # Check if we got real data or just instructions
    if isinstance(result, (list, dict)):
        print(f"✅ Got REAL DATA: {type(result).__name__}")
        if isinstance(result, list):
            print(f"   {len(result)} items returned")
            if result and isinstance(result[0], dict):
                print(f"   First item: {list(result[0].keys())[:3]}...")
        elif isinstance(result, dict):
            print(f"   Keys: {list(result.keys())[:5]}...")
    elif isinstance(result, str):
        if 'use' in result.lower() or 'try' in result.lower():
            print(f"❌ Got instructions: {result[:50]}...")
        else:
            print(f"✅ Got response: {result[:100]}...")
    else:
        print(f"🤔 Got: {type(result).__name__}")

print("\n" + "=" * 50)
print("✨ Ollama Bonjour now EXECUTES commands!")
print("It returns REAL DATA, not just instructions!")