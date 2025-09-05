#!/usr/bin/env python3
"""
Test the database-only restrictions for Claude
"""

from database_claude_handler import DatabaseOnlyClaudeHandler

def test_database_restrictions():
    """Test various queries to show what's allowed and what's blocked"""
    
    test_queries = [
        # ALLOWED - Database queries
        "who played the most events",
        "what tournaments are coming up",
        "show me the top organizations",
        "how many players are in the database",
        "what's the average attendance",
        "which venues host the most tournaments",
        "tell me about recent tournaments",
        
        # BLOCKED - Non-database queries
        "what's the weather today",
        "tell me a joke",
        "who are you",
        "write python code for me",
        "what's 2+2",
        "translate hello to spanish",
        "what's the meaning of life",
        "tell me about the stock market"
    ]
    
    print("=" * 70)
    print("DATABASE-ONLY RESTRICTION TEST")
    print("=" * 70)
    
    for query in test_queries:
        is_allowed, reason = DatabaseOnlyClaudeHandler.is_database_query(query)
        
        if is_allowed:
            print(f"✅ ALLOWED: '{query}'")
            print(f"   Category: {reason}")
        else:
            print(f"❌ BLOCKED: '{query}'")
            print(f"   Response: {reason}")
        print()

if __name__ == "__main__":
    test_database_restrictions()