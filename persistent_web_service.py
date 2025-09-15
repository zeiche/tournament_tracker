#!/usr/bin/env python3
"""
persistent_web_service.py - Advanced Web Editor Only

This service starts the actual advanced web editor from services/web_editor.py
"""

import sys
import os

# Load environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point - advanced web editor with HTTPS server"""
    print("🌐 Starting ADVANCED web editor service with HTTPS server")

    try:
        # Import and run the main function from services/web_editor.py
        # This uses the proper HTTPS server startup with SSL certificates
        from services.web_editor import main as web_editor_main

        print("🚀 Starting advanced web editor with HTTPS server...")
        print("🌐 Port: 8081 (HTTPS)")
        print("🔗 SSL access: https://editor.zilogo.com")
        print("📡 Features: Real-time logging, WebSocket support, mDNS discovery")
        print("🔒 Using LetsEncrypt SSL certificates")

        # Call the main function which starts the ManagedWebEditorService properly
        web_editor_main()

    except Exception as e:
        print(f"❌ Failed to start advanced web editor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()