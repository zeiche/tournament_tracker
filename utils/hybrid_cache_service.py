#!/usr/bin/env python3
"""
hybrid_cache_service.py - Hybrid cache service with RAM + Database persistence

Architecture:
- L1 Cache: RAM-based for real-time access (millisecond response)
- L2 Cache: Database table for persistence (session persistence)
- Write-through strategy: Updates both RAM and database
- Read strategy: RAM first, fallback to database, populate RAM

Key Features:
- Service locator integration
- 3-method polymorphic pattern
- TTL support for cache expiration
- Cache invalidation strategies
- Performance metrics
"""

import sys
import os
import threading
import time
import json
import hashlib
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.database import session_scope

Base = declarative_base()

class CacheEntry(Base):
    """Database table for cache persistence"""
    __tablename__ = 'service_cache_entries'
    
    id = Column(Integer, primary_key=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    method_name = Column(String(50), nullable=False)  # ask, tell, do
    cache_value = Column(Text, nullable=False)  # JSON serialized
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True, index=True)
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)

@dataclass
class CacheStats:
    """Cache performance statistics"""
    ram_hits: int = 0
    ram_misses: int = 0
    db_hits: int = 0
    db_misses: int = 0
    total_entries: int = 0
    expired_entries: int = 0
    ram_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.ram_hits + self.ram_misses + self.db_hits + self.db_misses
        if total == 0:
            return 0.0
        hits = self.ram_hits + self.db_hits
        return (hits / total) * 100
    
    @property
    def ram_hit_rate(self) -> float:
        total = self.ram_hits + self.ram_misses
        if total == 0:
            return 0.0
        return (self.ram_hits / total) * 100

