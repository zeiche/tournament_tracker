#!/usr/bin/env python3
"""
Base Bridge Class - Common functionality for all bridges
"""

import sys
import os
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer


class BaseBridge(ABC):
    """
    Abstract base class for all bridge services.
    Bridges connect two or more services together.
    """
    
    def __init__(self, name: str, source: str, target: str):
        """
        Initialize a bridge.
        
        Args:
            name: Name of this bridge
            source: Source service/system
            target: Target service/system
        """
        self.name = name
        self.source = source
        self.target = target
        self.active = False
        self.message_count = 0
        
        # Announce ourselves via Bonjour
        self._announce()
    
    def _announce(self):
        """Announce this bridge via Bonjour"""
        announcer.announce(
            self.name,
            [
                f"Bridge: {self.source} ↔ {self.target}",
                f"Status: {'Active' if self.active else 'Ready'}",
                f"Messages processed: {self.message_count}",
                "I connect services polymorphically"
            ],
            examples=[
                f"bridge.process('message')",
                f"bridge.get_status()",
                f"bridge.start()",
                f"bridge.stop()"
            ]
        )
    
    @abstractmethod
    async def process(self, message: Any, **kwargs) -> Any:
        """
        Process a message through the bridge.
        Must be implemented by subclasses.
        
        Args:
            message: Message to process
            **kwargs: Additional parameters
            
        Returns:
            Processed result
        """
        pass
    
    def start(self):
        """Start the bridge"""
        self.active = True
        self._announce()
        return f"{self.name} started"
    
    def stop(self):
        """Stop the bridge"""
        self.active = False
        self._announce()
        return f"{self.name} stopped"
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status"""
        return {
            "name": self.name,
            "source": self.source,
            "target": self.target,
            "active": self.active,
            "messages_processed": self.message_count
        }
    
    # Polymorphic interface
    def ask(self, query: str, **kwargs) -> Any:
        """Polymorphic ask - process as query"""
        return self.process(query, **kwargs)
    
    def tell(self, format: str, data: Any = None) -> str:
        """Polymorphic tell - format status"""
        if format == "json":
            import json
            return json.dumps(self.get_status(), indent=2)
        elif format == "discord":
            status = self.get_status()
            return f"**{status['name']}**\n{status['source']} ↔ {status['target']}\nActive: {status['active']}\nMessages: {status['messages_processed']}"
        else:
            return str(self.get_status())
    
    def do(self, action: str, **kwargs) -> Any:
        """Polymorphic do - perform action"""
        action_lower = action.lower()
        if "start" in action_lower:
            return self.start()
        elif "stop" in action_lower:
            return self.stop()
        elif "process" in action_lower:
            message = kwargs.get('message', action)
            return self.process(message, **kwargs)
        else:
            return f"Unknown action: {action}"


class BridgeRegistry:
    """Registry of all available bridges"""
    
    _bridges: Dict[str, BaseBridge] = {}
    
    @classmethod
    def register(cls, bridge: BaseBridge):
        """Register a bridge"""
        cls._bridges[bridge.name] = bridge
        announcer.announce(
            "Bridge Registry",
            [f"Registered bridge: {bridge.name}"]
        )
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseBridge]:
        """Get a bridge by name"""
        return cls._bridges.get(name)
    
    @classmethod
    def list_bridges(cls) -> List[str]:
        """List all registered bridges"""
        return list(cls._bridges.keys())
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseBridge]:
        """Get all bridges"""
        return cls._bridges