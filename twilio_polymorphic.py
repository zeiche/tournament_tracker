#!/usr/bin/env python3
"""
twilio_polymorphic.py - Polymorphic Twilio Bridge

Twilio bridge with just 3 methods: ask/tell/do
Handles voice calls, SMS, and speech recognition polymorphically.
"""

from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
from pathlib import Path
import sys
sys.path.insert(0, 'utils')
from universal_polymorphic import PolymorphicBridge
from capability_announcer import announcer
from polymorphic_queries import query as pq


class TwilioPolymorphic(PolymorphicBridge):
    """
    Twilio bridge with just 3 methods.
    
    Examples:
    - bridge.ask("phone number")      # Get our phone number
    - bridge.ask("active calls")      # List active calls
    - bridge.tell("status")          # Get Twilio status
    - bridge.do("call 555-1234")     # Make a call
    - bridge.do("send sms", to="...", body="...")  # Send SMS
    - bridge.do("start webhook")     # Start webhook server
    """
    
    def __init__(self):
        # Load credentials
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Try loading from .env if not in environment
        if not self.account_sid:
            env_file = Path(__file__).parent / '.env'
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if 'TWILIO_ACCOUNT_SID=' in line:
                            self.account_sid = line.split('=', 1)[1].strip().strip('"')
                        elif 'TWILIO_AUTH_TOKEN=' in line:
                            self.auth_token = line.split('=', 1)[1].strip().strip('"')
                        elif 'TWILIO_PHONE_NUMBER=' in line:
                            self.phone_number = line.split('=', 1)[1].strip().strip('"')
        
        # Initialize Twilio client if credentials available
        self.client = Client(self.account_sid, self.auth_token) if self.account_sid else None
        
        # Flask app for webhooks
        self.app = Flask(__name__)
        self.webhook_running = False
        
        # Speech handlers
        self.speech_handlers = []
        
        # Set up webhook routes
        self._setup_webhooks()
        
        # Call parent init
        super().__init__()
        
        # Announce ourselves
        announcer.announce(
            "TwilioPolymorphic",
            [
                "I'm a polymorphic Twilio bridge",
                f"Phone: {self.phone_number}",
                "I handle voice and SMS",
                "Use ask/tell/do pattern",
                "bridge.ask('phone')",
                "bridge.do('call 555-1234')",
                "bridge.do('send sms', to='...', body='...')"
            ]
        )
    
    def _setup_webhooks(self):
        """Set up Flask webhook routes"""
        
        @self.app.route('/voice', methods=['POST'])
        def handle_voice():
            """Handle incoming voice calls"""
            from_number = request.values.get('From')
            speech = request.values.get('SpeechResult')
            
            # Announce call
            announcer.announce(
                "TWILIO_CALL",
                [f"From: {from_number}", f"Speech: {speech or 'No speech yet'}"]
            )
            
            response = VoiceResponse()
            
            # Process speech if we have it
            if speech:
                # Use polymorphic query system
                result = pq(speech)
                if result:
                    response.say(result, voice='alice')
            else:
                # Welcome message
                response.say("Welcome to Try Hard Tournament Tracker. What would you like to know?", voice='alice')
            
            # Set up speech gathering
            response.gather(
                input='speech',
                timeout=30,
                action='/voice',
                language='en-US'
            )
            
            return str(response)
        
        @self.app.route('/sms', methods=['POST'])
        def handle_sms():
            """Handle incoming SMS"""
            from_number = request.values.get('From')
            body = request.values.get('Body')
            
            # Announce SMS
            announcer.announce(
                "TWILIO_SMS",
                [f"From: {from_number}", f"Message: {body}"]
            )
            
            # Process with polymorphic query
            result = pq(body)
            
            # Send response
            if result:
                self.do("send sms", to=from_number, body=result)
            
            return ""
    
    def _handle_ask(self, question: str, **kwargs):
        """Handle Twilio-specific questions"""
        q = str(question).lower()
        
        if any(word in q for word in ['phone', 'number']):
            return self.phone_number
        
        if any(word in q for word in ['account', 'sid']):
            return self.account_sid
        
        if any(word in q for word in ['webhook', 'server']):
            return "Running" if self.webhook_running else "Not running"
        
        if any(word in q for word in ['call', 'active']):
            return self._get_active_calls()
        
        if any(word in q for word in ['sms', 'message', 'text']):
            return self._get_recent_messages()
        
        if any(word in q for word in ['balance', 'credit']):
            return self._get_account_balance()
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str, **kwargs):
        """Tell about Twilio status"""
        if format in ['status', 'twilio']:
            return {
                'configured': bool(self.client),
                'phone': self.phone_number,
                'webhook': self.webhook_running,
                'account': self.account_sid[:8] + "..." if self.account_sid else None
            }
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs):
        """Handle Twilio actions"""
        act = str(action).lower()
        
        if 'call' in act:
            # Extract phone number from action or kwargs
            import re
            phone_match = re.search(r'[\d\-\(\)\+\s]+', action)
            phone = phone_match.group().strip() if phone_match else kwargs.get('to')
            message = kwargs.get('message', 'Hello from Tournament Tracker!')
            return self._make_call(phone, message)
        
        if 'sms' in act or 'text' in act:
            to = kwargs.get('to')
            body = kwargs.get('body', 'Hello from Tournament Tracker!')
            return self._send_sms(to, body)
        
        if 'webhook' in act or 'server' in act:
            if 'start' in act:
                return self._start_webhook_server(kwargs.get('port', 8082))
            elif 'stop' in act:
                return self._stop_webhook_server()
        
        if 'register' in act and 'handler' in act:
            handler = kwargs.get('handler')
            if handler:
                self.speech_handlers.append(handler)
                return f"Registered handler: {handler.__name__}"
        
        return super()._handle_do(action, **kwargs)
    
    def _make_call(self, to_number: str, message: str = None):
        """Make an outbound call"""
        if not self.client:
            return "Twilio not configured"
        
        if not to_number:
            return "No phone number provided"
        
        # Clean phone number
        to_number = ''.join(filter(str.isdigit, to_number))
        if not to_number.startswith('+'):
            if not to_number.startswith('1'):
                to_number = '1' + to_number
            to_number = '+' + to_number
        
        try:
            # Create TwiML for the call
            twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{message or 'Hello from Tournament Tracker!'}</Say>
    <Pause length="1"/>
    <Say voice="alice">Goodbye!</Say>
