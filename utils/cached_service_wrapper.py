#!/usr/bin/env python3
"""
cached_service_wrapper.py - Service wrapper with hybrid caching

This wrapper automatically caches service calls using the hybrid cache system.
It decorates any service to add caching without changing the service code.

Key Features:
- Transparent caching for ask/tell/do methods
- Configurable TTL per service/method
- Cache invalidation on write operations
- Performance metrics
- Service locator integration
"""

import sys
import os
import functools
import hashlib
import json
from typing import Any, Dict, List, Optional, Union, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core import announcer
from utils.hybrid_cache_service import hybrid_cache_service

class CachedServiceWrapper:
    """
    Wrapper that adds hybrid caching to any service
    
    Usage:
        original_service = get_service("database")
        cached_service = CachedServiceWrapper(original_service, "database")
        
        # Now calls are cached automatically
        result = cached_service.ask("stats")  # Cached for 1 hour
        result = cached_service.ask("stats")  # Returns from cache (fast!)
    """
    
    def __init__(self, service: Any, service_name: str, default_ttl: int = 3600):
        self._wrapped_service = service
        self._service_name = service_name
        self._default_ttl = default_ttl
        
        # Method-specific cache settings
        self._cache_config = {
            # ask() methods - cache read operations
            "ask": {
                "enabled": True,
                "ttl": 3600,  # 1 hour
                "invalidate_on_write": True
            },
            # tell() methods - cache formatting operations
            "tell": {
                "enabled": True,
                "ttl": 1800,  # 30 minutes
                "invalidate_on_write": False
            },
            # do() methods - usually don't cache write operations
            "do": {
                "enabled": False,  # Don't cache writes by default
                "ttl": 60,
                "invalidate_on_write": False
            }
        }
        
        # Performance tracking
        self._call_count = 0
        self._cache_hit_count = 0
        
        # Announce caching capability
        announcer.announce(
            f"Cached {service_name} Service",
            [
                f"Hybrid caching for {service_name}",
                "RAM + Database cache layers",
                "Configurable TTL per method",
                "Automatic cache invalidation"
            ]
        )
    
    def configure_cache(self, method: str, enabled: bool = True, ttl: int = None, invalidate_on_write: bool = None):
        """Configure caching for a specific method"""
        if method not in self._cache_config:
            self._cache_config[method] = {}
        
        self._cache_config[method]["enabled"] = enabled
        if ttl is not None:
            self._cache_config[method]["ttl"] = ttl
        if invalidate_on_write is not None:
            self._cache_config[method]["invalidate_on_write"] = invalidate_on_write
    
    def _should_cache_method(self, method_name: str) -> bool:
        """Check if method should be cached"""
        config = self._cache_config.get(method_name, {})
        return config.get("enabled", False)
    
    def _get_method_ttl(self, method_name: str) -> int:
        """Get TTL for method"""
        config = self._cache_config.get(method_name, {})
        return config.get("ttl", self._default_ttl)
    
    def _should_invalidate_on_write(self, method_name: str) -> bool:
        """Check if method should invalidate cache on write"""
        config = self._cache_config.get(method_name, {})
        return config.get("invalidate_on_write", False)
    
    def _is_write_operation(self, method_name: str, *args, **kwargs) -> bool:
        """Determine if this is a write operation that should invalidate cache"""
        if method_name == "do":
            return True  # do() methods are typically write operations
        
        if method_name == "ask":
            # Check if query suggests a read-only operation
            if args and isinstance(args[0], str):
                query = args[0].lower()
                write_keywords = ["update", "insert", "delete", "create", "drop", "alter", "set", "reset"]
                return any(keyword in query for keyword in write_keywords)
        
        return False
    
    def _invalidate_service_cache(self):
        """Invalidate all cache entries for this service"""
        hybrid_cache_service.invalidate_service(self._service_name)
    
    def ask(self, query: str, **kwargs) -> Any:
        """Cached ask method"""
        self._call_count += 1
        
        if not self._should_cache_method("ask"):
            return self._wrapped_service.ask(query, **kwargs)
        
        # Try cache first
        cached_result = hybrid_cache_service.get(
            self._service_name, "ask", query, **kwargs
        )
        
        if cached_result is not None:
            self._cache_hit_count += 1
            return cached_result
        
        # Call original service
        result = self._wrapped_service.ask(query, **kwargs)
        
        # Cache the result
        ttl = self._get_method_ttl("ask")
        hybrid_cache_service.set(
            self._service_name, "ask", result, query, ttl=ttl, **kwargs
        )
        
        # Invalidate cache if this was a write operation
        if self._is_write_operation("ask", query, **kwargs):
            if self._should_invalidate_on_write("ask"):
                self._invalidate_service_cache()
        
        return result
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """Cached tell method"""
        self._call_count += 1
        
        if not self._should_cache_method("tell"):
            return self._wrapped_service.tell(format_type, data, **kwargs)
        
        # Try cache first
        cached_result = hybrid_cache_service.get(
            self._service_name, "tell", format_type, data, **kwargs
        )
        
        if cached_result is not None:
            self._cache_hit_count += 1
            return cached_result
        
        # Call original service
        result = self._wrapped_service.tell(format_type, data, **kwargs)
        
        # Cache the result
        ttl = self._get_method_ttl("tell")
        hybrid_cache_service.set(
            self._service_name, "tell", result, format_type, data, ttl=ttl, **kwargs
        )
        
        return result
    
    def do(self, action: str, **kwargs) -> Any:
        """Cached do method (usually not cached)"""
        self._call_count += 1
        
        # For write operations, always invalidate cache first
        if self._is_write_operation("do", action, **kwargs):
            self._invalidate_service_cache()
        
        if not self._should_cache_method("do"):
            return self._wrapped_service.do(action, **kwargs)
        
        # Try cache first (rare for do operations)
        cached_result = hybrid_cache_service.get(
            self._service_name, "do", action, **kwargs
        )
        
        if cached_result is not None:
            self._cache_hit_count += 1
            return cached_result
        
        # Call original service
        result = self._wrapped_service.do(action, **kwargs)
        
        # Cache the result if configured
        ttl = self._get_method_ttl("do")
        hybrid_cache_service.set(
            self._service_name, "do", result, action, ttl=ttl, **kwargs
        )
        
        return result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics for this wrapper"""
        hit_rate = 0.0
        if self._call_count > 0:
            hit_rate = (self._cache_hit_count / self._call_count) * 100
        
        return {
            "service_name": self._service_name,
            "total_calls": self._call_count,
            "cache_hits": self._cache_hit_count,
            "cache_misses": self._call_count - self._cache_hit_count,
            "hit_rate": hit_rate,
            "cache_config": self._cache_config
        }
    
    def clear_cache(self):
        """Clear all cache entries for this service"""
        self._invalidate_service_cache()
    
    def __getattr__(self, name):
        """Delegate any other method calls to the wrapped service"""
        return getattr(self._wrapped_service, name)

class ServiceCacheManager:
    """
    Manager for cached service instances
    
    Provides a registry of cached services and global cache management
    """
    
    def __init__(self):
        self._cached_services: Dict[str, CachedServiceWrapper] = {}
        
        # Announce management capability
        announcer.announce(
            "Service Cache Manager",
            [
                "Manages cached service instances",
                "Global cache statistics",
                "Cache configuration management",
                "Bulk cache operations"
            ],
            [
                "cache_manager.ask('stats')",
                "cache_manager.do('clear all')"
            ]
        )
    
    def wrap_service(self, service: Any, service_name: str, **cache_config) -> CachedServiceWrapper:
        """Wrap a service with caching"""
        if service_name in self._cached_services:
            return self._cached_services[service_name]
        
        wrapper = CachedServiceWrapper(service, service_name)
        
        # Apply any configuration
        for method, config in cache_config.items():
            if isinstance(config, dict):
                wrapper.configure_cache(method, **config)
        
        self._cached_services[service_name] = wrapper
        return wrapper
    
    def get_cached_service(self, service_name: str) -> Optional[CachedServiceWrapper]:
        """Get cached service wrapper"""
        return self._cached_services.get(service_name)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all cached services"""
        stats = {}
        for service_name, wrapper in self._cached_services.items():
            stats[service_name] = wrapper.get_cache_stats()
        
        # Add global hybrid cache stats
        hybrid_stats = hybrid_cache_service.get_stats()
        stats["_global_cache"] = {
            "ram_hits": hybrid_stats.ram_hits,
            "ram_misses": hybrid_stats.ram_misses, 
            "db_hits": hybrid_stats.db_hits,
            "db_misses": hybrid_stats.db_misses,
            "hit_rate": hybrid_stats.hit_rate,
            "total_entries": hybrid_stats.total_entries,
            "ram_size": hybrid_stats.ram_size
        }
        
        return stats
    
    def clear_all_caches(self):
        """Clear all service caches"""
        for wrapper in self._cached_services.values():
            wrapper.clear_cache()
        
        # Also clear the global hybrid cache
        hybrid_cache_service.do("clear all")
    
    # 3-Method pattern for the cache manager itself
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query cache manager"""
        query_lower = query.lower().strip()
        
        if "stats" in query_lower or "statistics" in query_lower:
            return self.get_all_stats()
        elif "services" in query_lower:
            return list(self._cached_services.keys())
        elif "hit rate" in query_lower:
            stats = self.get_all_stats()
            return stats.get("_global_cache", {}).get("hit_rate", 0)
        else:
            return {"error": f"Unknown cache manager query: {query}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """Format cache manager information"""
        if data is None:
            data = self.get_all_stats()
        
        if format_type.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        elif format_type.lower() == "text":
            output = "Service Cache Statistics:\n"
            output += "=" * 50 + "\n"
            
            for service_name, stats in data.items():
                if service_name == "_global_cache":
                    output += f"\nGlobal Cache:\n"
                    output += f"  Hit Rate: {stats.get('hit_rate', 0):.1f}%\n"
                    output += f"  RAM Size: {stats.get('ram_size', 0)} entries\n"
                    output += f"  DB Size: {stats.get('total_entries', 0)} entries\n"
                else:
                    output += f"\n{service_name}:\n"
                    output += f"  Calls: {stats.get('total_calls', 0)}\n"
                    output += f"  Hits: {stats.get('cache_hits', 0)}\n"
                    output += f"  Hit Rate: {stats.get('hit_rate', 0):.1f}%\n"
            
            return output
        else:
            return json.dumps(data, default=str)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform cache manager actions"""
        action_lower = action.lower().strip()
        
        if "clear" in action_lower and "all" in action_lower:
            self.clear_all_caches()
            return {"status": "cleared all service caches"}
        elif "clear" in action_lower and "expired" in action_lower:
            hybrid_cache_service.clear_expired()
            return {"status": "cleared expired cache entries"}
        else:
            return {"error": f"Unknown cache manager action: {action}"}

