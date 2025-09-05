#!/usr/bin/env python3
"""
Test "show player west" query with Claude
"""

from claude_service import claude_service
from enhanced_database_context import EnhancedDatabaseContext
from database_claude_handler import DatabaseOnlyClaudeHandler

def test_player_west():
    query = "show player west"
    
    print("=" * 70)
    print("TESTING: show player west")
    print("=" * 70)
    
    # Check if allowed
    is_allowed, category = DatabaseOnlyClaudeHandler.is_database_query(query)
    print(f"Query allowed: {is_allowed}")
    print(f"Category: {category}\n")
    
    # Get comprehensive context
    db_context = EnhancedDatabaseContext.get_comprehensive_context(query)
    db_info = db_context['database_info']
    
    # Check if we found player "west" in the search
    player_results = db_info.get('player_search_results', [])
    print(f"Player search results found: {len(player_results)}")
    if player_results:
        for p in player_results:
            print(f"  - {p['gamer_tag']}")
            for placement in p.get('recent_placements', [])[:3]:
                print(f"    • {placement['placement']} at {placement['tournament']} ({placement['event']})")
    
    # Build the prompt as Discord does
    restricted_prompt = f"""You are a tournament database assistant. Here's what you can do and where to find the information:

## YOUR CAPABILITIES:

1. **COUNT ORGANIZATIONS**: 
   - Total count: {db_info['statistics']['total_organizations']} organizations
   - Organization list in: 'top_organizations' section below

2. **SHOW TOURNAMENT STANDINGS/TOP 8**:
   - {db_info['statistics']['tournaments_with_standings']} tournaments have standings
   - Find them in: 'tournaments_with_standings' section below
   - Each includes placement, player name, and event

3. **PLAYER STATISTICS**:
   - Total players: {db_info['statistics']['total_players']}
   - Winners list in: 'top_players_by_wins' 
   - Podium finishers in: 'top_players_by_podiums'
   - Tournament participation in: 'top_players_by_participation'

4. **TOURNAMENT INFORMATION**:
   - Total tournaments: {db_info['statistics']['total_tournaments']}
   - Recent tournaments with details in: 'recent_tournaments'
   - Each includes: name, date, attendance, venue, organization, and top 8 (if available)

5. **VENUE STATISTICS**:
   - Top venues by event count in: 'top_venues'
   - Includes city, events hosted, total attendance

6. **GAME/EVENT BREAKDOWN**:
   - Games played in: 'games_and_events'
   - Shows which games/events are run and player counts

7. **ATTENDANCE TRENDS**:
   - Monthly trends in: 'monthly_trends'
   - Shows tournaments per month and attendance

## USER QUESTION: {query}

## DATABASE CONTENTS:

PLAYER SEARCH RESULTS:
{db_info.get('player_search_results', [])}

PLAYER RANKINGS:
- By Wins: {db_info.get('top_players_by_wins', [])}
- By Podiums: {db_info.get('top_players_by_podiums', [])}
- By Participation: {db_info.get('top_players_by_participation', [])}

RECENT TOURNAMENTS:
{db_info.get('recent_tournaments', [])[:5]}

Use the specific sections above to answer the question. You have access to all this data - use it!"""
    
    print("\n" + "-" * 70)
    print("CLAUDE'S RESPONSE:")
    print("-" * 70)
    
    # Ask Claude
    result = claude_service.ask_question(restricted_prompt)
    
    if result.success:
        print(result.response)
    else:
        print(f"Error: {result.error}")

if __name__ == "__main__":
    test_player_west()