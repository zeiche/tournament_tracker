#!/usr/bin/env python3
"""
events.py - Pure mDNS Service Discovery
Real network discovery only. No fake announcements, no local registry.
Services discover each other via actual Bonjour protocol.
"""

from .real_bonjour import RealBonjourAnnouncer

# Pure mDNS - no compromises
announcer = RealBonjourAnnouncer()
CapabilityAnnouncer = RealBonjourAnnouncer

def announces_capability(service_name: str, *capabilities):
    """Decorator for announcing capabilities via real mDNS only"""
    def decorator(obj):
        announcer.announce(service_name, list(capabilities))
        return obj
    return decorator

__all__ = ['announcer', 'CapabilityAnnouncer', 'announces_capability']

print("🌐 Using PURE mDNS Service Discovery - real network only!")