# Global instance
service_cache_manager = ServiceCacheManager()

# Convenience functions
def wrap_service_with_cache(service: Any, service_name: str, **cache_config) -> CachedServiceWrapper:
    """Wrap a service with caching"""
    return service_cache_manager.wrap_service(service, service_name, **cache_config)

def get_cached_service(service_name: str) -> Optional[CachedServiceWrapper]:
    """Get cached service wrapper"""
    return service_cache_manager.get_cached_service(service_name)

if __name__ == "__main__":
    # Test the cached service wrapper
    print("🧪 Testing Cached Service Wrapper")
    
    # Mock service for testing
    class MockService:
        def ask(self, query):
            return f"Result for: {query}"
        
        def tell(self, format_type, data=None):
            return f"Formatted as {format_type}: {data}"
        
        def do(self, action):
            return f"Action performed: {action}"
    
    # Wrap with caching
    mock_service = MockService()
    cached_service = wrap_service_with_cache(mock_service, "mock_service")
    
    print("\n1. Testing cached operations:")
    result1 = cached_service.ask("test query")
    print(f"   First call: {result1}")
    
    result2 = cached_service.ask("test query")  # Should be cached
    print(f"   Second call (cached): {result2}")
    
    print("\n2. Cache statistics:")
    stats = cached_service.get_cache_stats()
    print(f"   Hit rate: {stats['hit_rate']:.1f}%")
    
    print("\n3. Manager statistics:")
    manager_stats = service_cache_manager.ask("stats")
    print(f"   Services cached: {len(manager_stats) - 1}")  # -1 for _global_cache
    
    print("\n✅ Cached service wrapper test complete!")