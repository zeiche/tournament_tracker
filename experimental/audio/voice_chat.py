#!/usr/bin/env python3
"""
voice_chat.py - Interactive voice chat with Claude
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

def start_voice_chat(phone_number):
    """Start an interactive voice chat session"""
    
    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    
    # TwiML for interactive chat - gathers speech and processes it
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hey! This is Claude. What's on your mind?</Say>
    <Gather input="speech" timeout="3" speechTimeout="auto" action="http://64.111.98.139:8085/process-speech" method="POST">
        <Say voice="alice">I'm listening...</Say>
    </Gather>
    <Say voice="alice">I didn't catch that. Let me call you back.</Say>
</Response>'''
    
    call = client.calls.create(
        to=phone_number,
        from_=os.getenv('TWILIO_PHONE_NUMBER'),
        twiml=twiml
    )
    
    print(f"📞 Starting voice chat with {phone_number}")
    print(f"Call SID: {call.sid}")
    return call.sid

if __name__ == "__main__":
    import sys
    phone = sys.argv[1] if len(sys.argv) > 1 else '+13233771681'
    start_voice_chat(phone)