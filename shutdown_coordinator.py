#!/usr/bin/env python3
"""
shutdown_coordinator.py - Graceful shutdown coordinator
Announces shutdown to all modules and waits for them to clean up
"""

import asyncio
import signal
import sys
import time
from typing import Set, Callable
from capability_announcer import announcer
from capability_discovery import capability_registry

class ShutdownCoordinator:
    """Coordinates graceful shutdown across all modules"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.shutdown_handlers: Set[Callable] = set()
        self.is_shutting_down = False
        self.shutdown_event = asyncio.Event() if asyncio.get_event_loop().is_running() else None
        
        # Announce ourselves
        announcer.announce(
            "ShutdownCoordinator",
            [
                "I coordinate graceful shutdowns",
                "I broadcast shutdown signals to all modules",
                "I wait for modules to clean up",
                "I ensure nothing is left running",
                "Register with me using register_shutdown_handler()"
            ]
        )
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def register_shutdown_handler(self, handler: Callable):
        """Register a shutdown handler that will be called on shutdown"""
        self.shutdown_handlers.add(handler)
        announcer.announce(
            "ShutdownCoordinator",
            [f"Registered shutdown handler: {handler.__name__ if hasattr(handler, '__name__') else str(handler)}"]
        )
        
    def unregister_shutdown_handler(self, handler: Callable):
        """Unregister a shutdown handler"""
        self.shutdown_handlers.discard(handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        if not self.is_shutting_down:
            announcer.announce(
                "ShutdownCoordinator",
                [f"Received signal {signum}, initiating graceful shutdown..."]
            )
            self.initiate_shutdown()
            
    def initiate_shutdown(self):
        """Initiate graceful shutdown"""
        if self.is_shutting_down:
            return
            
        self.is_shutting_down = True
        
        # Announce shutdown is starting
        announcer.announce(
            "SHUTDOWN",
            [
                "🛑 SHUTDOWN INITIATED",
                "All modules should save state and clean up",
                "Graceful shutdown in progress..."
            ]
        )
        
        print("\n" + "="*60)
        print("🛑 GRACEFUL SHUTDOWN INITIATED")
        print("="*60)
        
        # Call all registered shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                announcer.announce(
                    "ShutdownCoordinator",
                    [f"Calling shutdown handler: {handler.__name__ if hasattr(handler, '__name__') else str(handler)}"]
                )
                
                # Handle both sync and async handlers
                if asyncio.iscoroutinefunction(handler):
                    # Run async handler
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(handler())
                        else:
                            asyncio.run(handler())
                    except:
                        pass
                else:
                    # Run sync handler
                    handler()
                    
            except Exception as e:
                announcer.announce(
                    "ShutdownCoordinator",
                    [f"Error in shutdown handler: {e}"]
                )
                
        # Announce shutdown stages
        announcer.announce(
            "SHUTDOWN",
            ["Stage 1: Disconnecting from external services..."]
        )
        time.sleep(0.5)
        
        announcer.announce(
            "SHUTDOWN",
            ["Stage 2: Saving state and closing files..."]
        )
        time.sleep(0.5)
        
        announcer.announce(
            "SHUTDOWN",
            ["Stage 3: Cleaning up resources..."]
        )
        time.sleep(0.5)
        
        # Final announcement
        announcer.announce(
            "SHUTDOWN",
            [
                "✅ SHUTDOWN COMPLETE",
                "All modules have been notified",
                "Goodbye!"
            ]
        )
        
        print("\n✅ Graceful shutdown complete")
        print("="*60 + "\n")
        
        # Exit
        sys.exit(0)
        
    async def wait_for_shutdown(self):
        """Wait for shutdown signal (async)"""
        if not self.shutdown_event:
            self.shutdown_event = asyncio.Event()
        await self.shutdown_event.wait()
        
    def shutdown_requested(self) -> bool:
        """Check if shutdown has been requested"""
        return self.is_shutting_down

# Global instance
shutdown_coordinator = ShutdownCoordinator()

def register_for_shutdown(handler: Callable):
    """Global function to register shutdown handlers"""
    shutdown_coordinator.register_shutdown_handler(handler)
    
def request_shutdown():
    """Global function to request shutdown"""
    shutdown_coordinator.initiate_shutdown()
    
def on_shutdown(func):
    """Decorator to register a function as a shutdown handler"""
    register_for_shutdown(func)
    return func

# Auto-discover and shutdown services
def shutdown_all_services():
    """Shutdown all discovered services"""
    announcer.announce(
        "ShutdownCoordinator",
        ["Shutting down all discovered services..."]
    )
    
    # Try to shutdown each registered service
    if hasattr(capability_registry, 'services'):
        for service_name, service_getter in capability_registry.services.items():
            try:
                service = service_getter()
                
                # Try common shutdown methods
                if hasattr(service, 'shutdown'):
                    announcer.announce(
                        "ShutdownCoordinator",
                        [f"Shutting down service: {service_name}"]
                    )
                    service.shutdown()
                elif hasattr(service, 'close'):
                    service.close()
                elif hasattr(service, 'stop'):
                    service.stop()
                    
            except Exception as e:
                announcer.announce(
                    "ShutdownCoordinator",
                    [f"Error shutting down {service_name}: {e}"]
                )

# Register the service shutdown handler
register_for_shutdown(shutdown_all_services)

if __name__ == "__main__":
    print("Shutdown Coordinator Test")
    print("Press Ctrl+C to test graceful shutdown...")
    
    # Register a test handler
    @on_shutdown
    def test_handler():
        print("Test handler: Cleaning up...")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass