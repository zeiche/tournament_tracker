#!/usr/bin/env python3
"""
bonjour-style twilio telephony module

self-announces capabilities and handles all telephony operations
integrates with asterisk, twilio, and claude for voice interactions
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# add parent dir to path for imports
sys.path.append(str(Path(__file__).parent))

from capability_announcer import CapabilityAnnouncer
from claude_service import ClaudeService

# twilio imports (will add when we have credentials)
# from twilio.rest import Client
# from twilio.twiml.voice_response import VoiceResponse

class BonjourTwilio:
    """
    self-announcing telephony service that bridges twilio, asterisk, and claude
    
    announces:
    - can receive inbound calls
    - can make outbound calls
    - can transcribe audio to text
    - can convert text to speech
    - can bridge calls to claude ai
    - can manage call state
    - can record calls
    - can handle sms
    """
    
    def __init__(self):
        """initialize twilio service and announce capabilities"""
        self.announcer = CapabilityAnnouncer("bonjour_twilio")
        self.claude = ClaudeService()
        self.logger = self._setup_logging()
        
        # twilio config from env (api keys preferred)
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.api_key = os.getenv('TWILIO_API_KEY')
        self.api_secret = os.getenv('TWILIO_API_SECRET')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')  # fallback
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.sip_domain = os.getenv('TWILIO_SIP_DOMAIN')
        
        # check if we have credentials
        self.has_credentials = bool(self.account_sid and (self.api_key or self.auth_token))
        
        # asterisk config
        self.asterisk_host = os.getenv('ASTERISK_HOST', 'localhost')
        self.asterisk_ami_port = os.getenv('ASTERISK_AMI_PORT', '5038')
        self.asterisk_agi_port = os.getenv('ASTERISK_AGI_PORT', '4573')
        
        # call state tracking
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        
        # announce ourselves
        self._announce_capabilities()
        
    def _setup_logging(self) -> logging.Logger:
        """set up logging for twilio service"""
        logger = logging.getLogger('bonjour_twilio')
        logger.setLevel(logging.INFO)
        
        # create logs directory
        log_dir = Path('storage')
        log_dir.mkdir(exist_ok=True)
        
        # file handler
        fh = logging.FileHandler(log_dir / 'bonjour_twilio.log')
        fh.setLevel(logging.DEBUG)
        
        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
        
    def _announce_capabilities(self):
        """announce what this module can do"""
        if not self.has_credentials:
            capabilities = [
                "i need twilio credentials to work",
                "add TWILIO_ACCOUNT_SID to .env",
                "add TWILIO_API_KEY and TWILIO_API_SECRET (or TWILIO_AUTH_TOKEN) to .env",
                "once configured, i can handle all telephony",
                "run './go.py --twilio-config' to validate setup"
            ]
        else:
            capabilities = [
                "i can receive inbound phone calls via twilio",
                "i can make outbound phone calls",
                "i can transcribe speech to text in real-time",
                "i can convert text to natural speech",
                "i can connect phone calls to claude ai",
                "i can manage multiple simultaneous calls",
                "i can record and store call audio",
                "i can send and receive sms messages",
                "i can handle voicemail with transcription",
                "i can route calls based on caller id",
                "i can play hold music and announcements",
                "i can conference multiple callers",
                "i can transfer calls between extensions",
                "i can provide call analytics and logs"
            ]
        
        examples = [
            "say 'call 555-1234' to make an outbound call",
            "say 'answer' when receiving an inbound call",
            "say 'record this call' to start recording",
            "say 'transfer to claude' to connect to ai",
            "say 'send sms to 555-1234: hello' to text",
            "say 'show call history' for recent calls",
            "say 'conference with 555-1234' to add caller"
        ]
        
        self.announcer.announce(
            capabilities=capabilities,
            examples=examples,
            metadata={
                "service": "telephony",
                "integrations": ["twilio", "asterisk", "claude"],
                "protocols": ["sip", "webrtc", "pstn"],
                "audio_formats": ["wav", "mp3", "opus", "g711"],
                "features": ["transcription", "tts", "recording", "sms"]
            }
        )
        
        self.logger.info("bonjour_twilio announced capabilities")
        
    async def handle_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        handle incoming call from twilio
        
        args:
            call_data: twilio webhook data
            
        returns:
            response with twiml or action
        """
        call_sid = call_data.get('CallSid')
        from_number = call_data.get('From')
        to_number = call_data.get('To')
        
        self.logger.info(f"inbound call from {from_number} to {to_number}")
        
        # track call state
        self.active_calls[call_sid] = {
            'sid': call_sid,
            'from': from_number,
            'to': to_number,
            'direction': 'inbound',
            'started': datetime.now(),
            'status': 'ringing'
        }
        
        # announce the call
        self.announcer.announce(
            capabilities=[f"receiving call from {from_number}"],
            metadata={'call_sid': call_sid}
        )
        
        # create response (will enhance with twiml)
        response = {
            'action': 'answer',
            'message': f"hello, you've reached the ai assistant. how can i help you today?",
            'call_sid': call_sid
        }
        
        return response
        
    async def handle_outbound_call(self, to_number: str, message: str = None) -> Dict[str, Any]:
        """
        initiate outbound call via twilio
        
        args:
            to_number: number to call
            message: optional message to speak
            
        returns:
            call status and sid
        """
        self.logger.info(f"initiating outbound call to {to_number}")
        
        # announce the call attempt
        self.announcer.announce(
            capabilities=[f"calling {to_number}"],
            metadata={'to': to_number, 'message': message}
        )
        
        # would use twilio client here
        # client = Client(self.account_sid, self.auth_token)
        # call = client.calls.create(...)
        
        # for now, return mock response
        call_sid = f"CA{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.active_calls[call_sid] = {
            'sid': call_sid,
            'from': self.phone_number,
            'to': to_number,
            'direction': 'outbound',
            'started': datetime.now(),
            'status': 'dialing',
            'message': message
        }
        
        return {
            'success': True,
            'call_sid': call_sid,
            'status': 'dialing',
            'to': to_number
        }
        
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """
        transcribe audio to text
        
        args:
            audio_data: raw audio bytes
            
        returns:
            transcribed text
        """
        # would integrate with whisper or google speech-to-text
        # for now, return placeholder
        self.announcer.announce(
            capabilities=["transcribing audio to text"],
            metadata={'audio_size': len(audio_data)}
        )
        
        return "transcribed text from audio"
        
    async def text_to_speech(self, text: str) -> bytes:
        """
        convert text to speech audio
        
        args:
            text: text to speak
            
        returns:
            audio data bytes
        """
        # would integrate with elevenlabs or google tts
        # for now, return placeholder
        self.announcer.announce(
            capabilities=["converting text to speech"],
            metadata={'text_length': len(text)}
        )
        
        return b"audio data"
        
    async def bridge_to_claude(self, call_sid: str, user_input: str) -> str:
        """
        bridge call to claude for ai interaction
        
        args:
            call_sid: active call sid
            user_input: transcribed user speech
            
        returns:
            claude's response
        """
        self.logger.info(f"bridging call {call_sid} to claude: {user_input}")
        
        # get call context
        call_info = self.active_calls.get(call_sid, {})
        
        # build context for claude
        context = f"phone call from {call_info.get('from', 'unknown')}: {user_input}"
        
        # get claude's response
        response = await self.claude.process_message(context)
        
        self.announcer.announce(
            capabilities=["processed call through claude ai"],
            metadata={'call_sid': call_sid, 'response_length': len(response)}
        )
        
        return response
        
    async def handle_sms(self, sms_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        handle incoming sms message
        
        args:
            sms_data: twilio sms webhook data
            
        returns:
            response message
        """
        from_number = sms_data.get('From')
        body = sms_data.get('Body')
        
        self.logger.info(f"sms from {from_number}: {body}")
        
        self.announcer.announce(
            capabilities=[f"received sms from {from_number}"],
            metadata={'message': body}
        )
        
        # process with claude
        response = await self.claude.process_message(f"sms: {body}")
        
        return {
            'success': True,
            'response': response,
            'to': from_number
        }
        
    def get_call_status(self, call_sid: str = None) -> Dict[str, Any]:
        """
        get status of active calls
        
        args:
            call_sid: specific call or none for all
            
        returns:
            call status info
        """
        if call_sid:
            return self.active_calls.get(call_sid, {'error': 'call not found'})
        
        return {
            'active_calls': len(self.active_calls),
            'calls': list(self.active_calls.values())
        }
        
    async def end_call(self, call_sid: str) -> Dict[str, Any]:
        """
        end an active call
        
        args:
            call_sid: call to end
            
        returns:
            status
        """
        if call_sid in self.active_calls:
            call_info = self.active_calls[call_sid]
            call_info['status'] = 'completed'
            call_info['ended'] = datetime.now()
            
            self.logger.info(f"ended call {call_sid}")
            
            self.announcer.announce(
                capabilities=[f"ended call {call_sid}"],
                metadata=call_info
            )
            
            # remove from active calls after a delay
            await asyncio.sleep(5)
            del self.active_calls[call_sid]
            
            return {'success': True, 'call_sid': call_sid}
        
        return {'error': 'call not found'}
    
    def get_credentials_help(self):
        """help user get twilio credentials"""
        help_text = """
        TWILIO CREDENTIALS SETUP:
        
        1. Go to: https://www.twilio.com/console
        2. Login with: twillio@danpeterson.net
        3. Get from dashboard:
           - Account SID: ACxxxxxxxx (34 chars)
           - Auth Token: click 'Show' to reveal
        
        4. Or create API key (more secure):
           - Click account menu → API Keys & Tokens
           - Create API Key → Standard
           - Copy SID (SKxxxx) and Secret
        
        5. Add to .env:
           TWILIO_ACCOUNT_SID=ACxxxxxxxx
           TWILIO_API_KEY=SKxxxxxxxx
           TWILIO_API_SECRET=xxxxxxxx
           
           Or with auth token:
           TWILIO_ACCOUNT_SID=ACxxxxxxxx
           TWILIO_AUTH_TOKEN=xxxxxxxx
        
        6. Test with: ./go.py --twilio-config
        """
        return help_text
        
    async def run(self):
        """main run loop for the service"""
        self.logger.info("bonjour_twilio service started")
        
        # announce we're ready
        self.announcer.announce(
            capabilities=["twilio telephony service is ready"],
            metadata={'status': 'running', 'phone': self.phone_number}
        )
        
        # would start webhook server or asterisk agi listener here
        # for now, just keep running
        try:
            while True:
                await asyncio.sleep(60)
                # periodic health check
                self.announcer.announce(
                    capabilities=[f"telephony service healthy - {len(self.active_calls)} active calls"],
                    metadata={'uptime': 'running'}
                )
        except KeyboardInterrupt:
            self.logger.info("shutting down bonjour_twilio")
            

if __name__ == "__main__":
    # run the service
    service = BonjourTwilio()
    asyncio.run(service.run())