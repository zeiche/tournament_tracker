#!/usr/bin/env python3
"""
interactive_call.py - Interactive voice call that listens and responds
"""

import os
import sys
from pathlib import Path
from twilio.rest import Client
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import threading
import time
from search.polymorphic_queries import query as pq

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

app = Flask(__name__)

@app.route('/interactive', methods=['POST'])
def interactive():
    """Interactive voice handler that listens and responds"""
    response = VoiceResponse()
    
    # Check if we have speech input
    speech_result = request.values.get('SpeechResult', '')
    
    if speech_result:
        print(f"User said: {speech_result}")
        
        # Process the speech
        reply = process_speech(speech_result)
        
        # Respond
        response.say(reply, voice='alice')
        response.pause(length=1)
        
        # Keep conversation going if not goodbye
        if 'goodbye' not in speech_result.lower() and 'bye' not in speech_result.lower():
            gather = response.gather(
                input='speech',
                timeout=5,
                speech_timeout='auto',
                action='/interactive'
            )
            gather.say("What else?", voice='alice')
        else:
            response.say("Goodbye! Call anytime!", voice='alice')
    else:
        # Initial greeting
        response.say("Hello! I'm listening. Ask me anything!", voice='alice')
        gather = response.gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/interactive'
        )
        gather.say("What would you like to know?", voice='alice')
    
    return str(response)

def process_speech(speech):
    """Process speech and generate response"""
    speech_lower = speech.lower()
    
    # Simple responses
    if 'hello' in speech_lower or 'hi' in speech_lower:
        return "Hello there! How can I help you today?"
    elif 'tournament' in speech_lower:
        # Try polymorphic query
        try:
            result = pq("recent tournaments")
            if result and len(result) > 100:
                return "We have many recent tournaments. Text me for details!"
            return result[:200] if result else "I track fighting game tournaments in SoCal."
        except:
            return "I track fighting game tournaments. What would you like to know?"
    elif 'player' in speech_lower:
        return "I can tell you about player rankings. Which player?"
    elif 'who are you' in speech_lower or 'what are you' in speech_lower:
        return "I'm the tournament tracker AI. I help with FGC tournament info!"
    elif 'foo' in speech_lower:
        return "Yes, you are a foo! Backyard tryhards! Ha ha ha ha!"
    elif 'thank' in speech_lower:
        return "You're welcome! Anything else?"
    else:
        return f"I heard: {speech}. Ask about tournaments or players!"

def start_server():
    """Start webhook server"""
    app.run(host='0.0.0.0', port=8084, debug=False)

def make_interactive_call(to_number):
    """Make an interactive call"""
    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    
    # Make the call
    client = Client(account_sid, auth_token)
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url='http://64.111.98.139:8084/interactive',
        method='POST'
    )
    
    print(f"📞 Starting interactive call to {to_number}...")
    print(f"Call SID: {call.sid}")
    print("Server running for 5 minutes for conversation...")
    
    # Keep server running
    time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 interactive_call.py <phone>")
        sys.exit(1)
    
    phone = sys.argv[1]
    if not phone.startswith('+'):
        phone = '+1' + phone if not phone.startswith('1') else '+' + phone
    
    make_interactive_call(phone)