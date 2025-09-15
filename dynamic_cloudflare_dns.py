#!/usr/bin/env python3
"""
Dynamic Cloudflare DNS updater for zilogo.com subdomains
Automatically registers/removes DNS records as services start/stop
"""

import requests
import json
import time
import subprocess
from typing import Dict, List, Optional

# Configuration - these would need to be set
CLOUDFLARE_API_TOKEN = "your_api_token_here"
ZONE_ID = "your_zone_id_here"
DOMAIN = "zilogo.com"

def get_public_ip() -> str:
    """Get the public IP of this server"""
    try:
        response = requests.get('https://api.ipify.org', timeout=10)
        return response.text.strip()
    except:
        return "127.0.0.1"  # fallback

def discover_active_services() -> List[str]:
    """Discover all active bonjour services dynamically"""
    services = []

    try:
        # Run service discovery
        result = subprocess.run(['./go.py', '--service-status'],
                              capture_output=True, text=True, timeout=30)

        # Service mappings for subdomains
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

        for line in result.stdout.split('\n'):
            if '🔍 Discovered:' in line:
                service_name = line.split('🔍 Discovered: ')[1].split(' at ')[0].strip()

                # Find matching subdomain
                for key, subdomain in service_mappings.items():
                    if key in service_name:
                        found_services.add(subdomain)
                        break

        services = list(found_services)
        print(f"🔍 Active services: {services}")

    except Exception as e:
        print(f"Error discovering services: {e}")

    return services

def get_cloudflare_records() -> List[Dict]:
    """Get current DNS records from Cloudflare"""
    if not CLOUDFLARE_API_TOKEN or CLOUDFLARE_API_TOKEN == "your_api_token_here":
        return []

    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(
            f'https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records',
            headers=headers
        )

        if response.status_code == 200:
            return response.json()['result']
        else:
            print(f"Error getting DNS records: {response.text}")
            return []

    except Exception as e:
        print(f"Error connecting to Cloudflare: {e}")
        return []

def create_dns_record(subdomain: str, ip: str) -> bool:
    """Create a new DNS A record"""
    if not CLOUDFLARE_API_TOKEN or CLOUDFLARE_API_TOKEN == "your_api_token_here":
        print(f"🌐 Would create DNS: {subdomain}.{DOMAIN} -> {ip}")
        return True

    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        'type': 'A',
        'name': f'{subdomain}.{DOMAIN}',
        'content': ip,
        'ttl': 120  # 2 minutes for quick updates
    }

    try:
        response = requests.post(
            f'https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            print(f"✅ Created DNS: {subdomain}.{DOMAIN} -> {ip}")
            return True
        else:
            print(f"❌ Failed to create DNS record: {response.text}")
            return False

    except Exception as e:
        print(f"Error creating DNS record: {e}")
        return False

def delete_dns_record(record_id: str, subdomain: str) -> bool:
    """Delete a DNS record"""
    if not CLOUDFLARE_API_TOKEN or CLOUDFLARE_API_TOKEN == "your_api_token_here":
        print(f"🌐 Would delete DNS: {subdomain}.{DOMAIN}")
        return True

    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.delete(
            f'https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}',
            headers=headers
        )

        if response.status_code == 200:
            print(f"🗑️ Deleted DNS: {subdomain}.{DOMAIN}")
            return True
        else:
            print(f"❌ Failed to delete DNS record: {response.text}")
            return False

    except Exception as e:
        print(f"Error deleting DNS record: {e}")
        return False

def sync_dns_records():
    """Sync DNS records with active services"""
    active_services = discover_active_services()
    current_records = get_cloudflare_records()
    public_ip = get_public_ip()

    # Get existing subdomain records
    existing_subdomains = {}
    for record in current_records:
        if record['name'].endswith(f'.{DOMAIN}') and record['type'] == 'A':
            subdomain = record['name'].replace(f'.{DOMAIN}', '')
            existing_subdomains[subdomain] = record['id']

    # Create new records for active services
    for service in active_services:
        if service not in existing_subdomains:
            create_dns_record(service, public_ip)
        else:
            print(f"📍 DNS exists: {service}.{DOMAIN}")

    # Remove records for inactive services (optional - might want to keep them)
    # for subdomain, record_id in existing_subdomains.items():
    #     if subdomain not in active_services:
    #         delete_dns_record(record_id, subdomain)

def monitor_services():
    """Continuously monitor and update DNS"""
    print("🔄 Starting dynamic Cloudflare DNS updater...")

    last_services = []

    while True:
        try:
            current_services = discover_active_services()

            # Only update if services changed
            if current_services != last_services:
                print(f"📡 Service changes detected!")
                sync_dns_records()
                last_services = current_services

            time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            print("\n🛑 Stopping DNS updater")
            break
        except Exception as e:
            print(f"❌ Error in monitor loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        monitor_services()
    else:
        # One-time sync
        sync_dns_records()