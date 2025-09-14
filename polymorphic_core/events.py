#!/usr/bin/env python3
"""
events.py - Local Bonjour Service Discovery
Process-local service discovery. No network overhead.
Services discover each other via in-memory announcements.
"""

from .local_bonjour import local_announcer

# Local bonjour for everything
announcer = local_announcer

def announces_capability(service_name: str, *capabilities):
    """Decorator for announcing capabilities via local bonjour only"""
    def decorator(obj):
        local_announcer.announce(service_name, list(capabilities))
        return obj
    return decorator

__all__ = ['announcer', 'announces_capability']

print("🏠 Using LOCAL Bonjour Service Discovery - process-local only!")