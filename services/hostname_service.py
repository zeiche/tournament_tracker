#!/usr/bin/env python3
"""
hostname_service.py - mDNS hostname announcement service
Announces tournaments.zilogo.com hostname via the go.py mDNS system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core.execution_guard import require_go_py
require_go_py("services.hostname_service")

from polymorphic_core import announcer
import socket

class HostnameService:
    """Service that announces the hostname via mDNS for cross-network discovery"""

    def __init__(self):
        self.hostname = "tournaments"
        self.local_hostname = f"{self.hostname}.zilogo.com"

        # Get WireGuard IP
        self.wireguard_ip = self._get_wireguard_ip()

        # Announce hostname service with go.py flags AND create HTTPS server
        announcer.announce(
            "Hostname Service",
            [
                f"Announces {self.local_hostname} hostname via mDNS",
                f"Resolves to {self.wireguard_ip} on WireGuard network",
                "Enables zilogo.com hostname discovery for iPads and other devices",
                "Integrated with go.py process management",
                "GO_PY_FLAGS: --hostname-service"
            ],
            [
                f"ping {self.local_hostname}",
                f"http://{self.local_hostname}:8081/",
                f"Access from iPad via WireGuard tunnel"
            ],
            service_instance=self
        )

        print(f"🏠 Hostname service: {self.local_hostname} → {self.wireguard_ip}")

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
        return "10.0.0.1"  # fallback

    def ask(self, query: str) -> str:
        """Query hostname service"""
        query_lower = query.lower().strip()

        if "hostname" in query_lower or "name" in query_lower:
            return {
                "hostname": self.hostname,
                "fqdn": self.local_hostname,
                "ip": self.wireguard_ip,
                "status": "announced via mDNS"
            }
        elif "ip" in query_lower or "address" in query_lower:
            return self.wireguard_ip
        elif "status" in query_lower:
            return f"{self.local_hostname} announced on {self.wireguard_ip}"
        else:
            return f"Hostname: {self.local_hostname} → {self.wireguard_ip}"

    def tell(self, format_type: str, data=None) -> str:
        """Format hostname information"""
        info = data or self.ask("status")

        if format_type.lower() == "json":
            import json
            return json.dumps(info, indent=2)
        elif format_type.lower() == "discord":
            return f"🌐 **Hostname**: `{self.local_hostname}` → `{self.wireguard_ip}`"
        else:
            return str(info)

    def do(self, action: str) -> str:
        """Perform hostname service actions"""
        action_lower = action.lower().strip()

        if "announce" in action_lower or "broadcast" in action_lower:
            # Re-announce hostname WITH HTTPS server
            announcer.announce(
                f"Hostname-{self.hostname}",
                [f"Host {self.local_hostname} available at {self.wireguard_ip}"],
                [f"ping {self.local_hostname}"],
                service_instance=self
            )
            return f"Re-announced {self.local_hostname}"
        elif "test" in action_lower:
            return self._test_hostname()
        else:
            return f"Unknown action: {action}"

    def _test_hostname(self):
        """Test hostname resolution"""
        try:
            import subprocess
            result = subprocess.run(['ping', '-c', '1', self.local_hostname],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return f"✅ {self.local_hostname} resolves correctly"
            else:
                return f"❌ {self.local_hostname} resolution failed"
        except Exception as e:
            return f"❌ Test failed: {e}"

# Create service instance
hostname_service = HostnameService()

# Register switch for go.py
try:
    from polymorphic_core.local_bonjour import local_announcer
    local_announcer.announce(
        "GoSwitch__hostname",
        [
            "SWITCH: --hostname",
            "Starts hostname announcement service",
            "Announces tournaments.local via mDNS",
            "Enables .local domain discovery for iPads"
        ],
        ["./go.py --hostname"]
    )
except Exception as e:
    print(f"Could not register --hostname switch: {e}")

# Announce the hostname itself as a discoverable host WITH HTTPS
announcer.announce(
    "tournaments",
    [
        "Tournament tracker hostname",
        "Web interface on port 8081",
        "API access via WireGuard",
        "mDNS discoverable hostname"
    ],
    [
        "ping tournaments.local",
        "http://tournaments.local:8081/",
        "Access tournament data and web interface"
    ],
    service_instance=hostname_service
)

if __name__ == "__main__":
    print("🏠 Hostname Service Test")
    print(f"Hostname: {hostname_service.ask('hostname')}")
    print(f"Status: {hostname_service.do('test')}")