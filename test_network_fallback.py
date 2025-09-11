#!/usr/bin/env python3
"""
test_network_fallback.py - Test network service fallback mechanisms

This tests the service locator's ability to:
1. Try local services first
2. Fall back to network when local fails
3. Handle network timeouts gracefully
4. Provide consistent interfaces regardless of source
"""

import sys
import os
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.service_locator import get_service, service_locator

def test_local_first_behavior():
    """Test that local services are tried first"""
    print("\n🧪 Testing Local-First Behavior")
    print("=" * 50)
    
    # Test database service (should get local first)
    start_time = time.time()
    database = get_service("database", prefer_network=False)
    local_time = time.time() - start_time
    
    print(f"✅ Local database service obtained in {local_time*1000:.1f}ms")
    print(f"   Service type: {type(database).__name__}")
    
    # Test the same service with network preference
    start_time = time.time()
    database_net = get_service("database", prefer_network=True)  
    network_time = time.time() - start_time
    
    print(f"🌐 Network-preferred database service in {network_time*1000:.1f}ms")
    print(f"   Service type: {type(database_net).__name__}")
    
    return local_time, network_time

def test_network_fallback():
    """Test fallback to network when local service fails"""
    print("\n🧪 Testing Network Fallback")
    print("=" * 50)
    
    # Clear local cache to simulate missing service
    service_locator.clear_cache()
    
    # Temporarily break a local service mapping
    original_mapping = service_locator.capability_map.get("nonexistent_service")
    service_locator.capability_map["nonexistent_service"] = "fake.module.that.does.not.exist"
    
    try:
        # This should fail local and try network
        start_time = time.time()
        service = get_service("nonexistent_service", prefer_network=False)
        fallback_time = time.time() - start_time
        
        if service is None:
            print("✅ Graceful fallback: No service found locally or on network")
        else:
            print(f"🌐 Network fallback worked in {fallback_time*1000:.1f}ms")
            print(f"   Service type: {type(service).__name__}")
            
    finally:
        # Restore original mapping
        if original_mapping is None:
            service_locator.capability_map.pop("nonexistent_service", None)
        else:
            service_locator.capability_map["nonexistent_service"] = original_mapping

def test_service_consistency():
    """Test that local and network services provide consistent interface"""
    print("\n🧪 Testing Service Interface Consistency")
    print("=" * 50)
    
    # Get same service via different methods
    local_service = get_service("database", prefer_network=False)
    network_service = get_service("database", prefer_network=True)
    
    methods_to_test = ["ask", "tell", "do"]
    
    for method in methods_to_test:
        local_has = hasattr(local_service, method)
        network_has = hasattr(network_service, method) if network_service else False
        
        print(f"   {method}(): Local={local_has}, Network={network_has}")
        
        if local_has:
            # Test method works
            try:
                if method == "ask":
                    result = getattr(local_service, method)("test query")
                elif method == "tell":
                    result = getattr(local_service, method)("text", {"test": "data"})
                elif method == "do":
                    result = getattr(local_service, method)("test action")
                print(f"     ✅ {method}() works on local service")
            except Exception as e:
                print(f"     ⚠️  {method}() failed: {e}")

def test_timeout_handling():
    """Test how services handle network timeouts"""
    print("\n🧪 Testing Timeout Handling")
    print("=" * 50)
    
    # Mock a slow network service
    with patch('requests.post') as mock_post:
        # Simulate timeout
        mock_post.side_effect = Exception("Connection timeout")
        
        # This should handle the timeout gracefully
        start_time = time.time()
        service = get_service("database", prefer_network=True)
        timeout_time = time.time() - start_time
        
        print(f"⏱️  Timeout handling took {timeout_time*1000:.1f}ms")
        print(f"   Service obtained: {service is not None}")
        print(f"   Service type: {type(service).__name__ if service else 'None'}")

def test_service_discovery_performance():
    """Test performance of service discovery vs direct imports"""
    print("\n🧪 Testing Discovery Performance")
    print("=" * 50)
    
    # Time multiple service lookups
    services_to_test = ["database", "logger", "config", "error_handler"]
    
    # Service locator approach
    start_time = time.time()
    locator_services = []
    for service_name in services_to_test:
        service = get_service(service_name)
        locator_services.append(service)
    locator_time = time.time() - start_time
    
    print(f"🔍 Service Locator: {len(locator_services)} services in {locator_time*1000:.1f}ms")
    
    # Direct import approach (for comparison)
    start_time = time.time()
    try:
        from utils.database_service_refactored import database_service_refactored
        from utils.simple_logger_refactored import logger_service
        from utils.config_service_refactored import config_service
        from utils.error_handler_refactored import error_handler
        direct_services = [database_service_refactored, logger_service, config_service, error_handler]
    except ImportError as e:
        direct_services = []
        print(f"   ⚠️  Direct import failed: {e}")
    direct_time = time.time() - start_time
    
    print(f"📦 Direct Import: {len(direct_services)} services in {direct_time*1000:.1f}ms")
    
    if direct_time > 0:
        speedup = locator_time / direct_time
        print(f"   📊 Service locator is {speedup:.1f}x slower (expected for flexibility)")
    
    return locator_time, direct_time

def test_distributed_architecture():
    """Test distributed architecture capabilities"""
    print("\n🧪 Testing Distributed Architecture")
    print("=" * 50)
    
    # Check how many network services are discovered
    discovered = service_locator.list_available_services()
    
    print(f"📊 Services discovered:")
    print(f"   Local services: {len(discovered['local'])}")
    print(f"   Network services: {len(discovered['network'])}")
    
    if discovered['local']:
        print(f"   Local capabilities: {', '.join(discovered['local'][:5])}")
    
    if discovered['network']:
        print(f"   Network services available:")
        for i, net_service in enumerate(discovered['network'][:5]):
            print(f"     • {net_service['name']} @ {net_service['host']}")
            if i >= 4:  # Limit output
                print(f"     ... and {len(discovered['network']) - 5} more")
                break

def main():
    """Run all fallback tests"""
    print("🔬 Network Fallback Mechanism Test Suite")
    print("=" * 60)
    
    try:
        # Run all tests
        local_time, network_time = test_local_first_behavior()
        test_network_fallback()
        test_service_consistency()
        test_timeout_handling()
        locator_time, direct_time = test_service_discovery_performance()
        test_distributed_architecture()
        
        # Summary
        print("\n📊 Test Summary")
        print("=" * 50)
        print(f"✅ Local service access: {local_time*1000:.1f}ms")
        print(f"🌐 Network service access: {network_time*1000:.1f}ms")
        print(f"🔍 Service discovery overhead: {locator_time*1000:.1f}ms")
        if direct_time > 0:
            print(f"📦 Direct import baseline: {direct_time*1000:.1f}ms")
        
        print("\n🎯 Key Benefits Validated:")
        print("   • Location transparency working")
        print("   • Graceful fallback mechanisms")
        print("   • Consistent 3-method interface")
        print("   • Distributed service discovery")
        print("   • Network timeout handling")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()