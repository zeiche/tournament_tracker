"""
startgg_sync.py - Start.gg API Synchronization
Syncs tournament data using GraphQL API with session-safe database operations
"""
import os
import time
import requests
import calendar
from datetime import datetime
from collections import defaultdict

# Import our centralized modules
from log_manager import LogManager
from polymorphic_core import announcer

# Initialize logger for this module
logger = LogManager().get_logger('startgg_sync')

# Announce module capabilities on import
announcer.announce(
    "Start.gg Sync Service",
    [
        "Sync tournaments from start.gg API",
        "Fetch tournament standings and placements",
        "Update player rankings from events",
        "Query SoCal region tournaments",
        "Handle GraphQL API pagination",
        "Batch database operations for efficiency"
    ],
    [
        "./go.py --sync",
        "./go.py --fetch-standings",
        "sync_tournaments_from_startgg()"
    ]
)
from database import init_database, session_scope
from database_service import database_service
from database_queue import get_queue, commit_queue, queue_stats, batch_operations

# start.gg GraphQL queries
SOCAL_TOURNAMENTS_QUERY = """
query SocalTournaments($coordinates: String!, $radius: String!, $after: Timestamp, $before: Timestamp, $page: Int) {
    tournaments(query: {
        filter: {
            videogameIds: [1386]
            hasOnlineEvents: false
            location: {
                distanceFrom: $coordinates,
                distance: $radius
            }
            afterDate: $after
            beforeDate: $before
        }
        perPage: 50
        page: $page
    }) {
        pageInfo {
            total
            totalPages
            page
            perPage
        }
        nodes {
            id
            endAt
            startAt
            name
            numAttendees
            registrationClosesAt
            timezone
            venueAddress
            venueName
            city
            countryCode
            postalCode
            addrState
            lat
            lng
            owner {
                id
                name
            }
            primaryContact
            primaryContactType
            shortSlug
            slug
            state
            isRegistrationOpen
            currency
            hasOfflineEvents
            hasOnlineEvents
            tournamentType
            url
            events {
                id
                name
                numEntrants
            }
        }
    }
}
"""

