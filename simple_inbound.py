#!/usr/bin/env python3
"""
simple_inbound.py - Simplest possible inbound call handler
"""

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

@app.route('/voice', methods=['POST', 'GET'])
def handle_call():
    """Super simple voice handler"""
    response = VoiceResponse()
    
    # Check for speech or digits
    speech = request.values.get('SpeechResult', '')
    digits = request.values.get('Digits', '')
    
    if speech:
        # Echo what they said
        response.say(f"You said: {speech}", voice='alice')
        # Ask for more
        response.gather(input='speech', action='/voice', speech_timeout='auto')
        response.say("Say something else or hang up.", voice='alice')
    elif digits:
        # Handle digit press
        if digits == '1':
            response.say("Recent tournaments: West Coast Warzone had 150 players.", voice='alice')
        elif digits == '2':
            response.say("Top player is West with 45 tournament wins.", voice='alice')
        else:
            response.say(f"You pressed {digits}", voice='alice')
        response.redirect('/voice')
    else:
        # Initial greeting
        response.say("Tournament tracker. Press 1 for tournaments, 2 for players.", voice='alice')
        response.gather(numDigits=1, action='/voice')
        response.say("No input received. Goodbye.", voice='alice')
    
    return str(response)

@app.route('/status', methods=['GET'])
def status():
    return "Simple inbound handler active"

if __name__ == "__main__":
    print("🎯 Simple Inbound Handler")
    print("📞 Webhook: http://64.111.98.139:8082/voice")
    app.run(host='0.0.0.0', port=8082, debug=False)