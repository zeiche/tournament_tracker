#!/usr/bin/env python3
"""
events.py - Real mDNS Service Discovery
Network service discovery via mDNS/Bonjour.
Services discover each other across the network.
"""

from .real_bonjour import announcer as real_announcer

# Real mDNS bonjour for everything
announcer = real_announcer

def announces_capability(service_name: str, *capabilities):
    """Decorator for announcing capabilities via real mDNS"""
    def decorator(obj):
        real_announcer.announce(service_name, list(capabilities))
        return obj
    return decorator

__all__ = ['announcer', 'announces_capability']

print("🌐 Using REAL mDNS Service Discovery - network broadcasting enabled!")