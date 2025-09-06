#!/usr/bin/env python3
"""
polymorphic_tabulator.py - TRUE polymorphic tabulation that doesn't care what it's sorting

This is the EXCITING polymorphic tabulator that:
- Accepts ANY objects (players, tournaments, dicts, strings, numbers, anything!)
- Figures out how to score them based on hints or introspection
- Handles natural language scoring hints like "by wins", "most recent", "alphabetical"
- Can combine multiple scoring criteria
- Learns from the objects themselves

This is TRUE polymorphism - not just consolidated methods, but actual dynamic adaptation!
"""
from typing import Any, List, Union, Optional, Callable, Dict, Tuple
from dataclasses import dataclass
import inspect
import re
from datetime import datetime, date
from enum import Enum


class ScoringHint(Enum):
    """Natural language hints for scoring"""
    # Performance hints
    WINS = ["wins", "victories", "first", "champion"]
    POINTS = ["points", "score", "pts"]
    ATTENDANCE = ["attendance", "attendees", "size", "crowd"]
    
    # Time hints
    RECENT = ["recent", "latest", "newest", "last"]
    OLDEST = ["oldest", "earliest", "first", "original"]
    
    # Alphabetical hints
    ALPHABETICAL = ["alphabetical", "alpha", "name", "a-z"]
    REVERSE_ALPHA = ["reverse", "z-a", "backwards"]
    
    # Size hints
    LARGEST = ["largest", "biggest", "most", "max"]
    SMALLEST = ["smallest", "least", "min", "fewest"]
    
    # Quality hints
    BEST = ["best", "top", "highest", "greatest"]
    WORST = ["worst", "bottom", "lowest", "least"]
    
    @classmethod
    def parse(cls, hint: str) -> Optional['ScoringHint']:
        """Parse natural language hint into enum"""
        hint_lower = hint.lower()
        for scoring_type in cls:
            if any(keyword in hint_lower for keyword in scoring_type.value):
                return scoring_type
        return None


@dataclass
class PolymorphicScore:
    """A score that can be anything - number, string, date, composite"""
    primary: Any
    secondary: Any = None
    metadata: Dict[str, Any] = None
    
    def __lt__(self, other):
        """Smart comparison that handles different types"""
        # Handle None values
        if self.primary is None:
            return True  # None is always "less than" anything
        if other.primary is None:
            return False  # Something is always "greater than" None
        
        # Try numeric comparison first
        try:
            return float(self.primary) < float(other.primary)
        except (TypeError, ValueError):
            pass
        
        # Try date comparison
        if isinstance(self.primary, (datetime, date)) and isinstance(other.primary, (datetime, date)):
            return self.primary < other.primary
        
        # Fall back to string comparison
        return str(self.primary) < str(other.primary)
    
    def __eq__(self, other):
        return self.primary == other.primary


