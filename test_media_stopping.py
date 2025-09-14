#!/usr/bin/env python3
"""
Test media stopping functionality specifically
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("test_media_stopping")

from logging_services.polymorphic_log_manager import PolymorphicLogManager
from polymorphic_core.visualizable import MediaFile

# Initialize log manager
log_manager = PolymorphicLogManager()

print("🔊 Testing media stopping functionality")

# Log audio that should stop when modal closes
if os.path.exists("assets/main.wav"):
    media_file = MediaFile("assets/main.wav", "Test audio for media stopping")
    log_manager.log("INFO", "🔊 MEDIA STOP TEST: Click to play, then press X or Close to test stopping", media_file, source="media_stop_test")
    print("🎵 Audio logged for media stop test")

print("\n🎯 **Testing Instructions:**")
print("1. Visit: http://10.0.0.1:8081/logs") 
print("2. Click the entry that says 'MEDIA STOP TEST'")
print("3. Click play on the audio player")
print("4. While audio is playing, press [X] or [Close]")
print("5. Check browser console (F12) for debug messages")
print("6. Audio should immediately stop")
print("\n🔍 **Debug Info:**")
print("- Browser console will show how many audio elements were found")
print("- It will log the stopping process for each element")
print("- If no audio elements found, there might be a timing issue")