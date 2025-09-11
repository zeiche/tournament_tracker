#!/usr/bin/env python3
"""
twilio_service_refactored.py - Unified Twilio Service with Service Locator Pattern

This module consolidates all Twilio functionality using the service locator pattern
for transparent local/network service access.
"""

import sys
import os
import subprocess
from typing import Optional, List, Any, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.service_locator import get_service
from polymorphic_core.network_service_wrapper import NetworkServiceWrapper
from polymorphic_core import announcer
from dynamic_switches import announce_switch


class TwilioServiceRefactored:
    """
    Unified Twilio service using service locator pattern.
    
    Provides telephony operations with 3-method pattern:
    - ask(query): Query Twilio status and information
    - tell(format, data): Format Twilio data for output  
    - do(action): Perform Twilio operations
    """
    
    def __init__(self, prefer_network: bool = False):
        """Initialize with service locator dependencies"""
        self.prefer_network = prefer_network
        self._logger = None
        self._error_handler = None
        self._config = None
        self._process_manager = None
        
        # Service statistics
        self.stats = {
            'calls_made': 0,
            'bridges_started': 0,
            'services_started': 0,
            'errors': 0,
            'last_operation': None
        }
    
    @property
    def logger(self):
        """Get logger service via service locator"""
        if self._logger is None:
            self._logger = get_service("logger", self.prefer_network)
        return self._logger
    
    @property
    def error_handler(self):
        """Get error handler service via service locator"""
        if self._error_handler is None:
            self._error_handler = get_service("error_handler", self.prefer_network)
        return self._error_handler
    
    @property
    def config(self):
        """Get config service via service locator"""
        if self._config is None:
            self._config = get_service("config", self.prefer_network)
        return self._config
    
    @property
    def process_manager(self):
        """Get process manager (local only for now)"""
        if self._process_manager is None:
            from polymorphic_core.process import ProcessManager
            self._process_manager = ProcessManager
        return self._process_manager
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query Twilio service information using natural language.
        
        Args:
            query: Natural language query about Twilio
            **kwargs: Additional query parameters
            
        Returns:
            Relevant Twilio information
        """
        query_lower = query.lower().strip()
        
        try:
            if "status" in query_lower or "health" in query_lower:
                return self._get_service_status()
            elif "stats" in query_lower or "statistics" in query_lower:
                return self.stats
            elif "config" in query_lower or "configuration" in query_lower:
                return self._get_twilio_config()
            elif "processes" in query_lower or "running" in query_lower:
                return self._get_running_processes()
            elif "calls" in query_lower and "history" in query_lower:
                return self._get_call_history()
            elif "capabilities" in query_lower or "help" in query_lower:
                return self._get_capabilities()
            else:
                self.logger.warning(f"Unknown Twilio query: {query}")
                return {"error": f"Unknown query: {query}", "suggestions": self._get_capabilities()}
                
        except Exception as e:
            error_msg = f"Twilio query failed: {e}"
            self.error_handler.handle_error(error_msg, {"query": query})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """
        Format Twilio data for output.
        
        Args:
            format_type: Output format (discord, json, text, html)
            data: Data to format (uses current stats if None)
            
        Returns:
            Formatted string
        """
        if data is None:
            data = self.stats
            
        try:
            if format_type == "discord":
                return self._format_for_discord(data)
            elif format_type == "json":
                import json
                return json.dumps(data, indent=2)
            elif format_type == "text" or format_type == "console":
                return self._format_for_text(data)
            elif format_type == "html":
                return self._format_for_html(data)
            else:
                return str(data)
                
        except Exception as e:
            error_msg = f"Twilio formatting failed: {e}"
            self.error_handler.handle_error(error_msg, {"format": format_type, "data": data})
            return f"Error formatting data: {error_msg}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform Twilio operations using natural language.
        
        Args:
            action: Natural language action to perform
            **kwargs: Additional action parameters
            
        Returns:
            Action result
        """
        action_lower = action.lower().strip()
        self.stats['last_operation'] = action
        
        try:
            if "start bridge" in action_lower or "bridge" in action_lower:
                return self._start_bridge()
            elif "call" in action_lower:
                phone = kwargs.get('phone') or self._extract_phone_from_action(action)
                if phone:
                    return self._make_call(phone)
                else:
                    return {"error": "No phone number provided for call"}
            elif "start service" in action_lower or "service" in action_lower:
                return self._start_service()
            elif "generate config" in action_lower or "config" in action_lower:
                return self._generate_config()
            elif "start voice" in action_lower or "voice" in action_lower:
                return self._start_voice_servers()
            elif "start transcription" in action_lower or "transcription" in action_lower:
                return self._start_transcription()
            elif "start inbound" in action_lower or "inbound" in action_lower:
                return self._start_inbound_handler()
            elif "stop" in action_lower or "kill" in action_lower:
                return self._stop_services()
            elif "restart" in action_lower:
                self._stop_services()
                return self._start_bridge()
            else:
                self.logger.warning(f"Unknown Twilio action: {action}")
                return {"error": f"Unknown action: {action}", "suggestions": self._get_action_suggestions()}
                
        except Exception as e:
            error_msg = f"Twilio action failed: {e}"
            self.error_handler.handle_error(error_msg, {"action": action, "kwargs": kwargs})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _start_bridge(self) -> Dict[str, Any]:
        """Start Twilio bridge (handles calls/SMS)"""
        try:
            self.logger.info("Starting Twilio bridge...")
            
            # Try integrated process manager first
            try:
                sys.path.insert(0, 'experimental/telephony')
                from twilio_simple_voice_bridge import _twilio_process_manager
                self.logger.info("Starting Twilio services via integrated TwilioProcessManager")
                pids = _twilio_process_manager.start_services()
                self.logger.info(f"Twilio services started with PIDs: {pids}")
                self.stats['bridges_started'] += 1
                return {"success": True, "pids": pids, "method": "integrated"}
            except (ImportError, NameError) as e:
                self.logger.warning(f"Integrated TwilioProcessManager not available: {e}")
                return self._start_bridge_fallback()
                
        except Exception as e:
            error_msg = f"Twilio bridge startup failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _start_bridge_fallback(self) -> Dict[str, Any]:
        """Fallback bridge startup method"""
        try:
            self.logger.info("Falling back to manual process management")
            
            # Kill existing processes
            self.process_manager.kill_pattern('twilio_simple_voice_bridge')
            self.process_manager.kill_pattern('twiml_stream_server')
            self.process_manager.kill_pattern('twilio_stream_server')
            self.process_manager.kill_pattern('polymorphic_encryption')
            self.process_manager.kill_port(8087)
            self.process_manager.kill_port(8086)
            self.process_manager.kill_port(8443)
            
            import time
            time.sleep(1)
            
            # Start services in order
            services_started = []
            services_started.append(self.process_manager.start_service_safe('twilio_stream_server.py'))
            services_started.append(self.process_manager.start_service_safe('twiml_stream_server.py'))
            services_started.append(self.process_manager.start_service_safe('polymorphic_encryption_service.py', '--proxy', '8443', '8087'))
            services_started.append(self.process_manager.start_service_safe('experimental/telephony/twilio_simple_voice_bridge.py'))
            
            self.stats['bridges_started'] += 1
            return {"success": True, "services": services_started, "method": "fallback"}
            
        except Exception as e:
            error_msg = f"Fallback bridge startup failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _make_call(self, phone: str) -> Dict[str, Any]:
        """Make an outbound call"""
        try:
            self.logger.info(f"Making outbound call to {phone}...")
            result = subprocess.run([sys.executable, 'call_me.py', phone], 
                                 capture_output=True, text=True)
            self.stats['calls_made'] += 1
            return {
                "success": True, 
                "phone": phone, 
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            error_msg = f"Call to {phone} failed: {e}"
            self.error_handler.handle_error(error_msg, {"phone": phone})
            self.stats['errors'] += 1
            return {"error": error_msg, "phone": phone}
    
    def _start_service(self) -> Dict[str, Any]:
        """Start Twilio service using ProcessManager"""
        try:
            self.logger.info("Starting Twilio service...")
            result = self.process_manager.restart_service('bonjour_twilio.py')
            self.stats['services_started'] += 1
            return {"success": True, "service": "bonjour_twilio.py", "result": result}
        except Exception as e:
            error_msg = f"Twilio service startup failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _generate_config(self) -> Dict[str, Any]:
        """Generate Twilio configs"""
        try:
            self.logger.info("Generating Twilio configuration...")
            result = subprocess.run([sys.executable, 'twilio_config.py'], 
                                 capture_output=True, text=True)
            return {
                "success": True,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            error_msg = f"Config generation failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _start_voice_servers(self) -> Dict[str, Any]:
        """Start voice-enabled Twilio stream servers"""
        try:
            self.logger.info("Starting voice-enabled Twilio servers...")
            
            # Kill existing
            self.process_manager.kill_pattern('twiml_stream_server')
            self.process_manager.kill_pattern('modern_stream_server')
            
            # Start new
            services = []
            services.append(self.process_manager.start_service_safe('twiml_stream_server.py'))  # TwiML on 8086
            services.append(self.process_manager.start_service_safe('modern_stream_server.py'))  # Voice WebSocket on 8094
            
            return {"success": True, "services": services}
        except Exception as e:
            error_msg = f"Voice servers startup failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _start_transcription(self) -> Dict[str, Any]:
        """Start Twilio stream with polymorphic transcription"""
        try:
            self.logger.info("Starting Twilio transcription services...")
            
            # Kill existing processes
            patterns = [
                'twilio_stream_polymorphic',
                'twilio_transcription_bridge',
                'twiml_stream_server',
                'twilio_stream_server',
                'twilio_simple_voice_bridge'
            ]
            for pattern in patterns:
                self.process_manager.kill_pattern(pattern)
            
            self.process_manager.kill_port(8088)
            self.process_manager.kill_port(8086)
            
            import time
            time.sleep(2)
            
            # Start transcription services
            services = []
            services.append(self.process_manager.start_service_safe('twiml_stream_server.py'))  # TwiML on 8086
            services.append(self.process_manager.start_service_safe('twilio_transcription_bridge.py'))  # Bridge
            services.append(self.process_manager.start_service_safe('twilio_stream_polymorphic.py'))  # WebSocket on 8088
            
            return {"success": True, "services": services}
        except Exception as e:
            error_msg = f"Transcription services startup failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _start_inbound_handler(self) -> Dict[str, Any]:
        """Start inbound call handler"""
        try:
            self.logger.info("Starting inbound call handler...")
            process = subprocess.Popen([sys.executable, 'inbound_call_handler.py'])
            return {"success": True, "pid": process.pid}
        except Exception as e:
            error_msg = f"Inbound handler startup failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _stop_services(self) -> Dict[str, Any]:
        """Stop all Twilio services"""
        try:
            self.logger.info("Stopping all Twilio services...")
            
            patterns = [
                'twilio_simple_voice_bridge',
                'twiml_stream_server',
                'twilio_stream_server',
                'twilio_stream_polymorphic',
                'twilio_transcription_bridge',
                'polymorphic_encryption',
                'modern_stream_server',
                'inbound_call_handler'
            ]
            
            killed_patterns = []
            for pattern in patterns:
                if self.process_manager.kill_pattern(pattern):
                    killed_patterns.append(pattern)
            
            ports = [8086, 8087, 8088, 8094, 8443]
            killed_ports = []
            for port in ports:
                if self.process_manager.kill_port(port):
                    killed_ports.append(port)
            
            return {
                "success": True,
                "killed_patterns": killed_patterns,
                "killed_ports": killed_ports
            }
        except Exception as e:
            error_msg = f"Service shutdown failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get current Twilio service status"""
        try:
            # Check if key processes are running
            patterns = [
                'twilio_simple_voice_bridge',
                'twiml_stream_server',
                'twilio_stream_server',
                'polymorphic_encryption'
            ]
            
            running_services = []
            for pattern in patterns:
                if self.process_manager.is_process_running(pattern):
                    running_services.append(pattern)
            
            # Check if key ports are in use
            ports = [8086, 8087, 8088, 8443]
            active_ports = []
            for port in ports:
                if self.process_manager.is_port_in_use(port):
                    active_ports.append(port)
            
            return {
                "running_services": running_services,
                "active_ports": active_ports,
                "stats": self.stats,
                "healthy": len(running_services) > 0
            }
        except Exception as e:
            return {"error": f"Status check failed: {e}"}
    
    def _get_twilio_config(self) -> Dict[str, Any]:
        """Get Twilio configuration"""
        try:
            config_data = {}
            if self.config:
                config_data = {
                    "twilio_account_sid": self.config.get("TWILIO_ACCOUNT_SID", "Not set"),
                    "twilio_auth_token": "***" if self.config.get("TWILIO_AUTH_TOKEN") else "Not set",
                    "twilio_phone_number": self.config.get("TWILIO_PHONE_NUMBER", "Not set"),
                    "webhook_url": self.config.get("TWILIO_WEBHOOK_URL", "Not set")
                }
            return config_data
        except Exception as e:
            return {"error": f"Config retrieval failed: {e}"}
    
    def _get_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of running Twilio processes"""
        try:
            patterns = [
                'twilio_simple_voice_bridge',
                'twiml_stream_server',
                'twilio_stream_server',
                'twilio_stream_polymorphic',
                'twilio_transcription_bridge',
                'polymorphic_encryption',
                'modern_stream_server',
                'inbound_call_handler'
            ]
            
            processes = []
            for pattern in patterns:
                if self.process_manager.is_process_running(pattern):
                    processes.append({
                        "name": pattern,
                        "status": "running",
                        "pattern": pattern
                    })
                else:
                    processes.append({
                        "name": pattern,
                        "status": "stopped",
                        "pattern": pattern
                    })
            
            return processes
        except Exception as e:
            return [{"error": f"Process check failed: {e}"}]
    
    def _get_call_history(self) -> Dict[str, Any]:
        """Get call history (placeholder - would integrate with actual call logs)"""
        return {
            "total_calls": self.stats['calls_made'],
            "recent_calls": [],  # Would populate from actual call logs
            "note": "Full call history requires Twilio API integration"
        }
    
    def _get_capabilities(self) -> List[str]:
        """Get list of available capabilities"""
        return [
            "start bridge - Start Twilio bridge services",
            "call <phone> - Make outbound call",
            "start service - Start Twilio bonjour service",
            "generate config - Generate configuration",
            "start voice - Start voice servers",
            "start transcription - Start transcription services",
            "start inbound - Start inbound handler",
            "stop - Stop all services",
            "restart - Restart all services"
        ]
    
    def _get_action_suggestions(self) -> List[str]:
        """Get action suggestions"""
        return self._get_capabilities()
    
    def _extract_phone_from_action(self, action: str) -> Optional[str]:
        """Extract phone number from action string"""
        import re
        phone_match = re.search(r'call\s+(\+?[\d\-\(\)\s]+)', action)
        if phone_match:
            return phone_match.group(1).strip()
        return None
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, dict):
            if "error" in data:
                return f"❌ **Twilio Error:** {data['error']}"
            elif "success" in data and data["success"]:
                return f"✅ **Twilio Success:** Operation completed"
            elif "stats" in data or "calls_made" in data:
                stats = data.get("stats", data)
                return f"""📞 **Twilio Status:**
• Calls Made: {stats.get('calls_made', 0)}
• Bridges Started: {stats.get('bridges_started', 0)}
• Services Started: {stats.get('services_started', 0)}
• Errors: {stats.get('errors', 0)}
• Last Operation: {stats.get('last_operation', 'None')}"""
        return f"📞 Twilio: {str(data)}"
    
    def _format_for_text(self, data: Any) -> str:
        """Format data for text/console output"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        return str(data)
    
    def _format_for_html(self, data: Any) -> str:
        """Format data for HTML output"""
        if isinstance(data, dict):
            html = "<table border='1'>"
            for key, value in data.items():
                html += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
            html += "</table>"
            return html
        return f"<pre>{str(data)}</pre>"


# Announce service capabilities
announcer.announce(
    "Twilio Service (Refactored)",
    [
        "Telephony operations with 3-method pattern",
        "ask('status') - Query Twilio status and information",
        "tell('discord', data) - Format Twilio data for output",
        "do('start bridge') - Perform Twilio operations",
        "Supports: bridge, call, service, config, voice, transcription, inbound",
        "Uses service locator for transparent local/network operation"
    ],
    [
        "twilio.ask('status')",
        "twilio.do('start bridge')",
        "twilio.do('call +1234567890')",
        "twilio.tell('discord')"
    ]
)

# Singleton instance
twilio_service_refactored = TwilioServiceRefactored()

# Create network service wrapper for remote access
if __name__ != "__main__":
    try:
        wrapper = NetworkServiceWrapper(
            service=twilio_service_refactored,
            service_name="twilio_refactored",
            port_range=(9000, 9100)
        )
        # Auto-start network service in background
        wrapper.start_service_thread()
    except Exception as e:
        # Gracefully handle if network service fails
        pass


def start_twilio_service_refactored(args=None):
    """Handler for --twilio switch with service locator pattern"""
    
    # Determine operation from arguments
    operation = "bridge"  # default
    phone = None
    
    if hasattr(args, 'twilio') and args.twilio:
        if args.twilio.startswith('call:'):
            operation = "call"
            phone = args.twilio.split(':', 1)[1]
        else:
            operation = args.twilio
    
    twilio_service_refactored.logger.info(f"Starting Twilio operation: {operation}")
    
    try:
        if operation == "bridge":
            result = twilio_service_refactored.do("start bridge")
        elif operation == "call" and phone:
            result = twilio_service_refactored.do(f"call {phone}")
        elif operation == "service":
            result = twilio_service_refactored.do("start service")
        elif operation == "config":
            result = twilio_service_refactored.do("generate config")
        elif operation == "voice":
            result = twilio_service_refactored.do("start voice")
        elif operation == "transcription":
            result = twilio_service_refactored.do("start transcription")
        elif operation == "inbound":
            result = twilio_service_refactored.do("start inbound")
        else:
            twilio_service_refactored.logger.warning(f"Unknown Twilio operation: {operation}. Using bridge.")
            result = twilio_service_refactored.do("start bridge")
        
        # Format result for output
        if result:
            formatted = twilio_service_refactored.tell("text", result)
            print(formatted)
        
        return result
            
    except Exception as e:
        error_msg = f"Twilio operation failed: {e}"
        twilio_service_refactored.error_handler.handle_error(error_msg, {"operation": operation, "phone": phone})
        print(f"Error: {error_msg}")
        return None


# Register the refactored switch (commented out for now to avoid conflicts)
# announce_switch(
#     flag="--twilio-refactored",
#     help="START Twilio telephony (refactored with service locator)",
#     handler=start_twilio_service_refactored,
#     action="store",
#     nargs="?",
#     const="bridge",
#     metavar="CMD"
# )