#!/usr/bin/env python3
"""
startgg_sync.py - Start.gg sync service with ONLY ask/tell/do methods
All API operations go through these 3 polymorphic methods.
Now uses ManagedService for unified service identity.
"""
import os
import sys
import time
import json
import requests
import calendar
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

# Add path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.startgg_sync")

from polymorphic_core.service_identity import ManagedService
from polymorphic_core import announcer
from utils.database import session_scope
from utils.database_queue import batch_operations
from utils.database_service import database_service
from logging_services.polymorphic_log_manager import PolymorphicLogManager
from utils.error_handler import handle_errors, handle_exception, ErrorSeverity

# Initialize logger at module level
log_manager = PolymorphicLogManager()
def info(message): log_manager.do(f"log info {message}")
def warning(message): log_manager.do(f"log warning {message}")
def error(message): log_manager.do(f"log error {message}")
from utils.config_service import get_config

# Announce module capabilities on import
announcer.announce(
    "StartGG Sync Service",
    [
        "Sync with just 3 methods: ask(), tell(), do()",
        "Natural language API queries",
        "ask('tournaments from 2024') - get tournament data",
        "tell('json', tournaments) - format API response",
        "do('sync tournaments') - perform sync operation"
    ],
    [
        "startgg.ask('recent tournaments')",
        "startgg.ask('tournament 123 standings')",
        "startgg.do('sync all')",
        "startgg.do('fetch standings for 123')"
    ]
)

# GraphQL Queries
SOCAL_TOURNAMENTS_QUERY = """
query SoCalTournaments($coordinates: String!, $radius: String!, $page: Int, $after: Timestamp, $before: Timestamp) {
  tournaments(
    query: {
      perPage: 100
      page: $page
      filter: {
        location: {
          distanceFrom: $coordinates,
          distance: $radius
        }
        afterDate: $after
        beforeDate: $before
      }
    }
  ) {
    pageInfo {
      total
      totalPages
      page
      perPage
    }
    nodes {
      id
      name
      slug
      shortSlug
      numAttendees
      startAt
      endAt
      registrationClosesAt
      isRegistrationOpen
      hasOfflineEvents
      hasOnlineEvents
      venueName
      venueAddress
      city
      addrState
      countryCode
      postalCode
      lat
      lng
      timezone
      tournamentType
      primaryContact
      rules
      events(limit: 100) {
        id
        name
        slug
        startAt
        numEntrants
        type
        state
        videogame {
          id
          displayName
        }
      }
    }
  }
}
"""

