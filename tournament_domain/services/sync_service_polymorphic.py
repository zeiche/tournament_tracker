#!/usr/bin/env python3
"""
sync_service_polymorphic.py - Tournament sync with ask/tell/do pattern

Synchronization from start.gg using polymorphic pattern.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import sys
sys.path.insert(0, 'utils')
from universal_polymorphic import UniversalPolymorphic
from capability_announcer import announcer
from database_service import database_service
from startgg_service import startgg_service


class SyncMode(Enum):
    """Synchronization modes"""
    FULL = "full"
    RECENT = "recent"
    UPCOMING = "upcoming"
    SMART = "smart"


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
        if self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def success_rate(self) -> float:
        if self.tournaments_fetched == 0:
            return 0.0
        successful = self.tournaments_created + self.tournaments_updated
        return (successful / self.tournaments_fetched) * 100


class SyncServicePolymorphic(UniversalPolymorphic):
    """
    Tournament synchronization with ask/tell/do pattern.
    
    Examples:
        sync.ask("last sync")              # When was last sync?
        sync.ask("stats")                   # Get sync statistics
        sync.ask("mode")                    # Current sync mode
        sync.tell("status")                 # Full sync status
        sync.tell("history")                # Sync history
        sync.do("sync")                     # Run full sync
        sync.do("sync recent")              # Sync recent only
        sync.do("fetch standings")          # Fetch tournament standings
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.last_sync = None
            self.sync_history = []
            self.current_stats = None
            self.is_syncing = False
            self._initialized = True
            
            # Call parent init
            super().__init__()
            
            # Announce via Bonjour
            announcer.announce(
                "SyncServicePolymorphic",
                [
                    "I sync tournaments with ask/tell/do pattern",
                    "Use sync.ask('last sync')",
                    "Use sync.do('sync')",
                    "Use sync.do('sync recent')",
                    "Use sync.do('fetch standings')",
                    "I sync from start.gg API"
                ]
            )
    
    def _handle_ask(self, question: str, **kwargs):
        """
        Handle sync-specific questions.
        
        Examples:
            ask("last sync")        # When was last sync?
            ask("syncing")          # Is currently syncing?
            ask("stats")            # Current sync stats
            ask("history")          # Sync history
            ask("errors")           # Any sync errors?
            ask("success rate")     # Success rate
        """
        q = str(question).lower()
        
        if any(word in q for word in ['last', 'recent']) and 'sync' in q:
            if self.last_sync:
                delta = datetime.now() - self.last_sync
                return f"Last sync: {delta.days} days, {delta.seconds // 3600} hours ago"
            return "Never synced"
        
        if 'syncing' in q or 'running' in q:
            return self.is_syncing
        
        if 'stats' in q or 'statistics' in q:
            if self.current_stats:
                return {
                    'mode': self.current_stats.mode.value,
                    'fetched': self.current_stats.tournaments_fetched,
                    'created': self.current_stats.tournaments_created,
                    'updated': self.current_stats.tournaments_updated,
                    'success_rate': f"{self.current_stats.success_rate:.1f}%"
                }
            return "No sync stats available"
        
        if 'history' in q:
            return [
                {
                    'time': stats.started_at.isoformat(),
                    'mode': stats.mode.value,
                    'fetched': stats.tournaments_fetched,
                    'success': f"{stats.success_rate:.1f}%"
                }
                for stats in self.sync_history[-5:]  # Last 5 syncs
            ]
        
        if 'error' in q:
            if self.current_stats and self.current_stats.errors:
                return self.current_stats.errors
            return "No errors"
        
        if 'success' in q and 'rate' in q:
            if self.current_stats:
                return f"{self.current_stats.success_rate:.1f}%"
            return "N/A"
        
        if 'mode' in q:
            if self.current_stats:
                return self.current_stats.mode.value
            return "Not syncing"
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str, **kwargs):
        """
        Format sync information.
        
        Examples:
            tell("status")          # Full status
            tell("progress")        # Sync progress
            tell("summary")         # Summary of last sync
        """
        if format == "status":
            return {
                'is_syncing': self.is_syncing,
                'last_sync': self.last_sync.isoformat() if self.last_sync else None,
                'current_mode': self.current_stats.mode.value if self.current_stats else None,
                'history_count': len(self.sync_history)
            }
        
        if format == "progress":
            if not self.is_syncing or not self.current_stats:
                return "Not syncing"
            
            return (f"Syncing... {self.current_stats.tournaments_fetched} fetched, "
                   f"{self.current_stats.tournaments_created} created, "
                   f"{self.current_stats.tournaments_updated} updated")
        
        if format == "summary":
            if not self.sync_history:
                return "No sync history"
            
            last = self.sync_history[-1]
            return (f"Last sync: {last.mode.value} mode\n"
                   f"Fetched: {last.tournaments_fetched}\n"
                   f"Created: {last.tournaments_created}\n"
                   f"Updated: {last.tournaments_updated}\n"
                   f"Success rate: {last.success_rate:.1f}%\n"
                   f"Duration: {last.duration}")
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs):
        """
        Perform sync actions.
        
        Examples:
            do("sync")              # Full sync
            do("sync recent")       # Sync recent tournaments
            do("sync upcoming")     # Sync upcoming tournaments
            do("fetch standings")   # Fetch tournament standings
            do("stop")             # Stop current sync
        """
        act = str(action).lower()
        
        if 'sync' in act:
            if self.is_syncing:
                return "Already syncing"
            
            # Determine mode
            if 'recent' in act:
                mode = SyncMode.RECENT
            elif 'upcoming' in act:
                mode = SyncMode.UPCOMING
            elif 'smart' in act:
                mode = SyncMode.SMART
            else:
                mode = SyncMode.FULL
            
            return self._run_sync(mode, **kwargs)
        
        if 'fetch' in act and 'standing' in act:
            limit = kwargs.get('limit', 5)
            return self._fetch_standings(limit)
        
        if 'stop' in act:
            if self.is_syncing:
                self.is_syncing = False
                return "Sync stopped"
            return "Not syncing"
        
        if 'clear' in act and 'history' in act:
            self.sync_history.clear()
            return "History cleared"
        
        return super()._handle_do(action, **kwargs)
    
    def _run_sync(self, mode: SyncMode, **kwargs):
        """Run tournament synchronization"""
        self.is_syncing = True
        self.current_stats = SyncStats(
            started_at=datetime.now(),
            mode=mode
        )
        
        # Announce sync start
        announcer.announce(
            "SYNC_STARTED",
            [
                f"Starting {mode.value} sync",
                "Fetching from start.gg"
            ]
        )
        
        try:
            # Determine what to sync based on mode
            if mode == SyncMode.RECENT:
                days = kwargs.get('days', 90)
                result = self._sync_recent_tournaments(days)
            elif mode == SyncMode.UPCOMING:
                result = self._sync_upcoming_tournaments()
            elif mode == SyncMode.SMART:
                result = self._smart_sync()
            else:
                result = self._sync_all_tournaments()
            
            # Update stats
            self.current_stats.completed_at = datetime.now()
            self.last_sync = datetime.now()
            self.sync_history.append(self.current_stats)
            
            # Announce completion
            announcer.announce(
                "SYNC_COMPLETED",
                [
                    f"Sync completed in {self.current_stats.duration}",
                    f"Fetched: {self.current_stats.tournaments_fetched}",
                    f"Success rate: {self.current_stats.success_rate:.1f}%"
                ]
            )
            
            return result
            
        except Exception as e:
            self.current_stats.errors.append(str(e))
            return f"Sync failed: {e}"
        finally:
            self.is_syncing = False
    
    def _sync_recent_tournaments(self, days: int):
        """Sync recent tournaments"""
        # Use existing services
        result = startgg_service.fetch_recent_socal_tournaments(days)
        
        self.current_stats.tournaments_fetched = len(result.tournaments)
        self.current_stats.tournaments_created = result.created
        self.current_stats.tournaments_updated = result.updated
        
        return f"Synced {len(result.tournaments)} recent tournaments"
    
    def _sync_upcoming_tournaments(self):
        """Sync upcoming tournaments"""
        # Would fetch upcoming tournaments
        return "Upcoming sync not implemented"
    
    def _sync_all_tournaments(self):
        """Sync all tournaments"""
        result = startgg_service.fetch_recent_socal_tournaments(365)
        
        self.current_stats.tournaments_fetched = len(result.tournaments)
        self.current_stats.tournaments_created = result.created
        self.current_stats.tournaments_updated = result.updated
        
        return f"Synced {len(result.tournaments)} tournaments"
    
    def _smart_sync(self):
        """Smart sync based on last sync time"""
        if not self.last_sync:
            return self._sync_all_tournaments()
        
        days_since = (datetime.now() - self.last_sync).days
        
        if days_since > 30:
            return self._sync_all_tournaments()
        elif days_since > 7:
            return self._sync_recent_tournaments(30)
        else:
            return self._sync_recent_tournaments(7)
    
    def _fetch_standings(self, limit: int):
        """Fetch tournament standings"""
        result = startgg_service.fetch_recent_top8_standings(limit)
        
        return f"Fetched standings for {result.tournaments_updated} tournaments"
    
    def _get_capabilities(self):
        """List sync capabilities"""
        return [
            "ask('last sync')",
            "ask('syncing')",
            "ask('stats')",
            "tell('status')",
            "tell('progress')",
            "do('sync')",
            "do('sync recent')",
            "do('fetch standings')"
        ]


# Singleton instance
sync_service = SyncServicePolymorphic()


if __name__ == "__main__":
    print("Sync Service with ask/tell/do pattern")
    print("=" * 50)
    print(f"sync.ask('last sync'): {sync_service.ask('last sync')}")
    print(f"sync.ask('syncing'): {sync_service.ask('syncing')}")
    print(f"sync.tell('status'): {sync_service.tell('status')}")
    print("\nTo sync: sync.do('sync')")
    print("To sync recent: sync.do('sync recent')")