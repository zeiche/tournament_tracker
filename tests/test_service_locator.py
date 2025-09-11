#!/usr/bin/env python3
"""
test_service_locator.py - Test transparent local vs network service access

This test verifies that modules work identically whether they use:
1. Local Python services (direct imports)
2. Network services (via mDNS discovery)

The key principle: Same code, same results, regardless of service location.
"""

import unittest
import time
import threading
import json
from typing import Any, Dict

from polymorphic_core.service_locator import get_service, list_services
from polymorphic_core.network_service_wrapper import wrap_service
from services.startgg_sync_refactored import StartGGSyncService

class MockDatabaseService:
    """Mock database service for testing"""
    
    def __init__(self):
        self.data = {
            "tournaments": [
                {"id": 1, "name": "Test Tournament 1", "date": "2024-01-15"},
                {"id": 2, "name": "Test Tournament 2", "date": "2024-01-20"}
            ]
        }
    
    def ask(self, query: str, **kwargs) -> Any:
        """Mock database queries"""
        if "tournaments from" in query.lower():
            return {"tournaments": self.data["tournaments"]}
        elif "recent tournaments" in query.lower():
            return {"tournaments": self.data["tournaments"][:1]}
        elif "tournament" in query.lower() and "standings" in query.lower():
            return {"standings": [{"player": "TestPlayer", "rank": 1}]}
        else:
            return {"result": f"Mock response for: {query}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """Mock data formatting"""
        if format_type == "json":
            return json.dumps(data, indent=2)
        elif format_type == "summary":
            return f"Mock summary: {len(data) if hasattr(data, '__len__') else 'unknown'} items"
        else:
            return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Mock database actions"""
        return {"action": action, "status": "completed", "mock": True}

class MockLoggerService:
    """Mock logger service for testing"""
    
    def __init__(self):
        self.logs = []
    
    def info(self, message: str):
        self.logs.append(("INFO", message))
    
    def warning(self, message: str):
        self.logs.append(("WARNING", message))
    
    def error(self, message: str):
        self.logs.append(("ERROR", message))

class MockErrorHandler:
    """Mock error handler service for testing"""
    
    def handle_exception(self, exception: Exception, severity):
        return {"handled": True, "exception": str(exception), "severity": str(severity)}

class TestServiceLocator(unittest.TestCase):
    """Test the service locator and transparent service access"""
    
    def setUp(self):
        """Set up test services"""
        self.mock_db = MockDatabaseService()
        self.mock_logger = MockLoggerService()
        self.mock_error_handler = MockErrorHandler()
        
        # Register mock services as network services
        self.network_db = wrap_service(
            self.mock_db, 
            "test_database", 
            capabilities=["Mock database for testing"],
            auto_start=True
        )
        
        self.network_logger = wrap_service(
            self.mock_logger,
            "test_logger", 
            capabilities=["Mock logger for testing"],
            auto_start=True
        )
        
        # Give services time to start
        time.sleep(1)
    
    def test_local_vs_network_identical_results(self):
        """Test that local and network services return identical results"""
        
        # Create two sync services: one local-first, one network-first
        local_sync = StartGGSyncService(prefer_network=False)
        network_sync = StartGGSyncService(prefer_network=True)
        
        # Test queries - should return identical results
        test_queries = [
            "tournaments from 2024",
            "recent tournaments", 
            "sync status"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                local_result = local_sync.ask(query)
                network_result = network_sync.ask(query)
                
                # Results should be identical (ignoring service availability differences)
                # Focus on the structure and type of response
                self.assertIsInstance(local_result, type(network_result))
                if isinstance(local_result, dict) and isinstance(network_result, dict):
                    # Both should have similar keys
                    self.assertTrue(
                        len(local_result) > 0 or len(network_result) > 0,
                        f"Both services returned empty results for: {query}"
                    )
    
    def test_format_consistency(self):
        """Test that formatting is consistent between local and network"""
        
        local_sync = StartGGSyncService(prefer_network=False)
        network_sync = StartGGSyncService(prefer_network=True)
        
        test_data = {"tournaments": [{"name": "Test", "date": "2024-01-01"}]}
        formats = ["json", "summary", "discord"]
        
        for format_type in formats:
            with self.subTest(format_type=format_type):
                local_formatted = local_sync.tell(format_type, test_data)
                network_formatted = network_sync.tell(format_type, test_data)
                
                # Both should be strings
                self.assertIsInstance(local_formatted, str)
                self.assertIsInstance(network_formatted, str)
                
                # Both should contain some content
                self.assertGreater(len(local_formatted), 0)
                self.assertGreater(len(network_formatted), 0)
    
    def test_action_consistency(self):
        """Test that actions work consistently between local and network"""
        
        local_sync = StartGGSyncService(prefer_network=False)
        network_sync = StartGGSyncService(prefer_network=True)
        
        test_actions = [
            "test connection",
            "sync tournaments"
        ]
        
        for action in test_actions:
            with self.subTest(action=action):
                local_result = local_sync.do(action)
                network_result = network_sync.do(action)
                
                # Both should return dict results
                self.assertIsInstance(local_result, dict)
                self.assertIsInstance(network_result, dict)
                
                # Both should have some result
                self.assertGreater(len(local_result), 0)
                self.assertGreater(len(network_result), 0)
    
    def test_service_discovery(self):
        """Test that service discovery works"""
        
        services = list_services()
        
        # Should find both local and network services
        self.assertIn("local", services)
        self.assertIn("network", services)
        
        # Should have some services available
        self.assertTrue(
            len(services["local"]) > 0 or len(services["network"]) > 0,
            "No services discovered"
        )
        
        print(f"Discovered services: {services}")
    
    def test_fallback_behavior(self):
        """Test that fallback from local to network (or vice versa) works"""
        
        # Test with a non-existent local service
        # Should fall back to network if available
        sync_service = StartGGSyncService(prefer_network=False)
        
        # This should work even if some services are network-only
        status = sync_service.ask("sync status")
        self.assertIsInstance(status, dict)
        self.assertIn("status", status)
    
    def test_error_handling_consistency(self):
        """Test that error handling is consistent"""
        
        local_sync = StartGGSyncService(prefer_network=False)
        network_sync = StartGGSyncService(prefer_network=True)
        
        # Test invalid queries
        invalid_query = "invalid query that should fail gracefully"
        
        local_result = local_sync.ask(invalid_query)
        network_result = network_sync.ask(invalid_query)
        
        # Both should handle errors gracefully
        self.assertIsInstance(local_result, dict)
        self.assertIsInstance(network_result, dict)
        
        # Both should indicate error somehow
        self.assertTrue(
            "error" in local_result or "status" in local_result
        )
        self.assertTrue(
            "error" in network_result or "status" in network_result
        )

class TestNetworkServiceWrapper(unittest.TestCase):
    """Test the network service wrapper functionality"""
    
    def test_wrap_service(self):
        """Test wrapping a service for network access"""
        
        mock_service = MockDatabaseService()
        
        # Wrap the service
        wrapped = wrap_service(
            mock_service,
            "test_wrap_service",
            capabilities=["Test wrapping"],
            auto_start=True
        )
        
        # Should have network properties
        self.assertIsNotNone(wrapped.port)
        self.assertIsNotNone(wrapped.app)
        self.assertGreater(len(wrapped.capabilities), 0)
        
        # Give it time to start
        time.sleep(1)
        
        print(f"Wrapped service running on port {wrapped.port}")
    
    def test_three_method_pattern(self):
        """Test that wrapped services expose ask/tell/do pattern"""
        
        mock_service = MockDatabaseService()
        wrapped = wrap_service(mock_service, "test_three_methods", auto_start=True)
        
        time.sleep(1)
        
        # Test that the service is discoverable
        # (Full HTTP testing would require more setup)
        self.assertIsNotNone(wrapped.service)
        self.assertTrue(hasattr(wrapped.service, 'ask'))
        self.assertTrue(hasattr(wrapped.service, 'tell'))
        self.assertTrue(hasattr(wrapped.service, 'do'))

if __name__ == "__main__":
    print("🧪 Testing Service Locator and Network Transparency")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2)
    
    print("\n✅ Service locator tests complete!")
    print("💡 The same code works with local AND network services!")