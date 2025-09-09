#!/usr/bin/env python3
"""
sync_and_publish.py - Simple sync and publish for cron job
Calls existing working scripts in sequence
"""
import subprocess
import sys
import os
from datetime import datetime

def main():
    """Run sync and publish operations"""
    print(f"=== Sync and Publish Starting at {datetime.now()} ===")
    
    # Change to the tournament tracker directory
    os.chdir('/home/ubuntu/claude/tournament_tracker')
    
    # Step 1: Run the sync using api/startgg_query.py which we know works
    print("Step 1: Syncing tournaments from start.gg...")
    try:
        result = subprocess.run(
            [sys.executable, 'api/startgg_query.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        if result.returncode != 0:
            print(f"Sync error: {result.stderr}")
            # Don't fail completely - continue to publish what we have
        else:
            print("Sync completed successfully")
    except subprocess.TimeoutExpired:
        print("Sync timed out after 5 minutes")
    except Exception as e:
        print(f"Sync failed: {e}")
    
    # Step 2: Run the publish using compact publisher (stays under 50KB)
    print("Step 2: Publishing to Shopify...")
    try:
        result = subprocess.run(
            [sys.executable, 'publish_shopify_compact.py'],
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )
        if result.returncode != 0:
            print(f"Publish error: {result.stderr}")
            sys.exit(1)
        else:
            print("Published to Shopify successfully")
            if result.stdout:
                print(result.stdout)
    except subprocess.TimeoutExpired:
        print("Publish timed out after 1 minute")
        sys.exit(1)
    except Exception as e:
        print(f"Publish failed: {e}")
        sys.exit(1)
    
    print(f"=== Sync and Publish Completed at {datetime.now()} ===")
    sys.exit(0)

if __name__ == "__main__":
    main()