#!/usr/bin/env python3
"""
Event name standardization for tournament tracker
Maps various event names to standardized categories
"""

import re
from typing import Optional, Tuple

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.event_standardizer")

class EventStandardizer:
    """Standardize event names to consistent categories"""
    
    # Game detection patterns
    GAME_PATTERNS = {
        'ultimate': [
            r'ultimate', r'ssbu', r'smash\s*bros\s*ultimate', r'smash\s*ultimate',
            r'uas\b', r'apex.*series'  # UAS = Ultimate Apex Series
        ],
        'melee': [
            r'melee', r'ssbm', r'smash\s*bros\s*melee'
        ],
        'sf6': [
            r'sf\s*6', r'sf6', r'street\s*fighter\s*6', r'sfvi'
        ],
        'tekken8': [
            r'tekken\s*8', r't8\b', r'tk8'
        ],
        'tekken7': [
            r'tekken\s*7', r't7\b', r'tk7'
        ],
        'strive': [
            r'strive', r'ggst', r'guilty\s*gear\s*strive'
        ],
        'dbfz': [
            r'dbfz', r'dragon\s*ball\s*fighterz', r'fighterz'
        ],
        'mvc': [
            r'mvc', r'marvel', r'umvc', r'mvc3'
        ],
        'kof': [
            r'kof', r'king\s*of\s*fighters'
        ]
    }
    
    # Format detection patterns
    FORMAT_PATTERNS = {
        'singles': [
            r'singles?', r'1v1', r'solo',
            r'^[^:]*tournament$',  # Generic "Tournament" usually means singles
            r'^[^:]*bracket$',  # Generic "Bracket" usually means singles
            r'^ultimate\s*$',  # Just "Ultimate" usually means singles
            r'^ssbu\s*$',  # Just "SSBU" usually means singles
        ],
        'doubles': [
            r'doubles?', r'2v2', r'teams?', r'duos?'
        ],
        'squad_strike': [
            r'squad\s*strike', r'squad'
        ],
        'crews': [
            r'crew\s*battle', r'crew', r'3v3', r'4v4', r'5v5'
        ]
    }
    
    # Special event patterns (not regular competitive brackets)
    SPECIAL_PATTERNS = [
        r'arcadian',  # Beginners only
        r'elementary', r'middle\s*school', r'high\s*school',  # School brackets
        r'amateur', r'novice', r'beginner',
        r'finale', r'championship', r'grand\s*finals?',
        r'last\s*apex\s*standing', r'\blas\b',  # Special UAS format
        r'side\s*bracket', r'redemption',
        r'crew\s*battle'
    ]
    
    @classmethod
    def standardize(cls, event_name: str) -> dict:
        """
        Standardize an event name into categories
        
        Returns dict with:
        - game: Detected game (e.g., 'ultimate', 'sf6')
        - format: Event format ('singles', 'doubles', 'crews')
        - is_special: Whether this is a special/side event
        - standard_name: Standardized name for grouping
        """
        if not event_name:
            return {
                'game': 'unknown',
                'format': 'unknown',
                'is_special': False,
                'standard_name': 'Unknown'
            }
        
        event_lower = event_name.lower().strip()
        
        # Detect game
        game = cls._detect_game(event_lower)
        
        # Detect format
        format_type = cls._detect_format(event_lower)
        
        # Check if special event
        is_special = cls._is_special(event_lower)
        
        # Generate standardized name
        standard_name = cls._generate_standard_name(game, format_type, is_special)
        
        return {
            'original': event_name,
            'game': game,
            'format': format_type,
            'is_special': is_special,
            'standard_name': standard_name
        }
    
    @classmethod
    def _detect_game(cls, event_lower: str) -> str:
        """Detect which game this event is for"""
        for game, patterns in cls.GAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, event_lower):
                    return game
        return 'unknown'
    
    @classmethod
    def _detect_format(cls, event_lower: str) -> str:
        """Detect the format of the event"""
        # Check explicit format patterns
        for format_type, patterns in cls.FORMAT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, event_lower):
                    return format_type
        
        # Default heuristics
        # If it's a tournament/bracket without other qualifiers, assume singles
        if re.search(r'tournament|bracket', event_lower):
            # But not if it's a school bracket
            if not re.search(r'elementary|middle|high\s*school', event_lower):
                return 'singles'
        
        return 'unknown'
    
    @classmethod
    def _is_special(cls, event_lower: str) -> bool:
        """Check if this is a special/side event"""
        for pattern in cls.SPECIAL_PATTERNS:
            if re.search(pattern, event_lower):
                return True
        return False
    
    @classmethod
    def _generate_standard_name(cls, game: str, format_type: str, is_special: bool) -> str:
        """Generate a standardized name for grouping"""
        if game == 'unknown' and format_type == 'unknown':
            return 'Other'
        
        parts = []
        
        # Add game name (capitalize properly)
        game_names = {
            'ultimate': 'Ultimate',
            'melee': 'Melee',
            'sf6': 'SF6',
            'tekken8': 'Tekken 8',
            'tekken7': 'Tekken 7',
            'strive': 'Strive',
            'dbfz': 'DBFZ',
            'mvc': 'MvC',
            'kof': 'KOF',
            'unknown': 'Mixed'
        }
        parts.append(game_names.get(game, game.title()))
        
        # Add format
        if format_type != 'unknown':
            if format_type == 'squad_strike':
                parts.append('Squad Strike')
            else:
                parts.append(format_type.title())
        
        # Add special indicator
        if is_special:
            parts.append('(Special)')
        
        return ' '.join(parts)


def test_standardizer():
    """Test the event standardizer with sample data"""
    test_events = [
        "Ultimate Singles",
        "Ultimate Doubles", 
        "Ultimate Apex Series Finale",
        "UAS: Last Apex Standing (LAS)",
        "UAS: Doubles",
        "UAS: Arcadian",
        "GEEX Super Smash Ultimate Tournament",
        "(3/23/2025) Smash Bros Ultimate Tournament",
        "SSB Ultimate Elementary Bracket",
        "SF6 Singles",
        "Tekken 8 Tournament",
        "GGST Singles Bracket",
        "MvC3 Teams",
        "Random Fighting Game Event"
    ]
    
    print("Event Standardization Test Results:")
    print("=" * 80)
    
    for event in test_events:
        result = EventStandardizer.standardize(event)
        print(f"\nOriginal: {event}")
        print(f"  Game: {result['game']}")
        print(f"  Format: {result['format']}")
        print(f"  Special: {result['is_special']}")
        print(f"  Standard Name: {result['standard_name']}")


if __name__ == "__main__":
    test_standardizer()