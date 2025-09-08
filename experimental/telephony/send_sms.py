#!/usr/bin/env python3
"""
Send SMS using the Twilio bridge
"""

from twilio_simple_voice_bridge import get_bridge

# Get the bridge instance
bridge = get_bridge()

# Send SMS
phone_number = "+13233771681"
message = "Hello! This is Claude from Try Hard Tournament Tracker. The top 8 players are: Monte, Gamer Ace, ForeignSkies, Marvelous Marco, Tohru, Kiyarash, Andrik, and RandumMNK. Recent tournament: West Coast Warzone had 256 players!"

result = bridge.send_sms(phone_number, message)
print(f"SMS Result: {result}")