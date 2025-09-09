#!/usr/bin/env python3
"""
Show current bonjour advertisements - immediate, non-blocking
"""

import sys
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

from polymorphic_core import announcer

# Import modules to trigger their advertisements
from utils import database_service
from services import startgg_sync
from utils import tournament_operations
from services import web_editor

# Try to import graphics services
failed_imports = []
try:
    from utils import graphics_service
except Exception as e:
    failed_imports.append(f"graphics_service: {e}")

try:
    from tournament_domain.analytics import tournament_heatmap
except Exception as e:
    failed_imports.append(f"tournament_heatmap: {e}")

# Try to import audio services
try:
    from polymorphic_core.audio import audio_player, tts_service, audio_provider
except Exception as e:
    failed_imports.append(f"audio modules: {e}")

# Try to import core models
try:
    from models import tournament_models
except Exception as e:
    failed_imports.append(f"tournament_models: {e}")

# Try to import math services
try:
    from math_services import visualization_math, statistical_math, geometric_math, data_transforms
except Exception as e:
    failed_imports.append(f"math_services: {e}")

# Try to import visualization services
try:
    from visualization_services import heatmap_service, chart_service, map_service
except Exception as e:
    failed_imports.append(f"visualization_services: {e}")

# Just print what's currently advertised
print("\n📡 Current Bonjour Advertisements:")
print("=" * 50)

if not announcer.announcements:
    print("No services advertising yet")
else:
    for ann in announcer.announcements:
        print(f"\n🔹 {ann['service']}")
        for cap in ann['capabilities']:
            print(f"   • {cap}")

if failed_imports:
    print("\n⚠️  Services that failed to advertise:")
    for failure in failed_imports:
        print(f"   ❌ {failure}")