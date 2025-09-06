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
                
                # If no org match, normalize and use primary contact as org name
                if not org_match:
                    if primary_contact:
                        # Normalize the contact for display
                        normalized = self.normalize_contact(primary_contact)
                        # For display, convert discord codes and emails to better names
                        if 'discord.gg/' in primary_contact.lower() or 'discord.com/' in primary_contact.lower():
                            # Extract the invite code
                            org_match = f"Discord Group ({normalized})"
                        elif '@' in primary_contact:
                            # Use the part before @ for email addresses
                            username = primary_contact.split('@')[0]
                            # Clean up the username for display
                            org_match = username.replace('.', ' ').replace('_', ' ').replace('-', ' ').title()
                        else:
                            org_match = primary_contact
                    else:
                        org_match = 'Unknown'
                
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
    
    def get_organizations_with_stats(self) -> List[Dict[str, Any]]:
        """Get Organization objects with their tournament statistics - matches editor_service logic"""
        from tournament_models import Organization, Tournament, normalize_contact
        
        with self.session_scope() as session:
            # Get all tournaments and organizations
            tournaments = session.query(Tournament).all()
            organizations = session.query(Organization).all()
            
            # Build contact map (normalized contact -> org display name)
            contact_to_org = {}
            for org in organizations:
                for contact in org.contacts:
                    contact_value = contact.get('value', '')
                    if contact_value:
                        normalized = normalize_contact(contact_value)
                        if normalized:
                            contact_to_org[normalized] = org.display_name
            
            # Build organization stats by checking each tournament
            org_aggregated = {}
            
            for tournament in tournaments:
                # Try to match tournament to organization via contact
                org_name = None
                
                if tournament.primary_contact:
                    normalized = normalize_contact(tournament.primary_contact)
                    if normalized in contact_to_org:
                        org_name = contact_to_org[normalized]
                
                if not org_name:
                    # Fall back to owner_name if no organization found (matches editor_service)
                    org_name = tournament.owner_name or "Unknown"
                
                # Aggregate stats by organization name
                if org_name not in org_aggregated:
                    org_aggregated[org_name] = {
                        'display_name': org_name,
                        'tournament_count': 0,
                        'total_attendance': 0
                    }
                org_aggregated[org_name]['tournament_count'] += 1
                org_aggregated[org_name]['total_attendance'] += (tournament.num_attendees or 0)
            
            # Convert to list format
            result = []
            for org_name, stats in org_aggregated.items():
                result.append({
                    'organization': {
                        'id': None,  # May not have an ID if using owner_name
                        'display_name': stats['display_name'],
                        'contacts': []
                    },
                    'tournament_count': stats['tournament_count'],
                    'total_attendance': stats['total_attendance']
                })
            
            # Sort by total attendance
            result.sort(key=lambda x: x['total_attendance'], reverse=True)
            
            return result
    
    def get_recent_tournaments(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get recent tournaments within specified days"""
        from tournament_models import Tournament
        from datetime import datetime, timedelta
        
        with self.session_scope() as session:
            cutoff = datetime.now() - timedelta(days=days)
            cutoff_timestamp = int(cutoff.timestamp())
            
            tournaments = session.query(Tournament).filter(
                Tournament.start_at >= cutoff_timestamp
            ).order_by(Tournament.start_at.desc()).all()
            
            # Convert to dictionaries to avoid session issues
            result = []
            for t in tournaments:
                result.append({
                    'id': t.id,
                    'name': t.name,
                    'start_at': t.start_at,
                    'start_date': datetime.fromtimestamp(t.start_at) if t.start_at else None,
                    'num_attendees': t.num_attendees,
                    'venue_name': t.venue_name,
                    'city': t.city,
                    'state': t.addr_state,
                    'lat': t.lat,
                    'lng': t.lng
                })
            
            return result
    
    def get_player_rankings(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get player rankings with points and statistics"""
        from tournament_models import Player, TournamentPlacement
        
        with self.session_scope() as session:
            # Get all players
            players = session.query(Player).all()
            
            rankings = []
            for player in players:
                # Calculate points from placements
                total_points = 0
                first_places = 0
                top_3s = 0
                event_count = 0
                
                for placement in player.placements:
                    total_points += placement.get_points()
                    event_count += 1
                    if placement.placement == 1:
                        first_places += 1
                    if placement.placement <= 3:
                        top_3s += 1
                
                if total_points > 0:
                    rankings.append({
                        'player_id': player.id,
                        'name': player.name,
                        'points': total_points,
                        'events': event_count,
                        'first_places': first_places,
                        'top_3s': top_3s,
                        'win_rate': (first_places / event_count * 100) if event_count > 0 else 0,
                        'podium_rate': (top_3s / event_count * 100) if event_count > 0 else 0
                    })
            
            # Sort by points
            rankings.sort(key=lambda x: x['points'], reverse=True)
            
            return rankings[:limit] if limit else rankings
    
    def get_tournament_by_id(self, tournament_id: int) -> Optional[Any]:
        """Get a tournament by ID"""
        from tournament_models import Tournament
        with self.session_scope() as session:
            return session.query(Tournament).get(tournament_id)
    
    def get_tournaments_with_location(self, limit: Optional[int] = None) -> List[Any]:
        """Get tournaments that have location data"""
        from tournament_models import Tournament
        with self.session_scope() as session:
            query = session.query(Tournament).filter(
                Tournament.lat.isnot(None),
                Tournament.lng.isnot(None)
            )
            if limit:
                query = query.limit(limit)
            return query.all()
    
    def get_tournament_heatmap_data(self) -> List[tuple]:
        """Get tournament data formatted for heatmap visualization"""
        from tournament_models import Tournament
        points = []
        with self.session_scope() as session:
            tournaments = session.query(Tournament).filter(
                Tournament.lat.isnot(None),
                Tournament.lng.isnot(None)
            ).all()
            
            for t in tournaments:
                if hasattr(t, 'lat') and hasattr(t, 'lng'):
                    weight = t.get_heatmap_weight() if hasattr(t, 'get_heatmap_weight') else 1.0
                    points.append((t.lat, t.lng, weight, str(t)))
        
        return points


# Singleton instance - import this
database_service = DatabaseService()