#!/usr/bin/env python3
"""
voice_chat_server.py - Server for processing voice chat with Claude
"""

from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
import subprocess
import os
from pathlib import Path

app = Flask(__name__)

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

@app.route('/process-speech', methods=['POST'])
def process_speech():
    """Process speech and respond with Claude"""
    
    speech_result = request.values.get('SpeechResult', '')
    print(f"🎤 Heard: {speech_result}")
    
    response = VoiceResponse()
    
    if speech_result:
        # Process through Claude
        try:
            # Try polymorphic query first for tournament stuff
            from polymorphic_queries import query as pq
            answer = pq(speech_result)
            
            if answer == "I don't understand that query.":
                # Fall back to Claude AI
                result = subprocess.run(
                    ['./go.py', '--ai-ask', speech_result],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    answer = result.stdout.strip()
                else:
                    answer = "Let me think about that..."
            
            # Clean up for voice
            answer = answer.replace('*', '').replace('_', '').replace('#', '')
            answer = answer.replace('\n', '. ')
            if len(answer) > 300:
                answer = answer[:297] + "..."
            
            print(f"💬 Responding: {answer[:100]}...")
            response.say(answer, voice='alice')
            
        except Exception as e:
            print(f"❌ Error: {e}")
            response.say("I had trouble understanding that.", voice='alice')
        
        # Ask if they want to continue
        response.pause(length=1)
        gather = response.gather(
            input='speech',
            timeout=3,
            speechTimeout='auto',
            action='/process-speech',
            method='POST'
        )
        gather.say("What else?", voice='alice')
        
    else:
        response.say("I didn't catch that.", voice='alice')
        gather = response.gather(
            input='speech',
            timeout=3,
            speechTimeout='auto',
            action='/process-speech',
            method='POST'
        )
        gather.say("Try again?", voice='alice')
    
    response.say("Alright, talk to you later!", voice='alice')
    
    return str(response)

@app.route('/start-chat', methods=['POST'])
def start_chat():
    """Initial chat greeting"""
    response = VoiceResponse()
    response.say("Hey! This is Claude. What's on your mind?", voice='alice')
    
    gather = response.gather(
        input='speech',
        timeout=3,
        speechTimeout='auto',
        action='/process-speech',
        method='POST'
    )
    gather.say("I'm listening...", voice='alice')
    
    response.say("Hmm, I didn't hear anything. Call back when you're ready!", voice='alice')
    
    return str(response)

if __name__ == "__main__":
    print("🎯 Voice Chat Server")
    print("📞 Webhook: http://64.111.98.139:8085/start-chat")
    print("🤖 Connected to Claude via polymorphic queries")
    app.run(host='0.0.0.0', port=8085, debug=False)