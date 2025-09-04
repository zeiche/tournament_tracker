"""
tournament_models.py - SQLAlchemy Models for Tournament Tracker
Pure data models that use centralized session management from database_utils
"""
import re
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index, Float, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

# Import centralized session management
from database_utils import Session, get_session
from log_utils import log_debug, log_info, log_error

Base = declarative_base()

class LocationMixin:
    """Mixin for models that have geographic location data"""
    
    # Location columns (these will be inherited by models using this mixin)
    lat = Column(Float)  # Latitude as float for calculations
    lng = Column(Float)  # Longitude as float for calculations
    venue_name = Column(String)
    venue_address = Column(String)
    city = Column(String)
    addr_state = Column(String)  # State/province
    country_code = Column(String)
    postal_code = Column(String)
    
    @property
    def has_location(self) -> bool:
        """Check if this object has valid location data"""
        return self.lat is not None and self.lng is not None
    
    @property
    def coordinates(self) -> Optional[Tuple[float, float]]:
        """Get coordinates as a tuple (lat, lng)"""
        if self.has_location:
            try:
                return (float(self.lat), float(self.lng))
            except (ValueError, TypeError):
                return None
        return None
    
    @property
    def location_dict(self) -> Dict[str, Any]:
        """Get location data as a dictionary for JSON serialization"""
        return {
            'lat': self.lat,
            'lng': self.lng,
            'venue_name': self.venue_name,
            'venue_address': self.venue_address,
            'city': self.city,
            'state': self.addr_state,
            'country_code': self.country_code,
            'postal_code': self.postal_code,
            'has_location': self.has_location,
            'coordinates': self.coordinates
        }
    
    @property
    def full_address(self) -> str:
        """Get full formatted address"""
        parts = []
        if self.venue_name:
            parts.append(self.venue_name)
        if self.venue_address:
            parts.append(self.venue_address)
        if self.city:
            parts.append(self.city)
        if self.addr_state:
            parts.append(self.addr_state)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.country_code:
            parts.append(self.country_code)
        return ', '.join(filter(None, parts))
    
    def is_in_region(self, lat_min: float, lat_max: float, lng_min: float, lng_max: float) -> bool:
        """Check if location is within a geographic bounding box"""
        if not self.has_location:
            return False
        try:
            lat, lng = self.coordinates
            return lat_min <= lat <= lat_max and lng_min <= lng <= lng_max
        except:
            return False
    
    def is_in_socal(self) -> bool:
        """Check if location is in Southern California"""
        return self.is_in_region(32.5, 34.5, -119.0, -116.0)
    
    def distance_to(self, other_lat: float, other_lng: float) -> Optional[float]:
        """Calculate distance to another location in kilometers using Haversine formula"""
        if not self.has_location:
            return None
        
        try:
            from math import radians, cos, sin, asin, sqrt
            
            lat1, lng1 = self.coordinates
            lat2, lng2 = other_lat, other_lng
            
            # Convert to radians
            lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlng = lng2 - lng1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radius of earth in kilometers
            
            return r * c
        except:
            return None
    
    @classmethod
    def with_location(cls):
        """Query filter to get only objects with valid location data"""
        # Assume this is called from a class that inherits from BaseModel
        if hasattr(cls, 'session'):
            session = cls.session()
        else:
            from database_utils import get_session
            session = get_session().__enter__()
        
        return session.query(cls).filter(
            cls.lat.isnot(None),
            cls.lng.isnot(None)
        )
    
    @classmethod
    def in_region(cls, lat_min: float, lat_max: float, lng_min: float, lng_max: float):
        """Query filter to get objects within a geographic region"""
        # Assume this is called from a class that inherits from BaseModel
        if hasattr(cls, 'session'):
            session = cls.session()
        else:
            from database_utils import get_session
            session = get_session().__enter__()
        
        return session.query(cls).filter(
            cls.lat.isnot(None),
            cls.lng.isnot(None),
            cls.lat >= lat_min,
            cls.lat <= lat_max,
            cls.lng >= lng_min,
            cls.lng <= lng_max
        )
    
    @classmethod
    def in_socal(cls):
        """Query filter to get objects in Southern California"""
        return cls.in_region(32.5, 34.5, -119.0, -116.0)
    
    def get_heatmap_weight(self) -> float:
        """Get weight for heatmap visualization (can be overridden by subclasses)"""
        return 1.0

