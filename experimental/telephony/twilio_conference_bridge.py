#!/usr/bin/env python3
"""
twilio_conference_bridge.py - Twilio with conference room for continuous music
Uses conference to mix background music with speech continuously
"""

import os
from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse, Conference, Dial
from capability_announcer import announcer
from audio_service import get_audio_service

class TwilioConferenceBridge:
    """Twilio bridge using conference for continuous background music"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.audio_service = get_audio_service()
        self.conference_name = "tryhard_music_room"
        
        # Routes
        @self.app.route('/voice', methods=['POST'])
        def voice():
            """Main voice endpoint - puts caller in conference with music"""
            response = VoiceResponse()
            from_number = request.values.get('From', 'Unknown')
            
            # Say welcome
            response.say("Welcome to Try Hard Tournament Tracker!", voice='alice')
            
            # Put caller in conference
            dial = response.dial()
            conference = dial.conference(
                self.conference_name,
                start_conference_on_enter=True,
                end_conference_on_exit=True,
                wait_url="http://64.111.98.139:8082/wait_music",
                wait_method="GET"
            )
            
            return str(response)
        
        @self.app.route('/wait_music', methods=['GET', 'POST'])
        def wait_music():
            """Play music while in conference"""
            response = VoiceResponse()
            
            if self.audio_service.background_music_path:
                # Play background music on loop
                response.play(
                    f"http://64.111.98.139:8082/audio/game_music",
                    loop=0  # Play indefinitely
                )
            else:
                # Fallback to hold music
                response.play("http://demo.twilio.com/docs/classic.mp3", loop=0)
            
            return str(response)
        
        @self.app.route('/audio/<filename>', methods=['GET'])
        def serve_audio(filename):
            """Serve audio files"""
            if filename == "game_music" and self.audio_service.background_music_path:
                return send_file(self.audio_service.background_music_path, mimetype='audio/wav')
            return "Not found", 404
        
        # Announce
        announcer.announce(
            "TwilioConferenceBridge",
            [
                "I use Twilio conferences for continuous music",
                "Background music plays throughout the call",
                "Speech and music mix naturally"
            ]
        )
    
    def run(self, port=8083):
        """Run the server"""
        print(f"🎵 Twilio Conference Bridge on port {port}")
        print(f"🎵 Continuous background music enabled")
        self.app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    bridge = TwilioConferenceBridge()
    bridge.run()