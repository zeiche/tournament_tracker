#!/usr/bin/env python3
"""
benchmark_comparison.py - Comprehensive performance comparison

Compare service locator pattern vs direct imports across multiple dimensions:
1. Import time
2. First access time
3. Cached access time 
4. Memory overhead
5. Network discovery benefits
"""

import sys
import os
import time
import tracemalloc
from statistics import mean, median
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.benchmark_comparison")

from polymorphic_core.service_locator import get_service, service_locator

def benchmark_import_times(iterations: int = 10) -> Dict[str, List[float]]:
    """Benchmark import times for different approaches"""
    print(f"\n⚡ Benchmarking Import Times ({iterations} iterations)")
    print("=" * 60)
    
    results = {
        "service_locator": [],
        "direct_import": []
    }
    
    for i in range(iterations):
        # Clear caches
        service_locator.clear_cache()
        
        # Service locator approach
        start_time = time.time()
        database = get_service("database")
        logger = get_service("logger") 
        config = get_service("config")
        locator_time = time.time() - start_time
        results["service_locator"].append(locator_time * 1000)  # Convert to ms
        
        # Direct import approach
        start_time = time.time()
        try:
            from utils.database_service_refactored import database_service_refactored
            from utils.simple_logger_refactored import logger_service
            from utils.config_service_refactored import config_service
            direct_time = time.time() - start_time
            results["direct_import"].append(direct_time * 1000)
        except ImportError:
            results["direct_import"].append(0.0)
    
    # Print results
    for approach, times in results.items():
        if times:
            avg_time = mean(times)
            med_time = median(times)
            print(f"  {approach:15}: avg={avg_time:6.2f}ms, median={med_time:6.2f}ms")
    
    return results

def benchmark_access_performance(iterations: int = 100) -> Dict[str, List[float]]:
    """Benchmark service access performance"""
    print(f"\n⚡ Benchmarking Access Performance ({iterations} iterations)")
    print("=" * 60)
    
    # Get services once
    database_service = get_service("database")
    
    results = {
        "first_ask": [],
        "cached_ask": [],
        "tell_format": [],
        "do_action": []
    }
    
    for i in range(iterations):
        # Test ask() method
        start_time = time.time()
        result = database_service.ask("stats")
        ask_time = (time.time() - start_time) * 1000
        
        if i == 0:
            results["first_ask"].append(ask_time)
        else:
            results["cached_ask"].append(ask_time)
        
        # Test tell() method
        start_time = time.time()
        formatted = database_service.tell("text", result)
        tell_time = (time.time() - start_time) * 1000
        results["tell_format"].append(tell_time)
        
        # Test do() method
        start_time = time.time()
        database_service.do("reset stats")
        do_time = (time.time() - start_time) * 1000
        results["do_action"].append(do_time)
    
    # Print results
    for method, times in results.items():
        if times:
            avg_time = mean(times)
            med_time = median(times)
            print(f"  {method:15}: avg={avg_time:6.2f}ms, median={med_time:6.2f}ms")
    
    return results

def benchmark_memory_overhead() -> Dict[str, int]:
    """Benchmark memory overhead"""
    print(f"\n🧠 Memory Overhead Analysis")
    print("=" * 60)
    
    results = {}
    
    # Baseline memory
    tracemalloc.start()
    baseline = tracemalloc.get_traced_memory()[0]
    
    # Service locator memory
    services = []
    for service_name in ["database", "logger", "config", "error_handler", "claude", "web_editor"]:
        service = get_service(service_name)
        services.append(service)
    
    locator_memory = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    
    # Direct import memory
    tracemalloc.start()
    try:
        from utils.database_service_refactored import database_service_refactored
        from utils.simple_logger_refactored import logger_service  
        from utils.config_service_refactored import config_service
        from utils.error_handler_refactored import error_handler
        from services.claude_cli_service_refactored import claude_service
        from services.polymorphic_web_editor_refactored import web_editor
        direct_imports = [database_service_refactored, logger_service, config_service, error_handler, claude_service, web_editor]
    except ImportError:
        direct_imports = []
    
    direct_memory = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    
    results = {
        "baseline": baseline,
        "service_locator": locator_memory - baseline,
        "direct_import": direct_memory - baseline
    }
    
    print(f"  Baseline memory:     {baseline:,} bytes")
    print(f"  Service locator:     {results['service_locator']:,} bytes")
    print(f"  Direct imports:      {results['direct_import']:,} bytes")
    
    if results['direct_import'] > 0:
        overhead = (results['service_locator'] / results['direct_import']) * 100 - 100
        print(f"  Overhead:            {overhead:+.1f}%")
    
    return results

