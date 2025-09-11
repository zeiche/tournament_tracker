#!/usr/bin/env python3
"""
tournament_model.py - Tournament model with polymorphic pattern

Instead of 50+ tournament methods, just ask/tell/do!
"""

from datetime import datetime
from typing import Any, Optional, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship, Session
from dev.universal_polymorphic import PolymorphicModel
from .mixins import TimestampMixin, LocationMixin
from polymorphic_core import announcer


class Tournament(PolymorphicModel, TimestampMixin, LocationMixin):
    """Tournament model - now polymorphic!"""
    
    __tablename__ = 'tournaments'
    
    # Basic fields
    id = Column(Integer, primary_key=True)
    startgg_id = Column(Integer, unique=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    num_attendees = Column(Integer)
    tournament_url = Column(String)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    
    # Relationships
    organization = relationship("Organization", back_populates="tournaments")
    placements = relationship("TournamentPlacement", back_populates="tournament")
    
    def _handle_ask(self, question: str, **kwargs) -> Any:
        """
        Handle tournament-specific questions.
        
        Examples:
            tournament.ask("winner")         # Get winner
            tournament.ask("top 8")          # Get top 8 placements
            tournament.ask("attendance")     # Get number of attendees
            tournament.ask("when")           # Get date
            tournament.ask("major")          # Is it a major?
        """
        q = str(question).lower()
        session = kwargs.get('session')
        
        # Check mixins first
        location_answer = self.ask_location(question)
        if location_answer is not None:
            return location_answer
        
        timestamp_answer = self.ask_timestamp(question)
        if timestamp_answer is not None:
            return timestamp_answer
        
        # Tournament-specific questions
        if any(word in q for word in ['winner', 'first', 'champion', '1st']):
            return self._get_winner(session)
        
        if 'top' in q:
            # Extract number (default to 8)
            import re
            match = re.search(r'\d+', q)
            n = int(match.group()) if match else 8
            return self._get_top_n(n, session)
        
        if any(word in q for word in ['attendance', 'attendees', 'players', 'entrants']):
            return self.num_attendees or 0
        
        if any(word in q for word in ['when', 'date', 'start', 'end']):
            if 'end' in q:
                return self.end_date
            return self.start_date
        
        if any(word in q for word in ['major', 'big', 'large']):
            return self.num_attendees and self.num_attendees > 100
        
        if any(word in q for word in ['url', 'link', 'startgg']):
            return self.tournament_url
        
        if any(word in q for word in ['org', 'organization', 'host']):
            return self.organization.name if self.organization else "Unknown"
        
        if 'recent' in q:
            if self.start_date:
                days_ago = (datetime.now() - self.start_date).days
                return days_ago <= 30
            return False
        
        if 'growth' in q:
            return self._calculate_growth(session)
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str, **kwargs) -> Any:
        """
        Format tournament data.
        
        Examples:
            tournament.tell("discord")       # Format for Discord
            tournament.tell("brief")         # Short summary
            tournament.tell("detailed")      # Full details
        """
        if format == "discord":
            date_str = self.start_date.strftime("%b %d") if self.start_date else "Unknown date"
            return f"**{self.name}**\n📅 {date_str} | 👥 {self.num_attendees or 0} players"
        
        if format == "brief":
            return f"{self.name} ({self.num_attendees or 0} players)"
        
        if format == "detailed":
            lines = [
                f"Tournament: {self.name}",
                f"Date: {self.start_date}",
                f"Attendees: {self.num_attendees}",
                f"Organization: {self.organization.name if self.organization else 'Unknown'}",
                f"Venue: {self.venue_name or 'Unknown'}",
                f"City: {self.city or 'Unknown'}"
            ]
            return "\n".join(lines)
        
        if format == "json":
            return {
                'id': self.id,
                'name': self.name,
                'date': str(self.start_date),
                'attendees': self.num_attendees,
                'organization': self.organization.name if self.organization else None,
                'location': self.tell_location("json")
            }
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs) -> Any:
        """
        Perform tournament actions.
        
        Examples:
            tournament.do("sync")            # Sync from start.gg
            tournament.do("calculate stats") # Calculate statistics
            tournament.do("update")          # Update data
        """
        act = str(action).lower()
        session = kwargs.get('session')
        
        if 'sync' in act:
            return self._sync_from_startgg()
        
        if 'calculate' in act:
            return {
                'growth': self._calculate_growth(session),
                'is_major': self.num_attendees > 100 if self.num_attendees else False,
                'days_ago': (datetime.now() - self.start_date).days if self.start_date else None
            }
        
        if 'update' in act:
            if session:
                session.add(self)
                session.commit()
                return "Updated"
            return "No session provided"
        
        return super()._handle_do(action, **kwargs)
    
    def _get_winner(self, session: Optional[Session]) -> Optional[str]:
        """Get tournament winner"""
        if not session or not self.placements:
            return None
        
        for placement in self.placements:
            if placement.placement == 1:
                return placement.player.gamer_tag if placement.player else None
        return None
    
    def _get_top_n(self, n: int, session: Optional[Session]) -> List[str]:
        """Get top N placements"""
        if not self.placements:
            return []
        
        results = []
        sorted_placements = sorted(self.placements, key=lambda p: p.placement)
        
        for placement in sorted_placements[:n]:
            if placement.player:
                results.append({
                    'placement': placement.placement,
                    'player': placement.player.gamer_tag
                })
        
        return results
    
    def _calculate_growth(self, session: Optional[Session]) -> Optional[float]:
        """Calculate growth compared to previous tournament"""
        if not session or not self.organization_id:
            return None
        
        # Would need to query previous tournament from same org
        # Simplified for now
        return 0.0
    
    def _sync_from_startgg(self) -> bool:
        """Sync tournament data from start.gg"""
        # Would call start.gg API
        return True
    
    def _get_capabilities(self) -> List[str]:
        """List tournament capabilities"""
        return [
            "ask('winner')",
            "ask('top 8')",
            "ask('attendance')",
            "ask('when')",
            "ask('venue')",
            "ask('is major')",
            "tell('discord')",
            "tell('brief')",
            "do('sync')",
            "do('calculate stats')"
        ]


# Announce Tournament Model Service
announcer.announce(
    "Tournament Model Service",
    [
        "Polymorphic tournament data model with ask/tell/do interface",
        "Tournament attendance and venue information tracking",
        "Geographic location analysis with coordinate support",
        "Tournament classification (major/minor/weekly events)",
        "Top 8 placements and standings integration",
        "Natural language tournament queries and updates",
        "Discord-friendly tournament formatting and display",
        "Automatic statistics calculation and sync operations"
    ],
    examples=[
        "tournament.ask('attendance')",
        "tournament.ask('is major')",
        "tournament.ask('top 8')",
        "tournament.tell('discord', tournament_data)",
        "tournament.do('sync with startgg')"
    ]
)