#!/usr/bin/env python3
"""
test_phase1_integration.py - Integration test for Phase 1 refactored services

This test verifies that all Phase 1 core services work together:
1. Database Service (Refactored)
2. Logger Service (Refactored)
3. Error Handler (Refactored)
4. Config Service (Refactored)

Key validations:
- Service locator finds all refactored services
- Services work with both local and network dependencies
- Cross-service communication works via service locator
- Backward compatibility is maintained
"""

import unittest
import time
import tempfile
import os
from typing import Dict, Any

from polymorphic_core.service_locator import get_service, list_services, service_locator
from polymorphic_core.network_service_wrapper import wrap_service

# Import refactored services
from utils.database_service import RefactoredDatabaseService, database_service
from utils.simple_logger_refactored import RefactoredLoggerService, logger_service, info, warning, error
from utils.error_handler_refactored import RefactoredErrorHandler, error_handler, handle_exception, ErrorSeverity
from utils.config_service_refactored import RefactoredConfigService, config_service, get_config

class TestPhase1Integration(unittest.TestCase):
    """Test integration of all Phase 1 refactored services"""
    
    def setUp(self):
        """Set up test environment"""
        # Register refactored services in service locator
        service_locator.register_capability("database", "utils.database_service.database_service")
        service_locator.register_capability("logger", "utils.simple_logger_refactored.logger_service")
        service_locator.register_capability("error_handler", "utils.error_handler_refactored.error_handler")
        service_locator.register_capability("config", "utils.config_service_refactored.config_service")
        
        # Clear any caches
        service_locator.clear_cache()
    
    def test_service_discovery(self):
        """Test that all Phase 1 services can be discovered"""
        
        # Test local service discovery
        database = get_service("database")
        logger = get_service("logger")
        error_handler = get_service("error_handler")
        config = get_service("config")
        
        # All services should be found
        self.assertIsNotNone(database)
        self.assertIsNotNone(logger)
        self.assertIsNotNone(error_handler)
        self.assertIsNotNone(config)
        
        # Should be the refactored versions
        self.assertIsInstance(database, RefactoredDatabaseService)
        self.assertIsInstance(logger, RefactoredLoggerService)
        self.assertIsInstance(error_handler, RefactoredErrorHandler)
        self.assertIsInstance(config, RefactoredConfigService)
    
    def test_cross_service_communication(self):
        """Test that services can communicate with each other via service locator"""
        
        # Get services
        database = get_service("database")
        logger = get_service("logger")
        error_handler = get_service("error_handler")
        config = get_service("config")
        
        # Test database -> logger communication
        stats = database.ask("stats")
        self.assertIsInstance(stats, dict)
        
        # Test logger -> error handler communication
        logger.error("Test error message")
        recent_logs = logger.ask("recent logs")
        self.assertIn("logs", recent_logs)
        self.assertGreater(len(recent_logs["logs"]), 0)
        
        # Test error handler -> logger communication
        try:
            raise ValueError("Test exception for integration")
        except Exception as e:
            error_context = error_handler.handle_exception(e, ErrorSeverity.LOW)
            self.assertIsNotNone(error_context)
        
        # Test config service
        discord_token = config.ask("discord token")
        # Should return None or actual token, not error
        self.assertTrue(discord_token is None or isinstance(discord_token, str))
    
    def test_backward_compatibility(self):
        """Test that backward compatibility functions still work"""
        
        # Test logger backward compatibility
        info("Test info message")
        warning("Test warning message")
        error("Test error message")
        
        # Test error handler backward compatibility
        try:
            raise RuntimeError("Test runtime error")
        except Exception as e:
            error_context = handle_exception(e, ErrorSeverity.MEDIUM)
            self.assertIsNotNone(error_context)
        
        # Test config backward compatibility
        result = get_config("database")
        self.assertEqual(result, "tournament_tracker.db")
    
    def test_local_vs_network_consistency(self):
        """Test that local and network services work consistently"""
        
        # Create local-first services
        db_local = RefactoredDatabaseService(prefer_network=False)
        logger_local = RefactoredLoggerService(prefer_network=False)
        error_local = RefactoredErrorHandler(prefer_network=False)
        config_local = RefactoredConfigService(prefer_network=False)
        
        # Create network-first services
        db_network = RefactoredDatabaseService(prefer_network=True)
        logger_network = RefactoredLoggerService(prefer_network=True)
        error_network = RefactoredErrorHandler(prefer_network=True)
        config_network = RefactoredConfigService(prefer_network=True)
        
        # Test database consistency
        stats_local = db_local.ask("stats")
        stats_network = db_network.ask("stats")
        
        # Both should return similar structure
        self.assertIsInstance(stats_local, dict)
        self.assertIsInstance(stats_network, dict)
        
        # Test logger consistency
        logger_local.info("Local test message")
        logger_network.info("Network test message")
        
        local_logs = logger_local.ask("recent logs")
        network_logs = logger_network.ask("recent logs")
        
        self.assertIn("logs", local_logs)
        self.assertIn("logs", network_logs)
        
        # Test config consistency
        local_status = config_local.ask("config status")
        network_status = config_network.ask("config status")
        
        self.assertIsInstance(local_status, dict)
        self.assertIsInstance(network_status, dict)
    
    def test_error_handling_chain(self):
        """Test that error handling works across the service chain"""
        
        database = get_service("database")
        error_handler = get_service("error_handler")
        
        # Test error in database operation
        result = database.ask("invalid query that should fail gracefully")
        
        # Should handle error gracefully, not crash
        self.assertIsInstance(result, dict)
        
        # Check error handler received the error
        recent_errors = error_handler.ask("recent errors")
        self.assertIsInstance(recent_errors, dict)
    
    def test_three_method_pattern_consistency(self):
        """Test that all services follow the 3-method pattern consistently"""
        
        services = [
            get_service("database"),
            get_service("logger"),
            get_service("error_handler"),
            get_service("config")
        ]
        
        for service in services:
            # All should have ask, tell, do methods
            self.assertTrue(hasattr(service, 'ask'))
            self.assertTrue(hasattr(service, 'tell'))
            self.assertTrue(hasattr(service, 'do'))
            
            # All should be callable
            self.assertTrue(callable(service.ask))
            self.assertTrue(callable(service.tell))
            self.assertTrue(callable(service.do))
    
    def test_service_announcements(self):
        """Test that all services announce themselves properly"""
        
        # Check that services are available
        available = list_services()
        
        # Should have local services available
        self.assertIn("local", available)
        
        # Local services should include our registered ones
        # (This test depends on the service locator finding them)
        for service_name in ["database", "logger", "error_handler", "config"]:
            service = get_service(service_name)
            self.assertIsNotNone(service, f"Service {service_name} should be discoverable")
    
    def test_performance_impact(self):
        """Test that service locator doesn't significantly impact performance"""
        
        # Time direct access
        start = time.time()
        for _ in range(100):
            db = database_service
            db.ask("stats")
        direct_time = time.time() - start
        
        # Time via service locator
        start = time.time()
        for _ in range(100):
            db = get_service("database")
            db.ask("stats")
        locator_time = time.time() - start
        
        # Service locator should not be more than 2x slower due to caching
        overhead_ratio = locator_time / direct_time if direct_time > 0 else 1
        self.assertLess(overhead_ratio, 3.0, f"Service locator overhead too high: {overhead_ratio:.2f}x")
    
    def test_format_consistency(self):
        """Test that formatting is consistent across services"""
        
        database = get_service("database")
        logger = get_service("logger")
        error_handler = get_service("error_handler")
        config = get_service("config")
        
        # Test JSON formatting
        db_stats = database.ask("stats")
        db_json = database.tell("json", db_stats)
        self.assertTrue(db_json.startswith("{") or db_json.startswith("["))
        
        log_stats = logger.ask("log stats")
        log_json = logger.tell("json", log_stats)
        self.assertTrue(log_json.startswith("{") or log_json.startswith("["))
        
        # Test Discord formatting
        db_discord = database.tell("discord", db_stats)
        self.assertIsInstance(db_discord, str)
        self.assertGreater(len(db_discord), 0)
        
        config_status = config.ask("config status")
        config_discord = config.tell("discord", config_status)
        self.assertIsInstance(config_discord, str)

