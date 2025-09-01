#!/usr/bin/env python3
"""
Persistent web server for tournament contact editor
"""
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/ubuntu/claude/tournament_tracker/editor_web.log'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    try:
        from editor_web import run_server
        logging.info("Starting Tournament Editor Web Service")
        run_server(port=8081, host='0.0.0.0')  # Listen on all interfaces for service
    except Exception as e:
        logging.error(f"Failed to start web service: {e}")
        sys.exit(1)