#!/usr/bin/env python3
"""Debug player rankings issue"""
from database import get_session
from unified_tabulator import UnifiedTabulator

try:
    with get_session() as session:
        print("Getting player rankings...")
        ranked_items = UnifiedTabulator.tabulate_player_points(session, limit=5)
        
        print(f"Got {len(ranked_items)} ranked items")
        for item in ranked_items:
            print(f"Rank {item.rank}: Score={item.score}, Metadata={item.metadata}")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()