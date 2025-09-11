#!/usr/bin/env python3
"""
cached_service_locator.py - Service locator with integrated hybrid caching

This enhanced service locator automatically wraps services with caching.
All service access gets hybrid RAM + Database caching transparently.

Key Features:
- Transparent caching for all service locator calls
- Configurable cache policies per service
- Performance monitoring
- Cache management via 3-method pattern
"""

import sys
import os
from typing import Any, Dict, Optional, Union

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core.service_locator import ServiceLocator, NetworkServiceClient
from polymorphic_core import announcer
from utils.cached_service_wrapper import wrap_service_with_cache, service_cache_manager

class CachedServiceLocator(ServiceLocator):
    """
    Enhanced service locator with automatic hybrid caching
    
    This extends the base ServiceLocator to automatically wrap all services
    with the hybrid cache system (RAM + Database persistence).
    """
    
    def __init__(self, enable_caching: bool = True):
        super().__init__()
        self.enable_caching = enable_caching
        self.cached_services = {}  # Track which services are cached
        
        # Default cache configuration for different service types
        self.default_cache_configs = {
            # Core services - cache aggressively 
            "database": {
                "ask": {"enabled": True, "ttl": 1800, "invalidate_on_write": True},  # 30 min
                "tell": {"enabled": True, "ttl": 900, "invalidate_on_write": False},  # 15 min
                "do": {"enabled": False}  # Don't cache write operations
            },
            "logger": {
                "ask": {"enabled": True, "ttl": 300, "invalidate_on_write": False},  # 5 min
                "tell": {"enabled": True, "ttl": 600, "invalidate_on_write": False},  # 10 min
                "do": {"enabled": False}
            },
            "config": {
                "ask": {"enabled": True, "ttl": 3600, "invalidate_on_write": True},  # 1 hour
                "tell": {"enabled": True, "ttl": 1800, "invalidate_on_write": False},  # 30 min
                "do": {"enabled": False}
            },
            
            # Business services - moderate caching
            "claude": {
                "ask": {"enabled": True, "ttl": 300, "invalidate_on_write": False},  # 5 min
                "tell": {"enabled": True, "ttl": 600, "invalidate_on_write": False},  # 10 min
                "do": {"enabled": False}
            },
            "web_editor": {
                "ask": {"enabled": True, "ttl": 600, "invalidate_on_write": True},  # 10 min
                "tell": {"enabled": True, "ttl": 300, "invalidate_on_write": False},  # 5 min
                "do": {"enabled": False}
            },
            
            # Sync services - short caching due to data freshness
            "sync": {
                "ask": {"enabled": True, "ttl": 300, "invalidate_on_write": True},  # 5 min
                "tell": {"enabled": True, "ttl": 600, "invalidate_on_write": False},  # 10 min
                "do": {"enabled": False}
            }
        }
        
        # Announce caching capability
        announcer.announce(
            "Cached Service Locator",
            [
                "Service locator with hybrid caching",
                "Automatic RAM + Database cache layers",
                "Transparent caching for all services",
                "Configurable cache policies per service",
                "Performance monitoring and management"
            ],
            [
                "cached_locator.ask('cache stats')",
                "cached_locator.tell('text')",
                "cached_locator.do('clear cache')"
            ]
        )
    
    def get_service(self, capability_name: str, prefer_network: bool = False, enable_cache: Optional[bool] = None) -> Any:
        """
        Get a service with optional caching
        
        Args:
            capability_name: Service capability name
            prefer_network: Prefer network service over local
            enable_cache: Override global caching setting for this service
        
        Returns:
            Service (potentially wrapped with caching)
        """
        # Determine if caching should be enabled
        cache_enabled = enable_cache if enable_cache is not None else self.enable_caching
        
        # Check if we already have a cached version
        cache_key = f"{capability_name}_{prefer_network}_{cache_enabled}"
        if cache_key in self.cached_services:
            return self.cached_services[cache_key]
        
        # Get the base service from parent class
        service = super().get_service(capability_name, prefer_network)
        
        if service is None:
            return None
        
        # Wrap with caching if enabled
        if cache_enabled:
            cache_config = self.default_cache_configs.get(capability_name, {})
            wrapped_service = wrap_service_with_cache(
                service, 
                capability_name, 
                **cache_config
            )
            self.cached_services[cache_key] = wrapped_service
            return wrapped_service
        else:
            # Store uncached service
            self.cached_services[cache_key] = service
            return service
    
    def configure_service_cache(self, capability_name: str, **cache_config):
        """
        Configure caching for a specific service
        
        Args:
            capability_name: Service to configure
            **cache_config: Cache configuration (method -> config dict)
        """
        if capability_name not in self.default_cache_configs:
            self.default_cache_configs[capability_name] = {}
        
        self.default_cache_configs[capability_name].update(cache_config)
        
        # If service is already cached, update its configuration
        cached_service = service_cache_manager.get_cached_service(capability_name)
        if cached_service:
            for method, config in cache_config.items():
                if isinstance(config, dict):
                    cached_service.configure_cache(method, **config)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return service_cache_manager.get_all_stats()
    
    def clear_service_cache(self, capability_name: str = None):
        """Clear cache for specific service or all services"""
        if capability_name:
            cached_service = service_cache_manager.get_cached_service(capability_name)
            if cached_service:
                cached_service.clear_cache()
        else:
            service_cache_manager.clear_all_caches()
    
    def disable_caching(self):
        """Disable caching globally"""
        self.enable_caching = False
        self.cached_services.clear()
    
    def enable_caching(self):
        """Enable caching globally"""
        self.enable_caching = True
    
    # 3-Method pattern for cache management
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query cached service locator"""
        query_lower = query.lower().strip()
        
        if "cache" in query_lower and ("stats" in query_lower or "statistics" in query_lower):
            return self.get_cache_stats()
        elif "services" in query_lower and "cached" in query_lower:
            return list(self.cached_services.keys())
        elif "cache" in query_lower and "config" in query_lower:
            return self.default_cache_configs
        elif "hit rate" in query_lower:
            stats = self.get_cache_stats()
            global_stats = stats.get("_global_cache", {})
            return {"global_hit_rate": global_stats.get("hit_rate", 0)}
        else:
            # Fall back to base service locator behavior
            return {"available_services": list(self.capability_map.keys())}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """Format cached service locator information"""
        if data is None:
            data = self.get_cache_stats()
        
        return service_cache_manager.tell(format_type, data, **kwargs)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform cache management actions"""
        action_lower = action.lower().strip()
        
        if "clear" in action_lower and "cache" in action_lower:
            if "all" in action_lower:
                self.clear_service_cache()
                return {"status": "cleared all service caches"}
            else:
                service_name = kwargs.get("service")
                if service_name:
                    self.clear_service_cache(service_name)
                    return {"status": f"cleared cache for {service_name}"}
                else:
                    return {"error": "service name required for selective cache clear"}
        
        elif "disable" in action_lower and "cache" in action_lower:
            self.disable_caching()
            return {"status": "caching disabled"}
        
        elif "enable" in action_lower and "cache" in action_lower:
            self.enable_caching()
            return {"status": "caching enabled"}
        
        else:
            return {"error": f"Unknown cached service locator action: {action}"}

