"""
database_service.py - Pythonic OOP Database Service
Replaces procedural database_utils.py with proper class structure
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import func, case, desc, distinct
from polymorphic_core import announcer

# Use existing SSOT database module
from database import session_scope

# Announce module capabilities on import
announcer.announce(
    "Database Service",
    [
        "Manage database sessions and transactions",
        "Calculate database statistics",
        "Query tournaments, players, and organizations",
        "Handle batch database operations",
        "Provide session context management",
        "Track database operation metrics"
    ],
    [
        "database_service.get_statistics()",
        "with database_service.session_scope() as session:",
        "database_service.get_top_players(limit=50)"
    ]
)


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
        from models.tournament_models import Tournament, Organization, Player, TournamentPlacement
        
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
        """Get attendance rankings for reporting
        
        Now uses UnifiedTabulator for consistent ranking logic.
        """
        from unified_tabulator import UnifiedTabulator
        
        with self.session_scope() as session:
            # Use the unified tabulator for organization attendance rankings
            ranked_items = UnifiedTabulator.tabulate_org_attendance(session, limit)
            
            # Convert to expected format for backward compatibility
            rankings = []
            for item in ranked_items:
                meta = item.metadata.copy()
                meta['rank'] = item.rank
                rankings.append(meta)
            
            return rankings
    
    def get_organizations_with_stats(self) -> List[Dict[str, Any]]:
        """Get Organization objects with their tournament statistics - matches editor_service logic"""
        from models.tournament_models import Organization, Tournament, normalize_contact
        
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
        from models.tournament_models import Tournament
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
        """Get player rankings with points and statistics
        
        Now uses UnifiedTabulator to eliminate duplicate ranking logic.
        """
        from unified_tabulator import UnifiedTabulator
        
        with self.session_scope() as session:
            # Use the unified tabulator for consistent ranking
            ranked_items = UnifiedTabulator.tabulate_player_points(session, limit)
            
            # Convert to expected format for backward compatibility
            rankings = []
            for item in ranked_items:
                meta = item.metadata.copy()
                meta['rank'] = item.rank
                meta['points'] = int(item.score)
                # Rename some fields for backward compatibility
                meta['events'] = meta.pop('tournament_count', 0)
                meta['top_3s'] = meta.pop('top_3_finishes', 0)
                if meta['events'] > 0:
                    meta['win_rate'] = (meta.get('first_places', 0) / meta['events'] * 100)
                    meta['podium_rate'] = (meta.get('top_3s', 0) / meta['events'] * 100)
                else:
                    meta['win_rate'] = 0
                    meta['podium_rate'] = 0
                rankings.append(meta)
            
            return rankings
    
    def get_tournament_by_id(self, tournament_id: int) -> Optional[Any]:
        """Get a tournament by ID"""
        from models.tournament_models import Tournament
        with self.session_scope() as session:
            return session.query(Tournament).get(tournament_id)
    
    def get_tournaments_with_location(self, limit: Optional[int] = None) -> List[Any]:
        """Get tournaments that have location data"""
        from models.tournament_models import Tournament
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
        from models.tournament_models import Tournament
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
        from models.tournament_models import Tournament
        with self.session_scope() as session:
            return session.query(Tournament).all()
    
    def get_all_organizations(self) -> List[Any]:
        """Get all organizations"""
        from models.tournament_models import Organization
        with self.session_scope() as session:
            return session.query(Organization).all()
    
    def get_all_players(self) -> List[Any]:
        """Get all players"""
        from models.tournament_models import Player
        with self.session_scope() as session:
            return session.query(Player).all()
    
    def get_organization_by_id(self, org_id: int) -> Optional[Any]:
        """Get organization by ID"""
        from models.tournament_models import Organization
        with self.session_scope() as session:
            return session.query(Organization).get(org_id)
    
    def get_player_by_id(self, player_id: int) -> Optional[Any]:
        """Get player by ID"""
        from models.tournament_models import Player
        with self.session_scope() as session:
            return session.query(Player).get(player_id)
    
    def get_tournament_placements(self, tournament_id: int) -> List[Any]:
        """Get all placements for a tournament"""
        from models.tournament_models import TournamentPlacement
        with self.session_scope() as session:
            return session.query(TournamentPlacement).filter_by(
                tournament_id=tournament_id
            ).order_by(TournamentPlacement.placement).all()
    
    def upsert_tournament(self, tournament_data: Dict[str, Any]) -> Any:
        """Create or update a tournament"""
        from models.tournament_models import Tournament
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
        from models.tournament_models import Player
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
        from models.tournament_models import Organization
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
        from models.tournament_models import Tournament, Organization
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
        from models.tournament_models import Organization
        with self.session_scope() as session:
            org = Organization(display_name=display_name, contacts_json=contacts_json)
            session.add(org)
            session.commit()
            return org
    
    def get_tournaments_by_organization(self, org_id: int) -> List[Any]:
        """Get all tournaments for an organization"""
        from models.tournament_models import Tournament
        with self.session_scope() as session:
            return session.query(Tournament).filter_by(organization_id=org_id).all()
    
    def get_player_placements(self, player_id: int) -> List[Any]:
        """Get all tournament placements for a player"""
        from models.tournament_models import TournamentPlacement
        with self.session_scope() as session:
            return session.query(TournamentPlacement).filter_by(
                player_id=player_id
            ).order_by(TournamentPlacement.placement).all()
    
    def bulk_get_or_create_players(self, players_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk create or get players"""
        from models.tournament_models import Player
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
        from models.tournament_models import Tournament
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