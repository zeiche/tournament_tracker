#!/usr/bin/env python3
"""
mdns_dynamic_dns.py - Dynamic DNS based on mDNS announcements

This service listens to mDNS/Bonjour announcements and automatically creates
DNS entries for each service, mapping them to their announced ports.

For example, if a service announces as "Database Service" on port 39185,
it creates: database-service.tournaments.zilogo.com -> 10.0.0.1:39185

This solves the dynamic port mapping problem for iPad/VPN access.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core.execution_guard import require_go_py
require_go_py("services.mdns_dynamic_dns")

import socket
import time
import threading
import re
from typing import Dict, Set
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
from polymorphic_core import announcer

class MDNSDynamicDNS(ServiceListener):
    """
    Dynamic DNS service that listens to mDNS announcements and creates DNS entries.
    Each discovered service gets its own subdomain with the announced port.
    """

    def __init__(self):
        self.services = {}  # service_name -> {host, port, subdomain}
        self.dns_entries = set()  # Track what we've added to DNS

        # Initialize zeroconf browser
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, "_tournament._tcp.local.", self)

        # Announce ourselves
        announcer.announce(
            "mDNS Dynamic DNS Service",
            [
                "Automatically creates DNS entries for announced services",
                "Maps service-specific subdomains to dynamic ports",
                "Enables iPad access via predictable domain names",
                "Updates dnsmasq configuration dynamically"
            ],
            [
                "database-service.tournaments.zilogo.com -> 10.0.0.1:39185",
                "web-editor.tournaments.zilogo.com -> 10.0.0.1:8081",
                "Auto-discovers all mDNS announced services"
            ],
            service_instance=self
        )

        print("🌐 mDNS Dynamic DNS service started")
        print("📡 Listening for service announcements...")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a new service is discovered via mDNS"""
        try:
            info = zc.get_service_info(type_, name)
            if info and info.addresses:
                # Clean up service name for subdomain
                clean_name = self._clean_service_name(name.replace(f".{type_}", ""))

                # Get service details
                host = socket.inet_ntoa(info.addresses[0])
                port = info.port
                subdomain = f"{clean_name}.tournaments.zilogo.com"

                # Store service info
                self.services[name] = {
                    'host': host,
                    'port': port,
                    'subdomain': subdomain,
                    'clean_name': clean_name
                }

                # Add DNS entry
                self._add_dns_entry(subdomain, host)

                print(f"🔍 Discovered: {clean_name} -> {subdomain} ({host}:{port})")

        except Exception as e:
            print(f"⚠️  Error processing service {name}: {e}")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is removed"""
        if name in self.services:
            service = self.services[name]
            self._remove_dns_entry(service['subdomain'])
            del self.services[name]
            print(f"🗑️  Removed: {service['clean_name']} -> {service['subdomain']}")

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Called when a service is updated"""
        # For simplicity, treat as remove + add
        self.remove_service(zc, type_, name)
        self.add_service(zc, type_, name)

    def _clean_service_name(self, name: str) -> str:
        """Convert service name to DNS-safe subdomain"""
        # Remove service ID numbers (e.g., "Database Service-123" -> "Database Service")
        name = re.sub(r'-\d+$', '', name)

        # Convert to lowercase and replace spaces/special chars with hyphens
        clean = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower())
        clean = clean.strip('-')

        # Handle common service name patterns
        replacements = {
            'database-service': 'database',
            'web-editor-service': 'editor',
            'universal-web-editor-service': 'editor',
            'hostname-service': 'hostname',
            'tournament-model-service': 'tournaments',
            'player-model-service': 'players',
            'organization-model-service': 'organizations'
        }

        return replacements.get(clean, clean)

    def _add_dns_entry(self, subdomain: str, host: str):
        """Add DNS entry to dnsmasq configuration"""
        if subdomain in self.dns_entries:
            return  # Already added

        try:
            dns_line = f"address=/{subdomain}/{host}\n"

            # Append to dnsmasq config
            with open('/etc/dnsmasq.d/tournaments.conf', 'a') as f:
                f.write(dns_line)

            self.dns_entries.add(subdomain)

            # Restart dnsmasq to pick up new config
            os.system('sudo systemctl restart dnsmasq')

            print(f"📝 Added DNS: {subdomain} -> {host}")

        except Exception as e:
            print(f"⚠️  Failed to add DNS entry for {subdomain}: {e}")

    def _remove_dns_entry(self, subdomain: str):
        """Remove DNS entry from dnsmasq configuration"""
        if subdomain not in self.dns_entries:
            return  # Not in our tracking

        try:
            # Read current config
            with open('/etc/dnsmasq.d/tournaments.conf', 'r') as f:
                lines = f.readlines()

            # Filter out the line for this subdomain
            new_lines = [line for line in lines if f"/{subdomain}/" not in line]

            # Write back filtered config
            with open('/etc/dnsmasq.d/tournaments.conf', 'w') as f:
                f.writelines(new_lines)

            self.dns_entries.remove(subdomain)

            # Restart dnsmasq
            os.system('sudo systemctl restart dnsmasq')

            print(f"🗑️  Removed DNS: {subdomain}")

        except Exception as e:
            print(f"⚠️  Failed to remove DNS entry for {subdomain}: {e}")

    def ask(self, query: str) -> dict:
        """Query discovered services and DNS mappings"""
        query_lower = query.lower().strip()

        if query_lower in ['services', 'discovered', 'list']:
            return {
                'services': len(self.services),
                'dns_entries': len(self.dns_entries),
                'mappings': {name: info['subdomain'] for name, info in self.services.items()}
            }
        elif query_lower in ['dns', 'entries']:
            return list(self.dns_entries)
        elif 'stats' in query_lower:
            return {
                'total_services': len(self.services),
                'dns_entries': len(self.dns_entries),
                'active_mappings': len([s for s in self.services.values() if s['subdomain'] in self.dns_entries])
            }
        else:
            return self.services

    def tell(self, format_type: str, data=None) -> str:
        """Format service discovery information"""
        services = data or self.services

        if format_type.lower() == 'json':
            import json
            return json.dumps(services, indent=2)
        elif format_type.lower() == 'text':
            lines = [f"mDNS Dynamic DNS ({len(services)} services):"]
            for name, info in services.items():
                lines.append(f"  {info['clean_name']}: {info['subdomain']} -> {info['host']}:{info['port']}")
            return '\n'.join(lines)
        elif format_type.lower() == 'dns':
            lines = ["DNS Entries:"]
            for subdomain in sorted(self.dns_entries):
                lines.append(f"  {subdomain}")
            return '\n'.join(lines)
        else:
            return str(services)

    def do(self, action: str) -> str:
        """Perform DNS management actions"""
        action_lower = action.lower().strip()

        if 'refresh' in action_lower or 'rescan' in action_lower:
            # Clear and re-scan all services
            old_count = len(self.services)
            self.services.clear()
            # The browser will automatically re-discover services
            return f"Refreshed service discovery (was {old_count} services)"
        elif 'cleanup' in action_lower:
            # Remove DNS entries for services that are no longer active
            removed = 0
            for subdomain in list(self.dns_entries):
                if not any(info['subdomain'] == subdomain for info in self.services.values()):
                    self._remove_dns_entry(subdomain)
                    removed += 1
            return f"Cleaned up {removed} stale DNS entries"
        else:
            return f"Unknown action: {action}"

    def cleanup(self):
        """Clean shutdown"""
        try:
            if self.browser:
                self.browser.cancel()
            if self.zeroconf:
                self.zeroconf.close()
            print("🛑 mDNS Dynamic DNS service stopped")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

# Create service instance
mdns_dns = MDNSDynamicDNS()

if __name__ == "__main__":
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping mDNS Dynamic DNS...")
        mdns_dns.cleanup()