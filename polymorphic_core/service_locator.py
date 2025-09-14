#!/usr/bin/env python3
"""
service_locator.py - Transparent service discovery layer

This abstraction layer allows modules to request services without knowing
if they're local Python modules or remote network services.

Key principle: Modules request services by capability, not implementation.

Usage:
    # Old way (direct import):
    from utils.database_service import database_service
    
    # New way (capability request):
    database = get_service("database")
    
The service locator automatically:
1. First checks for local Python modules
2. Falls back to mDNS network discovery
3. Returns the same interface regardless of location
"""

import importlib
import sys
from typing import Any, Dict, Optional, Callable, Union
from .real_bonjour import announcer

class ServiceLocator:
    """
    Transparent service discovery that works with both local and network services.
    
    Services are requested by capability name, not import path.
    The locator tries local first, then network discovery.
    """
    
    def __init__(self):
        self.local_cache = {}  # Cached local services
        self.network_cache = {}  # Cached network service clients
        self.capability_map = {
            # Phase 1 - REFACTORED Core Services ✅
            "database": "utils.database_service_refactored.database_service_refactored",
            "logger": "utils.simple_logger_refactored.logger_service",
            "error_handler": "utils.error_handler_refactored.error_handler", 
            "config": "utils.config_service_refactored.config_service",
            
            # Phase 2 - REFACTORED Business Services ✅
            "claude": "services.claude_cli_service_refactored.claude_service",
            "web_editor": "services.polymorphic_web_editor_refactored.web_editor",
            "interactive": "services.interactive_service_refactored.interactive_service",
            "message_handler": "services.message_handler_refactored.message_handler",
            "formatter": "services.bonjour_formatter_service.formatter_service",
            
            # Legacy core services (fallback)
            "database_legacy": "utils.database_service.database_service",
            "logger_legacy": "utils.simple_logger",
            "error_handler_legacy": "utils.error_handler.error_handler",
            "config_legacy": "utils.config_service",
            
            # Legacy business services (fallback)
            "claude_legacy": "services.claude_cli_service.claude_service",
            "web_editor_legacy": "services.polymorphic_web_editor.web_editor",
            "interactive_legacy": "services.interactive_service",
            "message_handler_legacy": "services.message_handler",
            
            # Phase 3+ - Remaining Services (to be refactored)
            "sync": "services.startgg_sync.startgg_sync",
            "twilio": "twilio_service.twilio_service",
        }
        
    def get_service(self, capability_name: str, prefer_network: bool = False) -> Any:
        """
        Get a service by capability name.
        
        Args:
            capability_name: What capability you need (e.g., "database", "logger")
            prefer_network: If True, try network first before local
            
        Returns:
            Service object with the requested capability
            
        Behavior:
        1. If prefer_network=False (default):
           - Try local Python module first
           - Fall back to network service if local fails
        2. If prefer_network=True:
           - Try network service first  
           - Fall back to local Python module if network fails
           
        The returned service has the same interface regardless of source.
        """
        if prefer_network:
            # Network first approach
            service = self._get_network_service(capability_name)
            if service is not None:
                return service
            return self._get_local_service(capability_name)
        else:
            # Local first approach (default)
            service = self._get_local_service(capability_name)
            if service is not None:
                return service
            return self._get_network_service(capability_name)
    
    def _get_local_service(self, capability_name: str) -> Optional[Any]:
        """Try to get service from local Python modules"""
        
        # Check cache first
        if capability_name in self.local_cache:
            return self.local_cache[capability_name]
            
        # Look up module path
        if capability_name not in self.capability_map:
            return None
            
        module_path = self.capability_map[capability_name]
        
        try:
            # Import the module/service
            parts = module_path.split('.')
            if len(parts) == 1:
                # Simple module import
                module = importlib.import_module(parts[0])
                service = module
            else:
                # Import module.attribute
                module_name = '.'.join(parts[:-1])
                attr_name = parts[-1]
                module = importlib.import_module(module_name)
                service = getattr(module, attr_name)
            
            # Cache and return
            self.local_cache[capability_name] = service
            return service
            
        except (ImportError, AttributeError, ModuleNotFoundError) as e:
            # Local service not available
            return None
    
    def _get_network_service(self, capability_name: str) -> Optional[Any]:
        """Try to get service from network via mDNS discovery"""
        
        # Check cache first
        if capability_name in self.network_cache:
            return self.network_cache[capability_name]
        
        # Find services that advertise this capability
        discovered_services = announcer.find_capability(capability_name)
        
        if not discovered_services:
            return None
            
        # Use the first service that matches
        service_data = discovered_services[0]
        
        # Create a network service client
        network_service = NetworkServiceClient(
            service_data['name'],
            service_data['host'], 
            service_data['port'],
            service_data['capabilities']
        )
        
        # Cache and return
        self.network_cache[capability_name] = network_service
        return network_service
    
    def register_capability(self, capability_name: str, module_path: str):
        """Register a new capability mapping"""
        self.capability_map[capability_name] = module_path
    
    def clear_cache(self):
        """Clear both local and network caches"""
        self.local_cache.clear()
        self.network_cache.clear()
    
    def list_available_services(self) -> Dict[str, Dict]:
        """List all available services (local and network)"""
        result = {
            'local': [],
            'network': []
        }
        
        # Check local services
        for capability_name in self.capability_map:
            if self._get_local_service(capability_name) is not None:
                result['local'].append(capability_name)
        
        # Check network services
        discovered = announcer.discover_services()
        for service_data in discovered.values():
            result['network'].append({
                'name': service_data['name'],
                'capabilities': service_data['capabilities'],
                'host': f"{service_data['host']}:{service_data['port']}"
            })
        
        return result


