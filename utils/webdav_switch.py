#!/usr/bin/env python3
"""
WebDAV Database Browser Switch - Announces WebDAV service capability
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.webdav_switch")

from polymorphic_core import announcer, announces_capability


@announces_capability
class GoSwitchWebdav:
    """
    WebDAV Database Browser switch for go.py
    Provides file-system interface to database with built-in model visualizations.
    """
    
    def __init__(self):
        announcer.announce(
            "GoSwitch__webdav",
            [
                "WebDAV Database Browser - Virtual filesystem for database objects",
                "Maps tables to directories, records to files with built-in visualizations",
                "Exposes model intelligence: analytics, heatmaps, performance metrics",
                "Port 8081: http://localhost:8081",
                "Compatible with any WebDAV client or file manager"
            ],
            examples=[
                "./go.py --webdav    # Start WebDAV database browser on port 8443 (PERMANENT PORT)"
            ]
        )
    
    def get_argument_parser(self, parent_parser):
        """Add WebDAV arguments to the parser"""
        parent_parser.add_argument(
            '--webdav',
            nargs='?',
            const='start',
            help='START WebDAV database browser (start|port:8084)'
        )
        return parent_parser
    
    def handle_args(self, args, remaining_args):
        """Handle WebDAV-related arguments"""
        if hasattr(args, 'webdav') and args.webdav is not None:
            
            # Parse port if specified
            # ⚠️  CRITICAL: WEBDAV PERMANENTLY USES PORT 8443 - DO NOT CHANGE! ⚠️
            port = 8443
            if args.webdav != 'start' and ':' in args.webdav:
                try:
                    port = int(args.webdav.split(':')[1])
                except ValueError:
                    # ⚠️  CRITICAL: WEBDAV PERMANENTLY USES PORT 8443 - DO NOT CHANGE! ⚠️
            port = 8443
            
            # Start WebDAV service
            print(f"🗂️  Starting WebDAV Database Browser on port {port}")
            
            # Kill any existing service on the port
            import subprocess
            try:
                subprocess.run(['fuser', '-k', f'{port}/tcp'], 
                             capture_output=True, timeout=5)
            except:
                pass
            
            # Start the WebDAV launcher
            result = subprocess.run([
                sys.executable, 'webdav_launcher.py', str(port)
            ], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            return result.returncode == 0
            
        return False


# Create the switch instance
webdav_switch = GoSwitchWebdav()