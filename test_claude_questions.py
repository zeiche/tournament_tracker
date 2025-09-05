#!/usr/bin/env python3
"""
Test Claude's ability to answer tournament questions
"""

import os
from claude_service import claude_service
from database import get_session
from tournament_models import Player
from sqlalchemy import func, desc

def test_claude_questions():
    """Test Claude with tournament-specific questions"""
    
    print("=" * 70)
    print("TESTING CLAUDE WITH TOURNAMENT QUESTIONS")
    print("=" * 70)
    
    if not claude_service.is_enabled:
        print("\n❌ Claude is not enabled")
        return
    
    # Question: "who played the most events"
    print("\n📝 Question: who played the most events")
    print("-" * 70)
    
    # Get actual data to provide context
    with get_session() as session:
        # Find players with most tournament participations
        top_players = session.query(
            Player.gamer_tag,
            func.count(Player.id).label('event_count')
        ).group_by(
            Player.gamer_tag
        ).order_by(
            desc('event_count')
        ).limit(10).all()
        
        # Build context for Claude
        context_str = "Top players by event participation:\n"
        for player, count in top_players:
            if player:  # Skip null names
                context_str += f"- {player}: {count} events\n"
    
    # Ask Claude with context
    full_question = f"who played the most events\n\nContext:\n{context_str}"
    result = claude_service.ask_question(full_question)
    
    if result.success:
        print("✅ Claude's response:")
        print(result.response)
    else:
        print(f"❌ Error: {result.error}")
    
    # Test another question
    print("\n" + "=" * 70)
    print("📝 Question: hi")
    print("-" * 70)
    
    result = claude_service.ask_question("hi")
    if result.success:
        print("✅ Claude's response:")
        print(result.response)
    else:
        print(f"❌ Error: {result.error}")

if __name__ == "__main__":
    test_claude_questions()