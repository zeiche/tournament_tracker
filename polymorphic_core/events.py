#!/usr/bin/env python3
"""
events.py - Hybrid Service Discovery
Fast local announcements + Real network discovery where appropriate.
Smart routing based on service characteristics.
"""

from .hybrid_announcer import HybridAnnouncer, announcer, CapabilityAnnouncer, announces_capability

# Export everything from hybrid announcer
__all__ = ['announcer', 'CapabilityAnnouncer', 'announces_capability']

print("🎯 Using Hybrid Service Discovery - fast local + real network!")