class BaseModel:
    """Base model with session-safe REPL-friendly methods"""
    
    @classmethod
    def session(cls):
        """Get current session from centralized database_utils"""
        global Session
        if Session is None:
            # Auto-initialize if not already done
            from database_utils import init_db
            _, Session = init_db()
        return Session()
    
    def save(self):
        """Save this instance using centralized session"""
        session = self.session()
        session.add(self)
        session.commit()
        
        # Clear cache after save to ensure consistency
        from database_utils import clear_session_cache
        clear_session_cache()
        
        log_debug(f"Saved {self.__class__.__name__}: {getattr(self, 'id', 'unknown')}", "model")
        return self
    
    def delete(self):
        """Delete this instance using centralized session"""
        session = self.session()
        session.delete(self)
        session.commit()
        
        # Clear cache after delete
        from database_utils import clear_session_cache
        clear_session_cache()
        
        log_debug(f"Deleted {self.__class__.__name__}: {getattr(self, 'id', 'unknown')}", "model")
    
    def refresh(self):
        """Reload from database"""
        session = self.session()
        session.refresh(self)
        return self
    
    def update(self, **kwargs):
        """Update attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    @classmethod
    def find(cls, id):
        """Find by primary key"""
        session = cls.session()
        return session.get(cls, id)
    
    @classmethod
    def find_by(cls, **kwargs):
        """Find first record matching criteria"""
        session = cls.session()
        result = session.query(cls).filter_by(**kwargs).first()
        log_debug(f"Found {cls.__name__} by {kwargs}: {'Yes' if result else 'No'}", "model")
        return result
    
    @classmethod
    def where(cls, **kwargs):
        """Find all records matching criteria"""
        session = cls.session()
        results = session.query(cls).filter_by(**kwargs).all()
        log_debug(f"Found {len(results)} {cls.__name__} records matching {kwargs}", "model")
        return results
    
    @classmethod
    def all(cls):
        """Get all records"""
        session = cls.session()
        results = session.query(cls).all()
        log_debug(f"Loaded all {len(results)} {cls.__name__} records", "model")
        return results
    
    @classmethod
    def count(cls):
        """Count all records"""
        session = cls.session()
        count = session.query(cls).count()
        log_debug(f"{cls.__name__} count: {count}", "model")
        return count

class Tournament(Base, BaseModel, LocationMixin):
    """Tournament from start.gg API with comprehensive data"""
    __tablename__ = 'tournaments'
    
    # Primary data
    id = Column(String, primary_key=True)  # start.gg tournament ID
    name = Column(String, nullable=False)
    
    # Attendance and sizing
    num_attendees = Column(Integer, default=0)
    
    # Dates and timing
    start_at = Column(Integer)  # Unix timestamp
    end_at = Column(Integer)  # Unix timestamp
    registration_closes_at = Column(Integer)  # Unix timestamp
    timezone = Column(String)
    
    # Tournament state
    tournament_state = Column(Integer, default=0)  # Tournament status (1,2,3...)
    
    # Note: Location fields (lat, lng, venue_name, venue_address, city, addr_state, 
    # country_code, postal_code) are inherited from LocationMixin
    
    # Owner information
    owner_id = Column(String)  # Tournament owner ID
    owner_name = Column(String)  # Owner display name
    
    # Contact and URLs
    primary_contact = Column(String)
    primary_contact_type = Column(String)  # Type of primary contact
    short_slug = Column(String)  # Short URL slug
    slug = Column(String)  # Full URL slug
    url = Column(String)  # Full start.gg URL
    
    # Registration and settings
    is_registration_open = Column(Integer, default=0)  # Boolean as int
    currency = Column(String)
    has_offline_events = Column(Integer, default=1)  # Boolean as int
    has_online_events = Column(Integer, default=0)  # Boolean as int
    tournament_type = Column(Integer)  # Tournament type enum
    
    # Additional metadata
    sync_timestamp = Column(Integer)  # When we last synced
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    # Removed attendance_records relationship - table deleted
    placements = relationship("TournamentPlacement", back_populates="tournament", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tournament(id='{self.id}', name='{self.name}', attendees={self.num_attendees})>"
    
    def __str__(self):
        return f"Tournament: {self.name} ({self.num_attendees} attendees)"
    
    def get_heatmap_weight(self) -> float:
        """Get weight for heatmap visualization based on attendance"""
        if not self.num_attendees:
            return 0.0
        # Use log scale to prevent large tournaments from dominating
        import math
        return math.log10(max(self.num_attendees, 1))
    
    @property
    def start_date(self) -> Optional[datetime]:
        """Get start date as datetime object"""
        if self.start_at:
            return datetime.fromtimestamp(self.start_at)
        return None
    
    @property
    def end_date(self) -> Optional[datetime]:
        """Get end date as datetime object"""
        if self.end_at:
            return datetime.fromtimestamp(self.end_at)
        return None
    
    @hybrid_property
    def is_active(self) -> bool:
        """Check if tournament is currently active"""
        if not self.start_at or not self.end_at:
            return False
        now = datetime.now().timestamp()
        return self.start_at <= now <= self.end_at
    
    @hybrid_property
    def is_upcoming(self) -> bool:
        """Check if tournament is upcoming"""
        if not self.start_at:
            return False
        return self.start_at > datetime.now().timestamp()
    
    @hybrid_property
    def is_past(self) -> bool:
        """Check if tournament is in the past"""
        if not self.end_at:
            return False
        return self.end_at < datetime.now().timestamp()
    
    def days_until(self) -> Optional[int]:
        """Get days until tournament starts (negative if past)"""
        if not self.start_at:
            return None
        delta = datetime.fromtimestamp(self.start_at) - datetime.now()
        return delta.days
    
    @classmethod
    def upcoming(cls, days: int = 30):
        """Get upcoming tournaments within specified days"""
        session = cls.session()
        future_timestamp = (datetime.now() + timedelta(days=days)).timestamp()
        now_timestamp = datetime.now().timestamp()
        
        return session.query(cls).filter(
            cls.start_at > now_timestamp,
            cls.start_at <= future_timestamp
        ).order_by(cls.start_at).all()
    
    @classmethod
    def recent(cls, days: int = 30):
        """Get recent past tournaments within specified days"""
        session = cls.session()
        past_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        now_timestamp = datetime.now().timestamp()
        
        return session.query(cls).filter(
            cls.end_at < now_timestamp,
            cls.end_at >= past_timestamp
        ).order_by(cls.end_at.desc()).all()
    
    @classmethod
    def by_year(cls, year: int):
        """Get tournaments for a specific year"""
        from datetime import timezone as tz
        session = cls.session()
        
        # Convert year to timestamps
        year_start = datetime(year, 1, 1, tzinfo=tz.utc).timestamp()
        year_end = datetime(year, 12, 31, 23, 59, 59, tzinfo=tz.utc).timestamp()
        
        return session.query(cls).filter(
            cls.start_at >= year_start,
            cls.start_at <= year_end
        ).order_by(cls.start_at).all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tournament to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'num_attendees': self.num_attendees,
            'start_at': self.start_at,
            'end_at': self.end_at,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'timezone': self.timezone,
            'tournament_state': self.tournament_state,
            'is_finished': self.is_finished(),
            'is_upcoming': self.is_upcoming,
            'is_past': self.is_past,
            'days_until': self.days_until(),
            'location': self.location_dict,
            'url': self.url,
            'slug': self.slug,
            'short_slug': self.short_slug,
            'primary_contact': self.primary_contact,
            'owner_name': self.owner_name,
            'top_8': [{
                'placement': p.placement,
                'player': p.player.gamer_tag,
                'prize': p.prize_dollars
            } for p in self.top_8]
        }
    
    @property
    def organization(self):
        """Get the organization that runs this tournament based on contact matching"""
        if not self.primary_contact:
            return None
        from database_utils import normalize_contact
        normalized = normalize_contact(self.primary_contact)
        
        # Find organization that has this normalized contact
        # Use the same session to keep objects attached
        session = self.session()
        orgs = session.query(Organization).all()
        for org in orgs:
            # Check if any of the org's contacts match
            for contact in org.contacts:
                if normalize_contact(contact.get('value', '')) == normalized:
                    return org
        return None
    
    @classmethod
    def by_contact(cls, contact):
        """Find tournaments by contact (compares normalized values)"""
        from database_utils import normalize_contact, get_session
        normalized = normalize_contact(contact)
        
        with get_session() as session:
            tournaments = session.query(cls).all()
            matching = []
            for t in tournaments:
                if t.primary_contact and normalize_contact(t.primary_contact) == normalized:
                    matching.append(t)
            return matching
    
    @classmethod
    def finished(cls):
        """Get finished tournaments only"""
        session = cls.session()
        results = session.query(cls).filter(
            cls.num_attendees > 0,
            cls.tournament_state >= 3
        ).all()
        log_debug(f"Found {len(results)} finished tournaments", "model")
        return results
    
    def is_finished(self):
        """Check if tournament is finished"""
        return self.num_attendees > 0 and self.tournament_state >= 3
    
    @property
    def top_8(self):
        """Get top 8 placements for this tournament"""
        return sorted(self.placements, key=lambda p: p.placement)[:8]
    
    @property
    def winner(self):
        """Get tournament winner (1st place)"""
        first_place = next((p for p in self.placements if p.placement == 1), None)
        return first_place.player if first_place else None
    
    def add_placement(self, player_startgg_id, gamer_tag, placement, prize_amount=0):
        """Add a top 8 placement"""
        # Get or create player using database_utils pattern
        player = Player.get_or_create(player_startgg_id, gamer_tag)
        
        # Check if placement already exists
        existing = TournamentPlacement.find_by(tournament_id=self.id, player_id=player.id)
        if existing:
            existing.placement = placement
            existing.prize_amount = prize_amount
            existing.save()
            return existing
        else:
            placement_record = TournamentPlacement(
                tournament_id=self.id,
                player_id=player.id,
                placement=placement,
                prize_amount=prize_amount
            )
            placement_record.save()
            return placement_record
    
    def get_top_8_dict(self):
        """Get top 8 as dictionary for storage efficiency"""
        top_8_dict = {}
        for placement in self.top_8:
            top_8_dict[placement.placement] = {
                'player_tag': placement.player.gamer_tag,
                'player_startgg_id': placement.player.startgg_id,
                'prize': placement.prize_amount
            }
        return top_8_dict
    
    def show_top_8(self):
        """Display top 8 placements organized by event"""
        print(f"\n{self.name} Top 8:")
        if not self.placements:
            print("  No standings data")
            return
        
        # Group by event
        events = {}
        for p in self.placements:
            event = p.event_name or "Main Event"
            if event not in events:
                events[event] = []
            events[event].append(p)
        
        for event_name, placements in events.items():
            print(f"  {event_name}:")
            sorted_placements = sorted(placements, key=lambda x: x.placement)
            for p in sorted_placements:
                print(f"    {p.placement}. {p.player.gamer_tag}")
        print()

class Organization(Base, BaseModel):
    """Organization that runs tournaments"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String, nullable=False)
    contacts_json = Column(String, default='[]')  # JSON array of contact objects
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Removed relationships to deleted tables
    
    @property
    def contacts(self):
        """Get contacts as a Python list"""
        import json
        try:
            return json.loads(self.contacts_json or '[]')
        except:
            return []
    
    @contacts.setter
    def contacts(self, value):
        """Set contacts from a Python list"""
        import json
        self.contacts_json = json.dumps(value)
    
    def add_contact(self, contact_type, contact_value):
        """Add a new contact"""
        contacts = self.contacts
        contacts.append({'type': contact_type, 'value': contact_value})
        self.contacts = contacts
    
    def remove_contact(self, index):
        """Remove a contact by index"""
        contacts = self.contacts
        if 0 <= index < len(contacts):
            contacts.pop(index)
            self.contacts = contacts
    
    def update_contact(self, index, contact_type, contact_value):
        """Update a contact by index"""
        contacts = self.contacts
        if 0 <= index < len(contacts):
            contacts[index] = {'type': contact_type, 'value': contact_value}
            self.contacts = contacts
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.display_name}')>"
    
    def __str__(self):
        return f"Organization: {self.display_name}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this organization"""
        tournaments = self.tournaments
        
        # Calculate various stats
        total_tournaments = len(tournaments)
        total_attendance = sum(t.num_attendees or 0 for t in tournaments)
        
        if tournaments:
            avg_attendance = total_attendance / total_tournaments
            largest_tournament = max(tournaments, key=lambda t: t.num_attendees or 0)
            
            # Date-based stats
            recent_tournaments = [t for t in tournaments if t.is_past and t.days_until() and t.days_until() > -90]
            upcoming_tournaments = [t for t in tournaments if t.is_upcoming]
            
            # Location stats
            tournaments_with_location = [t for t in tournaments if t.has_location]
            socal_tournaments = [t for t in tournaments_with_location if t.is_in_socal()]
            
            # Get unique cities
            cities = set(t.city for t in tournaments if t.city)
            
            return {
                'total_tournaments': total_tournaments,
                'total_attendance': total_attendance,
                'average_attendance': round(avg_attendance, 1),
                'largest_tournament': {
                    'name': largest_tournament.name,
                    'attendance': largest_tournament.num_attendees
                } if largest_tournament else None,
                'recent_count': len(recent_tournaments),
                'upcoming_count': len(upcoming_tournaments),
                'tournaments_with_location': len(tournaments_with_location),
                'socal_tournaments': len(socal_tournaments),
                'unique_cities': len(cities),
                'cities': sorted(cities)
            }
        else:
            return {
                'total_tournaments': 0,
                'total_attendance': 0,
                'average_attendance': 0,
                'largest_tournament': None,
                'recent_count': 0,
                'upcoming_count': 0,
                'tournaments_with_location': 0,
                'socal_tournaments': 0,
                'unique_cities': 0,
                'cities': []
            }
    
    def get_location_coverage(self) -> Dict[str, int]:
        """Get breakdown of tournaments by location"""
        coverage = {}
        for t in self.tournaments:
            if t.city:
                city_key = f"{t.city}, {t.addr_state}" if t.addr_state else t.city
                coverage[city_key] = coverage.get(city_key, 0) + 1
        return dict(sorted(coverage.items(), key=lambda x: x[1], reverse=True))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert organization to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'display_name': self.display_name,
            'contacts': self.contacts,
            'stats': self.get_stats(),
            'location_coverage': self.get_location_coverage(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def search(cls, query: str):
        """Search organizations by name (case-insensitive)"""
        session = cls.session()
        search_term = f"%{query}%"
        return session.query(cls).filter(
            cls.display_name.ilike(search_term)
        ).all()
    
    @property
    def tournaments(self):
        """Get all tournaments for this organization by matching contacts"""
        from database_utils import normalize_contact, get_session
        
        # Collect all normalized contacts for this org
        org_contacts_normalized = set()
        for contact in self.contacts:
            value = contact.get('value', '')
            if value:
                org_contacts_normalized.add(normalize_contact(value))
        
        # Find tournaments that match any of these contacts
        # We need to keep them attached to session for lazy loading
        session = self.session()  # Use the current session
        tournaments = session.query(Tournament).all()
        matching = []
        for t in tournaments:
            if t.primary_contact:
                t_normalized = normalize_contact(t.primary_contact)
                if t_normalized in org_contacts_normalized:
                    matching.append(t)
        
        return matching
    
    @property
    def total_attendance(self):
        """Calculate total attendance across all tournaments"""
        return sum(t.num_attendees or 0 for t in self.tournaments)
    
    @property
    def tournament_count(self):
        """Count of tournaments"""
        return len(self.tournaments)
    
    
    @classmethod
    def get_or_create(cls, normalized_key, display_name=None):
        """Get existing organization or create new one"""
        org = cls.find_by(normalized_key=normalized_key)
        
        if not org:
            if not display_name:
                display_name = normalized_key
            
            org = cls(
                normalized_key=normalized_key,
                display_name=display_name
            )
            org.save()
            log_debug(f"Created organization: {display_name}", "model")
        
        return org
    
    @classmethod
    def top_by_attendance(cls, limit=20):
        """Get organizations ranked by attendance"""
        session = cls.session()
        
        from sqlalchemy import desc, func
        results = session.query(cls).join(AttendanceRecord).group_by(cls.id).order_by(
            desc(func.sum(AttendanceRecord.attendance))
        ).limit(limit).all()
        
        log_debug(f"Loaded top {len(results)} organizations by attendance", "model")
        return results

class Player(Base, BaseModel):
    """Player in tournaments"""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    startgg_id = Column(String, unique=True, index=True)  # start.gg player ID
    gamer_tag = Column(String, nullable=False)
    name = Column(String)  # Real name (if available)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    placements = relationship("TournamentPlacement", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(tag='{self.gamer_tag}', id={self.startgg_id})>"
    
    def __str__(self):
        return self.gamer_tag
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this player"""
        placements = self.placements
        
        # Count placements by position
        placement_counts = {}
        for p in placements:
            pos = p.placement
            placement_counts[pos] = placement_counts.get(pos, 0) + 1
        
        # Get tournament wins
        wins = [p for p in placements if p.placement == 1]
        top_3s = [p for p in placements if p.placement <= 3]
        
        # Calculate earnings
        total_earnings = sum(p.prize_amount or 0 for p in placements)
        
        # Get unique tournaments
        tournament_ids = set(p.tournament_id for p in placements)
        
        # Singles vs doubles
        singles_placements = [p for p in placements if p.is_singles]
        doubles_placements = [p for p in placements if not p.is_singles]
        
        return {
            'total_placements': len(placements),
            'tournament_count': len(tournament_ids),
            'wins': len(wins),
            'top_3s': len(top_3s),
            'placement_breakdown': dict(sorted(placement_counts.items())),
            'total_earnings_cents': total_earnings,
            'total_earnings_dollars': total_earnings / 100.0 if total_earnings else 0.0,
            'singles_placements': len(singles_placements),
            'doubles_placements': len(doubles_placements),
            'win_rate': round(len(wins) / len(placements) * 100, 1) if placements else 0,
            'top_3_rate': round(len(top_3s) / len(placements) * 100, 1) if placements else 0
        }
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tournament results"""
        # Sort placements by tournament date
        recent = sorted(
            self.placements,
            key=lambda p: p.tournament.end_at if p.tournament and p.tournament.end_at else 0,
            reverse=True
        )[:limit]
        
        return [{
            'tournament': p.tournament.name if p.tournament else 'Unknown',
            'date': p.tournament.end_date.isoformat() if p.tournament and p.tournament.end_date else None,
            'placement': p.placement,
            'event': p.event_name,
            'prize': p.prize_dollars
        } for p in recent]
    
    def get_head_to_head(self, other_player_id: int) -> Dict[str, Any]:
        """Get head-to-head statistics against another player"""
        # Find tournaments where both players placed
        my_tournaments = {p.tournament_id: p for p in self.placements}
        
        other_player = Player.find(other_player_id)
        if not other_player:
            return {'error': 'Player not found'}
        
        other_tournaments = {p.tournament_id: p for p in other_player.placements}
        
        # Find common tournaments
        common_tournament_ids = set(my_tournaments.keys()) & set(other_tournaments.keys())
        
        wins = 0
        losses = 0
        encounters = []
        
        for t_id in common_tournament_ids:
            my_placement = my_tournaments[t_id]
            other_placement = other_tournaments[t_id]
            
            # Only count if same event
            if my_placement.event_id == other_placement.event_id:
                if my_placement.placement < other_placement.placement:
                    wins += 1
                else:
                    losses += 1
                
                encounters.append({
                    'tournament': my_placement.tournament.name if my_placement.tournament else t_id,
                    'event': my_placement.event_name,
                    'my_placement': my_placement.placement,
                    'their_placement': other_placement.placement,
                    'result': 'W' if my_placement.placement < other_placement.placement else 'L'
                })
        
        return {
            'vs_player': other_player.gamer_tag,
            'wins': wins,
            'losses': losses,
            'total_encounters': len(encounters),
            'win_rate': round(wins / len(encounters) * 100, 1) if encounters else 0,
            'recent_encounters': encounters[:5]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'startgg_id': self.startgg_id,
            'gamer_tag': self.gamer_tag,
            'name': self.name,
            'stats': self.get_stats(),
            'recent_results': self.get_recent_results(5),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def search(cls, query: str):
        """Search players by gamer tag or name (case-insensitive)"""
        session = cls.session()
        search_term = f"%{query}%"
        return session.query(cls).filter(
            (cls.gamer_tag.ilike(search_term)) |
            (cls.name.ilike(search_term))
        ).all()
    
    @classmethod
    def top_earners(cls, limit: int = 10):
        """Get top players by prize money earned"""
        from sqlalchemy import desc
        session = cls.session()
        
        # Subquery to calculate total earnings per player
        earnings_subq = session.query(
            TournamentPlacement.player_id,
            func.sum(TournamentPlacement.prize_amount).label('total_earnings')
        ).group_by(TournamentPlacement.player_id).subquery()
        
        # Join and order by earnings
        return session.query(cls).join(
            earnings_subq,
            cls.id == earnings_subq.c.player_id
        ).order_by(
            desc(earnings_subq.c.total_earnings)
        ).limit(limit).all()
    
    @classmethod
    def most_wins(cls, limit: int = 10):
        """Get players with most tournament wins"""
        from sqlalchemy import desc
        session = cls.session()
        
        # Subquery to count wins (1st place finishes)
        wins_subq = session.query(
            TournamentPlacement.player_id,
            func.count(TournamentPlacement.id).label('win_count')
        ).filter(
            TournamentPlacement.placement == 1
        ).group_by(TournamentPlacement.player_id).subquery()
        
        # Join and order by win count
        return session.query(cls).join(
            wins_subq,
            cls.id == wins_subq.c.player_id
        ).order_by(
            desc(wins_subq.c.win_count)
        ).limit(limit).all()
    
    @classmethod
    def get_or_create(cls, startgg_id, gamer_tag, name=None):
        """Get existing player or create new one"""
        player = cls.find_by(startgg_id=startgg_id)
        
        if not player:
            player = cls(
                startgg_id=startgg_id,
                gamer_tag=gamer_tag,
                name=name
            )
            player.save()
            log_debug(f"Created player: {gamer_tag}", "model")
        else:
            # Update info if provided
            updated = False
            if gamer_tag and player.gamer_tag != gamer_tag:
                player.gamer_tag = gamer_tag
                updated = True
            if name and player.name != name:
                player.name = name
                updated = True
            
            if updated:
                player.save()
                log_debug(f"Updated player: {gamer_tag}", "model")
        
        return player
    
    @property
    def tournaments_won(self):
        """Get tournaments this player won (1st place)"""
        return [p.tournament for p in self.placements if p.placement == 1]
    
    @property
    def total_winnings(self):
        """Calculate total prize money"""
        return sum(p.prize_amount for p in self.placements if p.prize_amount)

# Removed OrganizationContact and AttendanceRecord classes - tables deleted
    

class TournamentPlacement(Base, BaseModel):
    """Top 8 placements in tournaments"""
    __tablename__ = 'tournament_placements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(String, ForeignKey('tournaments.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    placement = Column(Integer, nullable=False)  # 1-8 for top 8
    prize_amount = Column(Integer, default=0)  # Prize money in cents
    event_name = Column(String)  # Name of the specific event (e.g. "SF6 Singles", "SF6 Doubles")
    event_id = Column(String)  # start.gg event ID
    
    recorded_at = Column(DateTime, default=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="placements")
    player = relationship("Player", back_populates="placements")
    
    # Unique constraint per event (player can place in multiple events per tournament)
    __table_args__ = (
        Index('ix_tournament_player_event', tournament_id, player_id, event_id, unique=True),
    )
    
    def __repr__(self):
        event_info = f" ({self.event_name})" if self.event_name else ""
        return f"<Placement(tournament={self.tournament_id}, player={self.player.gamer_tag if self.player else 'Unknown'}, place={self.placement}{event_info})>"
    
    def __str__(self):
        return f"{self.placement}. {self.player.gamer_tag if self.player else 'Unknown'}"
    
    @property
    def prize_dollars(self):
        """Prize amount in dollars"""
        return self.prize_amount / 100.0 if self.prize_amount else 0.0
    
    @property 
    def is_singles(self):
        """Check if this is a singles event"""
        if not self.event_name:
            return True  # Default assumption
        
        event_name = self.event_name.lower()
        # Check for doubles/teams indicators
        if any(keyword in event_name for keyword in ['doubles', 'teams', 'crew', '2v2', 'tag']):
            return False
        return True

# Utility functions (moved from database_utils to avoid circular imports)
def normalize_contact(contact):
    """Normalize contact information for consistent grouping"""
    if not contact:
        return None
    
    contact = contact.strip().lower()
    
    # Normalize Discord URLs
    if 'discord.gg' in contact or 'discord.com' in contact:
        discord_match = re.search(r'discord\.(?:gg|com/invite)/([a-zA-Z0-9]+)', contact)
        if discord_match:
            return f"discord:{discord_match.group(1).lower()}"
    
    # Normalize email addresses
    if '@' in contact:
        return contact.lower()
    
    # For organization names, normalize spacing
    contact = re.sub(r'\s+', ' ', contact)
    return contact

def get_display_name_from_contact(contact):
    """Get display name from contact"""
    if not contact:
        return "Unknown"
    
    # If it's not email or discord, use as display name
    if '@' not in contact and 'discord' not in contact.lower():
        return contact
    
    return contact

def determine_contact_type(contact):
    """Determine contact type"""
    if '@' in contact:
        return 'email'
    elif 'discord' in contact.lower():
        return 'discord'
    else:
        return 'name'

# Test functions for model validation
def test_models():
    """Test model operations with session-safe functions"""
    log_info("=" * 60, "test")
    log_info("TESTING MODEL OPERATIONS", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test 1: Create tournament
        log_info("TEST 1: Create tournament", "test")
        tournament = Tournament(
            id="test_model_123",
            name="Test Model Tournament",
            num_attendees=50,
            primary_contact="test@model.com",
            normalized_contact=normalize_contact("test@model.com"),
            tournament_state=3
        )
        tournament.save()
        log_info("✅ Tournament created", "test")
        
        # Test 2: Create organization
        log_info("TEST 2: Create organization", "test")
        org = Organization.get_or_create("test@model.com", "Test Model Organization")
        org.add_contact("test@model.com", "email", True)
        log_info("✅ Organization created", "test")
        
        # Test 3: Record attendance
        log_info("TEST 3: Record attendance", "test")
        AttendanceRecord.record_attendance(tournament.id, org.id, 50)
        log_info("✅ Attendance recorded", "test")
        
        # Test 4: Test queries and relationships
        log_info("TEST 4: Test queries", "test")
        found_tournament = Tournament.find("test_model_123")
        if found_tournament:
            log_info(f"✅ Found tournament: {found_tournament.name}", "test")
        
        top_orgs = Organization.top_by_attendance(5)
        log_info(f"✅ Found {len(top_orgs)} top organizations", "test")
        
        # Test 5: Test session consistency
        log_info("TEST 5: Test session consistency", "test")
        org_before = Organization.find_by(normalized_key="test@model.com")
        original_name = org_before.display_name
        
        # Change name and save
        org_before.display_name = "Updated Model Test Org"
        org_before.save()
        
        # Load again and verify
        org_after = Organization.find_by(normalized_key="test@model.com") 
        if org_after.display_name == "Updated Model Test Org":
            log_info("✅ Session consistency verified", "test")
        else:
            log_error(f"❌ Session inconsistency: Expected 'Updated Model Test Org', Got '{org_after.display_name}'", "test")
        
        # Cleanup
        log_info("Cleaning up test data", "test")
        found_tournament.delete()
        org_after.delete()
        
        log_info("✅ Model tests completed successfully", "test")
        
    except Exception as e:
        log_error(f"Model test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_model_relationships():
    """Test model relationships and properties"""
    log_info("=" * 60, "test")
    log_info("TESTING MODEL RELATIONSHIPS", "test")  
    log_info("=" * 60, "test")
    
    try:
        # Create test data
        tournament = Tournament(
            id="rel_test_123",
            name="Relationship Test Tournament",
            num_attendees=100,
            normalized_contact="relationships@test.com",
            tournament_state=3
        )
        tournament.save()
        
        org = Organization.get_or_create("relationships@test.com", "Relationships Test Org")
        
        # Test attendance relationship
        AttendanceRecord.record_attendance(tournament.id, org.id, 100)
        
        # Create test player and placement
        player = Player.get_or_create("player123", "TestPlayer", "Test Player Name")
        
        placemt = TournamentPlacement(
            tournament_id=tournament.id,
            player_id=player.id,
            placement=1,
            event_name="Test Event",
            event_id="event123"
        )
        placement.save()
        
        # Test relationships
        log_info("Testing tournament relationships", "test")
        
        # Tournament -> Organization
        tournament_org = tournament.organization
        if tournament_org and tournament_org.normalized_key == "relationships@test.com":
            log_info("✅ Tournament -> Organization relationship works", "test")
        else:
            log_error("❌ Tournament -> Organization relationship failed", "test")
        
        # Tournament -> Placements
        if tournament.top_8 and len(tournament.top_8) >= 1:
            log_info("✅ Tournament -> Placements relationship works", "test")
        else:
            log_error("❌ Tournament -> Placements relationship failed", "test")
        
        # Organization -> Tournaments
        org_tournaments = org.tournaments
        if org_tournaments and len(org_tournaments) >= 1:
            log_info("✅ Organization -> Tournaments relationship works", "test")
        else:
            log_error("❌ Organization -> Tournaments relationship failed", "test")
        
        # Organization properties
        if org.total_attendance == 100:
            log_info("✅ Organization.total_attendance property works", "test")
        else:
            log_error(f"❌ Organization.total_attendance failed: got {org.total_attendance}, expected 100", "test")
        
        if org.tournament_count == 1:
            log_info("✅ Organization.tournament_count property works", "test")
        else:
            log_error(f"❌ Organization.tournament_count failed: got {org.tournament_count}, expected 1", "test")
        
        # Player -> Placements
        player_placements = player.placements
        if player_placements and len(player_placements) >= 1:
            log_info("✅ Player -> Placements relationship works", "test")
        else:
            log_error("❌ Player -> Placements relationship failed", "test")
        
        # Cleanup
        placement.delete()
        player.delete()
        tournament.delete()
        org.delete()
        
        log_info("✅ Relationship tests completed", "test")
        
    except Exception as e:
        log_error(f"Relationship test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def run_model_tests():
    """Run all model tests"""
    try:
        # Initialize logging
        from log_utils import init_logging, LogLevel
        init_logging(console=True, level=LogLevel.DEBUG, debug_file="model_test.txt")
        
        log_info("Starting model tests", "test")
        
        # Initialize database using centralized function
        from database_utils import init_db
        init_db()
        
        # Run test suites
        test_models()
        print()  # Spacing
        test_model_relationships()
        
        log_info("All model tests completed - check model_test.txt for details", "test")
        
    except Exception as e:
        log_error(f"Model test suite failed: {e}", "test")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running tournament model tests...")
    run_model_tests()

