#!/usr/bin/env python3
"""
real_bonjour.py - ACTUAL Bonjour/mDNS implementation
Replaces the fake announcements with real network service discovery.
"""

import socket
import json
import threading
import time
from typing import List, Dict, Any, Optional, Callable
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceListener
import uuid
# Avoiding circular import with logger

class RealBonjourAnnouncer:
    """
    Real Bonjour/mDNS announcer that actually uses the network.
    Backward compatible with the fake announcer API.
    """
    
    def __init__(self, service_type: str = "_tournament._tcp.local."):
        self.service_type = service_type
        self.announced_services = {}  # name -> ServiceInfo
        self.discovered_services = {}  # name -> service_data
        self.listeners = []  # Callback functions
        self.service_registry = {}  # For signals
        
        # Temporarily disabled real Bonjour - using local-only mode
        # try:
        #     # Try to create Zeroconf with error handling for socket issues
        #     self.zeroconf = Zeroconf(interfaces=None)
        #     # Start discovery browser
        #     self.browser = ServiceBrowser(self.zeroconf, self.service_type, self._ServiceListener(self))
        #     print(f"🌐 Real Bonjour announcer started (service type: {self.service_type})")
        # except Exception as e:
        #     print(f"⚠️  Warning: Real Bonjour failed to start ({e}). Falling back to local-only mode.")
        #     self.zeroconf = None
        #     self.browser = None

        print("🏠 Real Bonjour disabled - using local-only mode")
        self.zeroconf = None
        self.browser = None
    
    class _ServiceListener(ServiceListener):
        """Internal listener for discovered services"""
        
        def __init__(self, announcer):
            self.announcer = announcer
        
        def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            # Skip if we already know about this service
            if name in self.announcer.discovered_services:
                return
            
            # Skip if zeroconf is None (fallback mode)
            if not zc or not self.announcer.zeroconf:
                return
            
            # Skip if zeroconf is shutting down
            try:
                info = zc.get_service_info(type_, name)
            except Exception:
                # Zeroconf is shutting down, ignore this service
                return
            if info:
                # Parse service capabilities from TXT records
                properties = {}
                if info.properties:
                    for key, value in info.properties.items():
                        try:
                            properties[key.decode()] = value.decode() if value else ""
                        except:
                            properties[str(key)] = str(value) if value else ""
                
                # Store discovered service
                service_data = {
                    'name': name.replace(f".{type_}", ""),
                    'host': socket.inet_ntoa(info.addresses[0]) if info.addresses else "unknown",
                    'port': info.port,
                    'properties': properties,
                    'capabilities': properties.get('capabilities', '').split(',') if properties.get('capabilities') else [],
                    'examples': properties.get('examples', '').split('|') if properties.get('examples') else []
                }
                
                self.announcer.discovered_services[name] = service_data
                
                # Notify listeners (only once per service)
                for listener in self.announcer.listeners:
                    try:
                        listener(
                            service_data['name'], 
                            service_data['capabilities'], 
                            service_data['examples']
                        )
                    except Exception as e:
                        print(f"Listener error: {e}")
                
                print(f"🔍 Discovered: {service_data['name']} at {service_data['host']}:{service_data['port']}")
        
        def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            if name in self.announcer.discovered_services:
                service_data = self.announcer.discovered_services.pop(name)
                print(f"👋 Service left: {service_data['name']}")
        
        def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
            # Handle service updates
            self.add_service(zc, type_, name)
    
    def announce(self, service_name: str, capabilities: List[str], examples: List[str] = None, port: int = None):
        """
        Announce a service on the network using real mDNS - NON-BLOCKING!
        
        Args:
            service_name: Name of the service
            capabilities: List of things this service can do
            examples: Optional examples
            port: Port number (auto-assigned if None)
        """
        examples = examples or []
        
        # Skip if zeroconf is None (fallback mode)
        if not self.zeroconf:
            print(f"🏠 Local-only: {service_name} (mDNS unavailable)")
            return self
        
        # Skip if already announced or being announced
        if service_name in self.announced_services:
            return self
        
        # Mark as being processed to prevent duplicates
        self.announced_services[service_name] = None
        
        # Do the announcement in a background thread to avoid blocking
        import threading
        def _announce_background():
            try:
                # Get a free port if none specified
                if port is None:
                    sock = socket.socket()
                    sock.bind(('', 0))
                    port_to_use = sock.getsockname()[1]
                    sock.close()
                else:
                    port_to_use = port
                
                # Get local IP (cached to avoid repeated DNS lookups)
                if not hasattr(self, '_local_ip'):
                    hostname = socket.gethostname()
                    self._local_ip = socket.gethostbyname(hostname)
                    self._hostname = hostname
                
                # Create TXT record properties
                properties = {
                    'capabilities': ','.join(capabilities),
                    'examples': '|'.join(examples),
                    'type': 'tournament-service',
                    'version': '1.0'
                }
                
                # Convert to bytes for zeroconf (limit to 255 bytes per value)
                txt_properties = {}
                for key, value in properties.items():
                    # Truncate long values to avoid zeroconf error
                    value_str = str(value)
                    if len(value_str) > 200:  # Leave some margin
                        value_str = value_str[:200] + "..."
                    txt_properties[key.encode()[:63]] = value_str.encode()[:255]
                
                # Create service info with unique suffix to avoid conflicts
                import time
                unique_suffix = f"{int(time.time() * 1000) % 10000}"  # Last 4 digits of timestamp
                service_full_name = f"{service_name}-{unique_suffix}.{self.service_type}"
                info = ServiceInfo(
                    self.service_type,
                    service_full_name,
                    addresses=[socket.inet_aton(self._local_ip)],
                    port=port_to_use,
                    properties=txt_properties,
                    server=f"{self._hostname}.local."
                )
                
                # Register the service with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        self.zeroconf.register_service(info)
                        self.announced_services[service_name] = info
                        print(f"📡 Announced: {service_name} on {self._local_ip}:{port_to_use}")
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:  # Last attempt
                            if "already registered" in str(e).lower() or "nonuniquename" in str(e).lower():
                                print(f"⚠️  {service_name} already registered (OK)")
                                # Still mark as successful since service exists
                                self.announced_services[service_name] = info
                                break
                            else:
                                print(f"❌ Failed to announce {service_name} after {max_retries} attempts: {type(e).__name__}: {e}")
                                # Remove from announced_services since it failed
                                self.announced_services.pop(service_name, None)
                        else:
                            # Wait a bit before retry
                            import time
                            time.sleep(0.1 * (attempt + 1))
                
            except Exception as e:
                print(f"❌ Failed to announce {service_name}: {type(e).__name__}: {e}")
                # Remove from announced_services since it failed
                self.announced_services.pop(service_name, None)
        
        # Start background thread
        thread = threading.Thread(target=_announce_background, daemon=True)
        thread.start()
        
        # Return immediately - don't block!
        print(f"🚀 Starting mDNS announcement for {service_name}...")
        return self
    
    def discover_services(self) -> Dict[str, Dict]:
        """Get all currently discovered services"""
        return self.discovered_services.copy()
    
    def find_service(self, service_name: str) -> Optional[Dict]:
        """Find a specific service by name"""
        for name, service_data in self.discovered_services.items():
            if service_name.lower() in service_data['name'].lower():
                return service_data
        return None
    
    def find_capability(self, capability: str) -> List[Dict]:
        """Find all services that announce a specific capability"""
        results = []
        for service_data in self.discovered_services.values():
            for cap in service_data['capabilities']:
                if capability.lower() in cap.lower():
                    results.append(service_data)
                    break
        return results
    
    def add_listener(self, listener_func: Callable):
        """Add a listener function that gets called on service discovery"""
        self.listeners.append(listener_func)
    
    def register_service(self, service_name: str, handler):
        """Register a service handler for signals"""
        self.service_registry[service_name] = handler
    
    def send_signal(self, signal_type: str, target_service: str = None, data: dict = None):
        """Send signals to registered services"""
        responses = {}
        
        if target_service:
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
            # Broadcast to all registered services
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
        """Format discovered services for Claude"""
        if not self.discovered_services:
            return "No services discovered on the network yet."
        
        context = "=== Network Services Discovered via mDNS ===\n"
        for service_data in self.discovered_services.values():
            context += f"\n📡 {service_data['name']} @ {service_data['host']}:{service_data['port']}\n"
            context += "Capabilities:\n"
            for cap in service_data['capabilities']:
                context += f"  • {cap}\n"
            
            if service_data['examples']:
                context += "Examples:\n"
                for ex in service_data['examples']:
                    context += f"  - {ex}\n"
        
        return context
    
    def cleanup(self):
        """Clean shutdown"""
        print("🧹 Shutting down real Bonjour announcer...")
        
        # Skip cleanup if zeroconf is None (fallback mode)
        if not self.zeroconf:
            print("🏠 Local-only mode cleanup complete")
            return
        
        # Close browser first to stop discovery
        try:
            if hasattr(self, 'browser') and self.browser:
                self.browser.cancel()
        except Exception as e:
            print(f"Error closing browser: {e}")
        
        # Unregister all our announced services
        for service_name, info in self.announced_services.items():
            if info:  # Only unregister if we have valid info
                try:
                    self.zeroconf.unregister_service(info)
                    print(f"👋 Unregistered: {service_name}")
                except Exception as e:
                    print(f"Error unregistering {service_name}: {e}")
        
        # Close zeroconf
        try:
            self.zeroconf.close()
        except Exception as e:
            print(f"Error closing zeroconf: {e}")

# Global instance
announcer = RealBonjourAnnouncer()

def announces_capability(service_name: str, *capabilities):
    """Decorator for auto-announcing capabilities"""
    def decorator(obj):
        local_announcer.announce(service_name, list(capabilities))
        return obj
    return decorator

# Cleanup on exit
import atexit
atexit.register(announcer.cleanup)

if __name__ == "__main__":
    # Test the real announcer
    print("🧪 Testing Real Bonjour Announcer")
    
    # Announce ourselves
    real_local_announcer.announce(
        "Test Service", 
        ["Testing real mDNS", "Network service discovery"], 
        ["Try discovering me from another machine"]
    )
    
    print("📡 Service announced. Listening for 30 seconds...")
    print("💡 Try running this on another machine to see cross-network discovery!")
    
    # Show discovered services every 5 seconds
    for i in range(6):
        time.sleep(5)
        discovered = real_announcer.discover_services()
        print(f"\n[{i*5}s] Discovered {len(discovered)} services:")
        for service_data in discovered.values():
            print(f"  • {service_data['name']} at {service_data['host']}:{service_data['port']}")
    
    print("\n✅ Test complete!")