#!/usr/bin/env python3
"""
polymorphic_queries.py - Polymorphic Query Interface

This module provides a clean, polymorphic way to query the database.
Everything accepts anything and figures out what to do.
"""
from typing import Any, List, Optional, Union
from sqlalchemy import func, case, desc, and_
from sqlalchemy.orm import Session
from database import session_scope
from tournament_models import Player, Tournament, Organization, TournamentPlacement
from formatters import PlayerFormatter, TournamentFormatter
from points_system import PointsSystem


class PolymorphicQuery:
    """Universal query interface - accepts anything"""
    
    @classmethod
    def find_players(cls, input_data: Any, session: Session) -> List[Player]:
        """
        Find players based on polymorphic input
        
        Examples:
            find_players("west")          # Name search
            find_players("top 8")         # Top 8 by points
            find_players({"limit": 10})   # Top 10
            find_players(5)               # Player with ID 5 or top 5
        """
        if isinstance(input_data, str):
            input_lower = input_data.lower()
            
            # Check for "top X" pattern
            if "top" in input_lower:
                # Extract number from string like "top 8" or "top 50"
                import re
                numbers = re.findall(r'\d+', input_data)
                limit = int(numbers[0]) if numbers else 8
                return cls._get_top_players(session, limit)
            
            # Otherwise, search by name
            else:
                return cls._search_players_by_name(session, input_data)
        
        elif isinstance(input_data, int):
            # Could be ID or limit for top players
            if input_data > 100:
                # Probably an ID
                player = session.query(Player).filter_by(id=input_data).first()
                return [player] if player else []
            else:
                # Probably a limit
                return cls._get_top_players(session, input_data)
        
        elif isinstance(input_data, dict):
            # Complex query with filters
            limit = input_data.get('limit', 10)
            event = input_data.get('event')
            return cls._get_top_players(session, limit, event)
        
        elif isinstance(input_data, list):
            # Multiple searches
            results = []
            for item in input_data:
                results.extend(cls.find_players(item, session))
            return results
        
        else:
            # Default: return top 10
            return cls._get_top_players(session, 10)
    
    @classmethod
    def _search_players_by_name(cls, session: Session, name: str) -> List[Player]:
        """Search for players by name (case-insensitive, fuzzy)"""
        search_pattern = f'%{name}%'
        players = session.query(Player).filter(
            func.lower(Player.gamer_tag).like(search_pattern.lower())
        ).limit(10).all()
        
        # If no results, try display_name
        if not players:
            players = session.query(Player).filter(
                func.lower(Player.display_name).like(search_pattern.lower())
            ).limit(10).all()
        
        return players
    
    @classmethod
    def _get_top_players(cls, session: Session, limit: int = 8, event: Optional[str] = None) -> List[Player]:
        """Get top players by points with calculated stats"""
        # Use the centralized points system
        points_case = PointsSystem.get_sql_case_expression()
        
        query = session.query(
            Player,
            func.sum(points_case).label('total_points'),
            func.count(TournamentPlacement.id).label('tournament_count')
        ).join(TournamentPlacement).group_by(Player.id)
        
        # Filter by event if specified
        if event:
            query = query.filter(TournamentPlacement.event_name.ilike(f'%{event}%'))
        
        query = query.order_by(desc('total_points')).limit(limit)
        results = query.all()
        
        # Attach calculated stats to player objects for easy access
        players_with_stats = []
        for player, points, events in results:
            player._total_points = int(points or 0)
            player._tournament_count = events
            players_with_stats.append(player)
        
        return players_with_stats
    
    @classmethod
    def find_tournaments(cls, input_data: Any, session: Session) -> List[Tournament]:
        """
        Find tournaments based on polymorphic input
        
        Examples:
            find_tournaments("recent")           # Recent tournaments
            find_tournaments("tuesday")          # Tuesday tournaments
            find_tournaments({"year": 2025})    # 2025 tournaments
            find_tournaments("large")            # High attendance
        """
        if isinstance(input_data, str):
            input_lower = input_data.lower()
            
            if "recent" in input_lower:
                return session.query(Tournament)\
                    .order_by(desc(Tournament.start_date))\
                    .limit(10).all()
            
            elif "upcoming" in input_lower:
                from datetime import datetime
                return session.query(Tournament)\
                    .filter(Tournament.start_date > datetime.now())\
                    .order_by(Tournament.start_date)\
                    .limit(10).all()
            
            elif "large" in input_lower or "big" in input_lower:
                return session.query(Tournament)\
                    .filter(Tournament.num_attendees > 50)\
                    .order_by(desc(Tournament.num_attendees))\
                    .limit(10).all()
            
            else:
                # Search by name
                return session.query(Tournament)\
                    .filter(func.lower(Tournament.name).like(f'%{input_data}%'))\
                    .limit(10).all()
        
        elif isinstance(input_data, dict):
            query = session.query(Tournament)
            
            if 'year' in input_data:
                from datetime import datetime
                year = input_data['year']
                start = datetime(year, 1, 1)
                end = datetime(year, 12, 31, 23, 59, 59)
                query = query.filter(and_(
                    Tournament.start_date >= start,
                    Tournament.start_date <= end
                ))
            
            if 'limit' in input_data:
                query = query.limit(input_data['limit'])
            else:
                query = query.limit(10)
            
            return query.all()
        
        else:
            # Default: recent tournaments
            return session.query(Tournament)\
                .order_by(desc(Tournament.start_date))\
                .limit(10).all()
    
    @classmethod
    def find_organizations(cls, input_data: Any, session: Session) -> List[Organization]:
        """
        Find organizations based on polymorphic input
        
        Examples:
            find_organizations("top")          # Top orgs by tournament count
            find_organizations("TNS")          # Search by name
        """
        if isinstance(input_data, str):
            input_lower = input_data.lower()
            
            if "top" in input_lower:
                # Get top organizations by tournament count
                import re
                numbers = re.findall(r'\d+', input_data)
                limit = int(numbers[0]) if numbers else 8
                
                query = session.query(
                    Organization,
                    func.count(Tournament.id).label('tournament_count')
                ).join(
                    Tournament,
                    Tournament.organization_id == Organization.id
                ).group_by(Organization.id)\
                 .order_by(desc('tournament_count'))\
                 .limit(limit)
                
                results = query.all()
                orgs = []
                for org, count in results:
                    org._tournament_count = count
                    orgs.append(org)
                return orgs
            
            else:
                # Search by name
                return session.query(Organization)\
                    .filter(func.lower(Organization.name).like(f'%{input_data}%'))\
                    .limit(10).all()
        
        else:
            # Default: all organizations
            return session.query(Organization).limit(20).all()


