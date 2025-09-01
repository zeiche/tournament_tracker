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
from log_utils import log_info, log_debug, log_error, log_api_call, LogContext

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
            log_error("AUTH_KEY environment variable not set", "startgg")
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
        
        log_info(f"start.gg query client initialized for {current_year}", "startgg")
        log_debug(f"API endpoint: {self.api_url}", "startgg")
        log_debug(f"Search area: {self.coordinates} within {self.radius}", "startgg")
    
    def fetch_socal_tournaments(self, year_filter=True):
        """
        Fetch tournaments from start.gg API with comprehensive data
        Single API call with rate limiting and logging
        """
        log_info("Fetching SoCal tournaments from start.gg", "startgg")
        
        variables = {
            "coordinates": self.coordinates,
            "radius": self.radius
        }
        
        # Add current year date filtering if enabled
        if year_filter:
            variables["after"] = self.current_year_start
            variables["before"] = self.current_year_end
            log_debug(f"Filtering tournaments for {self.current_year}", "startgg")
        else:
            log_debug("No year filtering applied", "startgg")
        
        payload = {
            "query": SOCAL_TOURNAMENTS_QUERY,
            "variables": variables
        }
        
        # Make the API call with rate limiting and logging
        start_time = time.time()
        
        try:
            log_debug("Making GraphQL request to start.gg", "startgg")
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            
            # SINGLE rate limit sleep - this is the only place in the entire system
            time.sleep(1)
            log_debug("Applied 1-second rate limit delay", "startgg")
            
            response.raise_for_status()
            data = response.json()
            
            if 'errors' in data:
                error_msg = f"start.gg API error: {data['errors']}"
                log_error(error_msg, "startgg")
                raise RuntimeError(error_msg)
            
            tournaments = data.get('data', {}).get('tournaments', {}).get('nodes', [])
            
            api_time = time.time() - start_time
            year_info = f" ({self.current_year} only)" if year_filter else ""
            
            log_api_call(f"tournaments{year_info}", api_time, success=True, context="startgg")
            log_info(f"Successfully fetched {len(tournaments)} tournaments", "startgg")
            
            # Log sample tournament for debugging
            if tournaments:
                sample = tournaments[0]
                log_debug(f"Sample tournament: {sample.get('name')} ({sample.get('numAttendees')} attendees)", "startgg")
            
            return tournaments, api_time, year_info
            
        except requests.RequestException as e:
            api_time = time.time() - start_time
            log_api_call("tournaments", api_time, success=False, context="startgg")
            log_error(f"API request failed: {e}", "startgg")
            raise
        except Exception as e:
            api_time = time.time() - start_time
            log_api_call("tournaments", api_time, success=False, context="startgg")
            raise
    
    def fetch_tournament_standings(self, tournament_id):
        """Fetch top 8 standings for a specific tournament with logging"""
        log_debug(f"Fetching standings for tournament {tournament_id}", "startgg")
        
        variables = {"tournamentId": tournament_id}
        
        payload = {
            "query": TOURNAMENT_STANDINGS_QUERY,
            "variables": variables
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            time.sleep(1)  # Rate limiting for each standings call
            log_debug("Applied rate limit delay for standings", "startgg")
            
            response.raise_for_status()
            data = response.json()
            
            api_time = time.time() - start_time
            
            if 'errors' in data:
                error_msg = f"standings error: {data['errors']}"
                log_api_call(f"standings/{tournament_id}", api_time, success=False, context="startgg")
                log_error(error_msg, "startgg")
                return None, error_msg
            
            tournament_data = data.get('data', {}).get('tournament')
            if not tournament_data:
                log_api_call(f"standings/{tournament_id}", api_time, success=False, context="startgg")
                log_debug(f"No tournament data returned for {tournament_id}", "startgg")
                return None, "no tournament data returned"
            
            events = tournament_data.get('events', [])
            if not events:
                log_api_call(f"standings/{tournament_id}", api_time, success=False, context="startgg")
                log_debug(f"No events found for {tournament_id}", "startgg")
                return None, "no events found"
            
            # Collect standings from all events
            all_standings = []
            for event in events:
                event_name = event.get('name', '')
                event_id = event.get('id', '')
                standings = event.get('standings', {}).get('nodes', [])
                
                log_debug(f"Processing event: {event_name} ({len(standings)} standings)", "startgg")
                
                # Add event context to each standing
                for standing in standings[:8]:  # Top 8 per event
                    standing['event_name'] = event_name
                    standing['event_id'] = event_id
                    all_standings.append(standing)
            
            log_api_call(f"standings/{tournament_id}", api_time, success=True, context="startgg")
            log_info(f"Fetched {len(all_standings)} standings from {len(events)} events", "startgg")
            
            return all_standings, None
            
        except requests.RequestException as e:
            api_time = time.time() - start_time
            log_api_call(f"standings/{tournament_id}", api_time, success=False, context="startgg")
            log_error(f"Standings API request failed for {tournament_id}: {e}", "startgg")
            return None, str(e)
        except Exception as e:
            api_time = time.time() - start_time
            log_api_call(f"standings/{tournament_id}", api_time, success=False, context="startgg")
            log_error(f"Standings fetch failed for {tournament_id}: {e}", "startgg")
            return None, str(e)

# Test functions for query client
def test_startgg_query_client():
    """Test start.gg query client functionality"""
    log_info("=" * 60, "test")
    log_info("TESTING START.GG QUERY CLIENT", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test 1: Client initialization
        log_info("TEST 1: Client initialization", "test")
        
        if not os.getenv("AUTH_KEY"):
            log_warn("AUTH_KEY not set - skipping API tests", "test")
            log_info("Set AUTH_KEY environment variable to run full tests", "test")
            return
        
        client = StartGGQueryClient()
        log_info("✅ Query client initialized", "test")
        
        # Test 2: Fetch tournaments
        log_info("TEST 2: Fetch tournaments", "test")
        
        with LogContext("Test tournament fetch"):
            tournaments, api_time, year_info = client.fetch_socal_tournaments()
            
            if tournaments:
                log_info(f"✅ Fetched {len(tournaments)} tournaments{year_info} in {api_time:.2f}s", "test")
                
                # Show sample tournament data
                if tournaments:
                    sample = tournaments[0]
                    log_info("Sample tournament data:", "test")
                    log_info(f"   ID: {sample.get('id')}", "test")
                    log_info(f"   Name: {sample.get('name')}", "test")
                    log_info(f"   Attendees: {sample.get('numAttendees')}", "test")
                    log_info(f"   Contact: {sample.get('primaryContact')}", "test")
            else:
                log_error("❌ No tournaments fetched", "test")
                return
        
        # Test 3: Fetch standings (if tournaments available)
        if tournaments:
            log_info("TEST 3: Fetch tournament standings", "test")
            
            # Find a major tournament for standings test
            major_tournament = None
            for t in tournaments:
                if t.get('numAttendees', 0) > 50:
                    major_tournament = t
                    break
            
            if major_tournament:
                tournament_id = major_tournament.get('id')
                tournament_name = major_tournament.get('name')
                
                log_debug(f"Testing standings fetch for: {tournament_name}", "test")
                
                standings, error = client.fetch_tournament_standings(tournament_id)
                
                if standings:
                    log_info(f"✅ Fetched {len(standings)} standings for {tournament_name}", "test")
                    
                    # Show sample standing
                    if standings:
                        sample_standing = standings[0]
                        log_info("Sample standing data:", "test")
                        log_info(f"   Placement: {sample_standing.get('placement')}", "test")
                        log_info(f"   Event: {sample_standing.get('event_name')}", "test")
                        
                        entrant = sample_standing.get('entrant', {})
                        participants = entrant.get('participants', [])
                        if participants:
                            log_info(f"   Player: {participants[0].get('gamerTag')}", "test")
                elif error:
                    log_warn(f"Standings fetch failed: {error}", "test")
            else:
                log_info("No major tournaments found for standings test", "test")
        
        log_info("✅ start.gg query client tests completed", "test")
        
    except Exception as e:
        log_error(f"start.gg query client test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_api_error_handling():
    """Test API error handling and edge cases"""
    log_info("=" * 60, "test")
    log_info("TESTING API ERROR HANDLING", "test")
    log_info("=" * 60, "test")
    
    try:
        if not os.getenv("AUTH_KEY"):
            log_warn("AUTH_KEY not set - skipping error handling tests", "test")
            return
        
        client = StartGGQueryClient()
        
        # Test 1: Invalid tournament ID for standings
        log_info("TEST 1: Invalid tournament ID", "test")
        standings, error = client.fetch_tournament_standings("invalid_tournament_id")
        
        if error:
            log_info(f"✅ Error handling works: {error}", "test")
        else:
            log_warn("Expected error for invalid tournament ID", "test")
        
        # Test 2: API rate limiting behavior
        log_info("TEST 2: Rate limiting behavior", "test")
        
        start_time = time.time()
        # Make two quick calls to test rate limiting
        client.fetch_socal_tournaments()
        client.fetch_socal_tournaments()
        total_time = time.time() - start_time
        
        if total_time >= 2.0:  # Should be at least 2 seconds due to rate limiting
            log_info(f"✅ Rate limiting working: {total_time:.2f}s for 2 calls", "test")
        else:
            log_warn(f"Rate limiting may not be working: {total_time:.2f}s for 2 calls", "test")
        
        log_info("✅ API error handling tests completed", "test")
        
    except Exception as e:
        log_error(f"API error handling test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def run_startgg_query_tests():
    """Run all start.gg query tests"""
    try:
        # Initialize logging
        from log_utils import init_logging, LogLevel
        init_logging(console=True, level=LogLevel.DEBUG, debug_file="startgg_query_test.txt")
        
        log_info("Starting start.gg query client tests", "test")
        
        # Run test suites
        test_startgg_query_client()
        print()  # Spacing
        test_api_error_handling()
        
        log_info("All start.gg query tests completed - check startgg_query_test.txt for details", "test")
        
    except Exception as e:
        log_error(f"start.gg query test suite failed: {e}", "test")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing start.gg query client...")
    run_startgg_query_tests()

