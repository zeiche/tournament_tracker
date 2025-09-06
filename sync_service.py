"""
sync_service.py - Single Source of Truth for Tournament Synchronization
Consolidates sync_operation.py and sync_operation_v2.py into one Pythonic service
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from database_service import database_service
from startgg_service import startgg_service, SyncResult
from log_manager import LogManager


class SyncMode(Enum):
    """Synchronization modes"""
    FULL = "full"          # Sync everything
    RECENT = "recent"      # Only recent tournaments
    UPCOMING = "upcoming"  # Only upcoming tournaments
    SMART = "smart"        # Smart sync based on last sync time


@dataclass
class SyncStats:
    """Statistics for sync operation"""
    started_at: datetime
    completed_at: Optional[datetime] = None
    mode: SyncMode = SyncMode.FULL
    tournaments_fetched: int = 0
    tournaments_created: int = 0
    tournaments_updated: int = 0
    organizations_created: int = 0
    players_created: int = 0
    placements_created: int = 0
    errors: List[str] = field(default_factory=list)
    api_calls: int = 0
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate sync duration"""
        if self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.tournaments_fetched == 0:
            return 0.0
        successful = self.tournaments_created + self.tournaments_updated
        return (successful / self.tournaments_fetched) * 100


class SyncService:
    """Unified tournament synchronization service"""
    
    _instance: Optional['SyncService'] = None
    
    def __new__(cls) -> 'SyncService':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize sync service"""
        if not self._initialized:
            self.logger = LogManager().get_logger('sync')
            self.last_sync: Optional[datetime] = None
            self.sync_history: List[SyncStats] = []
            self._initialized = True
    
    def sync_tournaments(
        self,
        mode: SyncMode = SyncMode.FULL,
        fetch_standings: bool = False,
        standings_limit: int = 5,
        year: Optional[int] = None
    ) -> SyncStats:
        """
        Main sync method - consolidates all sync operations
        
        Args:
            mode: Sync mode (full, recent, upcoming, smart)
            fetch_standings: Whether to fetch tournament standings
            standings_limit: Number of tournaments to fetch standings for
            year: Specific year to sync (None for current year)
            
        Returns:
            SyncStats with results
        """
        stats = SyncStats(
            started_at=datetime.now(),
            mode=mode
        )
        
        self.logger.info(f"Starting {mode.value} sync")
        
        try:
            # Use StartGGService for API calls
            result = startgg_service.sync_tournaments(
                fetch_standings=fetch_standings,
                standings_limit=standings_limit
            )
            
            # Update stats from result
            stats.tournaments_fetched = result.tournaments_synced
            stats.organizations_created = result.organizations_created
            stats.players_created = result.players_created
            stats.api_calls = result.api_calls
            stats.errors = result.errors
            
            # Process tournaments based on mode
            if mode == SyncMode.SMART:
                self._smart_sync(stats)
            elif mode == SyncMode.RECENT:
                self._recent_sync(stats)
            elif mode == SyncMode.UPCOMING:
                self._upcoming_sync(stats)
            else:
                self._full_sync(stats)
            
            stats.completed_at = datetime.now()
            self.last_sync = datetime.now()
            self.sync_history.append(stats)
            
            self.logger.info(
                f"Sync completed: {stats.tournaments_created} created, "
                f"{stats.tournaments_updated} updated, "
                f"{len(stats.errors)} errors"
            )
            
        except Exception as e:
            stats.errors.append(str(e))
            self.logger.error(f"Sync failed: {e}")
        
        return stats
    
    def _full_sync(self, stats: SyncStats):
        """Perform full sync"""
        from tournament_models import Tournament
        
        with session_scope() as session:
            # Get all tournaments from API
            tournaments = startgg_service.fetch_tournaments()
            stats.tournaments_fetched = len(tournaments)
            
            for tourney_data in tournaments:
                try:
                    self._process_tournament(session, tourney_data, stats)
                except Exception as e:
                    stats.errors.append(f"Failed to process {tourney_data.get('id')}: {e}")
    
    def _recent_sync(self, stats: SyncStats):
        """Sync only recent tournaments (last 30 days)"""
        from tournament_models import Tournament
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=30)
        
        with session_scope() as session:
            tournaments = startgg_service.fetch_tournaments()
            
            for tourney_data in tournaments:
                if tourney_data.get('startAt'):
                    start_date = datetime.fromtimestamp(tourney_data['startAt'])
                    if start_date >= cutoff_date:
                        self._process_tournament(session, tourney_data, stats)
    
    def _upcoming_sync(self, stats: SyncStats):
        """Sync only upcoming tournaments"""
        now = datetime.now()
        
        with session_scope() as session:
            tournaments = startgg_service.fetch_tournaments()
            
            for tourney_data in tournaments:
                if tourney_data.get('startAt'):
                    start_date = datetime.fromtimestamp(tourney_data['startAt'])
                    if start_date >= now:
                        self._process_tournament(session, tourney_data, stats)
    
    def _smart_sync(self, stats: SyncStats):
        """Smart sync based on last sync time"""
        if self.last_sync:
            # If synced recently, only get upcoming
            if (datetime.now() - self.last_sync).days < 1:
                self._upcoming_sync(stats)
            else:
                self._recent_sync(stats)
        else:
            # First sync, do full
            self._full_sync(stats)
    
    def _process_tournament(self, session, tourney_data: Dict[str, Any], stats: SyncStats):
        """Process a single tournament"""
        from tournament_models import Tournament, Organization
        
        tournament_id = str(tourney_data['id'])
        
        # Get or create tournament
        tournament = session.query(Tournament).filter(
            Tournament.id == tournament_id
        ).first()
        
        if tournament:
            stats.tournaments_updated += 1
        else:
            tournament = Tournament(id=tournament_id)
            session.add(tournament)
            stats.tournaments_created += 1
        
        # Update fields
        self._update_tournament_fields(tournament, tourney_data)
        
        # Process organization if needed
        if tourney_data.get('primaryContact'):
            self._process_organization(session, tourney_data, stats)
    
    def _update_tournament_fields(self, tournament, data: Dict[str, Any]):
        """Update tournament fields from API data"""
        field_mapping = {
            'name': 'name',
            'slug': 'slug',
            'numAttendees': 'num_attendees',
            'city': 'city',
            'lat': 'lat',
            'lng': 'lng',
            'primaryContact': 'primary_contact'
        }
        
        for api_field, model_field in field_mapping.items():
            if api_field in data:
                setattr(tournament, model_field, data[api_field])
        
        # Handle dates
        if data.get('startAt'):
            tournament.start_at = datetime.fromtimestamp(data['startAt'])
        if data.get('endAt'):
            tournament.end_at = datetime.fromtimestamp(data['endAt'])
    
    def _process_organization(self, session, tourney_data: Dict[str, Any], stats: SyncStats):
        """Process organization from tournament data"""
        from tournament_models import Organization
        from database_service import database_service
        
        contact = tourney_data.get('primaryContact')
        if not contact:
            return
        
        normalized = database_service.normalize_contact(contact)
        
        # Check if organization exists
        org = session.query(Organization).filter(
            Organization.contacts_json.contains(normalized)
        ).first()
        
        if not org:
            # Create new organization
            org = Organization(
                display_name=tourney_data.get('name', 'Unknown Organizer'),
                contacts_json='[]'
            )
            org.add_contact(
                contact_type=database_service.determine_contact_type(contact),
                contact_value=contact
            )
            session.add(org)
            stats.organizations_created += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sync service statistics"""
        recent_syncs = self.sync_history[-10:] if self.sync_history else []
        
        return {
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'total_syncs': len(self.sync_history),
            'recent_syncs': [
                {
                    'started_at': s.started_at.isoformat(),
                    'duration': str(s.duration) if s.duration else None,
                    'mode': s.mode.value,
                    'tournaments_synced': s.tournaments_created + s.tournaments_updated,
                    'success_rate': f"{s.success_rate:.1f}%",
                    'errors': len(s.errors)
                }
                for s in recent_syncs
            ]
        }
    
    def clear_history(self):
        """Clear sync history"""
        self.sync_history.clear()
        self.logger.info("Sync history cleared")


# Singleton instance
sync_service = SyncService()