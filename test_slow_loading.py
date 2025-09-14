#!/usr/bin/env python3
"""
Test the spinner with slow-loading content
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("test_slow_loading")

from logging_services.polymorphic_log_manager import PolymorphicLogManager
from polymorphic_core.visualizable import MediaFile

# Initialize log manager
log_manager = PolymorphicLogManager()

print("⏳ Testing spinner with slow loading content")

# Log a large image that will take time to load
if os.path.exists("tournament_attendance_highres.png"):
    media_file = MediaFile("tournament_attendance_highres.png", "Large image to test spinner visibility")
    log_manager.log("INFO", "SPINNER TEST: Large image for slow loading test", media_file, source="spinner_visibility")
    print("📷 Large image logged for spinner test")

print("\n🎯 **Test Instructions:**")
print("1. Visit: http://10.0.0.1:8081/logs")
print("2. Click the entry with 'SPINNER TEST' in the message")
print("3. You should see a rotating hourglass (⏳) while it loads")
print("4. The hourglass should rotate 180°, pause, rotate to 360°, pause, repeat")
print("5. Once content loads, the spinner should disappear")
print("6. If you don't see rotation, there may be a CSS issue")