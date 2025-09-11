#!/usr/bin/env python3
"""
test_hybrid_cache_performance.py - Performance testing for hybrid cache system

Tests the performance characteristics of:
1. RAM cache access times
2. Database cache access times  
3. Cache miss penalties
4. Write-through performance
5. Cache invalidation speed
6. Memory usage
"""

import sys
import os
import time
import random
import threading
from statistics import mean, median
from typing import List, Dict, Any
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.hybrid_cache_service import hybrid_cache_service
from polymorphic_core.cached_service_locator import get_service, get_cache_stats, clear_cache

def benchmark_ram_cache_performance(iterations: int = 1000) -> Dict[str, float]:
    """Benchmark RAM cache performance"""
    print(f"🔥 RAM Cache Performance ({iterations} iterations)")
    print("=" * 60)
    
    service_name = "test_service"
    method = "ask"
    
    # Pre-populate some cache entries
    for i in range(100):
        hybrid_cache_service.set(service_name, method, f"cached_result_{i}", f"query_{i}", ttl=3600)
    
    # Test cache hits
    hit_times = []
    for i in range(iterations):
        query_id = random.randint(0, 99)  # Ensure cache hits
        
        start_time = time.perf_counter()
        result = hybrid_cache_service.get(service_name, method, f"query_{query_id}")
        end_time = time.perf_counter()
        
        if result is not None:
            hit_times.append((end_time - start_time) * 1000)  # Convert to ms
    
    # Test cache misses (RAM only)
    miss_times = []
    for i in range(100):  # Fewer iterations for misses
        start_time = time.perf_counter()
        result = hybrid_cache_service._get_from_ram(f"nonexistent_key_{i}")
        end_time = time.perf_counter()
        
        miss_times.append((end_time - start_time) * 1000)
    
    results = {
        "ram_hit_avg": mean(hit_times) if hit_times else 0,
        "ram_hit_median": median(hit_times) if hit_times else 0,
        "ram_hit_min": min(hit_times) if hit_times else 0,
        "ram_hit_max": max(hit_times) if hit_times else 0,
        "ram_miss_avg": mean(miss_times) if miss_times else 0,
        "cache_entries": len(hit_times)
    }
    
    print(f"   RAM Hit Average:    {results['ram_hit_avg']:.4f}ms")
    print(f"   RAM Hit Median:     {results['ram_hit_median']:.4f}ms")  
    print(f"   RAM Hit Range:      {results['ram_hit_min']:.4f} - {results['ram_hit_max']:.4f}ms")
    print(f"   RAM Miss Average:   {results['ram_miss_avg']:.4f}ms")
    print(f"   Speedup (miss/hit): {results['ram_miss_avg']/results['ram_hit_avg']:.1f}x" if results['ram_hit_avg'] > 0 else "N/A")
    
    return results

def benchmark_database_cache_performance(iterations: int = 100) -> Dict[str, float]:
    """Benchmark database cache performance"""
    print(f"\n💾 Database Cache Performance ({iterations} iterations)")
    print("=" * 60)
    
    service_name = "test_db_service"
    method = "ask"
    
    # Pre-populate database cache
    for i in range(50):
        hybrid_cache_service._set_to_database(
            f"db_key_{i}", service_name, method, f"db_result_{i}", ttl=3600
        )
    
    # Test database cache hits
    hit_times = []
    for i in range(iterations):
        query_id = random.randint(0, 49)  # Ensure cache hits
        
        start_time = time.perf_counter()
        result = hybrid_cache_service._get_from_database(f"db_key_{query_id}")
        end_time = time.perf_counter()
        
        if result is not None:
            hit_times.append((end_time - start_time) * 1000)
    
    # Test database cache misses
    miss_times = []
    for i in range(50):
        start_time = time.perf_counter()
        result = hybrid_cache_service._get_from_database(f"nonexistent_db_key_{i}")
        end_time = time.perf_counter()
        
        miss_times.append((end_time - start_time) * 1000)
    
    results = {
        "db_hit_avg": mean(hit_times) if hit_times else 0,
        "db_hit_median": median(hit_times) if hit_times else 0,
        "db_miss_avg": mean(miss_times) if miss_times else 0,
        "db_hit_min": min(hit_times) if hit_times else 0,
        "db_hit_max": max(hit_times) if hit_times else 0
    }
    
    print(f"   DB Hit Average:     {results['db_hit_avg']:.2f}ms")
    print(f"   DB Hit Median:      {results['db_hit_median']:.2f}ms")
    print(f"   DB Hit Range:       {results['db_hit_min']:.2f} - {results['db_hit_max']:.2f}ms")
    print(f"   DB Miss Average:    {results['db_miss_avg']:.2f}ms")
    
    return results

