#!/usr/bin/env python3
"""
claude_bonjour_service.py - Claude service enhanced with Bonjour discovery

This enhanced version:
1. Listens to all bonjour announcements to learn capabilities
2. Dynamically routes natural language requests to services
3. Builds context from live service announcements
4. Enables service-to-service conversations through Claude
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import anthropic
import logging
from typing import Optional, Dict, Any, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
from polymorphic_core import announcer, discover_capability, list_capabilities
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class ServiceCapability:
    """Represents a discovered service capability"""
    service_name: str
    capabilities: List[str]
    examples: List[str]
    last_seen: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_fresh(self, max_age_seconds: int = 300) -> bool:
        """Check if this capability announcement is still fresh"""
        age = (datetime.now() - self.last_seen).total_seconds()
        return age < max_age_seconds


class ClaudeBonjourService:
    """
    Claude service that dynamically discovers and uses capabilities via Bonjour.
    Instead of hardcoded methods, it learns what's available at runtime.
    """
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = "claude-3-haiku-20240307"
        self._api_client = None
        
        # Dynamic capability tracking
        self.discovered_services: Dict[str, ServiceCapability] = {}
        self.capability_history = deque(maxlen=100)
        self.service_patterns: Dict[str, List[str]] = {}  # Map patterns to services
        
        # Register as a bonjour listener
        announcer.add_listener(self._on_service_announcement)
        
        # Announce ourselves with DYNAMIC capabilities
        self._announce_capabilities()
        
        # Start capability discovery
        self._discover_initial_capabilities()
        
        logger.info("Claude Bonjour Service initialized - discovering capabilities dynamically")
    
    def _announce_capabilities(self):
        """Announce our capabilities - but emphasize they're DYNAMIC"""
        current_services = len(self.discovered_services)
        service_list = list(self.discovered_services.keys())[:5]  # First 5 as examples
        
        announcer.announce(
            "Claude Bonjour Service",
            [
                "I learn what services are available through Bonjour announcements",
                f"Currently aware of {current_services} services",
                "I route natural language requests to appropriate services",
                "I build context from live service announcements",
                "I enable service-to-service conversations",
                "My capabilities grow as new services announce themselves",
                "Ask me what I can do - it changes based on what's running!"
            ],
            [
                "What services are available?",
                "What can you do right now?",
                "Show me top players (routes to appropriate service)",
                "Edit tournament 123 (finds and uses editor service)",
                f"Known services: {', '.join(service_list)}" if service_list else "Discovering services..."
            ]
        )
    
    def _on_service_announcement(self, service_name: str, capabilities: List[str], examples: Optional[List[str]] = None):
        """Called whenever ANY service makes a bonjour announcement"""
        # Don't track our own announcements
        if "Claude" in service_name:
            return
            
        # Store/update the service capability
        self.discovered_services[service_name] = ServiceCapability(
            service_name=service_name,
            capabilities=capabilities,
            examples=examples or [],
            last_seen=datetime.now()
        )
        
        # Add to history
        self.capability_history.append({
            'timestamp': datetime.now(),
            'service': service_name,
            'event': 'discovered' if service_name not in self.discovered_services else 'updated'
        })
        
        # Extract patterns from capabilities and examples
        self._extract_patterns(service_name, capabilities, examples)
        
        # Re-announce ourselves with updated capability count
        if len(self.capability_history) % 10 == 0:  # Every 10 announcements
            self._announce_capabilities()
        
        logger.debug(f"Discovered/updated service: {service_name} with {len(capabilities)} capabilities")
    
    def _extract_patterns(self, service_name: str, capabilities: List[str], examples: List[str]):
        """Extract natural language patterns from capabilities and examples"""
        patterns = []
        
        # Extract verb patterns from capabilities
        for cap in capabilities:
            cap_lower = cap.lower()
            # Look for action words
            if any(verb in cap_lower for verb in ['edit', 'update', 'modify', 'change']):
                patterns.append('edit')
            if any(verb in cap_lower for verb in ['show', 'display', 'list', 'get']):
                patterns.append('show')
            if any(verb in cap_lower for verb in ['sync', 'synchronize', 'fetch']):
                patterns.append('sync')
            if any(verb in cap_lower for verb in ['generate', 'create', 'make']):
                patterns.append('generate')
                
        # Extract patterns from examples
        for example in examples or []:
            example_lower = example.lower()
            # Look for specific formats like "ask('query')" or "do('action')"
            if 'ask(' in example_lower:
                patterns.append('ask')
            if 'tell(' in example_lower:
                patterns.append('tell')
            if 'do(' in example_lower:
                patterns.append('do')
                
        # Map patterns to service
        for pattern in set(patterns):
            if pattern not in self.service_patterns:
                self.service_patterns[pattern] = []
            if service_name not in self.service_patterns[pattern]:
                self.service_patterns[pattern].append(service_name)
    
    def _discover_initial_capabilities(self):
        """Discover what capabilities are already registered"""
        try:
            registered = list_capabilities()
            logger.info(f"Initial discovery found: {registered}")
            
            # Try to get more info about each service
            for service_type, service_list in registered.items():
                for service_name in service_list:
                    # This might trigger announcements
                    service = discover_capability(service_name)
                    if service:
                        logger.debug(f"Discovered {service_name} via registry")
        except Exception as e:
            logger.debug(f"Initial discovery error (expected if no services running): {e}")
    
    @property
    def api_client(self):
        """Lazy load API client"""
        if self._api_client is None and self.api_key:
            self._api_client = anthropic.Anthropic(api_key=self.api_key)
        return self._api_client
    
    def get_dynamic_context(self) -> str:
        """Build context from live service announcements"""
        context_parts = ["=== Currently Available Services ===\n"]
        
        # Group services by freshness
        fresh_services = []
        stale_services = []
        
        for name, service in self.discovered_services.items():
            if service.is_fresh(max_age_seconds=300):  # 5 minutes
                fresh_services.append(service)
            else:
                stale_services.append(service)
        
        # Add fresh services first
        if fresh_services:
            context_parts.append("Active Services (recently announced):")
            for service in fresh_services:
                context_parts.append(f"\n• {service.service_name}")
                # Show first 3 capabilities
                for cap in service.capabilities[:3]:
                    context_parts.append(f"  - {cap}")
                if service.examples and service.examples[0]:
                    context_parts.append(f"  Example: {service.examples[0]}")
        
        # Add pattern mappings
        if self.service_patterns:
            context_parts.append("\n\n=== Natural Language Routing ===")
            context_parts.append("I can route these types of requests:")
            for pattern, services in list(self.service_patterns.items())[:10]:
                context_parts.append(f"• '{pattern}' requests → {', '.join(services[:3])}")
        
        # Add statistics
        context_parts.append(f"\n\n=== Discovery Statistics ===")
        context_parts.append(f"• Total services discovered: {len(self.discovered_services)}")
        context_parts.append(f"• Currently active: {len(fresh_services)}")
        context_parts.append(f"• Pattern mappings: {len(self.service_patterns)}")
        
        return "\n".join(context_parts)
    
    def ask_with_discovery(self, question: str) -> Dict[str, Any]:
        """
        Process a question using discovered capabilities.
        This is the MAIN method that replaces all the hardcoded methods.
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'No API key configured',
                'discovered_services': len(self.discovered_services)
            }
        
        try:
            # Build dynamic context from discoveries
            dynamic_context = self.get_dynamic_context()
            
            # Analyze the question to find relevant services
            relevant_services = self._find_relevant_services(question)
            
            # Build service-specific context
            service_context = ""
            if relevant_services:
                service_context = "\n\nRelevant services for this query:"
                for service_name in relevant_services[:3]:  # Top 3 relevant
                    if service_name in self.discovered_services:
                        svc = self.discovered_services[service_name]
                        service_context += f"\n• {service_name}: {svc.capabilities[0] if svc.capabilities else 'Available'}"
            
            # Create prompt with dynamic context
            system_prompt = f"""You are Claude, integrated with a Bonjour service discovery system.
