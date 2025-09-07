#!/usr/bin/env python3
"""
start_simple_twilio.py - Start the simplified Twilio bridge
"""

from twilio_simple_voice_bridge import get_bridge
from tournament_voice_handler import handle_tournament_speech

print("=" * 60)
print("🔌 STARTING SIMPLE TWILIO BRIDGE")
print("=" * 60)
print()
print("This is a THIN bridge like Discord:")
print("  • Just forwards speech to handlers")
print("  • No business logic in the bridge")
print("  • Voice recognition enabled")
print("  • Handlers do the actual work")
print()

# Get the bridge
bridge = get_bridge()

# Register the tournament handler
bridge.register_handler(handle_tournament_speech)

print("✅ Tournament handler registered")
print("📱 Call 878-TRY-HARD to test!")
print()

# Run it
bridge.run(port=8082)