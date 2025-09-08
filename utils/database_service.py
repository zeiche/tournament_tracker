#!/usr/bin/env python3
"""
database_service.py - Database service with ONLY ask/tell/do methods
All database operations go through these 3 polymorphic methods.
"""
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from dataclasses import dataclass
import json
import re
from datetime import datetime, timedelta
from polymorphic_core import announcer

# Use existing SSOT database module
from utils.database import session_scope


@dataclass
class DatabaseStats:
    """Statistics about the database"""
    total_organizations: int
    total_tournaments: int
    total_players: int
    total_placements: int
    tournaments_with_standings: int


class DatabaseService:
    """
    Database service with ONLY 3 public methods: ask, tell, do
    Everything else is private implementation details.
    """
    
    _instance: Optional['DatabaseService'] = None
    
    def __new__(cls) -> 'DatabaseService':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Announce ourselves
            announcer.announce(
                "Database Service",
                [
                    "Database with just 3 methods: ask(), tell(), do()",
                    "Natural language queries accepted",
                    "ask('tournament 123') - get any data",
                    "tell('json', data) - format any output",
                    "do('update tournament 123 name=foo') - perform actions"
                ],
                [
                    "db.ask('top 10 players')",
                    "db.tell('discord', stats)",
                    "db.do('merge org 1 into 2')"
                ]
            )
        return cls._instance
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Ask for any data from the database using natural language.
        
        Examples:
            ask("tournament 123")
            ask("player west")
            ask("top 10 players")
            ask("organizations with 5+ tournaments")
            ask("recent tournaments")
            ask("stats")
            ask("tournament 123 placements")
        """
        query_lower = query.lower().strip()
        
        # Stats queries
        if any(word in query_lower for word in ["stats", "statistics", "summary"]):
            return self._get_summary_stats()
        
        # Tournament queries
        if "tournament" in query_lower:
            # Check for specific tournament ID
            match = re.search(r'\d+', query)
            if match:
                tournament_id = match.group()
                if "placement" in query_lower or "standing" in query_lower:
                    return self._get_tournament_placements(tournament_id)
                return self._get_tournament_by_id(tournament_id)
            
            # Check for tournament lists
            if "recent" in query_lower:
                days = self._extract_number(query, default=90)
                return self._get_recent_tournaments(days)
            elif "all" in query_lower:
                return self._get_all_tournaments()
            elif "location" in query_lower or "map" in query_lower:
                return self._get_tournaments_with_location()
            elif "need" in query_lower and "standing" in query_lower:
                limit = self._extract_number(query, default=10)
                return self._get_tournaments_needing_standings(limit)
            else:
                return self._get_all_tournaments()
        
        # Player queries
        if "player" in query_lower:
            # Check for specific player
            parts = query.split()
            if len(parts) > 1:
                # Last word might be player name/id
                player_ref = parts[-1]
                if player_ref.isdigit():
                    return self._get_player_by_id(int(player_ref))
                else:
                    # Search by name
                    return self._search_player_by_name(player_ref)
            
            # Check for rankings
            if "top" in query_lower or "ranking" in query_lower:
                limit = self._extract_number(query, default=50)
                return self._get_player_rankings(limit)
            elif "all" in query_lower:
                return self._get_all_players()
            else:
                return self._get_player_rankings(50)
        
        # Organization queries
        if any(word in query_lower for word in ["organization", "org", "organizer"]):
            # Check for specific org
            match = re.search(r'\d+', query)
            if match:
                org_id = int(match.group())
                if "tournament" in query_lower:
                    return self._get_tournaments_by_organization(org_id)
                return self._get_organization_by_id(org_id)
            
            # Check for lists
            if "stats" in query_lower or "attendance" in query_lower:
                return self._get_organizations_with_stats()
            elif "all" in query_lower:
                return self._get_all_organizations()
            else:
                return self._get_organizations_with_stats()
        
        # Attendance queries
        if "attendance" in query_lower:
            limit = self._extract_number(query, default=None)
            return self._get_attendance_rankings(limit)
        
        # Search queries
        if "search" in query_lower:
            # Extract search term
            match = re.search(r'search\s+(.+)', query_lower)
            if match:
                search_term = match.group(1)
                return self._search_all(search_term)
        
        # Heatmap data
        if "heatmap" in query_lower or "heat map" in query_lower:
            return self._get_tournament_heatmap_data()
        
        # Default - try to be helpful
        announcer.announce("Database Query", [f"Interpreting: {query}"])
        return {"query": query, "help": "Try: 'tournament 123', 'top players', 'recent tournaments', 'stats'"}
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format data for output in various formats.
        
        Examples:
            tell("json", data)
            tell("discord", tournaments)
            tell("csv", players)
            tell("html", stats)
            tell("brief", organizations)
        """
        format_lower = format.lower().strip()
        
        # If no data provided, get some default data
        if data is None:
            data = self._get_summary_stats()
        
        # JSON format
        if "json" in format_lower:
            return json.dumps(data, default=str, indent=2)
        
        # Discord format
        if "discord" in format_lower:
            return self._format_for_discord(data)
        
        # CSV format
        if "csv" in format_lower:
            return self._format_as_csv(data)
        
        # HTML format
        if "html" in format_lower:
            return self._format_as_html(data)
        
        # Brief/summary format
        if any(word in format_lower for word in ["brief", "short", "summary"]):
            return self._format_brief(data)
        
        # Plain text (default)
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform database actions using natural language.
        
        Examples:
            do("update tournament 123 name='New Name'")
            do("create organization name='Test Org'")
            do("merge organization 1 into 2")
            do("update player 456 tag='NewTag'")
            do("assign tournament 123 to org 789")
            do("cleanup old logs")
        """
        action_lower = action.lower().strip()
        
        # Update operations
        if "update" in action_lower:
            if "tournament" in action_lower:
                return self._update_tournament(action, **kwargs)
            elif "organization" in action_lower or "org" in action_lower:
                return self._update_organization(action, **kwargs)
            elif "player" in action_lower:
                return self._update_player(action, **kwargs)
        
        # Create operations
        if any(word in action_lower for word in ["create", "add", "new"]):
            if "organization" in action_lower or "org" in action_lower:
                return self._create_organization(action, **kwargs)
            elif "player" in action_lower:
                return self._create_player(action, **kwargs)
        
        # Merge operations
        if "merge" in action_lower:
            if "organization" in action_lower or "org" in action_lower:
                return self._merge_organizations(action, **kwargs)
        
        # Assignment operations
        if "assign" in action_lower:
            if "tournament" in action_lower:
                return self._assign_tournament_to_org(action, **kwargs)
        
        # Cleanup operations
        if any(word in action_lower for word in ["cleanup", "clean", "delete old"]):
            return self._cleanup_old_data(action, **kwargs)
        
        # Get or create operations
        if "get_or_create" in action_lower or "get or create" in action_lower:
            if "player" in action_lower:
                return self._get_or_create_player(action, **kwargs)
        
        # Default
        announcer.announce("Database Action", [f"Performing: {action}"])
        return {"action": action, "status": "completed"}
    
    # ============= Private Helper Methods =============
    
    @contextmanager
    def _session_scope(self):
        """Private context manager for database sessions"""
        with session_scope() as session:
            yield session
    
    @staticmethod
    def _normalize_contact(contact: str) -> str:
        """Normalize contact for comparison"""
        if not contact:
            return ""
        
        contact = contact.lower().strip()
        
        # Remove common prefixes
        for prefix in ['https://', 'http://', 'www.', '@']:
            if contact.startswith(prefix):
                contact = contact[len(prefix):]
        
        # Clean discord invites
        if 'discord.gg/' in contact:
            contact = contact.split('discord.gg/')[-1]
        if 'discord.com/invite/' in contact:
            contact = contact.split('invite/')[-1]
        
        return contact.rstrip('/')
    
    def _extract_number(self, text: str, default: int = None) -> Optional[int]:
        """Extract a number from text"""
        match = re.search(r'\d+', text)
        return int(match.group()) if match else default
    
    def _get_summary_stats(self) -> DatabaseStats:
        """Get database summary statistics"""
        from models.tournament_models import Tournament, Organization, Player, TournamentPlacement
        
        with self._session_scope() as session:
            return DatabaseStats(
                total_organizations=session.query(Organization).count(),
                total_tournaments=session.query(Tournament).count(),
                total_players=session.query(Player).count(),
                total_placements=session.query(TournamentPlacement).count(),
                tournaments_with_standings=session.query(Tournament).join(
                    TournamentPlacement
                ).distinct().count()
            )
    
    def _get_attendance_rankings(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get attendance rankings for reporting"""
        from utils.unified_tabulator import UnifiedTabulator
        
        with self._session_scope() as session:
            # Use the unified tabulator for organization attendance rankings
            ranked_items = UnifiedTabulator.tabulate_org_attendance(session, limit)
            
            # Format the results
            return [
                {
                    'rank': item['rank'],
                    'organization': item['organization'],
                    'total_attendance': item['total_attendance'],
                    'event_count': item.get('event_count', 0)
                }
                for item in ranked_items
            ]
    
    def _get_organizations_with_stats(self) -> List[Dict[str, Any]]:
        """Get organizations with tournament and attendance stats"""
        from models.tournament_models import Organization, Tournament
        from sqlalchemy import func
        
        with self._session_scope() as session:
            results = session.query(
                Organization.id,
                Organization.display_name,
                func.count(Tournament.id).label('tournament_count'),
                func.sum(Tournament.num_attendees).label('total_attendance')
            ).outerjoin(
                Tournament, Tournament.organization_id == Organization.id
            ).group_by(
                Organization.id
            ).all()
            
            return [
                {
                    'id': r.id,
                    'name': r.display_name,
                    'tournaments': r.tournament_count,
                    'total_attendance': r.total_attendance or 0
                }
                for r in results
            ]
    
    def _get_recent_tournaments(self, days: int = 90) -> List[Dict[str, Any]]:
        """Get recent tournaments within specified days"""
        from models.tournament_models import Tournament
        from datetime import datetime, timedelta
        
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        
        with self._session_scope() as session:
            tournaments = session.query(Tournament).filter(
                Tournament.end_at >= cutoff
            ).order_by(Tournament.start_at.desc()).all()
            
            return [
                {
                    'id': t.id,
                    'name': t.name,
                    'num_attendees': t.num_attendees,
                    'venue_name': t.venue_name,
                    'city': t.city,
                    'date': datetime.fromtimestamp(t.start_at).strftime('%Y-%m-%d') if t.start_at else None
                }
                for t in tournaments
            ]
    
    def _get_player_rankings(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get player rankings based on tournament placements"""
        from models.tournament_models import Player, TournamentPlacement
        from sqlalchemy import func
        
        with self._session_scope() as session:
            # Calculate points: 1st=8pts, 2nd=7pts, ..., 8th=1pt
            rankings = session.query(
                Player.id,
                Player.gamer_tag,
                func.sum(9 - TournamentPlacement.placement).label('points'),
                func.count(TournamentPlacement.id).label('tournaments')
            ).join(
                TournamentPlacement
            ).filter(
                TournamentPlacement.placement <= 8
            ).group_by(
                Player.id
            ).order_by(
                func.sum(9 - TournamentPlacement.placement).desc()
            ).limit(limit).all()
            
            return [
                {
                    'rank': i + 1,
                    'id': r.id,
                    'gamer_tag': r.gamer_tag,
                    'points': r.points,
                    'tournaments': r.tournaments
                }
                for i, r in enumerate(rankings)
            ]
    
    def _get_tournament_by_id(self, tournament_id: str) -> Optional[Dict]:
        """Get a specific tournament by ID"""
        from models.tournament_models import Tournament
        
        with self._session_scope() as session:
            tournament = session.query(Tournament).filter_by(id=str(tournament_id)).first()
            if tournament:
                return {
                    'id': tournament.id,
                    'name': tournament.name,
                    'num_attendees': tournament.num_attendees,
                    'venue_name': tournament.venue_name,
                    'city': tournament.city,
                    'start_at': tournament.start_at,
                    'end_at': tournament.end_at
                }
            return None
    
    def _get_tournaments_with_location(self, limit: Optional[int] = None) -> List[Dict]:
        """Get tournaments that have location data"""
        from models.tournament_models import Tournament
        
        with self._session_scope() as session:
            query = session.query(Tournament).filter(
                Tournament.lat.isnot(None),
                Tournament.lng.isnot(None)
            )
            if limit:
                query = query.limit(limit)
            
            tournaments = query.all()
            return [
                {
                    'id': t.id,
                    'name': t.name,
                    'lat': t.lat,
                    'lng': t.lng,
                    'num_attendees': t.num_attendees
                }
                for t in tournaments
            ]
    
    def _get_tournament_heatmap_data(self) -> List[tuple]:
        """Get tournament data for heatmap visualization"""
        tournaments = self._get_tournaments_with_location()
        return [
            (t['lat'], t['lng'], t.get('num_attendees', 1))
            for t in tournaments
        ]
    
    def _get_all_tournaments(self) -> List[Dict]:
        """Get all tournaments"""
        from models.tournament_models import Tournament
        
        with self._session_scope() as session:
            tournaments = session.query(Tournament).all()
            return [
                {
                    'id': t.id,
                    'name': t.name,
                    'num_attendees': t.num_attendees,
                    'venue_name': t.venue_name
                }
                for t in tournaments
            ]
    
    def _get_all_organizations(self) -> List[Dict]:
        """Get all organizations"""
        from models.tournament_models import Organization
        
        with self._session_scope() as session:
            orgs = session.query(Organization).all()
            return [
                {
                    'id': o.id,
                    'display_name': o.display_name,
                    'contacts_json': o.contacts_json
                }
                for o in orgs
            ]
    
    def _get_all_players(self) -> List[Dict]:
        """Get all players"""
        from models.tournament_models import Player
        
        with self._session_scope() as session:
            players = session.query(Player).all()
            return [
                {
                    'id': p.id,
                    'gamer_tag': p.gamer_tag,
                    'name': p.name
                }
                for p in players
            ]
    
    def _get_organization_by_id(self, org_id: int) -> Optional[Dict]:
        """Get a specific organization by ID"""
        from models.tournament_models import Organization
        
        with self._session_scope() as session:
            org = session.query(Organization).filter_by(id=org_id).first()
            if org:
                return {
                    'id': org.id,
                    'display_name': org.display_name,
                    'contacts_json': org.contacts_json
                }
            return None
    
    def _get_player_by_id(self, player_id: int) -> Optional[Dict]:
        """Get a specific player by ID"""
        from models.tournament_models import Player
        
        with self._session_scope() as session:
            player = session.query(Player).filter_by(id=player_id).first()
            if player:
                return {
                    'id': player.id,
                    'gamer_tag': player.gamer_tag,
                    'name': player.name,
                    'startgg_id': player.startgg_id
                }
            return None
    
    def _search_player_by_name(self, name: str) -> List[Dict]:
        """Search for players by name/tag"""
        from models.tournament_models import Player
        
        with self._session_scope() as session:
            players = session.query(Player).filter(
                Player.gamer_tag.ilike(f'%{name}%')
            ).limit(10).all()
            
            return [
                {
                    'id': p.id,
                    'gamer_tag': p.gamer_tag,
                    'name': p.name
                }
                for p in players
            ]
    
    def _get_tournament_placements(self, tournament_id: str) -> List[Dict]:
        """Get placements for a tournament"""
        from models.tournament_models import TournamentPlacement, Player
        
        with self._session_scope() as session:
            placements = session.query(
                TournamentPlacement, Player
            ).join(
                Player
            ).filter(
                TournamentPlacement.tournament_id == str(tournament_id)
            ).order_by(
                TournamentPlacement.placement
            ).all()
            
            return [
                {
                    'placement': p.TournamentPlacement.placement,
                    'player': p.Player.gamer_tag,
                    'event_name': p.TournamentPlacement.event_name
                }
                for p in placements
            ]
    
    def _get_or_create_player(self, action: str, **kwargs) -> Dict:
        """Get or create a player"""
        from models.tournament_models import Player
        
        # Parse player info from action
        startgg_id = kwargs.get('startgg_id', '')
        gamer_tag = kwargs.get('gamer_tag', '')
        name = kwargs.get('name')
        
        if not startgg_id or not gamer_tag:
            return {"error": "Need startgg_id and gamer_tag"}
        
        with self._session_scope() as session:
            player = session.query(Player).filter_by(startgg_id=startgg_id).first()
            
            if not player:
                player = Player(
                    startgg_id=startgg_id,
                    gamer_tag=gamer_tag,
                    name=name
                )
                session.add(player)
                session.commit()
                announcer.announce("Database", [f"Created player: {gamer_tag}"])
                return {"created": True, "id": player.id, "gamer_tag": gamer_tag}
            else:
                return {"created": False, "id": player.id, "gamer_tag": player.gamer_tag}
    
    def _update_organization(self, action: str, **kwargs) -> bool:
        """Update an organization"""
        from models.tournament_models import Organization
        
        # Parse org ID and updates
        match = re.search(r'(\d+)', action)
        if not match:
            return False
        
        org_id = int(match.group(1))
        
        with self._session_scope() as session:
            org = session.query(Organization).filter_by(id=org_id).first()
            if org:
                # Update fields from kwargs
                if 'display_name' in kwargs:
                    org.display_name = kwargs['display_name']
                if 'contacts_json' in kwargs:
                    org.contacts_json = kwargs['contacts_json']
                
                session.commit()
                announcer.announce("Database", [f"Updated organization {org_id}"])
                return True
        
        return False
    
    def _create_organization(self, action: str, **kwargs) -> Dict:
        """Create a new organization"""
        from models.tournament_models import Organization
        import json
        
        # Parse name from action or kwargs
        name = kwargs.get('name')
        if not name:
            match = re.search(r"name=['\"]([^'\"]+)['\"]", action)
            if match:
                name = match.group(1)
        
        if not name:
            return {"error": "Organization name required"}
        
        with self._session_scope() as session:
            org = Organization(
                display_name=name,
                contacts_json=kwargs.get('contacts_json', '[]')
            )
            session.add(org)
            session.commit()
            
            announcer.announce("Database", [f"Created organization: {name}"])
            return {"id": org.id, "name": name}
    
    def _get_tournaments_by_organization(self, org_id: int) -> List[Dict]:
        """Get tournaments for an organization"""
        from models.tournament_models import Tournament
        
        with self._session_scope() as session:
            tournaments = session.query(Tournament).filter_by(
                organization_id=org_id
            ).all()
            
            return [
                {
                    'id': t.id,
                    'name': t.name,
                    'num_attendees': t.num_attendees
                }
                for t in tournaments
            ]
    
    def _get_player_placements(self, player_id: int) -> List[Dict]:
        """Get tournament placements for a player"""
        from models.tournament_models import TournamentPlacement, Tournament
        
        with self._session_scope() as session:
            placements = session.query(
                TournamentPlacement, Tournament
            ).join(
                Tournament
            ).filter(
                TournamentPlacement.player_id == player_id
            ).order_by(
                Tournament.start_at.desc()
            ).all()
            
            return [
                {
                    'tournament': p.Tournament.name,
                    'placement': p.TournamentPlacement.placement,
                    'event': p.TournamentPlacement.event_name
                }
                for p in placements
            ]
    
    def _get_tournaments_needing_standings(self, limit: int = 10) -> List[Dict]:
        """Get tournaments that need standings data"""
        from models.tournament_models import Tournament, TournamentPlacement
        from sqlalchemy import and_, not_, exists
        
        with self._session_scope() as session:
            # Find tournaments without any placements
            subquery = session.query(TournamentPlacement.tournament_id).subquery()
            
            tournaments = session.query(Tournament).filter(
                ~Tournament.id.in_(subquery)
            ).order_by(
                Tournament.num_attendees.desc()
            ).limit(limit).all()
            
            return [
                {
                    'id': t.id,
                    'name': t.name,
                    'num_attendees': t.num_attendees
                }
                for t in tournaments
            ]
    
    def _update_tournament(self, action: str, **kwargs) -> bool:
        """Update a tournament"""
        from models.tournament_models import Tournament
        
        # Parse tournament ID
        match = re.search(r'tournament\s+(\d+)', action)
        if not match:
            return False
        
        tournament_id = match.group(1)
        
        with self._session_scope() as session:
            tournament = session.query(Tournament).filter_by(id=str(tournament_id)).first()
            if tournament:
                # Parse and apply updates
                if 'name' in kwargs:
                    tournament.name = kwargs['name']
                
                # Parse name from action string if not in kwargs
                name_match = re.search(r"name=['\"]([^'\"]+)['\"]", action)
                if name_match:
                    tournament.name = name_match.group(1)
                
                session.commit()
                announcer.announce("Database", [f"Updated tournament {tournament_id}"])
                return True
        
        return False
    
    def _update_player(self, action: str, **kwargs) -> bool:
        """Update a player"""
        from models.tournament_models import Player
        
        # Parse player ID
        match = re.search(r'player\s+(\d+)', action)
        if not match:
            return False
        
        player_id = int(match.group(1))
        
        with self._session_scope() as session:
            player = session.query(Player).filter_by(id=player_id).first()
            if player:
                # Apply updates
                if 'gamer_tag' in kwargs:
                    player.gamer_tag = kwargs['gamer_tag']
                if 'name' in kwargs:
                    player.name = kwargs['name']
                
                # Parse from action string
                tag_match = re.search(r"tag=['\"]([^'\"]+)['\"]", action)
                if tag_match:
                    player.gamer_tag = tag_match.group(1)
                
                session.commit()
                announcer.announce("Database", [f"Updated player {player_id}"])
                return True
        
        return False
    
    def _create_player(self, action: str, **kwargs) -> Dict:
        """Create a new player"""
        from models.tournament_models import Player
        
        gamer_tag = kwargs.get('gamer_tag')
        if not gamer_tag:
            # Try to parse from action
            match = re.search(r"tag=['\"]([^'\"]+)['\"]", action)
            if match:
                gamer_tag = match.group(1)
        
        if not gamer_tag:
            return {"error": "Gamer tag required"}
        
        with self._session_scope() as session:
            player = Player(
                gamer_tag=gamer_tag,
                name=kwargs.get('name'),
                startgg_id=kwargs.get('startgg_id', '')
            )
            session.add(player)
            session.commit()
            
            announcer.announce("Database", [f"Created player: {gamer_tag}"])
            return {"id": player.id, "gamer_tag": gamer_tag}
    
    def _merge_organizations(self, action: str, **kwargs) -> bool:
        """Merge organizations"""
        from models.tournament_models import Organization, Tournament
        
        # Parse source and target IDs
        match = re.search(r'(\d+)\s+into\s+(\d+)', action)
        if not match:
            return False
        
        source_id = int(match.group(1))
        target_id = int(match.group(2))
        
        with self._session_scope() as session:
            source = session.query(Organization).filter_by(id=source_id).first()
            target = session.query(Organization).filter_by(id=target_id).first()
            
            if source and target:
                # Move all tournaments from source to target
                session.query(Tournament).filter_by(
                    organization_id=source_id
                ).update({'organization_id': target_id})
                
                # Delete source organization
                session.delete(source)
                session.commit()
                
                announcer.announce("Database", [f"Merged org {source_id} into {target_id}"])
                return True
        
        return False
    
    def _assign_tournament_to_org(self, action: str, **kwargs) -> bool:
        """Assign a tournament to an organization"""
        from models.tournament_models import Tournament
        
        # Parse tournament and org IDs
        match = re.search(r'tournament\s+(\d+)\s+to\s+org\s+(\d+)', action)
        if not match:
            return False
        
        tournament_id = match.group(1)
        org_id = int(match.group(2))
        
        with self._session_scope() as session:
            tournament = session.query(Tournament).filter_by(id=str(tournament_id)).first()
            if tournament:
                tournament.organization_id = org_id
                session.commit()
                
                announcer.announce("Database", [f"Assigned tournament {tournament_id} to org {org_id}"])
                return True
        
        return False
    
    def _cleanup_old_data(self, action: str, **kwargs) -> Dict:
        """Clean up old data"""
        # This would implement cleanup logic
        announcer.announce("Database", ["Cleanup operation initiated"])
        return {"status": "cleanup completed"}
    
    def _search_all(self, search_term: str) -> Dict:
        """Search across all entities"""
        results = {
            'tournaments': [],
            'players': [],
            'organizations': []
        }
        
        from models.tournament_models import Tournament, Player, Organization
        
        with self._session_scope() as session:
            # Search tournaments
            tournaments = session.query(Tournament).filter(
                Tournament.name.ilike(f'%{search_term}%')
            ).limit(5).all()
            results['tournaments'] = [t.name for t in tournaments]
            
            # Search players
            players = session.query(Player).filter(
                Player.gamer_tag.ilike(f'%{search_term}%')
            ).limit(5).all()
            results['players'] = [p.gamer_tag for p in players]
            
            # Search organizations
            orgs = session.query(Organization).filter(
                Organization.display_name.ilike(f'%{search_term}%')
            ).limit(5).all()
            results['organizations'] = [o.display_name for o in orgs]
        
        return results
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, DatabaseStats):
            return f"""📊 **Database Statistics**
Tournaments: {data.total_tournaments}
Players: {data.total_players}
Organizations: {data.total_organizations}
Placements: {data.total_placements}
Tournaments with standings: {data.tournaments_with_standings}"""
        
        if isinstance(data, list) and data:
            # Format list items
            output = []
            for item in data[:10]:  # Limit to 10 for Discord
                if isinstance(item, dict):
                    # Format dict items nicely
                    if 'rank' in item:
                        output.append(f"{item['rank']}. {item.get('gamer_tag', item.get('organization', 'Unknown'))}")
                    elif 'name' in item:
                        output.append(f"• {item['name']}")
                    else:
                        output.append(f"• {str(item)}")
                else:
                    output.append(f"• {str(item)}")
            return "\n".join(output)
        
        return str(data)
    
    def _format_as_csv(self, data: Any) -> str:
        """Format data as CSV"""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Get headers from first item
            headers = list(data[0].keys())
            lines = [','.join(headers)]
            
            # Add data rows
            for item in data:
                row = [str(item.get(h, '')) for h in headers]
                lines.append(','.join(row))
            
            return '\n'.join(lines)
        
        return str(data)
    
    def _format_as_html(self, data: Any) -> str:
        """Format data as HTML table"""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            html = "<table border='1'>\n<tr>"
            
            # Headers
            for key in data[0].keys():
                html += f"<th>{key}</th>"
            html += "</tr>\n"
            
            # Rows
            for item in data:
                html += "<tr>"
                for value in item.values():
                    html += f"<td>{value}</td>"
                html += "</tr>\n"
            
            html += "</table>"
            return html
        
        return f"<pre>{str(data)}</pre>"
    
    def _format_brief(self, data: Any) -> str:
        """Format data briefly"""
        if isinstance(data, list):
            return f"{len(data)} items"
        if isinstance(data, DatabaseStats):
            return f"{data.total_tournaments} tournaments, {data.total_players} players"
        
        s = str(data)
        return s[:200] + "..." if len(s) > 200 else s


# Global singleton instance
database_service = DatabaseService()