#!/usr/bin/env python3
"""
show_top_players.py - Show top 8 players by points
"""

from database import get_session
from tournament_models import Player, TournamentPlacement

def show_top_players_by_points():
    with get_session() as session:
        # Get all placements with placement value
        placements = session.query(TournamentPlacement).filter(
            TournamentPlacement.placement != None
        ).all()
        
        # Calculate points for each player based on placement
        player_points = {}
        for p in placements:
            if p.player_id not in player_points:
                player_points[p.player_id] = {
                    'name': p.player.name, 
                    'points': 0, 
                    'events': 0, 
                    'wins': 0,
                    'top3': 0
                }
            
            # Point system: 1st=10pts, 2nd=7pts, 3rd=5pts, 4th=3pts, 5-8th=1pt
            points = 0
            if p.placement == 1:
                points = 10
                player_points[p.player_id]['wins'] += 1
                player_points[p.player_id]['top3'] += 1
            elif p.placement == 2:
                points = 7
                player_points[p.player_id]['top3'] += 1
            elif p.placement == 3:
                points = 5
                player_points[p.player_id]['top3'] += 1
            elif p.placement == 4:
                points = 3
            elif p.placement <= 8:
                points = 1
            
            player_points[p.player_id]['points'] += points
            player_points[p.player_id]['events'] += 1
        
        # Convert to list and sort by points
        rankings = [(data['name'], data['points'], data['events'], data['wins'], data['top3']) 
                    for data in player_points.values()]
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        # Show top 8
        print('🏆 TOP 8 PLAYERS BY POINTS')
        print('=' * 60)
        print('Point System: 1st=10pts | 2nd=7pts | 3rd=5pts | 4th=3pts | 5-8th=1pt')
        print('-' * 60)
        
        for i, (name, points, events, wins, top3) in enumerate(rankings[:8], 1):
            win_rate = (wins/events*100) if events > 0 else 0
            top3_rate = (top3/events*100) if events > 0 else 0
            
            # Determine rank emoji
            emoji = ""
            if i == 1:
                emoji = "👑"
            elif i == 2:
                emoji = "🥈"
            elif i == 3:
                emoji = "🥉"
            else:
                emoji = f"#{i}"
            
            print(f'{emoji} {name}: {points} points')
            print(f'   📊 {events} events | 🏆 {wins} wins ({win_rate:.0f}%) | 🎯 {top3} top 3s ({top3_rate:.0f}%)')
            print()

if __name__ == "__main__":
    show_top_players_by_points()