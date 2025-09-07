#!/usr/bin/env python3
"""
twilio_bridge.py - Minimal Twilio capability that announces itself
Just receives calls/SMS and announces them. That's it.
"""

from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from pathlib import Path
from capability_announcer import announcer
from polymorphic_core.discovery import register_capability
import threading

class TwilioBridge:
    """Minimal Twilio capability - just announces calls/SMS"""
    
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
                            self.account_sid = line.split('=', 1)[1].strip()
                        elif 'TWILIO_AUTH_TOKEN=' in line:
                            self.auth_token = line.split('=', 1)[1].strip()
                        elif 'TWILIO_PHONE_NUMBER=' in line:
                            self.phone_number = line.split('=', 1)[1].strip()
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("No Twilio credentials found!")
        
        # Create Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
        # Create Flask app for webhooks
        self.app = Flask(__name__)
        
        # Message handlers - anyone can register
        self.sms_handlers = []
        self.call_handlers = []
        
        # Announce ourselves
        announcer.announce(
            "TwilioBridge",
            [
                "I connect to Twilio",
                "I receive calls and SMS and announce them",
                "Register handlers with me to process calls/SMS",
                f"Phone number: {self.phone_number}",
                "I don't do business logic - I just forward messages"
            ]
        )
        
        # Setup webhook routes
        @self.app.route('/voice', methods=['POST'])
        def handle_voice():
            """Handle incoming calls"""
            # Announce the call
            announcer.announce(
                "TWILIO_CALL",
                [
                    f"From: {request.values.get('From')}",
                    f"To: {request.values.get('To')}",
                    f"CallSid: {request.values.get('CallSid')}"
                ]
            )
            
            # Let handlers process it
            response = VoiceResponse()
            for handler in self.call_handlers:
                try:
                    handler_response = handler(request.values)
                    if handler_response:
                        response.say(handler_response)
                        break
                except Exception as e:
                    print(f"Call handler error: {e}")
            
            if not str(response):
                response.say("Hello from Twilio bridge")
            
            return str(response)
        
        @self.app.route('/sms', methods=['POST'])
        def handle_sms():
            """Handle incoming SMS"""
            # Announce the SMS
            announcer.announce(
                "TWILIO_SMS", 
                [
                    f"From: {request.values.get('From')}",
                    f"Body: {request.values.get('Body')}",
                    f"MessageSid: {request.values.get('MessageSid')}"
                ]
            )
            
            # Let handlers process it
            response = MessagingResponse()
            for handler in self.sms_handlers:
                try:
                    handler_response = handler(request.values)
                    if handler_response:
                        response.message(handler_response)
                        break
                except Exception as e:
                    print(f"SMS handler error: {e}")
            
            return str(response)
    
    def register_sms_handler(self, handler):
        """Register an SMS handler"""
        self.sms_handlers.append(handler)
        announcer.announce("TwilioBridge", [f"Registered SMS handler: {handler.__name__}"])
    
    def register_call_handler(self, handler):
        """Register a call handler"""
        self.call_handlers.append(handler)
        announcer.announce("TwilioBridge", [f"Registered call handler: {handler.__name__}"])
    
    def send_sms(self, to, body):
        """Send an SMS"""
        message = self.client.messages.create(
            to=to,
            from_=self.phone_number,
            body=body
        )
        return message.sid
    
    def make_call(self, to, message):
        """Make a call"""
        call = self.client.calls.create(
            to=to,
            from_=self.phone_number,
            twiml=f'<Response><Say>{message}</Say></Response>'
        )
        return call.sid
    
    def run(self, port=8080):
        """Run the webhook server"""
        print(f"🔌 Twilio bridge running on port {port}")
        print(f"📱 Phone: {self.phone_number}")
        print(f"🔗 Set webhooks to: http://your-server:{port}/voice and /sms")
        self.app.run(host='0.0.0.0', port=port, debug=False)

# Global instance
_bridge = None

def get_bridge():
    """Get or create bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = TwilioBridge()
    return _bridge

# Register as discoverable capability
register_capability("twilio", get_bridge)

if __name__ == "__main__":
    bridge = get_bridge()
    bridge.run()