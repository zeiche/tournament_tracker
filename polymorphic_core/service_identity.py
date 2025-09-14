"""
Service Identity System - Unified process management with database backing
"""
import os
import signal
import setproctitle
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

from database.tournament_models import ServiceState, get_session
from logging_services.polymorphic_log_manager import PolymorphicLogManager


class ManagedService(ABC):
    """Base class for all managed services that register in the database"""
    
    def __init__(self, service_name: str, process_title: Optional[str] = None):
        self.service_name = service_name
        self.process_title = process_title or f"tournament-{service_name}"
        self._registered = False
        self._pid = None
    
    def register(self, **extra_data):
        """Register this service in the database and set process title"""
        if self._registered:
            return
            
        # Set process title for ps visibility
        setproctitle.setproctitle(self.process_title)
        self._pid = os.getpid()
        
        # Store in database
        with get_session() as session:
            data = {
                'process_title': self.process_title,
                'registered_at': datetime.utcnow().isoformat(),
                **extra_data
            }
            ServiceState.register_service(session, self.service_name, self._pid, data)
        
        self._registered = True
        print(f"🔧 Service '{self.service_name}' registered with PID {self._pid}")
        
    def unregister(self):
        """Unregister this service from the database"""
        if not self._registered:
            return
            
        with get_session() as session:
            ServiceState.stop_service(session, self.service_name)
        
        self._registered = False
        print(f"🔧 Service '{self.service_name}' unregistered")
    
    def __enter__(self):
        self.register()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unregister()
    
    @abstractmethod
    def run(self):
        """Service implementation - must be implemented by subclass"""
        pass
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current service state from database"""
        with get_session() as session:
            state = ServiceState.get_service_state(session, self.service_name)
            return state.to_dict() if state else None


class ProcessKiller:
    """Utility class to hunt down and kill processes using database AND process discovery"""
    
    @staticmethod
    def find_processes_by_pattern(pattern: str) -> List[Dict[str, Any]]:
        """Find running processes by command line pattern"""
        import subprocess
        processes = []
        
        try:
            # Use ps to find processes matching pattern
            cmd = ['ps', 'aux']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if pattern in line and 'grep' not in line:
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        processes.append({
                            'user': parts[0],
                            'pid': int(parts[1]),
                            'cpu': parts[2],
                            'mem': parts[3],
                            'command': parts[10]
                        })
        except Exception as e:
            print(f"⚠️  Process discovery failed: {e}")
        
        return processes
    
    @staticmethod
    def find_tournament_processes() -> List[Dict[str, Any]]:
        """Find all processes related to tournament tracker"""
        patterns = [
            'tournament-',  # Our process titles
            'tournament_tracker/',  # Path-based
            'polymorphic_web_editor',
            'discord_bot',
            'claude_cli_service',
            'interactive_service',
            'startgg_sync'
        ]
        
        all_processes = []
        for pattern in patterns:
            processes = ProcessKiller.find_processes_by_pattern(pattern)
            all_processes.extend(processes)
        
        # Remove duplicates by PID
        seen_pids = set()
        unique_processes = []
        for proc in all_processes:
            if proc['pid'] not in seen_pids:
                seen_pids.add(proc['pid'])
                unique_processes.append(proc)
        
        return unique_processes
    
    @staticmethod
    def kill_service(service_name: str, signal_type: int = signal.SIGTERM) -> bool:
        """Kill a service by name using database PID lookup OR process discovery"""
        killed = False
        
        # Method 1: Try database PID lookup first
        with get_session() as session:
            pid = ServiceState.get_service_pid(session, service_name)
            if pid:
                try:
                    os.kill(pid, signal_type)
                    ServiceState.stop_service(session, service_name)
                    print(f"💀 Killed service '{service_name}' (PID {pid}) via database")
                    killed = True
                except ProcessLookupError:
                    ServiceState.stop_service(session, service_name)
                    print(f"⚰️  Service '{service_name}' was already dead, cleaned up database")
                except PermissionError:
                    print(f"❌ Permission denied killing service '{service_name}' (PID {pid})")
                    return False
        
        # Method 2: If database lookup failed, try process discovery
        if not killed:
            print(f"🔍 Database lookup failed, searching for '{service_name}' processes...")
            processes = ProcessKiller.find_processes_by_pattern(f'tournament-{service_name}')
            
            # Also try pattern matching on service name
            if not processes:
                processes = ProcessKiller.find_processes_by_pattern(service_name)
            
            for proc in processes:
                try:
                    os.kill(proc['pid'], signal_type)
                    print(f"💀 Killed process (PID {proc['pid']}) via discovery: {proc['command'][:80]}...")
                    killed = True
                except (ProcessLookupError, PermissionError) as e:
                    print(f"⚠️  Could not kill PID {proc['pid']}: {e}")
        
        if not killed:
            print(f"❌ No processes found for service '{service_name}'")
        
        return killed
    
    @staticmethod
    def kill_all_services(signal_type: int = signal.SIGTERM) -> int:
        """Nuclear option - kill all managed services"""
        killed_count = 0
        
        with get_session() as session:
            running_services = ServiceState.get_all_running_services(session)
            
            if not running_services:
                print("ℹ️  No running services found")
                return 0
                
            print(f"💥 Killing {len(running_services)} running services...")
            
            for state in running_services:
                try:
                    os.kill(state.pid, signal_type)
                    print(f"💀 Killed {state.service_name} (PID {state.pid})")
                    killed_count += 1
                except ProcessLookupError:
                    print(f"⚰️  {state.service_name} was already dead")
                except PermissionError:
                    print(f"❌ Permission denied killing {state.service_name} (PID {state.pid})")
                
                # Clean up database entry
                state.status = 'stopped'
                state.pid = None
            
            session.commit()
            
        return killed_count
    
    @staticmethod
    def list_services() -> List[Dict[str, Any]]:
        """List all services with their current status"""
        with get_session() as session:
            all_services = session.query(ServiceState).all()
            return [service.to_dict() for service in all_services]
    
    @staticmethod
    def cleanup_dead_processes() -> int:
        """Remove database entries for processes that no longer exist"""
        with get_session() as session:
            cleaned = ServiceState.cleanup_dead_processes(session)
            if cleaned > 0:
                print(f"🧹 Cleaned up {cleaned} dead process entries")
            return cleaned
    
    @staticmethod
    def force_kill_service(service_name: str) -> bool:
        """Force kill a service with SIGKILL"""
        return ProcessKiller.kill_service(service_name, signal.SIGKILL)
    
    @staticmethod
    def restart_service(service_name: str, start_func=None):
        """Kill existing service and optionally restart it"""
        killed = ProcessKiller.kill_service(service_name)
        
        if start_func:
            print(f"🔄 Restarting service '{service_name}'...")
            start_func()
            
        return killed


class ServiceManager:
    """High-level service management interface"""
    
    @staticmethod
    def status():
        """Print status of all services - database AND discovered processes with port info"""
        import subprocess
        import time
        import os

        def get_ports_for_pid(pid):
            """Get listening ports for a given PID"""
            try:
                # Use ss to find ports for this PID
                result = subprocess.run(['ss', '-tulpn'], capture_output=True, text=True)
                ports = []
                for line in result.stdout.split('\n'):
                    if f'pid={pid},' in line:
                        # Extract port from the line (format: 0.0.0.0:PORT or *:PORT)
                        parts = line.split()
                        if len(parts) >= 4:
                            local_addr = parts[3]
                            if ':' in local_addr:
                                port = local_addr.split(':')[-1]
                                if port.isdigit():
                                    ports.append(port)
                return sorted(set(ports))
            except:
                return []

        def check_system_health():
            """Check if system appears to need go.py to be run"""
            issues = []

            # Check if go.py has been run recently (environment variable would be set)
            go_py_running = os.environ.get('GO_PY_EXECUTION') == 'true'

            # Check system uptime to see if server was recently rebooted
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                uptime_hours = uptime_seconds / 3600

                if uptime_hours < 0.5:  # Less than 30 minutes uptime
                    issues.append(f"🔄 Server recently rebooted ({uptime_hours:.1f}h ago)")
            except:
                pass

            # Check if no services are running
            db_services = ProcessKiller.list_services()
            discovered_processes = ProcessKiller.find_tournament_processes()
            active_services = [s for s in db_services if s['is_running']]

            if not active_services and not discovered_processes:
                issues.append("⚠️  No tournament services are currently running")

            if not go_py_running and issues:
                issues.append("💡 Consider running: ./go.py --web or ./go.py --discord-bot")

            return issues

        # Get database services
        db_services = ProcessKiller.list_services()

        # Get discovered processes
        discovered_processes = ProcessKiller.find_tournament_processes()

        print(f"\n📊 Tournament Tracker Process Status")
        print("=" * 80)

        # Check for system health issues
        health_issues = check_system_health()
        if health_issues:
            print(f"\n🚨 System Health Alerts:")
            for issue in health_issues:
                print(f"  {issue}")
            print()

        # Show database-tracked services
        if db_services:
            print(f"\n🗄️  Database-tracked services ({len(db_services)}):")
            for service in db_services:
                status_icon = "🟢" if service['is_running'] else "🔴"
                uptime = f" (up {int(service['uptime_seconds'] or 0)}s)" if service['is_running'] else ""

                # Get port information if running
                ports_info = ""
                if service['is_running'] and service['pid']:
                    ports = get_ports_for_pid(service['pid'])
                    if ports:
                        ports_info = f" → ports: {','.join(ports)}"

                print(f"  {status_icon} {service['service_name']} - PID {service['pid'] or 'None'}{uptime}{ports_info}")

        # Show discovered processes
        if discovered_processes:
            print(f"\n🔍 Discovered processes ({len(discovered_processes)}):")
            for proc in discovered_processes:
                # Get port information
                ports = get_ports_for_pid(proc['pid'])
                ports_info = f" → ports: {','.join(ports)}" if ports else ""
                print(f"  🐍 PID {proc['pid']} - {proc['command'][:60]}...{ports_info}")

        if not db_services and not discovered_processes:
            print("ℹ️  No tournament tracker processes found")
        
        # Clean up dead processes
        ProcessKiller.cleanup_dead_processes()

    @staticmethod
    def watchdog():
        """Watchdog mode: check services and auto-restart failed ones"""
        import subprocess
        import os

        # Get logger instance
        log_manager = PolymorphicLogManager()

        # Check system health first
        def check_system_health():
            """Check if system appears to need go.py to be run"""
            issues = []
            go_py_running = os.environ.get('GO_PY_EXECUTION') == 'true'

            # Check system uptime
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                uptime_hours = uptime_seconds / 3600
                if uptime_hours < 0.5:
                    issues.append(f"Server recently rebooted ({uptime_hours:.1f}h ago)")
            except:
                pass

            # Check if no services are running
            db_services = ProcessKiller.list_services()
            discovered_processes = ProcessKiller.find_tournament_processes()
            active_services = [s for s in db_services if s['is_running']]

            if not active_services and not discovered_processes:
                issues.append("No tournament services running")

            return issues, not go_py_running

        issues, needs_restart = check_system_health()
        restart_count = 0

        log_manager.info(f"🐕 Service Watchdog - {len(issues)} issues detected")

        if issues:
            for issue in issues:
                log_manager.warning(f"  ⚠️  {issue}")

        # Auto-restart critical services - always check essential services
        log_manager.info(f"🔄 Checking essential services...")

        # Always check these critical services regardless of go.py execution status
        if True:  # Always check essential services

            # Start Discord bot if not running
            try:
                result = subprocess.run(['pgrep', '-f', 'discord'], capture_output=True)
                if result.returncode != 0:  # No Discord processes found
                    log_manager.info("  🤖 Starting Discord bot...")
                    subprocess.Popen([
                        '/home/ubuntu/claude/tournament_tracker/go.py', '--discord-bot'
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    restart_count += 1
            except:
                pass

            # Start web editor if not running
            try:
                result = subprocess.run(['pgrep', '-f', 'web.*editor'], capture_output=True)
                if result.returncode != 0:  # No web editor processes found
                    log_manager.info("  🌐 Starting web editor...")
                    subprocess.Popen([
                        '/home/ubuntu/claude/tournament_tracker/go.py', '--web'
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    restart_count += 1
            except:
                pass

            # Start WebDAV if not running
            try:
                # Check if port 8443 is listening (WebDAV port)
                port_result = subprocess.run(['ss', '-tulpn'], capture_output=True, text=True)
                if ':8443' not in port_result.stdout:  # Port 8443 not in use
                    log_manager.info("  📁 Starting WebDAV service...")
                    subprocess.Popen([
                        '/home/ubuntu/claude/tournament_tracker/go.py', '--webdav-refactored'
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    restart_count += 1
            except:
                pass

        if restart_count > 0:
            log_manager.info(f"✅ Watchdog restarted {restart_count} services")
            return 0
        elif issues:
            log_manager.info("ℹ️  Issues detected but no restarts needed")
            return 1
        else:
            log_manager.info("✅ All services healthy")
            return 0

    @staticmethod
    def restart_all():
        """Restart all services (kill all, but don't auto-restart)"""
        killed = ProcessKiller.kill_all_services()
        ProcessKiller.cleanup_dead_processes()
        print(f"🔄 Killed {killed} services. Use go.py commands to restart them.")
        return killed


# Convenience context manager for quick service registration
@contextmanager
def managed_service(service_name: str, **extra_data):
    """Context manager for quick service registration without subclassing"""
    
    class SimpleService(ManagedService):
        def run(self):
            pass  # No-op for context manager usage
    
    service = SimpleService(service_name)
    try:
        service.register(**extra_data)
        yield service
    finally:
        service.unregister()


# Module-level convenience functions
def register_service(service_name: str, **extra_data):
    """Register a service without context manager"""
    service = type('Service', (ManagedService,), {'run': lambda self: None})(service_name)
    service.register(**extra_data)
    return service

def kill_service(service_name: str) -> bool:
    """Kill a service by name"""
    return ProcessKiller.kill_service(service_name)

def kill_all_services() -> int:
    """Kill all services"""
    return ProcessKiller.kill_all_services()

def service_status():
    """Print service status"""
    ServiceManager.status()

def restart_all_services() -> int:
    """Restart all services"""
    return ServiceManager.restart_all()