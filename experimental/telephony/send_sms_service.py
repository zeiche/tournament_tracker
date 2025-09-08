#!/usr/bin/env python3
"""
send_sms_service.py - Service to send SMS messages
Started by go.py, announces itself via bonjour
"""

import sys
from capability_announcer import announcer
from twilio_simple_voice_bridge import get_bridge

def send_sms(phone_number, message=None):
    """Send SMS using the Twilio bridge"""
    
    # Default message if none provided
    if not message:
        message = "Hello from Claude at Try Hard Tournament Tracker! Top players: Monte, Gamer Ace, ForeignSkies. Call 878-TRY-HARD for more info!"
    
    # Announce what we're doing
    announcer.announce(
        "SMS_SERVICE",
        [
            f"Sending SMS to: {phone_number}",
            f"Message: {message[:50]}...",
            "Using Twilio bridge"
        ]
    )
    
    # Get bridge and send
    bridge = get_bridge()
    result = bridge.send_sms(phone_number, message)
    
    print(f"📱 SMS {'sent successfully!' if result.get('status') == 'success' else 'failed!'}")
    print(f"Result: {result}")
    
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 send_sms_service.py PHONE_NUMBER [MESSAGE]")
        sys.exit(1)
    
    phone = sys.argv[1]
    message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else None
    
    # Add country code if needed
    if not phone.startswith('+'):
        phone = '+1' + ''.join(filter(str.isdigit, phone))
    
    send_sms(phone, message)