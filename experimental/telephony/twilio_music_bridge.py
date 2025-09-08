#!/usr/bin/env python3
"""
twilio_music_bridge.py - Twilio bridge with background music support
Plays "Game On Tonight.wav" or other music in the background
"""

import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from capability_announcer import announcer

class TwilioMusicBridge:
    """Twilio bridge with background music support"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.speech_handlers = []
        self.music_url = None
        
        # Setup route
        self.app.route('/voice', methods=['GET', 'POST'])(self.voice)
        
        # Announce ourselves
        announcer.announce(
            "TwilioMusicBridge",
            [
                "I'm a Twilio bridge with background music",
                "I can play WAV files during calls",
                "Set TWILIO_MUSIC_URL environment variable"
            ]
        )
    
    def set_music_url(self, url: str):
        """Set the background music URL"""
        self.music_url = url
        print(f"🎵 Background music set: {url}")
    
    def register_handler(self, handler):
        """Register a speech handler"""
        self.speech_handlers.append(handler)
        return self
    
    def voice(self):
        """Handle incoming voice calls with music"""
        from_number = request.values.get('From', 'Unknown')
        speech = request.values.get('SpeechResult', '').strip()
        call_sid = request.values.get('CallSid', 'Unknown')
        
        response = VoiceResponse()
        
        # Check for music URL from environment or instance
        music_url = self.music_url or os.getenv('TWILIO_MUSIC_URL')
        
        if not speech:
            # Initial call - play music and greet
            if music_url:
                # Create a conference to mix audio
                # This allows background music with speech
                print(f"🎵 Playing background music: {music_url}")
                
                # Option 1: Simple play (music stops when speaking)
                # response.play(music_url, loop=1)
                
                # Option 2: Use enqueue to create hold music effect
                from twilio.twiml.voice_response import Enqueue
                enqueue = response.enqueue(
                    None,
                    wait_url=music_url,
                    wait_url_method='GET'
                )
                response.leave()
            
            # Welcome message
            response.say(
                "Welcome to Try Hard Tournament Tracker! "
                "The top 8 players are: Monte, Gamer Ace, ForeignSkies, "
                "Marvelous Marco, Tohru, Kiyarash, Andrik, and RandumMNK. "
                "What else would you like to know?",
                voice='alice'
            )
            
            # Gather speech
            gather = response.gather(
                input='speech',
                timeout=3,
                speech_timeout='auto',
                action='/voice',
                language='en-US',
                enhanced=True,
                speechModel='phone_call'
            )
            
            # If music URL exists, we can also play it during gather
            if music_url:
                gather.play(music_url, loop=1)
            
        else:
            # Process speech from handlers
            announcer.announce(
                "TWILIO_MUSIC_SPEECH",
                [f"From: {from_number}", f"Said: {speech}"]
            )
            
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
                response.say("I heard you say: " + speech, voice='alice')
            
            # Continue gathering with music
            response.pause(length=1)
            response.say("What else would you like to know?", voice='alice')
            
            gather = response.gather(
                input='speech',
                timeout=3,
                speech_timeout='auto',
                action='/voice',
                language='en-US',
                enhanced=True,
                speechModel='phone_call'
            )
            
            # Play music during gather if available
            if music_url:
                gather.play(music_url, loop=1)
        
        return str(response)
    
    def run(self, port=8082):
        """Run the Flask app"""
        print(f"🎵 Twilio Music Bridge running on port {port}")
        print(f"📱 Phone: +18788794283 (878-TRY-HARD)")
        print(f"🎤 Voice recognition: ENABLED")
        
        music_url = self.music_url or os.getenv('TWILIO_MUSIC_URL')
        if music_url:
            print(f"🎵 Background music: {music_url}")
        else:
            print("🎵 No background music configured")
            print("   Set TWILIO_MUSIC_URL environment variable")
            print("   Or upload 'Game On Tonight.wav' to a public URL")
        
        self.app.run(host='0.0.0.0', port=port)

# Singleton
_bridge = None

def get_bridge():
    global _bridge
    if _bridge is None:
        _bridge = TwilioMusicBridge()
    return _bridge

if __name__ == "__main__":
    bridge = get_bridge()
    
    # Register tournament handler
    from tournament_voice_handler import handle_tournament_speech
    bridge.register_handler(handle_tournament_speech)
    print("✅ Tournament handler registered")
    
    # Check for local WAV file
    if os.path.exists("Game On Tonight.wav"):
        print("🎵 Found 'Game On Tonight.wav' locally")
        print("   Upload it to a public URL and set TWILIO_MUSIC_URL")
    
    # Example URLs for testing (replace with your own)
    # bridge.set_music_url("https://example.com/game-on-tonight.wav")
    # Or set environment: export TWILIO_MUSIC_URL="https://example.com/music.wav"
    
    bridge.run(port=8082)