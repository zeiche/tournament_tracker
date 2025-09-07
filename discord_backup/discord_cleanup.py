#!/usr/bin/env python3
"""
discord_cleanup.py - Clean up stuck Discord voice sessions
Kills all Discord-related processes and restarts cleanly
"""

import os
import subprocess
import time
import signal

def kill_discord_processes():
    """Kill all Discord-related processes"""
    print("🔍 Finding Discord processes...")
    
    # Find all Python processes running Discord-related scripts
    patterns = [
        "polymorphic_discord",
        "discord_",
        "voice_",
        "go.py.*discord"
    ]
    
    killed = 0
    for pattern in patterns:
        try:
            # Get PIDs
            result = subprocess.run(
                f"pgrep -f '{pattern}'",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            print(f"  Killing PID {pid} (pattern: {pattern})")
                            os.kill(int(pid), signal.SIGKILL)
                            killed += 1
                        except:
                            pass
        except:
            pass
    
    if killed > 0:
        print(f"✅ Killed {killed} Discord processes")
        time.sleep(2)  # Wait for processes to die
    else:
        print("ℹ️  No Discord processes found")
    
    return killed

def clear_logs():
    """Clear Discord log files to start fresh"""
    log_files = [
        "discord.log",
        "discord_bot.log",
        "discord_live.log",
        "discord_voice.log",
        "voice_bot.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                # Truncate the log file
                with open(log_file, 'w') as f:
                    f.write("")
                print(f"  Cleared {log_file}")
            except:
                pass

def main():
    """Main cleanup routine"""
    print("=" * 60)
    print("🧹 Discord Voice Session Cleanup")
    print("=" * 60)
    
    # Kill processes
    killed = kill_discord_processes()
    
    # Clear logs
    print("\n📝 Clearing log files...")
    clear_logs()
    
    print("\n✨ Cleanup complete!")
    print("You can now restart the Discord bot with:")
    print("  ./go.py --discord-bot")
    print("=" * 60)

if __name__ == "__main__":
    main()