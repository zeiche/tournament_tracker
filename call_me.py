#!/usr/bin/env python3
"""
call_me.py - Bot that makes outbound calls
"""

import os
import sys
from pathlib import Path
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

# Get credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_PHONE_NUMBER')

def make_call(to_number, message=None):
    """Make an outbound call with a message"""
    
    # Default message if none provided
    if not message:
        message = "Hello! This is your tournament tracker AI calling. I can help you with tournament information, player stats, and more. Text me your questions!"
    
    # Create TwiML for the call
    twiml = VoiceResponse()
    twiml.say(message, voice='alice')
    twiml.pause(length=2)
    twiml.say("Goodbye!", voice='alice')
    
    # Create client and make call
    client = Client(account_sid, auth_token)
    
    # For dynamic responses, point to webhook
    # For static message, use twiml parameter
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        twiml=str(twiml),
        # Or use url for dynamic: url='http://64.111.98.139:8082/voice'
    )
    
    print(f"📞 Calling {to_number}...")
    print(f"Call SID: {call.sid}")
    print(f"Status: {call.status}")
    
    return call.sid

def call_with_webhook(to_number):
    """Make a call that uses the webhook for dynamic responses"""
    client = Client(account_sid, auth_token)
    
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url='http://64.111.98.139:8082/voice',  # Uses bridge for dynamic response
        method='POST'
    )
    
    print(f"📞 Calling {to_number} with dynamic webhook...")
    print(f"Call SID: {call.sid}")
    
    return call.sid

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 call_me.py <phone_number> [message]")
        print("  python3 call_me.py <phone_number> --dynamic")
        print("\nExamples:")
        print("  python3 call_me.py +15551234567")
        print("  python3 call_me.py +15551234567 'Hello, this is a test call'")
        print("  python3 call_me.py +15551234567 --dynamic")
        sys.exit(1)
    
    to_number = sys.argv[1]
    
    # Ensure number has country code
    if not to_number.startswith('+'):
        if to_number.startswith('1'):
            to_number = '+' + to_number
        else:
            to_number = '+1' + to_number
    
    # Check for dynamic flag
    if len(sys.argv) > 2 and sys.argv[2] == '--dynamic':
        call_with_webhook(to_number)
    else:
        # Use custom message if provided
        message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else None
        make_call(to_number, message)