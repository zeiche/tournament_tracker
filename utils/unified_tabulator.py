#!/usr/bin/env python3
"""
unified_tabulator.py - Single source of truth for ALL ranking/tabulation

This module provides a universal tabulation system that can handle:
- Player rankings by points
- Organization rankings by attendance
- Organization rankings by event count
- Any custom ranking metric

IMPORTANT: All ranking/tabulation should go through this module!
"""
from typing import Any, List, Tuple, Optional, Callable, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from dataclasses import dataclass
from enum import Enum


class RankingType(Enum):
    """Types of rankings we support"""
    PLAYER_POINTS = "player_points"
    ORG_ATTENDANCE = "org_attendance"
    ORG_EVENT_COUNT = "org_event_count"
    CUSTOM = "custom"


@dataclass
class RankedItem:
    """A ranked item with all necessary metadata"""
    rank: int
    item: Any
    score: float
    tie: bool = False
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/API responses"""
        result = {
            'rank': self.rank,
            'score': self.score,
            'tie': self.tie
        }
        if self.metadata:
            result.update(self.metadata)
        return result


class UnifiedTabulator:
    """
    Universal tabulator that eliminates all duplicate ranking code.
    
    This is the SINGLE SOURCE OF TRUTH for:
    - Calculating scores
    - Sorting items
    - Assigning ranks (with proper tie handling)
    - Formatting output
    """
    
    @classmethod
    def tabulate(cls, 
                 items: List[Any],
                 score_func: Callable[[Any], float],
                 sort_desc: bool = True,
                 limit: Optional[int] = None,
                 metadata_func: Optional[Callable[[Any], Dict]] = None) -> List[RankedItem]:
        """
        Universal tabulation method for ANY ranking type.
        
        Args:
            items: List of objects to rank (players, orgs, etc.)
            score_func: Function that returns score for an item
            sort_desc: Sort descending (True) or ascending (False)
            limit: Maximum number of items to return
            metadata_func: Optional function to generate metadata for each item
            
        Returns:
            List of RankedItem objects with proper ranking
            
        Example:
            # Rank players by points
            tabulate(players, lambda p: p.total_points, limit=50)
            
            # Rank orgs by attendance
            tabulate(orgs, lambda o: o.total_attendance, limit=20)
        """
        # Calculate scores for all items
        scored_items = []
        for item in items:
            score = score_func(item)
            metadata = metadata_func(item) if metadata_func else {}
            scored_items.append((score, item, metadata))
        
        # Sort by score
        scored_items.sort(key=lambda x: x[0], reverse=sort_desc)
        
        # Apply limit if specified
        if limit:
            scored_items = scored_items[:limit]
        
        # Assign ranks with proper tie handling
        ranked_items = []
        prev_score = None
        prev_rank = 0
        ties_count = 0
        
        for i, (score, item, metadata) in enumerate(scored_items, 1):
            if score != prev_score:
                # New score, update rank
                rank = i
                prev_rank = i
                ties_count = 0
                is_tie = False
            else:
                # Same score as previous = tie
                rank = prev_rank
                ties_count += 1
                is_tie = True
                # Mark previous item as tie too
                if ranked_items and ranked_items[-1].score == score:
                    ranked_items[-1].tie = True
            
            ranked_items.append(RankedItem(
                rank=rank,
                item=item,
                score=score,
                tie=is_tie,
                metadata=metadata
            ))
            prev_score = score
        
        return ranked_items
    
    @classmethod
    def tabulate_player_points(cls, session: Session, limit: int = 50, 
                               event_filter: Optional[str] = None) -> List[RankedItem]:
        """
        Tabulate players by tournament points using SQL aggregation.
        
        This replaces BOTH:
        - database_service.get_player_rankings()
        - polymorphic_queries._get_top_players()
        """
        from database.tournament_models import Player, TournamentPlacement
        from points_system import PointsSystem
        
        # Build efficient SQL query with aggregation
        points_case = PointsSystem.get_sql_case_expression()
        
        query = session.query(
            Player,
            func.sum(points_case).label('total_points'),
            func.count(TournamentPlacement.id).label('event_count'),
            func.sum(case(
                (TournamentPlacement.placement == 1, 1),
                else_=0
            )).label('first_places'),
            func.sum(case(
                (TournamentPlacement.placement <= 3, 1),
                else_=0
            )).label('top_3s')
        ).join(TournamentPlacement).group_by(Player.id)
        
        # Apply event filter if specified
        if event_filter:
            query = query.filter(TournamentPlacement.event_name.ilike(f'%{event_filter}%'))
        
        # Execute query
        results = query.all()
        
        # Create score and metadata functions
        def score_func(result):
            # Result is a Row object with named attributes
            return float(result.total_points or 0)
        
        def metadata_func(result):
            # Access by attribute name rather than unpacking
            return {
                'player_id': result.Player.id,
                'gamer_tag': result.Player.gamer_tag,
                'name': result.Player.name,
                'total_points': int(result.total_points or 0),
                'tournament_count': result.event_count,
                'first_places': int(result.first_places or 0),
                'top_3_finishes': int(result.top_3s or 0),
                'avg_points': round(float(result.total_points or 0) / result.event_count, 2) if result.event_count > 0 else 0
            }
        
        # Use unified tabulation
        return cls.tabulate(
            items=results,
            score_func=score_func,
            metadata_func=metadata_func,
            sort_desc=True,
            limit=limit
        )
    
    @classmethod
    def tabulate_org_attendance(cls, session: Session, limit: Optional[int] = None) -> List[RankedItem]:
        """
        Tabulate organizations by total attendance.
        
        Replaces database_service.get_attendance_rankings()
        """
        from database.tournament_models import Organization, Tournament
        
        # Get all organizations with their tournaments
        orgs = session.query(Organization).all()
        
        # Calculate attendance for each org
        org_data = []
        for org in orgs:
            # Use the relationship directly (org.tournaments)
            tournaments = org.tournaments if hasattr(org, 'tournaments') else []
            total_attendance = sum(t.num_attendees or 0 for t in tournaments)
            event_count = len(tournaments)
            
            if event_count > 0:  # Only include orgs with events
                org_data.append({
                    'org': org,
                    'attendance': total_attendance,
                    'events': event_count,
                    'avg_attendance': round(total_attendance / event_count, 1)
                })
        
        def score_func(data):
            return float(data['attendance'])
        
        def metadata_func(data):
            return {
                'org_id': data['org'].id,
                'display_name': data['org'].display_name,
                'total_attendance': data['attendance'],
                'tournament_count': data['events'],
                'avg_attendance': data['avg_attendance']
            }
        
        return cls.tabulate(
            items=org_data,
            score_func=score_func,
            metadata_func=metadata_func,
            sort_desc=True,
            limit=limit
        )
    
    @classmethod
    def tabulate_org_events(cls, session: Session, limit: Optional[int] = None) -> List[RankedItem]:
        """
        Tabulate organizations by number of events hosted.
        """
        from database.tournament_models import Organization
        
        orgs = session.query(Organization).all()
        
        # Build org data with event counts
        org_data = []
        for org in orgs:
            tournaments = org.tournaments if hasattr(org, 'tournaments') else []
            if tournaments:
                org_data.append({
                    'org': org,
                    'event_count': len(tournaments),
                    'total_attendance': sum(t.num_attendees or 0 for t in tournaments)
                })
        
        def score_func(data):
            return float(data['event_count'])
        
        def metadata_func(data):
            return {
                'org_id': data['org'].id,
                'display_name': data['org'].display_name,
                'tournament_count': data['event_count'],
                'total_attendance': data['total_attendance']
            }
        
        return cls.tabulate(
            items=org_data,
            score_func=score_func,
            metadata_func=metadata_func,
            sort_desc=True,
            limit=limit
        )
    
    @classmethod
    def tabulate_custom(cls, items: List[Any], score_attr: str, 
                       limit: Optional[int] = None, **kwargs) -> List[RankedItem]:
        """
        Tabulate items using a custom attribute as score.
        
        Args:
            items: List of objects to rank
            score_attr: Name of attribute to use as score
            limit: Maximum number of results
            **kwargs: Additional metadata to include
            
        Example:
            # Rank tournaments by attendance
            tabulate_custom(tournaments, 'num_attendees', limit=10)
        """
        def score_func(item):
            return float(getattr(item, score_attr, 0))
        
        def metadata_func(item):
            meta = {}
            for key, value in kwargs.items():
                if callable(value):
                    meta[key] = value(item)
                else:
                    meta[key] = getattr(item, value, None)
            return meta
        
        return cls.tabulate(
            items=items,
            score_func=score_func,
            metadata_func=metadata_func if kwargs else None,
            sort_desc=True,
            limit=limit
        )
    
    @classmethod
    def format_rankings(cls, ranked_items: List[RankedItem], 
                       format_type: str = "text") -> str:
        """
        Format rankings for display.
        
        Args:
            ranked_items: List of RankedItem objects
            format_type: "text", "markdown", "html", "json"
            
        Returns:
            Formatted string representation
        """
        if format_type == "text":
            lines = []
            for item in ranked_items:
                tie_marker = "T" if item.tie else " "
                lines.append(f"{item.rank:3d}{tie_marker} Score: {item.score:8.1f}")
            return "\n".join(lines)
        
        elif format_type == "markdown":
            lines = ["| Rank | Score | Tie |", "|------|-------|-----|"]
            for item in ranked_items:
                tie = "Yes" if item.tie else "No"
                lines.append(f"| {item.rank} | {item.score:.1f} | {tie} |")
            return "\n".join(lines)
        
        elif format_type == "html":
            rows = []
            for item in ranked_items:
                tie_class = ' class="tie"' if item.tie else ''
                rows.append(f"<tr{tie_class}><td>{item.rank}</td><td>{item.score:.1f}</td></tr>")
            return f"<table><thead><tr><th>Rank</th><th>Score</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
        
        elif format_type == "json":
            import json
            return json.dumps([item.to_dict() for item in ranked_items], indent=2)
        
        else:
            return str(ranked_items)


# Convenience functions for backward compatibility
def get_player_rankings(session: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Drop-in replacement for database_service.get_player_rankings()
    """
    ranked = UnifiedTabulator.tabulate_player_points(session, limit)
    return [item.metadata for item in ranked]