def benchmark_write_through_performance(iterations: int = 200) -> Dict[str, float]:
    """Benchmark write-through cache performance"""
    print(f"\n✍️  Write-Through Performance ({iterations} iterations)")
    print("=" * 60)
    
    service_name = "write_test_service"
    method = "ask"
    
    write_times = []
    
    for i in range(iterations):
        start_time = time.perf_counter()
        hybrid_cache_service.set(
            service_name, method, f"write_result_{i}", f"write_query_{i}", ttl=1800
        )
        end_time = time.perf_counter()
        
        write_times.append((end_time - start_time) * 1000)
    
    results = {
        "write_avg": mean(write_times),
        "write_median": median(write_times),
        "write_min": min(write_times),
        "write_max": max(write_times)
    }
    
    print(f"   Write Average:      {results['write_avg']:.2f}ms")
    print(f"   Write Median:       {results['write_median']:.2f}ms")
    print(f"   Write Range:        {results['write_min']:.2f} - {results['write_max']:.2f}ms")
    
    return results

def benchmark_cache_invalidation(iterations: int = 100) -> Dict[str, float]:
    """Benchmark cache invalidation performance"""
    print(f"\n🗑️  Cache Invalidation Performance ({iterations} iterations)")
    print("=" * 60)
    
    service_name = "invalidation_test"
    method = "ask"
    
    # Pre-populate cache entries
    for i in range(iterations):
        hybrid_cache_service.set(service_name, method, f"value_{i}", f"key_{i}", ttl=3600)
    
    # Benchmark individual invalidations
    invalidation_times = []
    for i in range(iterations):
        start_time = time.perf_counter()
        hybrid_cache_service.invalidate(service_name, method, f"key_{i}")
        end_time = time.perf_counter()
        
        invalidation_times.append((end_time - start_time) * 1000)
    
    # Benchmark service-wide invalidation
    # Pre-populate again
    for i in range(50):
        hybrid_cache_service.set(service_name, method, f"bulk_value_{i}", f"bulk_key_{i}", ttl=3600)
    
    start_time = time.perf_counter()
    hybrid_cache_service.invalidate_service(service_name)
    end_time = time.perf_counter()
    service_invalidation_time = (end_time - start_time) * 1000
    
    results = {
        "single_invalidation_avg": mean(invalidation_times),
        "single_invalidation_median": median(invalidation_times),
        "service_invalidation": service_invalidation_time
    }
    
    print(f"   Single Invalidation:  {results['single_invalidation_avg']:.2f}ms avg")
    print(f"   Service Invalidation: {results['service_invalidation']:.2f}ms (50 entries)")
    
    return results

