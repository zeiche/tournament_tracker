#!/usr/bin/env python3
"""
query_wrappers.py - Smart wrapper system for database results
Provides chainable, intuitive methods on query results

Examples:
    players("west").tournaments()  # Get all tournaments West played in
    players("west").wins()         # Get tournaments West won
    players("west").stats()        # Get West's statistics
    
    tournaments("recent").players()  # Get all players from recent tournaments
    tournaments("recent").top_8()    # Get top 8 finishers from recent tournaments
    
    organizations("shark tank").tournaments()  # Get all Shark Tank tournaments
"""

from typing import List, Optional, Union, Dict, Any, TypeVar, Generic
from database import session_scope
from tournament_models import Player, Tournament, Organization, TournamentPlacement
from sqlalchemy import func, desc, and_, or_, case
from datetime import datetime, timedelta
import re

T = TypeVar('T')


class ResultWrapper(Generic[T]):
    """Base wrapper class for all database results"""
    
    def __init__(self, results: Union[T, List[T]]):
        """Initialize with query results"""
        if isinstance(results, list):
            self._results = results
            self._single = False
        else:
            self._results = [results] if results else []
            self._single = True
    
    def __iter__(self):
        """Make the wrapper iterable"""
        return iter(self._results)
    
    def __len__(self):
        """Return the count of results"""
        return len(self._results)
    
    def __getitem__(self, index):
        """Allow indexing into results"""
        return self._results[index]
    
    def __bool__(self):
        """Return True if there are results"""
        return bool(self._results)
    
    def first(self):
        """Get the first result or None"""
        if self._results:
            obj = self._results[0]
            # Ensure all attributes are loaded if it's a SQLAlchemy model
            if hasattr(obj, '__dict__'):
                # Force load all attributes by accessing __dict__
                _ = {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
            return obj
        return None
    
    def all(self):
        """Get all results as a list"""
        return self._results
    
    def count(self):
        """Get the count of results"""
        return len(self._results)
    
    def get(self):
        """Get single result if there's only one, otherwise raise error"""
        if self._single and len(self._results) == 1:
            return self._results[0]
        elif len(self._results) == 1:
            return self._results[0]
        elif len(self._results) == 0:
            return None
        else:
            raise ValueError(f"Expected single result, got {len(self._results)}")


class PlayerWrapper(ResultWrapper[Player]):
    """Wrapper for Player query results with chainable methods"""
    
    def tournaments(self) -> 'TournamentWrapper':
        """Get all tournaments these players participated in"""
        with session_scope() as session:
            tournament_ids = set()
            for player in self._results:
                placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.player_id == player.id
                ).all()
                tournament_ids.update(p.tournament_id for p in placements)
            
            tournaments = session.query(Tournament).filter(
                Tournament.id.in_(tournament_ids)
            ).order_by(desc(Tournament.start_at)).all()
            
            # Detach from session by accessing all attributes
            for t in tournaments:
                _ = t.id, t.name, t.num_attendees, t.venue_name, t.start_at, t.end_at
            
            return TournamentWrapper(tournaments)
    
    def wins(self) -> 'TournamentWrapper':
        """Get tournaments these players won (1st place)"""
        with session_scope() as session:
            tournament_ids = set()
            for player in self._results:
                wins = session.query(TournamentPlacement).filter(
                    TournamentPlacement.player_id == player.id,
                    TournamentPlacement.placement == 1
                ).all()
                tournament_ids.update(w.tournament_id for w in wins)
            
            tournaments = session.query(Tournament).filter(
                Tournament.id.in_(tournament_ids)
            ).order_by(desc(Tournament.start_at)).all()
            
            # Detach from session by accessing all attributes
            for t in tournaments:
                _ = t.id, t.name, t.num_attendees, t.venue_name, t.start_at, t.end_at
            
            return TournamentWrapper(tournaments)
    
    def placements(self) -> List[TournamentPlacement]:
        """Get all placements for these players"""
        with session_scope() as session:
            all_placements = []
            for player in self._results:
                placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.player_id == player.id
                ).order_by(desc(TournamentPlacement.recorded_at)).all()
                
                # Detach from session
                for p in placements:
                    _ = p.placement, p.event_name
                
                all_placements.extend(placements)
            
            return all_placements
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics for these players"""
        if len(self._results) == 1:
            # Single player stats
            player = self._results[0]
            with session_scope() as session:
                from points_system import PointsSystem
                
                points_case = PointsSystem.get_sql_case_expression()
                stats = session.query(
                    func.sum(points_case).label('total_points'),
                    func.count(TournamentPlacement.id).label('tournament_count'),
                    func.sum(case((TournamentPlacement.placement == 1, 1), else_=0)).label('wins'),
                    func.sum(case((TournamentPlacement.placement <= 3, 1), else_=0)).label('podiums'),
                    func.sum(case((TournamentPlacement.placement <= 8, 1), else_=0)).label('top_8s')
                ).filter(
                    TournamentPlacement.player_id == player.id
                ).first()
                
                tournament_count = int(stats.tournament_count or 0) if stats else 0
                wins = int(stats.wins or 0) if stats else 0
                podiums = int(stats.podiums or 0) if stats else 0
                top_8s = int(stats.top_8s or 0) if stats else 0
                total_points = int(stats.total_points or 0) if stats else 0
                
                return {
                    'player': player.gamer_tag,
                    'total_points': total_points,
                    'tournaments': tournament_count,
                    'wins': wins,
                    'podiums': podiums,
                    'top_8_finishes': top_8s,
                    'win_rate': (wins / tournament_count * 100) if tournament_count > 0 else 0,
                    'podium_rate': (podiums / tournament_count * 100) if tournament_count > 0 else 0
                }
        else:
            # Multiple players aggregate stats
            with session_scope() as session:
                from points_system import PointsSystem
                
                player_ids = [p.id for p in self._results]
                points_case = PointsSystem.get_sql_case_expression()
                
                stats = session.query(
                    func.sum(points_case).label('total_points'),
                    func.count(TournamentPlacement.id).label('total_placements'),
                    func.count(func.distinct(TournamentPlacement.player_id)).label('player_count'),
                    func.sum(case((TournamentPlacement.placement == 1, 1), else_=0)).label('total_wins')
                ).filter(
                    TournamentPlacement.player_id.in_(player_ids)
                ).first()
                
                return {
                    'player_count': len(self._results),
                    'total_points': int(stats.total_points or 0),
                    'total_placements': stats.total_placements or 0,
                    'total_wins': stats.total_wins or 0
                }
    
    def recent(self, days: int = 30) -> 'PlayerWrapper':
        """Filter to players who played in the last N days"""
        with session_scope() as session:
            cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            recent_player_ids = set()
            for player in self._results:
                recent_placements = session.query(TournamentPlacement).join(
                    Tournament
                ).filter(
                    TournamentPlacement.player_id == player.id,
                    Tournament.start_at >= cutoff_timestamp
                ).limit(1).all()
                
                if recent_placements:
                    recent_player_ids.add(player.id)
            
            filtered_players = [p for p in self._results if p.id in recent_player_ids]
            return PlayerWrapper(filtered_players)
    
    def display(self) -> str:
        """Display formatted player information"""
        if not self._results:
            return "No players found"
        
        if self._single and len(self._results) == 1:
            player = self._results[0]
            stats = self.stats()
            return f"""