class NetworkServiceClient:
    """
    Client wrapper for network services discovered via mDNS.
    
    Provides the same interface as local services but communicates
    over the network using the 3-method pattern (ask/tell/do).
    """
    
    def __init__(self, service_name: str, host: str, port: int, capabilities: list):
        self.service_name = service_name
        self.host = host
        self.port = port
        self.capabilities = capabilities
        self.base_url = f"http://{host}:{port}"
    
    def ask(self, query: str, **kwargs) -> Any:
        """Send ask request to network service"""
        return self._make_request("ask", {"query": query, **kwargs})
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """Send tell request to network service"""  
        return self._make_request("tell", {"format": format_type, "data": data, **kwargs})
    
    def do(self, action: str, **kwargs) -> Any:
        """Send do request to network service"""
        return self._make_request("do", {"action": action, **kwargs})
    
    def _make_request(self, method: str, payload: dict) -> Any:
        """Make HTTP request to the network service"""
        import requests
        import json
        
        try:
            url = f"{self.base_url}/{method}"
            response = requests.post(
                url, 
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            # If network fails, we could fall back to error response
            return {
                "error": f"Network service {self.service_name} unavailable: {e}",
                "service": self.service_name,
                "method": method
            }
    
    def __getattr__(self, name):
        """
        For backward compatibility with direct method calls.
        
        If someone calls service.some_method(), we translate it to
        service.do("some_method") for network services.
        """
        def network_method(*args, **kwargs):
            # Convert method call to 'do' action
            if args:
                action = f"{name} {' '.join(str(arg) for arg in args)}"
            else:
                action = name
            
            return self.do(action, **kwargs)
        
        return network_method


# Global service locator instance
service_locator = ServiceLocator()

# Convenience functions for easy import
def get_service(capability_name: str, prefer_network: bool = False) -> Any:
    """Get a service by capability name - works with local or network services"""
    return service_locator.get_service(capability_name, prefer_network)

def register_service(capability_name: str, module_path: str):
    """Register a new service capability mapping"""
    service_locator.register_capability(capability_name, module_path)

def list_services() -> Dict[str, Dict]:
    """List all available services"""
    return service_locator.list_available_services()

# Auto-register known services on import
def _auto_register_services():
    """Register common services that modules typically need"""
    # These get registered automatically when this module is imported
    pass

_auto_register_services()

if __name__ == "__main__":
    # Test the service locator
    print("🧪 Testing Service Locator")
    
    # Test local service discovery
    print("\n1. Testing local service access:")
    database = get_service("database")
    print(f"Database service: {database}")
    
    # Test network service discovery  
    print("\n2. Testing network service discovery:")
    services = list_services()
    print(f"Available services: {services}")
    
    # Test network-first approach
    print("\n3. Testing network-first access:")
    network_db = get_service("database", prefer_network=True)
    print(f"Network database service: {network_db}")
    
    print("\n✅ Service locator test complete!")