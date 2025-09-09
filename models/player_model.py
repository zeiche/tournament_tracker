#!/usr/bin/env python3
"""
player_model.py - Player model with polymorphic pattern

Instead of dozens of player methods, just ask/tell/do!
"""

from typing import Any, Optional, List
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship, Session
import sys
sys.path.append('..')
from universal_polymorphic import PolymorphicModel
from models.mixins import TimestampMixin
from polymorphic_core import announcer


class Player(PolymorphicModel, TimestampMixin):
    """Player model - now polymorphic!"""
    
    __tablename__ = 'players'
    
    # Basic fields
    id = Column(Integer, primary_key=True)
    startgg_id = Column(Integer, unique=True, index=True)
    gamer_tag = Column(String, nullable=False, index=True)
    name = Column(String)
    state = Column(String)
    country = Column(String)
    main_character = Column(String)
    twitter = Column(String)
    twitch = Column(String)
    
    # Statistics (calculated)
    total_points = Column(Float, default=0.0)
    tournaments_entered = Column(Integer, default=0)
    first_places = Column(Integer, default=0)
    top_8s = Column(Integer, default=0)
    
    # Relationships
    placements = relationship("TournamentPlacement", back_populates="player")
    
    def _handle_ask(self, question: str, **kwargs) -> Any:
        """
        Handle player-specific questions.
        
        Examples:
            player.ask("points")            # Total points
            player.ask("wins")              # First place finishes
            player.ask("win rate")          # Win percentage
            player.ask("tournaments")       # Tournaments entered
            player.ask("main")              # Main character
            player.ask("recent")            # Recent tournaments
        """
        q = str(question).lower()
        session = kwargs.get('session')
        
        # Check mixins first
        timestamp_answer = self.ask_timestamp(question)
        if timestamp_answer is not None:
            return timestamp_answer
        
        # Player-specific questions
        if any(word in q for word in ['points', 'score', 'ranking']):
            return self.total_points or 0.0
        
        if any(word in q for word in ['wins', 'first', 'victories', '1st']):
            return self.first_places or 0
        
        if any(word in q for word in ['win rate', 'percentage', 'success']):
            if self.tournaments_entered and self.tournaments_entered > 0:
                return (self.first_places / self.tournaments_entered) * 100
            return 0.0
        
        if any(word in q for word in ['tournaments', 'events', 'entered']):
            return self.tournaments_entered or 0
        
        if any(word in q for word in ['top 8', 'top8', 'placements']):
            return self.top_8s or 0
        
        if any(word in q for word in ['main', 'character', 'char']):
            return self.main_character or "Unknown"
        
        if any(word in q for word in ['twitter', 'social']):
            return self.twitter or "No Twitter"
        
        if any(word in q for word in ['twitch', 'stream']):
            return self.twitch or "No Twitch"
        
        if any(word in q for word in ['state', 'location', 'from']):
            if self.state and self.country:
                return f"{self.state}, {self.country}"
            return self.state or self.country or "Unknown"
        
        if 'recent' in q:
            return self._get_recent_tournaments(session)
        
        if any(word in q for word in ['consistency', 'reliable']):
            return self._calculate_consistency()
        
        if 'rivals' in q:
            return self._get_rivals(session)
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str, **kwargs) -> Any:
        """
        Format player data.
        
        Examples:
            player.tell("discord")          # Format for Discord
            player.tell("stats")            # Show statistics
            player.tell("profile")          # Full profile
        """
        if format == "discord":
            location = f"{self.state}, {self.country}" if self.state else self.country or "Unknown"
            return (f"**{self.gamer_tag}**\n"
                   f"📍 {location} | 🎮 {self.main_character or 'Unknown'}\n"
                   f"🏆 {self.total_points:.0f} pts | "
                   f"🥇 {self.first_places} wins | "
                   f"🎯 {self.tournaments_entered} events")
        
        if format == "stats":
            win_rate = (self.first_places / self.tournaments_entered * 100) if self.tournaments_entered else 0
            return (f"Stats for {self.gamer_tag}:\n"
                   f"Points: {self.total_points:.0f}\n"
                   f"Tournaments: {self.tournaments_entered}\n"
                   f"Wins: {self.first_places}\n"
                   f"Top 8s: {self.top_8s}\n"
                   f"Win Rate: {win_rate:.1f}%")
        
        if format == "profile":
            lines = [
                f"Player: {self.gamer_tag}",
                f"Real Name: {self.name or 'Unknown'}",
                f"Location: {self.state or 'Unknown'}, {self.country or 'Unknown'}",
                f"Main: {self.main_character or 'Unknown'}",
                f"Twitter: {self.twitter or 'None'}",
                f"Twitch: {self.twitch or 'None'}",
                f"Total Points: {self.total_points:.0f}",
                f"Tournaments: {self.tournaments_entered}",
                f"First Places: {self.first_places}"
            ]
            return "\n".join(lines)
        
        if format == "brief":
            return f"{self.gamer_tag} ({self.total_points:.0f} pts)"
        
        if format == "json":
            return {
                'id': self.id,
                'gamer_tag': self.gamer_tag,
                'name': self.name,
                'location': f"{self.state}, {self.country}" if self.state else self.country,
                'main': self.main_character,
                'points': self.total_points,
                'tournaments': self.tournaments_entered,
                'wins': self.first_places
            }
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs) -> Any:
        """
        Perform player actions.
        
        Examples:
            player.do("calculate points")   # Recalculate points
            player.do("update stats")       # Update statistics
            player.do("merge", other)       # Merge with another player
        """
        act = str(action).lower()
        session = kwargs.get('session')
        
        if any(word in act for word in ['calculate', 'recalc', 'compute']):
            return self._recalculate_points(session)
        
        if any(word in act for word in ['update', 'refresh']):
            return self._update_stats(session)
        
        if 'merge' in act:
            other = kwargs.get('other')
            if other:
                return self._merge_with(other, session)
            return "No other player provided"
        
        return super()._handle_do(action, **kwargs)
    
    def _get_recent_tournaments(self, session: Optional[Session]) -> List[str]:
        """Get recent tournaments"""
        if not self.placements:
            return []
        
        recent = sorted(self.placements, 
                       key=lambda p: p.tournament.start_date if p.tournament else None,
                       reverse=True)[:5]
        
        return [p.tournament.name for p in recent if p.tournament]
    
    def _calculate_consistency(self) -> float:
        """Calculate consistency score"""
        if not self.tournaments_entered:
            return 0.0
        
        # Simple consistency: ratio of top 8s to tournaments
        return (self.top_8s / self.tournaments_entered) * 100 if self.tournaments_entered else 0.0
    
    def _get_rivals(self, session: Optional[Session]) -> List[str]:
        """Get players often faced"""
        # Would need to analyze tournament brackets
        # Simplified for now
        return []
    
    def _recalculate_points(self, session: Optional[Session]) -> float:
        """Recalculate total points from placements"""
        if not self.placements:
            return 0.0
        
        total = 0.0
        for placement in self.placements:
            # Points based on placement and tournament size
            if placement.tournament:
                base_points = max(0, 100 - (placement.placement * 10))
                size_multiplier = (placement.tournament.num_attendees / 50) if placement.tournament.num_attendees else 1
                total += base_points * size_multiplier
        
        self.total_points = total
        return total
    
    def _update_stats(self, session: Optional[Session]) -> bool:
        """Update player statistics"""
        if not self.placements:
            return False
        
        self.tournaments_entered = len(self.placements)
        self.first_places = sum(1 for p in self.placements if p.placement == 1)
        self.top_8s = sum(1 for p in self.placements if p.placement <= 8)
        
        if session:
            session.add(self)
            session.commit()
        
        return True
    
    def _merge_with(self, other: 'Player', session: Optional[Session]) -> bool:
        """Merge with another player record"""
        if not other or other.id == self.id:
            return False
        
        # Merge placements
        for placement in other.placements:
            placement.player_id = self.id
        
        # Merge stats
        self.total_points += other.total_points
        self.tournaments_entered += other.tournaments_entered
        self.first_places += other.first_places
        self.top_8s += other.top_8s
        
        # Keep better data
        self.name = self.name or other.name
        self.twitter = self.twitter or other.twitter
        self.twitch = self.twitch or other.twitch
        
        if session:
            session.delete(other)
            session.add(self)
            session.commit()
        
        return True
    
    def _get_capabilities(self) -> List[str]:
        """List player capabilities"""
        return [
            "ask('points')",
            "ask('wins')",
            "ask('win rate')",
            "ask('tournaments')",
            "ask('main')",
            "ask('recent')",
            "tell('discord')",
            "tell('stats')",
            "tell('profile')",
            "do('calculate points')",
            "do('update stats')"
        ]


# Announce Player Model Service
announcer.announce(
    "Player Model Service",
    [
        "Polymorphic player data model with ask/tell/do interface",
        "Player statistics and tournament performance tracking",
        "Win rate calculations and ranking analysis",
        "Character mains and social media integration",
        "Natural language player queries and updates",
        "Discord-friendly player profile formatting",
        "Automatic points calculation and statistics updates"
    ],
    examples=[
        "player.ask('points')",
        "player.ask('win rate')",
        "player.ask('recent tournaments')",
        "player.tell('discord', player_data)",
        "player.do('calculate points')"
    ]
)