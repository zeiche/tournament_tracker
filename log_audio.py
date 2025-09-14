#!/usr/bin/env python3
"""
Log intro.wav and main.wav audio files
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("log_audio")

from logging_services.polymorphic_log_manager import PolymorphicLogManager
from polymorphic_core.visualizable import MediaFile

# Initialize log manager
log_manager = PolymorphicLogManager()

print("🔊 Logging audio files...")

# Log intro.wav
intro_path = "assets/intro.wav"
if os.path.exists(intro_path):
    print(f"🎵 Logging intro audio: {intro_path}")
    intro_file = MediaFile(intro_path, "Introduction audio track")
    log_manager.log("INFO", f"Intro audio loaded: {intro_path}", intro_file, source="audio_system")
    print("✅ Intro audio logged")

# Log main.wav  
main_path = "assets/main.wav"
if os.path.exists(main_path):
    print(f"🎵 Logging main audio: {main_path}")
    main_file = MediaFile(main_path, "Main background audio track")
    log_manager.log("INFO", f"Main audio loaded: {main_path}", main_file, source="audio_system")
    print("✅ Main audio logged")

print("\n🌐 View clickable audio entries at: http://10.0.0.1:8081/logs")
print("🔊 Look for entries with speaker icons and click them to play!")