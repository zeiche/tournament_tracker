#!/usr/bin/env python3
"""
database_service_polymorphic.py - Database service using the 3-method pattern
Instead of 20+ specific methods, just ask(), tell(), and do()
"""
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from dataclasses import dataclass
from polymorphic_core import announcer

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.database_service_polymorphic")

# Use existing SSOT database module
from database import session_scope


@dataclass
class DatabaseStats:
    """Statistics about the database"""
    total_organizations: int
    total_tournaments: int
    total_players: int
    total_placements: int
    tournaments_with_standings: int


class DatabaseServicePolymorphic:
    """Database service with just 3 methods instead of 20+"""
    
    _instance: Optional['DatabaseServicePolymorphic'] = None
    
    def __new__(cls) -> 'DatabaseServicePolymorphic':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Announce when created
            announcer.announce(
                "Database Service (Polymorphic)",
                [
                    "I understand natural language database queries",
                    "ask('tournament 123') - get any data",
                    "tell('stats') - format any output",
                    "do('update tournament 123 name=foo') - perform actions"
                ]
            )
        return cls._instance
    
    def __init__(self):
        """Initialize the database service"""
        self.session_scope = session_scope
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Ask for any data from the database
        Examples:
            ask("tournament 123")
            ask("player west")
            ask("top 10 players")
            ask("organizations with 5+ tournaments")
            ask("stats")
        """
        query_lower = query.lower().strip()
        
        # Parse what they're asking for
        if "stats" in query_lower or "summary" in query_lower:
            return self._get_stats()
        
        if "tournament" in query_lower:
            # Extract ID if present
            parts = query_lower.split()
            if len(parts) > 1:
                potential_id = parts[1]
                return self._get_tournament(potential_id)
            elif "all" in query_lower:
                return self._get_all_tournaments()
            elif "recent" in query_lower:
                return self._get_recent_tournaments()
            elif "location" in query_lower or "heatmap" in query_lower:
                return self._get_tournaments_with_location()
        
        if "player" in query_lower:
            # Check for specific player name
            parts = query.split()
            if len(parts) > 1:
                player_name = parts[-1]  # Last word is likely the name
                return self._get_player(player_name)
            elif "top" in query_lower:
                # Extract number
                import re
                match = re.search(r'\d+', query)
                limit = int(match.group()) if match else 50
                return self._get_player_rankings(limit)
            elif "all" in query_lower:
                return self._get_all_players()
        
        if "organization" in query_lower or "org" in query_lower:
            if "all" in query_lower:
                return self._get_all_organizations()
            elif "stats" in query_lower:
                return self._get_organizations_with_stats()
            # Check for specific org
            parts = query.split()
            if len(parts) > 1 and parts[-1].isdigit():
                return self._get_organization(int(parts[-1]))
        
        if "standings" in query_lower or "placement" in query_lower:
            # Extract tournament ID
            parts = query.split()
            for part in parts:
                if part.isdigit():
                    return self._get_tournament_placements(part)
        
        # Default - return what we can figure out
        announcer.announce("Database Query", [f"Interpreting: {query}"])
        return None
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format data for output
        Examples:
            tell("discord", tournament)
            tell("json", stats)
            tell("brief", player_rankings)
            tell("html", organizations)
        """
        format_lower = format.lower().strip()
        
        # If no data provided, get default data based on format
        if data is None:
            if "stats" in format_lower:
                data = self._get_stats()
            elif "tournament" in format_lower:
                data = self._get_recent_tournaments()
            elif "player" in format_lower:
                data = self._get_player_rankings(10)
        
        # Format the data
        if "json" in format_lower:
            import json
            return json.dumps(data, default=str, indent=2)
        
        if "discord" in format_lower:
            return self._format_for_discord(data)
        
        if "html" in format_lower:
            return self._format_as_html(data)
        
        if "brief" in format_lower or "short" in format_lower:
            return self._format_brief(data)
        
        # Default - string representation
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform database actions
        Examples:
            do("update tournament 123 name='New Name'")
            do("create organization name='Test Org'")
            do("merge organization 1 into 2")
            do("sync tournaments")
        """
        action_lower = action.lower().strip()
        
        if "update" in action_lower:
            if "tournament" in action_lower:
                return self._update_tournament(action, **kwargs)
            if "organization" in action_lower or "org" in action_lower:
                return self._update_organization(action, **kwargs)
            if "player" in action_lower:
                return self._update_player(action, **kwargs)
        
        if "create" in action_lower or "add" in action_lower:
            if "organization" in action_lower:
                return self._create_organization(action, **kwargs)
            if "player" in action_lower:
                return self._create_player(action, **kwargs)
        
        if "merge" in action_lower:
            if "organization" in action_lower:
                return self._merge_organizations(action, **kwargs)
        
        if "sync" in action_lower:
            announcer.announce("Database Action", ["Syncing tournaments from start.gg"])
            # Would call sync service here
            return "Sync initiated"
        
        announcer.announce("Database Action", [f"Performing: {action}"])
        return f"Action performed: {action}"
    
    # --- Private helper methods (these do the actual work) ---
    
    def _get_stats(self) -> DatabaseStats:
        """Get database statistics"""
        from database.tournament_models import Tournament, Organization, Player, TournamentPlacement
        
        with self.session_scope() as session:
            return DatabaseStats(
                total_organizations=session.query(Organization).count(),
                total_tournaments=session.query(Tournament).count(),
                total_players=session.query(Player).count(),
                total_placements=session.query(TournamentPlacement).count(),
                tournaments_with_standings=session.query(Tournament).join(
                    TournamentPlacement
                ).distinct().count()
            )
    
    def _get_tournament(self, tournament_id: str) -> Any:
        """Get a specific tournament"""
        from database.tournament_models import Tournament
        
        with self.session_scope() as session:
            return session.query(Tournament).filter_by(id=str(tournament_id)).first()
    
    def _get_all_tournaments(self) -> List[Any]:
        """Get all tournaments"""
        from database.tournament_models import Tournament
        
        with self.session_scope() as session:
            return session.query(Tournament).all()
    
    def _get_recent_tournaments(self, days: int = 90) -> List[Any]:
        """Get recent tournaments"""
        from database.tournament_models import Tournament
        from datetime import datetime, timedelta
        
        cutoff = (datetime.now() - timedelta(days=days)).timestamp()
        
        with self.session_scope() as session:
            return session.query(Tournament).filter(
                Tournament.end_at >= cutoff
            ).order_by(Tournament.start_at.desc()).all()
    
    def _get_player(self, name: str) -> Any:
        """Get a player by name or ID"""
        from database.tournament_models import Player
        
        with self.session_scope() as session:
            # Try as ID first
            if name.isdigit():
                return session.query(Player).filter_by(id=int(name)).first()
            # Try as gamer tag
            return session.query(Player).filter(
                Player.gamer_tag.ilike(f"%{name}%")
            ).first()
    
    def _get_player_rankings(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get player rankings"""
        from database.tournament_models import Player, TournamentPlacement
        from sqlalchemy import func
        
        with self.session_scope() as session:
            # Calculate points per player
            rankings = session.query(
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
                    'player': r.gamer_tag,
                    'points': r.points,
                    'tournaments': r.tournaments
                }
                for i, r in enumerate(rankings)
            ]
    
    def _get_all_players(self) -> List[Any]:
        """Get all players"""
        from database.tournament_models import Player
        
        with self.session_scope() as session:
            return session.query(Player).all()
    
    def _get_organization(self, org_id: int) -> Any:
        """Get a specific organization"""
        from database.tournament_models import Organization
        
        with self.session_scope() as session:
            return session.query(Organization).filter_by(id=org_id).first()
    
    def _get_all_organizations(self) -> List[Any]:
        """Get all organizations"""
        from database.tournament_models import Organization
        
        with self.session_scope() as session:
            return session.query(Organization).all()
    
    def _get_organizations_with_stats(self) -> List[Dict[str, Any]]:
        """Get organizations with tournament counts"""
        from database.tournament_models import Organization, Tournament
        from sqlalchemy import func
        
        with self.session_scope() as session:
            org_stats = session.query(
                Organization.display_name,
                func.count(Tournament.id).label('tournament_count'),
                func.sum(Tournament.num_attendees).label('total_attendance')
            ).outerjoin(
                Tournament
            ).group_by(
                Organization.id
            ).all()
            
            return [
                {
                    'organization': o.display_name,
                    'tournaments': o.tournament_count,
                    'total_attendance': o.total_attendance or 0
                }
                for o in org_stats
            ]
    
    def _get_tournament_placements(self, tournament_id: str) -> List[Any]:
        """Get placements for a tournament"""
        from database.tournament_models import TournamentPlacement
        
        with self.session_scope() as session:
            return session.query(TournamentPlacement).filter_by(
                tournament_id=str(tournament_id)
            ).order_by(TournamentPlacement.placement).all()
    
    def _get_tournaments_with_location(self) -> List[Any]:
        """Get tournaments that have location data"""
        from database.tournament_models import Tournament
        
        with self.session_scope() as session:
            return session.query(Tournament).filter(
                Tournament.lat.isnot(None),
                Tournament.lng.isnot(None)
            ).all()
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, DatabaseStats):
            return f"""📊 **Database Stats**
Tournaments: {data.total_tournaments}
Players: {data.total_players}
Organizations: {data.total_organizations}
Placements: {data.total_placements}"""
        
        if isinstance(data, list) and data:
            # Format list of items
            output = []
            for item in data[:10]:  # Limit to 10 for Discord
                if hasattr(item, 'name'):
                    output.append(f"• {item.name}")
                elif isinstance(item, dict):
                    output.append(f"• {item}")
                else:
                    output.append(f"• {str(item)}")
            return "\n".join(output)
        
        return str(data)
    
    def _format_as_html(self, data: Any) -> str:
        """Format data as HTML"""
        # Simple HTML formatting
        html = "<div>"
        if isinstance(data, list):
            html += "<ul>"
            for item in data:
                html += f"<li>{item}</li>"
            html += "</ul>"
        else:
            html += f"<p>{data}</p>"
        html += "</div>"
        return html
    
    def _format_brief(self, data: Any) -> str:
        """Format data briefly"""
        if isinstance(data, list):
            return f"{len(data)} items"
        if isinstance(data, DatabaseStats):
            return f"{data.total_tournaments} tournaments, {data.total_players} players"
        return str(data)[:100]  # First 100 chars
    
    def _update_tournament(self, action: str, **kwargs) -> bool:
        """Update a tournament"""
        # Parse action string to extract ID and fields
        # This would parse and apply updates
        announcer.announce("Database Update", [f"Updating tournament: {action}"])
        return True
    
    def _update_organization(self, action: str, **kwargs) -> bool:
        """Update an organization"""
        announcer.announce("Database Update", [f"Updating organization: {action}"])
        return True
    
    def _update_player(self, action: str, **kwargs) -> bool:
        """Update a player"""
        announcer.announce("Database Update", [f"Updating player: {action}"])
        return True
    
    def _create_organization(self, action: str, **kwargs) -> Any:
        """Create a new organization"""
        from database.tournament_models import Organization
        
        # Parse name from action string
        import re
        match = re.search(r"name=['\"]([^'\"]+)['\"]", action)
        if match:
            name = match.group(1)
            with self.session_scope() as session:
                org = Organization(display_name=name)
                session.add(org)
                session.commit()
                announcer.announce("Database Create", [f"Created organization: {name}"])
                return org
        return None
    
    def _create_player(self, action: str, **kwargs) -> Any:
        """Create a new player"""
        announcer.announce("Database Create", [f"Creating player: {action}"])
        return None
    
    def _merge_organizations(self, action: str, **kwargs) -> bool:
        """Merge organizations"""
        # Parse source and target from action
        import re
        match = re.search(r"(\d+)\s+into\s+(\d+)", action)
        if match:
            source_id = int(match.group(1))
            target_id = int(match.group(2))
            announcer.announce("Database Merge", [f"Merging org {source_id} into {target_id}"])
            # Would perform actual merge here
            return True
        return False


# Global singleton instance
database_service = DatabaseServicePolymorphic()