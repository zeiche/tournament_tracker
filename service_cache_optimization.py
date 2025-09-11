#!/usr/bin/env python3
"""
service_cache_optimization.py - Hybrid service discovery cache

Implements a two-tier caching system:
- L1 Cache (RAM): Fast access for active services
- L2 Cache (Database): Persistent discovery results for faster startup

This optimizes both runtime performance and startup times.
"""
import time
import json
import sqlite3
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from polymorphic_core.service_locator import service_locator


@dataclass
class CacheEntry:
    """Represents a cached service discovery result"""
    capability: str
    service_type: str  # 'local' or 'network'
    module_path: str
    host: Optional[str] = None
    port: Optional[int] = None
    last_used: float = 0
    discovery_time: float = 0
    success_count: int = 0
    failure_count: int = 0


class HybridServiceCache:
    """
    Two-tier service discovery cache for optimal performance.
    
    L1 (RAM): Active service instances for microsecond access
    L2 (Database): Discovery metadata for faster startup and sharing
    """
    
    def __init__(self, db_path: str = "service_cache.db"):
        self.db_path = db_path
        self.l1_cache = {}  # RAM cache (same as current)
        self.l2_cache = {}  # Database cache metadata
        self.cache_stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'cache_misses': 0,
            'discoveries': 0,
            'persistent_saves': 0
        }
        
        # Initialize database
        self._init_database()
        self._load_l2_cache()
    
    def _init_database(self):
        """Initialize the service cache database table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS service_cache (
                    capability TEXT PRIMARY KEY,
                    service_type TEXT NOT NULL,
                    module_path TEXT NOT NULL,
                    host TEXT,
                    port INTEGER,
                    last_used REAL NOT NULL,
                    discovery_time REAL NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at REAL DEFAULT (julianday('now')),
                    updated_at REAL DEFAULT (julianday('now'))
                )
            """)
            
            # Index for performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_service_cache_last_used 
                ON service_cache(last_used)
            """)
    
    def _load_l2_cache(self):
        """Load persistent cache from database into memory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM service_cache 
                    ORDER BY last_used DESC
                """)
                
                for row in cursor:
                    entry = CacheEntry(
                        capability=row['capability'],
                        service_type=row['service_type'],
                        module_path=row['module_path'],
                        host=row['host'],
                        port=row['port'],
                        last_used=row['last_used'],
                        discovery_time=row['discovery_time'],
                        success_count=row['success_count'],
                        failure_count=row['failure_count']
                    )
                    self.l2_cache[row['capability']] = entry
                
                print(f"🔄 Loaded {len(self.l2_cache)} cached service discoveries")
        except Exception as e:
            print(f"⚠️  Could not load L2 cache: {e}")
    
    def get_service(self, capability: str, prefer_network: bool = False):
        """
        Get service with hybrid caching.
        
        1. Check L1 cache (RAM) first
        2. Check L2 cache (Database) for discovery hints
        3. Fall back to full discovery
        """
        start_time = time.time()
        
        # L1 Cache check (RAM)
        if capability in self.l1_cache:
            self.cache_stats['l1_hits'] += 1
            self._update_usage(capability)
            return self.l1_cache[capability]
        
        # L2 Cache check (Database metadata)
        if capability in self.l2_cache:
            self.cache_stats['l2_hits'] += 1
            entry = self.l2_cache[capability]
            
            # Try to restore service from cached metadata
            try:
                if entry.service_type == 'local':
                    service = self._restore_local_service(entry)
                else:
                    service = self._restore_network_service(entry)
                
                if service:
                    # Cache in L1 for future use
                    self.l1_cache[capability] = service
                    self._update_usage(capability, success=True)
                    return service
                else:
                    self._update_usage(capability, success=False)
            except Exception as e:
                print(f"⚠️  L2 cache restore failed for {capability}: {e}")
                self._update_usage(capability, success=False)
        
        # Cache miss - perform full discovery
        self.cache_stats['cache_misses'] += 1
        self.cache_stats['discoveries'] += 1
        
        # Use original service locator for discovery
        service = service_locator.get_service(capability, prefer_network)
        
        if service:
            # Cache in L1
            self.l1_cache[capability] = service
            
            # Cache metadata in L2
            self._cache_discovery_result(capability, service, prefer_network, time.time() - start_time)
        
        return service
    
    def _restore_local_service(self, entry: CacheEntry):
        """Restore a local service from cached metadata"""
        try:
            # Use the original service locator's local discovery
            return service_locator._get_local_service(entry.capability)
        except Exception:
            return None
    
    def _restore_network_service(self, entry: CacheEntry):
        """Restore a network service from cached metadata"""
        try:
            if entry.host and entry.port:
                # Create network service client
                from polymorphic_core.service_locator import NetworkServiceClient
                return NetworkServiceClient(
                    service_name=entry.capability,
                    host=entry.host,
                    port=entry.port,
                    capabilities=[f"Cached {entry.capability} service"]
                )
        except Exception:
            return None
    
    def _cache_discovery_result(self, capability: str, service: Any, prefer_network: bool, discovery_time: float):
        """Cache a successful discovery result in L2"""
        try:
            # Determine service type and metadata
            service_type = 'network' if prefer_network else 'local'
            module_path = service_locator.capability_map.get(capability, 'unknown')
            host = getattr(service, 'host', None) if hasattr(service, 'host') else None
            port = getattr(service, 'port', None) if hasattr(service, 'port') else None
            
            # Create cache entry
            entry = CacheEntry(
                capability=capability,
                service_type=service_type,
                module_path=module_path,
                host=host,
                port=port,
                last_used=time.time(),
                discovery_time=discovery_time,
                success_count=1,
                failure_count=0
            )
            
            # Store in L2 cache (memory)
            self.l2_cache[capability] = entry
            
            # Store in database
            self._persist_cache_entry(entry)
            self.cache_stats['persistent_saves'] += 1
            
        except Exception as e:
            print(f"⚠️  Failed to cache discovery result for {capability}: {e}")
    
    def _persist_cache_entry(self, entry: CacheEntry):
        """Persist cache entry to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO service_cache 
                    (capability, service_type, module_path, host, port, 
                     last_used, discovery_time, success_count, failure_count, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, julianday('now'))
                """, (
                    entry.capability,
                    entry.service_type,
                    entry.module_path,
                    entry.host,
                    entry.port,
                    entry.last_used,
                    entry.discovery_time,
                    entry.success_count,
                    entry.failure_count
                ))
        except Exception as e:
            print(f"⚠️  Failed to persist cache entry: {e}")
    
    def _update_usage(self, capability: str, success: bool = True):
        """Update usage statistics for a cached service"""
        if capability in self.l2_cache:
            entry = self.l2_cache[capability]
            entry.last_used = time.time()
            
            if success:
                entry.success_count += 1
            else:
                entry.failure_count += 1
            
            # Update database periodically (not every time for performance)
            if (entry.success_count + entry.failure_count) % 10 == 0:
                self._persist_cache_entry(entry)
    
    def clear_cache(self, cache_type: str = 'both'):
        """Clear cache (L1, L2, or both)"""
        if cache_type in ['l1', 'both']:
            self.l1_cache.clear()
            print("🧹 Cleared L1 (RAM) cache")
        
        if cache_type in ['l2', 'both']:
            self.l2_cache.clear()
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM service_cache")
                print("🧹 Cleared L2 (Database) cache")
            except Exception as e:
                print(f"⚠️  Could not clear L2 cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        l1_size = len(self.l1_cache)
        l2_size = len(self.l2_cache)
        total_requests = sum(self.cache_stats.values())
        
        if total_requests > 0:
            l1_hit_rate = (self.cache_stats['l1_hits'] / total_requests) * 100
            l2_hit_rate = (self.cache_stats['l2_hits'] / total_requests) * 100
            miss_rate = (self.cache_stats['cache_misses'] / total_requests) * 100
        else:
            l1_hit_rate = l2_hit_rate = miss_rate = 0
        
        return {
            'cache_sizes': {
                'l1_ram_cache': l1_size,
                'l2_database_cache': l2_size
            },
            'hit_rates': {
                'l1_hit_rate_percent': round(l1_hit_rate, 2),
                'l2_hit_rate_percent': round(l2_hit_rate, 2),
                'miss_rate_percent': round(miss_rate, 2)
            },
            'raw_stats': self.cache_stats,
            'cache_efficiency': round((l1_hit_rate + l2_hit_rate), 2)
        }
    
    def cleanup_old_entries(self, max_age_days: int = 30):
        """Remove old cache entries to prevent unlimited growth"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM service_cache 
                    WHERE last_used < ?
                """, (cutoff_time,))
                
                deleted_count = cursor.rowcount
                print(f"🧹 Cleaned up {deleted_count} old cache entries")
                
                # Reload L2 cache
                self._load_l2_cache()
                
        except Exception as e:
            print(f"⚠️  Cache cleanup failed: {e}")


# Global hybrid cache instance
hybrid_cache = HybridServiceCache()


def optimized_get_service(capability: str, prefer_network: bool = False):
    """Drop-in replacement for get_service with hybrid caching"""
    return hybrid_cache.get_service(capability, prefer_network)


if __name__ == "__main__":
    # Demo the hybrid cache
    print("🔄 Hybrid Service Cache Demo")
    print("=" * 40)
    
    # Show initial stats
    stats = hybrid_cache.get_cache_stats()
    print(f"Initial state: {stats}")
    
    # Test service access
    print("\nTesting service access...")
    
    # First access (should be cache miss)
    print("First access to database service:")
    start = time.time()
    db1 = hybrid_cache.get_service("database")
    time1 = time.time() - start
    print(f"  Time: {time1:.3f}s")
    
    # Second access (should be L1 hit)
    print("Second access to database service:")
    start = time.time()
    db2 = hybrid_cache.get_service("database")
    time2 = time.time() - start
    print(f"  Time: {time2:.3f}s (speedup: {time1/time2:.1f}x)")
    
    # Show final stats
    stats = hybrid_cache.get_cache_stats()
    print(f"\nFinal stats: {stats}")