TOURNAMENT_STANDINGS_QUERY = """
query TournamentStandings($tournamentId: ID!) {
  tournament(id: $tournamentId) {
    id
    name
    events {
      id
      name
      standings(query: {perPage: 8, page: 1}) {
        nodes {
          placement
          entrant {
            id
            name
            participants {
              id
              player {
                id
                gamerTag
                user {
                  name
                  discriminator
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


class StartGGSyncManaged(ManagedService):
    """
    Start.gg sync service with ONLY 3 public methods: ask, tell, do
    Everything else is private implementation.
    Now inherits from ManagedService for unified service identity.
    """
    
    def __init__(self):
        """Initialize the Start.gg sync service"""
        super().__init__("startgg-sync", "tournament-startgg-sync")
        # Get API token from environment
        self.api_token = get_config("startgg api key", "")
        if not self.api_token:
            warning("StartGG API token not found in environment")
        
        # API endpoint
        self.api_url = "https://api.start.gg/gql/alpha"
        
        # SoCal region configuration
        self.coordinates = "34.13436, -117.95763"  # SoCal coordinates
        self.radius = "67mi"
        
        # Current year date range
        current_year = datetime.now().year
        self.current_year_start = calendar.timegm((current_year, 1, 1, 0, 0, 0))
        self.current_year_end = calendar.timegm((current_year, 12, 31, 23, 59, 59))
        self.current_year = current_year
        
        # Request headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        # Stats tracking
        self.sync_stats = {
            'api_calls': 0,
            'tournaments_fetched': 0,
            'tournaments_processed': 0,
            'standings_fetched': 0,
            'errors': 0
        }
        
        # Announce ready
        announcer.announce(
            "StartGG Sync",
            [f"Ready to sync {current_year} tournaments from SoCal region"]
        )
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Ask for data from Start.gg API using natural language.
        
        Examples:
            ask("tournaments")                    # Get all tournaments
            ask("tournaments from 2024")          # Get 2024 tournaments
            ask("recent tournaments")              # Get recent tournaments
            ask("tournament 123 standings")       # Get standings for tournament
            ask("stats")                          # Get sync statistics
            ask("api status")                     # Check API connection
        """
        query_lower = query.lower().strip()
        
        # Stats queries
        if any(word in query_lower for word in ["stats", "statistics", "status"]):
            return self._get_stats()
        
        # API status check
        if "api" in query_lower and any(word in query_lower for word in ["status", "check", "test"]):
            return self._check_api_status()
        
        # Tournament queries
        if "tournament" in query_lower:
            # Check for standings query
            if "standing" in query_lower or "placement" in query_lower or "top" in query_lower:
                # Extract tournament ID
                import re
                match = re.search(r'\d+', query)
                if match:
                    tournament_id = match.group()
                    return self._fetch_standings(tournament_id)
            
            # Check for year filter
            year_filter = True
            if "all" in query_lower:
                year_filter = False
            elif "recent" in query_lower:
                year_filter = True
            else:
                # Check for specific year
                import re
                year_match = re.search(r'20\d{2}', query)
                if year_match:
                    year = int(year_match.group())
                    if year != self.current_year:
                        # Would need to adjust date range
                        self._set_year_range(year)
            
            # Fetch tournaments
            max_pages = kwargs.get('max_pages', 10)
            return self._fetch_tournaments(year_filter=year_filter, max_pages=max_pages)
        
        # Event queries
        if "event" in query_lower:
            # Return cached events or fetch from tournaments
            return self._get_events()
        
        # Default help
        return {
            "help": "Available queries",
            "examples": [
                "ask('tournaments')",
                "ask('tournaments from 2024')",
                "ask('tournament 123 standings')",
                "ask('stats')",
                "ask('api status')"
            ]
        }
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format Start.gg data for output.
        
        Examples:
            tell("json", tournaments)      # JSON format
            tell("discord", standings)      # Discord message format
            tell("csv", tournaments)        # CSV export
            tell("summary", data)          # Brief summary
            tell("stats")                  # Formatted statistics
        """
        format_lower = format.lower().strip()
        
        # Get default data if none provided
        if data is None:
            if "stat" in format_lower:
                data = self._get_stats()
            else:
                data = {"message": "No data provided"}
        
        # JSON format
        if "json" in format_lower:
            return json.dumps(data, default=str, indent=2)
        
        # Discord format
        if "discord" in format_lower:
            return self._format_for_discord(data)
        
        # CSV format
        if "csv" in format_lower:
            return self._format_as_csv(data)
        
        # Summary format
        if any(word in format_lower for word in ["summary", "brief", "short"]):
            return self._format_summary(data)
        
        # Stats format
        if "stat" in format_lower:
            return self._format_stats(data)
        
        # Plain text (default)
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform Start.gg sync actions using natural language.
        
        Examples:
            do("sync tournaments")              # Sync all tournaments
            do("sync")                          # Full sync
            do("fetch standings for 123")       # Fetch standings for tournament
            do("process tournaments")           # Process fetched tournaments
            do("update tournament 123")         # Update specific tournament
            do("cleanup old data")              # Clean old sync data
        """
        action_lower = action.lower().strip()
        
        # Sync operations
        if "sync" in action_lower:
            if "standing" in action_lower:
                # Sync standings for tournaments
                limit = self._extract_number(action, default=10)
                return self._sync_standings(limit=limit)
            elif "tournament" in action_lower or "all" in action_lower or action_lower == "sync":
                # Full tournament sync
                return self._sync_tournaments(**kwargs)
            else:
                # Default sync
                return self._sync_tournaments(**kwargs)
        
        # Fetch operations
        if "fetch" in action_lower:
            if "standing" in action_lower:
                # Extract tournament ID
                import re
                match = re.search(r'\d+', action)
                if match:
                    tournament_id = match.group()
                    standings = self._fetch_standings(tournament_id)
                    if standings:
                        self._process_standings(standings, tournament_id)
                    return {"fetched": tournament_id, "standings": len(standings) if standings else 0}
            elif "tournament" in action_lower:
                # Fetch tournaments
                tournaments = self._fetch_tournaments()
                return {"fetched": len(tournaments)}
        
        # Process operations
        if "process" in action_lower:
            if "tournament" in action_lower:
                # Process tournaments (expects data in kwargs)
                tournaments_data = kwargs.get('data', [])
                return self._process_tournaments(tournaments_data)
            elif "standing" in action_lower:
                # Process standings (expects data in kwargs)
                standings_data = kwargs.get('data', [])
                tournament_id = kwargs.get('tournament_id')
                return self._process_standings(standings_data, tournament_id)
        
        # Update operations
        if "update" in action_lower:
            if "tournament" in action_lower:
                # Extract tournament ID
                import re
                match = re.search(r'\d+', action)
                if match:
                    tournament_id = match.group()
                    return self._update_tournament(tournament_id)
        
        # Cleanup operations
        if any(word in action_lower for word in ["cleanup", "clean", "clear"]):
            return self._cleanup_old_data()
        
        # Default
        announcer.announce("StartGG Action", [f"Performing: {action}"])
        return {"action": action, "status": "completed"}
    
    # ============= Private Helper Methods =============
    
    def _extract_number(self, text: str, default: int = None) -> Optional[int]:
        """Extract a number from text"""
        import re
        match = re.search(r'\d+', text)
        return int(match.group()) if match else default
    
    def _set_year_range(self, year: int):
        """Set the year range for filtering"""
        self.current_year = year
        self.current_year_start = calendar.timegm((year, 1, 1, 0, 0, 0))
        self.current_year_end = calendar.timegm((year, 12, 31, 23, 59, 59))
        announcer.announce("StartGG", [f"Year range set to {year}"])
    
    def _get_stats(self) -> Dict:
        """Get sync statistics"""
        return {
            "sync_stats": self.sync_stats,
            "current_year": self.current_year,
            "region": f"{self.coordinates} ({self.radius})",
            "api_configured": bool(self.api_token)
        }
    
    def _check_api_status(self) -> Dict:
        """Check API connection status"""
        if not self.api_token:
            return {"status": "error", "message": "No API token configured"}
        
        # Try a simple query
        try:
            payload = {
                "query": "{ currentUser { id } }"
            }
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            if response.status_code == 200:
                return {"status": "connected", "api": "start.gg"}
            else:
                return {"status": "error", "code": response.status_code}
        except Exception as e:
            handle_exception(e, {"operation": "api_test", "api_url": self.api_url})
            return {"status": "error", "message": str(e)}
    
    @handle_errors(severity=ErrorSeverity.HIGH, context={"operation": "fetch_tournaments"})
    def _fetch_tournaments(self, year_filter: bool = True, max_pages: int = 10) -> List[Dict]:
        """Fetch tournaments from start.gg API"""
        info(f"Fetching tournaments from start.gg")
        announcer.announce("StartGG", ["Fetching tournaments from API"])
        
        all_tournaments = []
        page = 1
        total_pages = 1
        
        while page <= total_pages and page <= max_pages:
            variables = {
                "coordinates": self.coordinates,
                "radius": self.radius,
                "page": page
            }
            
            # Add year filtering
            if year_filter:
                variables["after"] = self.current_year_start
                variables["before"] = self.current_year_end
                # Debug info handled by announcer
            
            payload = {
                "query": SOCAL_TOURNAMENTS_QUERY,
                "variables": variables
            }
            
            try:
                # Make API call with timing
                start_time = time.time()
                announcer.announce("StartGG API", [f"Fetching page {page}"])
                response = requests.post(self.api_url, json=payload, headers=self.headers)
                response_time = time.time() - start_time
                
                # Adaptive rate limiting: faster responses = shorter waits
                adaptive_sleep = max(0.3, min(1.0, response_time * 0.5))
                time.sleep(adaptive_sleep)
                
                response.raise_for_status()
                data = response.json()
                
                if 'errors' in data:
                    error(f"API error: {data['errors']}")
                    self.sync_stats['errors'] += 1
                    break
                
                tournament_data = data.get('data', {}).get('tournaments', {})
                tournaments = tournament_data.get('nodes', [])
                page_info = tournament_data.get('pageInfo', {})
                
                # Update pagination
                if page == 1:
                    total_pages = page_info.get('totalPages', 1)
                    total_count = page_info.get('total', 0)
                    info(f"Found {total_count} tournaments across {total_pages} pages")
                    announcer.announce("StartGG API", [f"Found {total_count} tournaments"])
                
                all_tournaments.extend(tournaments)
                self.sync_stats['api_calls'] += 1
                
                # Next page
                page += 1
                
            except requests.RequestException as e:
                handle_exception(e, {
                    "operation": "fetch_tournaments_page", 
                    "page": page, 
                    "api_url": self.api_url,
                    "variables": variables
                })
                self.sync_stats['errors'] += 1
                break
            except Exception as e:
                handle_exception(e, {
                    "operation": "process_tournament_response", 
                    "page": page,
                    "context": "unexpected error during response processing"
                })
                self.sync_stats['errors'] += 1
                break
        
        self.sync_stats['tournaments_fetched'] = len(all_tournaments)
        info(f"Fetched {len(all_tournaments)} tournaments")
        announcer.announce("StartGG", [f"Fetched {len(all_tournaments)} tournaments"])
        
        return all_tournaments
    
    def _fetch_standings(self, tournament_id: str) -> Optional[List[Dict]]:
        """Fetch standings for a specific tournament"""
        # Debug info handled by announcer
        
        variables = {"tournamentId": tournament_id}
        payload = {
            "query": TOURNAMENT_STANDINGS_QUERY,
            "variables": variables
        }
        
        try:
            announcer.announce("StartGG API", [f"Fetching standings for {tournament_id}"])
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            # Reduced rate limiting for standings (less intensive)
            time.sleep(0.5)
            
            response.raise_for_status()
            data = response.json()
            
            if 'errors' in data:
                error(f"Standings error: {data['errors']}")
                return None
            
            tournament_data = data.get('data', {}).get('tournament')
            if not tournament_data:
                return None
            
            events = tournament_data.get('events', [])
            if not events:
                return None
            
            # Collect standings from all events
            all_standings = []
            for event in events:
                event_name = event.get('name', '')
                event_id = event.get('id', '')
                standings = event.get('standings', {}).get('nodes', [])
                
                # Add event context
                for standing in standings[:8]:  # Top 8 per event
                    standing['event_name'] = event_name
                    standing['event_id'] = event_id
                    all_standings.append(standing)
            
            self.sync_stats['standings_fetched'] += len(all_standings)
        # Debug info handled by announcer
            
            return all_standings
            
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            self.sync_stats['errors'] += 1
            return None
    
    def _process_tournaments(self, tournaments_data: List[Dict]) -> Dict:
        """Process tournament data for database storage"""
        logger.info(f"Processing {len(tournaments_data)} tournaments")
        announcer.announce("Database Sync", [f"Processing {len(tournaments_data)} tournaments"])
        
        processed = 0
        errors = 0
        
        with batch_operations(page_size=250) as queue:
            for tournament_data in tournaments_data:
                try:
                    self._process_single_tournament(queue, tournament_data)
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to process tournament: {e}")
                    errors += 1
        
        self.sync_stats['tournaments_processed'] += processed
        announcer.announce("Database Sync", [f"Processed {processed} tournaments"])
        
        return {"processed": processed, "errors": errors}
    
    def _process_single_tournament(self, queue, tournament_data: Dict):
        """Process a single tournament"""
        tournament_id = str(tournament_data.get('id', ''))
        if not tournament_id:
            return
        
        # Prepare tournament record
        tournament_record = {
            'id': tournament_id,
            'name': tournament_data.get('name', ''),
            'num_attendees': tournament_data.get('numAttendees', 0),
            'start_at': tournament_data.get('startAt'),
            'end_at': tournament_data.get('endAt'),
            'registration_closes_at': tournament_data.get('registrationClosesAt'),
            'timezone': tournament_data.get('timezone'),
            'venue_name': tournament_data.get('venueName'),
            'venue_address': tournament_data.get('venueAddress'),
            'city': tournament_data.get('city'),
            'country_code': tournament_data.get('countryCode'),
            'postal_code': tournament_data.get('postalCode'),
            'lat': tournament_data.get('lat'),
            'lng': tournament_data.get('lng'),
            'is_registration_open': 1 if tournament_data.get('isRegistrationOpen') else 0,
            'has_offline_events': 1 if tournament_data.get('hasOfflineEvents') else 0,
            'has_online_events': 1 if tournament_data.get('hasOnlineEvents') else 0,
            'tournament_type': tournament_data.get('tournamentType'),
            'sync_timestamp': int(time.time())
        }
        
        # Use database service to save/update
        result = database_service.do(f"update tournament {tournament_id}", **tournament_record)
        if not result:
            # Create new tournament
            from models.tournament_models import Tournament
            queue.create(Tournament, **tournament_record)
            announcer.announce("Database Save", [f"Created tournament: {tournament_record['name']}"])
    
    def _process_standings(self, standings_data: List[Dict], tournament_id: str) -> Dict:
        """Process standings data"""
        if not standings_data:
            return {"processed": 0}
        
        logger.debug(f"Processing {len(standings_data)} standings for {tournament_id}")
        announcer.announce("Database Sync", [f"Processing {len(standings_data)} standings"])
        
        processed = 0
        
        with batch_operations(page_size=50) as queue:
            for standing in standings_data:
                try:
                    self._process_single_standing(queue, standing, tournament_id)
                    processed += 1
                except Exception as e:
                    logger.error(f"Failed to process standing: {e}")
        
        announcer.announce("Database Save", [f"Saved {processed} standings"])
        return {"processed": processed}
    
    def _process_single_standing(self, queue, standing: Dict, tournament_id: str):
        """Process a single standing entry"""
        from models.tournament_models import TournamentPlacement
        
        placement = standing.get('placement')
        event_name = standing.get('event_name')
        event_id = standing.get('event_id')
        entrant = standing.get('entrant', {})
        
        if not entrant:
            return
        
        # Get player info from entrant
        participants = entrant.get('participants', [])
        if not participants:
            return
        
        player_info = participants[0].get('player', {})
        if not player_info:
            return
        
        startgg_id = str(player_info.get('id', ''))
        gamer_tag = player_info.get('gamerTag', '')
        
        if not startgg_id or not gamer_tag:
            return
        
        # Get or create player
        result = database_service.do("get or create player", 
                                    startgg_id=startgg_id,
                                    gamer_tag=gamer_tag)
        
        if result and 'id' in result:
            player_id = result['id']
            
            # Create placement record
            queue.create(TournamentPlacement,
                        tournament_id=str(tournament_id),
                        player_id=player_id,
                        placement=placement,
                        event_name=event_name,
                        event_id=str(event_id))
    
    def _sync_tournaments(self, **kwargs) -> Dict:
        """Full tournament sync operation"""
        logger.info("Starting full tournament sync")
        announcer.announce("StartGG Sync", ["Starting full tournament sync"])
        
        # Fetch tournaments
        tournaments = self._fetch_tournaments(**kwargs)
        
        if not tournaments:
            return {"status": "no tournaments found"}
        
        # Process tournaments
        result = self._process_tournaments(tournaments)
        
        # Optionally fetch standings
        if kwargs.get('fetch_standings', False):
            standings_limit = kwargs.get('standings_limit', 5)
            self._sync_standings(limit=standings_limit)
        
        announcer.announce("StartGG Sync", [f"Sync complete: {result['processed']} tournaments"])
        
        return {
            "tournaments_fetched": len(tournaments),
            "tournaments_processed": result['processed'],
            "errors": result.get('errors', 0),
            "stats": self.sync_stats
        }
    
    def _sync_standings(self, limit: int = 10) -> Dict:
        """Sync standings for tournaments that need them"""
        # Get tournaments needing standings
        tournaments_needing = database_service.ask(f"tournaments needing standings limit {limit}")
        
        if not tournaments_needing:
            return {"status": "no tournaments need standings"}
        
        synced = 0
        for tournament in tournaments_needing:
            tournament_id = tournament.get('id')
            if tournament_id:
                standings = self._fetch_standings(tournament_id)
                if standings:
                    self._process_standings(standings, tournament_id)
                    synced += 1
        
        return {"synced_standings": synced}
    
    def _update_tournament(self, tournament_id: str) -> Dict:
        """Update a specific tournament"""
        # Fetch fresh data for this tournament
        # This would need a specific query implementation
        announcer.announce("StartGG", [f"Updating tournament {tournament_id}"])
        return {"updated": tournament_id}
    
    def _cleanup_old_data(self) -> Dict:
        """Clean up old sync data"""
        announcer.announce("StartGG", ["Cleaning up old sync data"])
        # This would implement cleanup logic
        return {"status": "cleanup completed"}
    
    def _get_events(self) -> List[Dict]:
        """Get events from cached tournament data"""
        # This would return events from tournaments
        return []
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, dict) and 'sync_stats' in data:
            stats = data['sync_stats']
            return f"""📊 **Start.gg Sync Stats**
API Calls: {stats.get('api_calls', 0)}
Tournaments Fetched: {stats.get('tournaments_fetched', 0)}
Tournaments Processed: {stats.get('tournaments_processed', 0)}
Standings Fetched: {stats.get('standings_fetched', 0)}
Errors: {stats.get('errors', 0)}"""
        
        if isinstance(data, list) and data:
            # Format tournament list
            output = ["**Tournaments:**"]
            for item in data[:10]:
                if isinstance(item, dict):
                    name = item.get('name', 'Unknown')
                    attendees = item.get('numAttendees', 0)
                    output.append(f"• {name} ({attendees} attendees)")
            return "\n".join(output)
        
        return str(data)
    
    def _format_as_csv(self, data: Any) -> str:
        """Format data as CSV"""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Get headers
            headers = ['id', 'name', 'numAttendees', 'city', 'startAt']
            lines = [','.join(headers)]
            
            # Add rows
            for item in data:
                row = [str(item.get(h, '')) for h in headers]
                lines.append(','.join(row))
            
            return '\n'.join(lines)
        
        return str(data)
    
    def _format_summary(self, data: Any) -> str:
        """Format a brief summary"""
        if isinstance(data, list):
            return f"{len(data)} items"
        if isinstance(data, dict):
            if 'sync_stats' in data:
                stats = data['sync_stats']
                return f"Fetched: {stats.get('tournaments_fetched', 0)}, Processed: {stats.get('tournaments_processed', 0)}"
        return str(data)[:200]
    
    def _format_stats(self, data: Any) -> str:
        """Format statistics"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{key}:")
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        return str(data)
    
    def run(self):
        """
        Service run method required by ManagedService.
        For StartGG sync service, this can run periodic syncs or wait for commands.
        """
        info("StartGG Sync Service is running")
        announcer.announce("StartGG Sync", ["Service started and ready for sync operations"])
        
        try:
            # Service runs indefinitely, can be triggered via ask/tell/do methods
            while True:
                # Periodic health check or sync operations could go here
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            info("StartGG Sync Service shutdown requested")
        except Exception as e:
            error(f"StartGG Sync Service error: {e}")


# Global instance
startgg_sync = StartGGSyncManaged()


# Convenience function for backwards compatibility
def sync_from_startgg(page_size=250, fetch_standings=False, standings_limit=5):
    """Legacy sync function - now uses polymorphic pattern"""
    return startgg_sync.do("sync tournaments", 
                          fetch_standings=fetch_standings,
                          standings_limit=standings_limit)


def main():
    """Main function for running as a managed service"""
    with StartGGSyncManaged() as service:
        service.run()


if __name__ == "__main__":
    main()