"""
Claude - AI Assistant with Bonjour Discovery

This module provides Claude's capabilities:
- Dynamic service discovery via Bonjour
- Natural language understanding and routing
- Conversation management
- Service-to-service communication
"""

from .services.claude_bonjour_service import (
    claude_bonjour,
    ask_claude_with_discovery,
    get_claude_capabilities,
    ClaudeBonjourService
)

# For backwards compatibility - lazy import to avoid initialization
# Only import when explicitly needed
def _get_legacy_claude():
    from .services.claude_service import claude_service
    return claude_service

# Legacy functions - will import on first use
def ask_claude(*args, **kwargs):
    from .services.claude_service import ask_claude as legacy_ask
    return legacy_ask(*args, **kwargs)

def is_claude_enabled():
    from .services.claude_service import is_claude_enabled as legacy_enabled
    return legacy_enabled()

__all__ = [
    # New bonjour-enhanced
    'claude_bonjour',
    'ask_claude_with_discovery', 
    'get_claude_capabilities',
    'ClaudeBonjourService',
    
    # Legacy compatibility
    'ask_claude',
    'is_claude_enabled'
]