def benchmark_cached_service_locator(iterations: int = 100) -> Dict[str, float]:
    """Benchmark cached service locator performance"""
    print(f"\n🔧 Cached Service Locator ({iterations} iterations)")
    print("=" * 60)
    
    # Clear existing cache
    clear_cache()
    
    # Test getting services (should cache service instances)
    service_creation_times = []
    for i in range(10):  # Create services multiple times
        start_time = time.perf_counter()
        database = get_service("database")  # This should be cached after first call
        end_time = time.perf_counter()
        service_creation_times.append((end_time - start_time) * 1000)
    
    # Test cached service method calls
    database = get_service("database")  # Get cached service
    
    first_call_times = []
    cached_call_times = []
    
    for i in range(iterations):
        query = f"test_query_{i}"
        
        # First call (should cache result)
        start_time = time.perf_counter()
        result1 = database.ask(query)
        end_time = time.perf_counter()
        first_call_times.append((end_time - start_time) * 1000)
        
        # Second call (should be cached)
        start_time = time.perf_counter()
        result2 = database.ask(query)
        end_time = time.perf_counter()
        cached_call_times.append((end_time - start_time) * 1000)
    
    results = {
        "service_creation_first": service_creation_times[0] if service_creation_times else 0,
        "service_creation_cached": mean(service_creation_times[1:]) if len(service_creation_times) > 1 else 0,
        "method_call_first": mean(first_call_times),
        "method_call_cached": mean(cached_call_times),
        "cache_speedup": mean(first_call_times) / mean(cached_call_times) if cached_call_times else 1
    }
    
    print(f"   Service Creation (first):  {results['service_creation_first']:.2f}ms")
    print(f"   Service Creation (cached): {results['service_creation_cached']:.2f}ms")
    print(f"   Method Call (first):       {results['method_call_first']:.2f}ms")
    print(f"   Method Call (cached):      {results['method_call_cached']:.2f}ms")
    print(f"   Cache Speedup:             {results['cache_speedup']:.1f}x")
    
    return results

def benchmark_memory_usage() -> Dict[str, int]:
    """Benchmark memory usage of cache system"""
    print(f"\n🧠 Memory Usage Analysis")
    print("=" * 60)
    
    tracemalloc.start()
    baseline = tracemalloc.get_traced_memory()[0]
    
    # Create cache entries
    service_name = "memory_test"
    method = "ask"
    
    for i in range(1000):
        value = f"Memory test result {i} with some data to make it realistic"
        hybrid_cache_service.set(service_name, method, value, f"memory_query_{i}", ttl=3600)
    
    after_ram = tracemalloc.get_traced_memory()[0]
    
    # Force database writes
    time.sleep(0.1)  # Let writes complete
    
    final_memory = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    
    results = {
        "baseline": baseline,
        "after_1000_entries": after_ram - baseline,
        "final_memory": final_memory - baseline,
        "bytes_per_entry": (final_memory - baseline) // 1000 if final_memory > baseline else 0
    }
    
    print(f"   Baseline Memory:    {results['baseline']:,} bytes")
    print(f"   After 1000 entries: {results['after_1000_entries']:,} bytes")
    print(f"   Memory per entry:   ~{results['bytes_per_entry']} bytes")
    
    return results

def benchmark_concurrent_access(threads: int = 10, operations_per_thread: int = 100) -> Dict[str, float]:
    """Benchmark concurrent cache access"""
    print(f"\n🔄 Concurrent Access ({threads} threads, {operations_per_thread} ops each)")
    print("=" * 60)
    
    service_name = "concurrent_test"
    method = "ask"
    
    # Pre-populate some entries
    for i in range(50):
        hybrid_cache_service.set(service_name, method, f"concurrent_value_{i}", f"key_{i}", ttl=3600)
    
    results = []
    
    def worker_thread(thread_id: int):
        thread_times = []
        for i in range(operations_per_thread):
            key_id = random.randint(0, 99)  # Some hits, some misses
            
            start_time = time.perf_counter()
            result = hybrid_cache_service.get(service_name, method, f"key_{key_id}")
            end_time = time.perf_counter()
            
            thread_times.append((end_time - start_time) * 1000)
        
        results.append(thread_times)
    
    # Start all threads
    threads_list = []
    for i in range(threads):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads_list.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads_list:
        thread.join()
    
    # Aggregate results
    all_times = []
    for thread_times in results:
        all_times.extend(thread_times)
    
    concurrent_results = {
        "avg_response_time": mean(all_times),
        "median_response_time": median(all_times),
        "total_operations": len(all_times),
        "operations_per_second": len(all_times) / (mean(all_times) / 1000) if all_times else 0
    }
    
    print(f"   Average Response:   {concurrent_results['avg_response_time']:.3f}ms")
    print(f"   Median Response:    {concurrent_results['median_response_time']:.3f}ms")
    print(f"   Total Operations:   {concurrent_results['total_operations']}")
    print(f"   Operations/Second:  {concurrent_results['operations_per_second']:.0f}")
    
    return concurrent_results

