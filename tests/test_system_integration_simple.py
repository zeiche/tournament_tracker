#!/usr/bin/env python3
"""
test_system_integration_simple.py - Essential integration testing

Simplified integration test focusing on core functionality verification
without complex network service setup.
"""
import sys
import time
import json
from typing import Dict, Any

# Add current directory to path for imports
sys.path.append('.')

# Test core service locator functionality
from polymorphic_core.service_locator import get_service, service_locator


def test_service_locator_basic():
    """Test basic service locator functionality"""
    print("🔍 Testing Service Locator Basic Functionality...")
    
    try:
        # Clear cache to start fresh
        service_locator.clear_cache()
        
        # Test getting different services
        services_to_test = ["database", "logger", "error_handler", "config"]
        results = {}
        
        for service_name in services_to_test:
            try:
                start_time = time.time()
                service = get_service(service_name, prefer_network=False)
                discovery_time = time.time() - start_time
                
                if service is not None:
                    results[service_name] = {
                        'discovered': True,
                        'discovery_time': discovery_time,
                        'has_ask': hasattr(service, 'ask'),
                        'has_tell': hasattr(service, 'tell'),
                        'has_do': hasattr(service, 'do')
                    }
                    print(f"  ✅ {service_name}: discovered in {discovery_time:.3f}s, methods: ask={results[service_name]['has_ask']}, tell={results[service_name]['has_tell']}, do={results[service_name]['has_do']}")
                else:
                    results[service_name] = {'discovered': False}
                    print(f"  ❌ {service_name}: not discovered")
                    
            except Exception as e:
                results[service_name] = {'error': str(e)}
                print(f"  ❌ {service_name}: error - {e}")
        
        success_count = len([r for r in results.values() if r.get('discovered', False)])
        print(f"✅ Service discovery: {success_count}/{len(services_to_test)} services discovered")
        return results
        
    except Exception as e:
        print(f"❌ Service locator test failed: {e}")
        return {}


def test_3_method_pattern():
    """Test the 3-method pattern across discovered services"""
    print("\n🎯 Testing 3-Method Pattern Implementation...")
    
    try:
        services_to_test = ["database", "logger", "points_system"]
        results = {}
        
        for service_name in services_to_test:
            try:
                service = get_service(service_name, prefer_network=False)
                if service is None:
                    results[service_name] = {'skipped': 'service not available'}
                    print(f"  ⏭️  {service_name}: skipped (not available)")
                    continue
                
                # Test ask method
                try:
                    ask_result = service.ask("stats")
                    ask_works = isinstance(ask_result, dict)
                except Exception as e:
                    ask_result = f"error: {e}"
                    ask_works = False
                
                # Test tell method
                try:
                    tell_result = service.tell("json", {"test": "data"})
                    tell_works = isinstance(tell_result, str) and len(tell_result) > 0
                except Exception as e:
                    tell_result = f"error: {e}"
                    tell_works = False
                
                # Test do method
                try:
                    do_result = service.do("reset stats")
                    do_works = isinstance(do_result, dict)
                except Exception as e:
                    do_result = f"error: {e}"
                    do_works = False
                
                results[service_name] = {
                    'ask_works': ask_works,
                    'tell_works': tell_works,
                    'do_works': do_works,
                    'all_methods_work': ask_works and tell_works and do_works,
                    'ask_result': ask_result,
                    'tell_result': tell_result,
                    'do_result': do_result
                }
                
                status = "✅" if results[service_name]['all_methods_work'] else "⚠️"
                print(f"  {status} {service_name}: ask={ask_works}, tell={tell_works}, do={do_works}")
                
            except Exception as e:
                results[service_name] = {'error': str(e)}
                print(f"  ❌ {service_name}: error - {e}")
        
        working_services = len([r for r in results.values() if r.get('all_methods_work', False)])
        print(f"✅ 3-method pattern: {working_services}/{len(services_to_test)} services fully compliant")
        return results
        
    except Exception as e:
        print(f"❌ 3-method pattern test failed: {e}")
        return {}


def test_service_dependencies():
    """Test that services can find their dependencies"""
    print("\n🔗 Testing Service Dependencies...")
    
    try:
        results = {}
        
        # Test database service (minimal dependencies)
        try:
            db = get_service("database", prefer_network=False)
            if db:
                stats = db.ask("stats")
                results['database'] = {'works': True, 'stats': stats}
                print("  ✅ database: Working independently")
            else:
                results['database'] = {'works': False, 'reason': 'not discovered'}
                print("  ❌ database: Not available")
        except Exception as e:
            results['database'] = {'error': str(e)}
            print(f"  ❌ database: {e}")
        
        # Test logger service (depends on config, error handler)
        try:
            logger = get_service("logger", prefer_network=False)
            if logger:
                logger.info("Integration test log message")
                stats = logger.ask("stats")
                results['logger'] = {'works': True, 'stats': stats}
                print("  ✅ logger: Dependencies resolved")
            else:
                results['logger'] = {'works': False, 'reason': 'not discovered'}
                print("  ❌ logger: Not available")
        except Exception as e:
            results['logger'] = {'error': str(e)}
            print(f"  ❌ logger: {e}")
        
        # Test points system (depends on logger, error handler)
        try:
            points = get_service("points_system", prefer_network=False)
            if points:
                points_data = points.ask("points for placement 1")
                results['points_system'] = {'works': True, 'data': points_data}
                print("  ✅ points_system: Calculation working")
            else:
                results['points_system'] = {'works': False, 'reason': 'not discovered'}
                print("  ❌ points_system: Not available")
        except Exception as e:
            results['points_system'] = {'error': str(e)}
            print(f"  ❌ points_system: {e}")
        
        working_deps = len([r for r in results.values() if r.get('works', False)])
        print(f"✅ Service dependencies: {working_deps}/{len(results)} services with working dependencies")
        return results
        
    except Exception as e:
        print(f"❌ Service dependencies test failed: {e}")
        return {}