Player: {player.gamer_tag}
Real Name: {player.name or 'Unknown'}
Total Points: {stats['total_points']}
Tournaments: {stats['tournaments']}
Wins: {stats['wins']} ({stats['win_rate']:.1f}%)
Podiums: {stats['podiums']} ({stats['podium_rate']:.1f}%)
"""
        else:
            output = f"Found {len(self._results)} players:\n"
            for i, player in enumerate(self._results[:10], 1):
                output += f"{i}. {player.gamer_tag}"
                if player.name:
                    output += f" ({player.name})"
                output += "\n"
            if len(self._results) > 10:
                output += f"... and {len(self._results) - 10} more\n"
            return output


class TournamentWrapper(ResultWrapper[Tournament]):
    """Wrapper for Tournament query results with chainable methods"""
    
    def players(self) -> PlayerWrapper:
        """Get all players from these tournaments"""
        with session_scope() as session:
            player_ids = set()
            for tournament in self._results:
                placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.tournament_id == tournament.id
                ).all()
                player_ids.update(p.player_id for p in placements)
            
            players = session.query(Player).filter(
                Player.id.in_(player_ids)
            ).order_by(Player.gamer_tag).all()
            
            # Detach from session by accessing all attributes
            for p in players:
                _ = p.id, p.gamer_tag, p.name, p.startgg_id
            
            return PlayerWrapper(players)
    
    def winners(self) -> PlayerWrapper:
        """Get winners (1st place) from these tournaments"""
        with session_scope() as session:
            winner_ids = set()
            for tournament in self._results:
                winners = session.query(TournamentPlacement).filter(
                    TournamentPlacement.tournament_id == tournament.id,
                    TournamentPlacement.placement == 1
                ).all()
                winner_ids.update(w.player_id for w in winners)
            
            players = session.query(Player).filter(
                Player.id.in_(winner_ids)
            ).order_by(Player.gamer_tag).all()
            
            # Detach from session by accessing all attributes
            for p in players:
                _ = p.id, p.gamer_tag, p.name, p.startgg_id
            
            return PlayerWrapper(players)
    
    def top_8(self) -> List[Dict[str, Any]]:
        """Get top 8 finishers from these tournaments"""
        results = []
        with session_scope() as session:
            for tournament in self._results:
                placements = session.query(
                    TournamentPlacement, Player
                ).join(Player).filter(
                    TournamentPlacement.tournament_id == tournament.id,
                    TournamentPlacement.placement <= 8
                ).order_by(TournamentPlacement.placement).all()
                
                for placement, player in placements:
                    results.append({
                        'tournament': tournament.name,
                        'player': player.gamer_tag,
                        'placement': placement.placement,
                        'event': placement.event_name
                    })
        
        return results
    
    def organization(self) -> 'OrganizationWrapper':
        """Get the organizations that ran these tournaments"""
        with session_scope() as session:
            org_ids = set()
            for tournament in self._results:
                if tournament.organization_id:
                    org_ids.add(tournament.organization_id)
            
            orgs = session.query(Organization).filter(
                Organization.id.in_(org_ids)
            ).all()
            
            # Detach from session by accessing all attributes
            for o in orgs:
                _ = o.id, o.display_name, o.contacts
            
            return OrganizationWrapper(orgs)
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics for these tournaments"""
        if not self._results:
            return {'count': 0}
        
        total_attendance = sum(t.num_attendees or 0 for t in self._results)
        avg_attendance = total_attendance / len(self._results) if self._results else 0
        
        return {
            'count': len(self._results),
            'total_attendance': total_attendance,
            'average_attendance': avg_attendance,
            'date_range': {
                'earliest': min((t.start_date for t in self._results if t.start_date), default=None),
                'latest': max((t.start_date for t in self._results if t.start_date), default=None)
            }
        }
    
    def recent(self, days: int = 30) -> 'TournamentWrapper':
        """Filter to tournaments in the last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_timestamp = int(cutoff.timestamp())
        
        filtered = [t for t in self._results if t.start_at and t.start_at >= cutoff_timestamp]
        return TournamentWrapper(filtered)
    
    def display(self) -> str:
        """Display formatted tournament information"""
        if not self._results:
            return "No tournaments found"
        
        output = f"Found {len(self._results)} tournaments:\n"
        for t in self._results[:10]:
            date_str = t.start_date.strftime('%Y-%m-%d') if t.start_date else 'Unknown'
            output += f"- {t.name} ({date_str}) - {t.num_attendees or 0} attendees\n"
        
        if len(self._results) > 10:
            output += f"... and {len(self._results) - 10} more\n"
        
        return output


class OrganizationWrapper(ResultWrapper[Organization]):
    """Wrapper for Organization query results with chainable methods"""
    
    def tournaments(self) -> TournamentWrapper:
        """Get all tournaments from these organizations"""
        with session_scope() as session:
            tournament_ids = set()
            for org in self._results:
                tournaments = session.query(Tournament).filter(
                    Tournament.organization_id == org.id
                ).all()
                tournament_ids.update(t.id for t in tournaments)
            
            tournaments = session.query(Tournament).filter(
                Tournament.id.in_(tournament_ids)
            ).order_by(desc(Tournament.start_at)).all()
            
            # Detach from session by accessing all attributes
            for t in tournaments:
                _ = t.id, t.name, t.num_attendees, t.venue_name, t.start_at
            
            return TournamentWrapper(tournaments)
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics for these organizations"""
        with session_scope() as session:
            stats_list = []
            for org in self._results:
                tournaments = session.query(Tournament).filter(
                    Tournament.organization_id == org.id
                ).all()
                
                total_attendance = sum(t.num_attendees or 0 for t in tournaments)
                stats_list.append({
                    'organization': org.display_name,
                    'tournament_count': len(tournaments),
                    'total_attendance': total_attendance,
                    'avg_attendance': total_attendance / len(tournaments) if tournaments else 0
                })
            
            if self._single and len(stats_list) == 1:
                return stats_list[0]
            else:
                return {
                    'organization_count': len(self._results),
                    'organizations': stats_list,
                    'total_tournaments': sum(s['tournament_count'] for s in stats_list),
                    'total_attendance': sum(s['total_attendance'] for s in stats_list)
                }
    
    def display(self) -> str:
        """Display formatted organization information"""
        if not self._results:
            return "No organizations found"
        
        output = f"Found {len(self._results)} organizations:\n"
        for org in self._results[:10]:
            output += f"- {org.display_name}\n"
        
        if len(self._results) > 10:
            output += f"... and {len(self._results) - 10} more\n"
        
        return output


