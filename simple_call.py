#!/usr/bin/env python3
"""
simple_call.py - Simplest possible call with TwiML
"""

import os
import sys
from pathlib import Path
from twilio.rest import Client

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_PHONE_NUMBER')

def call_with_twiml(to_number, message):
    """Make call with inline TwiML"""
    
    # Simple TwiML XML string
    twiml_str = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{message}</Say>
    <Pause length="1"/>
    <Say voice="alice">Goodbye!</Say>
</Response>'''
    
    client = Client(account_sid, auth_token)
    
    # Try with twiml parameter
    try:
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            twiml=twiml_str
        )
        print(f"📞 Calling {to_number}...")
        print(f"Message: {message}")
        print(f"Call SID: {call.sid}")
        print(f"Status: {call.status}")
        return call.sid
    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying with URL instead...")
        
        # Fallback to URL method
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url='http://demo.twilio.com/docs/voice.xml'  # Twilio demo that works
        )
        print(f"Call SID: {call.sid}")
        return call.sid

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 simple_call.py <phone> [message]")
        sys.exit(1)
    
    phone = sys.argv[1]
    if not phone.startswith('+'):
        phone = '+1' + phone if not phone.startswith('1') else '+' + phone
    
    message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello from tournament tracker!"
    
    call_with_twiml(phone, message)