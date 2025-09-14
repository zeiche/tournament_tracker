#!/usr/bin/env python3
"""
Dynamic switch for Interactive Web Service Daemon
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.interactive_web_switch")

from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch
from polymorphic_core.process import ProcessManager
import subprocess

def handle_interactive_web(args):
    """Handle --interactive-web command"""
    
    # Announce this switch
    announcer.announce(
        "Interactive Web Service Switch", 
        ["Starts the Interactive Web Service Daemon on port 8083"]
    )
    
    print("🚀 Starting Interactive Web Service Daemon...")
    
    # Use ProcessManager to start the daemon properly
    process_manager = ProcessManager()
    
    # Start the interactive web service daemon
    service_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'services', 'interactive_web_service_daemon.py'
    )
    
    try:
        process_manager.start_background_service(
            'interactive_web_daemon',
            [sys.executable, service_path],
            description="Interactive Web Service Daemon (port 8083)"
        )
        print("✅ Interactive Web Service Daemon started")
        return "Interactive Web Service Daemon started on port 8083"
        
    except Exception as e:
        print(f"❌ Failed to start Interactive Web Service Daemon: {e}")
        return f"Failed to start: {e}"

# Register the switch
announce_switch(
    "--interactive-web", 
    handle_interactive_web,
    description="Start Interactive Web Service Daemon for non-blocking browser automation"
)