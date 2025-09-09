#!/usr/bin/env python3
"""
Intelligence Module - Offline AI capabilities for the tournament tracker
Provides local intelligence that can understand Bonjour announcements and services
"""

from .base_intelligence import BaseIntelligence
from .ollama_intelligence import OllamaIntelligence
from .mistral_intelligence import MistralIntelligence
from .pattern_intelligence import PatternIntelligence

# Export the main interface
__all__ = [
    'BaseIntelligence',
    'OllamaIntelligence', 
    'MistralIntelligence',
    'PatternIntelligence',
    'get_intelligence'
]

def get_intelligence(backend='auto'):
    """
    Factory function to get the best available intelligence backend
    
    Args:
        backend: 'ollama', 'mistral', 'pattern', or 'auto'
        
    Returns:
        Intelligence instance
    """
    if backend == 'auto':
        # Try backends in order of preference
        try:
            return MistralIntelligence()
        except Exception:
            pass
        
        try:
            return OllamaIntelligence()
        except Exception:
            pass
        
        # Fallback to pattern matching
        return PatternIntelligence()
    
    elif backend == 'mistral':
        return MistralIntelligence()
    elif backend == 'ollama':
        return OllamaIntelligence()
    elif backend == 'pattern':
        return PatternIntelligence()
    else:
        raise ValueError(f"Unknown backend: {backend}")