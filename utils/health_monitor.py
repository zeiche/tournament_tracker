#!/usr/bin/env python3
"""
health_monitor.py - Service Health Monitoring with 3-Method Pattern
Monitors all services and provides health status via ask/tell/do interface
"""
import sys
import os
import time
import psutil
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from threading import Thread, Lock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core import announcer
from utils.simple_logger import info, warning, error
from utils.config_service import get_config


@dataclass
class ServiceHealth:
    """Health status for a service"""
    name: str
    status: str  # healthy, degraded, unhealthy, unknown
    last_check: datetime
    response_time: float = 0.0
    error_count: int = 0
    uptime: Optional[timedelta] = None
    details: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """
    Service health monitoring with 3-method pattern
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceHealth] = {}
        self._lock = Lock()
        self._monitoring = False
        self._monitor_thread: Optional[Thread] = None
        
        # Known services to monitor
        self._known_services = {
            "discord": {"port": None, "process_name": "bonjour_discord.py"},
            "web_editor": {"port": 8081, "process_name": "web_editor.py"},
            "polymorphic_web_editor": {"port": 8081, "process_name": "polymorphic_web_editor.py"},
            "startgg_sync": {"port": None, "process_name": "startgg_sync.py"},
            "database": {"port": None, "file_path": "tournament_tracker.db"}
        }
        
        # Announce ourselves
        announcer.announce(
            "Health Monitor Service",
            [
                "Service health monitoring with 3-method pattern",
                "ask('service status') - Get health status",
                "tell('discord', health) - Format health reports",
                "do('start monitoring') - Begin health checks",
                "Monitors ports, processes, and service responses"
            ],
            [
                "health.ask('all services')",
                "health.do('check discord')",
                "health.tell('discord')"
            ]
        )
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query service health using natural language
        Examples:
            ask("all services")
            ask("discord status") 
            ask("unhealthy services")
            ask("system health")
        """
        query = query.lower().strip()
        
        if "all services" in query or "status" in query and "service" not in query:
            return self._get_all_health()
        
        elif "unhealthy" in query or "failed" in query:
            return self._get_unhealthy_services()
        
        elif "system" in query and "health" in query:
            return self._get_system_health()
        
        elif any(service in query for service in self._known_services.keys()):
            # Check specific service
            for service_name in self._known_services.keys():
                if service_name in query:
                    return self._check_service(service_name)
        
        else:
            return f"Unknown health query: {query}"
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format health information for output
        """
        if data is None:
            data = self._get_all_health()
        
        if format.lower() in ["json"]:
            import json
            return json.dumps(data, default=str, indent=2)
        
        elif format.lower() in ["discord", "text"]:
            if isinstance(data, dict):
                lines = ["🏥 **Service Health Status**"]
                
                for service_name, health in data.items():
                    if isinstance(health, ServiceHealth):
                        status_emoji = {
                            "healthy": "✅",
                            "degraded": "⚠️", 
                            "unhealthy": "❌",
                            "unknown": "❓"
                        }.get(health.status, "❓")
                        
                        lines.append(f"{status_emoji} {health.name}: {health.status}")
                        if health.response_time > 0:
                            lines.append(f"   Response: {health.response_time:.2f}ms")
                    else:
                        lines.append(f"• {service_name}: {health}")
                
                return "\n".join(lines)
            return str(data)
        
        else:
            return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform health monitoring actions
        Examples:
            do("start monitoring")
            do("stop monitoring")
            do("check all services")
            do("check discord")
        """
        action = action.lower().strip()
        
        if "start" in action and "monitor" in action:
            return self._start_monitoring()
        
        elif "stop" in action and "monitor" in action:
            return self._stop_monitoring()
        
        elif "check" in action:
            if "all" in action:
                return self._check_all_services()
            else:
                # Check specific service
                for service_name in self._known_services.keys():
                    if service_name in action:
                        health = self._check_service(service_name)
                        return f"{service_name}: {health.status}"
        
        elif "reset" in action:
            self._services.clear()
            return "Health history reset"
        
        else:
            return f"Unknown health action: {action}"
    
    def _start_monitoring(self) -> str:
        """Start background health monitoring"""
        if self._monitoring:
            return "Health monitoring already running"
        
        self._monitoring = True
        self._monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        info("Health monitoring started")
        return "Health monitoring started"
    
    def _stop_monitoring(self) -> str:
        """Stop background health monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        info("Health monitoring stopped")
        return "Health monitoring stopped"
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                self._check_all_services()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                error(f"Health monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_all_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all known services"""
        results = {}
        
        with self._lock:
            for service_name in self._known_services.keys():
                try:
                    health = self._check_service(service_name)
                    self._services[service_name] = health
                    results[service_name] = health
                except Exception as e:
                    error(f"Failed to check {service_name}: {e}")
                    health = ServiceHealth(
                        name=service_name,
                        status="unknown",
                        last_check=datetime.now(),
                        details={"error": str(e)}
                    )
                    self._services[service_name] = health
                    results[service_name] = health
        
        return results
    
    def _check_service(self, service_name: str) -> ServiceHealth:
        """Check health of a specific service"""
        service_config = self._known_services.get(service_name, {})
        start_time = time.time()
        
        health = ServiceHealth(
            name=service_name,
            status="unknown",
            last_check=datetime.now()
        )
        
        try:
            # Check if it's a database file
            if "file_path" in service_config:
                file_path = service_config["file_path"]
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    health.status = "healthy"
                    health.details = {"file_size": file_size}
                else:
                    health.status = "unhealthy"
                    health.details = {"error": "Database file not found"}
            
            # Check port if specified
            elif service_config.get("port"):
                port = service_config["port"]
                if self._check_port(port):
                    health.status = "healthy"
                    health.details = {"port": port, "listening": True}
                else:
                    health.status = "unhealthy" 
                    health.details = {"port": port, "listening": False}
            
            # Check process
            elif service_config.get("process_name"):
                process_name = service_config["process_name"]
                processes = self._find_processes(process_name)
                if processes:
                    health.status = "healthy"
                    health.details = {
                        "processes": len(processes),
                        "pids": [p.pid for p in processes]
                    }
                else:
                    health.status = "unhealthy"
                    health.details = {"process": process_name, "running": False}
            
            health.response_time = (time.time() - start_time) * 1000
            
        except Exception as e:
            health.status = "unhealthy"
            health.details = {"error": str(e)}
            health.response_time = (time.time() - start_time) * 1000
        
        return health
    
    def _check_port(self, port: int) -> bool:
        """Check if a port is listening"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(3)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except:
            return False
    
    def _find_processes(self, process_name: str) -> List[psutil.Process]:
        """Find processes by name"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if process_name in cmdline:
                        processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            error(f"Error finding processes: {e}")
        
        return processes
    
    def _get_all_health(self) -> Dict[str, ServiceHealth]:
        """Get health status of all services"""
        if not self._services:
            return self._check_all_services()
        return self._services.copy()
    
    def _get_unhealthy_services(self) -> Dict[str, ServiceHealth]:
        """Get only unhealthy services"""
        all_health = self._get_all_health()
        return {
            name: health for name, health in all_health.items()
            if health.status in ["unhealthy", "degraded"]
        }
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        all_health = self._get_all_health()
        total_services = len(all_health)
        healthy_services = sum(1 for h in all_health.values() if h.status == "healthy")
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
            "system_status": "healthy" if healthy_services == total_services else "degraded"
        }


# Global instance
health_monitor = HealthMonitor()


# Convenience functions
def check_service_health(service_name: str) -> ServiceHealth:
    """Check health of a specific service"""
    return health_monitor.do(f"check {service_name}")

def get_system_health() -> Dict[str, Any]:
    """Get overall system health"""
    return health_monitor.ask("system health")

def start_monitoring() -> str:
    """Start health monitoring"""
    return health_monitor.do("start monitoring")


if __name__ == "__main__":
    # Test the health monitor
    print("🏥 Testing Health Monitor...")
    
    # Check all services
    health_status = health_monitor.ask("all services")
    print(health_monitor.tell("discord", health_status))
    
    # Start monitoring
    result = health_monitor.do("start monitoring")
    print(f"Monitoring: {result}")