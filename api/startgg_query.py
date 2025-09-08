"""
startgg_query.py - Start.gg GraphQL API Query Interface
Raw API queries and data fetching with centralized logging
"""
import os
import time
import requests
import calendar
from datetime import datetime

# Import centralized logging
import sys
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')
from log_manager import LogManager

# Initialize logger for this module
logger = LogManager().get_logger('startgg_query')

# start.gg GraphQL queries
SOCAL_TOURNAMENTS_QUERY = """
query SocalTournaments($coordinates: String!, $radius: String!, $after: Timestamp, $before: Timestamp) {
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
    }) {
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

class StartGGQueryClient:
    """Raw start.gg API query client with logging"""
    
    def __init__(self):
        self.api_token = os.getenv("AUTH_KEY")
        if not self.api_token:
            logger.error("AUTH_KEY environment variable not set")
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
        
        logger.info(f"start.gg query client initialized for {current_year}")
        logger.debug(f"API endpoint: {self.api_url}")
        logger.debug(f"Search area: {self.coordinates} within {self.radius}")
    
    def fetch_socal_tournaments(self, year_filter=True):
        """
        Fetch tournaments from start.gg API with comprehensive data
        Single API call with rate limiting and logging
        """
        logger.info("Fetching SoCal tournaments from start.gg")
        
        variables = {
            "coordinates": self.coordinates,
            "radius": self.radius
        }
        
        # Add current year date filtering if enabled
        if year_filter:
            variables["after"] = self.current_year_start
            variables["before"] = self.current_year_end
            logger.debug(f"Filtering tournaments for {self.current_year}")
        else:
            logger.debug("No year filtering applied")
        
        payload = {
            "query": SOCAL_TOURNAMENTS_QUERY,
            "variables": variables
        }
        
        # Make the API call with rate limiting and logging
        start_time = time.time()
        
        try:
            logger.debug("Making GraphQL request to start.gg")
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            
            # SINGLE rate limit sleep - this is the only place in the entire system
            time.sleep(1)
            logger.debug("Applied 1-second rate limit delay")
            
            response.raise_for_status()
            data = response.json()
            
            if 'errors' in data:
                error_msg = f"start.gg API error: {data['errors']}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            tournaments = data.get('data', {}).get('tournaments', {}).get('nodes', [])
            
            api_time = time.time() - start_time
            year_info = f" ({self.current_year} only)" if year_filter else ""
            
            logger.debug(f"API call tournaments{year_info}: {api_time:.2f}s - success")
            logger.info(f"Successfully fetched {len(tournaments)} tournaments")
            
            # Log sample tournament for debugging
            if tournaments:
                sample = tournaments[0]
                logger.debug(f"Sample tournament: {sample.get('name')} ({sample.get('numAttendees')} attendees)")
            
            return tournaments, api_time, year_info
            
        except requests.RequestException as e:
            api_time = time.time() - start_time
            logger.debug(f"API call tournaments: {api_time:.2f}s - failed")
            logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            api_time = time.time() - start_time
            logger.debug(f"API call tournaments: {api_time:.2f}s - failed")
            raise
    
    def fetch_tournament_standings(self, tournament_id):
        """Fetch top 8 standings for a specific tournament with logging"""
        logger.debug(f"Fetching standings for tournament {tournament_id}")
        
        variables = {"tournamentId": tournament_id}
        
        payload = {
            "query": TOURNAMENT_STANDINGS_QUERY,
            "variables": variables
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            time.sleep(1)  # Rate limiting for each standings call
            logger.debug("Applied rate limit delay for standings")
            
            response.raise_for_status()
            data = response.json()
            
            api_time = time.time() - start_time
            
            if 'errors' in data:
                error_msg = f"standings error: {data['errors']}"
                logger.debug(f"API call standings/{tournament_id}: {api_time:.2f}s - failed")
                logger.error(error_msg)
                return None, error_msg
            
            tournament_data = data.get('data', {}).get('tournament')
            if not tournament_data:
                logger.debug(f"API call standings/{tournament_id}: {api_time:.2f}s - failed")
                logger.debug(f"No tournament data returned for {tournament_id}")
                return None, "no tournament data returned"
            
            events = tournament_data.get('events', [])
            if not events:
                logger.debug(f"API call standings/{tournament_id}: {api_time:.2f}s - failed")
                logger.debug(f"No events found for {tournament_id}")
                return None, "no events found"
            
            # Collect standings from all events
            all_standings = []
            for event in events:
                event_name = event.get('name', '')
                event_id = event.get('id', '')
                standings = event.get('standings', {}).get('nodes', [])
                
                logger.debug(f"Processing event: {event_name} ({len(standings)} standings)")
                
                # Add event context to each standing
                for standing in standings[:8]:  # Top 8 per event
                    standing['event_name'] = event_name
                    standing['event_id'] = event_id
                    all_standings.append(standing)
            
            logger.debug(f"API call standings/{tournament_id}: {api_time:.2f}s - success")
            logger.info(f"Fetched {len(all_standings)} standings from {len(events)} events")
            
            return all_standings, None
            
        except requests.RequestException as e:
            api_time = time.time() - start_time
            logger.debug(f"API call standings/{tournament_id}: {api_time:.2f}s - failed")
            logger.error(f"Standings API request failed for {tournament_id}: {e}")
            return None, str(e)
        except Exception as e:
            api_time = time.time() - start_time
            logger.debug(f"API call standings/{tournament_id}: {api_time:.2f}s - failed")
            logger.error(f"Standings fetch failed for {tournament_id}: {e}")
            return None, str(e)

# Test functions for query client
def test_startgg_query_client():
    """Test start.gg query client functionality"""
    logger.info("=" * 60)
    logger.info("TESTING START.GG QUERY CLIENT")
    logger.info("=" * 60)
    
    try:
        # Test 1: Client initialization
        logger.info("TEST 1: Client initialization")
        
        if not os.getenv("AUTH_KEY"):
            logger.warning("AUTH_KEY not set - skipping API tests")
            logger.info("Set AUTH_KEY environment variable to run full tests")
            return
        
        client = StartGGQueryClient()
        logger.info("✅ Query client initialized")
        
        # Test 2: Fetch tournaments
        logger.info("TEST 2: Fetch tournaments")
        
        tournaments, api_time, year_info = client.fetch_socal_tournaments()
        
        if tournaments:
            logger.info(f"✅ Fetched {len(tournaments)} tournaments{year_info} in {api_time:.2f}s")
            
            # Show sample tournament data
            if tournaments:
                sample = tournaments[0]
                logger.info("Sample tournament data:")
                logger.info(f"   ID: {sample.get('id')}")
                logger.info(f"   Name: {sample.get('name')}")
                logger.info(f"   Attendees: {sample.get('numAttendees')}")
                logger.info(f"   Contact: {sample.get('primaryContact')}")
        else:
            logger.error("❌ No tournaments fetched")
            return
        
        # Test 3: Fetch standings (if tournaments available)
        if tournaments:
            logger.info("TEST 3: Fetch tournament standings")
            
            # Find a major tournament for standings test
            major_tournament = None
            for t in tournaments:
                if t.get('numAttendees', 0) > 50:
                    major_tournament = t
                    break
            
            if major_tournament:
                tournament_id = major_tournament.get('id')
                tournament_name = major_tournament.get('name')
                
                logger.debug(f"Testing standings fetch for: {tournament_name}")
                
                standings, error = client.fetch_tournament_standings(tournament_id)
                
                if standings:
                    logger.info(f"✅ Fetched {len(standings)} standings for {tournament_name}")
                    
                    # Show sample standing
                    if standings:
                        sample_standing = standings[0]
                        logger.info("Sample standing data:")
                        logger.info(f"   Placement: {sample_standing.get('placement')}")
                        logger.info(f"   Event: {sample_standing.get('event_name')}")
                        
                        entrant = sample_standing.get('entrant', {})
                        participants = entrant.get('participants', [])
                        if participants:
                            logger.info(f"   Player: {participants[0].get('gamerTag')}")
                elif error:
                    logger.warning(f"Standings fetch failed: {error}")
            else:
                logger.info("No major tournaments found for standings test")
        
        logger.info("✅ start.gg query client tests completed")
        
    except Exception as e:
        logger.error(f"start.gg query client test failed: {e}")
        import traceback
        traceback.print_exc()

def test_api_error_handling():
    """Test API error handling and edge cases"""
    logger.info("=" * 60)
    logger.info("TESTING API ERROR HANDLING")
    logger.info("=" * 60)
    
    try:
        if not os.getenv("AUTH_KEY"):
            logger.warning("AUTH_KEY not set - skipping error handling tests")
            return
        
        client = StartGGQueryClient()
        
        # Test 1: Invalid tournament ID for standings
        logger.info("TEST 1: Invalid tournament ID")
        standings, error = client.fetch_tournament_standings("invalid_tournament_id")
        
        if error:
            logger.info(f"✅ Error handling works: {error}")
        else:
            logger.warning("Expected error for invalid tournament ID")
        
        # Test 2: API rate limiting behavior
        logger.info("TEST 2: Rate limiting behavior")
        
        start_time = time.time()
        # Make two quick calls to test rate limiting
        client.fetch_socal_tournaments()
        client.fetch_socal_tournaments()
        total_time = time.time() - start_time
        
        if total_time >= 2.0:  # Should be at least 2 seconds due to rate limiting
            logger.info(f"✅ Rate limiting working: {total_time:.2f}s for 2 calls")
        else:
            logger.warning(f"Rate limiting may not be working: {total_time:.2f}s for 2 calls")
        
        logger.info("✅ API error handling tests completed")
        
    except Exception as e:
        logger.error(f"API error handling test failed: {e}")
        import traceback
        traceback.print_exc()

def run_startgg_query_tests():
    """Run all start.gg query tests"""
    try:
        logger.info("Starting start.gg query client tests")
        
        # Run test suites
        test_startgg_query_client()
        print()  # Spacing
        test_api_error_handling()
        
        logger.info("All start.gg query tests completed")
        
    except Exception as e:
        logger.error(f"start.gg query test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing start.gg query client...")
    run_startgg_query_tests()

