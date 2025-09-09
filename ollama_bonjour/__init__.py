#!/usr/bin/env python3
"""
Ollama Bonjour - Complete integration of Ollama LLM with Bonjour service discovery

This module provides:
- OllamaBonjour: Main service that understands Bonjour announcements
- ServiceMemory: Persistent memory of discovered services
- BonjourBridge: Real-time bridge between announcements and intelligence
- BonjourRouter: Natural language routing to services
"""

from .ollama_service import OllamaBonjour, get_ollama_bonjour
from .service_memory import ServiceMemory, ServicePatternMatcher
from .bonjour_bridge import BonjourBridge, BonjourRouter, run_bridge

__all__ = [
    'OllamaBonjour',
    'get_ollama_bonjour',
    'ServiceMemory',
    'ServicePatternMatcher',
    'BonjourBridge',
    'BonjourRouter',
    'run_bridge'
]

# Module metadata
__version__ = '1.0.0'
__author__ = 'Tournament Tracker'
__description__ = "Claude's little brother - offline intelligence for Bonjour services"