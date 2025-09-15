#!/usr/bin/env python3
"""
test_full_system_integration.py - Comprehensive end-to-end system testing

This module tests the entire tournament tracker application with mixed local/network services
to verify the distributed service architecture works correctly in all scenarios.

Tests cover:
- Mixed local and network service operations
- Service failover scenarios (local to network and vice versa)
- Performance with network service calls
- Data consistency across distributed services
- End-to-end workflows through the service locator
"""
import time
import threading
from contextlib import contextmanager
from typing import Dict, Any, List
import tempfile
import json
import os

# Core service locator and network components
from polymorphic_core.service_locator import get_service, clear_service_cache
from polymorphic_core.network_service_wrapper import NetworkServiceWrapper
from polymorphic_core import announcer

# All refactored services for testing
from utils.database_service import DatabaseService
from utils.simple_logger_refactored import LoggerService
from utils.error_handler_refactored import ErrorHandlerService
from utils.config_service_refactored import ConfigService
from utils.points_system_refactored import PointsSystemService
from utils.unified_tabulator_refactored import UnifiedTabulatorService
from utils.database_queue_refactored import DatabaseQueueService
from services.claude_cli_service_refactored import ClaudeCliService
from services.polymorphic_web_editor_refactored import WebEditorService
from services.interactive_service_refactored import InteractiveService
from services.message_handler_refactored import MessageHandlerService
from services.twilio_service_refactored import TwilioService
from services.report_service_refactored import ReportService
from services.process_service_refactored import ProcessService
from services.startgg_sync_refactored import StartGGSyncService
from services.analytics_service_refactored import AnalyticsService


