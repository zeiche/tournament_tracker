#!/usr/bin/env python3
"""
Start a fresh WebDAV server with our new /bonjour filesystem
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.execution_guard import mark_go_py_execution
mark_go_py_execution()

from services.webdav_database_browser import create_webdav_app
from wsgiref.simple_server import make_server

# Get logger for proper logging
from polymorphic_core.service_locator import get_service

try:
    logger = get_service("logger", prefer_network=False)
except Exception:
    import logging
    logger = logging.getLogger(__name__)

def start_fresh_webdav():
    """Start fresh WebDAV server on port 8445"""
    logger.info("Starting fresh WebDAV server with /bonjour filesystem...")

    try:
        # Create the WebDAV app with our updated filesystem
        app = create_webdav_app()
        logger.info("WebDAV app created with /bonjour support")

        # Start server on port 8449
        port = 8449
        server = make_server('0.0.0.0', port, app)
        logger.info(f"WebDAV server starting on http://10.0.0.1:{port}")
        logger.info("Available directories: /tournaments/, /players/, /organizations/, /bonjour/")
        logger.info("Press Ctrl+C to stop")

        # Start serving
        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("WebDAV server stopped by user")
    except Exception as e:
        logger.error(f"Error starting WebDAV server: {e}")

if __name__ == "__main__":
    start_fresh_webdav()