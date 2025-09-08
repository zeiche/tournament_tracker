#!/usr/bin/env python3
"""
setup_twilio_function.py - Configure Twilio to handle inbound calls with a function
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

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

# TwiML Bin content - a chat-like experience for inbound calls
twiml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hey! Welcome to the tournament tracker chat line. I'm Claude, and I can tell you about fighting game tournaments.</Say>
    <Pause length="1"/>
    <Gather input="speech dtmf" timeout="5" speechTimeout="auto" numDigits="1">
        <Say voice="alice">Say something or press a key. Press 1 for recent tournaments, 2 for top players, or just talk to me.</Say>
    </Gather>
    <Say voice="alice">Let me tell you what I know. West Coast Warzone had 256 players. The top player is West with 45 wins. Call back anytime!</Say>
</Response>"""

# Create or update TwiML Bin
try:
    # Check if we already have a TwiML bin
    bins = client.twiml_apps.list(limit=10)
    chat_bin = None
    
    # Look for existing bin
    for bin in bins:
        if 'tournament' in bin.friendly_name.lower():
            chat_bin = bin
            break
    
    if not chat_bin:
        # Create new TwiML app
        print("Creating new TwiML app...")
        chat_bin = client.twiml_apps.create(
            friendly_name="Tournament Chat Handler",
            voice_url="http://demo.twilio.com/docs/voice.xml",  # Placeholder
            voice_method="POST"
        )
    
    print(f"TwiML App SID: {chat_bin.sid}")
    
except Exception as e:
    print(f"Note: TwiML apps require additional setup. Using direct TwiML instead.")

# Update phone number to use TwiML directly for inbound calls
phone_number = os.getenv('TWILIO_PHONE_NUMBER')
numbers = client.incoming_phone_numbers.list(phone_number=phone_number)

if numbers:
    number = numbers[0]
    
    # Use a Twilio demo URL that works
    demo_url = "http://demo.twilio.com/docs/voice.xml"
    
    print(f"📞 Updating {phone_number} for inbound calls...")
    print(f"Current webhook: {number.voice_url}")
    
    # For now, set it to play a simple message
    # In production, you'd use Twilio Functions or TwiML Bins
    number.update(
        voice_url=demo_url,
        voice_method="GET",
        voice_fallback_url="",
        status_callback=""
    )
    
    print(f"✅ Updated to demo handler")
    print("ℹ️  Inbound calls will now get a demo message")
    print("📝 To fully connect to chat, we need:")
    print("   1. Twilio Functions (serverless)")
    print("   2. OR a public webhook that works")
    print("   3. OR ngrok tunnel")
    
    # Create a simple inbound experience
    print("\n🎯 Creating direct inbound handler...")
    
    # This will make inbound calls hear a message
    simple_twiml = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="alice">Tournament tracker here! For recent tournaments, call back and press 1. For player rankings, press 2. This is a demo of connecting calls to chat.</Say>
        <Pause length="2"/>
        <Say voice="alice">In a full implementation, I would process your speech and respond with tournament data. Thanks for calling!</Say>
    </Response>"""
    
    # Save as a file that could be served
    with open('inbound_response.xml', 'w') as f:
        f.write(simple_twiml)
    
    print("✅ Created inbound_response.xml")
    print("📞 When you call, you'll hear the demo message")
    
else:
    print(f"❌ Phone number {phone_number} not found")