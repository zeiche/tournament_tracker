#!/usr/bin/env python3
"""
WebDAV Database Browser Switch (Refactored) - Go.py integration
Provides comprehensive WebDAV service with full process management
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.webdav_refactored_switch")

from polymorphic_core import announcer, announces_capability
from utils.dynamic_switches import announce_switch


@announces_capability("GoSwitch__webdav_refactored")
class GoSwitchWebdavRefactored:
    """
    Refactored WebDAV Database Browser switch for go.py
    Full-featured service with process management and 3-method pattern
    """
    
    def __init__(self):
        announcer.announce(
            "GoSwitch__webdav_refactored",
            [
                "WebDAV Database Browser (Refactored) - Production-ready service",
                "Full process management with BaseProcessManager",
                "3-method pattern: ask(), tell(), do() for all operations",
                "Service locator integration for dependencies",
                "Automatic port conflict resolution",
                "Health monitoring and recovery",
                "Virtual filesystem for database model intelligence",
                "Read-only access for data safety",
                "Compatible with any WebDAV client",
                "Self-managing with graceful shutdown"
            ],
            examples=[
                "./go.py --webdav-refactored              # Start with auto port selection",
                "./go.py --webdav-refactored port:8084    # Start on specific port",
                "./go.py --webdav-refactored status       # Check service status",
                "./go.py --webdav-refactored restart      # Restart service"
            ]
        )
    
    def get_argument_parser(self, parent_parser):
        """Add WebDAV refactored arguments to the parser"""
        parent_parser.add_argument(
            '--webdav-refactored',
            nargs='?',
            const='start',
            help='START WebDAV database browser (refactored) (start|status|restart|stop|port:8084)'
        )
        return parent_parser
    
    def handle_args(self, args, remaining_args=None):
        """Handle WebDAV refactored service arguments"""
        if hasattr(args, 'webdav_refactored') and args.webdav_refactored is not None:
            
            # Import service here to avoid circular dependencies
            from services.webdav_service_refactored import get_webdav_service
            
            action = args.webdav_refactored
            service = get_webdav_service()
            
            print(f"🗂️  WebDAV Database Browser (Refactored)")
            print("=" * 50)
            
            if action == 'start' or action.startswith('port:'):
                # Start service
                if action.startswith('port:'):
                    try:
                        port = int(action.split(':')[1])
                        result = service.do(f"start port={port}")
                    except ValueError:
                        print(f"❌ Invalid port: {action}")
                        return False
                else:
                    result = service.do("start")
                
                if result.get('success'):
                    print(f"✅ {result['message']}")
                    print(f"🌐 Access: {result['url']}")
                    print(f"📁 Virtual filesystem:")
                    print(f"   /tournaments/ - Tournament data and analytics")
                    print(f"   /players/     - Player stats and performance")  
                    print(f"   /organizations/ - Organization info and contacts")
                    print(f"🔧 Mount in file manager as WebDAV network drive")
                else:
                    print(f"❌ Failed to start: {result.get('error', 'Unknown error')}")
                    return False
            
            elif action == 'status':
                # Get status
                status = service.ask("status")
                print(service.tell("text", status))
            
            elif action == 'stats':
                # Get statistics
                stats = service.ask("stats")
                print(service.tell("text", stats))
            
            elif action == 'restart':
                # Restart service
                result = service.do("restart")
                if result.get('success'):
                    print(f"✅ {result['message']}")
                else:
                    print(f"❌ Restart failed: {result.get('error', 'Unknown error')}")
                    return False
            
            elif action == 'stop':
                # Stop service
                result = service.do("stop")
                if result.get('success'):
                    print(f"✅ {result['message']}")
                else:
                    print(f"❌ Stop failed: {result.get('error', 'Unknown error')}")
                    return False
            
            elif action == 'health':
                # Health check
                health = service.do("health")
                print(f"🏥 Health Status: {health.get('overall_health', 'unknown').upper()}")
                for check_name, check_result in health.get('checks', {}).items():
                    status_emoji = "✅" if check_result['status'] == 'pass' else "❌"
                    print(f"   {status_emoji} {check_name.replace('_', ' ').title()}: {check_result['message']}")
            
            else:
                print(f"❌ Unknown action: {action}")
                print("Available actions: start, status, stats, restart, stop, health, port:XXXX")
                return False
            
            return True
            
        return False


# Create the switch instance
webdav_refactored_switch = GoSwitchWebdavRefactored()

# Register with dynamic switches
announce_switch(
    flag="--webdav-refactored",
    help="START WebDAV database browser (refactored) (start|status|restart|stop|port:8084)",
    handler=webdav_refactored_switch.handle_args,
    action='store',
    nargs='?',
    const='start'
)