You have real-time awareness of what services are available and their capabilities.

{dynamic_context}
{service_context}

When answering questions:
1. Use your knowledge of available services to provide accurate responses
2. If a service can handle the request, mention it
3. Adapt your capabilities based on what services are running
4. If no relevant service is available, explain what would be needed

Remember: Your capabilities are DYNAMIC and change as services start/stop."""
            
            # Get response from Claude API
            message = self.api_client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": question}]
            )
            
            response = message.content[0].text
            
            return {
                'success': True,
                'response': response,
                'relevant_services': relevant_services,
                'total_services': len(self.discovered_services),
                'active_services': len([s for s in self.discovered_services.values() if s.is_fresh()])
            }
            
        except Exception as e:
            logger.error(f"Error in ask_with_discovery: {e}")
            return {
                'success': False,
                'error': str(e),
                'discovered_services': len(self.discovered_services)
            }
    
    def _find_relevant_services(self, question: str) -> List[str]:
        """Find services relevant to a question using pattern matching"""
        question_lower = question.lower()
        relevant = set()
        
        # Check each pattern
        for pattern, services in self.service_patterns.items():
            if pattern in question_lower:
                relevant.update(services)
        
        # Also check for service names directly mentioned
        for service_name in self.discovered_services.keys():
            if any(word in question_lower for word in service_name.lower().split()):
                relevant.add(service_name)
        
        # Check for domain-specific keywords
        keyword_map = {
            'tournament': ['Database Service', 'Start.gg Sync', 'Tournament Operations'],
            'player': ['Database Service', 'Polymorphic Query'],
            'edit': ['Web Editor Service'],
            'sync': ['Start.gg Sync', 'Tournament Operations'],
            'organization': ['Web Editor Service', 'Database Service'],
            'heat': ['Visualization Service', 'Analytics'],
            'stats': ['Database Service', 'Analytics'],
            'discord': ['Discord Bridge', 'Discord Service']
        }
        
        for keyword, service_hints in keyword_map.items():
            if keyword in question_lower:
                for hint in service_hints:
                    # Find services that match the hint
                    for service_name in self.discovered_services.keys():
                        if hint.lower() in service_name.lower():
                            relevant.add(service_name)
        
        return list(relevant)
    
    def route_to_service(self, request: str) -> Dict[str, Any]:
        """
        Route a natural language request to the appropriate service.
        This demonstrates service-to-service communication via Claude.
        """
        # Find relevant services
        relevant_services = self._find_relevant_services(request)
        
        if not relevant_services:
            return {
                'success': False,
                'error': 'No relevant services found for this request',
                'suggestion': 'Try starting the appropriate service first'
            }
        
        # For now, return which service would handle it
        # In a full implementation, this would actually call the service
        primary_service = relevant_services[0]
        service_info = self.discovered_services.get(primary_service, None)
        
        return {
            'success': True,
            'routed_to': primary_service,
            'service_capabilities': service_info.capabilities if service_info else [],
            'confidence': len(relevant_services),
            'alternatives': relevant_services[1:] if len(relevant_services) > 1 else []
        }
    
    def get_conversation_capabilities(self) -> Dict[str, Any]:
        """
        Return current conversation capabilities based on discovered services.
        This changes dynamically as services come and go!
        """
        capabilities = {
            'timestamp': datetime.now().isoformat(),
            'discovered_services': len(self.discovered_services),
            'active_services': len([s for s in self.discovered_services.values() if s.is_fresh()]),
            'available_patterns': list(self.service_patterns.keys()),
            'can_handle': []
        }
        
        # Build list of what we can currently handle
        for service in self.discovered_services.values():
            if service.is_fresh():
                for capability in service.capabilities[:2]:  # First 2 from each service
                    capabilities['can_handle'].append(f"{service.service_name}: {capability}")
        
        return capabilities


# Create global instance
claude_bonjour = ClaudeBonjourService()


def ask_claude_with_discovery(question: str) -> str:
    """Simple wrapper for the enhanced Claude service"""
    result = claude_bonjour.ask_with_discovery(question)
    if result['success']:
        return result['response']
    else:
        return f"Error: {result.get('error', 'Unknown error')}"


def get_claude_capabilities() -> Dict[str, Any]:
    """Get current Claude capabilities (changes as services are discovered!)"""
    return claude_bonjour.get_conversation_capabilities()


if __name__ == "__main__":
    print("Claude Bonjour Service - Dynamic Capability Discovery")
    print("=" * 60)
    
    # Show what we've discovered
    caps = get_claude_capabilities()
    print(f"Discovered {caps['discovered_services']} services")
    print(f"Active: {caps['active_services']}")
    print(f"Patterns: {', '.join(caps['available_patterns'][:10])}")
    
    # Test a question
    if claude_bonjour.api_key:
        print("\nTesting with question...")
        response = ask_claude_with_discovery("What services are currently available?")
        print(f"Response: {response[:500]}...")
    else:
        print("\nNo API key configured - would work with real services announcing")
    
    # Show dynamic context
    print("\nDynamic Context:")
    print(claude_bonjour.get_dynamic_context())