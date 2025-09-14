#!/usr/bin/env python3
"""
show_advertisements.py - Display current mDNS advertisements
Shows services discovered on the network via Bonjour/mDNS
"""

from polymorphic_core.real_bonjour import announcer
import time

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.show_advertisements")

def main():
    """Show current mDNS advertisements"""
    print("🔍 Current mDNS Service Advertisements")
    print("=" * 50)
    
    # Wait a moment for any discovery to complete
    time.sleep(1)
    
    # Get discovered services
    discovered = announcer.discover_services()
    
    if not discovered:
        print("No services discovered on the network.")
        print("\n💡 Services may take a few seconds to appear after startup.")
        return
    
    print(f"Found {len(discovered)} services:\n")
    
    for service_data in discovered.values():
        print(f"📡 {service_data['name']}")
        print(f"   Host: {service_data['host']}:{service_data['port']}")
        
        if service_data['capabilities']:
            print("   Capabilities:")
            for cap in service_data['capabilities']:
                if cap.strip():  # Skip empty capabilities
                    print(f"     • {cap}")
        
        if service_data['examples']:
            print("   Examples:")
            for ex in service_data['examples']:
                if ex.strip():  # Skip empty examples
                    print(f"     - {ex}")
        
        print()  # Empty line between services

if __name__ == "__main__":
    main()