def run_comprehensive_cache_benchmark():
    """Run all cache performance benchmarks"""
    print("🚀 Hybrid Cache Performance Benchmark Suite")
    print("=" * 80)
    
    # Clear cache before testing
    clear_cache()
    
    # Run all benchmarks
    ram_results = benchmark_ram_cache_performance(1000)
    db_results = benchmark_database_cache_performance(100)
    write_results = benchmark_write_through_performance(200)
    invalidation_results = benchmark_cache_invalidation(100)
    service_results = benchmark_cached_service_locator(100)
    memory_results = benchmark_memory_usage()
    concurrent_results = benchmark_concurrent_access(10, 100)
    
    # Get final statistics
    final_stats = get_cache_stats()
    global_stats = final_stats.get("_global_cache", {})
    
    print(f"\n📊 COMPREHENSIVE BENCHMARK RESULTS")
    print("=" * 80)
    
    print(f"Performance Metrics:")
    print(f"  RAM Cache Hit:      {ram_results['ram_hit_avg']:.4f}ms avg")
    print(f"  Database Cache Hit: {db_results['db_hit_avg']:.2f}ms avg")
    print(f"  Write-Through:      {write_results['write_avg']:.2f}ms avg")
    print(f"  Cache Invalidation: {invalidation_results['single_invalidation_avg']:.2f}ms avg")
    print(f"  Service Method:     {service_results['method_call_cached']:.2f}ms (cached)")
    
    print(f"\nThroughput Metrics:")
    print(f"  RAM Operations/sec: {1000 / ram_results['ram_hit_avg']:.0f}" if ram_results['ram_hit_avg'] > 0 else "N/A")
    print(f"  Concurrent Ops/sec: {concurrent_results['operations_per_second']:.0f}")
    
    print(f"\nMemory Metrics:")
    print(f"  Bytes per entry:    {memory_results['bytes_per_entry']} bytes")
    print(f"  Total memory:       {memory_results['final_memory']:,} bytes")
    
    print(f"\nCache Statistics:")
    print(f"  Global hit rate:    {global_stats.get('hit_rate', 0):.1f}%")
    print(f"  RAM cache size:     {global_stats.get('ram_size', 0)} entries")
    print(f"  DB cache size:      {global_stats.get('total_entries', 0)} entries")
    
    print(f"\n🎯 PERFORMANCE SUMMARY:")
    
    # Calculate cache effectiveness
    ram_speed = 1 / ram_results['ram_hit_avg'] if ram_results['ram_hit_avg'] > 0 else 0
    db_speed = 1 / db_results['db_hit_avg'] if db_results['db_hit_avg'] > 0 else 0
    speedup_ratio = ram_speed / db_speed if db_speed > 0 else 1
    
    print(f"  • RAM cache is {speedup_ratio:.0f}x faster than database cache")
    print(f"  • Service method calls have {service_results['cache_speedup']:.1f}x speedup when cached")
    print(f"  • System can handle {concurrent_results['operations_per_second']:.0f} concurrent operations/second")
    print(f"  • Memory overhead: ~{memory_results['bytes_per_entry']} bytes per cached entry")
    
    # Performance ratings
    if ram_results['ram_hit_avg'] < 0.1:
        print(f"  • RAM cache performance: 🔥 EXCELLENT (sub-millisecond)")
    elif ram_results['ram_hit_avg'] < 1.0:
        print(f"  • RAM cache performance: ✅ GOOD (sub-millisecond)")
    else:
        print(f"  • RAM cache performance: ⚠️  NEEDS OPTIMIZATION")
    
    if service_results['cache_speedup'] > 10:
        print(f"  • Cache effectiveness: 🔥 EXCELLENT ({service_results['cache_speedup']:.1f}x speedup)")
    elif service_results['cache_speedup'] > 2:
        print(f"  • Cache effectiveness: ✅ GOOD ({service_results['cache_speedup']:.1f}x speedup)")
    else:
        print(f"  • Cache effectiveness: ⚠️  LIMITED BENEFIT")

def main():
    """Run the comprehensive cache benchmark"""
    try:
        run_comprehensive_cache_benchmark()
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()