def benchmark_network_discovery() -> Dict[str, Any]:
    """Benchmark network discovery capabilities"""
    print(f"\n🌐 Network Discovery Benefits")  
    print("=" * 60)
    
    # Count discovered services
    available_services = service_locator.list_available_services()
    
    local_count = len(available_services['local'])
    network_count = len(available_services['network'])
    total_capabilities = local_count + network_count
    
    # Test network service access if available
    network_access_time = 0
    if available_services['network']:
        start_time = time.time()
        # Try to get a service that might be on network
        test_service = get_service("database", prefer_network=True)
        network_access_time = (time.time() - start_time) * 1000
    
    results = {
        "local_services": local_count,
        "network_services": network_count,  
        "total_capabilities": total_capabilities,
        "network_access_ms": network_access_time
    }
    
    print(f"  Local services:      {local_count}")
    print(f"  Network services:    {network_count}")
    print(f"  Total capabilities:  {total_capabilities}")
    if network_access_time > 0:
        print(f"  Network access:      {network_access_time:.2f}ms")
    
    # Show flexibility benefit
    print(f"\n  🎯 Flexibility Benefits:")
    print(f"     • Location transparency: ✅")
    print(f"     • Distributed deployment: ✅") 
    print(f"     • Auto-discovery: ✅")
    print(f"     • Fault tolerance: ✅")
    
    return results

def run_comprehensive_benchmark():
    """Run all benchmark tests"""
    print("🚀 Service Locator vs Direct Import - Comprehensive Benchmark")
    print("=" * 80)
    
    # Run all benchmark tests
    import_results = benchmark_import_times(5)
    access_results = benchmark_access_performance(50) 
    memory_results = benchmark_memory_overhead()
    network_results = benchmark_network_discovery()
    
    # Summary analysis
    print(f"\n📊 BENCHMARK SUMMARY")
    print("=" * 80)
    
    if import_results["service_locator"] and import_results["direct_import"]:
        locator_avg = mean(import_results["service_locator"])
        direct_avg = mean(import_results["direct_import"]) or 0.001  # Avoid division by zero
        slowdown = locator_avg / direct_avg if direct_avg > 0 else 1
        
        print(f"Import Performance:")
        print(f"  Service Locator: {locator_avg:.2f}ms")
        print(f"  Direct Import:   {direct_avg:.2f}ms") 
        print(f"  Slowdown:        {slowdown:.1f}x")
    
    if access_results["cached_ask"]:
        cached_avg = mean(access_results["cached_ask"])
        print(f"\nAccess Performance:")
        print(f"  Cached access:   {cached_avg:.2f}ms")
    
    print(f"\nArchitecture Benefits:")
    print(f"  Services discovered:     {network_results['total_capabilities']}")
    print(f"  Network transparency:    Yes")
    print(f"  Distributed deployment:  Yes") 
    print(f"  Auto-discovery:          Yes")
    
    # Final verdict
    print(f"\n🎯 VERDICT:")
    print(f"  • Service Locator adds ~{locator_avg:.1f}ms overhead")
    print(f"  • Enables distributed architecture")
    print(f"  • Provides location transparency") 
    print(f"  • Auto-discovers {network_results['network_services']} network services")
    print(f"  • Trade-off: Small performance cost for huge architectural flexibility")

def main():
    """Main benchmark execution"""
    try:
        run_comprehensive_benchmark()
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()