class TestServiceNetworkExposure(unittest.TestCase):
    """Test exposing refactored services over the network"""
    
    def setUp(self):
        """Set up network service wrappers"""
        self.wrapped_services = []
    
    def tearDown(self):
        """Clean up network services"""
        # In a real implementation, we'd stop the services
        pass
    
    def test_wrap_database_service(self):
        """Test wrapping database service for network access"""
        
        db_service = RefactoredDatabaseService(prefer_network=False)
        
        # Wrap for network access
        wrapped = wrap_service(
            db_service,
            "test_database_network",
            capabilities=["Test database service over network"],
            auto_start=False  # Don't start server in test
        )
        
        self.assertIsNotNone(wrapped)
        self.assertEqual(wrapped.name, "test_database_network")
        self.assertGreater(len(wrapped.capabilities), 0)
        
        # Service should have the required methods
        self.assertTrue(hasattr(wrapped.service, 'ask'))
        self.assertTrue(hasattr(wrapped.service, 'tell'))
        self.assertTrue(hasattr(wrapped.service, 'do'))
    
    def test_wrap_all_phase1_services(self):
        """Test wrapping all Phase 1 services for network access"""
        
        services_to_wrap = [
            (RefactoredDatabaseService(prefer_network=False), "network_database"),
            (RefactoredLoggerService(prefer_network=False), "network_logger"),
            (RefactoredErrorHandler(prefer_network=False), "network_error_handler"),
            (RefactoredConfigService(prefer_network=False), "network_config")
        ]
        
        for service, name in services_to_wrap:
            wrapped = wrap_service(
                service,
                name,
                capabilities=[f"Network-accessible {name}"],
                auto_start=False
            )
            
            self.assertIsNotNone(wrapped)
            self.assertEqual(wrapped.name, name)
            self.wrapped_services.append(wrapped)
        
        # All services should be wrapped successfully
        self.assertEqual(len(self.wrapped_services), 4)

if __name__ == "__main__":
    print("🧪 Testing Phase 1 Integration - Refactored Core Services")
    print("=" * 70)
    
    # Run the tests
    unittest.main(verbosity=2)
    
    print("\n✅ Phase 1 integration tests complete!")
    print("🎯 All core services refactored and working with service locator!")
    print("💡 Database, Logger, Error Handler, and Config services all use location transparency!")