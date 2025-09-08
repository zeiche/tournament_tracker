"""
tournament_models_enhanced.py - Fully object-oriented SQLAlchemy models
Every model exposes all its data through methods and properties in a Pythonic way
"""
import re
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple, Dict, Any, Set, Union
from collections import defaultdict, Counter
from functools import cached_property
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index, Float, Boolean, func, desc, asc
from sqlalchemy.orm import declarative_base, relationship, Query
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.sql import func

# Import centralized session management
from utils.database import Session, get_session
from utils.database_service import database_service
normalize_contact = database_service._normalize_contact if hasattr(database_service, '_normalize_contact') else lambda x: x
from log_manager import LogManager

# Import Bonjour announcer mixin
# Bonjour mixin not yet available
AnnouncerMixin = object

# Import polymorphic input handler
try:
    from polymorphic_inputs import InputHandler, FlexibleQuery, to_list, to_ids
except ImportError:
    # Fallback if polymorphic_inputs not available
    InputHandler = None
    FlexibleQuery = None
    to_list = lambda x: [x] if not isinstance(x, list) else x
    to_ids = lambda x: []

# Get logger for this module
_logger = LogManager().get_logger('models')
log_debug = _logger.debug
log_info = _logger.info
log_error = _logger.error

Base = declarative_base()

# ============================================================================
# MIXINS - Reusable functionality
# ============================================================================

class TimestampMixin:
    """Mixin for models that track creation and update times"""
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    @property
    def age_days(self) -> int:
        """How many days old is this record"""
        if not self.created_at:
            return 0
        delta = datetime.now() - self.created_at
        return delta.days
    
    @property
    def last_modified_days(self) -> int:
        """Days since last modification"""
        if not self.updated_at:
            return 0
        delta = datetime.now() - self.updated_at
        return delta.days
    
    def was_modified(self) -> bool:
        """Check if record was modified after creation"""
        if not self.created_at or not self.updated_at:
            return False
        # Account for small time differences in same transaction
        return (self.updated_at - self.created_at).total_seconds() > 1

class LocationMixin:
    """Mixin for models that have geographic location data"""
    
    lat = Column(Float)  # Latitude
    lng = Column(Float)  # Longitude
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
    def has_full_address(self) -> bool:
        """Check if we have complete address information"""
        return all([self.venue_address, self.city, self.addr_state or self.country_code])
    
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
            'has_full_address': self.has_full_address,
            'coordinates': self.coordinates,
            'full_address': self.full_address
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
    
    @property
    def city_state(self) -> str:
        """Get city, state format"""
        if self.city and self.addr_state:
            return f"{self.city}, {self.addr_state}"
        return self.city or self.addr_state or "Unknown"
    
    def is_in_region(self, lat_min: float, lat_max: float, lng_min: float, lng_max: float) -> bool:
        """Check if location is within a geographic bounding box"""
        if not self.has_location:
            return False
        try:
            lat, lng = self.coordinates
            return lat_min <= lat <= lat_max and lng_min <= lng <= lng_max
        except (TypeError, ValueError, AttributeError):
            return False
    
    def is_in_socal(self) -> bool:
        """Check if location is in Southern California"""
        return self.is_in_region(32.5, 34.5, -119.0, -116.0)
    
    def is_in_norcal(self) -> bool:
        """Check if location is in Northern California"""
        return self.is_in_region(36.0, 39.0, -123.0, -120.0)
    
    def is_in_california(self) -> bool:
        """Check if location is anywhere in California"""
        return self.is_in_socal() or self.is_in_norcal() or self.addr_state == 'CA'
    
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
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    
    def distance_to_miles(self, other_lat: float, other_lng: float) -> Optional[float]:
        """Calculate distance in miles"""
        km = self.distance_to(other_lat, other_lng)
        return km * 0.621371 if km else None
    
    @classmethod
    def with_location(cls) -> Query:
        """Query filter to get only objects with valid location data"""
        if hasattr(cls, 'session'):
            session = cls.session()
        else:
            from database import get_session
            session = get_session().__enter__()
        
        return session.query(cls).filter(
            cls.lat.isnot(None),
            cls.lng.isnot(None)
        )
    
    @classmethod
    def in_region(cls, lat_min: float, lat_max: float, lng_min: float, lng_max: float) -> Query:
        """Query filter to get objects within a geographic region"""
        if hasattr(cls, 'session'):
            session = cls.session()
        else:
            from database import get_session
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
    def in_socal(cls) -> Query:
        """Query filter to get objects in Southern California"""
        return cls.in_region(32.5, 34.5, -119.0, -116.0)
    
    @classmethod
    def in_city(cls, city: str, state: Optional[str] = None) -> Query:
        """Query filter to get objects in a specific city"""
        if hasattr(cls, 'session'):
            session = cls.session()
        else:
            from database import get_session
            session = get_session().__enter__()
        
        query = session.query(cls).filter(cls.city == city)
        if state:
            query = query.filter(cls.addr_state == state)
        return query
    
    def get_heatmap_weight(self) -> float:
        """Get weight for heatmap visualization (can be overridden by subclasses)"""
        return 1.0

# ============================================================================
# BASE MODEL - Common functionality for all models
# ============================================================================

class BaseModel:
    """Base model with session-safe REPL-friendly methods"""
    
    @classmethod
    def session(cls):
        """Get current session from centralized database_utils"""
        # Use the imported Session directly, no global needed
        return Session() if Session else get_session()
    
    def save(self):
        """Save this instance using centralized session"""
        # Announce the save operation
        if hasattr(self, 'announce_operation'):
            self.announce_operation(f"Saving {self.__class__.__name__}")
        
        session = self.session()
        session.add(self)
        session.commit()
        
        # Clear cache after save to ensure consistency
        # clear_session_cache() - not available yet
        
        # Announce completion
        if hasattr(self, 'announce_state_change'):
            self.announce_state_change("saved", {"id": getattr(self, 'id', 'unknown')})
        
        log_debug(f"Saved {self.__class__.__name__}: {getattr(self, 'id', 'unknown')}")
        return self
    
    def delete(self):
        """Delete this instance using centralized session"""
        # Announce the delete operation
        if hasattr(self, 'announce_operation'):
            self.announce_operation(f"Deleting {self.__class__.__name__}")
        
        session = self.session()
        session.delete(self)
        session.commit()
        
        # Clear cache after delete
        # clear_session_cache() - not available yet
        
        # Announce completion
        if hasattr(self, 'announce_state_change'):
            self.announce_state_change("deleted", {"id": getattr(self, 'id', 'unknown')})
        
        log_debug(f"Deleted {self.__class__.__name__}: {getattr(self, 'id', 'unknown')}")
    
    def refresh(self):
        """Reload from database"""
        session = self.session()
        session.refresh(self)
        return self
    
    def update(self, **kwargs):
        """Update attributes and save"""
        # Announce what's being updated
        if hasattr(self, 'announce_operation'):
            self.announce_operation(f"Updating {self.__class__.__name__}", kwargs)
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
        return self
    
    def update_if_changed(self, **kwargs) -> bool:
        """Update only if values have changed"""
        changed = False
        for key, value in kwargs.items():
            if hasattr(self, key) and getattr(self, key) != value:
                setattr(self, key, value)
                changed = True
        if changed:
            self.save()
        return changed
    
    @classmethod
    def find(cls, input_value: Union[str, int, dict, list, Any]):
        """
        Find records using flexible input
        
        Examples:
            Tournament.find(123)  # Find by ID
            Tournament.find("123")  # Find by ID string
            Tournament.find({"name": "Summer Showdown"})  # Find by attributes
            Tournament.find(["123", "456"])  # Find multiple by IDs
            Tournament.find(tournament_obj)  # Return the object itself
        """
        session = cls.session()
        
        # Use polymorphic handler if available
        if InputHandler:
            parsed = InputHandler.parse(input_value, cls.__name__.lower())
            
            # Handle different parsed types
            if isinstance(parsed, dict):
                # Single ID
                if 'id' in parsed:
                    return session.get(cls, parsed['id'])
                
                # Multiple IDs
                elif 'ids' in parsed:
                    return session.query(cls).filter(cls.id.in_(parsed['ids'])).all()
                
                # Search by attributes
                elif '_metadata' in parsed:
                    # Remove metadata before querying
                    query_dict = {k: v for k, v in parsed.items() if k != '_metadata'}
                    if query_dict:
                        return session.query(cls).filter_by(**query_dict).first()
                
                # Text search
                elif 'text' in parsed:
                    # Search in name field if available
                    if hasattr(cls, 'name'):
                        return session.query(cls).filter(
                            cls.name.ilike(f"%{parsed['text']}%")
                        ).first()
            
            # Handle lists
            elif isinstance(parsed, list):
                return session.query(cls).filter(cls.id.in_(parsed)).all()
        
        # Fallback to traditional behavior
        if isinstance(input_value, (str, int)):
            return session.get(cls, input_value)
        elif isinstance(input_value, cls):
            return input_value  # Already the right object
        elif isinstance(input_value, dict):
            return session.query(cls).filter_by(**input_value).first()
        elif isinstance(input_value, list):
            return session.query(cls).filter(cls.id.in_(input_value)).all()
        
        return None
    
    @classmethod
    def find_by(cls, **kwargs):
        """Find first record matching criteria"""
        session = cls.session()
        result = session.query(cls).filter_by(**kwargs).first()
        log_debug(f"Found {cls.__name__} by {kwargs}: {'Yes' if result else 'No'}", "model")
        return result
    
    @classmethod
    def find_or_create(cls, defaults=None, **kwargs):
        """Find or create with defaults"""
        instance = cls.find_by(**kwargs)
        if not instance:
            params = kwargs.copy()
            if defaults:
                params.update(defaults)
            instance = cls(**params)
            instance.save()
        return instance
    
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
    
    @classmethod
    def exists(cls, **kwargs) -> bool:
        """Check if any record exists matching criteria"""
        session = cls.session()
        return session.query(cls).filter_by(**kwargs).count() > 0
    
    @classmethod
    def first(cls):
        """Get first record"""
        session = cls.session()
        return session.query(cls).first()
    
    @classmethod
    def last(cls):
        """Get last record (by ID)"""
        session = cls.session()
        return session.query(cls).order_by(cls.id.desc()).first()
    
    @classmethod
    def random(cls, limit: int = 1):
        """Get random records"""
        session = cls.session()
        return session.query(cls).order_by(func.random()).limit(limit).all()
    
    @classmethod
    def pluck(cls, column: str) -> List[Any]:
        """Get list of values for a specific column"""
        session = cls.session()
        attr = getattr(cls, column)
        return [row[0] for row in session.query(attr).all()]
    
    @classmethod
    def distinct(cls, column: str) -> List[Any]:
        """Get distinct values for a column"""
        session = cls.session()
        attr = getattr(cls, column)
        return [row[0] for row in session.query(attr).distinct().all()]
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        if hasattr(self, 'to_dict'):
            return json.dumps(self.to_dict(), default=str)
        return json.dumps({
            'id': getattr(self, 'id', None),
            'class': self.__class__.__name__
        })
    
    def clone(self):
        """Create a copy of this instance (not saved)"""
        data = {}
        for column in self.__table__.columns:
            if column.name not in ['id', 'created_at', 'updated_at']:
                data[column.name] = getattr(self, column.name)
        return self.__class__(**data)

