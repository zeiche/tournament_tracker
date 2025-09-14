#!/usr/bin/env python3
"""
Service Management Utility - Wrapper for process identity system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.service_management")

from polymorphic_core.service_identity import ProcessKiller, ServiceManager
from utils.dynamic_switches import announce_switch


def restart_services_handler(args=None):
    """Handler for --restart-services switch"""
    print("🔄 Restarting all services...")
    return ServiceManager.restart_all()


def service_status_handler(args=None):
    """Handler for --service-status switch with optional auto-restart"""
    # Check if args is a string and contains 'auto-restart' or 'watchdog'
    if isinstance(args, str) and ('auto-restart' in args.lower() or 'watchdog' in args.lower()):
        return ServiceManager.watchdog()
    # Check if args is an object with auto_restart attribute
    elif hasattr(args, 'auto_restart') and args.auto_restart:
        return ServiceManager.watchdog()
    else:
        ServiceManager.status()
        return 0


def kill_service_handler(service_name):
    """Kill a specific service by name"""
    success = ProcessKiller.kill_service(service_name)
    return 0 if success else 1


# Announce switches for go.py
announce_switch(
    flag="--restart-services",
    help="Kill all managed services (use go.py commands to restart them)",
    handler=restart_services_handler
)

announce_switch(
    flag="--service-status",
    help="Show status of all managed services (use 'watchdog' for auto-restart)",
    handler=service_status_handler
)

# Command line interface when run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Service Management Tool")
    parser.add_argument("--restart-services", action="store_true", help="Kill all services")
    parser.add_argument("--service-status", action="store_true", help="Show service status")
    parser.add_argument("--auto-restart", action="store_true", help="Auto-restart failed services when used with --service-status")
    parser.add_argument("--kill", help="Kill specific service by name")
    parser.add_argument("--list", action="store_true", help="List all services")
    
    args = parser.parse_args()
    
    if args.restart_services:
        sys.exit(restart_services_handler())
    elif args.service_status:
        sys.exit(service_status_handler(args)) 
    elif args.kill:
        sys.exit(kill_service_handler(args.kill))
    elif args.list:
        services = ProcessKiller.list_services()
        for service in services:
            print(f"{service['service_name']}: {service['status']} (PID {service['pid']})")
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)