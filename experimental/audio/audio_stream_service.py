#!/usr/bin/env python3
"""
audio_stream_service.py - Real-time audio streaming and mixing
Streams mixed audio on-the-fly instead of creating files
"""

import os
import subprocess
from flask import Response, Flask
from capability_announcer import announcer

class AudioStreamService:
    """
    Real-time audio streaming service
    Mixes audio on-the-fly and streams it
    """
    
    def __init__(self):
        self.background_music = None
        self.app = Flask(__name__)
        
        # Check for music file
        if os.path.exists("game.wav"):
            self.background_music = "game.wav"
        
        # Announce
        announcer.announce(
            "AudioStreamService",
            [
                "I stream mixed audio in real-time",
                "No pre-recorded files - mix on the fly",
                "Continuous background music",
                "Low latency streaming"
            ]
        )
    
    def stream_mixed_audio(self, speech_text: str):
        """
        Stream mixed audio in real-time
        Generates and streams audio without saving to disk
        """
        def generate():
            # Create TTS on the fly
            tts_cmd = [
                "espeak", "-w", "-", speech_text
            ]
            
            # Mix with background music in real-time
            if self.background_music:
                # Use ffmpeg to mix in real-time and stream
                mix_cmd = [
                    "ffmpeg",
                    "-i", "pipe:0",  # TTS from stdin
                    "-i", self.background_music,
                    "-filter_complex",
                    "[1:a]volume=0.35,aloop=loop=-1:size=2e+09[bg];"
                    "[0:a]volume=1.0[fg];"
                    "[fg][bg]amix=inputs=2:duration=first",
                    "-f", "wav",
                    "-ac", "1",
                    "-ar", "8000",
                    "pipe:1"  # Output to stdout
                ]
                
                # Pipe TTS to mixer
                tts_proc = subprocess.Popen(tts_cmd, stdout=subprocess.PIPE)
                mix_proc = subprocess.Popen(mix_cmd, stdin=tts_proc.stdout, stdout=subprocess.PIPE)
                
                # Stream the output
                while True:
                    chunk = mix_proc.stdout.read(4096)
                    if not chunk:
                        break
                    yield chunk
            else:
                # No background music, just stream TTS
                proc = subprocess.Popen(tts_cmd, stdout=subprocess.PIPE)
                while True:
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        break
                    yield chunk
        
        return Response(generate(), mimetype='audio/wav')
    
    def create_continuous_stream(self):
        """
        Create a continuous music stream that doesn't restart
        Uses a circular buffer approach
        """
        def generate():
            if not self.background_music:
                return
            
            # Stream music continuously
            cmd = [
                "ffmpeg",
                "-stream_loop", "-1",  # Loop infinitely
                "-i", self.background_music,
                "-f", "wav",
                "-ac", "1",
                "-ar", "8000",
                "pipe:1"
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
        
        return Response(generate(), mimetype='audio/wav')

# Global instance
_stream_service = None

def get_stream_service():
    global _stream_service
    if _stream_service is None:
        _stream_service = AudioStreamService()
    return _stream_service

if __name__ == "__main__":
    service = get_stream_service()
    print("Audio Stream Service initialized")
    print(f"Background music: {service.background_music}")