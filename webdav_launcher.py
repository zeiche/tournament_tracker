#!/usr/bin/env python3
"""
WebDAV Database Browser Launcher
Starts the WebDAV server that exposes database objects as virtual files.
"""
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("webdav_launcher")

from services.webdav_database_browser import create_webdav_app
from wsgiref.simple_server import make_server
from polymorphic_core import announcer, announces_capability


@announces_capability
class WebDAVDatabaseBrowser:
    """WebDAV Database Browser Service with Bonjour announcements"""
    
    def __init__(self):
        announcer.announce(
            "WebDAV Database Browser",
            [
                "Virtual filesystem interface to tournament database",
                "Exposes model intelligence as browsable files",
                "Tournament analytics, player stats, organization data",
                "Compatible with any WebDAV client",
                "Read-only access for data safety",
                f"Access via: http://localhost:{{port}}",
                "Virtual structure:",
                "  /tournaments/tournament_123/data.json",
                "  /tournaments/tournament_123/analytics.html", 
                "  /players/player_west/stats.html",
                "  /organizations/org_runback/contacts.json"
            ],
            examples=[
                "python3 webdav_launcher.py 8084",
                "./go.py --webdav",
                "Mount as network drive in file manager"
            ]
        )


# Initialize service announcement
webdav_service = WebDAVDatabaseBrowser()


def start_webdav_server(host="0.0.0.0", port=8443):
    """
    ⚠️  CRITICAL: WEBDAV PERMANENTLY USES PORT 8443 - DO NOT CHANGE! ⚠️
    This is hardcoded to avoid port 443 privilege issues and confusion.
    Port 8443 is the PERMANENT WebDAV port for this system.
    """
    """Start the WebDAV database browser server"""
    
    # Update Bonjour announcement with actual port
    announcer.announce(
        f"WebDAV Database Browser (Port {port})",
        [
            f"🗂️  WebDAV Database Browser running on {host}:{port}",
            "Virtual filesystem interface to tournament database",
            "Exposes model intelligence as browsable files",
            "Tournament analytics, player stats, organization data",
            "Compatible with any WebDAV client",
            "Read-only access for data safety",
            f"🌐 Access via: http://localhost:{port}",
            "📁 Virtual filesystem structure:",
            "  /tournaments/tournament_123/data.json (Raw data)",
            "  /tournaments/tournament_123/analytics.html (Built-in analytics)",
            "  /tournaments/tournament_123/heatmap_data.json (Geographic data)",
            "  /players/player_west/stats.html (Performance dashboard)",
            "  /organizations/org_runback/contacts.json (Contact info)",
            "🔧 WebDAV clients can mount this as a network drive"
        ],
        status="running"
    )
    
    print(f"🗂️  Starting WebDAV Database Browser on {host}:{port}")
    print("📁 Virtual filesystem structure:")
    print("   /tournaments/tournament_123/")
    print("     ├── data.json           (Raw data)")
    print("     ├── analytics.html      (Built-in analytics)")  
    print("     ├── heatmap_data.json   (Geographic data)")
    print("     └── relationships.txt   (Object relationships)")
    print("   /players/player_west/")
    print("     ├── data.json           (Raw data)")
    print("     ├── stats.html          (Performance dashboard)")
    print("     └── performance.json    (Win rates, consistency)")
    print("   /organizations/org_runback/")
    print("     ├── data.json           (Raw data)")
    print("     ├── tournaments.html    (Tournament list)")
    print("     └── contacts.json       (Contact information)")
    print()
    print(f"🌐 Access via: http://localhost:{port}")
    print("🔧 WebDAV clients can mount this as a network drive")
    print()
    
    try:
        app = create_webdav_app()

        """
        # HTTP server (commented out for HTTPS-only)
        with make_server(host, port, app) as httpd:
            print(f"✅ WebDAV Database Browser running on port {port}")
            print("Press Ctrl+C to stop...")
            httpd.serve_forever()
        """

        # HTTPS-only server
        import ssl
        import pathlib

        # Use letsencrypt certificates
        cert_file = pathlib.Path("/etc/letsencrypt/live/zilogo.com/fullchain.pem")
        key_file = pathlib.Path("/etc/letsencrypt/live/zilogo.com/privkey.pem")

        if not (cert_file.exists() and key_file.exists()):
            print("❌ SSL certificates not found - HTTPS-only mode requires certificates")
            print("⚠️  Cannot start WebDAV server without SSL certificates")
            return False

        with make_server(host, port, app) as httpd:
            # Create SSL context
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(cert_file, key_file)
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Wrap server socket with SSL
            httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)

            print(f"✅ WebDAV Database Browser running on HTTPS port {port}")
            print("🔒 HTTPS-only mode enabled")
            print("Press Ctrl+C to stop...")
            httpd.serve_forever()
            
    except Exception as e:
        print(f"❌ Failed to start WebDAV server: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Import the persistent WebDAV service instead
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from persistent_webdav_service import main
    main()