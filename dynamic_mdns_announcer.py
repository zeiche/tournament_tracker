#!/usr/bin/env python3
"""
Dynamic mDNS announcer for zilogo.com subdomains
Uses zeroconf to announce services that can be discovered locally
"""

import time
import socket
import subprocess
from zeroconf import ServiceInfo, Zeroconf
from typing import Dict, Set

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "10.0.0.1"

def discover_active_services() -> Set[str]:
    """Discover all active bonjour services dynamically"""
    services = set()

    try:
        # Run service discovery
        result = subprocess.run(['./go.py', '--service-status'],
                              capture_output=True, text=True, timeout=10)

        # Service mappings for subdomains
        service_mappings = {
            'WebEditor': 'tournaments',
            'Tournament': 'tournaments',
            'Player': 'players',
            'Discord': 'discord',
            'Database': 'database',
            'Tournament Models': 'analytics',
            'ProcessManagement': 'admin',
            'Validation': 'api',
            'Organization': 'orgs',
            'Dashboard': 'dashboard',
            'mDNS': 'dns',
            'Bonjour': 'bonjour'
        }

        for line in result.stdout.split('\n'):
            if '🔍 Discovered:' in line or '🚀 Starting mDNS announcement' in line:
                service_name = line.split(':')[-1].strip() if '🚀' in line else line.split('🔍 Discovered: ')[1].split(' at ')[0].strip()

                # Find matching subdomain
                for key, subdomain in service_mappings.items():
                    if key in service_name:
                        services.add(subdomain)
                        break

        # Always include these core services
        services.update(['bonjour', 'tournaments', 'players'])

    except Exception as e:
        print(f"Error discovering services: {e}")
        # Fallback to core services
        services = {'bonjour', 'tournaments', 'players', 'admin', 'api', 'database'}

    return services

class DynamicMDNSAnnouncer:
    def __init__(self):
        self.zeroconf = Zeroconf()
        self.announced_services = {}
        self.local_ip = get_local_ip()

    def announce_service(self, subdomain: str):
        """Announce a zilogo.com subdomain via mDNS"""
        try:
            service_name = f"{subdomain}.zilogo.com"
            service_type = "_https._tcp.local."

            # Create service info
            info = ServiceInfo(
                service_type,
                f"{service_name}.{service_type}",
                addresses=[socket.inet_aton(self.local_ip)],
                port=443,
                properties={
                    'subdomain': subdomain,
                    'domain': 'zilogo.com',
                    'ssl': 'true'
                }
            )

            # Register the service
            self.zeroconf.register_service(info)
            self.announced_services[subdomain] = info

            print(f"📡 Announced: {service_name} -> {self.local_ip}:443")

        except Exception as e:
            print(f"Error announcing {subdomain}: {e}")

    def remove_service(self, subdomain: str):
        """Remove a service announcement"""
        if subdomain in self.announced_services:
            try:
                self.zeroconf.unregister_service(self.announced_services[subdomain])
                del self.announced_services[subdomain]
                print(f"🗑️ Removed: {subdomain}.zilogo.com")
            except Exception as e:
                print(f"Error removing {subdomain}: {e}")

    def update_services(self):
        """Update announced services based on what's active"""
        active_services = discover_active_services()
        currently_announced = set(self.announced_services.keys())

        # Announce new services
        for service in active_services:
            if service not in currently_announced:
                self.announce_service(service)

        # Remove inactive services
        for service in currently_announced:
            if service not in active_services:
                self.remove_service(service)

        print(f"🔍 Active: {active_services}")

    def start_monitoring(self):
        """Start monitoring and announcing services"""
        print(f"🌐 Starting dynamic mDNS announcer on {self.local_ip}")

        try:
            while True:
                self.update_services()
                time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\n🛑 Stopping mDNS announcer")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up all announced services"""
        for subdomain in list(self.announced_services.keys()):
            self.remove_service(subdomain)
        self.zeroconf.close()

def main():
    announcer = DynamicMDNSAnnouncer()
    announcer.start_monitoring()

if __name__ == "__main__":
    main()