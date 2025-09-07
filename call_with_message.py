#!/usr/bin/env python3
"""
call_with_message.py - Make a call with a specific message via webhook
"""

import os
import sys
from pathlib import Path
from twilio.rest import Client
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import threading
import time

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

# Store the message to speak
current_message = "Hello from tournament tracker"

app = Flask(__name__)

@app.route('/call-message', methods=['POST', 'GET'])
def call_message():
    """Webhook that speaks the message"""
    response = VoiceResponse()
    response.say(current_message, voice='alice')
    response.pause(length=1)
    response.say("Goodbye!", voice='alice')
    return str(response)

def start_webhook_server():
    """Run webhook server in background"""
    app.run(host='0.0.0.0', port=8083, debug=False)

def make_call_with_webhook(to_number, message):
    """Make call using webhook for message"""
    global current_message
    current_message = message
    
    # Start webhook server in background thread
    server_thread = threading.Thread(target=start_webhook_server, daemon=True)
    server_thread.start()
    time.sleep(1)  # Give server time to start
    
    # Make the call pointing to webhook
    client = Client(account_sid, auth_token)
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url='http://64.111.98.139:8083/call-message',
        method='POST'
    )
    
    print(f"📞 Calling {to_number} with message via webhook...")
    print(f"Message: {message}")
    print(f"Call SID: {call.sid}")
    
    # Keep server running for 30 seconds to handle the call
    time.sleep(30)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 call_with_message.py <phone> <message>")
        sys.exit(1)
    
    phone = sys.argv[1]
    if not phone.startswith('+'):
        phone = '+1' + phone if not phone.startswith('1') else '+' + phone
    
    message = ' '.join(sys.argv[2:])
    make_call_with_webhook(phone, message)