# Query helper functions
def players(query: Optional[Union[str, int]] = None) -> PlayerWrapper:
    """
    Query players with natural language or specific criteria
    
    Examples:
        players()               # All players
        players("west")        # Search for player named "west"
        players("top 10")      # Top 10 players by points
        players(123)           # Player with ID 123
    """
    with session_scope() as session:
        if query is None:
            # Return all players
            result = session.query(Player).order_by(Player.gamer_tag).all()
        elif isinstance(query, int):
            # Query by ID
            result = session.query(Player).filter(Player.id == query).first()
        elif isinstance(query, str):
            query_lower = query.lower()
            
            # Check for "top N" pattern
            if "top" in query_lower:
                match = re.search(r'top\s*(\d+)', query_lower)
                limit = int(match.group(1)) if match else 10
                
                from points_system import PointsSystem
                points_case = PointsSystem.get_sql_case_expression()
                
                result = session.query(
                    Player,
                    func.sum(points_case).label('total_points')
                ).join(TournamentPlacement).group_by(
                    Player.id
                ).order_by(
                    desc('total_points')
                ).limit(limit).all()
                
                # Extract just the Player objects
                result = [p[0] for p in result]
            else:
                # Search by name
                search_pattern = f'%{query}%'
                result = session.query(Player).filter(
                    or_(
                        func.lower(Player.gamer_tag).like(search_pattern.lower()),
                        func.lower(Player.name).like(search_pattern.lower())
                    )
                ).all()
        
        # Create detached copies with all attributes loaded
        detached_results = []
        if isinstance(result, list):
            for p in result:
                # Create a simple object with the needed attributes
                player_data = type('Player', (), {
                    'id': p.id,
                    'gamer_tag': p.gamer_tag,
                    'name': p.name,
                    'startgg_id': p.startgg_id,
                    '__tablename__': 'players'
                })()
                detached_results.append(player_data)
            return PlayerWrapper(detached_results)
        elif result:
            # Create a simple object with the needed attributes
            player_data = type('Player', (), {
                'id': result.id,
                'gamer_tag': result.gamer_tag,
                'name': result.name,
                'startgg_id': result.startgg_id,
                '__tablename__': 'players'
            })()
            return PlayerWrapper(player_data)
        else:
            return PlayerWrapper([])


