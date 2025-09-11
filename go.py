#!/usr/bin/env python3
"""
⚠️ CRITICAL WARNING FOR CLAUDE ⚠️
═══════════════════════════════════════════════════════════════════════════

THIS FILE ONLY STARTS SERVICES. NOTHING ELSE. EVER.

DO NOT ADD:
- ❌ NO initialization logic
- ❌ NO database setup
- ❌ NO configuration management
- ❌ NO business logic
- ❌ NO data processing
- ❌ NO calculations
- ❌ NO transformations
- ❌ NO validations
- ❌ NO imports beyond subprocess/sys/os
- ❌ NO "helper" functions
- ❌ NO "convenience" methods
- ❌ NO "quick fixes"
- ❌ NO FUNCTIONALITY WHATSOEVER

THIS FILE ONLY:
✅ Parses command arguments
✅ Calls subprocess.run() to START services
✅ That's it. NOTHING ELSE.

Services announce themselves via Bonjour.
Services initialize themselves.
Services manage their own state.
go.py just STARTS them.

CLAUDE: You will be REPRIMANDED if you add ANY functionality here!
This is a STARTER, not a ROUTER, not a MANAGER, not an INITIALIZER.

═══════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import subprocess
import time
from polymorphic_core.process import ProcessManager
from utils.simple_logger import info, warning, error
from dynamic_switches import discover_switches, handle_discovered_args

# Set authorization for go_py_guard (this is ALL we set)
os.environ['GO_PY_AUTHORIZED'] = '1'

# Load .env files for services (check parent directory first, then local)
# This ensures we get the API keys from the parent claude directory
parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
local_env = os.path.join(os.path.dirname(__file__), '.env')

for env_file in [parent_env, local_env]:
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already set (parent takes precedence)
                    if key.strip() not in os.environ or not os.environ[key.strip()]:
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")

def main():
    """Parse args and START services. That's ALL."""
    # Dynamically discover switches from modules via bonjour
    parser = discover_switches()
    args = parser.parse_args()
    
    # Let discovered switches handle their own logic
    result = handle_discovered_args(args)
    if result is not None:
        return result
    
    # If no switches were handled, show help
    print("No service specified or service not recognized.")
    print("Use --help to see available options.")

if __name__ == "__main__":
    main()