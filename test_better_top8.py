#!/usr/bin/env python3
"""
Test Claude with better prompt for top 8 singles
"""

from claude_service import claude_service
from enhanced_database_context import EnhancedDatabaseContext

def test_better_top8():
    query = "show me the top 8 for singles"
    
    # Get comprehensive database context
    db_context = EnhancedDatabaseContext.get_comprehensive_context(query)
    
    # Better prompt that explicitly points to the data
    prompt = f"""You are a tournament database assistant. Answer using ONLY the database information below.

USER QUESTION: {query}

DATABASE CONTAINS THESE TOURNAMENTS WITH TOP 8 STANDINGS:

{db_context['database_info'].get('tournaments_with_standings', [])}

Please format the top 8 standings from the most recent tournament that has standings data. Show the tournament name, date, and the complete top 8 placements."""
    
    print("=" * 70)
    print("ASKING CLAUDE FOR TOP 8 SINGLES")
    print("=" * 70)
    
    result = claude_service.ask_question(prompt)
    
    if result.success:
        print(result.response)
    else:
        print(f"Error: {result.error}")

if __name__ == "__main__":
    test_better_top8()