def get_attendance_rankings(session: Session, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Drop-in replacement for database_service.get_attendance_rankings()
    """
    ranked = UnifiedTabulator.tabulate_org_attendance(session, limit)
    results = []
    for item in ranked:
        meta = item.metadata.copy()
        meta['rank'] = item.rank
        results.append(meta)
    return results


if __name__ == "__main__":
    # Test the unified tabulator
    print("Unified Tabulator Test")
    print("=" * 50)
    
    # Test with sample data
    test_items = [
        {'name': 'Player A', 'points': 100},
        {'name': 'Player B', 'points': 85},
        {'name': 'Player C', 'points': 85},  # Tie
        {'name': 'Player D', 'points': 70},
        {'name': 'Player E', 'points': 70},  # Tie
        {'name': 'Player F', 'points': 50},
    ]
    
    ranked = UnifiedTabulator.tabulate(
        items=test_items,
        score_func=lambda x: x['points'],
        metadata_func=lambda x: {'name': x['name']}
    )
    
    print("\nTest Rankings:")
    for item in ranked:
        tie = " (TIE)" if item.tie else ""
        print(f"Rank {item.rank}: {item.metadata['name']} - {item.score} points{tie}")
    
    print("\nFormatted as Markdown:")
    print(UnifiedTabulator.format_rankings(ranked, "markdown"))