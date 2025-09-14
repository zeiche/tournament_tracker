#!/usr/bin/env python3
"""
Show intelligence announcements
"""

import sys
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

from polymorphic_core import announcer
from intelligence import get_intelligence

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.show_intelligence")

# Initialize intelligence to trigger announcements
print("Initializing Intelligence Module...")
try:
    ai = get_intelligence('auto')
    print(f"✅ Using {ai.__class__.__name__}")
except Exception as e:
    print(f"⚠️ Intelligence initialization: {e}")

# Show announcements
print("\n📡 Intelligence Announcements:")
print("=" * 50)

for ann in announcer.announcements:
    if 'intelligence' in ann['service'].lower() or 'mistral' in ann['service'].lower() or 'ollama' in ann['service'].lower():
        print(f"\n🔹 {ann['service']}")
        for cap in ann['capabilities']:
            print(f"   • {cap}")

print("\n✨ Intelligence is now advertising via Bonjour!")