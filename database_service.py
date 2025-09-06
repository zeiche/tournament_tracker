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
        """Context manager for database sessions - for complex operations only"""
        from database import session_scope
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
    
    def get_all_tournaments(self) -> List[Any]:
        """Get all tournaments"""
        from tournament_models import Tournament
        with self.session_scope() as session:
            return session.query(Tournament).all()
    
    def get_all_organizations(self) -> List[Any]:
        """Get all organizations"""
        from tournament_models import Organization
        with self.session_scope() as session:
            return session.query(Organization).all()
    
    def get_all_players(self) -> List[Any]:
        """Get all players"""
        from tournament_models import Player
        with self.session_scope() as session:
            return session.query(Player).all()
    
    def get_organization_by_id(self, org_id: int) -> Optional[Any]:
        """Get organization by ID"""
        from tournament_models import Organization
        with self.session_scope() as session:
            return session.query(Organization).get(org_id)
    
    def get_player_by_id(self, player_id: int) -> Optional[Any]:
        """Get player by ID"""
        from tournament_models import Player
        with self.session_scope() as session:
            return session.query(Player).get(player_id)
    
    def get_tournament_placements(self, tournament_id: int) -> List[Any]:
        """Get all placements for a tournament"""
        from tournament_models import TournamentPlacement
        with self.session_scope() as session:
            return session.query(TournamentPlacement).filter_by(
                tournament_id=tournament_id
            ).order_by(TournamentPlacement.placement).all()
    
    def upsert_tournament(self, tournament_data: Dict[str, Any]) -> Any:
        """Create or update a tournament"""
        from tournament_models import Tournament
        with self.session_scope() as session:
            tournament_id = tournament_data.get('id')
            if tournament_id:
                existing = session.query(Tournament).get(tournament_id)
                if existing:
                    for key, value in tournament_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    session.commit()
                    return existing
            
            # Create new
            tournament = Tournament(**tournament_data)
            session.add(tournament)
            session.commit()
            return tournament
    
    def get_or_create_player(self, startgg_id: str, gamer_tag: str, name: Optional[str] = None) -> Any:
        """Get existing player or create new one"""
        from tournament_models import Player
        with self.session_scope() as session:
            player = session.query(Player).filter_by(startgg_id=startgg_id).first()
            if not player:
                player = Player(startgg_id=startgg_id, gamertag=gamer_tag, name=name)
                session.add(player)
                session.commit()
            return player
    
    def update_organization(self, org_id: int, display_name: Optional[str] = None, 
                           contacts_json: Optional[str] = None) -> bool:
        """Update organization details"""
        from tournament_models import Organization
        with self.session_scope() as session:
            org = session.query(Organization).get(org_id)
            if org:
                if display_name:
                    org.display_name = display_name
                if contacts_json is not None:
                    org.contacts_json = contacts_json
                session.commit()
                return True
            return False
    
    def merge_organizations(self, source_id: int, target_id: int) -> bool:
        """Merge source organization into target"""
        from tournament_models import Tournament, Organization
        with self.session_scope() as session:
            source = session.query(Organization).get(source_id)
            target = session.query(Organization).get(target_id)
            
            if not source or not target:
                return False
            
            # Move all tournaments from source to target
            session.query(Tournament).filter_by(
                organization_id=source_id
            ).update({'organization_id': target_id})
            
            # Delete source organization
            session.delete(source)
            session.commit()
            return True
    
    def create_organization(self, display_name: str, contacts_json: str = '[]') -> Any:
        """Create a new organization"""
        from tournament_models import Organization
        with self.session_scope() as session:
            org = Organization(display_name=display_name, contacts_json=contacts_json)
            session.add(org)
            session.commit()
            return org
    
    def get_tournaments_by_organization(self, org_id: int) -> List[Any]:
        """Get all tournaments for an organization"""
        from tournament_models import Tournament
        with self.session_scope() as session:
            return session.query(Tournament).filter_by(organization_id=org_id).all()
    
    def get_player_placements(self, player_id: int) -> List[Any]:
        """Get all tournament placements for a player"""
        from tournament_models import TournamentPlacement
        with self.session_scope() as session:
            return session.query(TournamentPlacement).filter_by(
                player_id=player_id
            ).order_by(TournamentPlacement.placement).all()
    
    def bulk_get_or_create_players(self, players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk create or get players"""
        from tournament_models import Player
        created = []
        existing = []
        
        with self.session_scope() as session:
            for player_data in players_data:
                startgg_id = player_data.get('startgg_id')
                if startgg_id:
                    player = session.query(Player).filter_by(startgg_id=startgg_id).first()
                    if player:
                        existing.append(player)
                    else:
                        player = Player(**player_data)
                        session.add(player)
                        created.append(player)
            
            session.commit()
        
        return {'created': created, 'existing': existing}
    
    def get_tournaments_needing_standings(self, limit: int = 10) -> List[Any]:
        """Get tournaments that don't have standings fetched yet"""
        from tournament_models import Tournament
        from sqlalchemy import and_, or_
        
        with self.session_scope() as session:
            return session.query(Tournament).filter(
                or_(
                    Tournament.standings_fetched == False,
                    Tournament.standings_fetched.is_(None)
                )
            ).limit(limit).all()


# Singleton instance - import this
database_service = DatabaseService()