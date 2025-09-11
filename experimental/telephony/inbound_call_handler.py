#!/usr/bin/env python3
"""
inbound_call_handler.py - Enhanced inbound call handler for tournament tracker
Processes voice input through polymorphic queries and provides tournament info
"""

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from search.polymorphic_queries import query as pq
from capability_announcer import announcer
import subprocess
import re

app = Flask(__name__)

def process_voice_query(speech_text):
    """
    Process voice input through polymorphic query system
    Returns a voice-friendly response
    """
    # Clean up the speech text
    speech_text = speech_text.lower().strip()
    
    # Map common voice commands to queries
    voice_mappings = {
        "recent tournaments": "show recent tournaments brief",
        "top players": "show top 10 players brief", 
        "player rankings": "show top 10 players brief",
        "tournaments": "show recent tournaments brief",
        "who won": "show recent tournament winners",
        "attendance": "show tournament attendance trends",
        "help": "Available commands: recent tournaments, top players, tournament attendance"
    }
    
    # Check for direct mappings
    for phrase, query_text in voice_mappings.items():
        if phrase in speech_text:
            speech_text = query_text
            break
    
    # Try polymorphic query
    try:
        response = pq(speech_text)
        if response and response != "I don't understand that query.":
            # Clean up response for voice
            response = re.sub(r'[*_#`]', '', response)  # Remove markdown
            response = response.replace('\n', '. ')  # Convert newlines to pauses
            # Limit length for voice
            if len(response) > 500:
                response = response[:497] + "..."
            return response
    except Exception as e:
        announcer.announce("INBOUND_CALL_ERROR", [f"Query error: {e}"])
    
    # Fallback to go.py AI
    try:
        result = subprocess.run(
            ['./go.py', '--ai-ask', speech_text],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            response = result.stdout.strip()
            response = re.sub(r'[*_#`]', '', response)
            response = response.replace('\n', '. ')
            if len(response) > 500:
                response = response[:497] + "..."
            return response
    except Exception as e:
        announcer.announce("INBOUND_CALL_ERROR", [f"AI fallback error: {e}"])
    
    return "I couldn't understand that. Try asking about recent tournaments or top players."

@app.route('/inbound-voice', methods=['POST'])
def handle_inbound_call():
    """Handle incoming voice calls with tournament info"""
    
    # Get call info
    from_number = request.values.get('From', 'Unknown')
    call_sid = request.values.get('CallSid', '')
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Check if we have speech result from a previous gather
    speech_result = request.values.get('SpeechResult')
    digits = request.values.get('Digits')
    
    if speech_result:
        # Process the speech
        announcer.announce(
            "INBOUND_CALL_SPEECH",
            [f"From: {from_number}", f"Said: {speech_result}"]
        )
        
        # Get response from polymorphic system
        answer = process_voice_query(speech_result)
        response.say(answer, voice='alice', language='en-US')
        
        # Ask if they want to continue
        response.pause(length=1)
        gather = Gather(
            input='speech dtmf',
            timeout=5,
            speech_timeout='auto',
            action='/inbound-voice',
            method='POST'
        )
        gather.say("Is there anything else you'd like to know? Say yes to continue or hang up when done.", 
                  voice='alice', language='en-US')
        response.append(gather)
        
    elif digits:
        # Handle DTMF menu selection
        announcer.announce(
            "INBOUND_CALL_DTMF",
            [f"From: {from_number}", f"Pressed: {digits}"]
        )
        
        if digits == '1':
            answer = process_voice_query("show recent tournaments")
        elif digits == '2':
            answer = process_voice_query("show top 10 players")
        elif digits == '3':
            answer = process_voice_query("show tournament attendance")
        elif digits == '9':
            answer = "To hear about tournaments, say recent tournaments. For player rankings, say top players. For attendance info, say attendance."
        else:
            answer = "Invalid option. Please try again."
        
        response.say(answer, voice='alice', language='en-US')
        
        # Return to main menu
        response.pause(length=1)
        response.redirect('/inbound-voice')
        
    else:
        # Initial greeting
        announcer.announce(
            "INBOUND_CALL_NEW",
            [f"New call from: {from_number}", f"CallSid: {call_sid}"]
        )
        
        response.say(
            "Welcome to the Southern California Fighting Game Tournament Tracker! ",
            voice='alice',
            language='en-US'
        )
        
        # Offer both speech and DTMF options
        gather = Gather(
            input='speech dtmf',
            timeout=5,
            speech_timeout='auto',
            action='/inbound-voice',
            method='POST',
            num_digits=1
        )
        gather.say(
            "You can ask me anything about tournaments and players. "
            "For example, say recent tournaments, or top players. "
            "Or press 1 for recent tournaments, 2 for player rankings, "
            "3 for attendance info, or 9 for help.",
            voice='alice',
            language='en-US'
        )
        response.append(gather)
        
        # If no input, provide help
        response.say(
            "I didn't hear anything. Please call back to try again.",
            voice='alice',
            language='en-US'
        )
    
    return str(response)

@app.route('/inbound-status', methods=['GET', 'POST'])
def status():
    """Simple status endpoint"""
    return "Tournament Tracker Inbound Call Handler Active"

if __name__ == "__main__":
    announcer.announce(
        "INBOUND_CALL_HANDLER",
        [
            "Tournament tracker inbound call handler starting",
            "Webhook endpoint: /inbound-voice",
            "Supports both speech and DTMF input",
            "Connected to polymorphic query system"
        ]
    )
    
    print("🎯 Tournament Tracker Inbound Call Handler")
    print("📞 Configure Twilio webhook to: http://YOUR_SERVER:8083/inbound-voice")
    print("🎤 Supports speech recognition and DTMF menu")
    print("🔌 Connected to polymorphic query system")
    
    app.run(host='0.0.0.0', port=8083, debug=False)