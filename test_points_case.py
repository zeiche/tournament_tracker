#!/usr/bin/env python3
"""Debug the points case expression issue"""
from database import get_session
from tournament_models import Player, TournamentPlacement
from points_system import PointsSystem
from sqlalchemy import func

with get_session() as session:
    # Test the case expression
    try:
        points_case = PointsSystem.get_sql_case_expression()
        print(f"Case expression created: {points_case}")
        
        # Try a simple query first
        query = session.query(
            TournamentPlacement.player_id,
            func.sum(points_case).label('total_points')
        ).group_by(TournamentPlacement.player_id).limit(5)
        
        print("\nExecuting simple query...")
        results = query.all()
        
        print(f"Got {len(results)} results")
        for r in results:
            print(f"  Player {r.player_id}: {r.total_points} points")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()