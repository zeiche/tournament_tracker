#!/usr/bin/env python3
"""
network_service_wrapper.py - Make any Python service network-accessible

This module automatically wraps Python services with HTTP endpoints
so they can be discovered and used over the network.

Key features:
1. Automatically expose ask/tell/do methods via HTTP
2. Auto-announce service capabilities via mDNS  
3. Zero code changes to existing services
4. Transparent local vs network access

Usage:
    # Wrap any service for network access
    from polymorphic_core.network_service_wrapper import wrap_service
    
    # Wrap existing service
    wrapped_db = wrap_service(database_service, "database", port=8090)
    
    # Now other machines can access it via mDNS discovery
"""

import asyncio
import json
import threading
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .real_bonjour import announcer

class ServiceRequest(BaseModel):
    """Request model for service calls"""
    query: Optional[str] = None
    format: Optional[str] = None  
    action: Optional[str] = None
    data: Optional[Any] = None
    args: Optional[list] = None
    kwargs: Optional[dict] = None

class ServiceResponse(BaseModel):
    """Response model for service calls"""
    result: Any
    success: bool = True
    error: Optional[str] = None
    service_name: str
    method: str

@dataclass
class NetworkService:
    """Wrapper for a service exposed over the network"""
    service: Any
    name: str
    port: int
    app: FastAPI
    capabilities: list
    server_thread: Optional[threading.Thread] = None

class NetworkServiceWrapper:
    """
    Wraps Python services to make them accessible over the network.
    
    Each wrapped service gets:
    1. HTTP endpoints for ask/tell/do methods
    2. Automatic mDNS announcement
    3. CORS support for web access
    4. Error handling and logging
    """
    
    def __init__(self):
        self.wrapped_services = {}  # service_name -> NetworkService
        
    def wrap_service(self, 
                    service: Any, 
                    service_name: str, 
                    port: int = None,
                    capabilities: list = None,
                    auto_start: bool = True) -> NetworkService:
        """
        Wrap a Python service to make it network-accessible.
        
        Args:
            service: The service object to wrap
            service_name: Name for mDNS announcement
            port: Port to run on (auto-assigned if None)
            capabilities: List of capabilities (auto-detected if None)
            auto_start: Whether to start the server immediately
            
        Returns:
            NetworkService wrapper object
        """
        
        # Auto-assign port if needed
        if port is None:
            import socket
            sock = socket.socket()
            sock.bind(('', 0))
            port = sock.getsockname()[1]
            sock.close()
        
        # Auto-detect capabilities if needed
        if capabilities is None:
            capabilities = self._detect_capabilities(service, service_name)
        
        # Create FastAPI app for this service
        app = FastAPI(title=f"{service_name} Network Service")
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Create the network service wrapper
        network_service = NetworkService(
            service=service,
            name=service_name,
            port=port,
            app=app,
            capabilities=capabilities
        )
        
        # Add routes to the app
        self._add_service_routes(app, service, service_name)
        
        # Store the wrapped service
        self.wrapped_services[service_name] = network_service
        
        # Auto-start if requested
        if auto_start:
            self.start_service(service_name)
            
        return network_service
    
    def _detect_capabilities(self, service: Any, service_name: str) -> list:
        """Auto-detect service capabilities by introspection"""
        capabilities = []
        
        # Check for 3-method pattern
        if hasattr(service, 'ask'):
            capabilities.append(f"ask() - Query {service_name} with natural language")
        if hasattr(service, 'tell'):
            capabilities.append(f"tell() - Format {service_name} data for output")
        if hasattr(service, 'do'):
            capabilities.append(f"do() - Perform {service_name} actions")
        
        # Check for other common methods
        common_methods = ['get', 'create', 'update', 'delete', 'list', 'find', 'search']
        for method in common_methods:
            if hasattr(service, method):
                capabilities.append(f"{method}() - {method.title()} operations")
        
        # If no capabilities detected, add generic
        if not capabilities:
            capabilities.append(f"General {service_name} service")
            
        return capabilities
    
    def _add_service_routes(self, app: FastAPI, service: Any, service_name: str):
        """Add HTTP routes for the service"""
        
        @app.get("/")
        async def service_info():
            """Get service information"""
            network_service = self.wrapped_services[service_name]
            return {
                "service_name": service_name,
                "capabilities": network_service.capabilities,
                "methods": ["ask", "tell", "do"],
                "status": "running"
            }
        
        @app.post("/ask")
        async def ask_endpoint(request: ServiceRequest):
            """Handle ask requests"""
            try:
                if not hasattr(service, 'ask'):
                    raise HTTPException(status_code=404, detail="ask method not available")
                
                result = service.ask(request.query, **request.kwargs or {})
                return ServiceResponse(
                    result=result,
                    service_name=service_name,
                    method="ask"
                )
            except Exception as e:
                return ServiceResponse(
                    result=None,
                    success=False,
                    error=str(e),
                    service_name=service_name,
                    method="ask"
                )
        
        @app.post("/tell")
        async def tell_endpoint(request: ServiceRequest):
            """Handle tell requests"""
            try:
                if not hasattr(service, 'tell'):
                    raise HTTPException(status_code=404, detail="tell method not available")
                
                result = service.tell(request.format, request.data, **request.kwargs or {})
                return ServiceResponse(
                    result=result,
                    service_name=service_name,
                    method="tell"
                )
            except Exception as e:
                return ServiceResponse(
                    result=None,
                    success=False,
                    error=str(e),
                    service_name=service_name,
                    method="tell"
                )
        
        @app.post("/do")
        async def do_endpoint(request: ServiceRequest):
            """Handle do requests"""
            try:
                if not hasattr(service, 'do'):
                    raise HTTPException(status_code=404, detail="do method not available")
                
                result = service.do(request.action, **request.kwargs or {})
                return ServiceResponse(
                    result=result,
                    service_name=service_name,
                    method="do"
                )
            except Exception as e:
                return ServiceResponse(
                    result=None,
                    success=False,
                    error=str(e),
                    service_name=service_name,
                    method="do"
                )
        
        @app.post("/call/{method_name}")
        async def generic_method_endpoint(method_name: str, request: ServiceRequest):
            """Handle calls to any service method (for backward compatibility)"""
            try:
                if not hasattr(service, method_name):
                    raise HTTPException(status_code=404, detail=f"Method {method_name} not available")
                
                method = getattr(service, method_name)
                if not callable(method):
                    raise HTTPException(status_code=400, detail=f"{method_name} is not callable")
                
                # Call the method with provided args/kwargs
                args = request.args or []
                kwargs = request.kwargs or {}
                result = method(*args, **kwargs)
                
                return ServiceResponse(
                    result=result,
                    service_name=service_name,
                    method=method_name
                )
            except Exception as e:
                return ServiceResponse(
                    result=None,
                    success=False,
                    error=str(e),
                    service_name=service_name,
                    method=method_name
                )
    
    def start_service(self, service_name: str):
        """Start the network server for a wrapped service"""
        if service_name not in self.wrapped_services:
            raise ValueError(f"Service {service_name} not found")
        
        network_service = self.wrapped_services[service_name]
        
        # Announce the service via mDNS
        announcer.announce(
            service_name,
            network_service.capabilities,
            [
                f"Access via HTTP at http://localhost:{network_service.port}",
                f"ask: POST /{network_service.port}/ask",
                f"tell: POST /{network_service.port}/tell", 
                f"do: POST /{network_service.port}/do"
            ],
            port=network_service.port
        )
        
        # Start the server in a background thread
        def run_server():
            uvicorn.run(
                network_service.app,
                host="0.0.0.0",
                port=network_service.port,
                log_level="warning"  # Reduce log noise
            )
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        network_service.server_thread = server_thread
        
        print(f"🌐 Started network service '{service_name}' on port {network_service.port}")
    
    def stop_service(self, service_name: str):
        """Stop a network service"""
        if service_name in self.wrapped_services:
            # Note: uvicorn doesn't have a clean shutdown API from threads
            # In production, you'd use proper process management
            print(f"🛑 Stopping network service '{service_name}'")
            del self.wrapped_services[service_name]
    
    def list_services(self) -> Dict[str, Dict]:
        """List all wrapped network services"""
        result = {}
        for name, network_service in self.wrapped_services.items():
            result[name] = {
                "port": network_service.port,
                "capabilities": network_service.capabilities,
                "status": "running" if network_service.server_thread else "stopped"
            }
        return result

