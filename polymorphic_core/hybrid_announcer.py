#!/usr/bin/env python3
"""
hybrid_announcer.py - Intelligent Service Discovery Architecture

DESIGN PHILOSOPHY:
- Local announcements for capabilities/methods (fast, in-memory)
- Network announcements for actual services with ports (real mDNS)
- Smart routing based on service characteristics
"""

import threading
from typing import List, Dict, Any, Optional
from .real_bonjour import RealBonjourAnnouncer

class LocalAnnouncer:
    """
    Fast in-memory announcements for capabilities, methods, and functions.
    No network overhead - instant discovery.
    """
    
    def __init__(self):
        self.announcements = []
        self.listeners = []
        self.service_registry = {}
        self._lock = threading.Lock()
        print("⚡ LocalAnnouncer initialized - fast in-memory discovery")
    
    def announce(self, service_name: str, capabilities: List[str], examples: List[str] = None):
        """Fast local announcement - no network traffic"""
        examples = examples or []
        
        with self._lock:
            announcement = {
                'service': service_name,
                'capabilities': capabilities,
                'examples': examples,
                'type': 'local'
            }
            self.announcements.append(announcement)
            
            # Notify local listeners immediately
            for listener in self.listeners:
                try:
                    listener(service_name, capabilities, examples)
                except Exception as e:
                    print(f"Local listener error: {e}")
        
        print(f"⚡ Local: {service_name}")
        return self
    
    def add_listener(self, listener_func):
        """Add listener for local announcements"""
        with self._lock:
            self.listeners.append(listener_func)
    
    def get_announcements(self) -> List[Dict]:
        """Get all local announcements"""
        with self._lock:
            return self.announcements.copy()
    
    def find_capability(self, capability: str) -> List[Dict]:
        """Find services with specific capability"""
        results = []
        with self._lock:
            for ann in self.announcements:
                for cap in ann['capabilities']:
                    if capability.lower() in cap.lower():
                        results.append(ann)
                        break
        return results


class NetworkAnnouncer:
    """
    Real mDNS announcements for actual network services with ports.
    Cross-machine discovery capability.
    """
    
    def __init__(self):
        self.real_bonjour = RealBonjourAnnouncer()
        print("🌐 NetworkAnnouncer initialized - real mDNS discovery")
    
    def announce(self, service_name: str, capabilities: List[str], examples: List[str] = None, port: int = None):
        """Network announcement via real mDNS"""
        print(f"🌐 Network: {service_name} (port: {port or 'auto'})")
        return self.real_bonjour.announce(service_name, capabilities, examples, port)
    
    def discover_services(self) -> Dict[str, Dict]:
        """Discover network services"""
        return self.real_bonjour.discover_services()
    
    def cleanup(self):
        """Clean shutdown"""
        self.real_bonjour.cleanup()


