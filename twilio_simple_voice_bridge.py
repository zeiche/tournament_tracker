#!/usr/bin/env python3
"""
twilio_simple_voice_bridge.py - Minimal Twilio bridge (like Discord)
Just receives speech and announces it. That's it.
"""

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import os
from pathlib import Path
from capability_announcer import announcer

class SimpleTwilioBridge:
    """Minimal Twilio bridge - just announces speech, no business logic"""
    
    def __init__(self):
        # Load credentials
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not self.account_sid or not self.auth_token:
            env_file = Path(__file__).parent / '.env'
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if 'TWILIO_ACCOUNT_SID=' in line:
                            self.account_sid = line.split('=', 1)[1].strip().strip('"')
                        elif 'TWILIO_AUTH_TOKEN=' in line:
                            self.auth_token = line.split('=', 1)[1].strip().strip('"')
                        elif 'TWILIO_PHONE_NUMBER=' in line:
                            self.phone_number = line.split('=', 1)[1].strip().strip('"')
        
        # Flask app for webhooks
        self.app = Flask(__name__)
        
        # Speech handlers - anyone can register
        self.speech_handlers = []
        
        # Announce ourselves
        announcer.announce(
            "SimpleTwilioBridge",
            [
                "I'm a minimal Twilio bridge with voice recognition",
                "I just forward speech to handlers",
                "No business logic - just like Discord bridge",
                f"Phone: {self.phone_number}",
                "Register handlers with me to process speech"
            ]
        )
        
        # Single webhook route - minimal!
        @self.app.route('/voice', methods=['POST'])
        def handle_voice():
            """Handle voice calls - just forward speech"""
            call_sid = request.values.get('CallSid')
            from_number = request.values.get('From')
            speech = request.values.get('SpeechResult')
            
            response = VoiceResponse()
            
            if speech:
                # Announce the speech
                announcer.announce(
                    "TWILIO_SPEECH",
                    [
                        f"From: {from_number}",
                        f"Said: {speech}",
                        f"CallSid: {call_sid}"
                    ]
                )
                
                # Let handlers process it
                handled = False
                for handler in self.speech_handlers:
                    try:
                        handler_response = handler(speech, from_number)
                        if handler_response:
                            response.say(handler_response, voice='alice')
                            handled = True
                            break
                    except Exception as e:
                        print(f"Handler error: {e}")
                
                if not handled:
                    response.say("I heard you.", voice='alice')
            else:
                # First call - no speech yet
                response.say("Welcome to Try Hard. What would you like to know?", voice='alice')
            
            # Always gather more speech
            response.gather(
                input='speech',
                timeout=3,
                speech_timeout='auto',
                action='/voice',
                language='en-US',
                enhanced=True,
                speechModel='phone_call',
                actionOnEmptyResult=True
            )
            
            return str(response)
    
    def register_handler(self, handler):
        """Register a speech handler"""
        self.speech_handlers.append(handler)
        announcer.announce(
            "SimpleTwilioBridge",
            [f"Registered handler: {handler.__name__}"]
        )
    
    def run(self, port=8082):
        """Run the webhook server"""
        print(f"🔌 Simple Twilio bridge running on port {port}")
        print(f"📱 Phone: {self.phone_number}")
        print(f"🎤 Voice recognition: ENABLED")
        self.app.run(host='0.0.0.0', port=port, debug=False)

# Global instance
_bridge = None

def get_bridge():
    """Get or create bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = SimpleTwilioBridge()
    return _bridge

# Simple test handler
def echo_handler(speech, from_number):
    """Echo back what was said"""
    return f"You said: {speech}"

if __name__ == "__main__":
    bridge = get_bridge()
    # Register a simple handler for testing
    bridge.register_handler(echo_handler)
    bridge.run(port=8082)