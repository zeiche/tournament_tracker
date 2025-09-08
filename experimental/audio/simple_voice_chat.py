#!/usr/bin/env python3
"""
simple_voice_chat.py - Simplest voice chat that works
"""

import os
from pathlib import Path
from twilio.rest import Client

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_PHONE_NUMBER')

def call_with_simple_gather(phone):
    """Make a call with simple digit gathering (more reliable than speech)"""
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Tournament tracker here! Press 1 for recent tournaments. Press 2 for player rankings. Press 3 to hear a joke.</Say>
    <Gather numDigits="1" action="http://64.111.98.139:8082/voice" method="POST">
        <Say voice="alice">Please press a key.</Say>
    </Gather>
    <Say voice="alice">Goodbye!</Say>
</Response>'''
    
    client = Client(account_sid, auth_token)
    call = client.calls.create(
        to=phone,
        from_=from_number,
        twiml=twiml
    )
    
    print(f"📞 Calling {phone} with menu...")
    print(f"Call SID: {call.sid}")
    return call.sid

if __name__ == "__main__":
    call_with_simple_gather('+13233771681')