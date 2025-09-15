#!/usr/bin/env python3
"""
Simple dynamic nginx config generator
Discovers bonjour services and maps subdomains to ports
"""

import subprocess
import time

def get_bonjour_services():
    """Get active bonjour services and their ports"""
    services = {}
    try:
        # Run service discovery to get actual current ports
        result = subprocess.run(['./go.py', '--service-status'],
                              capture_output=True, text=True, timeout=10)

        # Service mappings for subdomains - look for these patterns
        service_mappings = {
            'ProcessManagementGuide': 'admin',
            'NextService_WebEditor': 'tournaments',
            'Player Model Service': 'players',
            'NextService_Discord': 'discord',
            'Database Service': 'database',
            'Tournament Models (Enhanced OOP)': 'analytics',
            'ValidationCommands': 'api',
            'Organization Model Service': 'orgs',
            'Tournament Management Dashboard': 'dashboard',
            'mDNS Dynamic DNS Service': 'dns',
            'Bonjour Service Discovery Web Interface': 'bonjour'
        }

        # Parse discovered services to get actual ports
        for line in result.stdout.split('\n'):
            if '🔍 Discovered:' in line and ' at 10.0.0.1:' in line:
                # Extract service name and port
                parts = line.split('🔍 Discovered: ')[1].split(' at 10.0.0.1:')
                service_name = parts[0].strip()
                port = parts[1].strip()

                # Find matching subdomain
                for key, subdomain in service_mappings.items():
                    if key in service_name:
                        services[subdomain] = port
                        break

        print(f"Discovered dynamic services: {services}")

    except Exception as e:
        print(f"Error discovering services: {e}")
        # Fallback to empty - nginx will use default port
        services = {}

    return services

def generate_nginx_config(services):
    """Generate nginx config with dynamic port mappings"""

    config = """# Dynamic nginx config - Auto-generated
ssl_certificate /home/ubuntu/claude/tournament_tracker/services/wildcard_certificate.pem;
ssl_certificate_key /home/ubuntu/claude/tournament_tracker/services/wildcard_private.key;

server {
    listen 443 ssl;
    server_name ~^(?<subdomain>.+)\\.zilogo\\.com$;

    location / {
        set $backend_port 8000;

"""

    # Add dynamic port mappings
    for subdomain, port in services.items():
        config += f'        if ($subdomain = "{subdomain}") {{ set $backend_port {port}; }}\n'

    config += """
        proxy_pass https://10.0.0.1:$backend_port;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}"""

    return config

def update_nginx():
    """Update nginx config and reload"""
    services = get_bonjour_services()
    print(f"Found services: {services}")

    if services:
        config = generate_nginx_config(services)

        # Write config
        with open('/home/ubuntu/claude/tournament_tracker/nginx-zilogo.conf', 'w') as f:
            f.write(config)

        # Reload nginx
        subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'])
        print("✅ Nginx updated and reloaded")
    else:
        print("No services found")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        # Continuous monitoring
        while True:
            try:
                update_nginx()
                time.sleep(60)
            except KeyboardInterrupt:
                break
    else:
        # One-time update
        update_nginx()