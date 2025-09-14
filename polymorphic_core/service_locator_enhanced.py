#!/usr/bin/env python3
"""
service_locator_enhanced.py - Enhanced service locator with hybrid cache

This replaces the original service_locator.py with hybrid caching for optimal performance.
Maintains 100% backward compatibility while adding database-backed caching.
"""

import importlib
import sys
from typing import Any, Dict, Optional, Callable, Union
# Import the hybrid cache and bonjour
import sys
import os
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from service_cache_optimization import HybridServiceCache

try:
    from polymorphic_core.real_bonjour import announcer
except ImportError:
    # Fallback if relative import fails
    import polymorphic_core.real_bonjour as announcer_module
    announcer = announcer_module.announcer


class EnhancedServiceLocator:
    """
    Enhanced service discovery with hybrid caching (RAM + Database).
    
    Provides the same interface as the original ServiceLocator but with:
    - L1 Cache (RAM): Microsecond access for active services
    - L2 Cache (Database): Persistent discovery results across restarts
    - Usage analytics and automatic cleanup
    
    100% backward compatible with existing code.
    """
    
    def __init__(self):
        # Initialize hybrid cache
        self.hybrid_cache = HybridServiceCache()
        
        # Maintain backward compatibility properties
        self.local_cache = self.hybrid_cache.l1_cache
        self.network_cache = {}  # Network cache handled by hybrid system
        
        self.capability_map = {
            # Phase 1 - REFACTORED Core Services ✅
            "database": "utils.database_service_refactored.database_service_refactored",
            "logger": "utils.simple_logger_refactored.logger_service",
            "error_handler": "utils.error_handler_refactored.error_handler", 
            "config": "utils.config_service_refactored.config_service",
            
            # Phase 2 - REFACTORED Business Services ✅
            "claude": "services.claude_cli_service_refactored.claude_service",
            "web_editor": "services.polymorphic_web_editor_refactored.web_editor",
            "interactive": "services.interactive_service_refactored.interactive_service",
            "message_handler": "services.message_handler_refactored.message_handler",
            
            # Phase 3 - REFACTORED Specialized Services ✅
            "twilio": "services.twilio_service_refactored.twilio_service",
            "report": "services.report_service_refactored.report_service",
            "process": "services.process_service_refactored.process_service",
            
            # Phase 4 - REFACTORED Domain Services ✅
            "startgg_sync": "services.startgg_sync_refactored.startgg_sync_service",
            
            # Phase 5 - REFACTORED Analytics Services ✅
            "analytics": "services.analytics_service_refactored.analytics_service",
            
            # Phase 5 - REFACTORED Utility Services ✅
            "queue": "utils.database_queue_refactored.queue_service",
            "points_system": "utils.points_system_refactored.points_service",
            "tabulator": "utils.unified_tabulator_refactored.tabulator_service",
            
            # Legacy core services (fallback)
            "database_legacy": "utils.database_service.database_service",
            "logger_legacy": "utils.simple_logger",
            "error_handler_legacy": "utils.error_handler.error_handler",
            "config_legacy": "utils.config_service",
            "claude_legacy": "services.claude_cli_service.claude_service",
            "web_editor_legacy": "services.polymorphic_web_editor.web_editor",
            "interactive_legacy": "services.interactive_service",
            "message_handler_legacy": "services.message_handler",
            
            # Domain services
            "sync": "services.startgg_sync.startgg_sync",
            "twilio": "twilio_service.twilio_service",
        }
    
    def get_service(self, capability_name: str, prefer_network: bool = False) -> Any:
        """
        Get service using hybrid cache for optimal performance.
        
        This method is 100% backward compatible but uses the hybrid cache
        for dramatically improved performance.
        """
        try:
            # Use hybrid cache which handles L1/L2 caching automatically
            service = self.hybrid_cache.get_service(capability_name, prefer_network)
            
            if service:
                local_announcer.announce(
                    f"ServiceLocator-{capability_name}",
                    [f"Retrieved service: {capability_name}"],
                    [f"Service type: {'network' if prefer_network else 'local'}"]
                )
                return service
            
            # If hybrid cache fails, fall back to original discovery logic
            if prefer_network:
                service = self._get_network_service(capability_name)
                if service:
                    return service
            
            return self._get_local_service(capability_name)
            
        except Exception as e:
            local_announcer.announce(
                f"ServiceLocator-Error",
                [f"Failed to get service {capability_name}: {str(e)}"]
            )
            return None
    
    def _get_local_service(self, capability_name: str) -> Optional[Any]:
        """Get local service (backward compatibility method)"""
        if capability_name not in self.capability_map:
            return None
        
        module_path = self.capability_map[capability_name]
        
        try:
            # Handle module.attribute syntax
            if '.' in module_path:
                parts = module_path.split('.')
                module_name = '.'.join(parts[:-1])
                attr_name = parts[-1]
                
                module = importlib.import_module(module_name)
                service = getattr(module, attr_name, None)
                
                if service:
                    return service
            
            # Handle direct module import
            module = importlib.import_module(module_path)
            return module
            
        except ImportError as e:
            local_announcer.announce(
                f"ServiceLocator-ImportError",
                [f"Could not import {module_path}: {str(e)}"]
            )
            return None
        except Exception as e:
            local_announcer.announce(
                f"ServiceLocator-Error",
                [f"Error loading {capability_name}: {str(e)}"]
            )
            return None
    
    def _get_network_service(self, capability_name: str) -> Optional[Any]:
        """Get network service via mDNS discovery"""
        try:
            # Try to discover service via mDNS
            from .real_bonjour import discover_services
            
            services = discover_services(service_type="_tournament._tcp.local.", timeout=2.0)
            
            for service_info in services:
                if capability_name in service_info.get('name', '').lower():
                    # Create network service client
                    return NetworkServiceClient(
                        service_name=service_info['name'],
                        host=service_info['host'],
                        port=service_info['port'],
                        capabilities=[f"Network {capability_name} service"]
                    )
            
            return None
            
        except Exception as e:
            local_announcer.announce(
                f"ServiceLocator-NetworkError",
                [f"Network discovery failed for {capability_name}: {str(e)}"]
            )
            return None
    
    def register_capability(self, capability_name: str, module_path: str):
        """Register a new capability mapping"""
        self.capability_map[capability_name] = module_path
        local_announcer.announce(
            f"ServiceLocator-Registration",
            [f"Registered {capability_name} → {module_path}"]
        )
    
    def clear_cache(self):
        """Clear all caches"""
        self.hybrid_cache.clear_cache()
        local_announcer.announce(
            "ServiceLocator-CacheCleared",
            ["All service caches cleared"]
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return self.hybrid_cache.get_cache_stats()
    
    def list_available_services(self) -> Dict[str, Dict]:
        """List all available services with metadata"""
        services = {}
        
        for capability, module_path in self.capability_map.items():
            # Check if service is cached
            cached_local = capability in self.local_cache
            
            services[capability] = {
                'module_path': module_path,
                'cached_local': cached_local,
                'cache_type': 'hybrid'
            }
        
        return services


class NetworkServiceClient:
    """
    Client for accessing network services via HTTP.
    
    Provides the same 3-method interface (ask/tell/do) for network services.
    """
    
    def __init__(self, service_name: str, host: str, port: int, capabilities: list):
        self.service_name = service_name
        self.host = host
        self.port = port
        self.capabilities = capabilities
        self.base_url = f"http://{host}:{port}"
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query the network service"""
        return self._make_request("ask", {"query": query, **kwargs})
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """Get formatted output from network service"""
        return self._make_request("tell", {"format": format_type, "data": data, **kwargs})
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform action on network service"""
        return self._make_request("do", {"action": action, **kwargs})
    
    def _make_request(self, method: str, payload: dict) -> Any:
        """Make HTTP request to network service"""
        import requests
        import json
        
        try:
            url = f"{self.base_url}/{method}"
            response = requests.post(url, json=payload, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "service": self.service_name}
    
    def __getattr__(self, name):
        """Fallback for any other method calls"""
        def network_method(*args, **kwargs):
            return self._make_request(name, {"args": args, "kwargs": kwargs})
        return network_method


# Create enhanced service locator instance
enhanced_service_locator = EnhancedServiceLocator()

# Convenience functions for easy import (backward compatibility)
def get_service(capability_name: str, prefer_network: bool = False) -> Any:
    """Get a service by capability name - works with local or network services"""
    return enhanced_service_locator.get_service(capability_name, prefer_network)

def register_service(capability_name: str, module_path: str):
    """Register a new service capability"""
    enhanced_service_locator.register_capability(capability_name, module_path)

def list_services() -> Dict[str, Dict]:
    """List all available services"""
    return enhanced_service_locator.list_available_services()

def get_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics"""
    return enhanced_service_locator.get_cache_stats()

def clear_cache():
    """Clear all service caches"""
    enhanced_service_locator.clear_cache()

# For backward compatibility, expose the enhanced locator as service_locator
service_locator = enhanced_service_locator


if __name__ == "__main__":
    # Test the enhanced service locator
    print("🚀 Enhanced Service Locator Test")
    print("=" * 50)
    
    # Show initial cache stats
    stats = get_cache_stats()
    print(f"Initial cache stats: {stats}")
    
    # Test service access
    print("\nTesting database service access...")
    
    import time
    
    # First access
    start = time.time()
    db1 = get_service("database")
    time1 = time.time() - start
    print(f"First access: {time1:.3f}s")
    
    # Second access (should be much faster)
    start = time.time()
    db2 = get_service("database")
    time2 = time.time() - start
    print(f"Second access: {time2:.6f}s")
    
    if time1 > 0 and time2 > 0:
        speedup = time1 / time2
        print(f"Speedup: {speedup:.1f}x")
    
    # Show final cache stats
    final_stats = get_cache_stats()
    print(f"\nFinal cache stats: {final_stats}")