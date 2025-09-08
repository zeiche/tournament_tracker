#!/usr/bin/env python3
"""
organization_model.py - Organization model with polymorphic pattern

Tournament organizers - now with just ask/tell/do!
"""

from typing import Any, Optional, List, Dict
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Session
import sys
sys.path.append('..')
from universal_polymorphic import PolymorphicModel
from models.mixins import TimestampMixin


class Organization(PolymorphicModel, TimestampMixin):
    """Organization model - now polymorphic!"""
    
    __tablename__ = 'organizations'
    
    # Basic fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    normalized_name = Column(String, index=True)
    website = Column(String)
    twitter = Column(String)
    discord = Column(String)
    email = Column(String)
    phone = Column(String)
    
    # Relationships
    tournaments = relationship("Tournament", back_populates="organization")
    contacts = relationship("OrganizationContact", back_populates="organization")
    
    def _handle_ask(self, question: str, **kwargs) -> Any:
        """
        Handle organization-specific questions.
        
        Examples:
            org.ask("tournaments")          # List tournaments
            org.ask("total attendance")     # Total attendance across all events
            org.ask("growth")              # Growth rate
            org.ask("contacts")            # Contact information
            org.ask("next event")          # Next scheduled tournament
        """
        q = str(question).lower()
        session = kwargs.get('session')
        
        # Check mixins first
        timestamp_answer = self.ask_timestamp(question)
        if timestamp_answer is not None:
            return timestamp_answer
        
        # Organization-specific questions
        if any(word in q for word in ['tournaments', 'events', 'count']):
            if 'count' in q or 'how many' in q:
                return len(self.tournaments) if self.tournaments else 0
            return [t.name for t in self.tournaments] if self.tournaments else []
        
        if any(word in q for word in ['attendance', 'total', 'players']):
            if self.tournaments:
                return sum(t.num_attendees or 0 for t in self.tournaments)
            return 0
        
        if any(word in q for word in ['average', 'avg', 'mean']):
            if self.tournaments:
                total = sum(t.num_attendees or 0 for t in self.tournaments)
                count = len(self.tournaments)
                return total / count if count > 0 else 0
            return 0
        
        if any(word in q for word in ['growth', 'trending', 'increase']):
            return self._calculate_growth()
        
        if any(word in q for word in ['contacts', 'contact', 'email', 'phone']):
            if 'email' in q:
                return self.email or "No email"
            if 'phone' in q:
                return self.phone or "No phone"
            if 'twitter' in q:
                return self.twitter or "No Twitter"
            if 'discord' in q:
                return self.discord or "No Discord"
            return self._get_all_contacts()
        
        if any(word in q for word in ['next', 'upcoming', 'future']):
            return self._get_next_tournament()
        
        if any(word in q for word in ['last', 'recent', 'previous']):
            return self._get_last_tournament()
        
        if any(word in q for word in ['venues', 'locations', 'cities']):
            return self._get_venues()
        
        if 'active' in q:
            # Active if had tournament in last 90 days
            if self.tournaments:
                from datetime import datetime, timedelta
                cutoff = datetime.now() - timedelta(days=90)
                return any(t.start_date and t.start_date > cutoff for t in self.tournaments)
            return False
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str, **kwargs) -> Any:
        """
        Format organization data.
        
        Examples:
            org.tell("discord")             # Format for Discord
            org.tell("summary")             # Organization summary
            org.tell("stats")               # Statistics
        """
        if format == "discord":
            total_attendance = sum(t.num_attendees or 0 for t in self.tournaments) if self.tournaments else 0
            event_count = len(self.tournaments) if self.tournaments else 0
            return (f"**{self.name}**\n"
                   f"📊 {event_count} events | 👥 {total_attendance} total attendance\n"
                   f"🌐 {self.website or 'No website'}")
        
        if format == "summary":
            lines = [
                f"Organization: {self.name}",
                f"Events: {len(self.tournaments) if self.tournaments else 0}",
                f"Total Attendance: {sum(t.num_attendees or 0 for t in self.tournaments) if self.tournaments else 0}",
                f"Website: {self.website or 'None'}",
                f"Twitter: {self.twitter or 'None'}",
                f"Discord: {self.discord or 'None'}"
            ]
            return "\n".join(lines)
        
        if format == "stats":
            if not self.tournaments:
                return f"{self.name}: No tournaments yet"
            
            total = sum(t.num_attendees or 0 for t in self.tournaments)
            avg = total / len(self.tournaments) if self.tournaments else 0
            growth = self._calculate_growth()
            
            return (f"{self.name} Statistics:\n"
                   f"Events: {len(self.tournaments)}\n"
                   f"Total Attendance: {total}\n"
                   f"Average: {avg:.0f}\n"
                   f"Growth: {growth:.1f}%" if growth else "Growth: N/A")
        
        if format == "brief":
            event_count = len(self.tournaments) if self.tournaments else 0
            return f"{self.name} ({event_count} events)"
        
        if format == "json":
            return {
                'id': self.id,
                'name': self.name,
                'tournaments': len(self.tournaments) if self.tournaments else 0,
                'total_attendance': sum(t.num_attendees or 0 for t in self.tournaments) if self.tournaments else 0,
                'website': self.website,
                'twitter': self.twitter,
                'discord': self.discord
            }
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs) -> Any:
        """
        Perform organization actions.
        
        Examples:
            org.do("add contact", type="email", value="...")
            org.do("merge", other=other_org)
            org.do("analyze")
        """
        act = str(action).lower()
        session = kwargs.get('session')
        
        if any(word in act for word in ['add', 'create']) and 'contact' in act:
            contact_type = kwargs.get('type')
            value = kwargs.get('value')
            if contact_type and value:
                return self._add_contact(contact_type, value, session)
            return "Need type and value for contact"
        
        if 'merge' in act:
            other = kwargs.get('other')
            if other:
                return self._merge_with(other, session)
            return "No other organization provided"
        
        if any(word in act for word in ['analyze', 'analysis']):
            return {
                'tournaments': len(self.tournaments) if self.tournaments else 0,
                'total_attendance': sum(t.num_attendees or 0 for t in self.tournaments) if self.tournaments else 0,
                'growth': self._calculate_growth(),
                'venues': self._get_venues(),
                'active': self.ask("active")
            }
        
        if 'normalize' in act:
            self.normalized_name = self.name.lower().replace(' ', '').replace('-', '')
            if session:
                session.add(self)
                session.commit()
            return "Normalized"
        
        return super()._handle_do(action, **kwargs)
    
    def _calculate_growth(self) -> Optional[float]:
        """Calculate growth rate"""
        if not self.tournaments or len(self.tournaments) < 2:
            return None
        
        # Sort by date
        sorted_tournaments = sorted(self.tournaments, 
                                  key=lambda t: t.start_date if t.start_date else None)
        
        # Compare last two tournaments
        if len(sorted_tournaments) >= 2:
            prev = sorted_tournaments[-2].num_attendees or 0
            curr = sorted_tournaments[-1].num_attendees or 0
            
            if prev > 0:
                return ((curr - prev) / prev) * 100
        
        return 0.0
    
    def _get_all_contacts(self) -> Dict[str, str]:
        """Get all contact information"""
        contacts = {}
        if self.email:
            contacts['email'] = self.email
        if self.phone:
            contacts['phone'] = self.phone
        if self.twitter:
            contacts['twitter'] = self.twitter
        if self.discord:
            contacts['discord'] = self.discord
        if self.website:
            contacts['website'] = self.website
        return contacts
    
    def _get_next_tournament(self) -> Optional[str]:
        """Get next upcoming tournament"""
        if not self.tournaments:
            return None
        
        from datetime import datetime
        now = datetime.now()
        
        future = [t for t in self.tournaments 
                 if t.start_date and t.start_date > now]
        
        if future:
            next_tournament = min(future, key=lambda t: t.start_date)
            return next_tournament.name
        
        return None
    
    def _get_last_tournament(self) -> Optional[str]:
        """Get most recent tournament"""
        if not self.tournaments:
            return None
        
        from datetime import datetime
        now = datetime.now()
        
        past = [t for t in self.tournaments 
               if t.start_date and t.start_date <= now]
        
        if past:
            last_tournament = max(past, key=lambda t: t.start_date)
            return last_tournament.name
        
        return None
    
    def _get_venues(self) -> List[str]:
        """Get all venues used"""
        if not self.tournaments:
            return []
        
        venues = set()
        for t in self.tournaments:
            if t.venue_name:
                venues.add(t.venue_name)
            elif t.city:
                venues.add(t.city)
        
        return list(venues)
    
    def _add_contact(self, contact_type: str, value: str, session: Optional[Session]) -> bool:
        """Add contact information"""
        if contact_type == "email":
            self.email = value
        elif contact_type == "phone":
            self.phone = value
        elif contact_type == "twitter":
            self.twitter = value
        elif contact_type == "discord":
            self.discord = value
        elif contact_type == "website":
            self.website = value
        else:
            return False
        
        if session:
            session.add(self)
            session.commit()
        
        return True
    
    def _merge_with(self, other: 'Organization', session: Optional[Session]) -> bool:
        """Merge with another organization"""
        if not other or other.id == self.id:
            return False
        
        # Move tournaments
        for tournament in other.tournaments:
            tournament.organization_id = self.id
        
        # Merge contacts (keep non-empty)
        self.email = self.email or other.email
        self.phone = self.phone or other.phone
        self.twitter = self.twitter or other.twitter
        self.discord = self.discord or other.discord
        self.website = self.website or other.website
        
        if session:
            session.delete(other)
            session.add(self)
            session.commit()
        
        return True
    
    def _get_capabilities(self) -> List[str]:
        """List organization capabilities"""
        return [
            "ask('tournaments')",
            "ask('total attendance')",
            "ask('growth')",
            "ask('contacts')",
            "ask('next event')",
            "ask('venues')",
            "tell('discord')",
            "tell('summary')",
            "tell('stats')",
            "do('add contact', type='...', value='...')",
            "do('merge', other=...)",
            "do('analyze')"
        ]