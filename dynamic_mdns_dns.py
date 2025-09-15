#!/usr/bin/env python3
"""
Dynamic mDNS to DNS Bridge
Listens for mDNS announcements and dynamically updates DNS records
"""

import time
import subprocess
import tempfile
from zeroconf import ServiceBrowser, Zeroconf
import threading

class DynamicDNSUpdater:
    def __init__(self):
        self.discovered_services = {}
        self.dns_records = {}

    def remove_service(self, zeroconf, type, name):
        """Service removed from network"""
        if name in self.discovered_services:
            print(f"🚮 Service removed: {name}")
            del self.discovered_services[name]
            self.update_dns_records()

    def add_service(self, zeroconf, type, name):
        """New service discovered"""
        info = zeroconf.get_service_info(type, name)
        if info:
            addresses = [addr for addr in info.addresses]
            if addresses:
                ip = ".".join(str(b) for b in addresses[0])

                # Extract service name and create DNS mapping
                service_name = name.split('.')[0]
                hostname = f"{service_name}.zilogo.com"

                self.discovered_services[name] = {
                    'hostname': hostname,
                    'ip': ip,
                    'port': info.port
                }

                print(f"🔍 Discovered: {hostname} -> {ip}:{info.port}")
                self.update_dns_records()

    def update_service(self, zeroconf, type, name):
        """Service updated"""
        self.add_service(zeroconf, type, name)

    def update_dns_records(self):
        """Update system DNS records dynamically"""
        try:
            # Create new hosts entries
            new_records = []
            for service in self.discovered_services.values():
                new_records.append(f"{service['ip']} {service['hostname']}")

            if new_records:
                # Write to temporary hosts file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hosts') as f:
                    f.write("# Dynamic mDNS mappings\n")
                    for record in new_records:
                        f.write(f"{record}\n")
                    temp_file = f.name

                # Update systemd-resolved with new records
                for service in self.discovered_services.values():
                    try:
                        subprocess.run([
                            'sudo', 'systemd-resolve', '--interface=wg0',
                            '--set-dns=10.0.0.1',
                            f'--set-domain={service["hostname"]}'
                        ], check=False, capture_output=True)
                    except:
                        pass

                print(f"📝 Updated DNS with {len(new_records)} dynamic records")

        except Exception as e:
            print(f"❌ DNS update failed: {e}")

def start_dynamic_mdns():
    """Start dynamic mDNS to DNS bridge"""
    print("🌐 Starting dynamic mDNS->DNS bridge...")

    updater = DynamicDNSUpdater()
    zeroconf = Zeroconf()

    # Listen for HTTP services
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", updater)

    try:
        while True:
            time.sleep(5)
            # Periodically refresh
    except KeyboardInterrupt:
        print("🛑 Stopping dynamic mDNS bridge")
    finally:
        zeroconf.close()

if __name__ == "__main__":
    start_dynamic_mdns()