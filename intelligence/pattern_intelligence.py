#!/usr/bin/env python3
"""
Pattern Intelligence - Simple pattern matching without LLM
Works completely offline with no dependencies
"""

import sys
import os
import json
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer
from .base_intelligence import BaseIntelligence, ServiceUnderstanding, QueryResponse

class PatternIntelligence(BaseIntelligence):
    """
    Pattern-based intelligence - no LLM required
    Simple rules and pattern matching for service discovery
    """
    
    def __init__(self):
        """Initialize pattern intelligence"""
        super().__init__()
        
        # Announce ourselves
        self._announce_service()
        
        # Subscribe to announcements
        self._subscribe_to_announcements()
    
    def _announce_service(self):
        """Announce Pattern Intelligence via Bonjour"""
        announcer.announce("Pattern Intelligence", [
            "Pattern Intelligence - Simple offline assistant",
            "No LLM required - pure pattern matching",
            "I understand Bonjour service patterns",
            "Zero dependencies, always available",
            "ask('services') - List discovered services",
            "ask('database') - Get database service info",
            "tell('json', data) - Format as JSON",
            "do('discover') - Refresh service discovery",
            "I work instantly with no setup required"
        ])
    
    def _subscribe_to_announcements(self):
        """Subscribe to Bonjour service announcements"""
        for announcement in announcer.announcements:
            service_name = announcement.get('service', 'Unknown')
            capabilities = announcement.get('capabilities', [])
            
            self.discovered_services[service_name] = {
                'capabilities': capabilities,
                'timestamp': None
            }
    
    def understand_service(self, name: str, capabilities: List[str]) -> ServiceUnderstanding:
        """Pattern-based service understanding"""
        name_lower = name.lower()
        caps_text = ' '.join(capabilities).lower()
        
        uses = []
        relationships = []
        confidence = 0.5
        
        # Database patterns
        if 'database' in name_lower or 'db' in caps_text:
            uses = ['Query data', 'Store results', 'Manage records']
            relationships = ['Works with sync', 'Feeds visualizer']
            confidence = 0.9
        
        # Sync patterns
        elif 'sync' in name_lower or 'startgg' in caps_text:
            uses = ['Sync tournaments', 'Update data', 'Refresh standings']
            relationships = ['Updates database', 'Triggers reports']
            confidence = 0.9
        
        # Visualization patterns
        elif 'visual' in name_lower or 'heat' in caps_text:
            uses = ['Create maps', 'Generate reports', 'Build charts']
            relationships = ['Reads database', 'Exports HTML']
            confidence = 0.85
        
        # Audio patterns
        elif 'audio' in name_lower or 'voice' in caps_text:
            uses = ['Play audio', 'Process voice', 'Generate speech']
            relationships = ['Discord integration', 'Notifications']
            confidence = 0.8
        
        # Editor patterns
        elif 'editor' in name_lower or 'web' in caps_text:
            uses = ['Edit organizations', 'Manage contacts', 'Web interface']
            relationships = ['Updates database', 'Port 8081']
            confidence = 0.85
        
        return ServiceUnderstanding(
            service_name=name,
            capabilities=capabilities,
            suggested_uses=uses or ['General service'],
            relationships=relationships or ['Standalone'],
            confidence=confidence
        )
    
    def query(self, question: str) -> QueryResponse:
        """Answer questions using patterns"""
        q_lower = question.lower()
        
        # Service listing
        if 'service' in q_lower and ('list' in q_lower or 'show' in q_lower):
            services = list(self.discovered_services.keys())
            answer = f"Discovered {len(services)} services: {', '.join(services)}"
            return QueryResponse(answer, 0.9, services, [])
        
        # Database queries
        if 'database' in q_lower or 'db' in q_lower:
            answer = "Database service: Use db.ask('query') for data, db.tell('format', data) to format, db.do('action') to modify"
            return QueryResponse(answer, 0.8, ['Database Service'], [])
        
        # Sync queries
        if 'sync' in q_lower:
            answer = "To sync: Use sync.do('sync tournaments') or run ./go.py --sync"
            return QueryResponse(answer, 0.8, ['Start.gg Sync'], [])
        
        # Tournament queries
        if 'tournament' in q_lower:
            if 'recent' in q_lower:
                answer = "For recent tournaments: db.ask('recent tournaments')"
            elif 'sync' in q_lower:
                answer = "To sync tournaments: sync.do('sync tournaments')"
            else:
                answer = "Tournament commands: db.ask('tournament ID'), sync.do('sync')"
            return QueryResponse(answer, 0.7, ['Database', 'Sync'], [])
        
        # Player queries
        if 'player' in q_lower:
            answer = "Player commands: db.ask('top 50 players'), db.ask('player NAME')"
            return QueryResponse(answer, 0.7, ['Database'], [])
        
        # Default
        answer = f"I found {len(self.discovered_services)} services. Try asking about: database, sync, tournaments, players"
        return QueryResponse(answer, 0.5, [], ["Ask about specific services"])
    
    def suggest_action(self, goal: str) -> List[Dict[str, Any]]:
        """Suggest actions based on patterns"""
        goal_lower = goal.lower()
        
        actions = []
        
        if 'sync' in goal_lower:
            actions.append({
                'service': 'sync',
                'method': 'do',
                'params': 'sync tournaments'
            })
        
        if 'tournament' in goal_lower:
            actions.append({
                'service': 'database',
                'method': 'ask',
                'params': 'recent tournaments'
            })
        
        if 'player' in goal_lower:
            actions.append({
                'service': 'database',
                'method': 'ask',
                'params': 'top 50 players'
            })
        
        if 'heat' in goal_lower or 'map' in goal_lower:
            actions.append({
                'service': 'visualizer',
                'method': 'do',
                'params': 'generate heatmap'
            })
        
        if not actions:
            actions.append({
                'service': 'unknown',
                'method': 'ask',
                'params': goal
            })
        
        return actions
    
    def ask(self, query: str, **kwargs) -> Any:
        """Polymorphic ask method"""
        return self.query(query)
    
    def tell(self, format: str, data: Any = None) -> str:
        """Polymorphic tell method"""
        if format == 'json':
            if hasattr(data, '__dict__'):
                return json.dumps(data.__dict__, indent=2)
            return json.dumps(data, indent=2)
        elif format == 'discord':
            if isinstance(data, QueryResponse):
                return f"**{data.answer}**"
            return str(data)
        else:
            return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Polymorphic do method"""
        action_lower = action.lower()
        
        if 'discover' in action_lower:
            self._subscribe_to_announcements()
            return f"Discovered {len(self.discovered_services)} services"
        
        elif 'analyze' in action_lower:
            analysis = []
            for name in self.discovered_services:
                caps = self.discovered_services[name]['capabilities']
                understanding = self.understand_service(name, caps)
                analysis.append({
                    'service': name,
                    'confidence': understanding.confidence
                })
            return analysis
        
        else:
            suggestions = self.suggest_action(action)
            return suggestions