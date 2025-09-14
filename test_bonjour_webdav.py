#!/usr/bin/env python3
"""
Quick test of the /bonjour filesystem implementation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.webdav_database_browser import RootCollection
from polymorphic_core.local_bonjour import local_announcer

def test_bonjour_filesystem():
    """Test the /bonjour virtual filesystem"""
    print("Testing /bonjour virtual filesystem...")

    # Show current services in local announcer first
    services = local_announcer.list_services()
    print(f"Local announcer has {len(services)} services")
    for name in list(services.keys())[:10]:
        print(f"  - {name}")

    # Test that our root collection includes bonjour
    print("\nTesting root collection member names...")

    # Just check what the root collection would return
    try:
        # Create fake environ with provider
        class MockProvider:
            pass

        environ = {"wsgidav.provider": MockProvider()}
        root = RootCollection("/", environ)
        members = root.get_member_names()
        print(f"Root collection members: {members}")

        if "bonjour" in members:
            print("✅ /bonjour successfully added to root directory!")
        else:
            print("❌ /bonjour not found in root directory")

    except Exception as e:
        print(f"Error testing root collection: {e}")

    print("✅ Bonjour filesystem structure test complete!")

if __name__ == "__main__":
    test_bonjour_filesystem()