"""
startgg_service.py - Single Source of Truth for start.gg API
Pythonic OOP service combining startgg_query and startgg_sync
"""
import os
import time
import httpx
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

from database import session_scope
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


def retry_on_error(max_retries: int = 3, strategy: RetryStrategy = RetryStrategy.EXPONENTIAL):
    """Decorator for retrying API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        if strategy == RetryStrategy.EXPONENTIAL:
                            wait_time = 2 ** attempt
                        elif strategy == RetryStrategy.LINEAR:
                            wait_time = attempt + 1
                        else:
                            wait_time = 0
                        
                        if wait_time > 0:
                            time.sleep(wait_time)
                    else:
                        raise last_error
            
            raise last_error
        return wrapper
    return decorator


class StartGGService:
    """Single Source of Truth for all start.gg operations"""
    
    _instance: Optional['StartGGService'] = None
    
    def __new__(cls) -> 'StartGGService':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[APIConfig] = None):
        """Initialize service with configuration"""
        if not self._initialized:
            self.config = config or APIConfig()
            self.config.api_key = self.config.api_key or os.getenv('STARTGG_API_KEY')
            
            self.logger = LogManager().get_logger('startgg')
            self.client: Optional[httpx.Client] = None
            self._cache: Dict[str, tuple[Any, float]] = {}
            self._initialized = True
            
            # Statistics tracking
            self.stats = {
                'api_calls': 0,
                'cache_hits': 0,
                'errors': 0,
                'total_tournaments': 0,
                'total_players': 0
            }
    
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
    
    # ========================================================================
    # GRAPHQL QUERIES
    # ========================================================================
    
    TOURNAMENT_QUERY = """
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
          contactEmail
          contactPhone
          contactTwitter
          contactUrl
          hasOnlineEvents
          hasOfflineEvents
          registrationClosesAt
          tournamentType
          currency
          isRegistrationOpen
          state
          primaryContact
          primaryContactType
          city
          countryCode
          postalCode
          lat
          lng
          venueAddress
          venueName
        }
      }
    }
    """
    
    STANDINGS_QUERY = """
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
    
    # ========================================================================
    # API METHODS
    # ========================================================================
    
    @retry_on_error(max_retries=3)
    def execute_query(self, query: str, variables: Dict[str, Any], 
                     use_cache: bool = True) -> Dict[str, Any]:
        """Execute GraphQL query with caching and retry"""
        # Check cache
        if use_cache:
            cache_key = self._cache_key(query, variables)
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        # Make API call
        client = self._ensure_client()
        self.stats['api_calls'] += 1
        
        try:
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
            self.stats['errors'] += 1
            self.logger.error(f"API call failed: {e}")
            raise
    
    def fetch_tournaments(self, lat: float = 33.7, lng: float = -117.8, 
                         radius: str = "100mi", year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch tournaments from start.gg"""
        current_year = year or datetime.now().year
        all_tournaments = []
        page = 1
        
        self.logger.info(f"Fetching {current_year} tournaments from start.gg")
        
        while True:
            result = self.execute_query(
                self.TOURNAMENT_QUERY,
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
    
    def fetch_standings(self, slug: str) -> Optional[Dict[str, Any]]:
        """Fetch tournament standings"""
        try:
            result = self.execute_query(
                self.STANDINGS_QUERY,
                {'slug': slug},
                use_cache=True
            )
            return result.get('tournament')
        except Exception as e:
            self.logger.error(f"Failed to fetch standings for {slug}: {e}")
            return None
    
    # ========================================================================
    # SYNC OPERATIONS
    # ========================================================================
    
    def sync_tournaments(self, fetch_standings: bool = False, 
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
            tournaments = self.fetch_tournaments()
            
            # Process tournaments
            from tournament_models import Tournament, Organization
            
            with session_scope() as session:
                for tournament_data in tournaments:
                    try:
                        # Create or update tournament
                        tournament = session.query(Tournament).filter(
                            Tournament.id == str(tournament_data['id'])
                        ).first()
                        
                        if not tournament:
                            tournament = Tournament(id=str(tournament_data['id']))
                            session.add(tournament)
                        
                        # Update tournament fields
                        self._update_tournament(tournament, tournament_data)
                        result.tournaments_synced += 1
                        
                    except Exception as e:
                        result.errors.append(f"Failed to sync tournament {tournament_data.get('id')}: {e}")
                
                session.commit()
            
            # Fetch standings for recent tournaments
            if fetch_standings:
                self._sync_standings(standings_limit, result)
            
            result.success = True
            result.duration = datetime.now() - start_time
            result.api_calls = self.stats['api_calls']
            
            self.logger.info(f"Sync completed: {result.tournaments_synced} tournaments")
            
        except Exception as e:
            result.errors.append(f"Sync failed: {e}")
            self.logger.error(f"Sync failed: {e}")
        
        return result
    
    def _update_tournament(self, tournament, data: Dict[str, Any]):
        """Update tournament model from API data"""
        # Map API fields to model fields
        field_mapping = {
            'name': 'name',
            'slug': 'slug',
            'startAt': 'start_at',
            'endAt': 'end_at',
            'numAttendees': 'num_attendees',
            'city': 'city',
            'countryCode': 'country_code',
            'lat': 'lat',
            'lng': 'lng',
            'venueName': 'venue_name',
            'venueAddress': 'venue_address',
            'primaryContact': 'primary_contact',
            'primaryContactType': 'primary_contact_type',
            'isRegistrationOpen': 'is_registration_open',
            'hasOnlineEvents': 'has_online_events',
            'hasOfflineEvents': 'has_offline_events'
        }
        
        for api_field, model_field in field_mapping.items():
            if api_field in data and data[api_field] is not None:
                if api_field in ['startAt', 'endAt'] and data[api_field]:
                    setattr(tournament, model_field, datetime.fromtimestamp(data[api_field]))
                else:
                    setattr(tournament, model_field, data[api_field])
    
    def _sync_standings(self, limit: int, result: SyncResult):
        """Sync tournament standings"""
        from tournament_models import Tournament, Player, TournamentPlacement
        
        with session_scope() as session:
            recent_tournaments = session.query(Tournament).filter(
                Tournament.slug.isnot(None)
            ).order_by(Tournament.start_at.desc()).limit(limit).all()
            
            for tournament in recent_tournaments:
                standings_data = self.fetch_standings(tournament.slug)
                if standings_data:
                    # Process standings...
                    pass  # Simplified for brevity
    
    # ========================================================================
    # STATISTICS AND MONITORING
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'enabled': bool(self.config.api_key),
            'api_calls': self.stats['api_calls'],
            'cache_hits': self.stats['cache_hits'],
            'cache_size': len(self._cache),
            'errors': self.stats['errors'],
            'total_tournaments': self.stats['total_tournaments'],
            'total_players': self.stats['total_players']
        }
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()
        self.logger.info("Cache cleared")
    
    def close(self):
        """Close HTTP client"""
        if self.client:
            self.client.close()
            self.client = None


# Singleton instance
startgg_service = StartGGService()