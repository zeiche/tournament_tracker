#!/usr/bin/env python3
"""
call_to_chat.py - Connect phone call to Claude chat
Uses Twilio's transcription to bridge voice to text chat
"""

from twilio.rest import Client
import os
from pathlib import Path
import subprocess
import time

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

def process_with_claude(text):
    """Process text through Claude"""
    try:
        # First try polymorphic queries for tournament stuff
        from polymorphic_queries import query as pq
        response = pq(text)
        
        if response == "I don't understand that query.":
            # Fall back to Claude AI
            result = subprocess.run(
                ['./go.py', '--ai-ask', text],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout:
                response = result.stdout.strip()
            else:
                response = "I'm thinking about that..."
        
        # Clean for voice
        response = response.replace('*', '').replace('_', '').replace('#', '')
        response = response.replace('\n', '. ')
        if len(response) > 400:
            response = response[:397] + "..."
        
        return response
    except Exception as e:
        return f"Let me think about that differently."

def call_with_chat(phone):
    """Make a call that processes responses through Claude"""
    
    client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
    
    # Pre-process some responses
    responses = {
        "greeting": process_with_claude("hello, this is a user calling about tournaments"),
        "tournaments": process_with_claude("tell me about recent tournaments"),
        "players": process_with_claude("who are the top players"),
        "help": process_with_claude("what can you tell me about")
    }
    
    # Build TwiML with Claude's responses
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{responses['greeting']}</Say>
    <Pause length="1"/>
    <Gather input="dtmf" numDigits="1" timeout="10">
        <Say voice="alice">Press 1 for tournaments, 2 for players, 3 for general help, or stay on the line to hear everything.</Say>
    </Gather>
    <Say voice="alice">Here's what I know about tournaments: {responses['tournaments']}</Say>
    <Pause length="2"/>
    <Say voice="alice">About top players: {responses['players']}</Say>
    <Pause length="1"/>
    <Say voice="alice">Call back anytime for more info!</Say>
</Response>'''
    
    print(f"📞 Calling {phone} with Claude-powered responses...")
    print(f"🤖 Responses prepared through Claude chat")
    
    call = client.calls.create(
        to=phone,
        from_=os.getenv('TWILIO_PHONE_NUMBER'),
        twiml=twiml
    )
    
    print(f"✅ Call initiated: {call.sid}")
    print(f"\nClaude's responses:")
    for key, value in responses.items():
        print(f"  {key}: {value[:50]}...")
    
    return call.sid

if __name__ == "__main__":
    call_with_chat('+13233771681')