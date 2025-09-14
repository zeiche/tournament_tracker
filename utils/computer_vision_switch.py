#!/usr/bin/env python3
"""
Dynamic switch for Computer Vision Service
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.computer_vision_switch")

from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch

def handle_computer_vision(args):
    """Handle --computer-vision command"""
    
    # Announce this switch
    announcer.announce(
        "Computer Vision Service Switch", 
        ["Starts the Computer Vision Service for image recognition and OCR"]
    )
    
    print("🔍 Initializing Computer Vision Service...")
    
    try:
        # Import and initialize the CV service
        from services.computer_vision_service import computer_vision_service
        
        # Test the service capabilities
        print("✅ Computer Vision Service initialized successfully")
        print("🧠 Available capabilities:")
        print("   - OCR text recognition with coordinates")
        print("   - Button detection and localization")  
        print("   - Input field identification")
        print("   - Email field specific detection")
        print("   - Image element analysis")
        
        # Show service status
        status = computer_vision_service.ask("status")
        print(f"📊 Service status: {status}")
        
        return "Computer Vision Service ready for image recognition tasks"
        
    except ImportError as e:
        print(f"❌ Failed to import Computer Vision Service: {e}")
        print("💡 Install dependencies: pip3 install --break-system-packages opencv-python pytesseract pillow")
        return f"Failed to import CV service: {e}"
        
    except Exception as e:
        print(f"❌ Failed to initialize Computer Vision Service: {e}")
        return f"Failed to initialize: {e}"

# Register the switch
announce_switch(
    "--computer-vision", 
    handle_computer_vision,
    description="Initialize Computer Vision Service for image recognition and OCR"
)