#!/usr/bin/env python3
"""
mixins.py - Reusable mixins for all models

These provide common functionality like timestamps, locations, etc.
Each mixin uses the polymorphic pattern internally.
"""

from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from sqlalchemy import Column, DateTime, Float, String, func


class TimestampMixin:
    """Adds created_at and updated_at timestamps to any model"""
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def ask_timestamp(self, question: str) -> Any:
        """Handle timestamp-related questions"""
        q = str(question).lower()
        
        if 'age' in q or 'old' in q:
            if not self.created_at:
                return 0
            delta = datetime.now() - self.created_at
            return delta.days
        
        if 'modified' in q or 'updated' in q:
            if not self.updated_at:
                return 0
            delta = datetime.now() - self.updated_at
            return delta.days
        
        if 'when' in q and 'created' in q:
            return self.created_at
        
        if 'when' in q and 'updated' in q:
            return self.updated_at
        
        return None


class LocationMixin:
    """Adds geographic location fields to any model"""
    
    lat = Column(Float)
    lng = Column(Float)
    venue_name = Column(String)
    venue_address = Column(String)
    city = Column(String)
    addr_state = Column(String)
    country_code = Column(String)
    postal_code = Column(String)
    
    def ask_location(self, question: str) -> Any:
        """Handle location-related questions"""
        q = str(question).lower()
        
        if 'coordinates' in q or 'coords' in q:
            if self.lat and self.lng:
                return (float(self.lat), float(self.lng))
            return None
        
        if 'address' in q:
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
            return ', '.join(filter(None, parts)) if parts else "No address"
        
        if 'city' in q:
            if self.city and self.addr_state:
                return f"{self.city}, {self.addr_state}"
            return self.city or "Unknown city"
        
        if 'venue' in q:
            return self.venue_name or "Unknown venue"
        
        if 'has' in q and 'location' in q:
            return self.lat is not None and self.lng is not None
        
        return None
    
    def tell_location(self, format: str) -> Any:
        """Format location data"""
        if format == "json":
            return {
                'lat': self.lat,
                'lng': self.lng,
                'venue_name': self.venue_name,
                'city': self.city,
                'state': self.addr_state,
                'coordinates': (self.lat, self.lng) if self.lat and self.lng else None
            }
        
        if format == "brief":
            return self.city or "Unknown location"
        
        return f"{self.venue_name or 'Unknown'} in {self.city or 'Unknown'}"