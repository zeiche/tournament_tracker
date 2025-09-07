#!/usr/bin/env python3
"""
twilio_to_claude.py - Connect Twilio calls directly to Claude intelligence
Just like Discord forwards messages to Claude, Twilio should too
"""

import os
from pathlib import Path
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from polymorphic_queries import query as pq
import subprocess

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

app = Flask(__name__)

@app.route('/voice-claude', methods=['POST'])
def voice_claude():
    """Handle voice calls - forward to Claude just like Discord does"""
    response = VoiceResponse()
    
    # Get what the user said
    speech_result = request.values.get('SpeechResult', '')
    
    if speech_result:
        print(f"User said: {speech_result}")
        
        # Send to Claude via polymorphic query (same as Discord)
        try:
            claude_response = pq(speech_result)
            if claude_response and claude_response != "I don't understand that query.":
                # Shorten for voice
                if len(claude_response) > 200:
                    claude_response = claude_response[:200] + "..."
            else:
                # Try go.py as fallback
                result = subprocess.run(
                    ['./go.py', '--ai-ask', speech_result],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    claude_response = result.stdout.strip()[:200]
                else:
                    claude_response = "I'll need to think about that. Text me for details."
        except:
            claude_response = "Let me process that. Text this number for full details."
        
        # Speak Claude's response
        response.say(claude_response, voice='alice')
        
        # Continue conversation
        if 'bye' not in speech_result.lower():
            response.pause(length=1)
            gather = response.gather(
                input='speech',
                timeout=4,
                speech_timeout='auto',
                action='/voice-claude'
            )
            gather.say("Anything else?", voice='alice')
        else:
            response.say("Goodbye!", voice='alice')
    else:
        # Initial greeting - ask for input
        response.say("Tournament tracker here. What's your question?", voice='alice')
        gather = response.gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/voice-claude'
        )
        gather.say("Go ahead, I'm listening.", voice='alice')
    
    return str(response)

if __name__ == "__main__":
    print("🔌 Twilio-to-Claude bridge on port 8084")
    print("📱 This connects voice calls to Claude intelligence")
    app.run(host='0.0.0.0', port=8084, debug=False)