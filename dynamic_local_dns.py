#!/usr/bin/env python3
"""
Dynamic local DNS server for zilogo.com subdomains
Automatically responds to DNS queries based on active services
"""

import socket
import struct
import threading
import time
import subprocess
from typing import Dict, List, Set

class DynamicDNSServer:
    def __init__(self, ip="10.0.0.1", port=53):
        self.ip = ip
        self.port = port
        self.active_services = set()
        self.server_ip = ip

    def discover_active_services(self) -> Set[str]:
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
            services.update(['bonjour', 'tournaments', 'players', 'admin'])

        except Exception as e:
            print(f"Error discovering services: {e}")
            # Fallback to core services
            services = {'bonjour', 'tournaments', 'players', 'admin', 'api', 'database'}

        return services

    def build_dns_response(self, query_data, query_name):
        """Build DNS response packet"""
        # Parse the query
        transaction_id = query_data[:2]
        flags = b'\x81\x80'  # Response, no error
        questions = b'\x00\x01'  # 1 question
        answers = b'\x00\x01'   # 1 answer
        authority = b'\x00\x00'  # 0 authority records
        additional = b'\x00\x00'  # 0 additional records

        # Query section (echo back)
        query_section = query_data[12:]  # Skip header

        # Answer section
        name_pointer = b'\xc0\x0c'  # Pointer to name in question
        record_type = b'\x00\x01'   # A record
        record_class = b'\x00\x01'  # IN class
        ttl = b'\x00\x00\x00\x3c'   # 60 seconds TTL
        data_length = b'\x00\x04'   # 4 bytes for IPv4
        ip_bytes = socket.inet_aton(self.server_ip)

        answer_section = name_pointer + record_type + record_class + ttl + data_length + ip_bytes

        return transaction_id + flags + questions + answers + authority + additional + query_section + answer_section

    def parse_dns_query(self, data):
        """Parse DNS query to extract domain name"""
        try:
            # Skip header (12 bytes)
            i = 12
            domain_parts = []

            while i < len(data):
                length = data[i]
                if length == 0:
                    break
                i += 1
                domain_parts.append(data[i:i+length].decode('utf-8'))
                i += length

            return '.'.join(domain_parts)
        except:
            return ""

    def handle_dns_query(self, data, addr, sock):
        """Handle incoming DNS query"""
        try:
            domain = self.parse_dns_query(data)
            print(f"📡 DNS query for: {domain}")

            # Check if it's a zilogo.com subdomain we should handle
            if domain.endswith('.zilogo.com'):
                subdomain = domain.replace('.zilogo.com', '')

                # Update active services
                self.active_services = self.discover_active_services()

                if subdomain in self.active_services:
                    print(f"✅ Responding to {domain} -> {self.server_ip}")
                    response = self.build_dns_response(data, domain)
                    sock.sendto(response, addr)
                else:
                    print(f"❌ Service {subdomain} not active, no response")
            else:
                print(f"🔄 Non-zilogo.com query: {domain}")

        except Exception as e:
            print(f"Error handling DNS query: {e}")

    def start_server(self):
        """Start the DNS server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.ip, self.port))

        print(f"🌐 Dynamic DNS server started on {self.ip}:{self.port}")
        print(f"📡 Handling *.zilogo.com queries")

        # Initial service discovery
        self.active_services = self.discover_active_services()
        print(f"🔍 Active services: {self.active_services}")

        # Start service monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
        monitor_thread.start()

        try:
            while True:
                data, addr = sock.recvfrom(512)
                # Handle each query in a separate thread
                query_thread = threading.Thread(
                    target=self.handle_dns_query,
                    args=(data, addr, sock),
                    daemon=True
                )
                query_thread.start()

        except KeyboardInterrupt:
            print("\n🛑 Stopping DNS server")
        finally:
            sock.close()

    def monitor_services(self):
        """Monitor services and update active list"""
        while True:
            try:
                new_services = self.discover_active_services()
                if new_services != self.active_services:
                    print(f"📋 Service update: {new_services}")
                    self.active_services = new_services

                time.sleep(30)  # Check every 30 seconds

            except Exception as e:
                print(f"Error monitoring services: {e}")
                time.sleep(10)

def main():
    # Create and start DNS server
    dns_server = DynamicDNSServer(ip="10.0.0.1", port=53)
    dns_server.start_server()

if __name__ == "__main__":
    main()