def tournaments(query: Optional[Union[str, int]] = None) -> TournamentWrapper:
    """
    Query tournaments with natural language or specific criteria
    
    Examples:
        tournaments()           # All tournaments
        tournaments("recent")   # Recent tournaments
        tournaments("shark")    # Search for tournaments with "shark" in name
        tournaments(123)        # Tournament with ID 123
    """
    with session_scope() as session:
        if query is None:
            # Return all tournaments
            result = session.query(Tournament).order_by(
                desc(Tournament.start_at)
            ).all()
        elif isinstance(query, int):
            # Query by ID
            result = session.query(Tournament).filter(Tournament.id == query).first()
        elif isinstance(query, str):
            query_lower = query.lower()
            
            if "recent" in query_lower:
                # Recent tournaments (last 30 days)
                cutoff = int((datetime.now() - timedelta(days=30)).timestamp())
                result = session.query(Tournament).filter(
                    Tournament.start_at >= cutoff
                ).order_by(desc(Tournament.start_at)).all()
            elif "upcoming" in query_lower:
                # Future tournaments
                current_timestamp = int(datetime.now().timestamp())
                result = session.query(Tournament).filter(
                    Tournament.start_at > current_timestamp
                ).order_by(Tournament.start_at).all()
            else:
                # Search by name
                search_pattern = f'%{query}%'
                result = session.query(Tournament).filter(
                    func.lower(Tournament.name).like(search_pattern.lower())
                ).order_by(desc(Tournament.start_at)).all()
        
        # Create detached copies with all attributes loaded while still in session
        if isinstance(result, list):
            detached_results = []
            for t in result:
                # Access all attributes while in session to eagerly load them
                tid = t.id
                tname = t.name
                tnum = t.num_attendees
                tvenue = t.venue_name
                tstart = t.start_at
                tend = t.end_at
                tlat = t.lat
                tlng = t.lng
                
                # Get organization_id through relationship if available
                org_id = None
                if hasattr(t, 'organization') and t.organization:
                    try:
                        org_id = t.organization.id
                    except:
                        pass
                
                # Get start_date property if available
                tdate = None
                try:
                    if hasattr(t, 'start_date'):
                        tdate = t.start_date
                except:
                    pass
                
                # Create a simple detached object
                tournament_data = type('Tournament', (), {
                    'id': tid,
                    'name': tname,
                    'num_attendees': tnum,
                    'venue_name': tvenue,
                    'start_at': tstart,
                    'end_at': tend,
                    'lat': tlat,
                    'lng': tlng,
                    'organization_id': org_id,
                    'start_date': tdate,
                    '__tablename__': 'tournaments'
                })()
                detached_results.append(tournament_data)
            return TournamentWrapper(detached_results)
        elif result:
            # Create a simple object with the needed attributes
            # Get organization_id through relationship if available
            org_id = None
            if hasattr(result, 'organization') and result.organization:
                org_id = result.organization.id
                
            tournament_data = type('Tournament', (), {
                'id': result.id,
                'name': result.name,
                'num_attendees': result.num_attendees,
                'venue_name': result.venue_name,
                'start_at': result.start_at,
                'end_at': result.end_at,
                'lat': result.lat,
                'lng': result.lng,
                'organization_id': org_id,
                'start_date': result.start_date if hasattr(result, 'start_date') else None,
                '__tablename__': 'tournaments'
            })()
            return TournamentWrapper(tournament_data)
        else:
            return TournamentWrapper([])


