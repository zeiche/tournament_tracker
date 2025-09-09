"""
Claude Services - Core Claude implementations
"""

from .claude_bonjour_service import claude_bonjour, ask_claude_with_discovery

# Legacy service - only import when needed to avoid initialization
# from .claude_service import claude_service, ask_claude

__all__ = [
    'claude_bonjour',
    'ask_claude_with_discovery'
]