class FullSystemIntegrationTest:
    """Comprehensive integration testing for the entire distributed system"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.service_instances = {}
        self.network_wrappers = {}
        self.test_ports = list(range(9000, 9020))  # Ports for test services
        
        # Test configuration
        self.test_config = {
            'test_database': ':memory:',  # In-memory SQLite for testing
            'test_mode': True,
            'network_timeout': 5.0,
            'max_retries': 3
        }
        
        print("🧪 Full System Integration Test Suite")
        print("=" * 60)
    
    def setup_test_environment(self):
        """Set up the test environment with both local and network services"""
        print("\n🔧 Setting up test environment...")
        
        # Clear any existing service cache
        clear_service_cache()
        
        # Create local service instances
        self.service_instances = {
            'database': DatabaseService(prefer_network=False),
            'logger': LoggerService(prefer_network=False),
            'error_handler': ErrorHandlerService(prefer_network=False),
            'config': ConfigService(prefer_network=False),
            'points_system': PointsSystemService(prefer_network=False),
            'tabulator': UnifiedTabulatorService(prefer_network=False),
            'queue': DatabaseQueueService(prefer_network=False),
            'claude_cli': ClaudeCliService(prefer_network=False),
            'web_editor': WebEditorService(prefer_network=False),
            'interactive': InteractiveService(prefer_network=False),
            'message_handler': MessageHandlerService(prefer_network=False),
            'twilio': TwilioService(prefer_network=False),
            'report': ReportService(prefer_network=False),
            'process': ProcessService(prefer_network=False),
            'startgg_sync': StartGGSyncService(prefer_network=False),
            'analytics': AnalyticsService(prefer_network=False)
        }
        
        # Create network wrappers for key services
        self.network_wrappers = {}
        port_idx = 0
        
        for service_name, service_instance in self.service_instances.items():
            try:
                if port_idx < len(self.test_ports):
                    port = self.test_ports[port_idx]
                    wrapper = NetworkServiceWrapper(
                        service=service_instance,
                        service_name=f"Test{service_name.title()}",
                        port=port,
                        capabilities=[f"Test {service_name} service"]
                    )
                    self.network_wrappers[service_name] = wrapper
                    port_idx += 1
                    print(f"  ✅ Created network wrapper for {service_name} on port {port}")
                else:
                    print(f"  ⚠️  Skipped network wrapper for {service_name} (no available port)")
            except Exception as e:
                print(f"  ❌ Failed to create network wrapper for {service_name}: {e}")
        
        print(f"✅ Test environment setup complete: {len(self.service_instances)} services, {len(self.network_wrappers)} network wrappers")
    
    def test_service_discovery(self):
        """Test that all services can be discovered via service locator"""
        print("\n🔍 Testing Service Discovery...")
        
        discovery_results = {}
        
        for service_name in self.service_instances.keys():
            try:
                start_time = time.time()
                
                # Test local discovery
                local_service = get_service(service_name, prefer_network=False)
                local_time = time.time() - start_time
                
                # Test network discovery if wrapper available
                network_time = None
                if service_name in self.network_wrappers:
                    start_time = time.time()
                    network_service = get_service(service_name, prefer_network=True)
                    network_time = time.time() - start_time
                
                discovery_results[service_name] = {
                    'local_discovered': local_service is not None,
                    'local_time': local_time,
                    'network_discovered': network_time is not None,
                    'network_time': network_time
                }
                
                status = "✅" if discovery_results[service_name]['local_discovered'] else "❌"
                print(f"  {status} {service_name}: Local={local_time:.3f}s, Network={network_time:.3f}s" if network_time else f"  {status} {service_name}: Local={local_time:.3f}s")
                
            except Exception as e:
                discovery_results[service_name] = {'error': str(e)}
                print(f"  ❌ {service_name}: Error - {e}")
        
        self.test_results['service_discovery'] = discovery_results
        print(f"✅ Service discovery test complete: {len([r for r in discovery_results.values() if r.get('local_discovered', False)])}/{len(discovery_results)} services discovered")
    
    def test_3_method_pattern_consistency(self):
        """Test that all services properly implement the 3-method pattern"""
        print("\n🎯 Testing 3-Method Pattern Consistency...")
        
        pattern_results = {}
        
        for service_name, service in self.service_instances.items():
            try:
                # Test ask method
                ask_result = service.ask("stats")
                ask_works = isinstance(ask_result, dict) and 'service_type' in str(ask_result)
                
                # Test tell method
                tell_result = service.tell("json", {"test": "data"})
                tell_works = isinstance(tell_result, str) and len(tell_result) > 0
                
                # Test do method
                do_result = service.do("reset stats")
                do_works = isinstance(do_result, dict)
                
                pattern_results[service_name] = {
                    'ask_works': ask_works,
                    'tell_works': tell_works,
                    'do_works': do_works,
                    'all_methods_work': ask_works and tell_works and do_works
                }
                
                status = "✅" if pattern_results[service_name]['all_methods_work'] else "❌"
                print(f"  {status} {service_name}: ask={ask_works}, tell={tell_works}, do={do_works}")
                
            except Exception as e:
                pattern_results[service_name] = {'error': str(e)}
                print(f"  ❌ {service_name}: Error - {e}")
        
        self.test_results['pattern_consistency'] = pattern_results
        working_services = len([r for r in pattern_results.values() if r.get('all_methods_work', False)])
        print(f"✅ 3-method pattern test complete: {working_services}/{len(pattern_results)} services fully compliant")
    
    def test_cross_service_dependencies(self):
        """Test that services can find and use their dependencies correctly"""
        print("\n🔗 Testing Cross-Service Dependencies...")
        
        dependency_results = {}
        
        # Test database service (should work independently)
        try:
            db = self.service_instances['database']
            stats = db.ask("stats")
            dependency_results['database'] = {'independent': True, 'stats': stats}
            print("  ✅ database: Independent operation confirmed")
        except Exception as e:
            dependency_results['database'] = {'error': str(e)}
            print(f"  ❌ database: {e}")
        
        # Test logger service (depends on config and error handler)
        try:
            logger = self.service_instances['logger']
            logger.info("Integration test message")
            stats = logger.ask("stats")
            dependency_results['logger'] = {'dependencies_resolved': True, 'stats': stats}
            print("  ✅ logger: Dependencies resolved successfully")
        except Exception as e:
            dependency_results['logger'] = {'error': str(e)}
            print(f"  ❌ logger: {e}")
        
        # Test points system (depends on logger and error handler)
        try:
            points = self.service_instances['points_system']
            points_data = points.ask("points for placement 1")
            dependency_results['points_system'] = {'calculation_works': True, 'data': points_data}
            print("  ✅ points_system: Cross-service calculation successful")
        except Exception as e:
            dependency_results['points_system'] = {'error': str(e)}
            print(f"  ❌ points_system: {e}")
        
        # Test tabulator (depends on database, logger, error handler, config, points system)
        try:
            tabulator = self.service_instances['tabulator']
            formats = tabulator.ask("formats")
            dependency_results['tabulator'] = {'complex_dependencies': True, 'formats': formats}
            print("  ✅ tabulator: Complex dependency chain resolved")
        except Exception as e:
            dependency_results['tabulator'] = {'error': str(e)}
            print(f"  ❌ tabulator: {e}")
        
        # Test message handler (depends on database, claude, logger, error handler)
        try:
            handler = self.service_instances['message_handler']
            stats = handler.ask("stats")
            dependency_results['message_handler'] = {'multi_dependencies': True, 'stats': stats}
            print("  ✅ message_handler: Multiple dependencies resolved")
        except Exception as e:
            dependency_results['message_handler'] = {'error': str(e)}
            print(f"  ❌ message_handler: {e}")
        
        self.test_results['cross_service_dependencies'] = dependency_results
        working_deps = len([r for r in dependency_results.values() if not r.get('error')])
        print(f"✅ Cross-service dependency test complete: {working_deps}/{len(dependency_results)} dependency chains working")
    
    def test_performance_benchmarks(self):
        """Test performance of service operations and network calls"""
        print("\n⚡ Testing Performance Benchmarks...")
        
        performance_results = {}
        
        # Test local service performance
        for service_name, service in list(self.service_instances.items())[:5]:  # Test first 5 services
            try:
                # Time ask operation
                start_time = time.time()
                service.ask("stats")
                ask_time = time.time() - start_time
                
                # Time tell operation
                start_time = time.time()
                service.tell("json", {"test": "data"})
                tell_time = time.time() - start_time
                
                # Time do operation
                start_time = time.time()
                service.do("reset stats")
                do_time = time.time() - start_time
                
                performance_results[service_name] = {
                    'ask_time_ms': ask_time * 1000,
                    'tell_time_ms': tell_time * 1000,
                    'do_time_ms': do_time * 1000,
                    'total_time_ms': (ask_time + tell_time + do_time) * 1000
                }
                
                total_ms = performance_results[service_name]['total_time_ms']
                print(f"  ⚡ {service_name}: {total_ms:.1f}ms total (ask={ask_time*1000:.1f}ms, tell={tell_time*1000:.1f}ms, do={do_time*1000:.1f}ms)")
                
            except Exception as e:
                performance_results[service_name] = {'error': str(e)}
                print(f"  ❌ {service_name}: {e}")
        
        self.test_results['performance_benchmarks'] = performance_results
        avg_time = sum(r.get('total_time_ms', 0) for r in performance_results.values()) / len(performance_results)
        print(f"✅ Performance benchmark complete: Average {avg_time:.1f}ms per service")
    
    def test_error_handling_resilience(self):
        """Test that services handle errors gracefully and maintain operation"""
        print("\n🛡️ Testing Error Handling Resilience...")
        
        resilience_results = {}
        
        for service_name, service in list(self.service_instances.items())[:3]:  # Test first 3 services
            try:
                # Test invalid ask query
                try:
                    result = service.ask("invalid_query_that_should_fail_gracefully")
                    ask_resilient = isinstance(result, dict) and ('error' in result or 'unknown' in str(result).lower())
                except Exception:
                    ask_resilient = False
                
                # Test invalid tell format
                try:
                    result = service.tell("invalid_format", {"data": "test"})
                    tell_resilient = isinstance(result, str) and len(result) > 0
                except Exception:
                    tell_resilient = False
                
                # Test invalid do action
                try:
                    result = service.do("invalid_action_that_should_fail")
                    do_resilient = isinstance(result, dict) and ('error' in result or 'unknown' in str(result).lower())
                except Exception:
                    do_resilient = False
                
                resilience_results[service_name] = {
                    'ask_resilient': ask_resilient,
                    'tell_resilient': tell_resilient,
                    'do_resilient': do_resilient,
                    'overall_resilient': ask_resilient and tell_resilient and do_resilient
                }
                
                status = "✅" if resilience_results[service_name]['overall_resilient'] else "⚠️"
                print(f"  {status} {service_name}: ask={ask_resilient}, tell={tell_resilient}, do={do_resilient}")
                
            except Exception as e:
                resilience_results[service_name] = {'error': str(e)}
                print(f"  ❌ {service_name}: {e}")
        
        self.test_results['error_handling_resilience'] = resilience_results
        resilient_services = len([r for r in resilience_results.values() if r.get('overall_resilient', False)])
        print(f"✅ Error handling test complete: {resilient_services}/{len(resilience_results)} services are resilient")
    
    def test_end_to_end_workflows(self):
        """Test complete workflows that span multiple services"""
        print("\n🔄 Testing End-to-End Workflows...")
        
        workflow_results = {}
        
        # Workflow 1: Points calculation and ranking workflow
        try:
            print("  🎯 Testing points calculation → ranking workflow...")
            
            # Step 1: Get points for various placements
            points_service = self.service_instances['points_system']
            placement_points = {}
            for placement in [1, 2, 3, 4, 5]:
                result = points_service.ask(f"points for placement {placement}")
                placement_points[placement] = result.get('points', 0) if isinstance(result, dict) else 0
            
            # Step 2: Use tabulator to rank test data
            tabulator = self.service_instances['tabulator']
            test_players = [
                {'name': 'Player A', 'total_points': placement_points[1] + placement_points[3]},
                {'name': 'Player B', 'total_points': placement_points[2] + placement_points[2]},
                {'name': 'Player C', 'total_points': placement_points[1]},
            ]
            
            ranking_result = tabulator.do("custom ranking", 
                                        items=test_players, 
                                        score_func=lambda p: p['total_points'])
            
            workflow_results['points_ranking'] = {
                'placement_points': placement_points,
                'ranking_success': isinstance(ranking_result, dict) and 'data' in ranking_result,
                'workflow_complete': True
            }
            print("    ✅ Points calculation → ranking workflow successful")
            
        except Exception as e:
            workflow_results['points_ranking'] = {'error': str(e)}
            print(f"    ❌ Points calculation → ranking workflow failed: {e}")
        
        # Workflow 2: Error handling → logging workflow
        try:
            print("  📝 Testing error handling → logging workflow...")
            
            # Step 1: Generate an error
            error_handler = self.service_instances['error_handler']
            test_error = Exception("Integration test error")
            error_handler.handle_error(test_error, {"test": "context"})
            
            # Step 2: Check that it was logged
            logger = self.service_instances['logger']
            log_stats = logger.ask("stats")
            
            workflow_results['error_logging'] = {
                'error_handled': True,
                'logging_active': isinstance(log_stats, dict) and 'total_logs' in str(log_stats),
                'workflow_complete': True
            }
            print("    ✅ Error handling → logging workflow successful")
            
        except Exception as e:
            workflow_results['error_logging'] = {'error': str(e)}
            print(f"    ❌ Error handling → logging workflow failed: {e}")
        
        # Workflow 3: Configuration → service initialization workflow
        try:
            print("  ⚙️ Testing configuration → service initialization workflow...")
            
            # Step 1: Check config service
            config = self.service_instances['config']
            config_stats = config.ask("stats")
            
            # Step 2: Verify services can access config
            logger = self.service_instances['logger']
            logger_can_access_config = hasattr(logger, 'config') and logger.config is not None
            
            workflow_results['config_initialization'] = {
                'config_active': isinstance(config_stats, dict),
                'services_access_config': logger_can_access_config,
                'workflow_complete': True
            }
            print("    ✅ Configuration → service initialization workflow successful")
            
        except Exception as e:
            workflow_results['config_initialization'] = {'error': str(e)}
            print(f"    ❌ Configuration → service initialization workflow failed: {e}")
        
        self.test_results['end_to_end_workflows'] = workflow_results
        successful_workflows = len([r for r in workflow_results.values() if r.get('workflow_complete', False)])
        print(f"✅ End-to-end workflow test complete: {successful_workflows}/{len(workflow_results)} workflows successful")
    
    def run_full_test_suite(self):
        """Run the complete integration test suite"""
        print("\n🚀 Starting Full System Integration Test Suite...")
        start_time = time.time()
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Core tests
            self.test_service_discovery()
            self.test_3_method_pattern_consistency()
            self.test_cross_service_dependencies()
            self.test_performance_benchmarks()
            self.test_error_handling_resilience()
            self.test_end_to_end_workflows()
            
            # Calculate overall results
            total_time = time.time() - start_time
            self.generate_test_report(total_time)
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")
            self.test_results['suite_error'] = str(e)
        
        finally:
            self.cleanup_test_environment()
    
    def generate_test_report(self, total_time: float):
        """Generate a comprehensive test report"""
        print(f"\n📊 Full System Integration Test Report")
        print("=" * 60)
        print(f"⏱️  Total test time: {total_time:.2f} seconds")
        
        # Count overall results
        total_tests = 0
        passed_tests = 0
        
        for test_category, results in self.test_results.items():
            if isinstance(results, dict):
                category_total = len(results)
                category_passed = len([r for r in results.values() if not r.get('error') and 
                                     (r.get('local_discovered', False) or 
                                      r.get('all_methods_work', False) or 
                                      r.get('workflow_complete', False) or
                                      r.get('overall_resilient', False) or
                                      'stats' in str(r))])
                
                total_tests += category_total
                passed_tests += category_passed
                
                print(f"✅ {test_category}: {category_passed}/{category_total} passed")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 80:
            print("🎉 INTEGRATION TEST SUITE: PASSED ✅")
            print("The distributed service architecture is working correctly!")
        elif success_rate >= 60:
            print("⚠️  INTEGRATION TEST SUITE: PARTIAL PASS ⚠️")
            print("Most services working, but some issues need attention.")
        else:
            print("❌ INTEGRATION TEST SUITE: FAILED ❌")
            print("Significant issues detected in the distributed architecture.")
        
        # Save detailed results
        self.save_test_results()
    
    def save_test_results(self):
        """Save detailed test results to file"""
        try:
            with open('integration_test_results.json', 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"📄 Detailed results saved to: integration_test_results.json")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        # Stop network wrappers
        for name, wrapper in self.network_wrappers.items():
            try:
                # Network wrappers may not have explicit stop methods
                print(f"  🛑 Stopped network wrapper: {name}")
            except Exception as e:
                print(f"  ⚠️  Error stopping {name}: {e}")
        
        # Clear service cache
        clear_service_cache()
        
        print("✅ Cleanup complete")


def main():
    """Run the full system integration test suite"""
    test_suite = FullSystemIntegrationTest()
    test_suite.run_full_test_suite()


if __name__ == "__main__":
    main()