# Convenience functions for direct use
def find(entity_type: str, input_data: Any) -> Any:
    """
    Universal find function
    
    Usage:
        find("players", "west")
        find("tournaments", "recent")
        find("organizations", "top 5")
    """
    with session_scope() as session:
        if "player" in entity_type.lower():
            return PolymorphicQuery.find_players(input_data, session)
        elif "tournament" in entity_type.lower():
            return PolymorphicQuery.find_tournaments(input_data, session)
        elif "org" in entity_type.lower():
            return PolymorphicQuery.find_organizations(input_data, session)
        else:
            return None


def query(input_string: str) -> str:
    """
    Natural language query interface
    
    Usage:
        query("show top 8 players")
        query("find player west")
        query("recent tournaments")
    """
    with session_scope() as session:
        input_lower = input_string.lower()
        
        # Determine what to query
        if "player" in input_lower:
            # Check if it's asking for top players
            if "top" in input_lower:
                # It's a top X query - pass the full string
                players = PolymorphicQuery.find_players(input_string, session)
            else:
                # Extract the query part after "player"
                parts = input_lower.split("player", 1)
                if len(parts) > 1 and parts[1].strip():
                    search_term = parts[1].strip()
                    players = PolymorphicQuery.find_players(search_term, session)
                else:
                    # Default to top 8
                    players = PolymorphicQuery.find_players("top 8", session)
            
            if not players:
                return "No players found"
            
            # Format response
            if len(players) == 1:
                # Single player - formatted output
                p = players[0]
                points = getattr(p, '_total_points', 0)
                events = getattr(p, '_tournament_count', 0)
                
                output = f"**{p.gamer_tag}** - Player Profile\n"
                output += f"```\n"
                output += f"Total Points: {points}\n"
                output += f"Tournaments: {events}\n"
                output += f"```\n"
                
                # Get recent placements
                recent = session.query(
                    TournamentPlacement, Tournament
                ).join(Tournament).filter(
                    TournamentPlacement.player_id == p.id
                ).limit(5).all()
                
                if recent:
                    output += "\n**Recent Results:**\n"
                    for tp, t in recent[:5]:
                        output += f"• {t.name}: Placement {tp.placement}\n"
                
                return output
            else:
                # Multiple players - simple list format
                output = f"**Found {len(players)} players:**\n"
                for i, p in enumerate(players[:10], 1):
                    points = getattr(p, '_total_points', 0)
                    events = getattr(p, '_tournament_count', 0)
                    output += f"{i}. **{p.gamer_tag}** - {points} points ({events} events)\n"
                return output
        
        elif "tournament" in input_lower:
            tournaments = PolymorphicQuery.find_tournaments("recent", session)
            
            if not tournaments:
                return "No tournaments found"
            
            output = "**Recent Tournaments:**\n"
            for t in tournaments[:10]:
                if t.start_date:
                    date_str = t.start_date.strftime('%Y-%m-%d')
                    output += f"- {t.name} ({date_str})\n"
                else:
                    output += f"- {t.name}\n"
            return output
        
        elif "org" in input_lower:
            orgs = PolymorphicQuery.find_organizations("top", session)
            
            if not orgs:
                return "No organizations found"
            
            output = "**Top Organizations:**\n"
            for i, org in enumerate(orgs[:10], 1):
                count = getattr(org, '_tournament_count', 0)
                output += f"{i}. {org.name} ({count} tournaments)\n"
            return output
        
        else:
            return "I'm not sure what you're looking for. Try 'show players', 'show tournaments', or 'show organizations'."


if __name__ == "__main__":
    # Test the polymorphic queries
    print("Testing polymorphic queries...")
    
    # Test player queries
    print("\n1. Testing 'top 5':")
    print(query("show top 5 players"))
    
    print("\n2. Testing 'player west':")
    print(query("show player west"))
    
    print("\n3. Testing 'recent tournaments':")
    print(query("recent tournaments"))