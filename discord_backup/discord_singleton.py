#!/usr/bin/env python3
"""
discord_singleton.py - Singleton lock mechanism for Discord bot
Ensures only one instance of the Discord bot can run at a time.
"""

import os
import sys
import fcntl
import signal
import psutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordSingleton:
    """Singleton lock manager for Discord bot"""
    
    def __init__(self):
        self.lock_file = Path('/tmp/discord_bot.lock')
        self.pid_file = Path('/tmp/discord_bot.pid')
        self.lock_fd = None
        
    def acquire_lock(self) -> bool:
        """
        Attempt to acquire exclusive lock.
        Returns True if lock acquired, False if another instance is running.
        """
        try:
            # First check if there's an existing PID file
            if self.pid_file.exists():
                try:
                    with open(self.pid_file, 'r') as f:
                        old_pid = int(f.read().strip())
                    
                    # Check if that process is still running
                    if psutil.pid_exists(old_pid):
                        # Check if it's actually a Discord bot process
                        try:
                            proc = psutil.Process(old_pid)
                            cmdline = ' '.join(proc.cmdline())
                            if 'discord' in cmdline.lower() or 'polymorphic_discord' in cmdline:
                                logger.error(f"Discord bot already running with PID {old_pid}")
                                logger.error(f"Command: {cmdline}")
                                return False
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # Old process is dead, clean up
                    logger.info(f"Cleaning up stale PID file for PID {old_pid}")
                    self.pid_file.unlink()
                except (ValueError, IOError):
                    # Invalid PID file, remove it
                    self.pid_file.unlink()
            
            # Try to acquire file lock
            self.lock_fd = open(self.lock_file, 'w')
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # Write our PID
                with open(self.pid_file, 'w') as f:
                    f.write(str(os.getpid()))
                
                logger.info(f"Lock acquired, PID {os.getpid()} written to {self.pid_file}")
                return True
                
            except IOError:
                logger.error("Could not acquire lock - another instance is running")
                self.lock_fd.close()
                self.lock_fd = None
                return False
                
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            return False
    
    def release_lock(self):
        """Release the lock and clean up"""
        try:
            if self.lock_fd:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                self.lock_fd = None
            
            if self.pid_file.exists():
                self.pid_file.unlink()
            
            if self.lock_file.exists():
                self.lock_file.unlink()
                
            logger.info("Lock released and cleaned up")
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
    
    def kill_existing(self) -> bool:
        """Kill any existing Discord bot processes"""
        killed = False
        
        # Check PID file first
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Killed existing Discord bot with PID {pid}")
                killed = True
            except (ValueError, IOError, ProcessLookupError):
                pass
        
        # Also check for any Discord-related Python processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if proc.info['pid'] != os.getpid():  # Don't kill ourselves
                    if ('discord' in cmdline.lower() and 'python' in cmdline.lower()) or \
                       'polymorphic_discord_bridge' in cmdline:
                        logger.info(f"Killing Discord process PID {proc.info['pid']}: {cmdline[:100]}")
                        proc.terminate()
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed:
            # Wait a moment for processes to die
            import time
            time.sleep(1)
        
        return killed
    
    def __enter__(self):
        """Context manager entry"""
        if not self.acquire_lock():
            raise RuntimeError("Could not acquire Discord bot lock - another instance is running")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release_lock()


# Global singleton instance
discord_lock = DiscordSingleton()


def ensure_singleton():
    """Ensure only one Discord bot instance is running"""
    if not discord_lock.acquire_lock():
        logger.error("="*60)
        logger.error("ANOTHER DISCORD BOT INSTANCE IS ALREADY RUNNING!")
        logger.error("Use './go.py --restart-services' to kill it first")
        logger.error("="*60)
        sys.exit(1)
    
    # Register cleanup on exit
    import atexit
    atexit.register(discord_lock.release_lock)
    
    # Register signal handlers for cleanup
    def cleanup_handler(signum, frame):
        logger.info(f"Received signal {signum}, cleaning up...")
        discord_lock.release_lock()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, cleanup_handler)
    signal.signal(signal.SIGINT, cleanup_handler)
    
    return True


if __name__ == "__main__":
    # Test the singleton
    print("Testing Discord singleton lock...")
    
    if discord_lock.acquire_lock():
        print("✅ Lock acquired successfully")
        print(f"   PID file: {discord_lock.pid_file}")
        print(f"   Lock file: {discord_lock.lock_file}")
        
        # Try to acquire again (should fail)
        lock2 = DiscordSingleton()
        if lock2.acquire_lock():
            print("❌ ERROR: Second lock should have failed!")
        else:
            print("✅ Second lock correctly failed")
        
        discord_lock.release_lock()
        print("✅ Lock released")
    else:
        print("❌ Could not acquire lock - another instance running")