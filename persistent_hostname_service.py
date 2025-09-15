#!/usr/bin/env python3
"""
persistent_hostname_service.py - Persistent hostname announcement for mDNS
Continuously announces tournaments.local hostname for iPad discovery
"""

import time
import sys
import os
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core import announcer
from polymorphic_core.local_bonjour import local_announcer

class PersistentHostnameService:
    """Persistent service that continuously announces hostname via mDNS"""

    def __init__(self):
        self.running = True
        self.hostname = "tournaments"
        self.fqdn = f"{self.hostname}.zilogo.com"
        self.wireguard_ip = self._get_wireguard_ip()

        # Announce the service
        announcer.announce(
            "Persistent Hostname Service",
            [
                f"Continuously announces {self.fqdn} hostname",
                f"Makes {self.fqdn} discoverable on WireGuard network",
                "Enables iPad zilogo.com domain resolution",
                "Persistent service managed by go.py"
            ],
            [
                f"ping {self.fqdn}",
                f"http://{self.fqdn}:8081/",
                "iPad discovery via Bonjour/mDNS"
            ]
        )

        print(f"🏠 Persistent hostname service started: {self.fqdn} → {self.wireguard_ip}")

    def _get_wireguard_ip(self):
        """Get WireGuard interface IP"""
        try:
            import subprocess
            result = subprocess.run(['ip', 'addr', 'show', 'wg0'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'inet ' in line and '/24' in line:
                        return line.split()[1].split('/')[0]
        except:
            pass
        return "10.0.0.1"

    def run(self):
        """Main service loop"""
        # Announce hostname continuously
        while self.running:
            try:
                # Re-announce hostname for discovery
                announcer.announce(
                    f"hostname-{self.hostname}",
                    [
                        f"Host {self.fqdn} available at {self.wireguard_ip}",
                        "Tournament tracker hostname",
                        "Web interface and API access"
                    ],
                    [
                        f"ping {self.fqdn}",
                        f"http://{self.fqdn}:8081/"
                    ]
                )

                # Sleep for 30 seconds before re-announcing
                time.sleep(30)

            except KeyboardInterrupt:
                print("Stopping hostname service...")
                self.running = False
                break
            except Exception as e:
                print(f"Hostname service error: {e}")
                time.sleep(5)

    def stop(self):
        """Stop the service"""
        self.running = False

# Register the switch
local_announcer.announce(
    "GoSwitch__hostname",
    [
        "SWITCH: --hostname",
        "Starts persistent hostname announcement service",
        "Announces tournaments.local via mDNS continuously",
        "Enables .local domain discovery for iPads and other devices"
    ],
    ["./go.py --hostname"]
)

def main():
    """Main entry point"""
    service = PersistentHostnameService()

    try:
        service.run()
    except KeyboardInterrupt:
        print("\n🛑 Hostname service stopped")
    finally:
        service.stop()

if __name__ == "__main__":
    main()