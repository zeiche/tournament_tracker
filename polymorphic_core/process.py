#!/usr/bin/env python3
"""
Process Management for Tournament Tracker Services
LEGACY WRAPPER - Now bridges to the new unified service identity system
"""

import os
import subprocess
import signal
import psutil
import time
from typing import List, Optional
from polymorphic_core.local_bonjour import local_announcer
from logging_services.polymorphic_log_manager import PolymorphicLogManager

# Import new unified system
try:
    from polymorphic_core.service_identity import ProcessKiller, ServiceManager
    UNIFIED_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_SYSTEM_AVAILABLE = False

class ProcessManager:
    """Manages service processes with duplicate prevention"""
    
    @staticmethod
    def find_processes_by_script(script_name: str) -> List[int]:
        """Find all PIDs running a specific script using simple ps and grep"""
        pids = []
        try:
            # Use simple shell command: ps aux | grep script_name | grep -v grep
            result = subprocess.run(
                f"ps aux | grep '{script_name}' | grep -v grep | awk '{{print $2}}'",
                shell=True, capture_output=True, text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            pids.append(int(line.strip()))
                        except ValueError:
                            continue
                            
        except Exception as e:
            print(f"Error finding processes: {e}")
            
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
                local_announcer.announce(
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
            local_announcer.announce(
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
            local_announcer.announce(
                "ProcessManager", 
                [f"Found {len(pids)} processes matching '{pattern}'"]
            )
            return ProcessManager.kill_processes(pids, force)
        return 0
    
    @staticmethod
    def start_service_safe(script_path: str, *args, check_existing: bool = True) -> subprocess.Popen:
        """Start a service with duplicate checking and crash monitoring"""
        if check_existing:
            script_name = os.path.basename(script_path)
            existing = ProcessManager.find_processes_by_script(script_name)

            if existing:
                local_announcer.announce(
                    "ProcessManager",
                    [f"Killing {len(existing)} existing {script_name} processes"]
                )
                ProcessManager.kill_processes(existing)
                time.sleep(1)  # Give processes time to die

        # Start new process with crash interception
        cmd = ['python3', script_path] + list(args)
        script_name = os.path.basename(script_path)
        log_file = f'{script_name.replace(".py", "")}.log'

        # Start process with crash monitoring
        proc = ProcessManager._start_with_crash_monitor(cmd, log_file, script_name)

        local_announcer.announce(
            "ProcessManager",
            [f"Started {script_name} as PID {proc.pid} with crash monitoring"]
        )

        return proc

    @staticmethod
    def _start_with_crash_monitor(cmd: list, log_file: str, script_name: str) -> subprocess.Popen:
        """Start process with real-time crash monitoring and logging"""
        import threading

        # Prepare environment for subprocess - inherit from go.py but ensure execution guard bypass
        env = os.environ.copy()
        env['BYPASS_EXECUTION_GUARD'] = 'true'  # Allow go.py-initiated subprocesses

        # Start the process with pipes for real-time monitoring
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )

        # Start crash monitoring thread
        def monitor_output():
            crash_buffer = []
            in_traceback = False

            try:
                # Initialize database logging
                log_manager = PolymorphicLogManager()

                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break

                    # Log to database instead of file
                    try:
                        log_manager.do(f"log info [{script_name}] {line.strip()}")
                    except:
                        pass  # Don't let logging errors break monitoring

                        # Monitor for crashes
                        line_stripped = line.strip()

                        if 'Traceback (most recent call last):' in line:
                            in_traceback = True
                            crash_buffer = [line_stripped]
                        elif in_traceback:
                            crash_buffer.append(line_stripped)

                            # Check if traceback ended
                            if line_stripped and not line.startswith(' ') and not line.startswith('  '):
                                # This is the error line, traceback is complete
                                ProcessManager._log_crash(script_name, crash_buffer)
                                in_traceback = False
                                crash_buffer = []
                        elif any(error in line for error in ['Error:', 'ERROR:', 'FATAL:', 'Exception:']):
                            # Single-line errors
                            ProcessManager._log_crash(script_name, [line_stripped])

            except Exception as e:
                print(f"Crash monitor error for {script_name}: {e}")

        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_output, daemon=True)
        monitor_thread.start()

        return proc

    @staticmethod
    def _log_crash(script_name: str, crash_lines: list):
        """Log subprocess crash to main logging system"""
        crash_text = '\n'.join(crash_lines)

        # Log to console immediately
        print(f"\n🚨 SUBPROCESS CRASH: {script_name}")
        print(f"📍 Crash details:\n{crash_text}\n")

        # Log to database via PolymorphicLogManager
        try:
            log_manager = PolymorphicLogManager()
            log_manager.do(f"log error 🚨 SUBPROCESS CRASH: {script_name}")
            log_manager.do(f"log error 📍 Crash details:\n{crash_text}")
        except:
            pass

    
    @staticmethod
    def restart_service(script_path: str, *args) -> subprocess.Popen:
        """Restart a service (kill existing + start new)"""
        return ProcessManager.start_service_safe(script_path, *args, check_existing=True)
    
    @staticmethod
    def find_processes_by_port(port: int) -> List[int]:
        """Find processes listening on a specific port"""
        pids = []
        try:
            # Use sudo lsof for reliable port detection (can see all processes)
            result = subprocess.run(['sudo', 'lsof', '-ti', f':{port}'],
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
            # Fallback to ss if lsof not available
            try:
                result = subprocess.run(['ss', '-tlnp'],
                                      capture_output=True, text=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if f':{port} ' in line and 'LISTEN' in line:
                        # ss output format: LISTEN 0 5 10.0.0.1:8081 0.0.0.0:* users:(("python3",pid=12345,fd=4))
                        if 'users:(' in line:
                            users_part = line.split('users:(')[1]
                            # Extract PID from users:(("python3",pid=12345,fd=4))
                            if 'pid=' in users_part:
                                pid_part = users_part.split('pid=')[1].split(',')[0]
                                try:
                                    pid = int(pid_part)
                                    if pid not in pids:
                                        pids.append(pid)
                                except ValueError:
                                    continue
            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                # Final fallback - aggressive search using fuser
                try:
                    result = subprocess.run(['fuser', f'{port}/tcp'],
                                          capture_output=True, text=True, timeout=5)
                    if result.stdout.strip():
                        for pid_str in result.stdout.strip().split():
                            try:
                                pid = int(pid_str)
                                if pid not in pids:
                                    pids.append(pid)
                            except ValueError:
                                continue
                except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
                    # Ultimate fallback - pattern matching
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
            local_announcer.announce(
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
    
    # ========================================================================
    # UNIFIED SYSTEM BRIDGE METHODS
    # ========================================================================
    
    @staticmethod
    def status():
        """Show service status using unified system if available"""
        if UNIFIED_SYSTEM_AVAILABLE:
            return ServiceManager.status()
        else:
            # Fallback to legacy method
            processes = ProcessManager.list_tournament_processes()
            if processes:
                print("Legacy Process Status:")
                for pattern, pids in processes.items():
                    print(f"  {pattern}: {len(pids)} processes ({pids})")
            else:
                print("No tournament processes found")
    
    @staticmethod
    def restart_all_services():
        """Restart all services using unified system if available"""
        if UNIFIED_SYSTEM_AVAILABLE:
            return ServiceManager.restart_all()
        else:
            # Fallback to legacy method
            print("⚠️  Using legacy restart method")
            patterns = ['web_editor', 'discord', 'bonjour']
            killed = 0
            for pattern in patterns:
                killed += ProcessManager.kill_by_pattern(pattern)
            return killed
    
    @staticmethod
    def kill_service_by_name(service_name: str):
        """Kill a service by name using unified system if available"""
        if UNIFIED_SYSTEM_AVAILABLE:
            return ProcessKiller.kill_service(service_name)
        else:
            # Fallback to pattern matching
            return ProcessManager.kill_by_pattern(service_name) > 0

# ProcessManager capabilities announced by individual process managers
# (removed module-level announcement to prevent duplicates)