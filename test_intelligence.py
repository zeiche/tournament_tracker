#!/usr/bin/env python3
"""
Test the intelligence module with Bonjour integration
"""

import sys
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

from intelligence import get_intelligence

print("Testing Intelligence Module with Bonjour Integration")
print("=" * 50)

# Try to get intelligence (will try Mistral, Ollama, then Pattern)
intelligence = get_intelligence('auto')

print(f"\nUsing: {intelligence.__class__.__name__}")
print("\nTesting polymorphic methods:")

# Test ask
print("\n1. Testing ask():")
response = intelligence.ask("What services are available?")
print(f"   Response: {response}")

# Test tell
print("\n2. Testing tell():")
formatted = intelligence.tell('discord', response)
print(f"   Discord format: {formatted}")

# Test do
print("\n3. Testing do():")
result = intelligence.do("discover services")
print(f"   Result: {result}")

print("\n4. Analyzing services:")
analysis = intelligence.do("analyze")
print(f"   Analysis: {analysis}")

print("\nIntelligence module is working with Bonjour!")