class HybridCacheService:
    """
    Hybrid cache service with RAM + Database layers
    
    L1 Cache (RAM):
    - Ultra-fast access (microseconds)
    - Limited size (configurable)
    - Volatile (lost on restart)
    
    L2 Cache (Database):
    - Persistent across restarts
    - Unlimited size (disk-based)
    - Slower access (milliseconds)
    
    Strategy:
    - Read: RAM first → Database fallback → Populate RAM
    - Write: Write-through to both RAM and Database
    - Eviction: LRU for RAM, TTL for both layers
    """
    
    def __init__(self, max_ram_entries: int = 10000, default_ttl: int = 3600):
        self.max_ram_entries = max_ram_entries
        self.default_ttl = default_ttl  # seconds
        
        # L1 Cache: RAM-based dictionary
        self._ram_cache: Dict[str, Dict[str, Any]] = {}
        self._ram_access_order: List[str] = []  # LRU tracking
        self._ram_lock = threading.RLock()
        
        # Performance statistics
        self._stats = CacheStats()
        self._stats_lock = threading.Lock()
        
        # Service dependencies (lazy-loaded via service locator)
        self._database = None
        self._logger = None
        self._error_handler = None
        
        # Initialize database table
        self._ensure_cache_table()
        
        # Announce ourselves
        announcer.announce(
            "Hybrid Cache Service",
            [
                "L1 RAM cache for real-time access",
                "L2 Database cache for persistence", 
                "Write-through cache strategy",
                "TTL and LRU eviction policies",
                "Performance metrics and monitoring",
                "Service locator integration"
            ],
            [
                "cache.ask('get key123')",
                "cache.tell('stats')",
                "cache.do('clear all')"
            ]
        )
    
    @property
    def database(self):
        """Lazy-loaded database service"""
        if self._database is None:
            self._database = get_service("database")
        return self._database
    
    @property
    def logger(self):
        """Lazy-loaded logger service"""
        if self._logger is None:
            self._logger = get_service("logger")
        return self._logger
    
    @property
    def error_handler(self):
        """Lazy-loaded error handler service"""
        if self._error_handler is None:
            self._error_handler = get_service("error_handler")
        return self._error_handler
    
    def _ensure_cache_table(self):
        """Create cache table if it doesn't exist"""
        try:
            # Use main tournament database
            from sqlalchemy import inspect
            with session_scope() as session:
                inspector = inspect(session.bind)
                if not inspector.has_table('service_cache_entries'):
                    Base.metadata.create_all(session.bind)
                    if self.logger:
                        self.logger.info("Created service_cache_entries table")
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_exception(e, "MEDIUM")
    
    def _safe_json_dumps(self, value):
        """Safely serialize value to JSON, handling complex objects"""
        try:
            return json.dumps(value)
        except TypeError:
            # Handle non-serializable objects
            if hasattr(value, '__dict__'):
                return json.dumps(value.__dict__)
            elif hasattr(value, '_asdict'):
                return json.dumps(value._asdict())
            else:
                return json.dumps(str(value))
    
    def _make_cache_key(self, service: str, method: str, *args, **kwargs) -> str:
        """Generate consistent cache key"""
        key_data = {
            'service': service,
            'method': method,
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]
    
    def _update_ram_access_order(self, key: str):
        """Update LRU order for RAM cache"""
        with self._ram_lock:
            if key in self._ram_access_order:
                self._ram_access_order.remove(key)
            self._ram_access_order.append(key)
    
    def _evict_ram_if_needed(self):
        """Evict oldest entries from RAM if over limit"""
        with self._ram_lock:
            while len(self._ram_cache) >= self.max_ram_entries:
                if self._ram_access_order:
                    oldest_key = self._ram_access_order.pop(0)
                    self._ram_cache.pop(oldest_key, None)
                else:
                    break
    
    def _get_from_ram(self, key: str) -> Optional[Any]:
        """Get value from RAM cache"""
        with self._ram_lock:
            entry = self._ram_cache.get(key)
            if entry is None:
                with self._stats_lock:
                    self._stats.ram_misses += 1
                return None
            
            # Check TTL
            if entry.get('expires_at') and datetime.utcnow() > entry['expires_at']:
                self._ram_cache.pop(key, None)
                if key in self._ram_access_order:
                    self._ram_access_order.remove(key)
                with self._stats_lock:
                    self._stats.ram_misses += 1
                    self._stats.expired_entries += 1
                return None
            
            # Update access order and stats
            self._update_ram_access_order(key)
            with self._stats_lock:
                self._stats.ram_hits += 1
                
            return entry['value']
    
    def _set_to_ram(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in RAM cache"""
        with self._ram_lock:
            self._evict_ram_if_needed()
            
            expires_at = None
            if ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            self._ram_cache[key] = {
                'value': value,
                'created_at': datetime.utcnow(),
                'expires_at': expires_at
            }
            self._update_ram_access_order(key)
            
            with self._stats_lock:
                self._stats.ram_size = len(self._ram_cache)
    
    def _get_from_database(self, key: str) -> Optional[Any]:
        """Get value from database cache"""
        try:
            with session_scope() as session:
                entry = session.query(CacheEntry).filter(
                    CacheEntry.cache_key == key
                ).first()
                
                if entry is None:
                    with self._stats_lock:
                        self._stats.db_misses += 1
                    return None
                
                # Check TTL
                if entry.expires_at and datetime.utcnow() > entry.expires_at:
                    session.delete(entry)
                    session.commit()
                    with self._stats_lock:
                        self._stats.db_misses += 1
                        self._stats.expired_entries += 1
                    return None
                
                # Update access stats
                entry.hit_count += 1
                entry.last_accessed = datetime.utcnow()
                session.commit()
                
                with self._stats_lock:
                    self._stats.db_hits += 1
                
                # Deserialize value
                return json.loads(entry.cache_value)
                
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_exception(e, "MEDIUM")
            with self._stats_lock:
                self._stats.db_misses += 1
            return None
    
    def _set_to_database(self, key: str, service: str, method: str, value: Any, ttl: Optional[int] = None):
        """Set value in database cache"""
        try:
            with session_scope() as session:
                expires_at = None
                if ttl:
                    expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                
                # Upsert entry
                entry = session.query(CacheEntry).filter(
                    CacheEntry.cache_key == key
                ).first()
                
                if entry:
                    entry.cache_value = self._safe_json_dumps(value)
                    entry.expires_at = expires_at
                    entry.last_accessed = datetime.utcnow()
                else:
                    entry = CacheEntry(
                        cache_key=key,
                        service_name=service,
                        method_name=method,
                        cache_value=self._safe_json_dumps(value),
                        expires_at=expires_at
                    )
                    session.add(entry)
                
                session.commit()
                
                with self._stats_lock:
                    # Update total count
                    self._stats.total_entries = session.query(CacheEntry).count()
                
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_exception(e, "MEDIUM")
    
    def get(self, service: str, method: str, *args, ttl: Optional[int] = None, **kwargs) -> Optional[Any]:
        """
        Get cached value with hybrid L1/L2 strategy
        
        1. Check RAM cache first (microseconds)
        2. Check database cache (milliseconds) 
        3. Populate RAM cache from database hit
        4. Return None if not found in either
        """
        key = self._make_cache_key(service, method, *args, **kwargs)
        
        # L1: Try RAM first
        value = self._get_from_ram(key)
        if value is not None:
            return value
        
        # L2: Try database
        value = self._get_from_database(key)
        if value is not None:
            # Populate RAM cache
            cache_ttl = ttl or self.default_ttl
            self._set_to_ram(key, value, cache_ttl)
            return value
        
        return None
    
    def set(self, service: str, method: str, value: Any, *args, ttl: Optional[int] = None, **kwargs):
        """
        Set cached value with write-through strategy
        
        1. Write to RAM cache immediately
        2. Write to database cache for persistence
        """
        key = self._make_cache_key(service, method, *args, **kwargs)
        cache_ttl = ttl or self.default_ttl
        
        # Write-through to both layers
        self._set_to_ram(key, value, cache_ttl)
        self._set_to_database(key, service, method, value, cache_ttl)
    
    def invalidate(self, service: str, method: str, *args, **kwargs):
        """Invalidate cache entry from both layers"""
        key = self._make_cache_key(service, method, *args, **kwargs)
        
        # Remove from RAM
        with self._ram_lock:
            self._ram_cache.pop(key, None)
            if key in self._ram_access_order:
                self._ram_access_order.remove(key)
        
        # Remove from database
        try:
            with session_scope() as session:
                session.query(CacheEntry).filter(
                    CacheEntry.cache_key == key
                ).delete()
                session.commit()
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_exception(e, "MEDIUM")
    
    def invalidate_service(self, service: str):
        """Invalidate all cache entries for a service"""
        # Clear from RAM
        with self._ram_lock:
            keys_to_remove = []
            for key in self._ram_cache:
                # We'd need to store service name in RAM entries to make this efficient
                # For now, we'll clear by checking the key pattern
                pass  # TODO: Optimize this
        
        # Clear from database
        try:
            with session_scope() as session:
                session.query(CacheEntry).filter(
                    CacheEntry.service_name == service
                ).delete()
                session.commit()
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_exception(e, "MEDIUM")
    
    def clear_expired(self):
        """Remove expired entries from both layers"""
        now = datetime.utcnow()
        
        # Clear from RAM
        with self._ram_lock:
            expired_keys = []
            for key, entry in self._ram_cache.items():
                if entry.get('expires_at') and now > entry['expires_at']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._ram_cache.pop(key, None)
                if key in self._ram_access_order:
                    self._ram_access_order.remove(key)
        
        # Clear from database
        try:
            with session_scope() as session:
                deleted = session.query(CacheEntry).filter(
                    CacheEntry.expires_at < now
                ).delete()
                session.commit()
                
                if deleted > 0 and self.logger:
                    self.logger.info(f"Cleared {deleted} expired cache entries")
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_exception(e, "MEDIUM")
    
    def get_stats(self) -> CacheStats:
        """Get current cache statistics"""
        with self._stats_lock:
            stats = CacheStats(
                ram_hits=self._stats.ram_hits,
                ram_misses=self._stats.ram_misses,
                db_hits=self._stats.db_hits,
                db_misses=self._stats.db_misses,
                total_entries=self._stats.total_entries,
                expired_entries=self._stats.expired_entries,
                ram_size=len(self._ram_cache)
            )
        
        # Get fresh database count
        try:
            with session_scope() as session:
                stats.total_entries = session.query(CacheEntry).count()
        except Exception:
            pass
        
        return stats
    
    # 3-Method Polymorphic Pattern Implementation
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query cache information"""
        query_lower = query.lower().strip()
        
        if "stats" in query_lower or "statistics" in query_lower:
            return asdict(self.get_stats())
        elif "hit rate" in query_lower:
            return {"hit_rate": self.get_stats().hit_rate}
        elif "size" in query_lower or "count" in query_lower:
            stats = self.get_stats()
            return {
                "ram_size": stats.ram_size,
                "db_size": stats.total_entries,
                "total_size": stats.ram_size + stats.total_entries
            }
        else:
            return {"error": f"Unknown cache query: {query}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """Format cache information"""
        if data is None:
            data = asdict(self.get_stats())
        
        if format_type.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        elif format_type.lower() == "text":
            if isinstance(data, dict) and "hit_rate" in data:
                return f"""
Hybrid Cache Statistics:
========================
RAM Cache:
  Hits: {data.get('ram_hits', 0)}
  Misses: {data.get('ram_misses', 0)}
  Hit Rate: {data.get('ram_hit_rate', 0):.1f}%
  Size: {data.get('ram_size', 0)} entries

Database Cache:
  Hits: {data.get('db_hits', 0)}
  Misses: {data.get('db_misses', 0)}
  Total Entries: {data.get('total_entries', 0)}

Overall:
  Hit Rate: {data.get('hit_rate', 0):.1f}%
  Expired: {data.get('expired_entries', 0)}
""".strip()
            else:
                return str(data)
        else:
            return json.dumps(data, default=str)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform cache actions"""
        action_lower = action.lower().strip()
        
        if "clear" in action_lower and "expired" in action_lower:
            self.clear_expired()
            return {"status": "cleared expired entries"}
        elif "clear" in action_lower and "all" in action_lower:
            # Clear everything
            with self._ram_lock:
                self._ram_cache.clear()
                self._ram_access_order.clear()
            
            try:
                with session_scope() as session:
                    session.query(CacheEntry).delete()
                    session.commit()
            except Exception as e:
                return {"error": f"Failed to clear database cache: {e}"}
            
            return {"status": "cleared all cache entries"}
        elif "reset" in action_lower and "stats" in action_lower:
            with self._stats_lock:
                self._stats = CacheStats()
            return {"status": "reset statistics"}
        else:
            return {"error": f"Unknown cache action: {action}"}

# Global instance
hybrid_cache_service = HybridCacheService()

# Convenience functions for service locator integration
def get_cache_service():
    """Get the hybrid cache service"""
    return hybrid_cache_service

if __name__ == "__main__":
    # Test the hybrid cache service
    print("🧪 Testing Hybrid Cache Service")
    
    cache = hybrid_cache_service
    
    # Test basic operations
    print("\n1. Testing cache operations:")
    cache.set("test_service", "ask", "cached_result", "test_query")
    
    # Test retrieval
    result = cache.get("test_service", "ask", "test_query")
    print(f"   Cached result: {result}")
    
    # Test stats
    print("\n2. Cache statistics:")
    print(cache.tell("text"))
    
    # Test 3-method pattern
    print("\n3. Testing 3-method pattern:")
    stats = cache.ask("stats")
    print(f"   Stats query: {stats}")
    
    formatted = cache.tell("json", stats)
    print(f"   JSON format: {formatted[:100]}...")
    
    result = cache.do("clear expired")
    print(f"   Clear action: {result}")
    
    print("\n✅ Hybrid cache service test complete!")