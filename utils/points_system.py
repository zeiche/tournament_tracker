#!/usr/bin/env python3
"""
points_system.py - Single source of truth for tournament points calculation

This module defines how points are awarded based on placement in tournaments.
ALL point calculations should use this module.
"""
from typing import Dict, Optional
from polymorphic_core import announcer

# Announce module capabilities on import
announcer.announce(
    "Points System",
    [
        "Calculate tournament points based on placement",
        "Define standard FGC point distribution (8-6-4-3-2-2-1-1)",
        "Calculate total points for players",
        "Provide point breakdowns by placement",
        "Single source of truth for all point calculations",
        "Support major tournament multipliers"
    ],
    [
        "PointsSystem.get_points_for_placement(1)",
        "PointsSystem.calculate_player_total_points(placements)",
        "PointsSystem.PLACEMENT_POINTS"
    ]
)


class PointsSystem:
    """Centralized tournament points calculation system"""
    
    # The ONLY place where placement points are defined
    # Maximum 8 points per tournament
    PLACEMENT_POINTS: Dict[int, int] = {
        1: 8,   # 1st place: 8 points
        2: 6,   # 2nd place: 6 points  
        3: 4,   # 3rd place: 4 points
        4: 3,   # 4th place: 3 points
        5: 2,   # 5th place: 2 points (5th-6th tied)
        6: 2,   # 6th place: 2 points (5th-6th tied)
        7: 1,   # 7th place: 1 point (7th-8th tied)
        8: 1,   # 8th place: 1 point (7th-8th tied)
    }
    
    @classmethod
    def get_points_for_placement(cls, placement: int) -> int:
        """
        Get points for a specific placement
        
        Args:
            placement: The placement (1st, 2nd, etc.)
            
        Returns:
            Points earned for that placement
        """
        if placement is None:
            return 0
        return cls.PLACEMENT_POINTS.get(placement, 0)
    
    @classmethod
    def get_points_dict(cls) -> Dict[int, int]:
        """
        Get the complete points dictionary
        
        Returns:
            Dictionary mapping placements to points
        """
        return cls.PLACEMENT_POINTS.copy()
    
    @classmethod
    def calculate_total_points(cls, placements: list) -> int:
        """
        Calculate total points from a list of placements
        
        Args:
            placements: List of placement numbers
            
        Returns:
            Total points earned
        """
        total = 0
        for placement in placements:
            total += cls.get_points_for_placement(placement)
        return total
    
    @classmethod
    def get_points_breakdown(cls, placements: list) -> Dict[str, any]:
        """
        Get detailed breakdown of points from placements
        
        Args:
            placements: List of placement numbers
            
        Returns:
            Dictionary with total points and breakdown
        """
        breakdown = {}
        total = 0
        
        for placement in placements:
            points = cls.get_points_for_placement(placement)
            if points > 0:
                key = f"{placement}th_place"
                breakdown[key] = breakdown.get(key, 0) + 1
                total += points
        
        return {
            'total_points': total,
            'placements': breakdown,
            'events_count': len(placements)
        }
    
    @classmethod
    def describe_system(cls) -> str:
        """
        Get a human-readable description of the points system
        
        Returns:
            String describing the points system
        """
        lines = ["Tournament Points System:"]
        for place, points in sorted(cls.PLACEMENT_POINTS.items()):
            if place == 1:
                lines.append(f"  1st place: {points} points")
            elif place == 2:
                lines.append(f"  2nd place: {points} points")
            elif place == 3:
                lines.append(f"  3rd place: {points} points")
            else:
                lines.append(f"  {place}th place: {points} point{'s' if points > 1 else ''}")
        lines.append(f"\nMaximum points per tournament: {max(cls.PLACEMENT_POINTS.values())}")
        return "\n".join(lines)
    
    @classmethod
    def get_sql_case_expression(cls):
        """
        Get SQLAlchemy case expression for points calculation
        
        This is used in database queries to calculate points on-the-fly.
        
        Example usage:
            from sqlalchemy import func, case
            from points_system import PointsSystem
            
            points_case = PointsSystem.get_sql_case_expression()
            query = session.query(
                Player,
                func.sum(points_case).label('total_points')
            )
        """
        from sqlalchemy import case
        from models.tournament_models import TournamentPlacement
        
        # Build case expression for SQL queries
        # SQLAlchemy case wants tuples as *args, not a list
        whens = []
        for placement, points in cls.PLACEMENT_POINTS.items():
            whens.append((TournamentPlacement.placement == placement, points))
        
        # Unpack the list of tuples as positional arguments
        return case(*whens, else_=0)


# Convenience functions for direct import
def get_points(placement: int) -> int:
    """Get points for a placement"""
    return PointsSystem.get_points_for_placement(placement)


def get_points_dict() -> Dict[int, int]:
    """Get the complete points dictionary"""
    return PointsSystem.get_points_dict()


def describe() -> str:
    """Describe the points system"""
    return PointsSystem.describe_system()


# Export the main constant for backward compatibility
# BUT everyone should use the methods above
PLACEMENT_POINTS = PointsSystem.PLACEMENT_POINTS


if __name__ == "__main__":
    # Test the points system
    print(PointsSystem.describe_system())
    print("\nTest calculations:")
    print(f"1st place: {get_points(1)} points")
    print(f"4th place: {get_points(4)} points") 
    print(f"9th place: {get_points(9)} points")
    
    # Test total calculation
    placements = [1, 3, 5, 7, 2]
    total = PointsSystem.calculate_total_points(placements)
    print(f"\nPlacements {placements} = {total} total points")
    
    # Test breakdown
    breakdown = PointsSystem.get_points_breakdown(placements)
    print(f"Breakdown: {breakdown}")