</Response>'''
            
            # Make the call
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                twiml=twiml
            )
            
            # Announce
            announcer.announce(
                "OUTBOUND_CALL",
                [f"Calling: {to_number}", f"SID: {call.sid}"]
            )
            
            return f"Calling {to_number} (SID: {call.sid})"
            
        except Exception as e:
            return f"Call failed: {e}"
    
    def _send_sms(self, to_number: str, body: str):
        """Send an SMS"""
        if not self.client:
            return "Twilio not configured"
        
        if not to_number:
            return "No phone number provided"
        
        # Clean phone number
        if not to_number.startswith('+'):
            to_number = '+1' + ''.join(filter(str.isdigit, to_number))
        
        try:
            message = self.client.messages.create(
                body=body,
                from_=self.phone_number,
                to=to_number
            )
            
            # Announce
            announcer.announce(
                "SMS_SENT",
                [f"To: {to_number}", f"Message: {body[:50]}..."]
            )
            
            return f"SMS sent to {to_number}"
            
        except Exception as e:
            return f"SMS failed: {e}"
    
    def _start_webhook_server(self, port: int = 8082):
        """Start webhook server"""
        if self.webhook_running:
            return "Webhook already running"
        
        import threading
        
        def run_server():
            self.webhook_running = True
            self.app.run(host='0.0.0.0', port=port, debug=False)
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        self.webhook_running = True
        return f"Webhook server started on port {port}"
    
    def _stop_webhook_server(self):
        """Stop webhook server"""
        if not self.webhook_running:
            return "Webhook not running"
        
        # Flask doesn't have a clean shutdown, would need more complex solution
        self.webhook_running = False
        return "Webhook stop requested (may need process restart)"
    
    def _get_active_calls(self):
        """Get active calls"""
        if not self.client:
            return "Twilio not configured"
        
        try:
            calls = self.client.calls.list(status='in-progress', limit=10)
            return [f"{c.from_} -> {c.to}" for c in calls] if calls else "No active calls"
        except Exception as e:
            return f"Error getting calls: {e}"
    
    def _get_recent_messages(self):
        """Get recent SMS messages"""
        if not self.client:
            return "Twilio not configured"
        
        try:
            messages = self.client.messages.list(limit=5)
            return [f"{m.from_}: {m.body[:30]}..." for m in messages] if messages else "No recent messages"
        except Exception as e:
            return f"Error getting messages: {e}"
    
    def _get_account_balance(self):
        """Get account balance"""
        if not self.client:
            return "Twilio not configured"
        
        try:
            account = self.client.api.accounts(self.account_sid).fetch()
            return f"Balance: {account.balance} {account.balance_currency}"
        except Exception as e:
            return f"Error getting balance: {e}"
    
    def _get_capabilities(self):
        """List Twilio capabilities"""
        return [
            "ask('phone number')",
            "ask('active calls')",
            "ask('recent messages')",
            "tell('status')",
            "do('call 555-1234')",
            "do('send sms', to='...', body='...')",
            "do('start webhook')",
            f"Phone: {self.phone_number}"
        ]
    
    def run(self, port: int = 8082):
        """Run the Twilio bridge"""
        print(f"Starting polymorphic Twilio bridge...")
        print(f"Phone: {self.phone_number}")
        
        # Start webhook server
        result = self.do("start webhook", port=port)
        print(result)
        
        print(f"Webhook running on port {port}")
        print("Ready for calls and SMS!")
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")


# Global instance
twilio_bridge = TwilioPolymorphic()


if __name__ == "__main__":
    # Run the bridge
    twilio_bridge.run()