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

# For backwards compatibility
from .services.claude_service import (
    claude_service,
    ask_claude,
    is_claude_enabled,
    ClaudeService
)

__all__ = [
    # New bonjour-enhanced
    'claude_bonjour',
    'ask_claude_with_discovery', 
    'get_claude_capabilities',
    'ClaudeBonjourService',
    
    # Legacy compatibility
    'claude_service',
    'ask_claude',
    'is_claude_enabled',
    'ClaudeService'
]