#!/usr/bin/env python3
"""
startgg_service_polymorphic.py - start.gg API with just ask/tell/do

Replaces 17 methods with 3 universal methods that understand intent.

Examples:
    # Instead of: startgg.fetch_tournaments()
    startgg.do("fetch tournaments")
    
    # Instead of: startgg.get_statistics()
    startgg.ask("statistics")
    
    # Instead of: startgg.sync_tournaments(fetch_standings=True)
    startgg.do("sync", fetch_standings=True)
"""

import os
import time
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import sys
sys.path.insert(0, 'utils')

from universal_polymorphic import UniversalPolymorphic
from polymorphic_core import announcer
from database_service import database_service
from log_manager import LogManager


class RetryStrategy(Enum):
    """Retry strategies for API calls"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    NONE = "none"


@dataclass
class SyncResult:
    """Result of a sync operation"""
    success: bool
    tournaments_synced: int
    organizations_created: int
    players_created: int
    errors: List[str] = field(default_factory=list)
    duration: Optional[timedelta] = None
    api_calls: int = 0


@dataclass 
class APIConfig:
    """Configuration for start.gg API"""
    api_key: Optional[str] = None
    base_url: str = "https://api.start.gg/gql/alpha"
    timeout: int = 30
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    cache_ttl: int = 3600  # 1 hour cache


class StartGGPolymorphic(UniversalPolymorphic):
    """
    start.gg API service with polymorphic ask/tell/do pattern.
    
    Examples:
        api = StartGGPolymorphic()
        
        # Ask for information
        api.ask("connected")           # Check if API key configured
        api.ask("statistics")          # Get API call stats
        api.ask("cache size")          # Get cache info
        
        # Tell in different formats
        api.tell("json")               # Full config as JSON
        api.tell("status")             # Current status
        api.tell("brief")              # Quick summary
        
        # Do actions
        api.do("fetch tournaments")                    # Fetch all tournaments
        api.do("fetch", slug="socal-colosseum")       # Fetch specific tournament
        api.do("sync")                                 # Sync to database
        api.do("sync", fetch_standings=True)          # Sync with standings
        api.do("clear cache")                          # Clear API cache
    """
    
    _instance: Optional['StartGGPolymorphic'] = None
    
    def __new__(cls) -> 'StartGGPolymorphic':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[APIConfig] = None):
        """Initialize with configuration"""
        if not self._initialized:
            # Setup config
            self.config = config or APIConfig()
            self.config.api_key = self.config.api_key or os.getenv('STARTGG_API_KEY')
            
            # Setup logging
            self.logger = LogManager().get_logger('startgg')
            
            # HTTP client
            self.client: Optional[httpx.Client] = None
            
            # Cache
            self._cache: Dict[str, tuple[Any, float]] = {}
            
            # Statistics
            self.stats = {
                'api_calls': 0,
                'cache_hits': 0,
                'errors': 0,
                'total_tournaments': 0,
                'total_players': 0
            }
            
            self._initialized = True
            
            # Call parent init (announces via UniversalPolymorphic)
            super().__init__()
            
            # Also announce via Bonjour
            announcer.announce(
                "StartGGPolymorphic",
                [
                    "start.gg API with ask/tell/do pattern",
                    "Use api.ask('statistics') for stats",
                    "Use api.do('fetch tournaments') to fetch",
                    "Use api.do('sync') to sync to database",
                    "Replaces 17 methods with just 3!"
                ]
            )
    
    # =========================================================================
    # POLYMORPHIC HANDLERS
    # =========================================================================
    
    def _handle_ask(self, question: Any, **kwargs) -> Any:
        """
        Handle ask() queries about the API service.
        
        Replaces:
        - get_statistics()
        - Various property getters
        """
        q = str(question).lower()
        
        # API status queries
        if any(word in q for word in ['connected', 'configured', 'enabled']):
            return bool(self.config.api_key)
        
        if any(word in q for word in ['statistics', 'stats']):
            return {
                'enabled': bool(self.config.api_key),
                'api_calls': self.stats['api_calls'],
                'cache_hits': self.stats['cache_hits'],
                'cache_size': len(self._cache),
                'errors': self.stats['errors'],
                'total_tournaments': self.stats['total_tournaments'],
                'total_players': self.stats['total_players']
            }
        
        if 'cache' in q and 'size' in q:
            return len(self._cache)
        
        if 'api' in q and 'calls' in q:
            return self.stats['api_calls']
        
        if 'errors' in q:
            return self.stats['errors']
        
        if 'tournaments' in q and 'count' in q:
            return self.stats['total_tournaments']
        
        # Configuration queries
        if 'config' in q or 'configuration' in q:
            return {
                'api_key_configured': bool(self.config.api_key),
                'base_url': self.config.base_url,
                'timeout': self.config.timeout,
                'cache_ttl': self.config.cache_ttl,
                'retry_strategy': self.config.retry_strategy.value
            }
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str = "default", **kwargs) -> Any:
        """
        Format API service information.
        
        Provides different views of the service state.
        """
        fmt = format.lower()
        
        if fmt in ['status', 'state']:
            return f"start.gg API: {'Connected' if self.config.api_key else 'Not configured'} | " \
                   f"API calls: {self.stats['api_calls']} | Cache: {len(self._cache)} items"
        
        if fmt in ['brief', 'summary']:
            return f"start.gg API with {self.stats['total_tournaments']} tournaments fetched"
        
        if fmt in ['detailed', 'full']:
            return {
                'service': 'start.gg API (Polymorphic)',
                'status': 'Connected' if self.config.api_key else 'Not configured',
                'statistics': self.stats,
                'cache': {
                    'size': len(self._cache),
                    'ttl': self.config.cache_ttl
                },
                'config': {
                    'base_url': self.config.base_url,
                    'timeout': self.config.timeout,
                    'retry_strategy': self.config.retry_strategy.value
                }
            }
        
        if fmt == 'discord':
            enabled = '✅' if self.config.api_key else '❌'
            return f"**start.gg API** {enabled}\n" \
                   f"API Calls: {self.stats['api_calls']}\n" \
                   f"Tournaments: {self.stats['total_tournaments']}\n" \
                   f"Cache: {len(self._cache)} items"
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: Any, **kwargs) -> Any:
        """
        Perform API actions.
        
        Replaces:
        - fetch_tournaments()
        - fetch_standings()
        - sync_tournaments()
        - clear_cache()
        - execute_query()
        """
        act = str(action).lower()
        
        # Announce the action
        announcer.announce(
            "StartGGPolymorphic.do",
            [f"Executing action: {action}"]
        )
        
        # Fetch operations
        if 'fetch' in act:
            if 'tournament' in act:
                # Fetch tournaments from API
                lat = kwargs.get('lat', 33.7)
                lng = kwargs.get('lng', -117.8)
                radius = kwargs.get('radius', '100mi')
                year = kwargs.get('year')
                
                result = self._fetch_tournaments(lat, lng, radius, year)
                announcer.announce(
                    "StartGGPolymorphic.fetch",
                    [f"Fetched {len(result)} tournaments"]
                )
                return result
            
            elif 'standing' in act or 'slug' in kwargs:
                # Fetch standings for a tournament
                slug = kwargs.get('slug')
                if not slug:
                    return {'error': 'slug parameter required'}
                
                result = self._fetch_standings(slug)
                announcer.announce(
                    "StartGGPolymorphic.fetch",
                    [f"Fetched standings for {slug}"]
                )
                return result
        
        # Sync operations
        if 'sync' in act:
            fetch_standings = kwargs.get('fetch_standings', False)
            standings_limit = kwargs.get('standings_limit', 5)
            
            result = self._sync_tournaments(fetch_standings, standings_limit)
            
            announcer.announce(
                "StartGGPolymorphic.sync",
                [
                    f"Sync complete: {result.tournaments_synced} tournaments",
                    f"Success: {result.success}"
                ]
            )
            return result
        
        # Cache operations
        if 'clear' in act and 'cache' in act:
            self._cache.clear()
            self.logger.info("Cache cleared")
            announcer.announce(
                "StartGGPolymorphic.cache",
                ["Cache cleared"]
            )
            return {'cache_cleared': True}
        
        # Query execution
        if 'query' in act or 'execute' in act:
            query = kwargs.get('query')
            variables = kwargs.get('variables', {})
            use_cache = kwargs.get('use_cache', True)
            
            if not query:
                return {'error': 'query parameter required'}
            
            result = self._execute_query(query, variables, use_cache)
            return result
        
        # Close/cleanup
        if 'close' in act or 'cleanup' in act:
            if self.client:
                self.client.close()
                self.client = None
            return {'closed': True}
        
        return super()._handle_do(action, **kwargs)
    
    # =========================================================================
    # INTERNAL METHODS (prefixed with _)
    # =========================================================================
    
    def _ensure_client(self) -> httpx.Client:
        """Ensure HTTP client is initialized"""
        if self.client is None:
            headers = {
                'Content-Type': 'application/json'
            }
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'
            
            self.client = httpx.Client(
                headers=headers,
                timeout=self.config.timeout
            )
        return self.client
    
    def _cache_key(self, query: str, variables: Dict[str, Any]) -> str:
        """Generate cache key for query"""
        content = f"{query}:{json.dumps(variables, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached result if not expired"""
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self.config.cache_ttl:
                self.stats['cache_hits'] += 1
                self.logger.debug(f"Cache hit for {key}")
                return result
        return None
    
    def _set_cache(self, key: str, result: Any):
        """Set cache entry"""
        self._cache[key] = (result, time.time())
    
    def _execute_query(self, query: str, variables: Dict[str, Any], 
                      use_cache: bool = True) -> Dict[str, Any]:
        """Execute GraphQL query with caching and retry"""
        # Check cache
        if use_cache:
            cache_key = self._cache_key(query, variables)
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        # Make API call with retries
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                client = self._ensure_client()
                self.stats['api_calls'] += 1
                
                response = client.post(
                    self.config.base_url,
                    json={'query': query, 'variables': variables}
                )
                response.raise_for_status()
                
                data = response.json()
                
                if 'errors' in data:
                    self.stats['errors'] += 1
                    self.logger.error(f"GraphQL errors: {data['errors']}")
                    raise Exception(f"GraphQL errors: {data['errors']}")
                
                # Cache result
                if use_cache:
                    self._set_cache(cache_key, data['data'])
                
                return data['data']
                
            except Exception as e:
                last_error = e
                self.stats['errors'] += 1
                
                if attempt < self.config.max_retries - 1:
                    # Calculate wait time based on strategy
                    if self.config.retry_strategy == RetryStrategy.EXPONENTIAL:
                        wait_time = 2 ** attempt
                    elif self.config.retry_strategy == RetryStrategy.LINEAR:
                        wait_time = attempt + 1
                    else:
                        wait_time = 0
                    
                    if wait_time > 0:
                        time.sleep(wait_time)
                else:
                    self.logger.error(f"API call failed after {self.config.max_retries} attempts: {e}")
                    raise last_error
    
    def _fetch_tournaments(self, lat: float = 33.7, lng: float = -117.8, 
                          radius: str = "100mi", year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch tournaments from start.gg"""
        current_year = year or datetime.now().year
        all_tournaments = []
        page = 1
        
        self.logger.info(f"Fetching {current_year} tournaments from start.gg")
        
        # GraphQL query
        query = """
        query TournamentsByLocation($lat: Float!, $lng: Float!, $radius: String!, 
                                   $page: Int!, $perPage: Int!) {
          tournaments(query: {
            page: $page
            perPage: $perPage
            filter: {
              location: {
                distanceFrom: {
                  point: {lat: $lat, lng: $lng}
                  radius: $radius
                }
              }
            }
          }) {
            pageInfo {
              total
              totalPages
            }
            nodes {
              id
              name
              slug
              startAt
              endAt
              numAttendees
              city
              countryCode
              lat
              lng
              venueName
              venueAddress
            }
          }
        }
        """
        
        while True:
            result = self._execute_query(
                query,
                {
                    'lat': lat,
                    'lng': lng,
                    'radius': radius,
                    'page': page,
                    'perPage': 50
                }
            )
            
            tournaments_data = result.get('tournaments', {})
            nodes = tournaments_data.get('nodes', [])
            
            # Filter by year
            for tournament in nodes:
                if tournament.get('startAt'):
                    start_date = datetime.fromtimestamp(tournament['startAt'])
                    if start_date.year == current_year:
                        all_tournaments.append(tournament)
            
            # Check for more pages
            page_info = tournaments_data.get('pageInfo', {})
            if page >= page_info.get('totalPages', 1):
                break
            
            page += 1
        
        self.stats['total_tournaments'] += len(all_tournaments)
        self.logger.info(f"Fetched {len(all_tournaments)} tournaments")
        return all_tournaments
    
    def _fetch_standings(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetch tournament standings"""
        query = """
        query EventStandings($slug: String!) {
          tournament(slug: $slug) {
            events {
              id
              name
              standings(query: {perPage: 8, page: 1}) {
                nodes {
                  placement
                  entrant {
                    name
                    participants {
                      gamerTag
                      user {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            result = self._execute_query(
                query,
                {'slug': slug},
                use_cache=True
            )
            return result.get('tournament')
        except Exception as e:
            self.logger.error(f"Failed to fetch standings for {slug}: {e}")
            return None
    
    def _sync_tournaments(self, fetch_standings: bool = False, 
                         standings_limit: int = 5) -> SyncResult:
        """Sync tournaments from start.gg to database"""
        start_time = datetime.now()
        result = SyncResult(
            success=False,
            tournaments_synced=0,
            organizations_created=0,
            players_created=0
        )
        
        try:
            # Fetch tournaments
            tournaments = self._fetch_tournaments()
            
            # Process tournaments using database service
            for tournament_data in tournaments:
                try:
                    # Use database service's polymorphic interface
                    saved = database_service.do(
                        "save tournament",
                        data=tournament_data
                    )
                    if saved:
                        result.tournaments_synced += 1
                except Exception as e:
                    result.errors.append(f"Failed to sync tournament {tournament_data.get('id')}: {e}")
            
            # Fetch standings for recent tournaments if requested
            if fetch_standings:
                recent = database_service.ask("recent tournaments", limit=standings_limit)
                for tournament in recent:
                    if tournament.get('slug'):
                        standings_data = self._fetch_standings(tournament['slug'])
                        if standings_data:
                            database_service.do(
                                "save standings",
                                tournament_id=tournament.get('id'),
                                data=standings_data
                            )
            
            result.success = True
            result.duration = datetime.now() - start_time
            result.api_calls = self.stats['api_calls']
            
            self.logger.info(f"Sync completed: {result.tournaments_synced} tournaments")
            
        except Exception as e:
            result.errors.append(f"Sync failed: {e}")
            self.logger.error(f"Sync failed: {e}")
        
        return result
    
    # =========================================================================
    # OVERRIDES FOR BASE CLASS
    # =========================================================================
    
    def _get_capabilities(self) -> List[str]:
        """Return capabilities for discovery"""
        return [
            "Fetch tournaments from start.gg API",
            "Sync tournaments to database",
            "Fetch tournament standings",
            "Cache API responses",
            "Retry failed requests",
            "Track API statistics",
            "Use ask('statistics') for stats",
            "Use do('fetch tournaments') to fetch",
            "Use do('sync') to sync database"
        ]
    
    def _get_info(self) -> Dict[str, Any]:
        """Get service information"""
        return {
            'service': 'start.gg API (Polymorphic)',
            'pattern': 'ask/tell/do',
            'methods_replaced': 17,
            'methods_now': 3,
            'reduction': '82%',
            'examples': [
                "api.ask('statistics')",
                "api.do('fetch tournaments')",
                "api.do('sync', fetch_standings=True)",
                "api.tell('discord')"
            ]
        }


# Singleton instance
startgg_polymorphic = StartGGPolymorphic()

# For backward compatibility
startgg_service = startgg_polymorphic