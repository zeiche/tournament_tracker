#!/usr/bin/env python3
"""
Avahi mDNS to DNS Bridge
Uses avahi-resolve to dynamically resolve .zilogo.com queries
"""

import subprocess
import socket
import threading
import time
from dnslib import DNSRecord, DNSHeader, RR, A, QTYPE
from dnslib.server import DNSServer, BaseResolver

class AvahiResolver(BaseResolver):
    """DNS resolver that uses Avahi for .zilogo.com domains"""

    def resolve(self, request, handler):
        """Resolve DNS queries using Avahi mDNS"""
        reply = request.reply()
        qname = str(request.q.qname).rstrip('.')
        qtype = request.q.qtype

        print(f"🔍 DNS query: {qname} ({QTYPE[qtype]})")

        # Handle .zilogo.com domains via mDNS
        if qname.endswith('.zilogo.com'):
            # Convert to .local for mDNS lookup
            local_name = qname.replace('.zilogo.com', '.local')

            try:
                # Use avahi-resolve to find the service
                result = subprocess.run([
                    'avahi-resolve', '-n', local_name
                ], capture_output=True, text=True, timeout=3)

                if result.returncode == 0:
                    # Parse result: "hostname.local	10.0.0.1"
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if '\t' in line:
                            hostname, ip = line.split('\t', 1)
                            if ip.strip():
                                print(f"✅ Resolved {qname} -> {ip.strip()}")
                                reply.add_answer(RR(qname, QTYPE.A, rdata=A(ip.strip())))
                                return reply

                # Try browsing for services if direct resolve failed
                result = subprocess.run([
                    'avahi-browse', '-t', '_http._tcp', '-r'
                ], capture_output=True, text=True, timeout=2)

                if result.returncode == 0:
                    # Look for matching service in browse output
                    for line in result.stdout.split('\n'):
                        if local_name.replace('.local', '') in line and '10.0.0.' in line:
                            parts = line.split()
                            for part in parts:
                                if part.startswith('10.0.0.'):
                                    print(f"✅ Found via browse: {qname} -> {part}")
                                    reply.add_answer(RR(qname, QTYPE.A, rdata=A(part)))
                                    return reply

                print(f"❌ No mDNS record found for {qname}")

            except Exception as e:
                print(f"❌ Avahi lookup failed for {qname}: {e}")

        # For non-.zilogo.com domains, return empty (will fall through to system DNS)
        return reply

def start_avahi_dns_bridge(port=5353):
    """Start Avahi DNS bridge server"""
    print(f"🌐 Starting Avahi DNS bridge on port {port}")
    print("📡 Will resolve *.zilogo.com via mDNS")

    resolver = AvahiResolver()
    server = DNSServer(resolver, port=port, address="10.0.0.1")

    try:
        server.start_thread()
        print(f"✅ DNS bridge running on 10.0.0.1:{port}")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("🛑 Stopping Avahi DNS bridge")
    finally:
        server.stop()

if __name__ == "__main__":
    start_avahi_dns_bridge()