#!/usr/bin/env python3
"""
Test Claude's response to a top 8 singles query with the enhanced database context
"""

from claude_service import claude_service
from enhanced_database_context import EnhancedDatabaseContext
from database_claude_handler import DatabaseOnlyClaudeHandler

def test_top8_query():
    query = "show me the top 8 for singles"
    
    print("=" * 70)
    print("TESTING CLAUDE WITH TOP 8 SINGLES QUERY")
    print("=" * 70)
    
    # Check if it's allowed
    is_allowed, category = DatabaseOnlyClaudeHandler.is_database_query(query)
    print(f"Query: {query}")
    print(f"Allowed: {is_allowed}")
    print(f"Category: {category}\n")
    
    if not is_allowed:
        print(f"Query rejected: {category}")
        return
    
    # Get comprehensive database context
    print("Fetching database context...")
    db_context = EnhancedDatabaseContext.get_comprehensive_context(query)
    
    # Show what data we have
    info = db_context['database_info']
    print(f"Context includes:")
    print(f"  - {len(info.get('recent_tournaments', []))} recent tournaments")
    print(f"  - {len(info.get('tournaments_with_standings', []))} tournaments with standings")
    print(f"  - {info['statistics']['total_placements_recorded']} total placements recorded")
    
    # Format the prompt as the Discord bot does
    restricted_prompt = f"""You are a tournament database assistant with access to comprehensive tournament data.

IMPORTANT: You can ONLY use the database information provided below. Do not use any external knowledge.

USER QUESTION: {query}

COMPREHENSIVE DATABASE INFORMATION:
{db_context['database_info']}

Based on the database information above, provide a detailed and accurate answer. If specific information is not in the database, say so clearly."""
    
    print("\nAsking Claude...")
    print("-" * 70)
    
    # Ask Claude
    result = claude_service.ask_question(restricted_prompt)
    
    if result.success:
        print("\n✅ CLAUDE'S RESPONSE:")
        print("-" * 70)
        print(result.response)
    else:
        print(f"\n❌ Error: {result.error}")

if __name__ == "__main__":
    test_top8_query()