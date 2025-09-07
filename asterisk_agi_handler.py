#!/usr/bin/env python3
"""
asterisk agi handler for claude integration

handles calls from asterisk and bridges to claude/twilio
implements agi protocol for real-time call processing
"""

import sys
import os
import re
import json
import asyncio
from pathlib import Path
from datetime import datetime

# add parent dir for imports
sys.path.append(str(Path(__file__).parent))

from bonjour_twilio import BonjourTwilio
from claude_service import ClaudeService
from capability_announcer import CapabilityAnnouncer

class AGI:
    """
    asterisk gateway interface handler
    
    implements agi protocol for asterisk communication
    """
    
    def __init__(self):
        """initialize agi and read environment"""
        self.env = {}
        self.bonjour = BonjourTwilio()
        self.claude = ClaudeService()
        self.announcer = CapabilityAnnouncer("asterisk_agi")
        
        # read agi environment from stdin
        self._read_environment()
        
        # announce ourselves
        self._announce_capabilities()
        
    def _read_environment(self):
        """read agi environment variables from asterisk"""
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                break
            if ':' in line:
                key, value = line.split(':', 1)
                self.env[key.strip()] = value.strip()
                
    def _announce_capabilities(self):
        """announce agi capabilities"""
        self.announcer.announce(
            capabilities=[
                "handling asterisk agi calls",
                "bridging calls to claude ai",
                "managing call flow and ivr",
                "recording and transcribing calls",
                "text-to-speech responses"
            ],
            metadata={
                "protocol": "agi",
                "asterisk_version": self.env.get('agi_version', 'unknown'),
                "channel": self.env.get('agi_channel', 'unknown')
            }
        )
        
    def send_command(self, command: str) -> str:
        """
        send agi command to asterisk
        
        args:
            command: agi command to send
            
        returns:
            asterisk response
        """
        print(command)
        sys.stdout.flush()
        response = sys.stdin.readline().strip()
        return response
        
    def get_variable(self, variable: str) -> str:
        """get asterisk channel variable"""
        response = self.send_command(f'GET VARIABLE {variable}')
        # parse response: 200 result=1 (value)
        match = re.search(r'\((.*?)\)', response)
        if match:
            return match.group(1)
        return ""
        
    def set_variable(self, variable: str, value: str):
        """set asterisk channel variable"""
        self.send_command(f'SET VARIABLE {variable} "{value}"')
        
    def answer(self):
        """answer the call"""
        self.send_command('ANSWER')
        
    def hangup(self):
        """hangup the call"""
        self.send_command('HANGUP')
        
    def stream_file(self, filename: str, escape_digits: str = ''):
        """
        play audio file
        
        args:
            filename: file to play (without extension)
            escape_digits: dtmf digits that can interrupt
        """
        self.send_command(f'STREAM FILE {filename} "{escape_digits}"')
        
    def record_file(self, filename: str, format: str = 'wav', 
                    escape_digits: str = '#', timeout: int = 60000,
                    silence: int = 3000) -> str:
        """
        record audio from caller
        
        args:
            filename: file to save to
            format: audio format
            escape_digits: digits to stop recording
            timeout: max recording time in ms
            silence: silence detection in ms
            
        returns:
            digit pressed or timeout
        """
        response = self.send_command(
            f'RECORD FILE {filename} {format} "{escape_digits}" {timeout} 0 1 {silence}'
        )
        return response
        
    def say_text(self, text: str):
        """
        say text using tts
        
        args:
            text: text to speak
        """
        # use festival or espeak for tts
        # for now, use asterisk's say functions
        for char in text:
            if char.isdigit():
                self.send_command(f'SAY DIGIT {char} ""')
            elif char.isalpha():
                self.send_command(f'SAY ALPHA {char} ""')
                
    def get_data(self, filename: str, timeout: int = 10000, 
                 max_digits: int = 10) -> str:
        """
        play file and get dtmf input
        
        args:
            filename: prompt to play
            timeout: timeout in ms
            max_digits: max digits to collect
            
        returns:
            digits pressed
        """
        response = self.send_command(
            f'GET DATA {filename} {timeout} {max_digits}'
        )
        # parse response: 200 result=12345
        match = re.search(r'result=(\d+)', response)
        if match:
            return match.group(1)
        return ""
        
    async def handle_call(self):
        """main call handler"""
        try:
            # answer the call
            self.answer()
            
            # get call info
            caller_id = self.get_variable('CALLERID(num)')
            channel = self.env.get('agi_channel', 'unknown')
            
            # announce call handling
            self.announcer.announce(
                capabilities=[f"handling call from {caller_id}"],
                metadata={'channel': channel}
            )
            
            # greeting
            self.stream_file('hello')
            
            # main loop
            while True:
                # record user input
                recording_file = f"/tmp/agi_recording_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.record_file(recording_file, 'wav', '#', 10000, 2000)
                
                # transcribe (would use real transcription)
                # user_input = await self.bonjour.transcribe_audio(audio_data)
                user_input = "test input"  # placeholder
                
                # get claude's response
                response = await self.claude.process_message(
                    f"phone call from {caller_id}: {user_input}"
                )
                
                # speak response (would use real tts)
                self.say_text(response[:100])  # limit for now
                
                # check if caller hung up
                status = self.get_variable('CHANNEL(state)')
                if status != 'Up':
                    break
                    
        except Exception as e:
            self.announcer.announce(
                capabilities=[f"error in call handling: {str(e)}"],
                metadata={'error': str(e)}
            )
        finally:
            self.hangup()
            

def main():
    """main entry point for agi script"""
    agi = AGI()
    
    # run async handler
    asyncio.run(agi.handle_call())
    

if __name__ == "__main__":
    main()