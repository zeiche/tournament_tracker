#!/usr/bin/env python3
"""
process_service_refactored.py - Essential Process Management Service with Service Locator Pattern

This module provides essential process management using the service locator pattern
for transparent local/network service access.
"""

import sys
import os
import json
from typing import Optional, List, Any, Dict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.service_locator import get_service
from polymorphic_core.network_service_wrapper import NetworkServiceWrapper
from polymorphic_core import announcer
from dynamic_switches import announce_switch


class ProcessServiceRefactored:
    """
    Essential process management service using service locator pattern.
    
    Provides process management with 3-method pattern:
    - ask(query): Query process status and information
    - tell(format, data): Format process data for output  
    - do(action): Perform process management operations
    """
    
    def __init__(self, prefer_network: bool = False):
        """Initialize with service locator dependencies"""
        self.prefer_network = prefer_network
        self._logger = None
        self._error_handler = None
        self._config = None
        self._process_manager = None
        
        # Process management statistics
        self.stats = {
            'services_restarted': 0,
            'status_checks': 0,
            'processes_killed': 0,
            'processes_started': 0,
            'errors': 0,
            'last_operation': None,
            'last_operation_time': None
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
        """Get process manager (local only for security)"""
        if self._process_manager is None:
            from polymorphic_core.process import ProcessManager
            self._process_manager = ProcessManager
        return self._process_manager
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query process service information using natural language.
        
        Args:
            query: Natural language query about processes
            **kwargs: Additional query parameters
            
        Returns:
            Relevant process information
        """
        query_lower = query.lower().strip()
        
        try:
            if "status" in query_lower or "health" in query_lower:
                return self._get_service_status()
            elif "stats" in query_lower or "statistics" in query_lower:
                return self.stats
            elif "running" in query_lower or "processes" in query_lower:
                return self._get_running_processes()
            elif "services" in query_lower:
                return self._get_registered_services()
            elif "history" in query_lower or "recent" in query_lower:
                return self._get_operation_history()
            elif "announcements" in query_lower or "bonjour" in query_lower:
                return self._get_service_announcements()
            elif "capabilities" in query_lower or "help" in query_lower:
                return self._get_capabilities()
            else:
                self.logger.warning(f"Unknown process query: {query}")
                return {"error": f"Unknown query: {query}", "suggestions": self._get_capabilities()}
                
        except Exception as e:
            error_msg = f"Process query failed: {e}"
            self.error_handler.handle_error(error_msg, {"query": query})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """
        Format process data for output.
        
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
                return json.dumps(data, indent=2, default=str)
            elif format_type == "text" or format_type == "console":
                return self._format_for_text(data)
            elif format_type == "html":
                return self._format_for_html(data)
            else:
                return str(data)
                
        except Exception as e:
            error_msg = f"Process formatting failed: {e}"
            self.error_handler.handle_error(error_msg, {"format": format_type, "data": data})
            return f"Error formatting data: {error_msg}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform process management operations using natural language.
        
        Args:
            action: Natural language action to perform
            **kwargs: Additional action parameters
            
        Returns:
            Action result
        """
        action_lower = action.lower().strip()
        self.stats['last_operation'] = action
        self.stats['last_operation_time'] = datetime.now().isoformat()
        
        try:
            if "restart services" in action_lower or "restart" in action_lower:
                return self._restart_services()
            elif "check status" in action_lower or "status" in action_lower:
                return self._check_service_status()
            elif "kill process" in action_lower or "kill" in action_lower:
                pattern = kwargs.get('pattern') or self._extract_pattern_from_action(action)
                if pattern:
                    return self._kill_process_pattern(pattern)
                else:
                    return {"error": "No process pattern specified for kill operation"}
            elif "start service" in action_lower or "start" in action_lower:
                service = kwargs.get('service') or self._extract_service_from_action(action)
                if service:
                    return self._start_service(service)
                else:
                    return {"error": "No service specified for start operation"}
            elif "list processes" in action_lower or "list" in action_lower:
                return self._list_all_processes()
            elif "clear stats" in action_lower or "reset" in action_lower:
                return self._clear_statistics()
            elif "test" in action_lower:
                return self._test_process_system()
            else:
                self.logger.warning(f"Unknown process action: {action}")
                return {"error": f"Unknown action: {action}", "suggestions": self._get_action_suggestions()}
                
        except Exception as e:
            error_msg = f"Process action failed: {e}"
            self.error_handler.handle_error(error_msg, {"action": action, "kwargs": kwargs})
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _restart_services(self) -> Dict[str, Any]:
        """Restart services using integrated process managers"""
        try:
            self.logger.info("Restarting services via integrated ProcessManagers")
            
            results = {
                "success": True,
                "services_restarted": [],
                "failures": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Restart Discord using its process manager
            try:
                from networking.bonjour_discord import _discord_process_manager
                discord_pids = _discord_process_manager.start_services()
                self.logger.info(f"Discord restarted with PIDs: {discord_pids}")
                results["services_restarted"].append({
                    "service": "Discord",
                    "method": "integrated",
                    "pids": discord_pids
                })
            except (ImportError, NameError) as e:
                self.logger.warning(f"Discord ProcessManager not available, using fallback: {e}")
                try:
                    self.process_manager.kill_pattern('discord')
                    self.process_manager.kill_pattern('polymorphic_discord')
                    pid = self.process_manager.start_service_safe('bonjour_discord.py', check_existing=False)
                    results["services_restarted"].append({
                        "service": "Discord",
                        "method": "fallback",
                        "pid": pid
                    })
                except Exception as fallback_error:
                    results["failures"].append({
                        "service": "Discord",
                        "error": str(fallback_error)
                    })
            
            # Restart Polymorphic Web Editor using its process manager
            try:
                from services.polymorphic_web_editor import _web_editor_process_manager
                web_pids = _web_editor_process_manager.start_services()
                self.logger.info(f"Polymorphic Web Editor restarted with PIDs: {web_pids}")
                results["services_restarted"].append({
                    "service": "Web Editor",
                    "method": "integrated",
                    "pids": web_pids
                })
            except (ImportError, NameError) as e:
                self.logger.warning(f"Polymorphic Web Editor ProcessManager not available, using fallback: {e}")
                try:
                    self.process_manager.kill_pattern('web_editor')
                    self.process_manager.kill_pattern('polymorphic_web_editor')
                    pid = self.process_manager.start_service_safe('services/polymorphic_web_editor.py', check_existing=False)
                    results["services_restarted"].append({
                        "service": "Web Editor",
                        "method": "fallback",
                        "pid": pid
                    })
                except Exception as fallback_error:
                    results["failures"].append({
                        "service": "Web Editor",
                        "error": str(fallback_error)
                    })
            
            self.stats['services_restarted'] += len(results["services_restarted"])
            self.logger.info("Services restarted")
            
            if results["failures"]:
                results["success"] = len(results["services_restarted"]) > 0
            
            return results
            
        except Exception as e:
            error_msg = f"Service restart failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _check_service_status(self) -> Dict[str, Any]:
        """Check service status using bonjour signals"""
        try:
            self.logger.info("Service Status (via Bonjour Signals)")
            
            results = {
                "success": True,
                "bonjour_responses": {},
                "registered_services": [],
                "announcements": "",
                "fallback_processes": {},
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                # Send status signal to all registered services
                self.logger.info("Sending status signal to all services")
                responses = announcer.send_signal('status')
                
                if responses:
                    results["bonjour_responses"] = responses
                else:
                    results["bonjour_responses"] = {"message": "No services responded to status signal"}
                
                # Get registered services
                if announcer.service_registry:
                    results["registered_services"] = list(announcer.service_registry.keys())
                
                # Get announcements
                context = announcer.get_announcements_for_claude()
                if context and "No services" not in context:
                    results["announcements"] = context
                else:
                    results["announcements"] = "No service announcements available"
                    
            except Exception as bonjour_error:
                results["bonjour_error"] = str(bonjour_error)
                
                # Fallback to ProcessManager process check
                self.logger.info("Falling back to ProcessManager process check")
                processes = self.process_manager.list_tournament_processes()
                if processes:
                    results["fallback_processes"] = {
                        pattern: {"process_count": len(pids), "pids": pids}
                        for pattern, pids in processes.items()
                    }
                else:
                    results["fallback_processes"] = {"message": "No tournament tracker processes found"}
            
            self.stats['status_checks'] += 1
            return results
            
        except Exception as e:
            error_msg = f"Status check failed: {e}"
            self.error_handler.handle_error(error_msg)
            self.stats['errors'] += 1
            return {"error": error_msg}
    
    def _kill_process_pattern(self, pattern: str) -> Dict[str, Any]:
        """Kill processes matching a pattern"""
        try:
            self.logger.info(f"Killing processes matching pattern: {pattern}")
            
            killed_count = self.process_manager.kill_pattern(pattern)
            self.stats['processes_killed'] += killed_count
            
            return {
                "success": True,
                "pattern": pattern,
                "killed_count": killed_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Process kill failed for pattern {pattern}: {e}"
            self.error_handler.handle_error(error_msg, {"pattern": pattern})
            self.stats['errors'] += 1
            return {"error": error_msg, "pattern": pattern}
    
    def _start_service(self, service: str) -> Dict[str, Any]:
        """Start a service"""
        try:
            self.logger.info(f"Starting service: {service}")
            
            pid = self.process_manager.start_service_safe(service, check_existing=True)
            self.stats['processes_started'] += 1
            
            return {
                "success": True,
                "service": service,
                "pid": pid,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Service start failed for {service}: {e}"
            self.error_handler.handle_error(error_msg, {"service": service})
            self.stats['errors'] += 1
            return {"error": error_msg, "service": service}
    
    def _list_all_processes(self) -> Dict[str, Any]:
        """List all tournament tracker processes"""
        try:
            processes = self.process_manager.list_tournament_processes()
            
            return {
                "success": True,
                "processes": {
                    pattern: {"count": len(pids), "pids": pids}
                    for pattern, pids in processes.items()
                },
                "total_patterns": len(processes),
                "total_processes": sum(len(pids) for pids in processes.values()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Process listing failed: {e}"
            self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _test_process_system(self) -> Dict[str, Any]:
        """Test the process management system"""
        try:
            self.logger.info("Testing process management system...")
            
            test_results = {}
            
            # Test ProcessManager availability
            try:
                test_results["process_manager"] = {
                    "available": self.process_manager is not None,
                    "methods": [
                        "kill_pattern",
                        "start_service_safe",
                        "list_tournament_processes",
                        "is_process_running"
                    ]
                }
            except Exception as e:
                test_results["process_manager"] = {"error": str(e)}
            
            # Test service dependencies
            try:
                service_tests = {}
                service_tests["logger"] = self.logger is not None
                service_tests["error_handler"] = self.error_handler is not None
                service_tests["config"] = self.config is not None
                test_results["services"] = service_tests
            except Exception as e:
                test_results["services"] = {"error": str(e)}
            
            # Test announcer functionality
            try:
                announcer_tests = {}
                announcer_tests["service_registry_size"] = len(announcer.service_registry) if announcer.service_registry else 0
                announcer_tests["can_send_signals"] = hasattr(announcer, 'send_signal')
                announcer_tests["can_get_announcements"] = hasattr(announcer, 'get_announcements_for_claude')
                test_results["announcer"] = announcer_tests
            except Exception as e:
                test_results["announcer"] = {"error": str(e)}
            
            return {
                "success": True,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Process system test failed: {e}"
            self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _clear_statistics(self) -> Dict[str, Any]:
        """Clear process management statistics"""
        try:
            old_stats = self.stats.copy()
            self.stats = {
                'services_restarted': 0,
                'status_checks': 0,
                'processes_killed': 0,
                'processes_started': 0,
                'errors': 0,
                'last_operation': None,
                'last_operation_time': None
            }
            
            return {
                "success": True,
                "message": "Statistics cleared",
                "previous_stats": old_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Statistics clear failed: {e}"
            self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get current process service status"""
        try:
            return {
                "status": "running",
                "stats": self.stats,
                "dependencies": {
                    "logger": self.logger is not None,
                    "error_handler": self.error_handler is not None,
                    "config": self.config is not None,
                    "process_manager": self.process_manager is not None
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Status check failed: {e}"}
    
    def _get_running_processes(self) -> Dict[str, Any]:
        """Get currently running processes"""
        try:
            return self._list_all_processes()
        except Exception as e:
            return {"error": f"Process listing failed: {e}"}
    
    def _get_registered_services(self) -> Dict[str, Any]:
        """Get registered services from announcer"""
        try:
            if announcer.service_registry:
                return {
                    "services": list(announcer.service_registry.keys()),
                    "count": len(announcer.service_registry)
                }
            else:
                return {"services": [], "count": 0}
        except Exception as e:
            return {"error": f"Service registry access failed: {e}"}
    
    def _get_operation_history(self) -> Dict[str, Any]:
        """Get operation history"""
        return {
            "last_operation": self.stats.get('last_operation'),
            "last_operation_time": self.stats.get('last_operation_time'),
            "total_operations": (
                self.stats.get('services_restarted', 0) +
                self.stats.get('status_checks', 0) +
                self.stats.get('processes_killed', 0) +
                self.stats.get('processes_started', 0)
            ),
            "breakdown": {
                "services_restarted": self.stats.get('services_restarted', 0),
                "status_checks": self.stats.get('status_checks', 0),
                "processes_killed": self.stats.get('processes_killed', 0),
                "processes_started": self.stats.get('processes_started', 0)
            },
            "errors": self.stats.get('errors', 0)
        }
    
    def _get_service_announcements(self) -> Dict[str, Any]:
        """Get service announcements"""
        try:
            context = announcer.get_announcements_for_claude()
            return {
                "announcements": context if context and "No services" not in context else "No announcements available",
                "registry_size": len(announcer.service_registry) if announcer.service_registry else 0
            }
        except Exception as e:
            return {"error": f"Announcement retrieval failed: {e}"}
    
    def _get_capabilities(self) -> List[str]:
        """Get list of available capabilities"""
        return [
            "restart services - Restart all core services",
            "check status - Check service status via bonjour",
            "kill process <pattern> - Kill processes matching pattern",
            "start service <service> - Start a specific service",
            "list processes - List all running processes",
            "test - Test process management system",
            "clear stats - Clear operation statistics"
        ]
    
    def _get_action_suggestions(self) -> List[str]:
        """Get action suggestions"""
        return self._get_capabilities()
    
    def _extract_pattern_from_action(self, action: str) -> Optional[str]:
        """Extract process pattern from action string"""
        import re
        pattern_match = re.search(r'kill\s+(?:process\s+)?([^\s]+)', action, re.IGNORECASE)
        if pattern_match:
            return pattern_match.group(1)
        return None
    
    def _extract_service_from_action(self, action: str) -> Optional[str]:
        """Extract service name from action string"""
        import re
        service_match = re.search(r'start\s+(?:service\s+)?([^\s]+)', action, re.IGNORECASE)
        if service_match:
            return service_match.group(1)
        return None
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, dict):
            if "error" in data:
                return f"❌ **Process Error:** {data['error']}"
            elif "success" in data and data["success"]:
                if "services_restarted" in data:
                    count = len(data["services_restarted"])
                    return f"🔄 **Services Restarted:** {count} services restarted successfully"
                elif "bonjour_responses" in data:
                    response_count = len(data["bonjour_responses"])
                    return f"📊 **Service Status:** {response_count} services responded"
                else:
                    return f"✅ **Process Success:** Operation completed"
            elif "stats" in data or "services_restarted" in data:
                stats = data.get("stats", data)
                return f"""🔧 **Process Management Status:**
• Services Restarted: {stats.get('services_restarted', 0)}
• Status Checks: {stats.get('status_checks', 0)}
• Processes Killed: {stats.get('processes_killed', 0)}
• Processes Started: {stats.get('processes_started', 0)}
• Errors: {stats.get('errors', 0)}
• Last Operation: {stats.get('last_operation', 'None')}"""
        return f"🔧 Process: {str(data)}"
    
    def _format_for_text(self, data: Any) -> str:
        """Format data for text/console output"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{key}:")
                    for subkey, subvalue in value.items():
                        lines.append(f"  {subkey}: {subvalue}")
                elif isinstance(value, list):
                    lines.append(f"{key}: {len(value)} items")
                    for i, item in enumerate(value[:5]):  # Show first 5 items
                        lines.append(f"  {i+1}: {item}")
                    if len(value) > 5:
                        lines.append(f"  ... and {len(value)-5} more")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        return str(data)
    
    def _format_for_html(self, data: Any) -> str:
        """Format data for HTML output"""
        if isinstance(data, dict):
            html = "<table border='1'>"
            for key, value in data.items():
                if isinstance(value, dict):
                    html += f"<tr><td><strong>{key}</strong></td><td>"
                    html += "<table border='1'>"
                    for subkey, subvalue in value.items():
                        html += f"<tr><td>{subkey}</td><td>{subvalue}</td></tr>"
                    html += "</table></td></tr>"
                else:
                    html += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
            html += "</table>"
            return html
        return f"<pre>{str(data)}</pre>"


# Announce service capabilities
announcer.announce(
    "Process Service (Refactored)",
    [
        "Process management with 3-method pattern",
        "ask('status') - Query process status and information",
        "tell('discord', data) - Format process data for output",
        "do('restart services') - Perform process management operations",
        "Essential infrastructure - cannot be consolidated",
        "Uses service locator for transparent local/network operation"
    ],
    [
        "process.ask('status')",
        "process.do('restart services')",
        "process.do('check status')",
        "process.tell('discord')"
    ]
)

# Singleton instance
process_service_refactored = ProcessServiceRefactored()

# Create network service wrapper for remote access
# Note: Process management is sensitive, so network access should be carefully controlled
if __name__ != "__main__":
    try:
        wrapper = NetworkServiceWrapper(
            service=process_service_refactored,
            service_name="process_refactored",
            port_range=(9200, 9300)
        )
        # Auto-start network service in background
        wrapper.start_service_thread()
    except Exception as e:
        # Gracefully handle if network service fails
        pass


def restart_services_handler_refactored(args=None):
    """Handler for --restart-services switch with service locator pattern"""
    try:
        result = process_service_refactored.do("restart services")
        
        # Format result for output
        if result:
            formatted = process_service_refactored.tell("text", result)
            print(formatted)
        
        return result
    except Exception as e:
        error_msg = f"Service restart failed: {e}"
        process_service_refactored.error_handler.handle_error(error_msg)
        print(f"Error: {error_msg}")
        return None


def service_status_handler_refactored(args=None):
    """Handler for --service-status switch with service locator pattern"""
    try:
        result = process_service_refactored.do("check status")
        
        # Format result for output
        if result:
            formatted = process_service_refactored.tell("text", result)
            print(formatted)
        
        return result
    except Exception as e:
        error_msg = f"Status check failed: {e}"
        process_service_refactored.error_handler.handle_error(error_msg)
        print(f"Error: {error_msg}")
        return None


# Register the refactored switches (commented out for now to avoid conflicts)
# announce_switch(
#     flag="--restart-services-refactored",
#     help="Kill and restart all services (refactored with service locator)",
#     handler=restart_services_handler_refactored
# )

# announce_switch(
#     flag="--service-status-refactored", 
#     help="Check service status via bonjour signals (refactored with service locator)",
#     handler=service_status_handler_refactored
# )