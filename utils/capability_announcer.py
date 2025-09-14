"""
Compatibility layer - re-exports core announcer functionality.
Provides model-specific announcement helpers for legacy code.
"""

from polymorphic_core import announcer, announces_capability

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.capability_announcer")

__all__ = ['announcer', 'announces_capability', 'get_full_context']

def get_full_context():
    """
    Get all announcements for Claude - legacy function for Discord bot.
    """
    return announcer.get_announcements_for_claude()