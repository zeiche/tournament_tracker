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
    
    def get_attendance_rankings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get attendance rankings for reporting"""
        with self.session_scope() as session:
            from tournament_models import Organization, Tournament
            
            # Get all tournaments to calculate attendance
            all_tournaments = session.query(Tournament).all()
            
            # Group tournaments by their matching organizations
            org_attendance = {}
            
            for tournament in all_tournaments:
                # Find which org this tournament belongs to (if any)
                org_match = None
                primary_contact = tournament.primary_contact
                
                if primary_contact:
                    # Check all organizations for a matching contact
                    orgs = session.query(Organization).all()
                    for org in orgs:
                        for contact in org.contacts:
                            if contact.get('value') and contact['value'].lower() in primary_contact.lower():
                                org_match = org.display_name
                                break
                        if org_match:
                            break
                
                # If no org match, use primary contact as org name
                if not org_match:
                    org_match = primary_contact or 'Unknown'
                
                # Add to totals
                if org_match not in org_attendance:
                    org_attendance[org_match] = {
                        'display_name': org_match,
                        'tournament_count': 0,
                        'total_attendance': 0,
                        'tournaments': []
                    }
                
                org_attendance[org_match]['tournament_count'] += 1
                org_attendance[org_match]['total_attendance'] += tournament.num_attendees or 0
                org_attendance[org_match]['tournaments'].append(tournament.name)
            
            # Convert to list and calculate averages
            rankings = []
            for org_name, data in org_attendance.items():
                rankings.append({
                    'display_name': data['display_name'],
                    'tournament_count': data['tournament_count'],
                    'total_attendance': data['total_attendance'],
                    'avg_attendance': data['total_attendance'] / data['tournament_count'] if data['tournament_count'] > 0 else 0
                })
            
            # Sort by total attendance
            rankings.sort(key=lambda x: x['total_attendance'], reverse=True)
            
            if limit:
                rankings = rankings[:limit]
            
            return rankings


# Singleton instance - import this
database_service = DatabaseService()