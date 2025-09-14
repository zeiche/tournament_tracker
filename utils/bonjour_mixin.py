#!/usr/bin/env python3
"""
bonjour_mixin.py - Base mixin for all models to announce themselves
Every model that inherits this will automatically announce its state changes.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from polymorphic_core import announcer

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.bonjour_mixin")


class AnnouncerMixin:
    """
    Mixin that makes any class announce itself like a Bonjour service.
    Add this to any model class to make it self-announcing.
    """
    
    def __init__(self, *args, **kwargs):
        """Override init to announce creation"""
        super().__init__(*args, **kwargs)
        self._announce_creation()
    
    def _announce_creation(self):
        """Announce when this object is created"""
        class_name = self.__class__.__name__
        
        # Build capabilities from class methods and properties
        capabilities = self._discover_capabilities()
        
        # Announce existence
        announcer.announce(
            f"{class_name} Instance",
            [f"New {class_name} created with id: {getattr(self, 'id', 'unknown')}"] + capabilities,
            self._get_example_usage()
        )
    
    def _discover_capabilities(self) -> List[str]:
        """Introspect to find what this object can do"""
        capabilities = []
        class_name = self.__class__.__name__
        
        # Check for common model capabilities
        if hasattr(self, 'id'):
            capabilities.append(f"Has unique identifier: {self.id}")
        
        if hasattr(self, 'name'):
            capabilities.append(f"Named: {getattr(self, 'name', 'unnamed')}")
            
        if hasattr(self, 'created_at'):
            capabilities.append("Tracks creation timestamp")
            
        if hasattr(self, 'updated_at'):
            capabilities.append("Tracks modification timestamp")
        
        # Tournament-specific
        if class_name == 'Tournament':
            if hasattr(self, 'num_attendees'):
                capabilities.append(f"Tracks {self.num_attendees} attendees")
            if hasattr(self, 'venue_name'):
                capabilities.append(f"Located at {self.venue_name}")
            if hasattr(self, 'start_date'):
                capabilities.append(f"Scheduled for {self.start_date}")
                
        # Player-specific
        elif class_name == 'Player':
            if hasattr(self, 'placements'):
                capabilities.append(f"Has {len(self.placements)} tournament placements")
            if hasattr(self, 'wins'):
                capabilities.append(f"Won {self.wins} tournaments")
                
        # Organization-specific
        elif class_name == 'Organization':
            if hasattr(self, 'tournaments'):
                capabilities.append(f"Hosted {len(self.tournaments)} events")
            if hasattr(self, 'contacts'):
                capabilities.append(f"Has {len(self.contacts)} contact methods")
        
        return capabilities
    
    def _get_example_usage(self) -> List[str]:
        """Get example usage for this type of object"""
        class_name = self.__class__.__name__
        
        if class_name == 'Tournament':
            return [
                f"tournament.ask('who won')",
                f"tournament.tell('discord')",
                f"tournament.do('sync')"
            ]
        elif class_name == 'Player':
            return [
                f"player.ask('win rate')",
                f"player.tell('brief')",
                f"player.do('calculate_points')"
            ]
        elif class_name == 'Organization':
            return [
                f"org.ask('total events')",
                f"org.tell('json')",
                f"org.do('merge')"
            ]
        return []
    
    def announce_state_change(self, what_changed: str, details: Optional[Dict] = None):
        """Call this whenever the object's state changes"""
        class_name = self.__class__.__name__
        object_id = getattr(self, 'id', 'unknown')
        
        announcement = [f"{class_name} {object_id}: {what_changed}"]
        if details:
            for key, value in details.items():
                announcement.append(f"  {key}: {value}")
        
        announcer.announce(
            f"{class_name} State Change",
            announcement
        )
    
    def announce_error(self, operation: str, error: Exception):
        """Announce when an error occurs"""
        class_name = self.__class__.__name__
        object_id = getattr(self, 'id', 'unknown')
        
        announcer.announce(
            f"{class_name} Error",
            [
                f"Error in {class_name} {object_id}",
                f"Operation: {operation}",
                f"Error: {str(error)}"
            ]
        )
    
    def announce_operation(self, operation: str, result: Any = None):
        """Announce when an operation completes"""
        class_name = self.__class__.__name__
        object_id = getattr(self, 'id', 'unknown')
        
        announcement = [f"{class_name} {object_id} completed: {operation}"]
        if result is not None:
            announcement.append(f"Result: {result}")
        
        announcer.announce(
            f"{class_name} Operation",
            announcement
        )
    
    # Override common SQLAlchemy lifecycle methods to announce
    def before_insert(self):
        """Called before inserting into database"""
        self.announce_state_change("being inserted into database")
        if hasattr(super(), 'before_insert'):
            super().before_insert()
    
    def after_insert(self):
        """Called after inserting into database"""
        self.announce_state_change("inserted into database", {"id": getattr(self, 'id', None)})
        if hasattr(super(), 'after_insert'):
            super().after_insert()
    
    def before_update(self):
        """Called before updating in database"""
        self.announce_state_change("being updated in database")
        if hasattr(super(), 'before_update'):
            super().before_update()
    
    def after_update(self):
        """Called after updating in database"""
        self.announce_state_change("updated in database")
        if hasattr(super(), 'after_update'):
            super().after_update()
    
    def before_delete(self):
        """Called before deleting from database"""
        self.announce_state_change("being deleted from database")
        if hasattr(super(), 'before_delete'):
            super().before_delete()
    
    def after_delete(self):
        """Called after deleting from database"""
        self.announce_state_change("deleted from database")
        if hasattr(super(), 'after_delete'):
            super().after_delete()


class ServiceAnnouncerMixin:
    """
    Mixin for services (Discord bot, web server, etc) to announce their status.
    """
    
    def __init__(self, service_name: str, *args, **kwargs):
        """Initialize service with announcements"""
        super().__init__(*args, **kwargs)
        self.service_name = service_name
        self._announce_service_start()
    
    def _announce_service_start(self):
        """Announce service startup"""
        announcer.announce(
            f"{self.service_name} Service",
            [
                f"{self.service_name} is starting up",
                f"Process ID: {self._get_pid()}",
                f"Status: initializing"
            ]
        )
    
    def _get_pid(self) -> int:
        """Get current process ID"""
        import os
        return os.getpid()
    
    def announce_ready(self, details: Optional[Dict] = None):
        """Announce when service is ready"""
        announcement = [
            f"{self.service_name} is ready",
            f"Status: active"
        ]
        
        if details:
            for key, value in details.items():
                announcement.append(f"{key}: {value}")
        
        announcer.announce(f"{self.service_name} Ready", announcement)
    
    def announce_connection(self, connection_type: str, details: str):
        """Announce new connections"""
        announcer.announce(
            f"{self.service_name} Connection",
            [
                f"New {connection_type} connection",
                details
            ]
        )
    
    def announce_request(self, request_type: str, details: str):
        """Announce incoming requests"""
        announcer.announce(
            f"{self.service_name} Request",
            [
                f"Handling {request_type} request",
                details
            ]
        )
    
    def announce_error(self, error: Exception, context: str = ""):
        """Announce service errors"""
        announcer.announce(
            f"{self.service_name} Error",
            [
                f"Error in {self.service_name}",
                f"Context: {context}" if context else "General error",
                f"Error: {str(error)}"
            ]
        )
    
    def announce_shutdown(self):
        """Announce service shutdown"""
        announcer.announce(
            f"{self.service_name} Shutdown",
            [
                f"{self.service_name} is shutting down",
                f"Process ID: {self._get_pid()}",
                "Status: stopping"
            ]
        )