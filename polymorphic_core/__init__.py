"""
polymorphic_core - General purpose polymorphic infrastructure
This has nothing to do with tournaments - it's pure polymorphic patterns.
"""

from .events import announcer, announces_capability
from .discovery import register_capability, discover_capability, list_capabilities, get_capability_info
from .process import ProcessManager
from . import process_management_guide  # Import to trigger announcements

__all__ = [
    'announcer', 
    'register_capability',
    'discover_capability',
    'announces_capability',
    'list_capabilities',
    'get_capability_info',
    'ProcessManager'
]