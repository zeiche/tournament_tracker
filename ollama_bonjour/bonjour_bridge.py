#!/usr/bin/env python3
"""
Bonjour Bridge - Connects Bonjour announcements to Ollama intelligence
Real-time monitoring and routing of service discovery
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer

from .ollama_service import get_ollama_bonjour
from .service_memory import ServiceMemory, ServicePatternMatcher

logger = logging.getLogger('ollama_bonjour.bridge')

class BonjourBridge:
    """
    Bridge between Bonjour announcements and Ollama intelligence
    """
    
    def __init__(self):
        """Initialize the bridge"""
        self.ollama = get_ollama_bonjour()
        self.memory = ServiceMemory()
        self.pattern_matcher = ServicePatternMatcher()
        self.running = False
        
        # Track announcement processing
        self.processed_count = 0
        self.last_processed = None
        
        logger.info("Bonjour Bridge initialized")
    
    async def start(self):
        """Start the bridge service"""
        self.running = True
        logger.info("Starting Bonjour Bridge...")
        
        # Initial scan of existing announcements
        self._scan_announcements()
        
        # Start monitoring loop
        await self._monitoring_loop()
    
    def stop(self):
        """Stop the bridge service"""
        self.running = False
        self.memory.save()
        logger.info(f"Bridge stopped. Processed {self.processed_count} announcements")
    
    def _scan_announcements(self):
        """Scan and process current announcements"""
        for announcement in announcer.announcements:
            self._process_announcement(announcement)
        
        logger.info(f"Initial scan: found {len(announcer.announcements)} services")
    
    def _process_announcement(self, announcement: Dict):
        """
        Process a single announcement
        
        Args:
            announcement: Bonjour announcement dict
        """
        service_name = announcement.get('service', 'Unknown')
        capabilities = announcement.get('capabilities', [])
        
        # Skip our own announcements
        if 'ollama' in service_name.lower():
            return
        
        # Remember in persistent memory
        self.memory.remember_service(service_name, capabilities)
        
        # Categorize the service
        category = self.pattern_matcher.categorize(service_name, capabilities)
        
        # Update Ollama's knowledge
        self.ollama._process_announcement(announcement)
        
        # Track processing
        self.processed_count += 1
        self.last_processed = datetime.now()
        
        logger.debug(f"Processed {service_name} (category: {category})")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        check_interval = 5  # seconds
        last_count = len(announcer.announcements)
        
        while self.running:
            try:
                # Check for new announcements
                current_count = len(announcer.announcements)
                
                if current_count != last_count:
                    logger.info(f"Announcement count changed: {last_count} -> {current_count}")
                    self._scan_announcements()
                    last_count = current_count
                
                # Periodic re-announcement
                if self.processed_count > 0 and self.processed_count % 20 == 0:
                    self._announce_bridge_status()
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(check_interval)
    
    def _announce_bridge_status(self):
        """Announce bridge status via Bonjour"""
        announcer.announce("Bonjour Bridge", [
            "Bridge between Bonjour and Ollama Intelligence",
            f"Monitoring {len(self.memory.services)} services",
            f"Processed {self.processed_count} announcements",
            f"Learned {len(self.memory.relationships)} relationships",
            f"Recorded {len(self.memory.interaction_history)} interactions",
            "I connect service discovery to intelligence",
            "I remember everything services announce",
            "I help Ollama understand your service landscape"
        ])
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Route a query through the bridge
        
        Args:
            query: User query
            
        Returns:
            Response dict with answer and metadata
        """
        # Find relevant services for the query
        relevant_services = self.memory.find_services_for_goal(query)
        
        # Get Ollama's response
        response = self.ollama.ask(query)
        
        # Record the interaction
        self.memory.record_interaction(query, response, relevant_services)
        
        # Build complete response
        return {
            'answer': response,
            'relevant_services': relevant_services,
            'suggested_service': self.pattern_matcher.suggest_service_for_query(
                query, self.memory.services
            ),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_service_graph(self) -> Dict:
        """
        Get the service relationship graph
        
        Returns:
            Graph data for visualization
        """
        nodes = []
        edges = []
        
        # Create nodes for each service
        for service_name, service_data in self.memory.services.items():
            nodes.append({
                'id': service_name,
                'label': service_name,
                'category': self.pattern_matcher.categorize(
                    service_name,
                    service_data.get('current_capabilities', [])
                ),
                'announcement_count': service_data.get('announcement_count', 0)
            })
        
        # Create edges for relationships
        for rel_key, rel_data in self.memory.relationships.items():
            services = rel_data['services']
            if len(services) == 2:
                edges.append({
                    'source': services[0],
                    'target': services[1],
                    'weight': rel_data['strength'],
                    'types': rel_data['types']
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'statistics': self.memory.get_statistics()
        }


class BonjourRouter:
    """
    Smart router that uses Bonjour + Ollama to route requests
    """
    
    def __init__(self):
        """Initialize router"""
        self.bridge = BonjourBridge()
        self.routes = {}
        
    def route(self, request: str) -> str:
        """
        Route a natural language request to the right service
        
        Args:
            request: Natural language request
            
        Returns:
            Service routing recommendation
        """
        # Get routing from bridge
        result = self.bridge.route_query(request)
        
        if result['suggested_service']:
            service = result['suggested_service']
            # Build routing command
            if 'database' in service.lower():
                return f"Route to: database.ask('{request}')"
            elif 'sync' in service.lower():
                return f"Route to: sync.do('{request}')"
            elif 'visual' in service.lower():
                return f"Route to: visualizer.do('{request}')"
            else:
                return f"Route to: {service} (try .ask() or .do())"
        
        return result['answer']


async def run_bridge():
    """Run the bridge as a service"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bridge = BonjourBridge()
    
    # Announce the bridge
    bridge._announce_bridge_status()
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Shutting down bridge...")
        bridge.stop()


if __name__ == "__main__":
    asyncio.run(run_bridge())