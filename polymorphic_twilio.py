#!/usr/bin/env python3
"""
polymorphic_twilio.py - Twilio that follows the TRUE OOP pattern
Just THREE methods: ask(), tell(), do()
"""

from typing import Any, Optional, Dict, List, Union
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from twilio.twiml.messaging_response import MessagingResponse
from flask import Flask, request
import os
from pathlib import Path
from capability_announcer import announcer
from polymorphic_core.discovery import register_capability
import threading
import queue
import json

class PolymorphicTwilio:
    """
    Twilio service with just THREE methods that do EVERYTHING.
    
    Instead of send_sms(), make_call(), handle_webhook(), etc:
    - ask(): Query Twilio state/info
    - tell(): Format Twilio data for output
    - do(): Perform Twilio actions
    """
    
    def __init__(self):
        # Announce we're initializing
        announcer.announce(
            "TWILIO_INITIALIZING",
            ["Starting polymorphic Twilio service..."]
        )
        
        # Load credentials polymorphically
        self._load_credentials()
        
        # Announce credentials loaded
        announcer.announce(
            "TWILIO_CREDENTIALS_LOADED",
            [
                f"Account: {self.account_sid[:8]}...",
                f"Phone: {self.phone_number}"
            ]
        )
        
        # Create Twilio client
        self.client = Client(self.account_sid, self.auth_token)
        
        # Announce client ready
        announcer.announce(
            "TWILIO_CLIENT_READY",
            ["Twilio API client initialized"]
        )
        
        # Flask app for webhooks
        self.app = Flask(__name__)
        
        # Queues for async handling
        self.sms_queue = queue.Queue()
        self.call_queue = queue.Queue()
        
        # Active calls/messages tracking
        self.active_calls = {}
        self.recent_messages = []
        
        # Setup webhook routes
        self._setup_webhooks()
        
        # Announce ourselves polymorphically - full bonjour style
        announcer.announce(
            "PolymorphicTwilio",
            [
                "🔌 I am PolymorphicTwilio - I handle telephony polymorphically",
                "📱 Just ask(), tell(), or do() - I figure out the rest",
                "🎯 No need to remember send_sms() or make_call()",
                "🌐 I accept anything: natural language, objects, whatever",
                f"☎️ Phone: {self.phone_number}",
                "✨ I announce everything I do via bonjour",
                "🚀 Ready to handle calls and SMS!"
            ],
            examples=[
                'twilio.do("call 555-1234 with hello")',
                'twilio.do("text", to="555-1234", body="hi")',
                'twilio.ask("recent messages")',
                'twilio.tell("status")'
            ]
        )
        
        # Announce capabilities
        announcer.announce(
            "TWILIO_CAPABILITIES",
            [
                "INBOUND: Receive calls via /voice webhook",
                "INBOUND: Receive SMS via /sms webhook", 
                "OUTBOUND: Make calls with TTS",
                "OUTBOUND: Send SMS messages",
                "SPEECH: Convert speech to text",
                "TTS: Convert text to speech",
                "POLYMORPHIC: Natural language interface"
            ]
        )
    
    def ask(self, question: Any) -> Any:
        """
        Ask Twilio ANYTHING. It figures out what you want.
        
        Examples:
            twilio.ask("phone number")         # Returns configured number
            twilio.ask("recent messages")      # Returns recent SMS
            twilio.ask("active calls")         # Returns current calls
            twilio.ask("account balance")      # Returns account info
            twilio.ask("capabilities")         # What can I do?
        """
        # Announce what we're being asked
        announcer.announce(
            "TWILIO_ASK",
            [f"Question: {question}"]
        )
        
        q = str(question).lower()
        
        # Phone number queries
        if any(word in q for word in ['phone', 'number', 'from']):
            return self.phone_number
        
        # Message queries
        if any(word in q for word in ['message', 'sms', 'text']):
            if 'recent' in q or 'last' in q:
                return self.recent_messages[-10:]
            if 'count' in q:
                return len(self.recent_messages)
            return self.recent_messages
        
        # Call queries
        if any(word in q for word in ['call', 'voice', 'active']):
            if 'active' in q or 'current' in q:
                return self.active_calls
            if 'count' in q:
                return len(self.active_calls)
            return list(self.active_calls.keys())
        
        # Account queries
        if any(word in q for word in ['balance', 'account', 'credit']):
            account = self.client.api.accounts(self.account_sid).fetch()
            return {
                'balance': account.balance,
                'status': account.status,
                'type': account.type
            }
        
        # Capabilities
        if any(word in q for word in ['capability', 'can', 'what']):
            return [
                "I can send SMS messages",
                "I can make phone calls",
                "I can receive SMS and calls",
                "I can handle interactive voice response",
                "I can transcribe speech to text",
                "Just use do() with natural language!"
            ]
        
        # Status
        if 'status' in q:
            return {
                'phone': self.phone_number,
                'active_calls': len(self.active_calls),
                'recent_messages': len(self.recent_messages),
                'webhook_running': hasattr(self, '_webhook_thread')
            }
        
        return f"I don't understand '{question}'. Try: recent messages, active calls, phone number, capabilities"
    
    def tell(self, format: str = "default", **kwargs) -> Union[str, Dict]:
        """
        Tell about Twilio state in any format.
        
        Examples:
            twilio.tell()                  # Default status
            twilio.tell("discord")         # Format for Discord
            twilio.tell("json")            # Return as JSON
            twilio.tell("brief")           # Quick summary
        """
        # Announce format request
        announcer.announce(
            "TWILIO_TELL",
            [f"Format requested: {format}"]
        )
        
        fmt = format.lower()
        
        if fmt in ["discord", "chat"]:
            return f"📱 **Twilio Status**\n" \
                   f"Phone: {self.phone_number}\n" \
                   f"Active Calls: {len(self.active_calls)}\n" \
                   f"Recent Messages: {len(self.recent_messages)}"
        
        if fmt in ["json", "data"]:
            return {
                'phone': self.phone_number,
                'active_calls': self.active_calls,
                'recent_messages': self.recent_messages[-10:],
                'capabilities': self.ask("capabilities")
            }
        
        if fmt in ["brief", "summary", "short"]:
            return f"Twilio: {self.phone_number} | Calls: {len(self.active_calls)} | Messages: {len(self.recent_messages)}"
        
        # Default: comprehensive status
        return f"PolymorphicTwilio Service\n" \
               f"========================\n" \
               f"Phone: {self.phone_number}\n" \
               f"Account: {self.account_sid[:8]}...\n" \
               f"Active Calls: {len(self.active_calls)}\n" \
               f"Recent Messages: {len(self.recent_messages)}\n" \
               f"Webhook Status: {'Running' if hasattr(self, '_webhook_thread') else 'Stopped'}\n"
    
    def do(self, action: Any, **kwargs) -> Any:
        """
        Do ANYTHING with Twilio. Polymorphic action handler.
        
        Examples:
            twilio.do("send sms to 555-1234: Hello!")
            twilio.do("call", to="555-1234", message="Hello")
            twilio.do("text 555-1234 saying hi")
            twilio.do("start webhooks")
            twilio.do("stop")
        """
        # Announce action request
        announcer.announce(
            "TWILIO_DO",
            [f"Action: {action}", f"Params: {kwargs}"]
        )
        
        act = str(action).lower()
        
        # SMS actions
        if any(word in act for word in ['sms', 'text', 'message']):
            return self._do_sms(act, **kwargs)
        
        # Call actions
        if any(word in act for word in ['call', 'phone', 'dial']):
            return self._do_call(act, **kwargs)
        
        # Webhook actions
        if 'webhook' in act or 'start' in act:
            return self._do_start_webhooks(**kwargs)
        
        if 'stop' in act:
            return self._do_stop()
        
        # Status check
        if 'status' in act or 'check' in act:
            return self.tell("brief")
        
        return f"I don't understand action '{action}'. Try: send sms, make call, start webhooks"
    
    # Private helper methods
    
    def _load_credentials(self):
        """Load Twilio credentials polymorphically"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token]):
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
        
        if not all([self.account_sid, self.auth_token]):
            raise ValueError("No Twilio credentials found!")
    
    def _setup_webhooks(self):
        """Setup Flask webhook routes"""
        @self.app.route('/voice', methods=['POST'])
        def handle_voice():
            """Handle incoming calls polymorphically"""
            call_data = dict(request.values)
            self.active_calls[call_data.get('CallSid')] = call_data
            
            # Announce the call
            announcer.announce(
                "TWILIO_CALL_RECEIVED",
                [f"From: {call_data.get('From')}", f"CallSid: {call_data.get('CallSid')}"]
            )
            
            response = VoiceResponse()
            
            # Check if this is speech result
            speech = request.values.get('SpeechResult')
            if speech:
                # Announce speech received
                announcer.announce(
                    "TWILIO_SPEECH_RECEIVED",
                    [
                        f"💬 Speech input: {speech}",
                        f"From: {call_data.get('From')}"
                    ]
                )
                
                # Process speech through Claude chat!
                try:
                    from claude_chat import ask_one_shot
                    
                    # Get response from Claude
                    claude_response = ask_one_shot(speech)
                    
                    if claude_response:
                        # Announce Claude responded
                        announcer.announce(
                            "TWILIO_CLAUDE_RESPONSE",
                            [
                                f"🤖 Claude response generated",
                                f"Length: {len(claude_response)} chars"
                            ]
                        )
                        
                        # Truncate if too long for TTS (Twilio has limits)
                        if len(claude_response) > 500:
                            claude_response = claude_response[:497] + "..."
                        
                        response.say(claude_response, voice='alice')
                    else:
                        response.say("I couldn't process that. Could you try again?", voice='alice')
                    
                except Exception as e:
                    announcer.announce(
                        "TWILIO_CLAUDE_ERROR",
                        [f"Error connecting to Claude: {e}"]
                    )
                    response.say("Sorry, I'm having trouble connecting to my brain. Please try again.", voice='alice')
                
                response.pause(length=1)
            else:
                response.say("Hello! This is the tournament tracker. Ask me anything about tournaments or players!", voice='alice')
            
            # Always gather more speech
            gather = response.gather(
                input='speech',
                timeout=5,
                speech_timeout='auto',
                action='/voice'
            )
            gather.say("What would you like to know?", voice='alice')
            
            return str(response)
        
        @self.app.route('/sms', methods=['POST'])
        def handle_sms():
            """Handle incoming SMS polymorphically"""
            sms_data = dict(request.values)
            self.recent_messages.append(sms_data)
            
            # Keep only last 100 messages
            if len(self.recent_messages) > 100:
                self.recent_messages = self.recent_messages[-100:]
            
            # Announce the SMS
            announcer.announce(
                "TWILIO_SMS_RECEIVED",
                [f"From: {sms_data.get('From')}", f"Body: {sms_data.get('Body')}"]
            )
            
            # Queue for processing
            self.sms_queue.put(sms_data)
            
            response = MessagingResponse()
            response.message("Message received! Processing...")
            return str(response)
    
    def _do_sms(self, action: str, **kwargs):
        """Send SMS polymorphically"""
        # Extract recipient and message from natural language or kwargs
        to = kwargs.get('to')
        body = kwargs.get('body')
        
        if not to or not body:
            # Try to parse from natural language
            import re
            # Match patterns like "text 555-1234 saying hello"
            match = re.search(r'(\d{3}[-.]?\d{3}[-.]?\d{4})', action)
            if match:
                to = match.group(1)
            
            # Extract message after "saying", "with", or last part
            if 'saying' in action:
                body = action.split('saying', 1)[1].strip()
            elif 'with' in action:
                body = action.split('with', 1)[1].strip()
            elif ':' in action:
                body = action.split(':', 1)[1].strip()
            else:
                body = kwargs.get('message', 'Hello from Tournament Tracker!')
        
        if not to:
            return "Need a recipient! Use: do('text 555-1234 saying hello')"
        
        # Announce we're sending
        announcer.announce(
            "TWILIO_SMS_SENDING",
            [f"Preparing to send SMS to {to}"]
        )
        
        # Send the SMS
        message = self.client.messages.create(
            to=to,
            from_=self.phone_number,
            body=body
        )
        
        # Announce success
        announcer.announce(
            "TWILIO_SMS_SENT",
            [
                f"✅ SMS sent successfully!",
                f"To: {to}",
                f"Body: {body}",
                f"Sid: {message.sid}",
                f"Status: {message.status}"
            ]
        )
        
        return f"SMS sent to {to}: {body}"
    
    def _do_call(self, action: str, **kwargs):
        """Make call polymorphically"""
        # Extract recipient and message
        to = kwargs.get('to')
        message = kwargs.get('message')
        
        if not to or not message:
            # Parse from natural language
            import re
            match = re.search(r'(\d{3}[-.]?\d{3}[-.]?\d{4})', action)
            if match:
                to = match.group(1)
            
            if 'with' in action:
                message = action.split('with', 1)[1].strip()
            elif 'saying' in action:
                message = action.split('saying', 1)[1].strip()
            else:
                message = kwargs.get('text', 'Hello from Tournament Tracker!')
        
        if not to:
            return "Need a recipient! Use: do('call 555-1234 with hello')"
        
        # Announce we're calling
        announcer.announce(
            "TWILIO_CALL_INITIATING",
            [f"Preparing to call {to}"]
        )
        
        # Make the call
        call = self.client.calls.create(
            to=to,
            from_=self.phone_number,
            twiml=f'<Response><Say voice="alice">{message}</Say></Response>'
        )
        
        self.active_calls[call.sid] = {'to': to, 'status': 'initiated'}
        
        # Announce call initiated
        announcer.announce(
            "TWILIO_CALL_MADE",
            [
                f"📞 Call initiated!",
                f"To: {to}",
                f"Message: {message}",
                f"Sid: {call.sid}",
                f"Status: {call.status}"
            ]
        )
        
        return f"Calling {to} with message: {message}"
    
    def _do_start_webhooks(self, port=8080, **kwargs):
        """Start webhook server"""
        if hasattr(self, '_webhook_thread'):
            announcer.announce(
                "TWILIO_WEBHOOK_ALREADY_RUNNING",
                [f"Webhook server already active on port {self._webhook_port}"]
            )
            return "Webhooks already running!"
        
        # Announce starting
        announcer.announce(
            "TWILIO_WEBHOOK_STARTING",
            [f"Starting webhook server on port {port}..."]
        )
        
        def run_server():
            self.app.run(host='0.0.0.0', port=port, debug=False)
        
        self._webhook_thread = threading.Thread(target=run_server, daemon=True)
        self._webhook_port = port
        self._webhook_thread.start()
        
        # Announce ready
        announcer.announce(
            "TWILIO_WEBHOOK_READY",
            [
                f"🌐 Webhook server running!",
                f"Voice URL: http://YOUR_SERVER:{port}/voice",
                f"SMS URL: http://YOUR_SERVER:{port}/sms",
                "Configure these in Twilio console"
            ]
        )
        
        return f"Webhook server started on port {port}"
    
    def _do_stop(self):
        """Stop the service"""
        # Can't actually stop Flask thread, but we can clear data
        self.active_calls.clear()
        return "Service data cleared"

# Global instance
_twilio = None

def get_twilio():
    """Get or create Twilio instance"""
    global _twilio
    if _twilio is None:
        announcer.announce(
            "TWILIO_SINGLETON_CREATE",
            ["Creating global PolymorphicTwilio instance"]
        )
        _twilio = PolymorphicTwilio()
    else:
        announcer.announce(
            "TWILIO_SINGLETON_EXISTS",
            ["Returning existing PolymorphicTwilio instance"]
        )
    return _twilio

# Register as discoverable capability
register_capability("twilio", get_twilio)

if __name__ == "__main__":
    # Example usage
    twilio = get_twilio()
    
    # Natural language usage
    print(twilio.ask("what's your phone number"))
    print(twilio.tell("discord"))
    
    # Start webhooks
    twilio.do("start webhooks", port=8080)
    
    print("Polymorphic Twilio running! Use ask(), tell(), or do() for everything!")
    
    # Keep running
    import time
    while True:
        time.sleep(1)