#!/usr/bin/env python3
"""
Base Intelligence Interface - Abstract base for all intelligence implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger('intelligence.base')

@dataclass
class ServiceUnderstanding:
    """Understanding of a discovered service"""
    service_name: str
    capabilities: List[str]
    suggested_uses: List[str]
    relationships: List[str]  # How it relates to other services
    confidence: float  # 0.0 to 1.0

@dataclass
class QueryResponse:
    """Response to a query"""
    answer: str
    confidence: float
    sources: List[str]  # Which services were considered
    suggestions: List[str]  # Follow-up actions

class BaseIntelligence(ABC):
    """
    Abstract base class for all intelligence implementations
    Designed to work with the Bonjour service discovery model
    """
    
    def __init__(self):
        self.discovered_services = {}
        self.service_relationships = {}
        self.context_history = []
        self.max_context = 10
        
        # Announce ourselves if polymorphic_core is available
        try:
            from polymorphic_core import announcer
            announcer.announce(
                f"{self.__class__.__name__}",
                [
                    "Offline intelligence service",
                    "Understands Bonjour announcements",
                    "Maps service relationships",
                    "Answers queries about available services",
                    "Works completely offline"
                ]
            )
        except ImportError:
            logger.debug("Polymorphic core not available for announcement")
    
    @abstractmethod
    def understand_service(self, name: str, capabilities: List[str]) -> ServiceUnderstanding:
        """
        Understand a newly discovered service
        
        Args:
            name: Service name from Bonjour announcement
            capabilities: List of announced capabilities
            
        Returns:
            ServiceUnderstanding object
        """
        pass
    
    @abstractmethod
    def query(self, question: str) -> QueryResponse:
        """
        Answer a question using available service knowledge
        
        Args:
            question: Natural language question
            
        Returns:
            QueryResponse with answer and metadata
        """
        pass
    
    @abstractmethod
    def suggest_action(self, goal: str) -> List[Dict[str, Any]]:
        """
        Suggest actions to achieve a goal using available services
        
        Args:
            goal: What the user wants to accomplish
            
        Returns:
            List of suggested actions with service calls
        """
        pass
    
    def process_announcement(self, announcement: Dict[str, Any]):
        """
        Process a Bonjour service announcement
        
        Args:
            announcement: Dict with 'name', 'capabilities', etc.
        """
        name = announcement.get('name', 'Unknown')
        capabilities = announcement.get('capabilities', [])
        
        # Understand the service
        understanding = self.understand_service(name, capabilities)
        
        # Store in our knowledge base
        self.discovered_services[name] = {
            'capabilities': capabilities,
            'understanding': understanding,
            'announcement': announcement
        }
        
        # Update relationships
        self._update_relationships(name, understanding)
        
        logger.info(f"Processed announcement for {name} (confidence: {understanding.confidence:.2f})")
        
        return understanding
    
    def _update_relationships(self, service_name: str, understanding: ServiceUnderstanding):
        """Update service relationship graph"""
        if service_name not in self.service_relationships:
            self.service_relationships[service_name] = []
        
        # Find related services
        for other_service, data in self.discovered_services.items():
            if other_service == service_name:
                continue
                
            # Check for relationships
            for relationship in understanding.relationships:
                if other_service.lower() in relationship.lower():
                    self.service_relationships[service_name].append({
                        'service': other_service,
                        'type': relationship
                    })
    
    def get_service_map(self) -> Dict[str, Any]:
        """Get a map of all discovered services and their relationships"""
        return {
            'services': self.discovered_services,
            'relationships': self.service_relationships,
            'total_services': len(self.discovered_services)
        }
    
    def explain_capabilities(self) -> str:
        """Explain what the system can do based on discovered services"""
        if not self.discovered_services:
            return "No services discovered yet. Waiting for Bonjour announcements..."
        
        explanation = "Based on discovered services, I can help with:\n\n"
        
        for name, data in self.discovered_services.items():
            understanding = data['understanding']
            explanation += f"**{name}**\n"
            for use in understanding.suggested_uses[:3]:
                explanation += f"  - {use}\n"
            explanation += "\n"
        
        return explanation
    
    def ask(self, query: str) -> str:
        """Polymorphic ask method for compatibility"""
        response = self.query(query)
        return response.answer
    
    def tell(self, format: str, data: Any = None) -> str:
        """Polymorphic tell method for compatibility"""
        if format == 'json':
            return json.dumps(self.get_service_map(), indent=2)
        elif format == 'text':
            return self.explain_capabilities()
        elif format == 'markdown':
            return self._format_markdown()
        else:
            return str(data or self.get_service_map())
    
    def do(self, action: str) -> Any:
        """Polymorphic do method for compatibility"""
        if 'announce' in action.lower():
            # Re-announce ourselves
            self.__init__()
            return "Re-announced intelligence service"
        elif 'discover' in action.lower():
            # Trigger discovery
            return self.get_service_map()
        elif 'suggest' in action.lower():
            # Extract goal from action
            goal = action.replace('suggest', '').strip()
            return self.suggest_action(goal)
        else:
            return self.query(action)
    
    def _format_markdown(self) -> str:
        """Format service map as markdown"""
        md = "# Discovered Services\n\n"
        
        for name, data in self.discovered_services.items():
            understanding = data['understanding']
            md += f"## {name}\n"
            md += f"*Confidence: {understanding.confidence:.1%}*\n\n"
            md += "**Capabilities:**\n"
            for cap in understanding.capabilities[:5]:
                md += f"- {cap}\n"
            md += "\n"
        
        return md