#!/usr/bin/env python3
"""
process_service.py - Essential Process Management Service

This module provides the essential --restart-services and --service-status switches
for system management. These cannot be consolidated as they're core infrastructure.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.process_service")

from utils.simple_logger import info, warning, error
from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch


class ProcessService:
    """Essential process management operations"""
    
    def restart_services(self):
        """Restart services using integrated process managers"""
        info("Restarting services via integrated ProcessManagers")
        
        # Restart Discord using its process manager
        try:
            from networking.bonjour_discord import _discord_process_manager
            discord_pids = _discord_process_manager.start_services()
            info(f"Discord restarted with PIDs: {discord_pids}")
        except (ImportError, NameError) as e:
            warning(f"Discord ProcessManager not available, using fallback: {e}")
            from polymorphic_core.process import ProcessManager
            ProcessManager.kill_pattern('discord')
            ProcessManager.kill_pattern('polymorphic_discord')
            ProcessManager.start_service_safe('bonjour_discord.py', check_existing=False)
        
        # Restart Polymorphic Web Editor using its process manager
        try:
            from services.polymorphic_web_editor import _web_editor_process_manager
            web_pids = _web_editor_process_manager.start_services()
            info(f"Polymorphic Web Editor restarted with PIDs: {web_pids}")
        except (ImportError, NameError) as e:
            warning(f"Polymorphic Web Editor ProcessManager not available, using fallback: {e}")
            from polymorphic_core.process import ProcessManager
            ProcessManager.kill_pattern('web_editor')
            ProcessManager.kill_pattern('polymorphic_web_editor')
            ProcessManager.start_service_safe('services/polymorphic_web_editor.py', check_existing=False)
        
        info("Services restarted")
    
    def check_service_status(self):
        """Check status using bonjour signals"""
        info("Service Status (via Bonjour Signals)")
        
        try:
            sys.path.append('/home/ubuntu/claude/tournament_tracker')
            from polymorphic_core import announcer
            
            # Send status signal to all registered services
            info("Sending status signal to all services")
            responses = announcer.send_signal('status')
            
            if responses:
                print("\n=== Service Responses ===")
                for service_name, response in responses.items():
                    if isinstance(response, dict) and 'error' in response:
                        print(f"{service_name}: ERROR - {response['error']}")
                    else:
                        print(f"{service_name}: {response}")
            else:
                print("No services responded to status signal")
            
            # Also show registered services
            if announcer.service_registry:
                print(f"\n=== Registered Services ({len(announcer.service_registry)}) ===")
                for service_name in announcer.service_registry:
                    print(f"  • {service_name}")
            
            # Show announcements
            context = announcer.get_announcements_for_claude()
            if context and "No services" not in context:
                print("\n=== Service Announcements ===")
                print(context)
                
        except Exception as e:
            print(f"Error checking service status: {e}")
            # Fallback to ProcessManager process check
            print("\n=== Fallback: Process Check via ProcessManager ===")
            from polymorphic_core.process import ProcessManager
            processes = ProcessManager.list_tournament_processes()
            if processes:
                for pattern, pids in processes.items():
                    print(f"{pattern}: Running ({len(pids)} processes)")
            else:
                print("No tournament tracker processes found")


# Announce service capabilities
announcer.announce(
    "Essential Process Service",
    [
        "Core system management operations",
        "Restart services and check status",
        "Cannot be consolidated - essential infrastructure"
    ],
    [
        "process.restart_services()",
        "process.check_service_status()"
    ]
)

# Singleton instance
process_service = ProcessService()


def restart_services_handler(args=None):
    """Handler for --restart-services switch"""
    try:
        process_service.restart_services()
    except Exception as e:
        error(f"Service restart failed: {e}")


def service_status_handler(args=None):
    """Handler for --service-status switch"""
    try:
        process_service.check_service_status()
    except Exception as e:
        error(f"Status check failed: {e}")


# Announce both essential switches
announce_switch(
    flag="--restart-services",
    help="Kill and restart all services",
    handler=restart_services_handler
)

announce_switch(
    flag="--service-status", 
    help="Check service status via bonjour signals",
    handler=service_status_handler
)