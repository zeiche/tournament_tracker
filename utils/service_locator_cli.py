#!/usr/bin/env python3
"""
service_locator_cli.py - Command-line interface for service locator management

This module provides CLI commands for managing and testing the service locator
system, including service discovery, health checks, and network service testing.
"""
import sys
import time
import json
from typing import Dict, Any, List
from utils.dynamic_switches import announce_switch
from polymorphic_core.service_locator import get_service, service_locator, list_services

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.service_locator_cli")


def service_locator_handler(args):
    """Handler for --service-locator switch"""
    cmd = getattr(args, 'service_locator', 'status')
    
    if cmd == 'status':
        show_service_status()
    elif cmd == 'test':
        test_all_services()
    elif cmd == 'discover':
        discover_network_services()
    elif cmd == 'health':
        health_check_services()
    elif cmd == 'clear':
        clear_service_cache()
    elif cmd == 'list':
        list_available_services()
    elif cmd == 'benchmark':
        benchmark_service_performance()
    elif cmd == 'cache':
        show_hybrid_cache_status()
    elif cmd == 'optimize':
        enable_hybrid_cache()
    else:
        print(f"Unknown service-locator command: {cmd}")
        print("Available commands: status, test, discover, health, clear, list, benchmark, cache, optimize")


def show_service_status():
    """Show the status of all services in the service locator"""
    print("🌐 Service Locator Status")
    print("=" * 50)
    
    # Get service locator info
    local_cache_count = len(service_locator.local_cache)
    network_cache_count = len(service_locator.network_cache)
    total_capabilities = len(service_locator.capability_map)
    
    print(f"📊 Cache Status:")
    print(f"  Local cached services: {local_cache_count}")
    print(f"  Network cached services: {network_cache_count}")
    print(f"  Total registered capabilities: {total_capabilities}")
    
    # Show available services
    print(f"\n🔍 Available Service Capabilities:")
    for capability in sorted(service_locator.capability_map.keys()):
        module_path = service_locator.capability_map[capability]
        is_cached_local = capability in service_locator.local_cache
        is_cached_network = capability in service_locator.network_cache
        
        status_indicators = []
        if is_cached_local:
            status_indicators.append("🟢 Local")
        if is_cached_network:
            status_indicators.append("🌐 Network")
        if not status_indicators:
            status_indicators.append("⚪ Not loaded")
        
        status = " ".join(status_indicators)
        print(f"  • {capability}: {status}")
        if len(module_path) > 60:
            print(f"    ↳ {module_path[:60]}...")
        else:
            print(f"    ↳ {module_path}")


def test_all_services():
    """Test connectivity and basic functionality of all services"""
    print("🧪 Testing All Services")
    print("=" * 50)
    
    # Get list of all available capabilities
    capabilities = list(service_locator.capability_map.keys())
    test_results = {}
    
    for capability in capabilities:
        print(f"\n🔍 Testing {capability}...")
        
        try:
            # Test local service discovery
            start_time = time.time()
            local_service = get_service(capability, prefer_network=False)
            local_time = time.time() - start_time
            
            # Test basic functionality
            local_works = False
            if local_service:
                try:
                    # Try ask method
                    result = local_service.ask("stats")
                    local_works = isinstance(result, dict) or isinstance(result, str)
                except Exception as e:
                    print(f"  ⚠️  Local service functional test failed: {e}")
            
            # Test network service discovery
            network_works = False
            network_time = None
            try:
                start_time = time.time()
                network_service = get_service(capability, prefer_network=True)
                network_time = time.time() - start_time
                
                if network_service and network_service != local_service:
                    # Try ask method on network service
                    result = network_service.ask("stats")
                    network_works = isinstance(result, dict) or isinstance(result, str)
                elif network_service == local_service:
                    network_works = None  # Same as local
            except Exception as e:
                print(f"  ⚠️  Network service test failed: {e}")
            
            test_results[capability] = {
                'local_discovered': local_service is not None,
                'local_functional': local_works,
                'local_time': local_time,
                'network_discovered': network_service is not None if network_time else False,
                'network_functional': network_works,
                'network_time': network_time
            }
            
            # Status reporting
            local_status = "✅" if local_works else ("🟡" if local_service else "❌")
            if network_works is None:
                network_status = "🔄"  # Same as local
            elif network_works:
                network_status = "✅"
            elif network_time is not None:
                network_status = "🟡"  # Discovered but not functional
            else:
                network_status = "❌"
            
            print(f"  Local: {local_status} ({local_time:.3f}s) | Network: {network_status}" + 
                  (f" ({network_time:.3f}s)" if network_time else ""))
                  
        except Exception as e:
            test_results[capability] = {'error': str(e)}
            print(f"  ❌ Test failed: {e}")
    
    # Summary
    print(f"\n📊 Test Summary:")
    local_working = len([r for r in test_results.values() if r.get('local_functional', False)])
    network_working = len([r for r in test_results.values() if r.get('network_functional', False)])
    total_services = len(test_results)
    
    print(f"  Local services working: {local_working}/{total_services}")
    print(f"  Network services working: {network_working}/{total_services}")
    print(f"  Overall success rate: {((local_working + network_working) / (total_services * 2) * 100):.1f}%")


