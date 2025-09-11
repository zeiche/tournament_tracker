#!/usr/bin/env python3
"""
Fuzzy Search Utility Module
Provides fuzzy matching capabilities for all user-facing searches in the tournament tracker.
Uses multiple algorithms for best match quality.
"""

import re
from typing import List, Tuple, Optional, Any, Dict, Union
from difflib import SequenceMatcher, get_close_matches
from dataclasses import dataclass
import unicodedata


@dataclass
class FuzzyMatch:
    """Represents a fuzzy match result"""
    original: str
    matched: str
    score: float
    item: Any = None  # The original object/row that was matched
    
    def __repr__(self):
        return f"FuzzyMatch('{self.matched}', score={self.score:.2f})"


class FuzzySearcher:
    """
    Universal fuzzy search handler for the tournament tracker.
    Provides multiple search algorithms and smart fallbacks.
    """
    
    def __init__(self, threshold: float = 0.6):
        """
        Initialize fuzzy searcher
        
        Args:
            threshold: Minimum similarity score (0-1) to consider a match
        """
        self.threshold = threshold
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for better matching
        - Lowercase
        - Remove accents/diacritics
        - Collapse whitespace
        - Remove special characters (optional)
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove accents/diacritics
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        # Collapse multiple spaces to single space
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings
        Uses SequenceMatcher for detailed comparison
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def fuzzy_match(
        self,
        query: str,
        candidates: List[str],
        limit: int = 10,
        cutoff: Optional[float] = None
    ) -> List[FuzzyMatch]:
        """
        Find fuzzy matches for a query in a list of candidates
        
        Args:
            query: Search query
            candidates: List of strings to search in
            limit: Maximum number of results
            cutoff: Override threshold for this search
        
        Returns:
            List of FuzzyMatch objects sorted by score
        """
        if not query or not candidates:
            return []
        
        cutoff = cutoff or self.threshold
        query_norm = self.normalize_text(query)
        
        matches = []
        for candidate in candidates:
            if not candidate:
                continue
            
            candidate_norm = self.normalize_text(candidate)
            
            # Try multiple matching strategies
            scores = []
            
            # 1. Exact substring match (highest priority)
            if query_norm in candidate_norm:
                scores.append(1.0)
            
            # 2. Starts with query
            elif candidate_norm.startswith(query_norm):
                scores.append(0.9)
            
            # 3. All query words present
            elif all(word in candidate_norm for word in query_norm.split()):
                scores.append(0.85)
            
            # 4. Sequence matching (handles typos)
            else:
                scores.append(self.calculate_similarity(query_norm, candidate_norm))
            
            # 5. Token-based matching (words in different order)
            query_tokens = set(query_norm.split())
            candidate_tokens = set(candidate_norm.split())
            if query_tokens and candidate_tokens:
                token_score = len(query_tokens & candidate_tokens) / len(query_tokens)
                scores.append(token_score * 0.8)
            
            # Take the best score
            best_score = max(scores)
            
            if best_score >= cutoff:
                matches.append(FuzzyMatch(
                    original=query,
                    matched=candidate,
                    score=best_score
                ))
        
        # Sort by score descending
        matches.sort(key=lambda x: x.score, reverse=True)
        
        return matches[:limit]
    
    def fuzzy_match_objects(
        self,
        query: str,
        objects: List[Any],
        key_func: callable,
        limit: int = 10,
        cutoff: Optional[float] = None
    ) -> List[FuzzyMatch]:
        """
        Find fuzzy matches for objects using a key function
        
        Args:
            query: Search query
            objects: List of objects to search
            key_func: Function to extract searchable text from each object
            limit: Maximum number of results
            cutoff: Override threshold
        
        Returns:
            List of FuzzyMatch objects with the original objects attached
        """
        if not query or not objects:
            return []
        
        # Extract searchable text from objects
        candidates_with_objects = [(key_func(obj), obj) for obj in objects]
        candidates = [text for text, _ in candidates_with_objects]
        
        # Get matches
        matches = self.fuzzy_match(query, candidates, limit=limit, cutoff=cutoff)
        
        # Attach original objects to matches
        for match in matches:
            for text, obj in candidates_with_objects:
                if text == match.matched:
                    match.item = obj
                    break
        
        return matches
    
    def smart_search(
        self,
        query: str,
        data: Union[List[str], List[Any]],
        key_func: Optional[callable] = None,
        limit: int = 10
    ) -> List[FuzzyMatch]:
        """
        Smart search that adapts threshold based on results
        
        If no results with default threshold, progressively lower it
        """
        # Determine if we're searching strings or objects
        if key_func:
            search_func = lambda cutoff: self.fuzzy_match_objects(
                query, data, key_func, limit=limit, cutoff=cutoff
            )
        else:
            search_func = lambda cutoff: self.fuzzy_match(
                query, data, limit=limit, cutoff=cutoff
            )
        
        # Try with progressively lower thresholds
        thresholds = [0.8, 0.7, 0.6, 0.5, 0.4]
        
        for threshold in thresholds:
            results = search_func(threshold)
            if results:
                return results
        
        # If still no results, return best matches regardless of score
        return search_func(0.0)[:limit]