class HybridAnnouncer:
    """
    Intelligent announcer that routes to local vs network based on service type.
    
    ROUTING LOGIC:
    - Has port number → Network (real mDNS)
    - Service name contains "Service", "Server", "API" → Network
    - Math, Model, Capability words → Local (fast)
    - Default → Local (safe, fast)
    """
    
    def __init__(self):
        self.local = LocalAnnouncer()
        self.network = NetworkAnnouncer()
        self.stats = {'local': 0, 'network': 0}
        print("🎯 HybridAnnouncer initialized - intelligent routing")
    
    @property
    def announcements(self):
        """Backward compatibility: combined view of all announcements"""
        combined = []
        
        # Add local announcements
        combined.extend(self.local.get_announcements())
        
        # Add network services as announcements
        network_services = self.network.discover_services()
        for service_data in network_services.values():
            combined.append({
                'service': service_data['name'],
                'capabilities': service_data['capabilities'],
                'examples': service_data['examples'],
                'type': 'network',
                'host': service_data.get('host', 'unknown'),
                'port': service_data.get('port', 0)
            })
        
        return combined
    
    def announce(self, service_name: str, capabilities: List[str], examples: List[str] = None, port: int = None):
        """Smart routing: local vs network based on service characteristics"""
        
        # Explicit port = definitely network service
        if port is not None:
            self.stats['network'] += 1
            return self.network.announce(service_name, capabilities, examples, port)
        
        # Service name analysis - be more specific about network services
        service_lower = service_name.lower()
        
        # Strong network indicators (definitely network services)
        network_keywords = [
            'server', 'api', 'web', 'http', 'bridge', 'discord', 'twilio', 
            'editor service', 'database service', 'web editor'
        ]
        
        # Strong local indicators (definitely local/fast)
        local_keywords = [
            'model', 'math', 'capability', 'announcer', 'request',
            'processor', 'handler', 'manager', 'generator', 'analyzer'
        ]
        
        # Check for strong local indicators first
        for keyword in local_keywords:
            if keyword in service_lower:
                self.stats['local'] += 1
                return self.local.announce(service_name, capabilities, examples)
        
        # Check for network service indicators
        for keyword in network_keywords:
            if keyword in service_lower:
                self.stats['network'] += 1
                print(f"🌐 Routing to network: {service_name} (keyword: {keyword})")
                return self.network.announce(service_name, capabilities, examples)
        
        # Check capabilities for network indicators
        caps_text = ' '.join(capabilities).lower()
        if any(keyword in caps_text for keyword in ['port', 'server', 'http', 'web', 'api']):
            self.stats['network'] += 1
            print(f"🌐 Routing to network: {service_name} (capability keywords)")
            return self.network.announce(service_name, capabilities, examples)
        
        # Default to local (fast, safe)
        self.stats['local'] += 1
        return self.local.announce(service_name, capabilities, examples)
    
    def get_announcements_for_claude(self) -> str:
        """Get combined view of all announcements"""
        context = f"=== Hybrid Service Discovery ===\n"
        context += f"Local services: {self.stats['local']}, Network services: {self.stats['network']}\n\n"
        
        # Local announcements
        local_announcements = self.local.get_announcements()
        if local_announcements:
            context += "📱 LOCAL SERVICES (Fast):\n"
            for ann in local_announcements[-10:]:  # Show last 10
                context += f"  • {ann['service']}: {', '.join(ann['capabilities'][:3])}...\n"
        
        # Network announcements
        network_services = self.network.discover_services()
        if network_services:
            context += f"\n🌐 NETWORK SERVICES (mDNS - {len(network_services)} discovered):\n"
            for service_data in list(network_services.values())[:5]:  # Show first 5
                context += f"  • {service_data['name']} @ {service_data['host']}:{service_data['port']}\n"
        
        return context
    
    def discover_all(self) -> Dict[str, Any]:
        """Discover both local and network services"""
        return {
            'local': self.local.get_announcements(),
            'network': self.network.discover_services(),
            'stats': self.stats
        }
    
    # Backward compatibility methods
    def add_listener(self, listener_func):
        """Add listener to both local and network"""
        self.local.add_listener(listener_func)
    
    def register_service(self, service_name: str, handler):
        """Register service handler (local registry)"""
        self.local.service_registry[service_name] = handler
    
    def send_signal(self, signal_type: str, target_service: str = None, data: dict = None):
        """Send signals to registered services"""
        responses = {}
        for service_name, handler in self.local.service_registry.items():
            if target_service and service_name != target_service:
                continue
            try:
                if hasattr(handler, 'handle_signal'):
                    responses[service_name] = handler.handle_signal(signal_type, data)
                elif callable(handler):
                    responses[service_name] = handler(signal_type, data)
            except Exception as e:
                responses[service_name] = {'error': str(e)}
        return responses
    
    def cleanup(self):
        """Clean shutdown"""
        print("🧹 Shutting down hybrid announcer...")
        self.network.cleanup()
        print(f"📊 Final stats: {self.stats['local']} local, {self.stats['network']} network")


# Export for backward compatibility
announcer = HybridAnnouncer()
CapabilityAnnouncer = HybridAnnouncer

def announces_capability(service_name: str, *capabilities):
    """Decorator for auto-announcing capabilities"""
    def decorator(obj):
        announcer.announce(service_name, list(capabilities))
        return obj
    return decorator

# Cleanup on exit
import atexit
atexit.register(announcer.cleanup)

print("🎉 Hybrid service discovery ready - fast local + real network!")