def discover_network_services():
    """Discover available network services"""
    print("🌐 Network Service Discovery")
    print("=" * 50)
    
    print("Scanning for network services...")
    
    # Try to discover each capability via network
    capabilities = list(service_locator.capability_map.keys())
    network_services = []
    
    for capability in capabilities:
        try:
            # Force network discovery
            service = get_service(capability, prefer_network=True)
            if service and capability in service_locator.network_cache:
                network_service = service_locator.network_cache[capability]
                network_services.append({
                    'capability': capability,
                    'host': getattr(network_service, 'host', 'unknown'),
                    'port': getattr(network_service, 'port', 'unknown'),
                    'service_name': getattr(network_service, 'service_name', 'unknown')
                })
                print(f"  🌐 {capability}: {network_service.host}:{network_service.port}")
        except Exception as e:
            print(f"  ❌ {capability}: Discovery failed - {e}")
    
    print(f"\n📊 Network Discovery Summary:")
    print(f"  Network services found: {len(network_services)}")
    print(f"  Discovery success rate: {(len(network_services) / len(capabilities) * 100):.1f}%")


def health_check_services():
    """Perform health check on all available services"""
    print("🏥 Service Health Check")
    print("=" * 50)
    
    capabilities = list(service_locator.capability_map.keys())
    health_results = {}
    
    for capability in capabilities:
        print(f"\n💊 Health check: {capability}")
        
        try:
            service = get_service(capability, prefer_network=False)
            if not service:
                health_results[capability] = {'status': 'unavailable'}
                print(f"  ❌ Service unavailable")
                continue
            
            # Test ask method
            try:
                stats_result = service.ask("stats")
                ask_healthy = True
            except Exception as e:
                ask_healthy = False
                print(f"  ⚠️  ask() method unhealthy: {e}")
            
            # Test tell method
            try:
                tell_result = service.tell("json", {"test": "data"})
                tell_healthy = isinstance(tell_result, str)
            except Exception as e:
                tell_healthy = False
                print(f"  ⚠️  tell() method unhealthy: {e}")
            
            # Test do method
            try:
                do_result = service.do("reset stats")
                do_healthy = True
            except Exception as e:
                do_healthy = False
                print(f"  ⚠️  do() method unhealthy: {e}")
            
            overall_health = ask_healthy and tell_healthy and do_healthy
            health_results[capability] = {
                'status': 'healthy' if overall_health else 'degraded',
                'ask_healthy': ask_healthy,
                'tell_healthy': tell_healthy,
                'do_healthy': do_healthy
            }
            
            status = "✅ Healthy" if overall_health else "🟡 Degraded"
            print(f"  {status}: ask={ask_healthy}, tell={tell_healthy}, do={do_healthy}")
            
        except Exception as e:
            health_results[capability] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ Health check failed: {e}")
    
    # Health summary
    healthy = len([r for r in health_results.values() if r.get('status') == 'healthy'])
    degraded = len([r for r in health_results.values() if r.get('status') == 'degraded'])
    unavailable = len([r for r in health_results.values() if r.get('status') in ['unavailable', 'error']])
    
    print(f"\n🏥 Health Summary:")
    print(f"  Healthy services: {healthy}")
    print(f"  Degraded services: {degraded}")
    print(f"  Unavailable services: {unavailable}")
    print(f"  System health: {(healthy / len(capabilities) * 100):.1f}%")


