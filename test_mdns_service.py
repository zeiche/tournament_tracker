#!/usr/bin/env python3
"""Test service that advertises switches via mDNS"""

from zeroconf import ServiceInfo, Zeroconf
import socket
import time

def advertise_test_service():
    """Advertise a test service with switches"""
    try:
        # Create service info with switches in TXT record
        service_info = ServiceInfo(
            "_tournament._tcp.local.",
            "test-service._tournament._tcp.local.",
            addresses=[socket.inet_aton("127.0.0.1")],
            port=9999,
            properties={
                'switches': '--test,--example',
                'service': 'test-service',
                'description': 'Test service for mDNS discovery'
            }
        )

        # Register the service
        zeroconf = Zeroconf()
        zeroconf.register_service(service_info)
        print("📡 Test service advertised via mDNS: --test, --example switches")

        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            zeroconf.unregister_service(service_info)
            zeroconf.close()

    except Exception as e:
        print(f"Failed to advertise test service: {e}")

if __name__ == "__main__":
    advertise_test_service()