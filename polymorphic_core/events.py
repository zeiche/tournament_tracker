#!/usr/bin/env python3
"""
synchronous_events.py - Polymorphic event system
Handles all events polymorphically - doesn't care if sync or async.
Events flow through the system without blocking.
"""

class SynchronousEvents:
    """
    Like Bonjour/mDNS - services announce their presence and capabilities.
    """
    def __init__(self):
        self.announcements = []
        self.listeners = []  # Functions that listen for announcements
        self.service_registry = {}  # Map service names to their handlers
    
    def add_listener(self, listener_func):
        """Add a listener function that gets called on every announcement"""
        self.listeners.append(listener_func)
    
    def announce(self, service_name: str, capabilities: list, examples: list = None):
        """
        Service announces itself - "Hello, I'm here and I can do these things!"
        
        Args:
            service_name: "Tournament Model", "Query Engine", etc.
            capabilities: List of things this service can do
            examples: Optional example usage
        """
        announcement = {
            'service': service_name,
            'capabilities': capabilities,
            'examples': examples or []
        }
        self.announcements.append(announcement)
        
        # Notify all listeners - check if we're in async context
        import asyncio
        import threading
        
        try:
            # Check if there's an event loop running
            loop = asyncio.get_running_loop()
            # We're in async context - schedule listeners to run without blocking
            for listener in self.listeners:
                async def run_async():
                    try:
                        # Run sync listener in executor to not block
                        await loop.run_in_executor(None, listener, service_name, capabilities, examples)
                    except Exception as e:
                        print(f"Listener error: {e}")
                # Create task to run concurrently
                asyncio.create_task(run_async())
        except RuntimeError:
            # No event loop - we're in sync context, run normally
            for listener in self.listeners:
                try:
                    listener(service_name, capabilities, examples)
                except Exception as e:
                    print(f"Listener error: {e}")
        
        return self
    
    def register_service(self, service_name: str, handler):
        """
        Register a service handler that can respond to signals.
        
        Args:
            service_name: Name of the service
            handler: Object or function that handles signals (must have handle_signal method or be callable)
        """
        self.service_registry[service_name] = handler
    
    def send_signal(self, signal_type: str, target_service: str = None, data: dict = None):
        """
        Send a signal to services (like Bonjour discovery).
        
        Args:
            signal_type: Type of signal ('status', 'ping', 'info', etc.)
            target_service: Specific service to target, or None for broadcast
            data: Optional data to include with signal
        
        Returns:
            Dict of service responses
        """
        responses = {}
        
        if target_service:
            # Send to specific service
            if target_service in self.service_registry:
                handler = self.service_registry[target_service]
                try:
                    if hasattr(handler, 'handle_signal'):
                        responses[target_service] = handler.handle_signal(signal_type, data)
                    elif callable(handler):
                        responses[target_service] = handler(signal_type, data)
                except Exception as e:
                    responses[target_service] = {'error': str(e)}
        else:
            # Broadcast to all services
            for service_name, handler in self.service_registry.items():
                try:
                    if hasattr(handler, 'handle_signal'):
                        responses[service_name] = handler.handle_signal(signal_type, data)
                    elif callable(handler):
                        responses[service_name] = handler(signal_type, data)
                except Exception as e:
                    responses[service_name] = {'error': str(e)}
        
        return responses
    
    def get_announcements_for_claude(self) -> str:
        """
        Format all announcements for Claude's context.
        """
        if not self.announcements:
            return "No services have announced themselves yet."
        
        context = "=== Services Available to You ===\n"
        for announcement in self.announcements:
            context += f"\n📢 {announcement['service']} announces:\n"
            context += "I can:\n"
            for cap in announcement['capabilities']:
                context += f"  • {cap}\n"
            
            if announcement['examples']:
                context += "Examples:\n"
                for ex in announcement['examples']:
                    context += f"  - {ex}\n"
        
        return context


# Global event system - polymorphic singleton
announcer = SynchronousEvents()
# Keep compatibility
CapabilityAnnouncer = SynchronousEvents


# Auto-announcement decorators
def announces_capability(service_name: str, *capabilities):
    """
    Decorator for classes/functions to announce their capabilities.
    """
    def decorator(obj):
        # Announce when decorated
        announcer.announce(service_name, list(capabilities))
        return obj
    return decorator

# Export for compatibility
__all__ = ['SynchronousEvents', 'announcer', 'CapabilityAnnouncer', 'announces_capability']


# When models are imported, they announce themselves
def announce_models():
    """
    Models announce what they can do when loaded.
    """
    try:
        # Tournament model announces itself
        announcer.announce(
            "Tournament Model",
            [
                "Track tournament events with dates and locations",
                "Calculate attendance and growth metrics",
                "Determine if tournaments are majors",
                "Measure days since tournament"
            ],
            [
                "Ask about recent tournaments",
                "Get tournament attendance numbers",
                "Find tournaments by venue"
            ]
        )
        
        # Player model announces itself
        announcer.announce(
            "Player Model", 
            [
                "Track player performance and standings",
                "Calculate win rates and consistency scores",
                "Show podium finishes",
                "Rank players by points"
            ],
            [
                "Show top players",
                "Get player statistics",
                "Find player's tournament history"
            ]
        )
        
        # Organization model announces itself
        announcer.announce(
            "Organization Model",
            [
                "Track tournament organizers and venues",
                "Count total events hosted",
                "Manage contact information",
                "Show organization growth"
            ],
            [
                "Which venues host the most events",
                "Organization contact details",
                "Venue tournament history"
            ]
        )
        
    except Exception as e:
        announcer.announce(
            "Error Reporter",
            [f"Models couldn't fully announce: {e}"]
        )


def announce_queries():
    """
    Query system announces its capabilities.
    """
    try:
        announcer.announce(
            "Query Engine",
            [
                "Natural language tournament queries",
                "Top player rankings",
                "Recent tournament listings",
                "Organization statistics"
            ],
            [
                "show top 10 players",
                "recent tournaments",
                "show player WEST"
            ]
        )
    except:
        pass


def get_full_context():
    """
    Get all announcements for Claude - this is what Discord bot calls.
    """
    # Clear and re-announce (in case new services loaded)
    global announcer
    announcer = CapabilityAnnouncer()
    
    # Services announce themselves
    announce_models()
    announce_queries()
    
    # Check what's actually available
    try:
        import tournament_models
        announcer.announce(
            "System Status",
            ["tournament_models module is loaded and ready"]
        )
    except:
        announcer.announce(
            "System Status", 
            ["Running in limited mode - models not loaded"]
        )
    
    return announcer.get_announcements_for_claude()


if __name__ == "__main__":
    # Test announcements
    print(get_full_context())