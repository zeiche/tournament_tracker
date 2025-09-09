#!/usr/bin/env python3
"""
test_claude_bonjour.py - Test the enhanced Claude service with Bonjour discovery
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.claude_bonjour_service import claude_bonjour, ask_claude_with_discovery, get_claude_capabilities
from polymorphic_core import announcer
import time


def simulate_service_announcements():
    """Simulate various services announcing themselves"""
    print("Simulating service announcements...")
    
    # Simulate database service
    announcer.announce(
        "Database Service",
        [
            "Query tournaments with natural language",
            "Get player rankings and statistics",
            "Find organizations and venues",
            "Calculate points and standings"
        ],
        [
            "db.ask('top 10 players')",
            "db.ask('tournaments this month')",
            "db.tell('discord', data)"
        ]
    )
    
    # Simulate web editor
    announcer.announce(
        "Web Editor Service",
        [
            "Edit organization names and contacts",
            "Merge duplicate organizations",
            "Assign tournaments to organizations",
            "Web interface on port 8081"
        ],
        [
            "editor.do('update tournament 123 contact=Org')",
            "editor.ask('unnamed tournaments')",
            "./go.py --edit-contacts"
        ]
    )
    
    # Simulate sync service
    announcer.announce(
        "Start.gg Sync Service",
        [
            "Synchronize tournaments from start.gg",
            "Fetch latest tournament data",
            "Update player standings",
            "Track sync operations"
        ],
        [
            "sync.do('sync tournaments')",
            "sync.ask('last sync time')",
            "./go.py --sync"
        ]
    )
    
    # Simulate visualization service
    announcer.announce(
        "Visualization Service",
        [
            "Generate heat maps of tournament activity",
            "Create player journey visualizations",
            "Produce venue quality maps",
            "Export visualizations as images"
        ],
        [
            "viz.do('generate heatmap')",
            "viz.tell('png', heatmap_data)",
            "./go.py --heatmap"
        ]
    )
    
    print("Service announcements complete!\n")


def test_discovery():
    """Test that Claude discovered the services"""
    print("=" * 60)
    print("Testing Claude's Dynamic Discovery")
    print("=" * 60)
    
    # Get current capabilities
    caps = get_claude_capabilities()
    
    print(f"\n📊 Discovery Statistics:")
    print(f"   • Services discovered: {caps['discovered_services']}")
    print(f"   • Currently active: {caps['active_services']}")
    print(f"   • Pattern mappings: {len(caps['available_patterns'])}")
    
    if caps['available_patterns']:
        print(f"\n🔍 Recognized patterns:")
        for pattern in caps['available_patterns'][:10]:
            print(f"   • {pattern}")
    
    if caps['can_handle']:
        print(f"\n✅ Can currently handle:")
        for capability in caps['can_handle'][:10]:
            print(f"   • {capability}")
    
    # Show the dynamic context
    print("\n📝 Dynamic Context Preview:")
    context = claude_bonjour.get_dynamic_context()
    print(context[:500] + "..." if len(context) > 500 else context)


def test_routing():
    """Test routing natural language to services"""
    print("\n" + "=" * 60)
    print("Testing Natural Language Routing")
    print("=" * 60)
    
    test_requests = [
        "Show me the top 10 players",
        "Edit organization contact info",
        "Sync tournaments from start.gg",
        "Generate a heat map",
        "What happened in the last sync?",
        "Find unnamed tournaments"
    ]
    
    for request in test_requests:
        print(f"\n🎯 Request: '{request}'")
        result = claude_bonjour.route_to_service(request)
        
        if result['success']:
            print(f"   ✓ Would route to: {result['routed_to']}")
            if result['alternatives']:
                print(f"   • Alternatives: {', '.join(result['alternatives'])}")
            print(f"   • Confidence: {result['confidence']} service(s) matched")
        else:
            print(f"   ✗ {result['error']}")


def test_conversation():
    """Test actual conversation with Claude using discovered capabilities"""
    print("\n" + "=" * 60)
    print("Testing Claude Conversation with Discovery")
    print("=" * 60)
    
    if not claude_bonjour.api_key:
        print("⚠️  No API key configured - showing what would happen:")
        print("   Claude would use discovered services to answer questions")
        print("   Responses would include awareness of available services")
        return
    
    # Test questions that should use discovered capabilities
    questions = [
        "What services are currently available?",
        "How can I edit tournament information?",
        "What analytics capabilities do you have?"
    ]
    
    for question in questions:
        print(f"\n❓ Question: {question}")
        result = claude_bonjour.ask_with_discovery(question)
        
        if result['success']:
            print(f"✅ Claude's response:")
            print(f"   {result['response'][:200]}...")
            print(f"\n   📊 Used {len(result['relevant_services'])} relevant services")
            if result['relevant_services']:
                print(f"   • Services: {', '.join(result['relevant_services'])}")
        else:
            print(f"❌ Error: {result['error']}")


def main():
    print("🚀 Claude Bonjour Integration Test")
    print("=" * 60)
    print("This demonstrates how Claude dynamically discovers capabilities")
    print("through Bonjour announcements instead of hardcoded methods.\n")
    
    # Simulate services announcing
    simulate_service_announcements()
    
    # Give announcements time to propagate
    time.sleep(0.5)
    
    # Test discovery
    test_discovery()
    
    # Test routing
    test_routing()
    
    # Test conversation
    test_conversation()
    
    print("\n" + "=" * 60)
    print("✨ Key Insights:")
    print("=" * 60)
    print("1. Claude discovered services WITHOUT being told about them")
    print("2. Claude can route requests based on announcement patterns")
    print("3. Claude's capabilities CHANGE as services start/stop")
    print("4. No hardcoded service knowledge required!")
    print("\nThis is the power of Bonjour + Claude integration! 🎉")


if __name__ == "__main__":
    main()