# Global cached service locator instance
cached_service_locator = CachedServiceLocator()

# Updated convenience functions
def get_service(capability_name: str, prefer_network: bool = False, enable_cache: Optional[bool] = None) -> Any:
    """Get a service with automatic hybrid caching"""
    return cached_service_locator.get_service(capability_name, prefer_network, enable_cache)

def get_service_no_cache(capability_name: str, prefer_network: bool = False) -> Any:
    """Get a service without caching"""
    return cached_service_locator.get_service(capability_name, prefer_network, enable_cache=False)

def configure_service_cache(capability_name: str, **cache_config):
    """Configure caching for a specific service"""
    cached_service_locator.configure_service_cache(capability_name, **cache_config)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return cached_service_locator.get_cache_stats()

def clear_cache(service_name: str = None):
    """Clear cache"""
    cached_service_locator.clear_service_cache(service_name)

if __name__ == "__main__":
    # Test the cached service locator
    print("🧪 Testing Cached Service Locator")
    
    # Test getting a service with caching
    print("\n1. Testing cached service access:")
    database = get_service("database")
    print(f"   Database service: {type(database).__name__}")
    
    # Test cache statistics
    print("\n2. Testing cache statistics:")
    stats = get_cache_stats()
    print(f"   Services tracked: {len(stats) - 1}")  # -1 for _global_cache
    
    # Test configuration
    print("\n3. Testing cache configuration:")
    configure_service_cache("database", ask={"ttl": 1200})
    print("   Database cache TTL updated")
    
    # Test 3-method pattern
    print("\n4. Testing 3-method pattern:")
    result = cached_service_locator.ask("cache stats")
    print(f"   Stats keys: {list(result.keys()) if isinstance(result, dict) else 'Not dict'}")
    
    formatted = cached_service_locator.tell("text")
    print(f"   Formatted stats length: {len(formatted)} characters")
    
    action_result = cached_service_locator.do("clear cache all")
    print(f"   Clear action: {action_result}")
    
    print("\n✅ Cached service locator test complete!")