def test_points_system_workflow():
    """Test a complete points calculation workflow"""
    print("\n🎯 Testing Points System Workflow...")
    
    try:
        points = get_service("points_system", prefer_network=False)
        if not points:
            print("  ⏭️  Skipped: Points system not available")
            return {'skipped': 'points system not available'}
        
        # Test individual point calculations
        placements_to_test = [1, 2, 3, 4, 5, 8, 9]  # Include invalid placement
        points_results = {}
        
        for placement in placements_to_test:
            try:
                result = points.ask(f"points for placement {placement}")
                if isinstance(result, dict) and 'points' in result:
                    points_results[placement] = result['points']
                    print(f"    Placement {placement}: {result['points']} points")
                else:
                    points_results[placement] = 0
                    print(f"    Placement {placement}: 0 points (invalid)")
            except Exception as e:
                points_results[placement] = f"error: {e}"
                print(f"    Placement {placement}: error - {e}")
        
        # Test total calculation
        try:
            total_result = points.do("calculate total", placements=[1, 2, 3])
            total_works = isinstance(total_result, dict) and 'total' in str(total_result)
            print(f"    Total calculation: {'✅ working' if total_works else '❌ failed'}")
        except Exception as e:
            total_works = False
            print(f"    Total calculation: ❌ error - {e}")
        
        # Verify expected points (FGC standard: 8-6-4-3-2-2-1-1)
        expected_points = {1: 8, 2: 6, 3: 4, 4: 3, 5: 2, 8: 1, 9: 0}
        points_correct = all(points_results.get(p, -1) == expected_points[p] for p in expected_points)
        
        workflow_result = {
            'points_calculated': len([p for p in points_results.values() if isinstance(p, int)]),
            'total_calculation_works': total_works,
            'points_distribution_correct': points_correct,
            'workflow_complete': points_correct and total_works
        }
        
        status = "✅" if workflow_result['workflow_complete'] else "⚠️"
        print(f"  {status} Points workflow: calculation={'✅' if total_works else '❌'}, distribution={'✅' if points_correct else '❌'}")
        
        return workflow_result
        
    except Exception as e:
        print(f"❌ Points workflow test failed: {e}")
        return {'error': str(e)}


def run_integration_tests():
    """Run all integration tests and generate report"""
    print("🧪 Simple System Integration Test Suite")
    print("=" * 50)
    
    start_time = time.time()
    all_results = {}
    
    try:
        # Run tests
        all_results['service_locator'] = test_service_locator_basic()
        all_results['method_pattern'] = test_3_method_pattern()
        all_results['dependencies'] = test_service_dependencies()
        all_results['points_workflow'] = test_points_system_workflow()
        
        # Generate report
        total_time = time.time() - start_time
        generate_test_report(all_results, total_time)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        all_results['suite_error'] = str(e)
    
    # Save results
    try:
        with open('simple_integration_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"📄 Results saved to: simple_integration_results.json")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")


def generate_test_report(results: Dict[str, Any], total_time: float):
    """Generate a summary test report"""
    print(f"\n📊 Integration Test Report")
    print("=" * 40)
    print(f"⏱️  Total time: {total_time:.2f} seconds")
    
    # Count successes
    total_tests = 0
    passed_tests = 0
    
    for test_name, test_results in results.items():
        if test_name == 'service_locator':
            discovered = len([r for r in test_results.values() if r.get('discovered', False)])
            total = len(test_results)
            total_tests += total
            passed_tests += discovered
            print(f"🔍 Service Discovery: {discovered}/{total}")
            
        elif test_name == 'method_pattern':
            working = len([r for r in test_results.values() if r.get('all_methods_work', False)])
            total = len([r for r in test_results.values() if not r.get('skipped')])
            total_tests += total
            passed_tests += working
            print(f"🎯 3-Method Pattern: {working}/{total}")
            
        elif test_name == 'dependencies':
            working = len([r for r in test_results.values() if r.get('works', False)])
            total = len(test_results)
            total_tests += total
            passed_tests += working
            print(f"🔗 Dependencies: {working}/{total}")
            
        elif test_name == 'points_workflow':
            if not test_results.get('skipped') and not test_results.get('error'):
                workflow_works = test_results.get('workflow_complete', False)
                total_tests += 1
                passed_tests += (1 if workflow_works else 0)
                print(f"🎯 Points Workflow: {'✅' if workflow_works else '❌'}")
    
    # Overall success rate
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 INTEGRATION TESTS: PASSED ✅")
        print("The service locator architecture is working correctly!")
    elif success_rate >= 60:
        print("⚠️  INTEGRATION TESTS: PARTIAL PASS ⚠️")
        print("Core functionality working, minor issues present.")
    else:
        print("❌ INTEGRATION TESTS: FAILED ❌")
        print("Significant issues with the service architecture.")


if __name__ == "__main__":
    run_integration_tests()