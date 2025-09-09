#!/usr/bin/env python3
"""
Service Memory - Persistent memory for discovered Bonjour services
Stores service announcements and builds knowledge over time
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger('ollama_bonjour.memory')

class ServiceMemory:
    """
    Persistent memory for Bonjour service discovery
    """
    
    def __init__(self, memory_file='ollama_bonjour/service_memory.json'):
        """
        Initialize service memory
        
        Args:
            memory_file: Path to persistent memory file
        """
        self.memory_file = memory_file
        self.services = {}
        self.relationships = {}
        self.interaction_history = []
        
        # Load existing memory
        self.load()
    
    def load(self):
        """Load memory from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.services = data.get('services', {})
                    self.relationships = data.get('relationships', {})
                    self.interaction_history = data.get('interaction_history', [])
                    logger.info(f"Loaded memory: {len(self.services)} services")
            except Exception as e:
                logger.error(f"Could not load memory: {e}")
    
    def save(self):
        """Save memory to disk"""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump({
                    'services': self.services,
                    'relationships': self.relationships,
                    'interaction_history': self.interaction_history[-1000:]  # Keep last 1000
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save memory: {e}")
    
    def remember_service(self, name: str, capabilities: List[str], metadata: Dict = None):
        """
        Remember a service announcement
        
        Args:
            name: Service name
            capabilities: List of capabilities
            metadata: Optional metadata
        """
        if name not in self.services:
            self.services[name] = {
                'first_seen': datetime.now().isoformat(),
                'capabilities_history': [],
                'announcement_count': 0,
                'metadata': metadata or {}
            }
        
        service = self.services[name]
        service['last_seen'] = datetime.now().isoformat()
        service['announcement_count'] += 1
        service['current_capabilities'] = capabilities
        
        # Track capability changes over time
        caps_snapshot = {
            'timestamp': datetime.now().isoformat(),
            'capabilities': capabilities
        }
        service['capabilities_history'].append(caps_snapshot)
        
        # Limit history
        if len(service['capabilities_history']) > 100:
            service['capabilities_history'] = service['capabilities_history'][-50:]
        
        # Auto-save periodically
        if service['announcement_count'] % 10 == 0:
            self.save()
    
    def learn_relationship(self, service1: str, service2: str, relationship_type: str):
        """
        Learn a relationship between services
        
        Args:
            service1: First service
            service2: Second service  
            relationship_type: Type of relationship (uses, complements, requires, etc.)
        """
        key = f"{service1}<->{service2}"
        if key not in self.relationships:
            self.relationships[key] = {
                'services': [service1, service2],
                'types': [],
                'strength': 0,
                'first_observed': datetime.now().isoformat()
            }
        
        rel = self.relationships[key]
        if relationship_type not in rel['types']:
            rel['types'].append(relationship_type)
        rel['strength'] += 1
        rel['last_observed'] = datetime.now().isoformat()
    
    def record_interaction(self, query: str, response: str, services_used: List[str]):
        """
        Record a user interaction
        
        Args:
            query: User query
            response: System response
            services_used: Services referenced in response
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response[:500],  # Truncate long responses
            'services_used': services_used
        }
        
        self.interaction_history.append(interaction)
        
        # Learn from interaction - services used together
        for i, s1 in enumerate(services_used):
            for s2 in services_used[i+1:]:
                self.learn_relationship(s1, s2, 'used_together')
    
    def get_service_context(self, service_name: str) -> Dict:
        """
        Get full context about a service
        
        Args:
            service_name: Service to get context for
            
        Returns:
            Context dictionary
        """
        if service_name not in self.services:
            return {}
        
        service = self.services[service_name]
        
        # Find related services
        related = []
        for key, rel in self.relationships.items():
            if service_name in rel['services']:
                other = [s for s in rel['services'] if s != service_name][0]
                related.append({
                    'service': other,
                    'relationship': rel['types'],
                    'strength': rel['strength']
                })
        
        # Find recent interactions
        recent_uses = [
            inter for inter in self.interaction_history[-20:]
            if service_name in inter.get('services_used', [])
        ]
        
        return {
            'service': service_name,
            'info': service,
            'related_services': related,
            'recent_interactions': recent_uses
        }
    
    def find_services_for_goal(self, goal: str) -> List[str]:
        """
        Find services that might help with a goal
        
        Args:
            goal: Goal description
            
        Returns:
            List of relevant service names
        """
        goal_lower = goal.lower()
        relevant = []
        
        # Check service capabilities
        for name, service in self.services.items():
            caps = ' '.join(service.get('current_capabilities', [])).lower()
            
            # Score relevance
            score = 0
            for word in goal_lower.split():
                if len(word) > 3 and word in caps:
                    score += 1
                if len(word) > 3 and word in name.lower():
                    score += 2
            
            if score > 0:
                relevant.append((score, name))
        
        # Check interaction history
        for inter in self.interaction_history[-50:]:
            if any(word in inter['query'].lower() for word in goal_lower.split() if len(word) > 3):
                for service in inter.get('services_used', []):
                    relevant.append((1, service))
        
        # Deduplicate and sort by score
        seen = {}
        for score, name in relevant:
            if name not in seen or seen[name] < score:
                seen[name] = score
        
        return [name for name, _ in sorted(seen.items(), key=lambda x: -x[1])][:5]
    
    def get_statistics(self) -> Dict:
        """Get memory statistics"""
        return {
            'total_services': len(self.services),
            'total_relationships': len(self.relationships),
            'total_interactions': len(self.interaction_history),
            'most_active_service': max(self.services.items(), 
                                      key=lambda x: x[1]['announcement_count'])[0] if self.services else None,
            'strongest_relationship': max(self.relationships.items(),
                                        key=lambda x: x[1]['strength'])[0] if self.relationships else None,
            'memory_file': self.memory_file
        }


class ServicePatternMatcher:
    """
    Pattern matching for service discovery without LLM
    """
    
    def __init__(self):
        """Initialize pattern matcher"""
        self.patterns = {
            'database': ['database', 'db', 'sql', 'query', 'store', 'data'],
            'sync': ['sync', 'api', 'fetch', 'update', 'refresh', 'startgg'],
            'visualization': ['visual', 'graph', 'chart', 'map', 'plot', 'heat'],
            'audio': ['audio', 'voice', 'sound', 'speech', 'tts', 'play'],
            'web': ['web', 'http', 'server', 'port', 'editor', 'ui'],
            'discord': ['discord', 'bot', 'chat', 'message'],
            'intelligence': ['ai', 'llm', 'ollama', 'intelligence', 'smart']
        }
    
    def categorize(self, service_name: str, capabilities: List[str]) -> str:
        """
        Categorize a service based on patterns
        
        Args:
            service_name: Service name
            capabilities: Service capabilities
            
        Returns:
            Category name
        """
        text = f"{service_name} {' '.join(capabilities)}".lower()
        
        scores = {}
        for category, keywords in self.patterns.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[category] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return 'other'
    
    def match_query_to_category(self, query: str) -> List[str]:
        """
        Match a query to service categories
        
        Args:
            query: User query
            
        Returns:
            List of relevant categories
        """
        query_lower = query.lower()
        matches = []
        
        for category, keywords in self.patterns.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                matches.append((score, category))
        
        matches.sort(reverse=True)
        return [cat for _, cat in matches]
    
    def suggest_service_for_query(self, query: str, available_services: Dict) -> Optional[str]:
        """
        Suggest a service based on query patterns
        
        Args:
            query: User query
            available_services: Available services dict
            
        Returns:
            Suggested service name or None
        """
        categories = self.match_query_to_category(query)
        
        if not categories:
            return None
        
        # Find services in matching categories
        for category in categories:
            for service_name, service_data in available_services.items():
                service_category = self.categorize(
                    service_name, 
                    service_data.get('current_capabilities', [])
                )
                if service_category == category:
                    return service_name
        
        return None