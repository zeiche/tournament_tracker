"""
Compatibility layer - re-exports core announcer functionality.
Provides model-specific announcement helpers for legacy code.
"""

from polymorphic_core import announcer, announces_capability

__all__ = ['announcer', 'announces_capability', 'get_full_context']

def get_full_context():
    """
    Get all announcements for Claude - legacy function for Discord bot.
    """
    return announcer.get_announcements_for_claude()