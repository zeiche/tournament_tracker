#!/usr/bin/env python3
"""
twilio_simple_bridge.py - SUPER SIMPLE Twilio bridge like Discord
Just receives calls/SMS and announces them. That's it.
"""

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
import os
from pathlib import Path
from capability_announcer import announcer
from twilio_handlers import sms_handlers, call_handlers
from polymorphic_core.discovery import register_capability

app = Flask(__name__)

# Announce ourselves via Bonjour
announcer.announce(
    "TWILIO_BRIDGE",
    [
        "I am the Twilio telephony bridge",
        "I receive calls and SMS",
        "I forward them to handlers",
        "I connect voice to intelligence",
        "Just like Discord, but for phone"
    ]
)

# Load token for validation
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

@app.route('/voice', methods=['POST'])
def voice():
    """Handle voice calls with interactive menu"""
    from_number = request.values.get('From')
    digits = request.values.get('Digits')
    
    # Announce the call
    announcer.announce(
        "TWILIO_VOICE",
        [
            f"Call from: {from_number}",
            f"Digits: {digits}" if digits else "New call"
        ]
    )
    
    response = VoiceResponse()
    
    if digits:
        # Handle menu selection
        if digits == '1':
            response.say("Recent tournament: West Coast Warzone had 256 players. JLPC took first place.", voice='alice')
        elif digits == '2':
            response.say("Top players: West with 45 wins, JLPC with 38 wins, King Vu with 35 wins.", voice='alice')
        elif digits == '3':
            response.say("Attendance is growing. Average tournament size increased 20 percent this year.", voice='alice')
        else:
            response.say("Invalid selection.", voice='alice')
        
        # Return to menu
        response.pause(length=1)
        response.redirect('/voice')
    else:
        # Initial greeting with menu
        response.say("Welcome to the SoCal Fighting Game Tournament Tracker!", voice='alice')
        gather = response.gather(numDigits=1, action='/voice', method='POST')
        gather.say("Press 1 for recent tournaments. Press 2 for player rankings. Press 3 for attendance trends.", voice='alice')
        response.say("No input received. Goodbye!", voice='alice')
    
    return str(response)

@app.route('/sms', methods=['POST'])
def sms():
    """Handle SMS - use handlers if available"""
    body = request.values.get('Body', '')
    from_number = request.values.get('From', '')
    
    # Announce the SMS
    announcer.announce(
        "TWILIO_SMS",
        [
            f"SMS from: {from_number}",
            f"Message: {body}"
        ]
    )
    
    # Try handlers
    response = MessagingResponse()
    for handler in sms_handlers:
        try:
            message = handler(from_number, body)
            if message:
                response.message(message)
                break
        except:
            pass
    
    # Default if no handler responded
    if not str(response):
        response.message(f"Got your message: {body}")
    
    return str(response)

if __name__ == "__main__":
    print("🔌 Simple Twilio bridge on port 8082")
    print(f"📱 Webhooks: http://your-server:8082/voice and /sms")
    app.run(host='0.0.0.0', port=8082, debug=False)