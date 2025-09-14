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

from polymorphic_core.service_locator import get_service
from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch


class BonjourService:
    """Unified service for all Bonjour/mDNS operations"""

    def __init__(self):
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = get_service("logger", prefer_network=False)
        return self._logger

    def show_advertisements(self):
        """Show current bonjour advertisements (non-blocking)"""
        try:
            self.logger.info("Showing current mDNS advertisements...")
            subprocess.run([sys.executable, 'utils/show_advertisements.py'])
        except Exception as e:
            self.logger.error(f"Advertisement display failed: {e}")
    
    def start_monitor(self):
        """Start Bonjour announcement monitor with proper path"""
        try:
            self.logger.info("Starting Bonjour monitor...")
            monitor_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                      'utils', 'bonjour_monitor.py')
            subprocess.Popen([sys.executable, monitor_path, 'live'])
        except Exception as e:
            self.logger.error(f"Bonjour monitor failed: {e}")

    def start_discovery(self):
        """Start dynamic command discovery"""
        try:
            self.logger.info("Starting discovery service...")
            subprocess.run([sys.executable, 'utils/bonjour_discovery_service.py'])
        except Exception as e:
            self.logger.error(f"Discovery service failed: {e}")

    def start_server(self, ports: List[str] = None):
        """Start Bonjour Universal Server with proper path"""
        try:
            self.logger.info("Starting Bonjour Universal Server...")
            server_path = os.path.join(os.path.dirname(__file__), 'bonjour_universal_server.py')
            if ports:
                subprocess.Popen([sys.executable, server_path] + ports)
            else:
                subprocess.Popen([sys.executable, server_path])
        except Exception as e:
            self.logger.error(f"Bonjour server failed: {e}")

    def start_lightweight(self):
        """Start lightweight pattern intelligence (no LLM)"""
        try:
            self.logger.info("Starting lightweight pattern intelligence...")
            subprocess.call([sys.executable, '-u', 'lightweight_bonjour.py'])
        except Exception as e:
            self.logger.error(f"Lightweight service failed: {e}")


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

    bonjour_service.logger.info(f"Starting Bonjour operation: {operation}")

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
            bonjour_service.logger.warning(f"Unknown Bonjour operation: {operation}. Using ads.")
            bonjour_service.show_advertisements()

    except Exception as e:
        bonjour_service.logger.error(f"Bonjour operation failed: {e}")
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