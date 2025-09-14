#!/usr/bin/env python3
"""
Process Management Mixin for Self-Managing Services
Allows services to announce and manage their own processes
"""

import time
from typing import List
from .local_bonjour import local_announcer
from .process import ProcessManager

class ProcessManagementMixin:
    """Mixin for services that manage their own processes"""
    
    def announce_process_management(self, service_name: str, processes: List[str], 
                                  ports: List[int], cleanup_method: str = "cleanup_processes"):
        """Announce this service's process management capabilities"""
        capabilities = [
            f"I manage processes: {', '.join(processes)}",
            f"I use ports: {', '.join(map(str, ports))}" if ports else "I use no specific ports",
            f"Call {cleanup_method} to clean shutdown",
            "I am a PROCESS_MANAGER service"
        ]
        
        local_announcer.announce(f"{service_name}ProcessManager", capabilities)
    
    def cleanup_processes(self):
        """Override in subclasses to implement cleanup logic"""
        raise NotImplementedError("Subclasses must implement cleanup_processes()")
    
    def start_services(self):
        """Override in subclasses to implement startup logic"""
        raise NotImplementedError("Subclasses must implement start_services()")

class BaseProcessManager(ProcessManagementMixin):
    """Base class for process managers with common patterns"""
    
    PROCESSES: List[str] = []
    PORTS: List[int] = []
    SERVICE_NAME: str = ""
    
    def __init__(self):
        if not self.SERVICE_NAME:
            raise ValueError("SERVICE_NAME must be set in subclass")
        
        self.announce_process_management(
            self.SERVICE_NAME, 
            self.PROCESSES, 
            self.PORTS
        )
    
    def cleanup_processes(self):
        """Standard cleanup: kill processes by script name and port"""
        killed_total = 0
        
        # Kill processes by script name
        for process in self.PROCESSES:
            script_name = process.split('/')[-1]  # Get filename from path
            killed = ProcessManager.kill_script(script_name)
            killed_total += killed
        
        # Kill processes by port
        for port in self.PORTS:
            killed = ProcessManager.kill_port(port)
            killed_total += killed
        
        if killed_total > 0:
            local_announcer.announce(
                f"{self.SERVICE_NAME}ProcessManager",
                [f"Cleaned up {killed_total} processes"]
            )
        
        return killed_total
    
    def start_services(self):
        """Standard startup: cleanup then start all processes"""
        # Clean up first
        self.cleanup_processes()
        
        # Wait for processes to die and ports to be released
        time.sleep(1)
        
        # Start all processes
        started_pids = []
        for process in self.PROCESSES:
            try:
                proc = ProcessManager.start_service_safe(process, check_existing=False)
                started_pids.append(proc.pid)
            except Exception as e:
                local_announcer.announce(
                    f"{self.SERVICE_NAME}ProcessManager",
                    [f"Failed to start {process}: {e}"]
                )
        
        if started_pids:
            local_announcer.announce(
                f"{self.SERVICE_NAME}ProcessManager", 
                [f"Started {len(started_pids)} processes: {started_pids}"]
            )
        
        return started_pids