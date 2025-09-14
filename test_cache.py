#!/usr/bin/env python3
"""Test the bonjour services cache system"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.execution_guard import mark_go_py_execution
mark_go_py_execution()

from polymorphic_core.local_bonjour import local_announcer
from utils.dynamic_switches import discover_switches

# Discover all switches to populate services
print("Discovering switches...")
parser = discover_switches()
print(f"Found {len(local_announcer.list_services())} services")

# Manually save cache
print("Saving cache...")
local_announcer.save_services_cache()

# Test loading cache
print("Testing cache load...")
if local_announcer.load_services_cache():
    print("✅ Cache loaded successfully")
    services = local_announcer.list_services()
    switch_services = [name for name in services.keys() if name.startswith('GoSwitch')]
    print(f"Switch services in cache: {switch_services[:5]}...")
else:
    print("❌ Cache load failed")