class PolymorphicTabulator:
    """
    The TRULY polymorphic tabulator that doesn't care what you give it.
    It figures out how to rank ANYTHING.
    """
    
    @classmethod
    def tabulate(cls, 
                 objects: List[Any],
                 hint: Optional[Union[str, List[str]]] = None,
                 scorer: Optional[Callable] = None,
                 reverse: Optional[bool] = None) -> List[Tuple[int, Any, Any]]:
        """
        Tabulate ANYTHING - figures out scoring automatically!
        
        Args:
            objects: ANY list of objects - models, dicts, strings, numbers, anything!
            hint: Natural language hint like "by wins", "most recent", "alphabetical"
            scorer: Optional custom scoring function
            reverse: Override sort direction (None = auto-detect from hint)
            
        Returns:
            List of (rank, object, score) tuples
            
        Examples:
            # Players by natural language
            tabulate(players, "most wins")
            tabulate(players, "highest points")
            
            # Tournaments by multiple criteria
            tabulate(tournaments, ["most recent", "largest attendance"])
            
            # Anything by introspection
            tabulate(random_objects)  # Figures it out!
        """
        if not objects:
            return []
        
        # Determine scoring function
        if scorer:
            score_func = scorer
        elif hint:
            score_func = cls._create_scorer_from_hint(objects[0], hint)
        else:
            score_func = cls._introspect_scorer(objects[0])
        
        # Score all objects
        scored = []
        for obj in objects:
            try:
                score = score_func(obj)
                if not isinstance(score, PolymorphicScore):
                    score = PolymorphicScore(primary=score)
                scored.append((score, obj))
            except Exception as e:
                # Object doesn't support this scoring - give it a null score
                scored.append((PolymorphicScore(primary=0), obj))
        
        # Determine sort direction
        if reverse is None:
            reverse = cls._should_reverse(hint) if hint else True
        
        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=reverse)
        
        # Assign ranks with tie handling
        ranked = []
        prev_score = None
        prev_rank = 0
        
        for i, (score, obj) in enumerate(scored, 1):
            if score.primary != prev_score:
                rank = i
                prev_rank = i
            else:
                rank = prev_rank  # Tie
            
            ranked.append((rank, obj, score.primary))
            prev_score = score.primary
        
        return ranked
    
    @classmethod
    def _create_scorer_from_hint(cls, sample_obj: Any, hint: Union[str, List[str]]) -> Callable:
        """Create scoring function from natural language hint"""
        
        # Handle multiple hints (composite scoring)
        if isinstance(hint, list):
            scorers = [cls._create_scorer_from_hint(sample_obj, h) for h in hint]
            def composite_scorer(obj):
                scores = [s(obj) for s in scorers]
                return PolymorphicScore(
                    primary=scores[0].primary if scores else 0,
                    secondary=[s.primary for s in scores[1:]] if len(scores) > 1 else None
                )
            return composite_scorer
        
        # Parse single hint
        hint_type = ScoringHint.parse(hint)
        
        # WINS/VICTORIES
        if hint_type == ScoringHint.WINS:
            def wins_scorer(obj):
                # Try various ways to get wins
                if hasattr(obj, 'wins'):
                    return PolymorphicScore(obj.wins)
                if hasattr(obj, 'first_places'):
                    return PolymorphicScore(obj.first_places)
                if hasattr(obj, 'placements'):
                    wins = sum(1 for p in obj.placements if p.placement == 1)
                    return PolymorphicScore(wins)
                if isinstance(obj, dict):
                    return PolymorphicScore(obj.get('wins', obj.get('first_places', 0)))
                return PolymorphicScore(0)
            return wins_scorer
        
        # POINTS
        if hint_type == ScoringHint.POINTS:
            def points_scorer(obj):
                # Try various ways to get points
                if hasattr(obj, 'points'):
                    return PolymorphicScore(obj.points)
                if hasattr(obj, 'total_points'):
                    return PolymorphicScore(obj.total_points)
                if hasattr(obj, 'get_points'):
                    return PolymorphicScore(obj.get_points())
                if hasattr(obj, 'placements'):
                    # Calculate points from placements
                    from points_system import PointsSystem
                    total = sum(PointsSystem.get_points_for_placement(p.placement) 
                               for p in obj.placements)
                    return PolymorphicScore(total)
                if isinstance(obj, dict):
                    return PolymorphicScore(obj.get('points', obj.get('total_points', 0)))
                return PolymorphicScore(0)
            return points_scorer
        
        # ATTENDANCE
        if hint_type == ScoringHint.ATTENDANCE:
            def attendance_scorer(obj):
                if hasattr(obj, 'num_attendees'):
                    return PolymorphicScore(obj.num_attendees or 0)
                if hasattr(obj, 'attendance'):
                    return PolymorphicScore(obj.attendance)
                if hasattr(obj, 'total_attendance'):
                    return PolymorphicScore(obj.total_attendance)
                if hasattr(obj, 'tournaments'):
                    total = sum(t.num_attendees or 0 for t in obj.tournaments)
                    return PolymorphicScore(total)
                if isinstance(obj, dict):
                    return PolymorphicScore(
                        obj.get('attendance', obj.get('num_attendees', 
                               obj.get('total_attendance', 0)))
                    )
                return PolymorphicScore(0)
            return attendance_scorer
        
        # RECENT/TIME
        if hint_type == ScoringHint.RECENT:
            def recency_scorer(obj):
                # Try to get a timestamp or date
                if hasattr(obj, 'start_at'):
                    return PolymorphicScore(obj.start_at or 0)
                if hasattr(obj, 'created_at'):
                    return PolymorphicScore(obj.created_at or 0)
                if hasattr(obj, 'date'):
                    return PolymorphicScore(obj.date)
                if hasattr(obj, 'timestamp'):
                    return PolymorphicScore(obj.timestamp)
                if isinstance(obj, dict):
                    return PolymorphicScore(
                        obj.get('start_at', obj.get('date', 
                               obj.get('timestamp', 0)))
                    )
                return PolymorphicScore(0)
            return recency_scorer
        
        # ALPHABETICAL
        if hint_type == ScoringHint.ALPHABETICAL:
            def alpha_scorer(obj):
                # Get name for alphabetical sorting
                if hasattr(obj, 'name'):
                    return PolymorphicScore(obj.name or '')
                if hasattr(obj, 'gamer_tag'):
                    return PolymorphicScore(obj.gamer_tag or '')
                if hasattr(obj, 'display_name'):
                    return PolymorphicScore(obj.display_name or '')
                if isinstance(obj, dict):
                    return PolymorphicScore(
                        obj.get('name', obj.get('gamer_tag', 
                               obj.get('display_name', '')))
                    )
                return PolymorphicScore(str(obj))
            return alpha_scorer
        
        # LARGEST/SIZE
        if hint_type == ScoringHint.LARGEST:
            def size_scorer(obj):
                # Try to get size/count
                if hasattr(obj, '__len__'):
                    return PolymorphicScore(len(obj))
                if hasattr(obj, 'size'):
                    return PolymorphicScore(obj.size)
                if hasattr(obj, 'count'):
                    return PolymorphicScore(obj.count)
                if hasattr(obj, 'num_attendees'):
                    return PolymorphicScore(obj.num_attendees or 0)
                if isinstance(obj, (int, float)):
                    return PolymorphicScore(obj)
                return PolymorphicScore(0)
            return size_scorer
        
        # Default: try to extract a number from the hint
        # e.g., "by tournament_count" -> look for tournament_count attribute
        words = hint.lower().split()
        for word in words:
            # Remove common words
            word = word.strip('by').strip('most').strip('highest')
            if word and len(word) > 2:
                def attr_scorer(obj, attr=word):
                    if hasattr(obj, attr):
                        val = getattr(obj, attr)
                        if callable(val):
                            val = val()
                        return PolymorphicScore(val or 0)
                    if isinstance(obj, dict):
                        return PolymorphicScore(obj.get(attr, 0))
                    return PolymorphicScore(0)
                return attr_scorer
        
        # Fallback to introspection
        return cls._introspect_scorer(sample_obj)
    
    @classmethod
    def _introspect_scorer(cls, sample_obj: Any) -> Callable:
        """Figure out how to score an object by introspection"""
        
        # For numbers, score is the number itself
        if isinstance(sample_obj, (int, float)):
            return lambda obj: PolymorphicScore(obj)
        
        # For strings, alphabetical
        if isinstance(sample_obj, str):
            return lambda obj: PolymorphicScore(obj)
        
        # For dates/times, use the timestamp
        if isinstance(sample_obj, (datetime, date)):
            return lambda obj: PolymorphicScore(obj)
        
        # For dicts, look for common scoring keys
        if isinstance(sample_obj, dict):
            scoring_keys = ['score', 'points', 'total', 'value', 'count', 'rank']
            for key in scoring_keys:
                if key in sample_obj:
                    return lambda obj: PolymorphicScore(obj.get(key, 0))
            # No scoring key found, use first numeric value
            for key, val in sample_obj.items():
                if isinstance(val, (int, float)):
                    return lambda obj: PolymorphicScore(obj.get(key, 0))
        
        # For objects, look for scoring attributes
        if hasattr(sample_obj, '__dict__'):
            # Look for methods/properties that suggest scoring
            scoring_attrs = []
            for attr_name in dir(sample_obj):
                if attr_name.startswith('_'):
                    continue
                
                # Check for scoring-related names
                if any(word in attr_name.lower() for word in 
                       ['points', 'score', 'total', 'count', 'wins', 'rank']):
                    attr = getattr(sample_obj, attr_name)
                    # If it's a method, check if it takes no args
                    if callable(attr):
                        sig = inspect.signature(attr)
                        if len(sig.parameters) == 0:
                            scoring_attrs.append(attr_name)
                    else:
                        scoring_attrs.append(attr_name)
            
            # Use the first scoring attribute found
            if scoring_attrs:
                attr_name = scoring_attrs[0]
                def obj_scorer(obj):
                    if hasattr(obj, attr_name):
                        val = getattr(obj, attr_name)
                        if callable(val):
                            try:
                                val = val()
                            except:
                                val = 0
                        return PolymorphicScore(val or 0)
                    return PolymorphicScore(0)
                return obj_scorer
            
            # Look for numeric attributes
            for attr_name in dir(sample_obj):
                if not attr_name.startswith('_'):
                    try:
                        val = getattr(sample_obj, attr_name)
                        if isinstance(val, (int, float)) and not callable(val):
                            return lambda obj: PolymorphicScore(
                                getattr(obj, attr_name, 0)
                            )
                    except:
                        pass
        
        # Ultimate fallback: hash value (stable within session)
        return lambda obj: PolymorphicScore(hash(str(obj)))
    
    @classmethod
    def _should_reverse(cls, hint: Union[str, List[str]]) -> bool:
        """Determine sort direction from hint"""
        if isinstance(hint, list):
            hint = hint[0]  # Use first hint for direction
        
        hint_lower = hint.lower()
        
        # Ascending hints (smallest to largest, A to Z)
        ascending_words = ['ascending', 'smallest', 'least', 'oldest', 
                          'earliest', 'alphabetical', 'a-z', 'first']
        if any(word in hint_lower for word in ascending_words):
            return False
        
        # Default to descending (largest to smallest) for most rankings
        return True
    
    @classmethod
    def multi_tabulate(cls, 
                       objects: List[Any],
                       criteria: List[Union[str, Callable]]) -> List[Tuple[int, Any, List[Any]]]:
        """
        Tabulate with multiple criteria (like SQL ORDER BY col1, col2, col3)
        
        Args:
            objects: List of objects to rank
            criteria: List of hints or scoring functions in priority order
            
        Returns:
            List of (rank, object, [scores]) tuples
        """
        if not objects or not criteria:
            return []
        
        # Create scorers for each criterion
        scorers = []
        for criterion in criteria:
            if callable(criterion):
                scorers.append(criterion)
            else:
                scorers.append(cls._create_scorer_from_hint(objects[0], criterion))
        
        # Score objects on all criteria
        scored = []
        for obj in objects:
            scores = []
            for scorer in scorers:
                try:
                    score = scorer(obj)
                    if not isinstance(score, PolymorphicScore):
                        score = PolymorphicScore(primary=score)
                    scores.append(score.primary)
                except:
                    scores.append(0)
            scored.append((scores, obj))
        
        # Sort by all criteria
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Assign ranks
        ranked = []
        prev_scores = None
        prev_rank = 0
        
        for i, (scores, obj) in enumerate(scored, 1):
            if scores != prev_scores:
                rank = i
                prev_rank = i
            else:
                rank = prev_rank
            
            ranked.append((rank, obj, scores))
            prev_scores = scores
        
        return ranked


