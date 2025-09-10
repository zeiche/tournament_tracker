#!/usr/bin/env python3
"""
Process Management for Tournament Tracker Services
Handles starting, stopping, and checking processes with duplicate prevention
"""

import os
import subprocess
import signal
import psutil
import time
from typing import List, Optional
from polymorphic_core import announcer

class ProcessManager:
    """Manages service processes with duplicate prevention"""
    
    @staticmethod
    def find_processes_by_script(script_name: str) -> List[int]:
        """Find all PIDs running a specific script"""
        pids = []
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                cmdline = proc.info['cmdline']
                if cmdline and any(script_name in arg for arg in cmdline):
                    # Exclude grep/pgrep commands themselves
                    if not any(grep in ' '.join(cmdline) for grep in ['grep', 'pgrep']):
                        pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return pids
    
    @staticmethod  
    def find_processes_by_pattern(pattern: str) -> List[int]:
        """Find processes matching a pattern in command line"""
        pids = []
        try:
            result = subprocess.run(['pgrep', '-f', pattern], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pids = [int(pid) for pid in result.stdout.strip().split('\n')]
        except (subprocess.SubprocessError, ValueError):
            pass
        return pids
    
    @staticmethod
    def kill_processes(pids: List[int], force: bool = False) -> int:
        """Kill processes by PID list. Returns count of killed processes."""
        killed = 0
        signal_type = signal.SIGKILL if force else signal.SIGTERM
        
        for pid in pids:
            try:
                # Skip our own process
                if pid == os.getpid():
                    continue
                    
                os.kill(pid, signal_type)
                killed += 1
                announcer.announce(
                    "ProcessManager", 
                    [f"Killed process {pid} ({'force' if force else 'graceful'})"]
                )
            except (ProcessLookupError, PermissionError):
                # Process already dead or no permission
                pass
        
        return killed
    
    @staticmethod
    def kill_script(script_name: str, force: bool = False) -> int:
        """Kill all processes running a specific script"""
        pids = ProcessManager.find_processes_by_script(script_name)
        if pids:
            announcer.announce(
                "ProcessManager",
                [f"Found {len(pids)} processes running {script_name}"]
            )
            return ProcessManager.kill_processes(pids, force)
        return 0
    
    @staticmethod
    def kill_pattern(pattern: str, force: bool = False) -> int:
        """Kill all processes matching a pattern"""
        pids = ProcessManager.find_processes_by_pattern(pattern)
        if pids:
            announcer.announce(
                "ProcessManager", 
                [f"Found {len(pids)} processes matching '{pattern}'"]
            )
            return ProcessManager.kill_processes(pids, force)
        return 0
    
    @staticmethod
    def start_service_safe(script_path: str, *args, check_existing: bool = True) -> subprocess.Popen:
        """Start a service with duplicate checking"""
        if check_existing:
            script_name = os.path.basename(script_path)
            existing = ProcessManager.find_processes_by_script(script_name)
            
            if existing:
                announcer.announce(
                    "ProcessManager",
                    [f"Killing {len(existing)} existing {script_name} processes"]
                )
                ProcessManager.kill_processes(existing)
                time.sleep(1)  # Give processes time to die
        
        # Start new process
        cmd = ['python3', script_path] + list(args)
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        announcer.announce(
            "ProcessManager",
            [f"Started {os.path.basename(script_path)} as PID {proc.pid}"]
        )
        
        return proc
    
    @staticmethod
    def restart_service(script_path: str, *args) -> subprocess.Popen:
        """Restart a service (kill existing + start new)"""
        return ProcessManager.start_service_safe(script_path, *args, check_existing=True)
    
    @staticmethod
    def find_processes_by_port(port: int) -> List[int]:
        """Find processes listening on a specific port"""
        pids = []
        try:
            # Use ss command to find processes by port
            result = subprocess.run(['ss', '-tulpn'], capture_output=True, text=True)
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if f':{port} ' in line or f':{port}\t' in line:
                        # Extract PID from ss output format: users:(("process",pid=12345,fd=3))
                        import re
                        pid_match = re.search(r'pid=(\d+)', line)
                        if pid_match:
                            pid = int(pid_match.group(1))
                            if pid not in pids:
                                pids.append(pid)
        except (subprocess.SubprocessError, ValueError):
            pass
        return pids
    
    @staticmethod
    def kill_port(port: int, force: bool = False) -> int:
        """Kill all processes listening on a specific port"""
        pids = ProcessManager.find_processes_by_port(port)
        if pids:
            announcer.announce(
                "ProcessManager",
                [f"Found {len(pids)} processes using port {port}"]
            )
            return ProcessManager.kill_processes(pids, force)
        return 0

    @staticmethod
    def list_tournament_processes() -> dict:
        """List all tournament tracker related processes"""
        patterns = [
            'web_editor', 'discord', 'bonjour', 'twilio', 'twiml', 
            'stream_server', 'bridge', 'lightweight'
        ]
        
        processes = {}
        for pattern in patterns:
            pids = ProcessManager.find_processes_by_pattern(pattern)
            if pids:
                processes[pattern] = pids
        
        return processes

# Announce the process manager
announcer.announce(
    "ProcessManager",
    [
        "Process management with duplicate prevention",
        "Safe service starting and stopping", 
        "Pattern-based process discovery",
        "Automatic cleanup of old processes"
    ]
)