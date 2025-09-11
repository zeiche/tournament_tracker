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
        """Find all PIDs running a specific script (filters out temporary commands)"""
        pids = []
        try:
            for proc in psutil.process_iter(['pid', 'cmdline', 'ppid', 'name']):
                cmdline = proc.info['cmdline']
                if not cmdline or not any(script_name in arg for arg in cmdline):
                    continue
                
                cmd_str = ' '.join(cmdline)
                
                # Skip grep/pgrep commands
                if any(grep in cmd_str for grep in ['grep', 'pgrep']):
                    continue
                
                # Skip bash wrapper commands (temporary Claude Code executions)
                if any(wrapper in cmd_str for wrapper in ['bash -c', 'eval', 'python3 -c']):
                    continue
                
                # Skip if parent process is bash and command is embedded in a larger script
                try:
                    parent = psutil.Process(proc.info['ppid'])
                    if parent.name() == 'bash' and len(cmd_str) > 200:  # Long embedded commands
                        continue
                except:
                    pass
                
                # Only include direct python script executions
                if (proc.info['name'] in ['python3', 'python'] and 
                    len(cmdline) >= 2 and 
                    script_name in cmdline[1]):
                    pids.append(proc.info['pid'])
                        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return pids
    
    @staticmethod  
    def find_processes_by_pattern(pattern: str) -> List[int]:
        """Find processes matching a pattern in command line (filters out temporary commands)"""
        pids = []
        try:
            # Use pgrep first for speed
            result = subprocess.run(['pgrep', '-f', pattern], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                candidate_pids = [int(pid) for pid in result.stdout.strip().split('\n')]
                
                # Filter out temporary/wrapper commands
                for pid in candidate_pids:
                    try:
                        proc = psutil.Process(pid)
                        cmdline = proc.cmdline()
                        if not cmdline:
                            continue
                            
                        cmd_str = ' '.join(cmdline)
                        
                        # Skip bash wrapper commands (temporary Claude Code executions)
                        if any(wrapper in cmd_str for wrapper in ['bash -c', 'eval', 'python3 -c']):
                            continue
                            
                        # Skip if parent process is bash and command is very long (embedded)
                        try:
                            parent = psutil.Process(proc.ppid())
                            if parent.name() == 'bash' and len(cmd_str) > 200:
                                continue
                        except:
                            pass
                            
                        pids.append(pid)
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # If we can't check the process, include it (conservative approach)
                        pids.append(pid)
                        
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
                
                # Additional safety: verify this is actually a service we should kill
                try:
                    proc = psutil.Process(pid)
                    cmdline = proc.cmdline()
                    if not cmdline:
                        continue
                        
                    # Only kill Python processes that look like services
                    if not (proc.name() in ['python3', 'python'] and len(cmdline) >= 2):
                        continue
                        
                    # Extra safety: don't kill system Python processes
                    cmd_str = ' '.join(cmdline)
                    if any(sys_pattern in cmd_str for sys_pattern in ['/usr/', 'unattended-upgrade', 'apt']):
                        continue
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # If we can't verify it's safe, skip it
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
        
        # Start new process with output redirected to log file
        cmd = ['python3', script_path] + list(args)
        log_file = f'/tmp/{os.path.basename(script_path)}.log'
        with open(log_file, 'w') as f:
            proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
        
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
            # Use lsof for reliable port detection
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.stdout.strip():
                for pid_str in result.stdout.strip().split('\n'):
                    try:
                        pid = int(pid_str)
                        if pid not in pids:
                            pids.append(pid)
                    except ValueError:
                        continue
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback to netstat if lsof not available
            try:
                result = subprocess.run(['netstat', '-tlnp'], 
                                      capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if f':{port} ' in line and 'LISTEN' in line:
                        parts = line.split()
                        for part in parts:
                            if '/' in part:
                                try:
                                    pid = int(part.split('/')[0])
                                    if pid not in pids:
                                        pids.append(pid)
                                except ValueError:
                                    continue
            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                # Final fallback - pattern matching
                try:
                    all_processes = ProcessManager.find_processes_by_pattern(f'python.*{port}')
                    pids.extend(all_processes)
                except:
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

# ProcessManager capabilities announced by individual process managers
# (removed module-level announcement to prevent duplicates)