# Global instance for easy access
fuzzy_searcher = FuzzySearcher()


# Convenience functions
def fuzzy_search(query: str, candidates: List[str], limit: int = 10) -> List[str]:
    """
    Simple fuzzy search returning matched strings
    
    Args:
        query: Search query
        candidates: List of strings to search
        limit: Maximum results
    
    Returns:
        List of matched strings
    """
    matches = fuzzy_searcher.fuzzy_match(query, candidates, limit)
    return [m.matched for m in matches]


def fuzzy_search_objects(
    query: str,
    objects: List[Any],
    key_func: callable,
    limit: int = 10
) -> List[Any]:
    """
    Fuzzy search objects, returning the objects themselves
    
    Args:
        query: Search query
        objects: List of objects to search
        key_func: Function to extract searchable text
        limit: Maximum results
    
    Returns:
        List of matched objects
    """
    matches = fuzzy_searcher.fuzzy_match_objects(query, objects, key_func, limit)
    return [m.item for m in matches if m.item is not None]


def fuzzy_find_best(query: str, candidates: List[str]) -> Optional[str]:
    """
    Find single best fuzzy match
    
    Args:
        query: Search query
        candidates: List of strings to search
    
    Returns:
        Best match or None if no good matches
    """
    matches = fuzzy_searcher.fuzzy_match(query, candidates, limit=1)
    return matches[0].matched if matches else None


# Database integration helpers
def create_fuzzy_filter(column, query: str, threshold: float = 0.6):
    """
    Create a SQLAlchemy filter for fuzzy matching
    This is a simple version - for true fuzzy DB search, use PostgreSQL extensions
    """
    from sqlalchemy import or_, func
    
    query_norm = FuzzySearcher.normalize_text(query)
    
    # Multiple search strategies
    filters = [
        func.lower(column).contains(query_norm),  # Substring match
        func.lower(column).startswith(query_norm),  # Prefix match
    ]
    
    # Add word-based search for multi-word queries
    words = query_norm.split()
    if len(words) > 1:
        for word in words:
            if len(word) > 2:  # Skip very short words
                filters.append(func.lower(column).contains(word))
    
    return or_(*filters)


# Test function
def test_fuzzy_search():
    """Test fuzzy search functionality"""
    
    # Test data
    players = [
        "John Smith",
        "Johnny Appleseed", 
        "Jane Doe",
        "Jon Snow",
        "Jonathan Williams",
        "Smith Johnson"
    ]
    
    print("Testing Fuzzy Search")
    print("=" * 50)
    
    # Test cases
    test_queries = [
        "john",      # Should match John, Johnny, Jonathan, Johnson
        "smth",      # Typo for Smith
        "jon snow",  # Exact match
        "snow jon",  # Words reversed
        "jane d",    # Partial match
        "johny",     # Typo for Johnny
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        matches = fuzzy_searcher.fuzzy_match(query, players, limit=3)
        for match in matches:
            print(f"  {match}")
    
    print("\n" + "=" * 50)
    print("Smart search (adaptive threshold):")
    
    # Test smart search
    results = fuzzy_searcher.smart_search("smithy", players)  # No exact match
    print(f"Query: 'smithy'")
    for match in results:
        print(f"  {match}")


if __name__ == "__main__":
    test_fuzzy_search()