#!/usr/bin/env python3
"""
bonjour_service.py - Unified Bonjour Service (Consolidates discovery switches)

This module consolidates all Bonjour/mDNS functionality into a single --bonjour switch
with subcommands for different discovery operations.
"""

import sys
import os
import subprocess
from typing import Optional, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.simple_logger import info, warning, error
from polymorphic_core import announcer
from dynamic_switches import announce_switch


class BonjourService:
    """Unified service for all Bonjour/mDNS operations"""
    
    def show_advertisements(self):
        """Show current bonjour advertisements (non-blocking)"""
        try:
            info("Showing current mDNS advertisements...")
            subprocess.run([sys.executable, 'show_advertisements.py'])
        except Exception as e:
            error(f"Advertisement display failed: {e}")
    
    def start_monitor(self):
        """Start Bonjour announcement monitor"""
        try:
            info("Starting Bonjour monitor...")
            subprocess.Popen([sys.executable, 'utils/bonjour_monitor.py', 'live'])
        except Exception as e:
            error(f"Bonjour monitor failed: {e}")
    
    def start_discovery(self):
        """Start dynamic command discovery"""
        try:
            info("Starting discovery service...")
            subprocess.run([sys.executable, 'utils/bonjour_discovery_service.py'])
        except Exception as e:
            error(f"Discovery service failed: {e}")
    
    def start_server(self, ports: List[str] = None):
        """Start Bonjour Universal Server"""
        try:
            info("Starting Bonjour Universal Server...")
            if ports:
                subprocess.Popen([sys.executable, 'bonjour_universal_server.py'] + ports)
            else:
                subprocess.Popen([sys.executable, 'bonjour_universal_server.py'])
        except Exception as e:
            error(f"Bonjour server failed: {e}")
    
    def start_lightweight(self):
        """Start lightweight pattern intelligence (no LLM)"""
        try:
            info("Starting lightweight pattern intelligence...")
            subprocess.call([sys.executable, '-u', 'lightweight_bonjour.py'])
        except Exception as e:
            error(f"Lightweight service failed: {e}")


# Announce service capabilities
announcer.announce(
    "Unified Bonjour Service",
    [
        "Consolidated mDNS discovery operations",
        "Supports: ads, monitor, discover, server, lightweight",
        "Single --bonjour switch with subcommands"
    ],
    [
        "bonjour.show_advertisements()",
        "bonjour.start_monitor()",
        "bonjour.start_discovery()"
    ]
)

# Singleton instance
bonjour_service = BonjourService()


def start_bonjour_service(args=None):
    """Handler for --bonjour switch with subcommands"""
    
    # Determine operation from arguments
    operation = "ads"  # default to show advertisements
    
    if hasattr(args, 'bonjour') and args.bonjour:
        operation = args.bonjour
    
    info(f"Starting Bonjour operation: {operation}")
    
    try:
        if operation == "ads" or operation == "advertisements":
            bonjour_service.show_advertisements()
        elif operation == "monitor":
            bonjour_service.start_monitor()
        elif operation == "discover" or operation == "discovery":
            bonjour_service.start_discovery()
        elif operation == "server":
            bonjour_service.start_server()
        elif operation == "lightweight":
            bonjour_service.start_lightweight()
        else:
            warning(f"Unknown Bonjour operation: {operation}. Using ads.")
            bonjour_service.show_advertisements()
            
    except Exception as e:
        error(f"Bonjour operation failed: {e}")
        return None


announce_switch(
    flag="--bonjour",
    help="START Bonjour/mDNS operations (ads|monitor|discover|server|lightweight)",
    handler=start_bonjour_service,
    action="store",
    nargs="?",
    const="ads",  # Default when no argument provided
    metavar="CMD"
)