TOURNAMENT_STANDINGS_QUERY = """
query TournamentStandings($tournamentId: ID!) {
    tournament(id: $tournamentId) {
        events(filter: {videogameId: 1386}) {
            id
            name
            standings(query: {page: 1, perPage: 8}) {
                nodes {
                    placement
                    entrant {
                        id
                        name
                        participants {
                            gamerTag
                            user {
                                id
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

class StartGGSyncClient:
    """start.gg API synchronization client"""
    
    def __init__(self):
        self.api_token = os.getenv("AUTH_KEY")
        if not self.api_token:
            raise RuntimeError("AUTH_KEY environment variable not set")
        
        self.api_url = "https://api.start.gg/gql/alpha"
        self.coordinates = "34.13436, -117.95763"  # SoCal coordinates
        self.radius = "67mi"
        
        # Current year date range (Unix timestamps)
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
        self.api_stats = {
            'api_calls': 0,
            'api_time': 0,
            'rate_limit_sleeps': 0
        }
        
        logger.info(f"StartGG client initialized for {current_year}")
    
    def fetch_tournaments(self, year_filter=True, max_pages=10):
        """Fetch tournaments from start.gg API with pagination"""
        logger.info(f"Fetching SoCal tournaments from start.gg")
        
        all_tournaments = []
        page = 1
        total_pages = 1
        
        while page <= total_pages and page <= max_pages:
            variables = {
                "coordinates": self.coordinates,
                "radius": self.radius,
                "page": page
            }
            
            # Add current year date filtering if enabled
            if year_filter:
                variables["after"] = self.current_year_start
                variables["before"] = self.current_year_end
                if page == 1:
                    logger.debug(f"Filtering for {self.current_year} tournaments only")
            
            payload = {
                "query": SOCAL_TOURNAMENTS_QUERY,
                "variables": variables
            }
            
            # Make the API call with rate limiting
            start_time = time.time()
            
            try:
                response = requests.post(self.api_url, json=payload, headers=self.headers)
                
                # Rate limiting - single sleep per API call
                time.sleep(1)
                self.api_stats['rate_limit_sleeps'] += 1
                
                response.raise_for_status()
                data = response.json()
                
                if 'errors' in data:
                    logger.error(f"start.gg API error: {data['errors']}")
                    raise RuntimeError(f"start.gg API error: {data['errors']}")
                
                tournament_data = data.get('data', {}).get('tournaments', {})
                tournaments = tournament_data.get('nodes', [])
                page_info = tournament_data.get('pageInfo', {})
                
                # Update pagination info
                if page == 1:
                    total_pages = page_info.get('totalPages', 1)
                    total_count = page_info.get('total', 0)
                    logger.info(f"Found {total_count} tournaments across {total_pages} pages")
                
                all_tournaments.extend(tournaments)
                
                # Update stats
                api_time = time.time() - start_time
                self.api_stats['api_calls'] += 1
                self.api_stats['api_time'] += api_time
                
                year_info = f" ({self.current_year} only)" if year_filter else ""
                logger.debug(f"API call tournaments{year_info} page {page}: {api_time:.2f}s - success")
                logger.debug(f"Fetched page {page}/{total_pages}: {len(tournaments)} tournaments")
                
                page += 1
                
            except Exception as e:
                api_time = time.time() - start_time
                self.api_stats['api_calls'] += 1
                logger.debug(f"API call tournaments page {page}: {api_time:.2f}s - failed")
                raise
        
        logger.info(f"Fetched {len(all_tournaments)} tournaments from start.gg")
        return all_tournaments
    
    def fetch_standings(self, tournament_id):
        """Fetch top 8 standings for a specific tournament"""
        logger.debug(f"Fetching standings for tournament {tournament_id}")
        
        variables = {"tournamentId": tournament_id}
        payload = {
            "query": TOURNAMENT_STANDINGS_QUERY,
            "variables": variables
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            time.sleep(1)  # Rate limiting
            self.api_stats['rate_limit_sleeps'] += 1
            
            response.raise_for_status()
            data = response.json()
            
            api_time = time.time() - start_time
            self.api_stats['api_calls'] += 1
            self.api_stats['api_time'] += api_time
            
            if 'errors' in data:
                logger.error(f"Standings error for {tournament_id}: {data['errors']}")
                return None, f"API error: {data['errors']}"
            
            tournament_data = data.get('data', {}).get('tournament')
            if not tournament_data:
                logger.debug(f"No tournament data for {tournament_id}")
                return None, "no tournament data"
            
            events = tournament_data.get('events', [])
            if not events:
                logger.debug(f"No events found for {tournament_id}")
                return None, "no events found"
            
            # Collect standings from all events
            all_standings = []
            for event in events:
                event_name = event.get('name', '')
                event_id = event.get('id', '')
                standings = event.get('standings', {}).get('nodes', [])
                
                # Add event context to each standing
                for standing in standings[:8]:  # Top 8 per event
                    standing['event_name'] = event_name
                    standing['event_id'] = event_id
                    all_standings.append(standing)
            
            logger.debug(f"API call standings/{tournament_id}: {api_time:.2f}s - success")
            logger.debug(f"Fetched {len(all_standings)} standings for {tournament_id}")
            
            return all_standings, None
            
        except Exception as e:
            api_time = time.time() - start_time
            self.api_stats['api_calls'] += 1
            logger.debug(f"API call standings/{tournament_id}: {api_time:.2f}s - failed")
            return None, str(e)
    
    def get_stats(self):
        """Get API client statistics"""
        return {
            'api_stats': self.api_stats
        }

class TournamentSyncProcessor:
    """Processes tournament data for database storage"""
    
    def __init__(self, page_size=250):
        self.page_size = page_size
        self.sync_stats = {
            'tournaments_processed': 0,
            'tournaments_created': 0,
            'tournaments_updated': 0,
            'organizations_created': 0,
            'standings_processed': 0,
            'processing_errors': 0
        }
    
    def process_tournaments(self, tournaments_data):
        """Process tournament data using paged queue system"""
        logger.info(f"Processing {len(tournaments_data)} tournaments", "sync")
        
        with batch_operations(page_size=self.page_size) as queue:
            for tournament_data in tournaments_data:
                try:
                    self._process_single_tournament(queue, tournament_data)
                    self.sync_stats['tournaments_processed'] += 1
                    
                except Exception as e:
                    self.sync_stats['processing_errors'] += 1
                    logger.error(f"Failed to process tournament {tournament_data.get('id', 'unknown')}: {e}", "sync")
        
        logger.info(f"Tournament processing completed - {self.sync_stats['tournaments_processed']} processed", "sync")
    
    def _process_single_tournament(self, queue, tournament_data):
        """Process a single tournament"""
        tournament_id = tournament_data.get('id')
        if not tournament_id:
            logger.error("Tournament missing ID, skipping", "sync")
            return
        
        # Convert tournament ID to string to match database schema
        tournament_id = str(tournament_id)
        
        # Prepare tournament record data
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
            'tournament_state': tournament_data.get('state', 0),
            'addr_state': tournament_data.get('addrState'),
            'lat': tournament_data.get('lat'),
            'lng': tournament_data.get('lng'),
            'owner_id': tournament_data.get('owner', {}).get('id'),
            'owner_name': tournament_data.get('owner', {}).get('name'),
            'primary_contact': tournament_data.get('primaryContact'),
            'primary_contact_type': tournament_data.get('primaryContactType'),
            # normalized_contact column removed from database
            'short_slug': tournament_data.get('shortSlug'),
            'slug': tournament_data.get('slug'),
            'url': tournament_data.get('url'),
            'is_registration_open': 1 if tournament_data.get('isRegistrationOpen') else 0,
            'currency': tournament_data.get('currency'),
            'has_offline_events': 1 if tournament_data.get('hasOfflineEvents') else 0,
            'has_online_events': 1 if tournament_data.get('hasOnlineEvents') else 0,
            'tournament_type': tournament_data.get('tournamentType'),
            'sync_timestamp': int(time.time())
        }
        
        # Simply replace/create tournament with latest data from start.gg
        from tournament_models import Tournament
        from database_service import database_service
        
        # Use proper session management for updates
        with session_scope() as session:
            existing = database_service.get_tournament_by_id(tournament_id)
            if existing:
                # Replace all fields with current start.gg data
                for key, value in tournament_record.items():
                    setattr(existing, key, value)
                # Session will auto-commit when context exits
            else:
                # Create new tournament via queue
                queue.create(Tournament, **tournament_record)
        
        # Process organization and attendance
        self._process_tournament_organization(queue, tournament_data)
    
    def _process_tournament_organization(self, queue, tournament_data):
        """Process organization and attendance for tournament"""
        primary_contact = tournament_data.get('primaryContact')
        num_attendees = tournament_data.get('numAttendees', 0)
        tournament_id = str(tournament_data.get('id'))  # Convert to string
        
        if not primary_contact or num_attendees <= 0:
            return
        
        # Organization creation disabled - normalized_key column no longer exists
        # Organizations are now created through the identify_orgs_simple.py script
        # after sync completes
        pass
    
    def process_standings(self, standings_data, tournament_id):
        """Process top 8 standings data"""
        if not standings_data:
            return
        
        logger.debug(f"Processing {len(standings_data)} standings for {tournament_id}", "sync")
        
        with batch_operations(page_size=50) as queue:
            for standing in standings_data:
                try:
                    self._process_single_standing(queue, standing, tournament_id)
                    self.sync_stats['standings_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process standing: {e}", "sync")
    
    def _process_single_standing(self, queue, standing, tournament_id):
        """Process a single standing entry"""
        from event_standardizer import EventStandardizer
        
        placement = standing.get('placement')
        event_name = standing.get('event_name')
        event_id = standing.get('event_id')
        
        # Standardize the event name
        event_info = EventStandardizer.standardize(event_name)
        
        # Only process Ultimate events (already filtered by API, but double-check)
        if event_info['game'] != 'ultimate':
            logger.debug(f"Skipping non-Ultimate event: {event_name} (detected as {event_info['game']})", "sync")
            return
        
        # Use the standardized name for storage
        normalized_event_name = event_info['standard_name']
        
        entrant = standing.get('entrant', {})
        participants = entrant.get('participants', [])
        
        if not participants:
            return
        
        # Get primary participant (first one)
        participant = participants[0]
        gamer_tag = participant.get('gamerTag', '')
        user_data = participant.get('user', {})
        user_id = user_data.get('id')
        real_name = user_data.get('name')
        
        if not gamer_tag or not user_id:
            return
        
        # Create player and placement callback
        def create_player_and_placement(session, startgg_id, tag, name, tourney_id, place, event_name, event_id):
            from tournament_models import Player, TournamentPlacement
            
            # Get or create player
            player = session.query(Player).filter_by(startgg_id=str(startgg_id)).first()
            if not player:
                player = Player(
                    startgg_id=str(startgg_id),
                    gamer_tag=tag,
                    name=name
                )
                session.add(player)
                session.flush()
            else:
                # Update info if provided
                if tag and player.gamer_tag != tag:
                    player.gamer_tag = tag
                if name and player.name != name:
                    player.name = name
            
            # Check if placement already exists
            existing = session.query(TournamentPlacement).filter_by(
                tournament_id=str(tourney_id),
                player_id=player.id,
                event_id=str(event_id)
            ).first()
            
            if existing:
                existing.placement = place
                existing.event_name = event_name
            else:
                placement_record = TournamentPlacement(
                    tournament_id=str(tourney_id),
                    player_id=player.id,
                    placement=place,
                    event_name=event_name,
                    event_id=str(event_id),
                    prize_amount=0  # Could be enhanced later
                )
                session.add(placement_record)
        
        # Queue player and placement creation
        queue.custom(
            create_player_and_placement,
            startgg_id=user_id,
            tag=gamer_tag,
            name=real_name,
            tourney_id=tournament_id,
            place=placement,
            event_name=normalized_event_name,  # Use normalized name
            event_id=event_id
        )
    
    def get_stats(self):
        """Get API client statistics"""
        return {
            'api_stats': self.api_stats
        }

def sync_from_startgg(page_size=250, fetch_standings=False, standings_limit=5):
    """Main synchronization function"""
    logger.info("Starting start.gg synchronization", "sync")
    
    sync_start_time = time.time()
    
    try:
        # Initialize client and processor
        client = StartGGSyncClient()
        processor = TournamentSyncProcessor(page_size=page_size)
        
        # Fetch tournaments
        with LogContext("Fetch tournaments from start.gg"):
            tournaments = client.fetch_tournaments(year_filter=True)
        
        if not tournaments:
            logger.error("No tournaments fetched from start.gg", "sync")
            return None
        
        # Process tournaments
        with LogContext("Process tournaments to database"):
            processor.process_tournaments(tournaments)
        
        # Fetch standings if requested
        if fetch_standings and tournaments:
            logger.info(f"Fetching standings for top {standings_limit} tournaments", "sync")
            
            # Sort by attendance and take top tournaments
            # Filter out tournaments with None attendees
            valid_tournaments = [
                t for t in tournaments 
                if t.get('numAttendees') is not None and t.get('numAttendees', 0) > 30
            ]
            major_tournaments = sorted(
                valid_tournaments,
                key=lambda x: x.get('numAttendees', 0),
                reverse=True
            )[:standings_limit]
            
            for tournament in major_tournaments:
                tournament_id = tournament.get('id')
                tournament_name = tournament.get('name', 'Unknown')
                
                logger.debug(f"Fetching standings for {tournament_name}", "sync")
                standings, error = client.fetch_standings(tournament_id)
                
                if standings:
                    processor.process_standings(standings, tournament_id)
                elif error:
                    logger.error(f"Standings fetch failed for {tournament_name}: {error}", "sync")
        
        # Normalize event names after fetching standings
        if fetch_standings:
            logger.info("Normalizing event names in database", "sync")
            from normalize_events import normalize_database_events
            norm_stats = normalize_database_events(dry_run=False)
            logger.info(f"Normalized {norm_stats['events_normalized']} events ({norm_stats['placements_updated']} placements)", "sync")
        
        # Calculate final stats
        sync_time = time.time() - sync_start_time
        client_stats = client.get_stats()
        processor_stats = processor.sync_stats
        
        # Get database summary
        db_stats = database_service.get_summary_stats()
        
        # Combined stats
        final_stats = {
            'api_stats': client_stats['api_stats'],
            'summary': {
                'tournaments_processed': processor_stats['tournaments_processed'],
                'organizations_created': processor_stats['organizations_created'],
                'standings_processed': processor_stats['standings_processed'],
                'processing_errors': processor_stats['processing_errors'],
                'total_processing_time': sync_time,
                'success_rate': (processor_stats['tournaments_processed'] / max(1, len(tournaments))) * 100
            },
            'database_totals': db_stats
        }
        
        # Log final summary
        logger.info("=" * 60, "sync")
        logger.info("SYNCHRONIZATION COMPLETED", "sync")
        logger.info("=" * 60, "sync")
        logger.info(f"API calls: {client_stats['api_stats']['api_calls']}", "sync")
        logger.info(f"Tournaments processed: {processor_stats['tournaments_processed']}", "sync")
        logger.info(f"Organizations created: {processor_stats['organizations_created']}", "sync")
        logger.info(f"Processing time: {sync_time:.2f}s", "sync")
        logger.info(f"Success rate: {final_stats['summary']['success_rate']:.1f}%", "sync")
        logger.info("=" * 60, "sync")
        
        return final_stats
        
    except Exception as e:
        logger.error(f"Synchronization failed: {e}", "sync")
        import traceback
        traceback.print_exc()
        return None
