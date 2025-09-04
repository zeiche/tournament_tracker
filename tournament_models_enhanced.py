"""
tournament_models_enhanced.py - Fully object-oriented SQLAlchemy models
Every model exposes all its data through methods and properties in a Pythonic way
"""
import re
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple, Dict, Any, Set
from collections import defaultdict, Counter
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index, Float, Boolean, func, desc, asc
from sqlalchemy.orm import declarative_base, relationship, Query
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.sql import func

# Import centralized session management
from database_utils import Session, get_session
from log_utils import log_debug, log_info, log_error

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
        except:
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
        except:
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
            from database_utils import get_session
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
    def in_socal(cls) -> Query:
        """Query filter to get objects in Southern California"""
        return cls.in_region(32.5, 34.5, -119.0, -116.0)
    
    @classmethod
    def in_city(cls, city: str, state: Optional[str] = None) -> Query:
        """Query filter to get objects in a specific city"""
        if hasattr(cls, 'session'):
            session = cls.session()
        else:
            from database_utils import get_session
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
        """Update attributes and save"""
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

class Tournament(Base, BaseModel, LocationMixin, TimestampMixin):
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
    
    @property
    def organization(self) -> Optional["Organization"]:
        """Get the organization that runs this tournament"""
        if not self.primary_contact:
            return None
        from database_utils import normalize_contact
        normalized = normalize_contact(self.primary_contact)
        
        session = self.session()
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
        from database_utils import normalize_contact
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
# (This is getting long, should I continue with the rest?)