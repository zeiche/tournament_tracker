#!/usr/bin/env python3
"""
twilio_service.py - Unified Twilio Service (Consolidates 6+ twilio switches)

This module consolidates all Twilio functionality into a single --twilio switch
with subcommands for different telephony operations.
"""

import sys
import os
import subprocess
from typing import Optional, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.simple_logger import info, warning, error
from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch


class TwilioService:
    """Unified service for all Twilio telephony operations"""
    
    def start_bridge(self):
        """Start Twilio bridge (handles calls/SMS)"""
        try:
            info("Starting Twilio bridge...")
            # Import the bridge file to get access to its process manager
            sys.path.insert(0, 'experimental/telephony')
            from twilio_simple_voice_bridge import _twilio_process_manager
            info("Starting Twilio services via integrated TwilioProcessManager")
            pids = _twilio_process_manager.start_services()
            info(f"Twilio services started with PIDs: {pids}")
            return pids
        except (ImportError, NameError) as e:
            warning(f"Integrated TwilioProcessManager not available: {e}")
            self._start_bridge_fallback()
    
    def _start_bridge_fallback(self):
        """Fallback bridge startup method"""
        from polymorphic_core.process import ProcessManager
        info("Falling back to manual process management")
        ProcessManager.kill_pattern('twilio_simple_voice_bridge')
        ProcessManager.kill_pattern('twiml_stream_server')
        ProcessManager.kill_pattern('twilio_stream_server')
        ProcessManager.kill_pattern('polymorphic_encryption')
        ProcessManager.kill_port(8087)
        ProcessManager.kill_port(8086)
        ProcessManager.kill_port(8443)
        import time
        time.sleep(1)
        ProcessManager.start_service_safe('twilio_stream_server.py')
        ProcessManager.start_service_safe('twiml_stream_server.py')
        ProcessManager.start_service_safe('polymorphic_encryption_service.py', '--proxy', '8443', '8087')
        ProcessManager.start_service_safe('experimental/telephony/twilio_simple_voice_bridge.py')
    
    def make_call(self, phone: str):
        """Make an outbound call"""
        try:
            info(f"Making outbound call to {phone}...")
            subprocess.run([sys.executable, 'call_me.py', phone])
        except Exception as e:
            error(f"Call failed: {e}")
    
    def start_service(self):
        """Start Twilio service using ProcessManager"""
        try:
            info("Starting Twilio service...")
            from polymorphic_core.process import ProcessManager
            ProcessManager.restart_service('bonjour_twilio.py')
        except Exception as e:
            error(f"Twilio service failed: {e}")
    
    def generate_config(self):
        """Generate Twilio configs"""
        try:
            info("Generating Twilio configuration...")
            subprocess.run([sys.executable, 'twilio_config.py'])
        except Exception as e:
            error(f"Config generation failed: {e}")
    
    def start_voice_servers(self):
        """Start voice-enabled Twilio stream servers"""
        try:
            info("Starting voice-enabled Twilio servers...")
            from polymorphic_core.process import ProcessManager
            ProcessManager.kill_pattern('twiml_stream_server')
            ProcessManager.kill_pattern('modern_stream_server')
            ProcessManager.start_service_safe('twiml_stream_server.py')  # TwiML on 8086
            ProcessManager.start_service_safe('modern_stream_server.py')  # Voice WebSocket on 8094
        except Exception as e:
            error(f"Voice servers failed: {e}")
    
    def start_transcription(self):
        """Start Twilio stream with polymorphic transcription"""
        try:
            info("Starting Twilio transcription services...")
            from polymorphic_core.process import ProcessManager
            ProcessManager.kill_pattern('twilio_stream_polymorphic')
            ProcessManager.kill_pattern('twilio_transcription_bridge')
            ProcessManager.kill_pattern('twiml_stream_server')
            ProcessManager.kill_pattern('twilio_stream_server')
            ProcessManager.kill_pattern('twilio_simple_voice_bridge')
            ProcessManager.kill_port(8088)
            ProcessManager.kill_port(8086)
            import time
            time.sleep(2)
            ProcessManager.start_service_safe('twiml_stream_server.py')  # TwiML on 8086
            ProcessManager.start_service_safe('twilio_transcription_bridge.py')  # Bridge
            ProcessManager.start_service_safe('twilio_stream_polymorphic.py')  # WebSocket on 8088
        except Exception as e:
            error(f"Transcription services failed: {e}")
    
    def start_inbound_handler(self):
        """Start inbound call handler with ManagedService identity"""
        try:
            info("Starting inbound call handler...")
            # Use relative path from tournament_tracker root
            handler_path = 'experimental/telephony/inbound_call_handler.py'
            subprocess.Popen([sys.executable, handler_path])
        except Exception as e:
            error(f"Inbound handler failed: {e}")


# Announce service capabilities
announcer.announce(
    "Unified Twilio Service",
    [
        "Consolidated telephony operations",
        "Supports: bridge, call, service, config, voice, transcription, inbound",
        "Single --twilio switch with subcommands"
    ],
    [
        "twilio.start_bridge()",
        "twilio.make_call('555-1234')",
        "twilio.start_transcription()"
    ]
)

# Singleton instance
twilio_service = TwilioService()


def start_twilio_service(args=None):
    """Handler for --twilio switch with subcommands"""
    
    # Determine operation from arguments
    operation = "bridge"  # default
    phone = None
    
    if hasattr(args, 'twilio') and args.twilio:
        if args.twilio.startswith('call:'):
            operation = "call"
            phone = args.twilio.split(':', 1)[1]
        else:
            operation = args.twilio
    
    info(f"Starting Twilio operation: {operation}")
    
    try:
        if operation == "bridge":
            twilio_service.start_bridge()
        elif operation == "call" and phone:
            twilio_service.make_call(phone)
        elif operation == "service":
            twilio_service.start_service()
        elif operation == "config":
            twilio_service.generate_config()
        elif operation == "voice":
            twilio_service.start_voice_servers()
        elif operation == "transcription":
            twilio_service.start_transcription()
        elif operation == "inbound":
            twilio_service.start_inbound_handler()
        else:
            warning(f"Unknown Twilio operation: {operation}. Using bridge.")
            twilio_service.start_bridge()
            
    except Exception as e:
        error(f"Twilio operation failed: {e}")
        return None


announce_switch(
    flag="--twilio",
    help="START Twilio telephony (bridge|call:PHONE|service|config|voice|transcription|inbound)",
    handler=start_twilio_service,
    action="store",
    nargs="?",
    const="bridge",  # Default when no argument provided
    metavar="CMD"
)