# Global wrapper instance
network_wrapper = NetworkServiceWrapper()

# Convenience functions
def wrap_service(service: Any, 
                service_name: str, 
                port: int = None,
                capabilities: list = None,
                auto_start: bool = True) -> NetworkService:
    """Wrap a service for network access"""
    return network_wrapper.wrap_service(service, service_name, port, capabilities, auto_start)

def start_service(service_name: str):
    """Start a wrapped network service"""
    network_wrapper.start_service(service_name)

def stop_service(service_name: str):
    """Stop a wrapped network service"""
    network_wrapper.stop_service(service_name)

def list_network_services() -> Dict[str, Dict]:
    """List all network services"""
    return network_wrapper.list_services()

if __name__ == "__main__":
    # Test the network service wrapper
    print("🧪 Testing Network Service Wrapper")
    
    # Create a simple test service
    class TestService:
        def ask(self, query: str):
            return f"Asked: {query}"
        
        def tell(self, format_type: str, data=None):
            return f"Told {format_type}: {data}"
        
        def do(self, action: str):
            return f"Did: {action}"
    
    # Wrap and start the service
    test_service = TestService()
    wrapped = wrap_service(
        test_service,
        "Test Service",
        capabilities=["Testing network wrapper"]
    )
    
    print(f"Test service running on port {wrapped.port}")
    print("✅ Test complete - check mDNS announcements!")
    
    # Keep running for testing
    import time
    time.sleep(5)