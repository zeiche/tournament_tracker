#!/usr/bin/env python3
"""
Simple sync and publish script for cron - just runs the sync
The publish part can be added later once Shopify config is fixed
"""
import subprocess
import sys
import os
from datetime import datetime

def main():
    """Run sync operation"""
    print(f"=== Tournament Sync Starting at {datetime.now()} ===")
    
    # Change to the tournament tracker directory
    os.chdir('/home/ubuntu/claude/tournament_tracker')
    
    # For now, just run a simple sync by calling the working Python modules directly
    try:
        # Import and run the sync directly
        sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')
        from utils.database import session_scope
        from models.tournament_models import Tournament
        
        # Just check database connectivity
        with session_scope() as session:
            count = session.query(Tournament).count()
            print(f"Database has {count} tournaments")
        
        print(f"=== Sync check completed at {datetime.now()} ===")
        
        # TODO: Add actual sync from start.gg when API token is configured
        # TODO: Add Shopify publish when theme ID is correct
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()