# Convenience function for easy use
def tabulate(objects: Any, hint: Any = None) -> List[Tuple[int, Any, Any]]:
    """
    Quick tabulation of anything!
    
    Examples:
        # Just throw objects at it
        tabulate([5, 2, 8, 1])  # Numbers
        tabulate(["zebra", "apple", "banana"])  # Strings
        tabulate(players, "most wins")  # Models with hint
        tabulate(tournaments, ["recent", "largest"])  # Multiple criteria
    """
    return PolymorphicTabulator.tabulate(objects, hint)


if __name__ == "__main__":
    print("=" * 60)
    print("POLYMORPHIC TABULATOR DEMO")
    print("=" * 60)
    
    # Demo 1: Numbers (no hint needed)
    print("\n1. Tabulating raw numbers:")
    numbers = [42, 17, 99, 17, 3, 88]
    for rank, num, score in tabulate(numbers):
        tie = " (tie)" if rank > 1 and score == tabulate(numbers)[rank-2][2] else ""
        print(f"  Rank {rank}: {num}{tie}")
    
    # Demo 2: Strings (alphabetical by default)
    print("\n2. Tabulating strings (auto-alphabetical):")
    words = ["zebra", "apple", "banana", "apple", "cherry"]
    for rank, word, score in tabulate(words, "alphabetical"):
        print(f"  Rank {rank}: {word}")
    
    # Demo 3: Dicts with hint
    print("\n3. Tabulating dicts with hint:")
    players = [
        {"name": "Alice", "wins": 5, "points": 45},
        {"name": "Bob", "wins": 8, "points": 30},
        {"name": "Charlie", "wins": 5, "points": 50},
    ]
    for rank, player, score in tabulate(players, "most wins"):
        print(f"  Rank {rank}: {player['name']} with {score} wins")
    
    # Demo 4: Mixed types (handles gracefully)
    print("\n4. Tabulating mixed types:")
    mixed = [42, "hello", {"value": 17}, 3.14, [1, 2, 3]]
    for rank, item, score in tabulate(mixed):
        print(f"  Rank {rank}: {type(item).__name__} - {item}")
    
    # Demo 5: Multi-criteria
    print("\n5. Multi-criteria ranking:")
    teams = [
        {"name": "Eagles", "wins": 10, "points": 250},
        {"name": "Bears", "wins": 10, "points": 200},
        {"name": "Lions", "wins": 8, "points": 300},
    ]
    for rank, team, scores in PolymorphicTabulator.multi_tabulate(teams, ["wins", "points"]):
        print(f"  Rank {rank}: {team['name']} (wins={scores[0]}, points={scores[1]})")
    
    print("\n" + "=" * 60)
    print("TRUE POLYMORPHISM - Ranks ANYTHING without caring what it is!")
    print("=" * 60)