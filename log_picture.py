#!/usr/bin/env python3
"""
Log a picture to test the clickable media viewer
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("log_picture")

from logging_services.polymorphic_log_manager import PolymorphicLogManager
from polymorphic_core.visualizable import MediaFile

# Initialize log manager
log_manager = PolymorphicLogManager()

# Log the high-res tournament attendance image
image_path = "tournament_attendance_highres.png"
if os.path.exists(image_path):
    print(f"📷 Logging high-res image: {image_path}")
    media_file = MediaFile(image_path, "High-resolution tournament attendance heatmap visualization")
    log_manager.log("INFO", f"Generated tournament attendance heatmap: {image_path}", media_file, source="heatmap_generator")
    print("✅ Image logged successfully!")
    print("🌐 View at: http://localhost:8081/logs")
    print("🖼️ Look for the entry with the camera icon and click it!")
else:
    print(f"❌ Image not found: {image_path}")