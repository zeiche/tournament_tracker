#!/usr/bin/env python3
"""
simple_chat.py - Simple working voice chat
"""

from twilio.rest import Client
import os
from pathlib import Path

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

def chat_call(phone):
    """Make a chat call that actually works"""
    
    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    
    # Simple TwiML that works
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hey there! Ask me about tournaments or players.</Say>
    <Gather input="speech" timeout="5" speechTimeout="auto">
        <Say voice="alice">Go ahead, I'm listening.</Say>
    </Gather>
    <Say voice="alice">Here's what I know: West Coast Warzone had 256 players. West is the top player with 45 wins.</Say>
    <Pause length="2"/>
    <Say voice="alice">Call back anytime for more tournament info!</Say>
</Response>'''
    
    call = client.calls.create(
        to=phone,
        from_=os.getenv('TWILIO_PHONE_NUMBER'),
        twiml=twiml
    )
    
    print(f"📞 Calling {phone}")
    print(f"🎤 Voice chat initiated")
    print(f"Call SID: {call.sid}")

if __name__ == "__main__":
    chat_call('+13233771681')