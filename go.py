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
import traceback

# Mark this as authorized go.py execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from polymorphic_core.execution_guard import mark_go_py_execution
mark_go_py_execution()
import time

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Log all unhandled exceptions globally - TURBOCHARGE development debugging!"""
    if exc_type is KeyboardInterrupt:
        print("🛑 Interrupted by user (Ctrl+C)")
        return  # Don't log Ctrl+C as errors

    # Format the full traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_str = ''.join(tb_lines)

    # Log to console immediately
    print(f"\n🚨 FATAL ERROR: Unhandled {exc_type.__name__}: {exc_value}")
    print(f"📍 Full traceback:\n{tb_str}")

    # Also try to log via the logging system if available
    try:
        from logging_services.polymorphic_log_manager import PolymorphicLogManager
        log_manager = PolymorphicLogManager()
        log_manager.do(f"log error FATAL: Unhandled {exc_type.__name__}: {exc_value}")
        log_manager.do(f"log error Full traceback:\n{tb_str}")
    except:
        pass  # Logging system might not be available

    # Log to database via PolymorphicLogManager for persistence
    try:
        log_manager.do(f"log error 🚨 FATAL ERROR: {exc_type.__name__}: {exc_value}")
        log_manager.do(f"log error 📍 Traceback:\n{tb_str}")
    except:
        pass

# Install global exception handler - this will catch ALL unhandled exceptions!
sys.excepthook = global_exception_handler
print("🔧 Global exception handler installed - all crashes will be logged!")

# Set authorization for go_py_guard (this is ALL we set)
os.environ['GO_PY_AUTHORIZED'] = '1'

# Load .env files for services (check home directory first, then parent, then local)
home_env = os.path.expanduser('~/.env')
parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
local_env = os.path.join(os.path.dirname(__file__), '.env')

for env_file in [home_env, parent_env, local_env]:
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already set (parent takes precedence)
                    if key.strip() not in os.environ or not os.environ[key.strip()]:
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")

def show_ram_tree_help():
    """Ask the live RAM tree objects directly for their switches"""
    try:
        import argparse

        # Import the live bonjour announcer - modules are already loaded in RAM
        from polymorphic_core.local_bonjour import local_announcer

        # Get the live services from RAM (no file I/O)
        services = local_announcer.services

        # Filter for switch services and ask each object what it provides
        switch_services = {name: info for name, info in services.items()
                          if name.startswith('GoSwitch')}

        if not switch_services:
            return False

        parser = argparse.ArgumentParser(description='Service STARTER')
        added_switches = set()

        for service_name, info in switch_services.items():
            # Clean up switch name: GoSwitch__test_logs -> --test-logs
            switch_name = service_name.replace('GoSwitch__', '--').replace('GoSwitch', '--').replace('_', '-').lower()

            # Skip duplicates
            if switch_name in added_switches:
                continue
            added_switches.add(switch_name)

            # Ask the object in RAM what help it provides
            capabilities = info.get('capabilities', [])
            help_text = "Unknown service"
            for cap in capabilities:
                if cap.startswith('Help: '):
                    help_text = cap[6:]  # Remove "Help: " prefix
                    break
                elif not cap.startswith('Provides go.py flag: '):
                    help_text = cap
                    break

            parser.add_argument(switch_name, help=help_text, nargs='?', default=None)

        parser.print_help()
        import sys
        sys.exit(0)

    except Exception as e:
        if os.environ.get('DEBUG_HELP'):
            print(f"RAM tree help failed: {e}")
        return False
    except SystemExit:
        # Re-raise SystemExit so it actually exits
        raise

def main():
    """Parse args and START services. That's ALL."""
    # Check for quiet operations FIRST, before any imports
    if '--help' in sys.argv or '-h' in sys.argv or '--service-status' in sys.argv:
        os.environ['QUIET_MODE'] = '1'

    # Fast path for help using live RAM tree (ask objects directly)
    if '--help' in sys.argv or '-h' in sys.argv:
        if show_ram_tree_help():
            return

    # Import discovery functions only when we actually need them
    from utils.dynamic_switches import discover_switches, handle_discovered_args

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