#!/usr/bin/env python3
"""
Test database context retrieval
"""

from database_claude_handler import DatabaseOnlyClaudeHandler
import json

def test_context():
    query = "who played the most events"
    is_allowed, category = DatabaseOnlyClaudeHandler.is_database_query(query)
    
    print(f"Query: {query}")
    print(f"Allowed: {is_allowed}")
    print(f"Category: {category}")
    
    if is_allowed:
        context = DatabaseOnlyClaudeHandler.get_database_context(query, category)
        print("\nDatabase Context:")
        print(json.dumps(context['database_info'], indent=2))
        
        # Test the formatted prompt
        prompt = DatabaseOnlyClaudeHandler.format_restricted_prompt(query, context)
        print("\nFormatted Prompt:")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

if __name__ == "__main__":
    test_context()