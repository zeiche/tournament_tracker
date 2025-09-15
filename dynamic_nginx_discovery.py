#!/usr/bin/env python3
"""
Dynamic nginx service discovery for tournament tracker
Maps subdomains to active bonjour services in real-time
"""

import json
import time
import subprocess
from typing import Dict, List, Optional

def discover_active_services() -> Dict[str, str]:
    """Discover active bonjour services and map to domains"""
    try:
        # Run bonjour discovery
        result = subprocess.run(['./go.py', '--service-status'],
                              capture_output=True, text=True, timeout=30)

        # Parse the output for service announcements
        services = {}
        lines = result.stdout.split('\n')

        # Find the latest/best service for each type
        tournament_services = []
        player_services = []
        bonjour_services = []

        for line in lines:
            if '🔍 Discovered:' in line:
                # Parse: "🔍 Discovered: Service Name at 10.0.0.1:port"
                parts = line.split(' at ')
                if len(parts) == 2:
                    service_name = parts[0].split('🔍 Discovered: ')[1].strip()
                    address_port = parts[1].strip()

                    # Collect all services by type
                    if 'WebEditor' in service_name or 'Tournament' in service_name:
                        tournament_services.append(address_port)
                    elif 'Player' in service_name:
                        player_services.append(address_port)
                    elif 'Bonjour' in service_name or 'Web Interface' in service_name:
                        bonjour_services.append(address_port)
                    elif 'Dashboard' in service_name:
                        tournament_services.append(address_port)

        # Use the first available service of each type
        if tournament_services:
            services['tournaments'] = tournament_services[0]
        if player_services:
            services['players'] = player_services[0]
        if bonjour_services:
            services['bonjour'] = bonjour_services[0]

        print(f"🔍 Found services: {services}")
        return services
    except Exception as e:
        print(f"Error discovering services: {e}")
        return {}

def generate_nginx_upstream_config(services: Dict[str, str]) -> str:
    """Generate nginx upstream configuration"""
    config = ""

    for subdomain, address_port in services.items():
        config += f"""
upstream {subdomain}_backend {{
    server {address_port};
}}
"""

    return config

def generate_nginx_server_config(services: Dict[str, str]) -> str:
    """Generate nginx server blocks with dynamic upstreams"""
    config = """
# SSL certificates for all *.zilogo.com sites
ssl_certificate /home/ubuntu/claude/tournament_tracker/services/wildcard_certificate.pem;
ssl_certificate_key /home/ubuntu/claude/tournament_tracker/services/wildcard_private.key;
"""

    # Add upstream blocks
    config += generate_nginx_upstream_config(services)

    # Add server blocks for each discovered service
    for subdomain, address_port in services.items():
        config += f"""
# {subdomain}.zilogo.com - Dynamic routing
server {{
    listen 443 ssl;
    server_name {subdomain}.zilogo.com;

    location / {{
        proxy_pass https://{subdomain}_backend;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

    # Default catch-all
    primary_service = list(services.keys())[0] if services else 'bonjour'
    config += f"""
# Default catch-all for any other *.zilogo.com
server {{
    listen 443 ssl default_server;
    server_name *.zilogo.com;

    return 301 https://{primary_service}.zilogo.com$request_uri;
}}
"""

    return config

def update_nginx_config():
    """Update nginx configuration with current services"""
    services = discover_active_services()

    if not services:
        print("No services discovered, keeping existing config")
        return False

    print(f"Discovered services: {services}")

    # Generate new config
    new_config = generate_nginx_server_config(services)

    # Write to nginx config file
    config_path = '/home/ubuntu/claude/tournament_tracker/nginx-zilogo.conf'
    with open(config_path, 'w') as f:
        f.write(f"# Dynamic nginx configuration - Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# Auto-discovered active bonjour services\n\n")
        f.write(new_config)

    # Test and reload nginx
    try:
        subprocess.run(['sudo', 'nginx', '-t'], check=True)
        subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'], check=True)
        print("✅ Nginx configuration updated and reloaded")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Nginx configuration error: {e}")
        return False

def monitor_services():
    """Continuously monitor and update nginx config"""
    print("🔄 Starting dynamic nginx service discovery...")

    last_services = {}

    while True:
        try:
            current_services = discover_active_services()

            # Only update if services changed
            if current_services != last_services:
                print(f"📡 Service changes detected: {current_services}")
                if update_nginx_config():
                    last_services = current_services

            time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\n🛑 Stopping dynamic discovery")
            break
        except Exception as e:
            print(f"❌ Error in monitor loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        monitor_services()
    else:
        # One-time update
        update_nginx_config()