def clear_service_cache():
    """Clear service locator cache"""
    print("🧹 Clearing Service Cache")
    print("=" * 50)
    
    # Record cache size before clearing
    local_before = len(service_locator.local_cache)
    network_before = len(service_locator.network_cache)
    
    # Clear cache
    service_locator.clear_cache()
    
    print(f"  Cleared local cache: {local_before} services")
    print(f"  Cleared network cache: {network_before} services")
    print(f"  ✅ Cache cleared successfully")


def list_available_services():
    """List all available services in detail"""
    print("📋 Available Services Detail")
    print("=" * 50)
    
    services_info = list_services()
    
    for service_name, info in services_info.items():
        print(f"\n🔧 {service_name}:")
        for key, value in info.items():
            if isinstance(value, str) and len(value) > 80:
                print(f"  {key}: {value[:80]}...")
            else:
                print(f"  {key}: {value}")


def benchmark_service_performance():
    """Benchmark service performance"""
    print("⚡ Service Performance Benchmark")
    print("=" * 50)
    
    capabilities = list(service_locator.capability_map.keys())[:5]  # Test first 5 services
    benchmark_results = {}
    
    for capability in capabilities:
        print(f"\n⚡ Benchmarking {capability}...")
        
        try:
            service = get_service(capability, prefer_network=False)
            if not service:
                print(f"  ⏭️  Skipped: Service unavailable")
                continue
            
            # Benchmark ask method
            ask_times = []
            for i in range(3):
                start = time.time()
                service.ask("stats")
                ask_times.append(time.time() - start)
            
            # Benchmark tell method
            tell_times = []
            for i in range(3):
                start = time.time()
                service.tell("json", {"test": "data"})
                tell_times.append(time.time() - start)
            
            # Benchmark do method
            do_times = []
            for i in range(3):
                start = time.time()
                service.do("reset stats")
                do_times.append(time.time() - start)
            
            avg_ask = sum(ask_times) / len(ask_times) * 1000
            avg_tell = sum(tell_times) / len(tell_times) * 1000
            avg_do = sum(do_times) / len(do_times) * 1000
            total_avg = avg_ask + avg_tell + avg_do
            
            benchmark_results[capability] = {
                'ask_ms': avg_ask,
                'tell_ms': avg_tell,
                'do_ms': avg_do,
                'total_ms': total_avg
            }
            
            print(f"  ask(): {avg_ask:.1f}ms, tell(): {avg_tell:.1f}ms, do(): {avg_do:.1f}ms")
            print(f"  Total: {total_avg:.1f}ms")
            
        except Exception as e:
            print(f"  ❌ Benchmark failed: {e}")
    
    # Performance summary
    if benchmark_results:
        avg_total = sum(r['total_ms'] for r in benchmark_results.values()) / len(benchmark_results)
        fastest = min(benchmark_results.values(), key=lambda x: x['total_ms'])
        slowest = max(benchmark_results.values(), key=lambda x: x['total_ms'])
        
        print(f"\n⚡ Performance Summary:")
        print(f"  Average total time: {avg_total:.1f}ms")
        print(f"  Fastest service: {fastest['total_ms']:.1f}ms")
        print(f"  Slowest service: {slowest['total_ms']:.1f}ms")


# Announce the service locator switch
announce_switch(
    flag="--service-locator",
    help="Service locator management (status|test|discover|health|clear|list|benchmark)",
    handler=service_locator_handler,
    action="store",
    nargs="?",
    const="status",
    metavar="CMD"
)

if __name__ == "__main__":
    # For testing when run directly
    class Args:
        service_locator = "test"
    
    args = Args()
    service_locator_handler(args)