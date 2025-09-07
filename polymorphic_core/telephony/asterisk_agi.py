#!/usr/bin/env python3
"""
asterisk_agi.py - Polymorphic Asterisk AGI interface
Handles phone calls polymorphically - you just call, it figures out what you want
"""

import sys
import os
import re
from typing import Optional, Dict, Any

# Add parent path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')
from polymorphic_core import announcer

class PolymorphicAGI:
    """
    AGI (Asterisk Gateway Interface) that handles calls polymorphically
    Just like Discord but for real phone calls
    """
    
    def __init__(self):
        self.env = {}
        self.caller_id = None
        self.channel = None
        
        # Read AGI environment from stdin
        self._read_environment()
        
        # Announce ourselves
        announcer.announce(
            "PolymorphicAGI",
            [
                "I handle phone calls polymorphically",
                "I connect Asterisk to Claude",
                "I don't care about SIP, PJSIP, or IAX - just voice",
                "Call me and I figure out what you want",
                "I'm the telephony equivalent of Discord bot"
            ]
        )
    
    def _read_environment(self):
        """Read AGI environment variables from stdin"""
        while True:
            line = sys.stdin.readline().strip()
            if not line:
                break
            if ':' in line:
                key, value = line.split(':', 1)
                self.env[key.strip()] = value.strip()
                
                # Extract important info
                if key == 'agi_callerid':
                    self.caller_id = value.strip()
                elif key == 'agi_channel':
                    self.channel = value.strip()
    
    def send_command(self, command: str) -> str:
        """Send AGI command to Asterisk"""
        print(command)
        sys.stdout.flush()
        
        # Read response
        response = sys.stdin.readline().strip()
        
        # Parse response code
        if response.startswith('200'):
            # Success response format: "200 result=X"
            match = re.search(r'result=(-?\d+)', response)
            if match:
                return match.group(1)
        
        return response
    
    def answer(self):
        """Answer the call"""
        self.send_command("ANSWER")
        announcer.announce(
            "CALL_ANSWERED",
            [f"Caller: {self.caller_id}", f"Channel: {self.channel}"]
        )
    
    def say(self, text: str):
        """Say text using TTS"""
        # Use Asterisk's built-in TTS or espeak
        # For now, use STREAM FILE with pre-generated audio
        announcer.announce(
            "TEXT_TO_SPEECH",
            [f"TEXT: {text}", f"CHANNEL: {self.channel}"]
        )
        
        # Generate audio file path
        audio_file = self._generate_tts(text)
        if audio_file:
            self.stream_file(audio_file)
    
    def _generate_tts(self, text: str) -> Optional[str]:
        """Generate TTS audio file"""
        import hashlib
        import subprocess
        
        # Create unique filename based on text
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        audio_path = f"/tmp/tts_{text_hash}"
        
        try:
            # Use espeak to generate audio
            subprocess.run([
                'espeak',
                '-w', f'{audio_path}.wav',
                text
            ], check=True, capture_output=True)
            
            # Convert to GSM for Asterisk (smaller, telephony-optimized)
            subprocess.run([
                'sox',
                f'{audio_path}.wav',
                '-r', '8000',
                '-c', '1',
                f'{audio_path}.gsm'
            ], check=True, capture_output=True)
            
            return audio_path  # Asterisk adds extension automatically
            
        except Exception as e:
            announcer.announce(
                "TTS_ERROR",
                [f"Failed to generate TTS: {e}"]
            )
            return None
    
    def stream_file(self, filename: str):
        """Stream audio file to caller"""
        # Remove extension - Asterisk adds it
        if '.' in filename:
            filename = filename.rsplit('.', 1)[0]
        
        result = self.send_command(f'STREAM FILE {filename} ""')
        return result
    
    def record_audio(self, timeout: int = 5000) -> Optional[str]:
        """Record audio from caller"""
        import time
        
        filename = f"/tmp/recording_{int(time.time())}"
        
        # Record in wav format, max timeout milliseconds
        result = self.send_command(
            f'RECORD FILE {filename} wav "" {timeout}'
        )
        
        if os.path.exists(f"{filename}.wav"):
            announcer.announce(
                "AUDIO_RECORDED",
                [
                    f"FILE: {filename}.wav",
                    f"CALLER: {self.caller_id}"
                ]
            )
            return f"{filename}.wav"
        
        return None
    
    def get_speech(self, prompt: str = None) -> str:
        """Get speech from caller and transcribe"""
        if prompt:
            self.say(prompt)
        
        # Record audio
        audio_file = self.record_audio()
        
        if audio_file:
            # Announce for transcription service to handle
            announcer.announce(
                "TRANSCRIBE_REQUEST",
                [
                    f"FILE: {audio_file}",
                    f"CALLER: {self.caller_id}",
                    "SERVICE: asterisk"
                ]
            )
            
            # Wait for transcription (in real implementation, would listen for announcement)
            # For now, do it directly
            text = self._transcribe(audio_file)
            
            announcer.announce(
                "TRANSCRIPTION_COMPLETE",
                [
                    f"USER {self.caller_id} said: '{text}'",
                    "SOURCE: phone"
                ]
            )
            
            return text
        
        return ""
    
    def _transcribe(self, audio_file: str) -> str:
        """Transcribe audio using Whisper"""
        try:
            import subprocess
            result = subprocess.run([
                'whisper',
                audio_file,
                '--model', 'base',
                '--output_format', 'txt',
                '--output_dir', '/tmp'
            ], capture_output=True, text=True)
            
            # Read transcription
            txt_file = audio_file.replace('.wav', '.txt')
            if os.path.exists(txt_file):
                with open(txt_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            announcer.announce("TRANSCRIPTION_ERROR", [str(e)])
        
        return ""
    
    def hangup(self):
        """Hang up the call"""
        self.send_command("HANGUP")
        announcer.announce(
            "CALL_ENDED",
            [f"Caller: {self.caller_id}", f"Channel: {self.channel}"]
        )
    
    def run_conversation(self):
        """Main conversation loop"""
        # Answer the call
        self.answer()
        
        # Greet the caller
        self.say("Hello, this is Claude. How can I help you today?")
        
        # Conversation loop
        while True:
            # Get what the caller says
            user_text = self.get_speech()
            
            if not user_text:
                self.say("I didn't catch that. Could you repeat?")
                continue
            
            # Check for goodbye
            if any(word in user_text.lower() for word in ['bye', 'goodbye', 'hang up', 'exit']):
                self.say("Goodbye! Have a great day!")
                break
            
            # Announce the message for Claude to process
            announcer.announce(
                "PHONE_MESSAGE",
                [
                    f"CALLER: {self.caller_id}",
                    f"MESSAGE: {user_text}",
                    "NEEDS_RESPONSE: true"
                ]
            )
            
            # In real implementation, would wait for CLAUDE_RESPONSE announcement
            # For now, just echo back
            response = f"I heard you say: {user_text}"
            
            # Say the response
            self.say(response)
        
        # Hang up
        self.hangup()


def main():
    """Main AGI entry point - called by Asterisk"""
    agi = PolymorphicAGI()
    
    try:
        agi.run_conversation()
    except Exception as e:
        announcer.announce(
            "AGI_ERROR",
            [f"Error in AGI: {e}"]
        )
        agi.say("Sorry, I encountered an error. Please try again later.")
        agi.hangup()


if __name__ == "__main__":
    main()