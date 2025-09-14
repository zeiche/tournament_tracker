#!/usr/bin/env python3
"""
local_bonjour.py - In-process Bonjour for polymorphic core
Local service discovery for polymorphic routines within the same process.
No network overhead - pure in-memory event system.
"""

from typing import Dict, List, Any, Optional, Callable
import threading
from collections import defaultdict
import time

class LocalBonjourAnnouncer:
    """
    In-process Bonjour announcer for polymorphic core services.
    Fast, local service discovery within the same Python process.
    """
    
    def __init__(self):
        self.services = {}  # service_name -> service_info
        self.listeners = defaultdict(list)  # service_name -> [callbacks]
        self.lock = threading.Lock()
        self.announcement_log = []  # For debugging

        # Check for quiet mode
        import os
        self._quiet_mode = os.environ.get('QUIET_MODE', '0') == '1'
        if not self._quiet_mode:
            print("🏠 Local Bonjour announcer started (process-local only)")

        # Announce ourselves as a queryable service
        self.announce(
            "BonjourRegistry",
            ["Provides bonjour service registry", "Supports ask(), tell(), do() methods"],
            examples=["ask('list all services')", "ask('find service X')"]
        )

        # Register cleanup on exit
        import atexit
        atexit.register(self.cleanup)
    
    def announce(self, service_name: str, capabilities: List[str], examples: List[str] = None):
        """Announce a service locally within this process"""
        with self.lock:
            service_info = {
                'name': service_name,
                'capabilities': capabilities,
                'examples': examples or [],
                'announced_at': time.time(),
                'pid': threading.current_thread().ident
            }

            self.services[service_name] = service_info
            self.announcement_log.append({
                'action': 'announce',
                'service': service_name,
                'timestamp': time.time()
            })

            # Ultra-thin database reference (just pointer to RAM)
            self._register_pointer(service_name)

            # Notify listeners
            for callback in self.listeners[service_name]:
                try:
                    callback(service_info)
                except Exception as e:
                    print(f"⚠️  Local Bonjour listener error: {e}")

            if not self._quiet_mode:
                print(f"🏠 Local: {service_name}")

    def _register_pointer(self, service_name: str):
        """Register ultra-thin top-level pointer only - drilling goes to RAM"""
        try:
            import sqlite3
            import os

            db_path = os.path.join(os.getcwd(), 'tournament_tracker.db')
            with sqlite3.connect(db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS service_directory (
                        service_name TEXT PRIMARY KEY,
                        process_id INTEGER
                    )
                ''')

                # Only store: "service X exists in process Y"
                # All details/drilling goes to live RAM
                conn.execute('''
                    INSERT OR REPLACE INTO service_directory
                    (service_name, process_id)
                    VALUES (?, ?)
                ''', (service_name, os.getpid()))

                conn.commit()
        except Exception:
            pass
    
    def discover(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Discover a service locally"""
        with self.lock:
            return self.services.get(service_name)
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all services - use running process server if available"""
        with self.lock:
            # If we have services, return them (we're the server)
            if self.services:
                return self.services.copy()

            # If empty, we're a client - find server via database pointers
            server_pid = self._find_server_process()
            if server_pid:
                try:
                    from polymorphic_core.service_locator import get_service
                    remote_bonjour = get_service("bonjour", prefer_network=True)
                    if remote_bonjour and remote_bonjour != self:
                        # Ask the server process for live RAM data
                        return remote_bonjour.ask("list all services")
                except Exception:
                    pass

            # No server running - return empty (this process will become server)
            return {}

    def _find_server_process(self) -> Optional[int]:
        """Find which process has the services using database pointers"""
        try:
            import sqlite3
            import os

            db_path = os.path.join(os.getcwd(), 'tournament_tracker.db')
            if not os.path.exists(db_path):
                return None

            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute('''
                    SELECT DISTINCT process_id FROM service_directory
                    LIMIT 1
                ''')
                row = cursor.fetchone()
                if row:
                    pid = row[0]
                    # Quick check if process is still alive
                    try:
                        os.kill(pid, 0)  # Signal 0 just checks if process exists
                        return pid
                    except OSError:
                        # Process dead, clean up directory entries
                        conn.execute('DELETE FROM service_directory WHERE process_id = ?', (pid,))
                        conn.commit()
                return None
        except Exception:
            return None

    # No persistence needed - use running process server
    
    def add_listener(self, service_name: str, callback: Callable):
        """Add listener for service announcements"""
        with self.lock:
            self.listeners[service_name].append(callback)
    
    def remove_listener(self, service_name: str, callback: Callable):
        """Remove service announcement listener"""
        with self.lock:
            if callback in self.listeners[service_name]:
                self.listeners[service_name].remove(callback)
    
    # No caching - RAM is single source of truth

    def ask(self, query: str) -> Any:
        """Query the bonjour registry"""
        query_lower = query.lower().strip()

        if 'list all services' in query_lower or 'all services' in query_lower:
            return self.services.copy()
        elif 'find service' in query_lower:
            # Extract service name from query
            parts = query.split()
            if len(parts) > 2:
                service_name = parts[-1]
                return self.services.get(service_name)
        elif 'switches' in query_lower or 'goswitch' in query_lower:
            return {name: info for name, info in self.services.items()
                   if name.startswith('GoSwitch')}
        else:
            return self.services.copy()

    def tell(self, format_type: str, data=None) -> str:
        """Format bonjour data for output"""
        services = data or self.services

        if format_type.lower() == 'json':
            import json
            return json.dumps(services, indent=2, default=str)
        elif format_type.lower() == 'text':
            lines = [f"Services ({len(services)}):"]
            for name, info in services.items():
                caps = ', '.join(info.get('capabilities', [])[:2])  # First 2 caps
                lines.append(f"  {name}: {caps}")
            return '\n'.join(lines)
        else:
            return str(services)

    def do(self, action: str) -> Any:
        """Perform bonjour registry actions"""
        action_lower = action.lower().strip()

        if 'cleanup' in action_lower or 'clear' in action_lower:
            return self.cleanup()
        elif 'stats' in action_lower:
            return {
                'total_services': len(self.services),
                'switches': len([s for s in self.services if s.startswith('GoSwitch')]),
                'announcement_log_size': len(self.announcement_log)
            }
        else:
            return f"Unknown action: {action}"

    def cleanup(self):
        """Clean shutdown - just clear RAM (no persistence needed)"""
        with self.lock:
            services_count = len(self.services)
            self.services.clear()
            self.listeners.clear()
            if not self._quiet_mode:
                print(f"🏠 Local Bonjour cleaned up ({services_count} services)")

# Create global local announcer for polymorphic core
local_announcer = LocalBonjourAnnouncer()

__all__ = ['local_announcer', 'LocalBonjourAnnouncer']