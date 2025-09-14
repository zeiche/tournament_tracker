#!/usr/bin/env python3
"""
webdav_bonjour_switch.py - WebDAV Bonjour service switch for go.py integration
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.webdav_bonjour_switch")

from polymorphic_core import announcer, announces_capability
from utils.dynamic_switches import announce_switch
import time

@announces_capability("GoSwitch__webdav_bonjour")
class GoSwitchWebdavBonjour:
    """WebDAV Bonjour service switch for go.py"""
    
    def __init__(self):
        announcer.announce(
            "GoSwitch__webdav_bonjour",
            [
                "WebDAV Bonjour Service - Pure service-oriented architecture",
                "Uses ONLY Bonjour-discovered services",
                "No filesystem access - pure service calls",
                "3-method pattern: ask/tell/do for all operations", 
                "RESTful WebDAV interface",
                "Compatible with WebDAV clients",
                "Dynamic service discovery via mDNS"
            ],
            examples=[
                "./go.py --webdav-bonjour              # Start on default port 8088",
                "./go.py --webdav-bonjour 8090         # Start on specific port", 
                "curl http://localhost:8088/data/players  # Get player data",
                "curl -X PROPFIND http://localhost:8088/services  # Discover services"
            ]
        )

def webdav_bonjour_handler(args, remaining_args=None):
    """Handle WebDAV Bonjour service startup"""

    # Default port
    port = 8088

    # Parse port from args
    if hasattr(args, 'webdav_bonjour') and args.webdav_bonjour:
        try:
            port = int(args.webdav_bonjour)
        except (ValueError, TypeError):
            pass

    print(f"🌐 Starting WebDAV Bonjour Service on port {port}")
    print("=" * 50)

    # FIRST: Kill any existing WebDAV processes using ProcessManager
    from polymorphic_core.process import ProcessManager

    print("🧹 Cleaning up existing WebDAV processes...")
    killed = ProcessManager.kill_pattern("webdav", force=False)
    killed += ProcessManager.kill_pattern("start_fresh_webdav", force=False)
    killed += ProcessManager.kill_port(port, force=False)

    if killed > 0:
        print(f"🧹 Killed {killed} existing processes")
        import time
        time.sleep(2)  # Give processes time to die and release ports

    # Import here to avoid circular dependencies
    from services.webdav_bonjour_service import BonjourWebDAVService
    
    # Create and start service
    service = BonjourWebDAVService(port=port)
    
    if service.start():
        print(f"✅ WebDAV Bonjour service started")
        print(f"🌐 Access: http://localhost:{port}")
        print(f"📋 Endpoints:")
        print(f"   GET /data/players - Player rankings")
        print(f"   GET /data/stats - Database statistics")
        print(f"   PROPFIND /services - Discover services")
        print(f"   PROPFIND /data - Discover data types")
        
        announcer.announce(
            "WebDAV Bonjour Service Active",
            [f"Running on port {port}"],
            [f"http://localhost:{port}"]
        )
        
        try:
            print("\nPress Ctrl+C to stop the service")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down WebDAV service...")
            service.stop()
            return True
    else:
        print("❌ Failed to start WebDAV Bonjour service")
        return False

# Create switch instance
webdav_bonjour_switch = GoSwitchWebdavBonjour()

# Register with dynamic switches
announce_switch(
    flag="--webdav-bonjour",
    help="Start WebDAV service using Bonjour discovery [port]",
    handler=webdav_bonjour_handler,
    action='store',
    nargs='?',
    const='8088',
    default=None
)