def organizations(query: Optional[Union[str, int]] = None) -> OrganizationWrapper:
    """
    Query organizations with natural language or specific criteria
    
    Examples:
        organizations()         # All organizations
        organizations("shark")  # Search for orgs with "shark" in name
        organizations(123)      # Organization with ID 123
    """
    with session_scope() as session:
        if query is None:
            # Return all organizations
            result = session.query(Organization).order_by(
                Organization.display_name
            ).all()
        elif isinstance(query, int):
            # Query by ID
            result = session.query(Organization).filter(Organization.id == query).first()
        elif isinstance(query, str):
            # Search by name
            search_pattern = f'%{query}%'
            result = session.query(Organization).filter(
                func.lower(Organization.display_name).like(search_pattern.lower())
            ).all()
        
        # Create detached copies with all attributes loaded
        detached_results = []
        if isinstance(result, list):
            for o in result:
                # Create a simple object with the needed attributes
                org_data = type('Organization', (), {
                    'id': o.id,
                    'display_name': o.display_name,
                    'contacts': o.contacts,
                    '__tablename__': 'organizations'
                })()
                detached_results.append(org_data)
            return OrganizationWrapper(detached_results)
        elif result:
            # Create a simple object with the needed attributes
            org_data = type('Organization', (), {
                'id': result.id,
                'display_name': result.display_name,
                'contacts': result.contacts,
                '__tablename__': 'organizations'
            })()
            return OrganizationWrapper(org_data)
        else:
            return OrganizationWrapper([])


# Aliases for convenience
p = players
t = tournaments
o = organizations


if __name__ == "__main__":
    # Test the wrapper system
    print("Testing Query Wrapper System")
    print("=" * 50)
    
    # Test player queries
    print("\n1. Testing players('west'):")
    west = players("west")
    if west:
        print(west.display())
        
        print("\n2. West's tournament count:")
        west_tournaments = west.tournaments()
        print(f"   {west_tournaments.count()} tournaments")
        
        print("\n3. West's wins:")
        west_wins = west.wins()
        print(f"   {west_wins.count()} wins")
        
        print("\n4. West's stats:")
        stats = west.stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print("   Player 'west' not found")
    
    # Test tournament queries
    print("\n5. Recent tournaments:")
    recent = tournaments("recent")
    print(f"   Found {recent.count()} recent tournaments")
    if recent:
        print("\n6. Players from recent tournaments:")
        recent_players = recent.players()
        print(f"   {recent_players.count()} unique players")
    
    # Test chaining
    print("\n7. Top 10 players' recent tournaments:")
    top_players = players("top 10")
    if top_players:
        their_recent = top_players.recent(30).tournaments().recent(30)
        print(f"   {their_recent.count()} recent tournaments from top 10 players")
    
    print("\n8. Testing organization queries:")
    shark = organizations("shark")
    if shark:
        print(shark.display())
        shark_tournaments = shark.tournaments()
        print(f"   Runs {shark_tournaments.count()} tournaments")