#!/usr/bin/env python3
"""
database_singleton.py - Database-based singleton lock mechanism
Uses a system_locks table to ensure only one instance of a service can run.
No file system writes required.
"""

import os
import sys
import time
import signal
import logging
import psutil
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, create_engine
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.exc import IntegrityError, OperationalError

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.database_singleton")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class SystemLock(Base):
    """System lock table for managing singleton services"""
    __tablename__ = 'system_locks'
    
    service_name = Column(String(100), primary_key=True)
    pid = Column(Integer, nullable=False)
    hostname = Column(String(255), nullable=False)
    started_at = Column(DateTime, nullable=False)
    last_heartbeat = Column(DateTime, nullable=False)
    command_line = Column(String(1000))
    is_active = Column(Boolean, default=True)


class DatabaseSingleton:
    """Database-based singleton lock manager"""
    
    def __init__(self, service_name: str = 'discord_bot', db_path: str = None):
        """
        Initialize the database singleton lock.
        
        Args:
            service_name: Name of the service to lock (e.g., 'discord_bot')
            db_path: Path to the database file (defaults to tournament_tracker.db)
        """
        self.service_name = service_name
        self.pid = os.getpid()
        self.hostname = os.uname().nodename
        self.locked = False
        self.session = None
        self.heartbeat_thread = None
        
        # Setup database connection
        if not db_path:
            db_path = '/home/ubuntu/claude/tournament_tracker/tournament_tracker.db'
        
        self.engine = create_engine(f'sqlite:///{db_path}', 
                                   connect_args={'timeout': 30})
        
        # Create table if it doesn't exist
        Base.metadata.create_all(self.engine)
        
        # Register signal handlers for cleanup
        signal.signal(signal.SIGTERM, self._cleanup_handler)
        signal.signal(signal.SIGINT, self._cleanup_handler)
    
    def acquire_lock(self, force: bool = False) -> bool:
        """
        Attempt to acquire the lock for this service.
        
        Args:
            force: If True, forcefully take the lock even if another instance exists
            
        Returns:
            True if lock acquired, False otherwise
        """
        try:
            self.session = Session(self.engine)
            
            # Check for existing lock
            existing = self.session.query(SystemLock).filter_by(
                service_name=self.service_name
            ).first()
            
            if existing:
                # Check if the process is still alive
                if self._is_process_alive(existing.pid, existing.hostname):
                    # Check if heartbeat is recent (within 30 seconds)
                    if existing.last_heartbeat and \
                       (datetime.now() - existing.last_heartbeat).seconds < 30:
                        if not force:
                            logger.error(f"Service '{self.service_name}' is already running:")
                            logger.error(f"  PID: {existing.pid}")
                            logger.error(f"  Host: {existing.hostname}")
                            logger.error(f"  Started: {existing.started_at}")
                            logger.error(f"  Command: {existing.command_line}")
                            return False
                        else:
                            logger.warning(f"Force acquiring lock, killing PID {existing.pid}")
                            self._kill_process(existing.pid)
                
                # Process is dead or stale, remove the lock
                logger.info(f"Removing stale lock for PID {existing.pid}")
                self.session.delete(existing)
                self.session.commit()
            
            # Create new lock
            lock = SystemLock(
                service_name=self.service_name,
                pid=self.pid,
                hostname=self.hostname,
                started_at=datetime.now(),
                last_heartbeat=datetime.now(),
                command_line=self._get_command_line(),
                is_active=True
            )
            
            self.session.add(lock)
            self.session.commit()
            
            self.locked = True
            logger.info(f"Lock acquired for '{self.service_name}' (PID: {self.pid})")
            
            # Start heartbeat thread
            self._start_heartbeat()
            
            return True
            
        except IntegrityError:
            # Another process got the lock first
            logger.error(f"Could not acquire lock - another instance is starting")
            if self.session:
                self.session.rollback()
            return False
            
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            if self.session:
                self.session.rollback()
            return False
    
    def release_lock(self):
        """Release the lock for this service"""
        try:
            if self.session and self.locked:
                # Stop heartbeat
                self._stop_heartbeat()
                
                # Remove lock from database
                lock = self.session.query(SystemLock).filter_by(
                    service_name=self.service_name,
                    pid=self.pid
                ).first()
                
                if lock:
                    self.session.delete(lock)
                    self.session.commit()
                    logger.info(f"Lock released for '{self.service_name}' (PID: {self.pid})")
                
                self.locked = False
                
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
        
        finally:
            if self.session:
                self.session.close()
                self.session = None
    
    def kill_existing(self) -> bool:
        """Kill any existing instance of this service"""
        killed = False
        
        try:
            session = Session(self.engine)
            
            # Find existing lock
            existing = session.query(SystemLock).filter_by(
                service_name=self.service_name
            ).first()
            
            if existing:
                if self._kill_process(existing.pid):
                    logger.info(f"Killed existing {self.service_name} (PID: {existing.pid})")
                    killed = True
                
                # Remove lock from database
                session.delete(existing)
                session.commit()
            
            session.close()
            
            # Also kill any orphaned processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['pid'] == self.pid:
                        continue
                        
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if self.service_name in cmdline or \
                       ('discord' in cmdline.lower() and 'python' in cmdline.lower()):
                        logger.info(f"Killing orphaned process PID {proc.info['pid']}")
                        proc.terminate()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed:
                time.sleep(1)  # Wait for processes to die
                
        except Exception as e:
            logger.error(f"Error killing existing processes: {e}")
        
        return killed
    
    def get_status(self) -> dict:
        """Get status of all locked services"""
        try:
            session = Session(self.engine)
            locks = session.query(SystemLock).all()
            
            status = {}
            for lock in locks:
                alive = self._is_process_alive(lock.pid, lock.hostname)
                recent = (datetime.now() - lock.last_heartbeat).seconds < 30 if lock.last_heartbeat else False
                
                status[lock.service_name] = {
                    'pid': lock.pid,
                    'hostname': lock.hostname,
                    'started_at': lock.started_at.isoformat() if lock.started_at else None,
                    'last_heartbeat': lock.last_heartbeat.isoformat() if lock.last_heartbeat else None,
                    'is_alive': alive,
                    'heartbeat_recent': recent,
                    'status': 'running' if alive and recent else 'stale'
                }
            
            session.close()
            return status
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {}
    
    def _is_process_alive(self, pid: int, hostname: str) -> bool:
        """Check if a process is still alive"""
        # Only check local processes
        if hostname != self.hostname:
            return True  # Assume remote processes are alive
        
        try:
            return psutil.pid_exists(pid)
        except:
            return False
    
    def _kill_process(self, pid: int) -> bool:
        """Kill a process by PID"""
        try:
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                proc.terminate()
                time.sleep(0.5)
                if proc.is_running():
                    proc.kill()
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return False
    
    def _get_command_line(self) -> str:
        """Get the command line of the current process"""
        try:
            proc = psutil.Process(self.pid)
            return ' '.join(proc.cmdline())[:1000]  # Limit to 1000 chars
        except:
            return f"python {sys.argv[0]}"
    
    def _start_heartbeat(self):
        """Start heartbeat thread to update last_heartbeat"""
        import threading
        
        def heartbeat_worker():
            while self.locked:
                try:
                    if self.session:
                        lock = self.session.query(SystemLock).filter_by(
                            service_name=self.service_name,
                            pid=self.pid
                        ).first()
                        
                        if lock:
                            lock.last_heartbeat = datetime.now()
                            self.session.commit()
                    
                    time.sleep(10)  # Update every 10 seconds
                    
                except Exception as e:
                    logger.debug(f"Heartbeat error: {e}")
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        self.heartbeat_thread.start()
    
    def _stop_heartbeat(self):
        """Stop the heartbeat thread"""
        self.locked = False  # This will cause the thread to exit
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=1)
    
    def _cleanup_handler(self, signum, frame):
        """Signal handler for cleanup"""
        logger.info(f"Received signal {signum}, cleaning up...")
        self.release_lock()
        sys.exit(0)
    
    def __enter__(self):
        """Context manager entry"""
        if not self.acquire_lock():
            raise RuntimeError(f"Could not acquire lock for {self.service_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release_lock()


# Convenience function for Discord bot
def ensure_discord_singleton(force: bool = False):
    """
    Ensure only one Discord bot instance is running.
    
    Args:
        force: If True, kill existing instance and take the lock
    """
    singleton = DatabaseSingleton('discord_bot')
    
    if force:
        singleton.kill_existing()
    
    if not singleton.acquire_lock():
        logger.error("="*60)
        logger.error("ANOTHER DISCORD BOT INSTANCE IS ALREADY RUNNING!")
        logger.error("Use './go.py --restart-services' to kill it first")
        logger.error("="*60)
        sys.exit(1)
    
    # Register cleanup on exit
    import atexit
    atexit.register(singleton.release_lock)
    
    return singleton


if __name__ == "__main__":
    # Test the database singleton
    print("Testing Database Singleton Lock...")
    
    singleton = DatabaseSingleton('test_service')
    
    # Test acquiring lock
    if singleton.acquire_lock():
        print("✅ Lock acquired successfully")
        print(f"   Service: {singleton.service_name}")
        print(f"   PID: {singleton.pid}")
        print(f"   Host: {singleton.hostname}")
        
        # Test status
        status = singleton.get_status()
        print(f"\n📊 Current locks:")
        for service, info in status.items():
            print(f"   {service}: {info['status']} (PID: {info['pid']})")
        
        # Try to acquire again (should fail)
        singleton2 = DatabaseSingleton('test_service')
        if singleton2.acquire_lock():
            print("❌ ERROR: Second lock should have failed!")
        else:
            print("✅ Second lock correctly failed")
        
        singleton.release_lock()
        print("✅ Lock released")
    else:
        print("❌ Could not acquire lock")