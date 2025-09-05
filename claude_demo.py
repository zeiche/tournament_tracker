#!/usr/bin/env python3
"""
Claude Integration Demo for Tournament Tracker
Shows how Claude can answer questions about tournament data
"""

import os
from claude_service import claude_service, is_claude_enabled
from database import get_session
from tournament_models import Tournament, Organization, Player
from datetime import datetime, timedelta
from sqlalchemy import func, desc

def demo_claude_integration():
    """Demo Claude's ability to answer questions about tournament data"""
    
    print("=" * 70)
    print("CLAUDE TOURNAMENT TRACKER INTEGRATION DEMO")
    print("=" * 70)
    
    # Check Claude status
    if not is_claude_enabled():
        print("\n⚠️  Claude is not enabled. To enable:")
        print("   1. Get an API key from https://console.anthropic.com/")
        print("   2. Set it: export ANTHROPIC_API_KEY='your-key-here'")
        print("\n📊 Showing database statistics instead...\n")
        show_database_stats()
        return
    
    print("\n✅ Claude is ready to answer questions about tournaments!")
    
    # Example questions Claude can answer
    questions = [
        "What are the top 5 largest tournaments by attendance?",
        "Which organizations run the most tournaments?",
        "What is the trend in tournament attendance over time?",
        "Which venues host the most events?",
        "Who are the most successful players in recent tournaments?",
        "What games are most popular in SoCal tournaments?",
        "How has the tournament scene grown year over year?",
        "What are the peak months for tournaments?",
        "Which tournaments have the highest skill level competition?",
        "What is the geographic distribution of tournaments?"
    ]
    
    print("\n📝 Example questions Claude can answer:")
    for i, q in enumerate(questions, 1):
        print(f"   {i}. {q}")
    
    # Demo: Answer a specific question with context
    print("\n" + "=" * 70)
    print("DEMO: Answering a tournament question with full context")
    print("=" * 70)
    
    # Gather context for Claude
    with get_session() as session:
        # Get statistics
        total_tournaments = session.query(Tournament).count()
        total_orgs = session.query(Organization).count()
        total_players = session.query(Player).count()
        
        # Get recent tournaments
        recent = session.query(Tournament).order_by(
            Tournament.start_at.desc()
        ).limit(5).all()
        
        # Get top organizations
        top_orgs = session.query(
            Organization.name,
            func.count(Tournament.id).label('count')
        ).join(Tournament).group_by(
            Organization.id
        ).order_by(desc('count')).limit(5).all()
    
    print(f"\n📊 Database Context:")
    print(f"   Total Tournaments: {total_tournaments}")
    print(f"   Total Organizations: {total_orgs}")
    print(f"   Total Players: {total_players}")
    
    if recent:
        print(f"\n🏆 Recent Tournaments:")
        for t in recent[:3]:
            print(f"   - {t.name} ({t.num_attendees or 0} attendees)")
    
    if top_orgs:
        print(f"\n🏢 Top Organizations:")
        for org_name, count in top_orgs[:3]:
            print(f"   - {org_name}: {count} tournaments")
    
    # Example of how to ask Claude with context
    print("\n" + "=" * 70)
    print("CLAUDE RESPONSE EXAMPLE")
    print("=" * 70)
    
    question = "Based on the tournament data, what insights can you provide about the SoCal FGC scene?"
    
    print(f"\n❓ Question: {question}")
    print("\n💭 Claude would analyze the data and provide insights like:")
    print("""
   The SoCal Fighting Game Community shows strong activity with:
   - Regular weekly/monthly events across multiple venues
   - Growing attendance trends indicating healthy community growth
   - Diverse game representation (Street Fighter, Tekken, Guilty Gear, etc.)
   - Strong organizational structure with dedicated TOs
   - Geographic clustering around major population centers
   
   Key recommendations:
   - Focus on venue accessibility for continued growth
   - Consider cross-promotion between organizations
   - Track player retention and progression metrics
   """)
    
    print("\n" + "=" * 70)
    print("INTEGRATION FEATURES")
    print("=" * 70)
    
    print("""
Claude can help with:
✅ Natural language queries about tournament data
✅ Trend analysis and insights
✅ Player performance analysis
✅ Venue and geographic analysis
✅ Growth predictions and recommendations
✅ Automated report generation
✅ Question answering for Discord bot
✅ Data quality checks and suggestions

Integration points:
- Discord bot (!ask command)
- Web interface (AI chat)
- CLI tool (./go.py --ai-ask)
- API endpoint for external apps
""")

def show_database_stats():
    """Show database statistics when Claude is not available"""
    with get_session() as session:
        from sqlalchemy import func, desc
        
        # Get counts
        tournaments = session.query(Tournament).count()
        organizations = session.query(Organization).count()
        players = session.query(Player).count()
        # standings = session.query(Standing).count()  # Standing model not available
        standings = 0  # Placeholder
        
        # Get date range
        oldest = session.query(func.min(Tournament.start_at)).scalar()
        newest = session.query(func.max(Tournament.start_at)).scalar()
        
        # Get top tournaments by attendance
        top_tournaments = session.query(Tournament).filter(
            Tournament.num_attendees.isnot(None)
        ).order_by(
            desc(Tournament.num_attendees)
        ).limit(5).all()
        
        print("📊 Database Statistics:")
        print(f"   Tournaments: {tournaments}")
        print(f"   Organizations: {organizations}")
        print(f"   Players: {players}")
        print(f"   Standings: {standings}")
        
        if oldest and newest:
            print(f"\n📅 Date Range:")
            if isinstance(oldest, datetime):
                print(f"   From: {oldest.strftime('%Y-%m-%d')}")
            else:
                print(f"   From: {oldest}")
            if isinstance(newest, datetime):
                print(f"   To: {newest.strftime('%Y-%m-%d')}")
            else:
                print(f"   To: {newest}")
        
        if top_tournaments:
            print(f"\n🏆 Top Tournaments by Attendance:")
            for t in top_tournaments:
                print(f"   - {t.name}: {t.num_attendees} attendees")

if __name__ == "__main__":
    demo_claude_integration()