#!/usr/bin/env python3
"""
discord_killer.py - Simple, robust Discord process killer
Just kills Discord-related processes. No locks, no complexity.
"""

import os
import signal
import time
import psutil
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def kill_discord_processes(verbose: bool = True) -> int:
    """
    Kill ALL Discord-related Python processes.
    
    Returns:
        Number of processes killed
    """
    killed_count = 0
    
    # First, try the simple pkill approach
    subprocess.run(['pkill', '-f', 'discord'], stderr=subprocess.DEVNULL)
    subprocess.run(['pkill', '-f', 'polymorphic_discord'], stderr=subprocess.DEVNULL)
    
    # Now hunt down any stragglers with psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            pid = proc.info['pid']
            cmdline = ' '.join(proc.info['cmdline'] or [])
            
            # Skip our own process
            if pid == os.getpid():
                continue
            
            # Check if it's a Discord-related Python process
            is_discord = False
            
            # Check various Discord-related patterns
            patterns = [
                'discord_service.py',
                'discord_bot.py',
                'polymorphic_discord',
                'discord_bridge',
                'discord_voice',
                '--discord-bot',
                'discord_audio',
                'discord_dm_service'
            ]
            
            for pattern in patterns:
                if pattern in cmdline:
                    is_discord = True
                    break
            
            # Also check for go.py running with discord flag
            if 'go.py' in cmdline and '--discord' in cmdline:
                is_discord = True
            
            if is_discord:
                if verbose:
                    logger.info(f"Killing Discord process PID {pid}: {cmdline[:100]}...")
                
                try:
                    # Try graceful termination first
                    proc.terminate()
                    killed_count += 1
                    
                    # Give it a moment
                    time.sleep(0.1)
                    
                    # If still alive, force kill
                    if proc.is_running():
                        proc.kill()
                        if verbose:
                            logger.info(f"  Force killed PID {pid}")
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Final cleanup with pkill again
    time.sleep(0.5)
    subprocess.run(['pkill', '-9', '-f', 'discord'], stderr=subprocess.DEVNULL)
    
    if verbose and killed_count > 0:
        logger.info(f"Killed {killed_count} Discord processes")
    elif verbose:
        logger.info("No Discord processes found")
    
    return killed_count


def ensure_discord_dead():
    """
    Ensure Discord is completely dead before starting a new instance.
    """
    # Kill everything
    kill_discord_processes()
    
    # Wait a moment
    time.sleep(1)
    
    # Check if anything survived
    survivors = []
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'discord' in cmdline.lower() and 'python' in cmdline:
                survivors.append(proc.info['pid'])
        except:
            pass
    
    if survivors:
        logger.warning(f"Some Discord processes survived: {survivors}")
        # Try one more aggressive kill
        for pid in survivors:
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
        time.sleep(0.5)


if __name__ == "__main__":
    print("Killing all Discord processes...")
    count = kill_discord_processes()
    print(f"Done. Killed {count} processes.")