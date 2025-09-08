#!/usr/bin/env python3
"""
start_voice_server.py - Start the 878-TRY-HARD voice server
"""

from polymorphic_twilio import get_twilio

print("=" * 60)
print("🎮 STARTING 878-TRY-HARD VOICE SERVER")
print("=" * 60)
print()
print("📱 Phone: 878-879-4283 (878-TRY-HARD)")
print("🌐 Webhook port: 8082")
print("🎤 Speech recognition: ENABLED")
print("🤖 Claude integration: ACTIVE")
print()
print("📞 WHEN YOU CALL:")
print("  1. You'll hear a greeting")
print("  2. SPEAK your question (not DTMF!)")
print("  3. Claude responds with tournament info")
print("  4. Conversation continues naturally")
print()
print("🎯 VOICE COMMANDS:")
print("  • 'help' - Get help menu")
print("  • 'top players' - Quick rankings")
print("  • 'recent tournaments' - Latest events")
print("  • 'stats' - Database statistics")
print("  • 'repeat' - Say that again")
print()
print("=" * 60)

# Start the server
twilio = get_twilio()
twilio.do("start webhooks", port=8082)

print("✅ Server running on port 8082")
print("📞 Call 878-TRY-HARD to test!")
print()
print("Press Ctrl+C to stop...")

# Keep running
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 Stopping server...")
    print("Goodbye!")