"""
database_service.py - Pythonic OOP Database Service
Replaces procedural database_utils.py with proper class structure
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import func, case, desc, distinct

# Use existing SSOT database module
from database import session_scope


@dataclass
class DatabaseStats:
    """Statistics about the database"""
    total_organizations: int
    total_tournaments: int
    total_players: int
    total_placements: int
    tournaments_with_standings: int


class DatabaseService:
    """Pythonic OOP replacement for database_utils.py"""
    
    _instance: Optional['DatabaseService'] = None
    
    def __new__(cls) -> 'DatabaseService':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @contextmanager
    def session_scope(self):
        """Context manager for database sessions"""
        with session_scope() as session:
            yield session
    
    @staticmethod
    def normalize_contact(contact: str) -> str:
        """Normalize contact for comparison"""
        if not contact:
            return ""
        
        contact = contact.lower().strip()
        
        # Remove common prefixes
        for prefix in ['https://', 'http://', 'www.', '@']:
            if contact.startswith(prefix):
                contact = contact[len(prefix):]
        
        # Clean discord invites
        if 'discord.gg/' in contact:
            contact = contact.split('discord.gg/')[-1]
        if 'discord.com/invite/' in contact:
            contact = contact.split('invite/')[-1]
        
        return contact.rstrip('/')
    
    def get_summary_stats(self) -> DatabaseStats:
        """Get database summary statistics"""
        from tournament_models import Tournament, Organization, Player, TournamentPlacement
        
        with self.session_scope() as session:
            return DatabaseStats(
                total_organizations=session.query(Organization).count(),
                total_tournaments=session.query(Tournament).count(),
                total_players=session.query(Player).count(),
                total_placements=session.query(TournamentPlacement).count(),
                tournaments_with_standings=session.query(Tournament).join(
                    TournamentPlacement
                ).distinct().count()
            )


# Singleton instance - import this
database_service = DatabaseService()