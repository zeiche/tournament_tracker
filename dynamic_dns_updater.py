#!/usr/bin/env python3
"""
Dynamic DNS updater for zilogo.com subdomains
Automatically registers active services with DNS
"""

import subprocess
import time
import json
import requests
from typing import Dict, List

def get_public_ip() -> str:
    """Get the public IP of this server"""
    try:
        response = requests.get('https://api.ipify.org', timeout=10)
        return response.text.strip()
    except:
        try:
            response = requests.get('https://ifconfig.me', timeout=10)
            return response.text.strip()
        except:
            return "UNKNOWN"

def get_wireguard_ip() -> str:
    """Get the wireguard IP (10.0.0.1)"""
    return "10.0.0.1"

def discover_active_services() -> List[str]:
    """Discover all active bonjour services dynamically"""
    services = []

    try:
        # Get all bonjour service announcements
        bonjour_lines = get_bonjour_services()

        # Map all discovered services to subdomains
        service_mappings = {
            'WebEditor': 'tournaments',
            'Tournament': 'tournaments',
            'Player': 'players',
            'Discord': 'discord',
            'Database': 'database',
            'Tournament Models (Enhanced OOP)': 'analytics',
            'ProcessManagementGuide': 'admin',
            'ValidationCommands': 'api',
            'Organization': 'orgs',
            'Dashboard': 'dashboard',
            'mDNS Dynamic DNS': 'dns',
            'Bonjour': 'bonjour'
        }

        found_services = set()

        for line in bonjour_lines:
            if '🔍 Discovered:' in line:
                service_name = line.split('🔍 Discovered: ')[1].split(' at ')[0].strip()

                # Find matching subdomain
                for key, subdomain in service_mappings.items():
                    if key in service_name:
                        found_services.add(subdomain)
                        break

        services = list(found_services)
        print(f"🔍 Discovered services: {services}")

    except Exception as e:
        print(f"Error discovering services: {e}")

    return services

def get_bonjour_services() -> List[str]:
    """Get bonjour service announcements"""
    try:
        result = subprocess.run(['./go.py', '--service-status'],
                              capture_output=True, text=True, timeout=30)
        return result.stdout.split('\n')
    except:
        return []

def update_hosts_file(services: List[str], ip: str):
    """Update local /etc/hosts file"""
    hosts_entries = []
    for service in services:
        hosts_entries.append(f"{ip} {service}.zilogo.com")

    if not hosts_entries:
        return

    # Read current hosts file
    try:
        with open('/etc/hosts', 'r') as f:
            current_hosts = f.read()
    except:
        current_hosts = ""

    # Remove old zilogo.com entries
    lines = current_hosts.split('\n')
    filtered_lines = [line for line in lines if 'zilogo.com' not in line]

    # Add new entries
    filtered_lines.extend(hosts_entries)

    # Write back
    try:
        with open('/etc/hosts', 'w') as f:
            f.write('\n'.join(filtered_lines))
        print(f"✅ Updated /etc/hosts with: {', '.join(services)}")
    except Exception as e:
        print(f"❌ Failed to update /etc/hosts: {e}")

def update_cloudflare_dns(services: List[str], ip: str):
    """Update Cloudflare DNS (if configured)"""
    # This would need API tokens and zone info
    # For now, just announce what we would do
    print(f"🌐 Would update DNS for: {', '.join(f'{s}.zilogo.com' for s in services)} -> {ip}")

def announce_services(services: List[str], ip: str):
    """Announce services via bonjour"""
    try:
        # Create service announcements
        for service in services:
            subprocess.run([
                './go.py', '--bonjour', 'ads',
                f'{service}.zilogo.com', ip, '443'
            ], timeout=10)
    except Exception as e:
        print(f"Error announcing services: {e}")

def main():
    """Main dynamic DNS updater"""
    print("🔄 Starting dynamic DNS updater for zilogo.com subdomains...")

    public_ip = get_public_ip()
    wireguard_ip = get_wireguard_ip()

    print(f"📡 Public IP: {public_ip}")
    print(f"🔒 Wireguard IP: {wireguard_ip}")

    last_services = []

    while True:
        try:
            # Discover what's actually running
            current_services = discover_active_services()

            if current_services != last_services:
                print(f"📋 Active services: {current_services}")

                # Update local hosts file (for local testing)
                update_hosts_file(current_services, wireguard_ip)

                # Update public DNS (would need API setup)
                update_cloudflare_dns(current_services, public_ip)

                # Announce via bonjour
                announce_services(current_services, wireguard_ip)

                last_services = current_services

            time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\n🛑 Stopping dynamic DNS updater")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        # One-time update
        services = discover_active_services()
        ip = get_wireguard_ip()
        update_hosts_file(services, ip)
        print(f"Updated DNS for: {services}")
    else:
        # Continuous monitoring
        main()