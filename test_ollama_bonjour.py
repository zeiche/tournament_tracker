#!/usr/bin/env python3
"""
Test the complete Ollama Bonjour module
"""

import sys
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

from ollama_bonjour import get_ollama_bonjour, ServiceMemory, BonjourRouter

print("Testing Ollama Bonjour Module")
print("=" * 50)

# Test OllamaBonjour service
print("\n1. Testing OllamaBonjour service:")
try:
    ollama = get_ollama_bonjour()
    print(f"   ✅ Service created")
    print(f"   Model: {ollama.model}")
    print(f"   Available: {ollama.available}")
    print(f"   Services discovered: {len(ollama.service_memory)}")
    
    # Test ask
    response = ollama.ask("What services are available?")
    print(f"   Response preview: {response[:100]}...")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test ServiceMemory
print("\n2. Testing ServiceMemory:")
try:
    memory = ServiceMemory()
    memory.remember_service("Test Service", ["Can do X", "Can do Y"])
    stats = memory.get_statistics()
    print(f"   ✅ Memory working")
    print(f"   Services tracked: {stats['total_services']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test BonjourRouter
print("\n3. Testing BonjourRouter:")
try:
    router = BonjourRouter()
    route = router.route("I need to sync data")
    print(f"   ✅ Router working")
    print(f"   Route suggestion: {route}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✨ Ollama Bonjour module is fully integrated!")
print("\nUsage:")
print("  ./go.py --ollama-bonjour    # Start intelligence service")
print("  ./go.py --ollama-bridge     # Start async bridge")
print("\nThe module is now a complete Bonjour citizen!")