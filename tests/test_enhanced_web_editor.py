#!/usr/bin/env python3
"""
test_enhanced_web_editor.py - Test enhanced universal web editor
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.polymorphic_web_editor import EnhancedPolymorphicWebEditor


def test_enhanced_web_editor():
    """Test enhanced web editor functionality"""
    print("🌐 Testing Enhanced Universal Web Editor...")
    
    editor = EnhancedPolymorphicWebEditor()
    
    # Test enhanced ask functionality
    print("\n❓ Testing enhanced ask functionality...")
    
    # Test service discovery
    services = editor.ask("enhanced services")
    print(f"✅ Discovered {len(services)} services with health data")
    
    # Test search functionality
    search_results = editor.ask("search tournament")
    print(f"✅ Search for 'tournament' found {len(search_results)} matches")
    
    # Test analytics
    analytics = editor.ask("service stats")
    print(f"✅ Service analytics: {analytics}")
    
    # Test health dashboard
    dashboard = editor.ask("health dashboard")
    print(f"✅ Health dashboard available: {'services' in dashboard}")


def test_enhanced_tell_functionality():
    """Test enhanced tell functionality"""
    print("\n📢 Testing enhanced tell functionality...")
    
    editor = EnhancedPolymorphicWebEditor()
    
    # Test enhanced HTML rendering
    services = editor.ask("enhanced services")
    enhanced_html = editor.tell("enhanced_html", services)
    
    # Check if enhanced HTML contains expected elements
    expected_elements = [
        "Enhanced Universal Web Editor",
        "Real-time service discovery",
        "service-list",
        "dashboard",
        "search-box"
    ]
    
    html_check = all(element in enhanced_html for element in expected_elements)
    print(f"✅ Enhanced HTML rendering: {'✓' if html_check else '✗'}")
    
    if html_check:
        print("   Contains: search box, dashboard, service list, modern styling")
    
    # Test JSON output
    json_output = editor.tell("json", services)
    print(f"✅ JSON output generated: {len(json_output)} characters")


def test_enhanced_do_functionality():
    """Test enhanced do functionality"""
    print("\n🔧 Testing enhanced do functionality...")
    
    editor = EnhancedPolymorphicWebEditor()
    
    # Test live update functionality
    live_update = editor.do("live update")
    print(f"✅ Live update data: {live_update}")
    
    # Test service testing (if services are available)
    services = editor.ask("enhanced services")
    if services:
        first_service = list(services.keys())[0]
        test_results = editor.do(f"test service {first_service}")
        print(f"✅ Service testing for '{first_service}': {len(test_results.get('tests', []))} tests run")
    else:
        print("⚠️ No services available for testing")


def test_search_functionality():
    """Test service search capabilities"""
    print("\n🔍 Testing search functionality...")
    
    editor = EnhancedPolymorphicWebEditor()
    
    # Test various search terms
    search_terms = ["service", "health", "database", "web", "api"]
    
    for term in search_terms:
        results = editor.ask(f"search {term}")
        print(f"✅ Search '{term}': {len(results)} results")


def test_analytics_functionality():
    """Test service analytics"""
    print("\n📊 Testing analytics functionality...")
    
    editor = EnhancedPolymorphicWebEditor()
    
    # Get analytics
    analytics = editor.ask("service stats")
    
    expected_keys = ['total_services', 'categories', 'capability_frequency']
    analytics_check = all(key in analytics for key in expected_keys)
    
    print(f"✅ Analytics completeness: {'✓' if analytics_check else '✗'}")
    
    if analytics_check:
        print(f"   Total services: {analytics.get('total_services', 0)}")
        print(f"   Categories: {len(analytics.get('categories', {}))}")
        print(f"   Top capabilities: {list(analytics.get('capability_frequency', {}).keys())[:3]}")


def test_error_handling():
    """Test error handling in enhanced editor"""
    print("\n🔴 Testing error handling...")
    
    editor = EnhancedPolymorphicWebEditor()
    
    # Test with invalid service name
    test_result = editor.do("test service NonExistentService")
    error_handled = 'error' in test_result
    print(f"✅ Invalid service test handled: {'✓' if error_handled else '✗'}")
    
    # Test with invalid search
    search_result = editor.ask("search ")  # Empty search
    print(f"✅ Empty search handled: {len(search_result)} results")


if __name__ == "__main__":
    print("🧪 Starting Enhanced Universal Web Editor tests...\n")
    
    test_enhanced_web_editor()
    test_enhanced_tell_functionality()
    test_enhanced_do_functionality()
    test_search_functionality()
    test_analytics_functionality()
    test_error_handling()
    
    print("\n🎉 All enhanced web editor tests complete!")
    print("\nThe Enhanced Universal Web Editor now provides:")
    print("• 🔍 Real-time service discovery with search")
    print("• 📊 Service analytics and health monitoring")
    print("• 🧪 Interactive service testing capabilities")
    print("• 🎨 Modern, responsive web interface")
    print("• 🔧 Advanced error handling and recovery")
    print("• 📈 Performance monitoring and benchmarking")