# ============================================================================
# TOURNAMENT MODEL
# ============================================================================

class Tournament(Base, BaseModel, LocationMixin, TimestampMixin, AnnouncerMixin):
    """Tournament from start.gg API with comprehensive data and methods"""
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
    
    # Relationships
    placements = relationship("TournamentPlacement", back_populates="tournament", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tournament(id='{self.id}', name='{self.name}', attendees={self.num_attendees})>"
    
    def __str__(self):
        return f"{self.name} ({self.num_attendees} attendees)"
    
    def __eq__(self, other):
        """Enable equality comparison"""
        if not isinstance(other, Tournament):
            return NotImplemented
        return self.id == other.id
    
    def __lt__(self, other):
        """Enable sorting by date (earlier tournaments first)"""
        if not isinstance(other, Tournament):
            return NotImplemented
        # Handle None values
        self_date = self.start_at or datetime.min
        other_date = other.start_at or datetime.min
        return self_date < other_date
    
    def __hash__(self):
        """Make tournaments hashable for use in sets/dicts"""
        return hash((self.__class__.__name__, self.id))
    
    # ========================================================================
    # DATE AND TIME METHODS
    # ========================================================================
    
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
    
    @property
    def registration_close_date(self) -> Optional[datetime]:
        """Get registration close date"""
        if self.registration_closes_at:
            return datetime.fromtimestamp(self.registration_closes_at)
        return None
    
    @property
    def duration_days(self) -> Optional[int]:
        """Get tournament duration in days"""
        if self.start_at and self.end_at:
            return max(1, (self.end_at - self.start_at) // 86400)
        return None
    
    @property
    def duration_hours(self) -> Optional[float]:
        """Get tournament duration in hours"""
        if self.start_at and self.end_at:
            return (self.end_at - self.start_at) / 3600
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
    
    @property
    def is_registration_open_bool(self) -> bool:
        """Get registration status as boolean"""
        return bool(self.is_registration_open)
    
    @property
    def has_offline_events_bool(self) -> bool:
        """Get offline events status as boolean"""
        return bool(self.has_offline_events)
    
    @property
    def has_online_events_bool(self) -> bool:
        """Get online events status as boolean"""
        return bool(self.has_online_events)
    
    def days_until(self) -> Optional[int]:
        """Get days until tournament starts (negative if past)"""
        if not self.start_at:
            return None
        delta = datetime.fromtimestamp(self.start_at) - datetime.now()
        return delta.days
    
    def days_since(self) -> Optional[int]:
        """Get days since tournament ended"""
        if not self.end_at:
            return None
        delta = datetime.now() - datetime.fromtimestamp(self.end_at)
        return delta.days
    
    def get_month(self) -> Optional[str]:
        """Get month of tournament"""
        if self.start_date:
            return self.start_date.strftime("%B %Y")
        return None
    
    def get_weekday(self) -> Optional[str]:
        """Get day of week"""
        if self.start_date:
            return self.start_date.strftime("%A")
        return None
    
    # ========================================================================
    # STATE AND STATUS METHODS
    # ========================================================================
    
    def is_finished(self) -> bool:
        """Check if tournament is finished"""
        return self.num_attendees > 0 and self.tournament_state >= 3
    
    def is_cancelled(self) -> bool:
        """Check if tournament was cancelled"""
        return self.tournament_state == 0 and self.is_past
    
    def get_state_name(self) -> str:
        """Get human-readable state name"""
        states = {
            0: "Created",
            1: "Registration Open",
            2: "Registration Closed",
            3: "In Progress",
            4: "Complete",
            5: "Cancelled"
        }
        return states.get(self.tournament_state, "Unknown")
    
    def get_status(self) -> str:
        """Get current status"""
        if self.is_cancelled():
            return "Cancelled"
        elif self.is_upcoming:
            return "Upcoming"
        elif self.is_active:
            return "Active"
        elif self.is_finished():
            return "Finished"
        else:
            return "Past"
    
    # ========================================================================
    # ATTENDANCE AND SIZE METHODS
    # ========================================================================
    
    def get_size_category(self) -> str:
        """Categorize tournament by size"""
        if not self.num_attendees:
            return "Unknown"
        elif self.num_attendees < 20:
            return "Local"
        elif self.num_attendees < 50:
            return "Small"
        elif self.num_attendees < 100:
            return "Medium"
        elif self.num_attendees < 200:
            return "Large"
        elif self.num_attendees < 500:
            return "Major"
        else:
            return "Premier"
    
    def get_heatmap_weight(self) -> float:
        """Get weight for heatmap visualization based on attendance"""
        if not self.num_attendees:
            return 0.0
        # Use log scale to prevent large tournaments from dominating
        import math
        return math.log10(max(self.num_attendees, 1))
    
    def is_major(self) -> bool:
        """Check if this is a major tournament (100+ attendees)"""
        return self.num_attendees and self.num_attendees >= 100
    
    def is_premier(self) -> bool:
        """Check if this is a premier tournament (500+ attendees)"""
        return self.num_attendees and self.num_attendees >= 500
    
    # ========================================================================
    # PLACEMENT AND RESULTS METHODS
    # ========================================================================
    
    @property
    def top_8(self) -> List["TournamentPlacement"]:
        """Get top 8 placements for this tournament"""
        return sorted([p for p in self.placements if p.placement <= 8], 
                     key=lambda p: p.placement)
    
    @property
    def winner(self) -> Optional["Player"]:
        """Get tournament winner (1st place)"""
        first_place = next((p for p in self.placements if p.placement == 1), None)
        return first_place.player if first_place else None
    
    def get_placement(self, placement: int) -> Optional["TournamentPlacement"]:
        """Get specific placement"""
        return next((p for p in self.placements if p.placement == placement), None)
    
    def get_top_n(self, n: int) -> List["TournamentPlacement"]:
        """Get top N placements"""
        return sorted([p for p in self.placements if p.placement <= n], 
                     key=lambda p: p.placement)
    
    def get_placements_by_event(self) -> Dict[str, List["TournamentPlacement"]]:
        """Group placements by event"""
        events = defaultdict(list)
        for p in self.placements:
            event = p.event_name or "Main Event"
            events[event].append(p)
        return {event: sorted(places, key=lambda x: x.placement) 
                for event, places in events.items()}
    
    def has_player(self, player_id: int) -> bool:
        """Check if a player participated"""
        return any(p.player_id == player_id for p in self.placements)
    
    def get_player_placement(self, player_id: int) -> Optional[int]:
        """Get placement for a specific player"""
        placement = next((p for p in self.placements if p.player_id == player_id), None)
        return placement.placement if placement else None
    
    # ========================================================================
    # ORGANIZATION AND CONTACT METHODS
    # ========================================================================
    
    @cached_property
    def organization(self) -> Optional["Organization"]:
        """Get the organization that runs this tournament (cached)"""
        if not self.primary_contact:
            return None
        normalized = normalize_contact(self.primary_contact)
        
        from database import session_scope
        with session_scope() as session:
            orgs = session.query(Organization).all()
            for org in orgs:
                for contact in org.contacts:
                    if normalize_contact(contact.get('value', '')) == normalized:
                        return org
            return None
    
    def get_contact_type(self) -> str:
        """Determine the type of primary contact"""
        if not self.primary_contact:
            return "none"
        contact = self.primary_contact.lower()
        if '@' in contact:
            return "email"
        elif 'discord' in contact:
            return "discord"
        elif contact.startswith('http'):
            return "website"
        else:
            return "other"
    
    # ========================================================================
    # URL AND LINK METHODS
    # ========================================================================
    
    def get_startgg_url(self) -> str:
        """Get full start.gg URL"""
        if self.url:
            return self.url
        elif self.slug:
            return f"https://start.gg/tournament/{self.slug}"
        return f"https://start.gg/tournament/{self.id}"
    
    def get_registration_url(self) -> str:
        """Get registration URL"""
        return f"{self.get_startgg_url()}/register"
    
    # ========================================================================
    # ANALYTICS AND STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive tournament statistics"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.get_status(),
            'size_category': self.get_size_category(),
            'attendees': self.num_attendees,
            'duration_days': self.duration_days,
            'days_until': self.days_until() if self.is_upcoming else None,
            'days_since': self.days_since() if self.is_past else None,
            'has_location': self.has_location,
            'is_major': self.is_major(),
            'is_premier': self.is_premier(),
            'placement_count': len(self.placements),
            'unique_events': len(set(p.event_name for p in self.placements if p.event_name)),
            'total_prize_pool': sum(p.prize_amount or 0 for p in self.placements) / 100,
            'has_offline': self.has_offline_events_bool,
            'has_online': self.has_online_events_bool,
            'organization': self.organization.display_name if self.organization else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'num_attendees': self.num_attendees,
            'status': self.get_status(),
            'state': self.get_state_name(),
            'size_category': self.get_size_category(),
            
            # Dates
            'start_at': self.start_at,
            'end_at': self.end_at,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'month': self.get_month(),
            'weekday': self.get_weekday(),
            'timezone': self.timezone,
            
            # Status flags
            'is_finished': self.is_finished(),
            'is_upcoming': self.is_upcoming,
            'is_past': self.is_past,
            'is_active': self.is_active,
            'is_major': self.is_major(),
            
            # Time calculations
            'days_until': self.days_until(),
            'days_since': self.days_since(),
            'duration_days': self.duration_days,
            
            # Location
            'location': self.location_dict,
            
            # URLs and contact
            'url': self.url,
            'slug': self.slug,
            'short_slug': self.short_slug,
            'startgg_url': self.get_startgg_url(),
            'primary_contact': self.primary_contact,
            'contact_type': self.get_contact_type(),
            'owner_name': self.owner_name,
            
            # Settings
            'is_registration_open': self.is_registration_open_bool,
            'currency': self.currency,
            'has_offline_events': self.has_offline_events_bool,
            'has_online_events': self.has_online_events_bool,
            
            # Results
            'winner': self.winner.gamer_tag if self.winner else None,
            'top_8': [{
                'placement': p.placement,
                'player': p.player.gamer_tag,
                'prize': p.prize_dollars
            } for p in self.top_8],
            
            # Organization
            'organization': self.organization.display_name if self.organization else None,
            
            # Metadata
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sync_timestamp': self.sync_timestamp
        }
    
    # ========================================================================
    # CLASS METHODS - QUERIES
    # ========================================================================
    
    @classmethod
    def upcoming(cls, days: int = 30) -> List["Tournament"]:
        """Get upcoming tournaments within specified days"""
        session = cls.session()
        future_timestamp = (datetime.now() + timedelta(days=days)).timestamp()
        now_timestamp = datetime.now().timestamp()
        
        return session.query(cls).filter(
            cls.start_at > now_timestamp,
            cls.start_at <= future_timestamp
        ).order_by(cls.start_at).all()
    
    @classmethod
    def recent(cls, days: int = 30) -> List["Tournament"]:
        """Get recent past tournaments within specified days"""
        session = cls.session()
        past_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
        now_timestamp = datetime.now().timestamp()
        
        return session.query(cls).filter(
            cls.end_at < now_timestamp,
            cls.end_at >= past_timestamp
        ).order_by(cls.end_at.desc()).all()
    
    @classmethod
    def active(cls) -> List["Tournament"]:
        """Get currently active tournaments"""
        session = cls.session()
        now_timestamp = datetime.now().timestamp()
        
        return session.query(cls).filter(
            cls.start_at <= now_timestamp,
            cls.end_at >= now_timestamp
        ).all()
    
    @classmethod
    def by_year(cls, year: int) -> List["Tournament"]:
        """Get tournaments for a specific year"""
        from datetime import timezone as tz
        session = cls.session()
        
        year_start = datetime(year, 1, 1, tzinfo=tz.utc).timestamp()
        year_end = datetime(year, 12, 31, 23, 59, 59, tzinfo=tz.utc).timestamp()
        
        return session.query(cls).filter(
            cls.start_at >= year_start,
            cls.start_at <= year_end
        ).order_by(cls.start_at).all()
    
    @classmethod
    def by_month(cls, year: int, month: int) -> List["Tournament"]:
        """Get tournaments for a specific month"""
        from datetime import timezone as tz
        from calendar import monthrange
        session = cls.session()
        
        month_start = datetime(year, month, 1, tzinfo=tz.utc).timestamp()
        last_day = monthrange(year, month)[1]
        month_end = datetime(year, month, last_day, 23, 59, 59, tzinfo=tz.utc).timestamp()
        
        return session.query(cls).filter(
            cls.start_at >= month_start,
            cls.start_at <= month_end
        ).order_by(cls.start_at).all()
    
    @classmethod
    def by_size(cls, min_size: int = 0, max_size: Optional[int] = None) -> List["Tournament"]:
        """Get tournaments by attendance size"""
        session = cls.session()
        query = session.query(cls).filter(cls.num_attendees >= min_size)
        if max_size:
            query = query.filter(cls.num_attendees <= max_size)
        return query.order_by(cls.num_attendees.desc()).all()
    
    @classmethod
    def majors(cls) -> List["Tournament"]:
        """Get major tournaments (100+ attendees)"""
        return cls.by_size(min_size=100)
    
    @classmethod
    def premiers(cls) -> List["Tournament"]:
        """Get premier tournaments (500+ attendees)"""
        return cls.by_size(min_size=500)
    
    @classmethod
    def finished(cls) -> List["Tournament"]:
        """Get finished tournaments only"""
        session = cls.session()
        return session.query(cls).filter(
            cls.num_attendees > 0,
            cls.tournament_state >= 3
        ).all()
    
    @classmethod
    def with_results(cls) -> List["Tournament"]:
        """Get tournaments that have placement results"""
        session = cls.session()
        return session.query(cls).join(TournamentPlacement).distinct().all()
    
    @classmethod
    def search(cls, query: str) -> List["Tournament"]:
        """Search tournaments by name"""
        session = cls.session()
        search_term = f"%{query}%"
        return session.query(cls).filter(
            cls.name.ilike(search_term)
        ).all()
    
    @classmethod
    def by_contact(cls, contact: str) -> List["Tournament"]:
        """Find tournaments by contact"""
        normalized = normalize_contact(contact)
        
        session = cls.session()
        tournaments = session.query(cls).all()
        matching = []
        for t in tournaments:
            if t.primary_contact and normalize_contact(t.primary_contact) == normalized:
                matching.append(t)
        return matching
    
    @classmethod
    def by_owner(cls, owner_name: str) -> List["Tournament"]:
        """Find tournaments by owner"""
        session = cls.session()
        return session.query(cls).filter(cls.owner_name == owner_name).all()

# Continue with Organization, Player, and TournamentPlacement models...
# (This is getting long, should I continue with the rest?)# ============================================================================
# ORGANIZATION MODEL
# ============================================================================

class Organization(Base, BaseModel, TimestampMixin, AnnouncerMixin):
    """Organization that runs tournaments with comprehensive analytics"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String, nullable=False)
    contacts_json = Column(String, default='[]')  # JSON array of contact objects
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.display_name}')>"
    
    def __str__(self):
        return self.display_name
    
    def __eq__(self, other):
        """Enable equality comparison"""
        if not isinstance(other, Organization):
            return NotImplemented
        return self.id == other.id
    
    def __lt__(self, other):
        """Enable sorting by display name (alphabetical)"""
        if not isinstance(other, Organization):
            return NotImplemented
        return self.display_name.lower() < other.display_name.lower()
    
    def __hash__(self):
        """Make organizations hashable for use in sets/dicts"""
        return hash((self.__class__.__name__, self.id))
    
    # ========================================================================
    # CONTACT MANAGEMENT
    # ========================================================================
    
    @property
    def contacts(self) -> List[Dict[str, str]]:
        """Get contacts as a Python list"""
        import json
        try:
            return json.loads(self.contacts_json or '[]')
        except (json.JSONDecodeError, TypeError, AttributeError):
            return []
    
    @contacts.setter
    def contacts(self, value: List[Dict[str, str]]):
        """Set contacts from a Python list"""
        import json
        self.contacts_json = json.dumps(value)
    
    def add_contact(self, contact_type: str, contact_value: str) -> "Organization":
        """Add a new contact"""
        contacts = self.contacts
        contacts.append({'type': contact_type, 'value': contact_value})
        self.contacts = contacts
        self.save()
        return self
    
    def remove_contact(self, index: int) -> bool:
        """Remove a contact by index"""
        contacts = self.contacts
        if 0 <= index < len(contacts):
            contacts.pop(index)
            self.contacts = contacts
            self.save()
            return True
        return False
    
    def update_contact(self, index: int, contact_type: str, contact_value: str) -> bool:
        """Update a contact by index"""
        contacts = self.contacts
        if 0 <= index < len(contacts):
            contacts[index] = {'type': contact_type, 'value': contact_value}
            self.contacts = contacts
            self.save()
            return True
        return False
    
    def has_contact(self, contact_value: str) -> bool:
        """Check if organization has a specific contact"""
        normalized = normalize_contact(contact_value)
        for contact in self.contacts:
            if normalize_contact(contact.get('value', '')) == normalized:
                return True
        return False
    
    def get_contact_by_type(self, contact_type: str) -> List[str]:
        """Get all contacts of a specific type"""
        return [c['value'] for c in self.contacts if c.get('type') == contact_type]
    
    def get_primary_contact(self) -> Optional[str]:
        """Get the primary (first) contact"""
        if self.contacts:
            return self.contacts[0].get('value')
        return None
    
    def get_contact_types(self) -> Set[str]:
        """Get unique contact types"""
        return set(c.get('type', 'unknown') for c in self.contacts)
    
    # ========================================================================
    # TOURNAMENT RELATIONSHIPS
    # ========================================================================
    
    @property
    def tournaments(self) -> List[Tournament]:
        """Get all tournaments for this organization"""
        
        # Collect all normalized contacts for this org
        org_contacts_normalized = set()
        for contact in self.contacts:
            value = contact.get('value', '')
            if value:
                org_contacts_normalized.add(normalize_contact(value))
        
        # Find tournaments that match any of these contacts
        session = self.session()
        tournaments = session.query(Tournament).all()
        matching = []
        for t in tournaments:
            if t.primary_contact:
                t_normalized = normalize_contact(t.primary_contact)
                if t_normalized in org_contacts_normalized:
                    matching.append(t)
        
        return matching
    
    @property
    def tournament_count(self) -> int:
        """Count of tournaments"""
        return len(self.tournaments)
    
    @property
    def total_attendance(self) -> int:
        """Calculate total attendance across all tournaments"""
        return sum(t.num_attendees or 0 for t in self.tournaments)
    
    @property
    def average_attendance(self) -> float:
        """Calculate average attendance"""
        tournaments = self.tournaments
        if not tournaments:
            return 0.0
        total = sum(t.num_attendees or 0 for t in tournaments)
        return total / len(tournaments)
    
    def get_tournaments_by_year(self, year: int) -> List[Tournament]:
        """Get tournaments for a specific year"""
        return [t for t in self.tournaments 
                if t.start_date and t.start_date.year == year]
    
    def get_upcoming_tournaments(self) -> List[Tournament]:
        """Get upcoming tournaments"""
        return sorted([t for t in self.tournaments if t.is_upcoming],
                     key=lambda t: t.start_at)
    
    def get_recent_tournaments(self, days: int = 90) -> List[Tournament]:
        """Get recent tournaments"""
        return [t for t in self.tournaments 
                if t.is_past and t.days_since() and t.days_since() <= days]
    
    def get_active_tournaments(self) -> List[Tournament]:
        """Get currently active tournaments"""
        return [t for t in self.tournaments if t.is_active]
    
    def get_largest_tournament(self) -> Optional[Tournament]:
        """Get the largest tournament by attendance"""
        tournaments = self.tournaments
        if not tournaments:
            return None
        return max(tournaments, key=lambda t: t.num_attendees or 0)
    
    def get_first_tournament(self) -> Optional[Tournament]:
        """Get the earliest tournament"""
        tournaments = [t for t in self.tournaments if t.start_at]
        if not tournaments:
            return None
        return min(tournaments, key=lambda t: t.start_at)
    
    def get_latest_tournament(self) -> Optional[Tournament]:
        """Get the most recent tournament"""
        tournaments = [t for t in self.tournaments if t.end_at]
        if not tournaments:
            return None
        return max(tournaments, key=lambda t: t.end_at)
    
    # ========================================================================
    # LOCATION ANALYTICS
    # ========================================================================
    
    def get_location_coverage(self) -> Dict[str, int]:
        """Get breakdown of tournaments by location"""
        coverage = {}
        for t in self.tournaments:
            if t.city:
                city_key = f"{t.city}, {t.addr_state}" if t.addr_state else t.city
                coverage[city_key] = coverage.get(city_key, 0) + 1
        return dict(sorted(coverage.items(), key=lambda x: x[1], reverse=True))
    
    def get_unique_cities(self) -> Set[str]:
        """Get unique cities where tournaments are held"""
        return set(t.city for t in self.tournaments if t.city)
    
    def get_unique_venues(self) -> Set[str]:
        """Get unique venues"""
        return set(t.venue_name for t in self.tournaments if t.venue_name)
    
    def get_geographic_spread(self) -> Optional[float]:
        """Calculate geographic spread (max distance between tournaments) in km"""
        tournaments_with_loc = [t for t in self.tournaments if t.has_location]
        if len(tournaments_with_loc) < 2:
            return None
        
        max_distance = 0
        for i, t1 in enumerate(tournaments_with_loc):
            for t2 in tournaments_with_loc[i+1:]:
                if t1.coordinates and t2.coordinates:
                    distance = t1.distance_to(*t2.coordinates)
                    if distance and distance > max_distance:
                        max_distance = distance
        
        return max_distance if max_distance > 0 else None
    
    def is_local_org(self) -> bool:
        """Check if this is a local organization (all tournaments in same city)"""
        cities = self.get_unique_cities()
        return len(cities) == 1
    
    def is_regional_org(self) -> bool:
        """Check if this is a regional organization (multiple cities)"""
        cities = self.get_unique_cities()
        return len(cities) > 1
    
    # ========================================================================
    # TEMPORAL ANALYTICS
    # ========================================================================
    
    def get_activity_span_days(self) -> Optional[int]:
        """Get the span of activity in days (first to last tournament)"""
        first = self.get_first_tournament()
        last = self.get_latest_tournament()
        
        if first and last and first.start_at and last.end_at:
            return (last.end_at - first.start_at) // 86400
        return None
    
    def get_frequency(self) -> Optional[float]:
        """Get average frequency of tournaments (per month)"""
        span_days = self.get_activity_span_days()
        if not span_days or span_days == 0:
            return None
        
        months = span_days / 30
        return self.tournament_count / months if months > 0 else None
    
    def get_monthly_distribution(self) -> Dict[str, int]:
        """Get distribution of tournaments by month"""
        distribution = defaultdict(int)
        for t in self.tournaments:
            if t.start_date:
                month_key = t.start_date.strftime("%B")
                distribution[month_key] += 1
        return dict(distribution)
    
    def get_weekday_distribution(self) -> Dict[str, int]:
        """Get distribution of tournaments by day of week"""
        distribution = defaultdict(int)
        for t in self.tournaments:
            if t.start_date:
                weekday = t.start_date.strftime("%A")
                distribution[weekday] += 1
        return dict(distribution)
    
    def get_yearly_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics broken down by year"""
        yearly = defaultdict(lambda: {'count': 0, 'attendance': 0, 'tournaments': []})
        
        for t in self.tournaments:
            if t.start_date:
                year = t.start_date.year
                yearly[year]['count'] += 1
                yearly[year]['attendance'] += t.num_attendees or 0
                yearly[year]['tournaments'].append(t.name)
        
        # Calculate averages
        for year, stats in yearly.items():
            if stats['count'] > 0:
                stats['avg_attendance'] = stats['attendance'] / stats['count']
        
        return dict(yearly)
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    def get_growth_rate(self) -> Optional[float]:
        """Calculate year-over-year growth rate in attendance"""
        yearly = self.get_yearly_stats()
        if len(yearly) < 2:
            return None
        
        years = sorted(yearly.keys())
        recent = yearly[years[-1]]['attendance']
        previous = yearly[years[-2]]['attendance']
        
        if previous == 0:
            return None
        
        return ((recent - previous) / previous) * 100
    
    def get_consistency_score(self) -> float:
        """Calculate consistency score (0-100) based on regular tournament schedule"""
        freq = self.get_frequency()
        if not freq:
            return 0.0
        
        # Score based on frequency (1-4 per month is good)
        if 1 <= freq <= 4:
            return min(100, freq * 25)
        elif freq < 1:
            return freq * 100  # Less than monthly
        else:
            return max(0, 100 - (freq - 4) * 10)  # Too frequent
    
    def get_retention_metrics(self) -> Dict[str, Any]:
        """Calculate player retention metrics"""
        # Track players across tournaments
        player_tournaments = defaultdict(list)
        
        for t in self.tournaments:
            for p in t.placements:
                player_tournaments[p.player_id].append(t.id)
        
        # Calculate metrics
        total_players = len(player_tournaments)
        returning_players = sum(1 for tournaments in player_tournaments.values() 
                               if len(tournaments) > 1)
        
        retention_rate = (returning_players / total_players * 100) if total_players > 0 else 0
        
        # Average tournaments per player
        avg_tournaments = (sum(len(t) for t in player_tournaments.values()) / total_players) if total_players > 0 else 0
        
        return {
            'total_unique_players': total_players,
            'returning_players': returning_players,
            'retention_rate': round(retention_rate, 1),
            'avg_tournaments_per_player': round(avg_tournaments, 2),
            'loyal_players': sum(1 for t in player_tournaments.values() if len(t) >= 5)
        }
    
    # ========================================================================
    # COMPREHENSIVE STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this organization"""
        tournaments = self.tournaments
        
        if not tournaments:
            return self._empty_stats()
        
        largest = self.get_largest_tournament()
        retention = self.get_retention_metrics()
        
        return {
            # Basic metrics
            'total_tournaments': len(tournaments),
            'total_attendance': self.total_attendance,
            'average_attendance': round(self.average_attendance, 1),
            
            # Size metrics
            'largest_tournament': {
                'name': largest.name,
                'attendance': largest.num_attendees
            } if largest else None,
            
            # Temporal metrics
            'upcoming_count': len(self.get_upcoming_tournaments()),
            'recent_count': len(self.get_recent_tournaments()),
            'activity_span_days': self.get_activity_span_days(),
            'frequency_per_month': round(self.get_frequency() or 0, 2),
            'growth_rate': self.get_growth_rate(),
            'consistency_score': round(self.get_consistency_score(), 1),
            
            # Location metrics
            'unique_cities': len(self.get_unique_cities()),
            'unique_venues': len(self.get_unique_venues()),
            'cities': sorted(self.get_unique_cities()),
            'is_local': self.is_local_org(),
            'is_regional': self.is_regional_org(),
            'geographic_spread_km': round(self.get_geographic_spread() or 0, 1),
            
            # Location breakdown
            'location_coverage': self.get_location_coverage(),
            'socal_tournaments': len([t for t in tournaments if t.is_in_socal()]),
            
            # Player metrics
            'retention_metrics': retention,
            
            # Tournament categories
            'major_tournaments': len([t for t in tournaments if t.is_major()]),
            'premier_tournaments': len([t for t in tournaments if t.is_premier()]),
            'finished_tournaments': len([t for t in tournaments if t.is_finished()]),
            
            # Distributions
            'monthly_distribution': self.get_monthly_distribution(),
            'weekday_distribution': self.get_weekday_distribution()
        }
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats structure"""
        return {
            'total_tournaments': 0,
            'total_attendance': 0,
            'average_attendance': 0,
            'largest_tournament': None,
            'upcoming_count': 0,
            'recent_count': 0,
            'activity_span_days': None,
            'frequency_per_month': 0,
            'growth_rate': None,
            'consistency_score': 0,
            'unique_cities': 0,
            'unique_venues': 0,
            'cities': [],
            'is_local': False,
            'is_regional': False,
            'geographic_spread_km': 0,
            'location_coverage': {},
            'socal_tournaments': 0,
            'retention_metrics': {
                'total_unique_players': 0,
                'returning_players': 0,
                'retention_rate': 0,
                'avg_tournaments_per_player': 0,
                'loyal_players': 0
            },
            'major_tournaments': 0,
            'premier_tournaments': 0,
            'finished_tournaments': 0,
            'monthly_distribution': {},
            'weekday_distribution': {}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'display_name': self.display_name,
            'contacts': self.contacts,
            'contact_types': list(self.get_contact_types()),
            'primary_contact': self.get_primary_contact(),
            'tournament_count': self.tournament_count,
            'total_attendance': self.total_attendance,
            'average_attendance': round(self.average_attendance, 1),
            'stats': self.get_stats(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'age_days': self.age_days,
            'last_modified_days': self.last_modified_days
        }
    
    # ========================================================================
    # CLASS METHODS - QUERIES
    # ========================================================================
    
    @classmethod
    def search(cls, query: str) -> List["Organization"]:
        """Search organizations by name"""
        session = cls.session()
        search_term = f"%{query}%"
        return session.query(cls).filter(
            cls.display_name.ilike(search_term)
        ).all()
    
    @classmethod
    def by_contact(cls, contact: str) -> Optional["Organization"]:
        """Find organization by contact"""
        normalized = normalize_contact(contact)
        
        session = cls.session()
        orgs = session.query(cls).all()
        for org in orgs:
            for c in org.contacts:
                if normalize_contact(c.get('value', '')) == normalized:
                    return org
        return None
    
    @classmethod
    def top_by_attendance(cls, limit: int = 10) -> List["Organization"]:
        """Get top organizations by total attendance"""
        session = cls.session()
        orgs = session.query(cls).all()
        
        # Calculate attendance for each
        org_attendance = []
        for org in orgs:
            total = org.total_attendance
            if total > 0:
                org_attendance.append((org, total))
        
        # Sort and return top N
        org_attendance.sort(key=lambda x: x[1], reverse=True)
        return [org for org, _ in org_attendance[:limit]]
    
    @classmethod
    def top_by_tournament_count(cls, limit: int = 10) -> List["Organization"]:
        """Get top organizations by number of tournaments"""
        session = cls.session()
        orgs = session.query(cls).all()
        
        # Calculate count for each
        org_counts = []
        for org in orgs:
            count = org.tournament_count
            if count > 0:
                org_counts.append((org, count))
        
        # Sort and return top N
        org_counts.sort(key=lambda x: x[1], reverse=True)
        return [org for org, _ in org_counts[:limit]]
    
    @classmethod
    def active(cls) -> List["Organization"]:
        """Get organizations with recent or upcoming tournaments"""
        session = cls.session()
        orgs = session.query(cls).all()
        
        active_orgs = []
        for org in orgs:
            if org.get_upcoming_tournaments() or org.get_recent_tournaments(days=90):
                active_orgs.append(org)
        
        return active_orgs
    
    @classmethod
    def local(cls) -> List["Organization"]:
        """Get local organizations (single city)"""
        session = cls.session()
        orgs = session.query(cls).all()
        return [org for org in orgs if org.is_local_org()]
    
    @classmethod
    def regional(cls) -> List["Organization"]:
        """Get regional organizations (multiple cities)"""
        session = cls.session()
        orgs = session.query(cls).all()
        return [org for org in orgs if org.is_regional_org()]# ============================================================================
# PLAYER MODEL
# ============================================================================

class Player(Base, BaseModel, TimestampMixin, AnnouncerMixin):
    """Player in tournaments with comprehensive analytics and history"""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    startgg_id = Column(String, unique=True, index=True)  # start.gg player ID
    gamer_tag = Column(String, nullable=False)
    name = Column(String)  # Real name (if available)
    
    # Relationships
    placements = relationship("TournamentPlacement", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(tag='{self.gamer_tag}', id={self.startgg_id})>"
    
    def __str__(self):
        return self.gamer_tag
    
    def __eq__(self, other):
        """Enable equality comparison"""
        if not isinstance(other, Player):
            return NotImplemented
        return self.startgg_id == other.startgg_id
    
    def __lt__(self, other):
        """Enable sorting by gamer tag (alphabetical)"""
        if not isinstance(other, Player):
            return NotImplemented
        return self.gamer_tag.lower() < other.gamer_tag.lower()
    
    def __hash__(self):
        """Make players hashable for use in sets/dicts"""
        return hash((self.__class__.__name__, self.startgg_id))
    
    # ========================================================================
    # BASIC PROPERTIES
    # ========================================================================
    
    @property
    def display_name(self) -> str:
        """Get display name (real name if available, otherwise gamer tag)"""
        return self.name if self.name else self.gamer_tag
    
    @property
    def has_real_name(self) -> bool:
        """Check if we have the player's real name"""
        return bool(self.name)
    
    @property
    def tournament_count(self) -> int:
        """Count of unique tournaments participated in"""
        return len(set(p.tournament_id for p in self.placements))
    
    @property
    def total_placements(self) -> int:
        """Total number of placements (can be multiple per tournament)"""
        return len(self.placements)
    
    # ========================================================================
    # PLACEMENT AND RESULTS
    # ========================================================================
    
    @property
    def tournaments(self) -> List[Tournament]:
        """Get all tournaments this player participated in"""
        return list({p.tournament for p in self.placements})
    
    @property
    def tournaments_won(self) -> List[Tournament]:
        """Get tournaments this player won (1st place)"""
        return [p.tournament for p in self.placements if p.placement == 1]
    
    @property
    def win_count(self) -> int:
        """Number of tournament wins"""
        return len([p for p in self.placements if p.placement == 1])
    
    @property
    def podium_finishes(self) -> int:
        """Number of top 3 finishes"""
        return len([p for p in self.placements if p.placement <= 3])
    
    @property
    def top_8_finishes(self) -> int:
        """Number of top 8 finishes"""
        return len([p for p in self.placements if p.placement <= 8])
    
    def get_placement_distribution(self) -> Dict[int, int]:
        """Get distribution of placements"""
        distribution = Counter(p.placement for p in self.placements)
        return dict(sorted(distribution.items()))
    
    def get_best_placement(self) -> Optional[int]:
        """Get best placement ever achieved"""
        if not self.placements:
            return None
        return min(p.placement for p in self.placements)
    
    def get_worst_placement(self) -> Optional[int]:
        """Get worst placement"""
        if not self.placements:
            return None
        return max(p.placement for p in self.placements)
    
    def get_average_placement(self) -> float:
        """Calculate average placement"""
        if not self.placements:
            return 0.0
        return sum(p.placement for p in self.placements) / len(self.placements)
    
    def get_median_placement(self) -> Optional[int]:
        """Calculate median placement"""
        if not self.placements:
            return None
        placements = sorted(p.placement for p in self.placements)
        n = len(placements)
        if n % 2 == 0:
            return (placements[n//2 - 1] + placements[n//2]) // 2
        return placements[n//2]
    
    # ========================================================================
    # EARNINGS AND PRIZES
    # ========================================================================
    
    @property
    def total_earnings_cents(self) -> int:
        """Total prize money earned in cents"""
        return sum(p.prize_amount or 0 for p in self.placements)
    
    @property
    def total_earnings(self) -> float:
        """Total prize money earned in dollars"""
        return self.total_earnings_cents / 100.0
    
    def get_earnings_by_year(self) -> Dict[int, float]:
        """Get earnings broken down by year"""
        earnings = defaultdict(float)
        for p in self.placements:
            if p.tournament and p.tournament.start_date and p.prize_amount:
                year = p.tournament.start_date.year
                earnings[year] += p.prize_amount / 100.0
        return dict(earnings)
    
    def get_earnings_by_tournament(self) -> List[Tuple[str, float]]:
        """Get earnings by tournament"""
        earnings = []
        for p in self.placements:
            if p.prize_amount and p.prize_amount > 0:
                tournament_name = p.tournament.name if p.tournament else "Unknown"
                earnings.append((tournament_name, p.prize_amount / 100.0))
        return sorted(earnings, key=lambda x: x[1], reverse=True)
    
    def get_highest_earning(self) -> Optional[Tuple[str, float]]:
        """Get highest single tournament earning"""
        earnings = self.get_earnings_by_tournament()
        return earnings[0] if earnings else None
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate (percentage of tournaments won)"""
        if not self.placements:
            return 0.0
        wins = len([p for p in self.placements if p.placement == 1])
        return (wins / len(self.placements)) * 100
    
    @property
    def podium_rate(self) -> float:
        """Calculate podium finish rate (top 3)"""
        if not self.placements:
            return 0.0
        podiums = len([p for p in self.placements if p.placement <= 3])
        return (podiums / len(self.placements)) * 100
    
    @property
    def top_8_rate(self) -> float:
        """Calculate top 8 finish rate"""
        if not self.placements:
            return 0.0
        top8s = len([p for p in self.placements if p.placement <= 8])
        return (top8s / len(self.placements)) * 100
    
    def get_consistency_score(self) -> float:
        """Calculate consistency score based on placement variance"""
        if len(self.placements) < 2:
            return 0.0
        
        placements = [p.placement for p in self.placements]
        avg = sum(placements) / len(placements)
        variance = sum((p - avg) ** 2 for p in placements) / len(placements)
        
        # Lower variance = more consistent
        # Convert to 0-100 scale (100 = very consistent)
        return max(0, 100 - variance * 2)
    
    def get_improvement_trend(self) -> Optional[str]:
        """Analyze if player is improving, declining, or stable"""
        if len(self.placements) < 3:
            return None
        
        # Get recent placements sorted by date
        recent = sorted(self.placements, 
                       key=lambda p: p.tournament.end_at if p.tournament else 0)[-10:]
        
        if len(recent) < 3:
            return None
        
        # Compare first half to second half average
        mid = len(recent) // 2
        first_half_avg = sum(p.placement for p in recent[:mid]) / mid
        second_half_avg = sum(p.placement for p in recent[mid:]) / len(recent[mid:])
        
        # Lower placement number = better performance
        if second_half_avg < first_half_avg - 1:
            return "improving"
        elif second_half_avg > first_half_avg + 1:
            return "declining"
        else:
            return "stable"
    
    # ========================================================================
    # EVENT TYPE ANALYSIS
    # ========================================================================
    
    def get_singles_placements(self) -> List["TournamentPlacement"]:
        """Get singles event placements"""
        return [p for p in self.placements if p.is_singles]
    
    def get_doubles_placements(self) -> List["TournamentPlacement"]:
        """Get doubles/teams event placements"""
        return [p for p in self.placements if not p.is_singles]
    
    def get_event_breakdown(self) -> Dict[str, List["TournamentPlacement"]]:
        """Group placements by event name"""
        events = defaultdict(list)
        for p in self.placements:
            event = p.event_name or "Unknown Event"
            events[event].append(p)
        return dict(events)
    
    def get_best_event(self) -> Optional[str]:
        """Determine which event type the player performs best in"""
        event_stats = {}
        for event, placements in self.get_event_breakdown().items():
            if placements:
                avg_placement = sum(p.placement for p in placements) / len(placements)
                event_stats[event] = avg_placement
        
        if not event_stats:
            return None
        
        # Lower average placement is better
        return min(event_stats.items(), key=lambda x: x[1])[0]
    
    # ========================================================================
    # TEMPORAL ANALYSIS
    # ========================================================================
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tournament results"""
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
            'prize': p.prize_dollars,
            'attendees': p.tournament.num_attendees if p.tournament else None
        } for p in recent]
    
    def get_activity_by_year(self) -> Dict[int, Dict[str, Any]]:
        """Get activity statistics by year"""
        yearly = defaultdict(lambda: {
            'tournaments': 0,
            'wins': 0,
            'podiums': 0,
            'earnings': 0.0,
            'best_placement': None,
            'events': []
        })
        
        for p in self.placements:
            if p.tournament and p.tournament.start_date:
                year = p.tournament.start_date.year
                yearly[year]['tournaments'] += 1
                
                if p.placement == 1:
                    yearly[year]['wins'] += 1
                if p.placement <= 3:
                    yearly[year]['podiums'] += 1
                if p.prize_amount:
                    yearly[year]['earnings'] += p.prize_amount / 100.0
                
                if yearly[year]['best_placement'] is None or p.placement < yearly[year]['best_placement']:
                    yearly[year]['best_placement'] = p.placement
                
                yearly[year]['events'].append(p.tournament.name)
        
        return dict(yearly)
    
    def get_active_years(self) -> List[int]:
        """Get list of years the player was active"""
        years = set()
        for p in self.placements:
            if p.tournament and p.tournament.start_date:
                years.add(p.tournament.start_date.year)
        return sorted(years)
    
    def get_career_span_years(self) -> Optional[int]:
        """Get career span in years"""
        years = self.get_active_years()
        if len(years) < 2:
            return None
        return max(years) - min(years) + 1
    
    def is_active_player(self, days: int = 90) -> bool:
        """Check if player has been active recently"""
        for p in self.placements:
            if p.tournament and p.tournament.is_past and p.tournament.days_since():
                if p.tournament.days_since() <= days:
                    return True
        return False
    
    # ========================================================================
    # OPPONENT ANALYSIS
    # ========================================================================
    
    def get_common_opponents(self, min_encounters: int = 2) -> Dict[int, int]:
        """Get players frequently encountered in tournaments"""
        opponents = defaultdict(int)
        
        for p in self.placements:
            if p.tournament:
                # Get all other players in the same tournament/event
                for other_p in p.tournament.placements:
                    if other_p.player_id != self.id and other_p.event_id == p.event_id:
                        opponents[other_p.player_id] += 1
        
        # Filter to minimum encounters
        return {pid: count for pid, count in opponents.items() if count >= min_encounters}
    
    def get_head_to_head(self, other_player_id: int) -> Dict[str, Any]:
        """Get head-to-head statistics against another player"""
        other_player = Player.find(other_player_id)
        if not other_player:
            return {'error': 'Player not found'}
        
        # Find common tournaments/events
        my_placements = {(p.tournament_id, p.event_id): p for p in self.placements}
        other_placements = {(p.tournament_id, p.event_id): p for p in other_player.placements}
        
        common_events = set(my_placements.keys()) & set(other_placements.keys())
        
        wins = 0
        losses = 0
        encounters = []
        
        for event_key in common_events:
            my_p = my_placements[event_key]
            other_p = other_placements[event_key]
            
            if my_p.placement < other_p.placement:
                wins += 1
                result = 'W'
            else:
                losses += 1
                result = 'L'
            
            encounters.append({
                'tournament': my_p.tournament.name if my_p.tournament else 'Unknown',
                'event': my_p.event_name,
                'date': my_p.tournament.end_date.isoformat() if my_p.tournament and my_p.tournament.end_date else None,
                'my_placement': my_p.placement,
                'their_placement': other_p.placement,
                'result': result
            })
        
        # Sort by date
        encounters.sort(key=lambda x: x['date'] or '', reverse=True)
        
        return {
            'vs_player': other_player.gamer_tag,
            'vs_player_name': other_player.name,
            'total_encounters': len(encounters),
            'wins': wins,
            'losses': losses,
            'win_rate': round(wins / len(encounters) * 100, 1) if encounters else 0,
            'recent_encounters': encounters[:10],
            'first_encounter': encounters[-1] if encounters else None,
            'last_encounter': encounters[0] if encounters else None
        }
    
    def get_rivals(self, min_encounters: int = 3) -> List[Dict[str, Any]]:
        """Get rival players (frequently faced with close records)"""
        rivals = []
        
        for opponent_id, encounter_count in self.get_common_opponents(min_encounters).items():
            h2h = self.get_head_to_head(opponent_id)
            
            # Consider a rival if win rate is between 30-70%
            if 30 <= h2h['win_rate'] <= 70 and encounter_count >= min_encounters:
                rivals.append({
                    'player_id': opponent_id,
                    'gamer_tag': h2h['vs_player'],
                    'encounters': encounter_count,
                    'wins': h2h['wins'],
                    'losses': h2h['losses'],
                    'win_rate': h2h['win_rate']
                })
        
        # Sort by number of encounters
        return sorted(rivals, key=lambda x: x['encounters'], reverse=True)
    
    # ========================================================================
    # LOCATION ANALYSIS
    # ========================================================================
    
    def get_tournament_locations(self) -> List[str]:
        """Get list of locations where player has competed"""
        locations = set()
        for p in self.placements:
            if p.tournament and p.tournament.city:
                city = p.tournament.city_state
                locations.add(city)
        return sorted(locations)
    
    def get_home_region(self) -> Optional[str]:
        """Guess player's home region based on tournament frequency"""
        location_counts = defaultdict(int)
        
        for p in self.placements:
            if p.tournament and p.tournament.city:
                location_counts[p.tournament.city_state] += 1
        
        if not location_counts:
            return None
        
        # Most frequent location is likely home
        return max(location_counts.items(), key=lambda x: x[1])[0]
    
    def get_travel_distance(self) -> Optional[float]:
        """Calculate total approximate travel distance in km"""
        tournaments_with_loc = []
        for p in self.placements:
            if p.tournament and p.tournament.has_location:
                tournaments_with_loc.append(p.tournament)
        
        if len(tournaments_with_loc) < 2:
            return None
        
        # Sort by date
        tournaments_with_loc.sort(key=lambda t: t.start_at or 0)
        
        total_distance = 0
        for i in range(1, len(tournaments_with_loc)):
            prev = tournaments_with_loc[i-1]
            curr = tournaments_with_loc[i]
            if prev.coordinates and curr.coordinates:
                distance = prev.distance_to(*curr.coordinates)
                if distance:
                    total_distance += distance
        
        return total_distance
    
    # ========================================================================
    # COMPREHENSIVE STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this player"""
        return {
            # Basic info
            'gamer_tag': self.gamer_tag,
            'real_name': self.name,
            'startgg_id': self.startgg_id,
            
            # Tournament participation
            'total_tournaments': self.tournament_count,
            'total_placements': self.total_placements,
            'active_years': self.get_active_years(),
            'career_span_years': self.get_career_span_years(),
            'is_active': self.is_active_player(),
            
            # Results
            'wins': self.win_count,
            'podiums': self.podium_finishes,
            'top_8s': self.top_8_finishes,
            'best_placement': self.get_best_placement(),
            'worst_placement': self.get_worst_placement(),
            'average_placement': round(self.get_average_placement(), 2),
            'median_placement': self.get_median_placement(),
            'placement_distribution': self.get_placement_distribution(),
            
            # Performance metrics
            'win_rate': round(self.win_rate, 1),
            'podium_rate': round(self.podium_rate, 1),
            'top_8_rate': round(self.top_8_rate, 1),
            'consistency_score': round(self.get_consistency_score(), 1),
            'improvement_trend': self.get_improvement_trend(),
            
            # Earnings
            'total_earnings_cents': self.total_earnings_cents,
            'total_earnings_dollars': self.total_earnings,
            'earnings_by_year': self.get_earnings_by_year(),
            'highest_earning': self.get_highest_earning(),
            
            # Event breakdown
            'singles_placements': len(self.get_singles_placements()),
            'doubles_placements': len(self.get_doubles_placements()),
            'best_event': self.get_best_event(),
            'events_played': list(self.get_event_breakdown().keys()),
            
            # Location
            'locations_played': self.get_tournament_locations(),
            'home_region': self.get_home_region(),
            'travel_distance_km': self.get_travel_distance(),
            
            # Recent activity
            'recent_results': self.get_recent_results(5)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'startgg_id': self.startgg_id,
            'gamer_tag': self.gamer_tag,
            'name': self.name,
            'display_name': self.display_name,
            'stats': self.get_stats(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'age_days': self.age_days
        }
    
    # ========================================================================
    # CLASS METHODS - QUERIES
    # ========================================================================
    
    @classmethod
    def get_or_create(cls, startgg_id: str, gamer_tag: str, name: Optional[str] = None) -> "Player":
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
    
    @classmethod
    def search(cls, query: str) -> List["Player"]:
        """Search players by gamer tag or name"""
        session = cls.session()
        search_term = f"%{query}%"
        return session.query(cls).filter(
            (cls.gamer_tag.ilike(search_term)) |
            (cls.name.ilike(search_term))
        ).all()
    
    @classmethod
    def top_earners(cls, limit: int = 10) -> List["Player"]:
        """Get top players by prize money earned"""
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
    def most_wins(cls, limit: int = 10) -> List["Player"]:
        """Get players with most tournament wins"""
        session = cls.session()
        
        # Subquery to count wins
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
    def most_tournaments(cls, limit: int = 10) -> List["Player"]:
        """Get players who have played in the most tournaments"""
        session = cls.session()
        
        # Subquery to count unique tournaments
        tournament_subq = session.query(
            TournamentPlacement.player_id,
            func.count(func.distinct(TournamentPlacement.tournament_id)).label('tournament_count')
        ).group_by(TournamentPlacement.player_id).subquery()
        
        return session.query(cls).join(
            tournament_subq,
            cls.id == tournament_subq.c.player_id
        ).order_by(
            desc(tournament_subq.c.tournament_count)
        ).limit(limit).all()
    
    @classmethod
    def active_players(cls, days: int = 90) -> List["Player"]:
        """Get recently active players"""
        session = cls.session()
        players = session.query(cls).all()
        return [p for p in players if p.is_active_player(days)]
    
    @classmethod
    def elite_players(cls, min_wins: int = 5) -> List["Player"]:
        """Get elite players with minimum number of wins"""
        session = cls.session()
        players = session.query(cls).all()
        return [p for p in players if p.win_count >= min_wins]# ============================================================================
# TOURNAMENT PLACEMENT MODEL
# ============================================================================

class TournamentPlacement(Base, BaseModel):
    """Top placements in tournaments with detailed analytics"""
    __tablename__ = 'tournament_placements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(String, ForeignKey('tournaments.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    placement = Column(Integer, nullable=False)  # 1-8 for top 8, higher for others
    prize_amount = Column(Integer, default=0)  # Prize money in cents
    event_name = Column(String)  # Name of the specific event (e.g. "SF6 Singles")
    event_id = Column(String)  # start.gg event ID
    
    recorded_at = Column(DateTime, default=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="placements")
    player = relationship("Player", back_populates="placements")
    
    # Unique constraint per event
    __table_args__ = (
        Index('ix_tournament_player_event', tournament_id, player_id, event_id, unique=True),
    )
    
    def __repr__(self):
        event_info = f" ({self.event_name})" if self.event_name else ""
        player_tag = self.player.gamer_tag if self.player else 'Unknown'
        return f"<Placement(tournament={self.tournament_id}, player={player_tag}, place={self.placement}{event_info})>"
    
    def __str__(self):
        return f"{self.placement}. {self.player.gamer_tag if self.player else 'Unknown'}"
    
    # ========================================================================
    # BASIC PROPERTIES
    # ========================================================================
    
    @property
    def prize_dollars(self) -> float:
        """Prize amount in dollars"""
        return self.prize_amount / 100.0 if self.prize_amount else 0.0
    
    @property
    def is_singles(self) -> bool:
        """Check if this is a singles event"""
        if not self.event_name:
            return True  # Default assumption
        
        event_name = self.event_name.lower()
        # Check for doubles/teams indicators
        doubles_keywords = ['doubles', 'teams', 'crew', '2v2', '3v3', 'tag', 'duo', 'squad']
        return not any(keyword in event_name for keyword in doubles_keywords)
    
    @property
    def is_win(self) -> bool:
        """Check if this is a tournament win"""
        return self.placement == 1
    
    @property
    def is_podium(self) -> bool:
        """Check if this is a podium finish (top 3)"""
        return self.placement <= 3
    
    @property
    def is_top_8(self) -> bool:
        """Check if this is a top 8 finish"""
        return self.placement <= 8
    
    def get_placement_name(self) -> str:
        """Get human-readable placement name"""
        placements = {
            1: "1st (Winner)",
            2: "2nd",
            3: "3rd",
            4: "4th",
            5: "5th-6th",
            6: "5th-6th",
            7: "7th-8th",
            8: "7th-8th"
        }
        
        if self.placement in placements:
            return placements[self.placement]
        elif self.placement <= 12:
            return f"9th-12th"
        elif self.placement <= 16:
            return f"13th-16th"
        else:
            return f"{self.placement}th"
    
    def get_points(self, system: str = "standard") -> int:
        """Calculate points based on placement - USES CENTRALIZED POINTS SYSTEM"""
        from points_system import PointsSystem
        
        # ALL systems now use the centralized points system
        # This ensures single source of truth
        return PointsSystem.get_points_for_placement(self.placement)
    
    # ========================================================================
    # TOURNAMENT CONTEXT
    # ========================================================================
    
    def get_tournament_size(self) -> Optional[int]:
        """Get the size of the tournament"""
        if self.tournament:
            return self.tournament.num_attendees
        return None
    
    def get_placement_percentage(self) -> Optional[float]:
        """Get placement as percentage of field"""
        size = self.get_tournament_size()
        if size and size > 0:
            return (self.placement / size) * 100
        return None
    
    def get_players_beaten(self) -> Optional[int]:
        """Calculate number of players beaten"""
        size = self.get_tournament_size()
        if size:
            return size - self.placement
        return None
    
    def is_major_placement(self) -> bool:
        """Check if this is a placement at a major tournament"""
        return self.tournament and self.tournament.is_major()
    
    def is_premier_placement(self) -> bool:
        """Check if this is a placement at a premier tournament"""
        return self.tournament and self.tournament.is_premier()
    
    def get_tournament_date(self) -> Optional[datetime]:
        """Get the date of the tournament"""
        if self.tournament:
            return self.tournament.end_date
        return None
    
    # ========================================================================
    # OPPONENT ANALYSIS
    # ========================================================================
    
    def get_other_placements(self) -> List["TournamentPlacement"]:
        """Get other placements in the same event"""
        if not self.tournament:
            return []
        
        return [p for p in self.tournament.placements 
                if p.event_id == self.event_id and p.id != self.id]
    
    def get_players_above(self) -> List["Player"]:
        """Get players who placed above this placement"""
        others = self.get_other_placements()
        return [p.player for p in others if p.placement < self.placement and p.player]
    
    def get_players_below(self) -> List["Player"]:
        """Get players who placed below this placement"""
        others = self.get_other_placements()
        return [p.player for p in others if p.placement > self.placement and p.player]
    
    def get_closest_rivals(self, range: int = 2) -> List["TournamentPlacement"]:
        """Get placements within a certain range"""
        others = self.get_other_placements()
        return [p for p in others 
                if abs(p.placement - self.placement) <= range and p.id != self.id]
    
    def beat_player(self, player_id: int) -> bool:
        """Check if this placement beat a specific player"""
        others = self.get_other_placements()
        for p in others:
            if p.player_id == player_id:
                return self.placement < p.placement
        return False
    
    # ========================================================================
    # VALUE AND QUALITY METRICS
    # ========================================================================
    
    def get_quality_score(self) -> float:
        """Calculate quality score based on placement and tournament size"""
        if not self.tournament:
            return 0.0
        
        # Base score from placement
        placement_score = 100 / self.placement if self.placement > 0 else 0
        
        # Weight by tournament size
        size_multiplier = 1.0
        if self.tournament.num_attendees:
            if self.tournament.num_attendees >= 500:
                size_multiplier = 3.0
            elif self.tournament.num_attendees >= 200:
                size_multiplier = 2.0
            elif self.tournament.num_attendees >= 100:
                size_multiplier = 1.5
            elif self.tournament.num_attendees >= 50:
                size_multiplier = 1.2
        
        return placement_score * size_multiplier
    
    def get_prize_percentage(self) -> Optional[float]:
        """Get prize as percentage of total tournament prize pool"""
        if not self.tournament or not self.prize_amount:
            return None
        
        total_prize = sum(p.prize_amount or 0 for p in self.tournament.placements)
        if total_prize > 0:
            return (self.prize_amount / total_prize) * 100
        return None
    
    def get_relative_performance(self) -> Optional[str]:
        """Categorize performance relative to tournament size"""
        percentage = self.get_placement_percentage()
        if not percentage:
            return None
        
        if percentage <= 1:
            return "elite"  # Top 1%
        elif percentage <= 5:
            return "excellent"  # Top 5%
        elif percentage <= 10:
            return "great"  # Top 10%
        elif percentage <= 25:
            return "good"  # Top 25%
        elif percentage <= 50:
            return "average"  # Top 50%
        else:
            return "below_average"
    
    # ========================================================================
    # COMPARISON METHODS
    # ========================================================================
    
    def is_better_than(self, other: "TournamentPlacement") -> bool:
        """Compare if this placement is better than another"""
        # First compare by placement number
        if self.placement != other.placement:
            return self.placement < other.placement
        
        # If same placement, compare by tournament size
        my_size = self.get_tournament_size() or 0
        other_size = other.get_tournament_size() or 0
        
        return my_size > other_size
    
    def compare_to(self, other: "TournamentPlacement") -> Dict[str, Any]:
        """Detailed comparison with another placement"""
        return {
            'better': self.is_better_than(other),
            'my_placement': self.placement,
            'their_placement': other.placement,
            'my_tournament': self.tournament.name if self.tournament else None,
            'their_tournament': other.tournament.name if other.tournament else None,
            'my_tournament_size': self.get_tournament_size(),
            'their_tournament_size': other.get_tournament_size(),
            'my_prize': self.prize_dollars,
            'their_prize': other.prize_dollars,
            'my_quality_score': self.get_quality_score(),
            'their_quality_score': other.get_quality_score()
        }
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this placement"""
        return {
            'placement': self.placement,
            'placement_name': self.get_placement_name(),
            'event': self.event_name,
            'event_id': self.event_id,
            'is_singles': self.is_singles,
            'is_win': self.is_win,
            'is_podium': self.is_podium,
            'is_top_8': self.is_top_8,
            
            # Tournament context
            'tournament': self.tournament.name if self.tournament else None,
            'tournament_id': self.tournament_id,
            'tournament_size': self.get_tournament_size(),
            'tournament_date': self.get_tournament_date().isoformat() if self.get_tournament_date() else None,
            'is_major': self.is_major_placement(),
            'is_premier': self.is_premier_placement(),
            
            # Performance metrics
            'placement_percentage': self.get_placement_percentage(),
            'players_beaten': self.get_players_beaten(),
            'relative_performance': self.get_relative_performance(),
            'quality_score': round(self.get_quality_score(), 2),
            
            # Prize
            'prize_cents': self.prize_amount,
            'prize_dollars': self.prize_dollars,
            'prize_percentage': self.get_prize_percentage(),
            
            # Points
            'points_standard': self.get_points('standard'),
            'points_evo': self.get_points('evo'),
            
            # Player info
            'player': self.player.gamer_tag if self.player else None,
            'player_id': self.player_id,
            
            # Metadata
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'tournament_name': self.tournament.name if self.tournament else None,
            'player_id': self.player_id,
            'player_tag': self.player.gamer_tag if self.player else None,
            'placement': self.placement,
            'placement_name': self.get_placement_name(),
            'event_name': self.event_name,
            'event_id': self.event_id,
            'prize_dollars': self.prize_dollars,
            'is_singles': self.is_singles,
            'is_win': self.is_win,
            'is_podium': self.is_podium,
            'quality_score': round(self.get_quality_score(), 2),
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    # ========================================================================
    # CLASS METHODS - QUERIES
    # ========================================================================
    
    @classmethod
    def wins(cls) -> List["TournamentPlacement"]:
        """Get all tournament wins"""
        session = cls.session()
        return session.query(cls).filter(cls.placement == 1).all()
    
    @classmethod
    def podiums(cls) -> List["TournamentPlacement"]:
        """Get all podium finishes"""
        session = cls.session()
        return session.query(cls).filter(cls.placement <= 3).all()
    
    @classmethod
    def top_8s(cls) -> List["TournamentPlacement"]:
        """Get all top 8 finishes"""
        session = cls.session()
        return session.query(cls).filter(cls.placement <= 8).all()
    
    @classmethod
    def by_event(cls, event_name: str) -> List["TournamentPlacement"]:
        """Get placements for a specific event"""
        session = cls.session()
        return session.query(cls).filter(cls.event_name == event_name).all()
    
    @classmethod
    def by_tournament(cls, tournament_id: str) -> List["TournamentPlacement"]:
        """Get all placements for a tournament"""
        session = cls.session()
        return session.query(cls).filter(
            cls.tournament_id == tournament_id
        ).order_by(cls.placement).all()
    
    @classmethod
    def by_player(cls, player_id: int) -> List["TournamentPlacement"]:
        """Get all placements for a player"""
        session = cls.session()
        return session.query(cls).filter(
            cls.player_id == player_id
        ).order_by(cls.placement).all()
    
    @classmethod
    def recent(cls, days: int = 30) -> List["TournamentPlacement"]:
        """Get recent placements"""
        session = cls.session()
        cutoff = datetime.now() - timedelta(days=days)
        
        return session.query(cls).join(Tournament).filter(
            Tournament.end_at >= cutoff.timestamp()
        ).order_by(desc(Tournament.end_at)).all()
    
    @classmethod
    def highest_prizes(cls, limit: int = 10) -> List["TournamentPlacement"]:
        """Get placements with highest prizes"""
        session = cls.session()
        return session.query(cls).filter(
            cls.prize_amount > 0
        ).order_by(desc(cls.prize_amount)).limit(limit).all()
    
    @classmethod
    def at_majors(cls) -> List["TournamentPlacement"]:
        """Get placements at major tournaments"""
        session = cls.session()
        return session.query(cls).join(Tournament).filter(
            Tournament.num_attendees >= 100
        ).all()
    
    @classmethod
    def singles_only(cls) -> List["TournamentPlacement"]:
        """Get singles event placements only"""
        session = cls.session()
        all_placements = session.query(cls).all()
        return [p for p in all_placements if p.is_singles]
    
    @classmethod
    def doubles_only(cls) -> List["TournamentPlacement"]:
        """Get doubles/teams event placements only"""
        session = cls.session()
        all_placements = session.query(cls).all()
        return [p for p in all_placements if not p.is_singles]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_contact(contact: str) -> Optional[str]:
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

def get_display_name_from_contact(contact: str) -> str:
    """Get display name from contact"""
    if not contact:
        return "Unknown"
    
    # If it's not email or discord, use as display name
    if '@' not in contact and 'discord' not in contact.lower():
        return contact
    
    return contact

def determine_contact_type(contact: str) -> str:
    """Determine contact type"""
    if not contact:
        return 'unknown'
    contact = contact.lower()
    
    if '@' in contact:
        return 'email'
    elif 'discord' in contact:
        return 'discord'
    elif contact.startswith('http'):
        return 'website'
    elif contact.replace(' ', '').replace('-', '').isdigit():
        return 'phone'
    else:
        return 'name'