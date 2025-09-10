#!/usr/bin/env python3
"""
events.py - Real Bonjour/mDNS network discovery
All fake announcements stripped - only real network discovery remains.
"""

from .real_bonjour import RealBonjourAnnouncer

# Global real mDNS announcer - no more fake fallback
announcer = RealBonjourAnnouncer()
CapabilityAnnouncer = RealBonjourAnnouncer

def announces_capability(service_name: str, *capabilities):
    """Decorator for auto-announcing capabilities via real mDNS"""
    def decorator(obj):
        announcer.announce(service_name, list(capabilities))
        return obj
    return decorator

# Exports - only real Bonjour
__all__ = ['announcer', 'CapabilityAnnouncer', 'announces_capability']

print("🎉 Using REAL Bonjour/mDNS only - fake announcements stripped!")