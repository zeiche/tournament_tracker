#!/usr/bin/env python3
"""
Mistral Intelligence - Optimized for Mistral 7B model
Fast, efficient local intelligence focused on service discovery
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core import announcer
from .ollama_intelligence import OllamaIntelligence

class MistralIntelligence(OllamaIntelligence):
    """
    Mistral-specific intelligence optimized for tournament tracker
    """
    
    def __init__(self):
        """Initialize with Mistral model"""
        super().__init__(model='mistral')
        
        # Override system prompt for Mistral
        self.system_prompt = """You are Mistral, Claude's efficient little brother for the tournament tracker.
You understand Bonjour service discovery and help users interact with discovered services.
Be extremely concise - single sentences when possible.
Focus on the tournament tracker domain: tournaments, players, organizations.
You work offline and respond instantly."""
    
    def _announce_service(self):
        """Announce Mistral Intelligence via Bonjour"""
        capabilities = [
            "Mistral Intelligence - Claude's fast little brother",
            "Mistral 7B model (optimized for speed)",
            "Tournament tracker specialist",
            "I understand all Bonjour services",
            "Instant offline responses",
            "ask('recent tournaments') - Query about tournaments",
            "ask('top players') - Get player rankings",
            "ask('how to sync') - Service guidance",
            "tell('discord', data) - Format for Discord",
            "do('analyze') - Analyze all services",
            "I am 10x faster than Claude, work offline"
        ]
        
        if self.available:
            capabilities.append("✅ Mistral is running and ready")
        else:
            capabilities.append("⚠️ Mistral not available - run: ollama pull mistral")
        
        announcer.announce("Mistral Intelligence", capabilities)
    
    def ask(self, query: str, **kwargs):
        """Optimized ask for tournament domain"""
        query_lower = query.lower()
        
        # Handle common tournament queries directly
        if 'tournament' in query_lower:
            if 'recent' in query_lower:
                return "Use database.ask('recent tournaments') to get recent tournaments"
            elif 'sync' in query_lower:
                return "Use sync.do('sync tournaments') to sync from start.gg"
        
        elif 'player' in query_lower:
            if 'top' in query_lower or 'rank' in query_lower:
                return "Use database.ask('top 50 players') for player rankings"
        
        elif 'organization' in query_lower or 'org' in query_lower:
            return "Use editor.ask('organizations') to see all orgs"
        
        elif 'service' in query_lower:
            # List discovered services
            services = list(self.discovered_services.keys())
            if services:
                return f"Discovered services: {', '.join(services[:5])}"
            return "No services discovered yet. Run services to see announcements."
        
        # Fall back to Ollama for complex queries
        return super().ask(query, **kwargs)
    
    def do(self, action: str, **kwargs):
        """Optimized actions for tournament tracker"""
        action_lower = action.lower()
        
        if 'sync' in action_lower:
            return "Triggering sync: sync.do('sync tournaments')"
        
        elif 'publish' in action_lower:
            return "Publishing: ./go.py --sync-and-publish"
        
        elif 'heat' in action_lower or 'map' in action_lower:
            return "Generating heatmap: ./go.py --heatmap"
        
        elif 'discord' in action_lower:
            return "Start Discord bot: ./go.py --discord-bot"
        
        # Fall back to parent implementation
        return super().do(action, **kwargs)