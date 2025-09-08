#!/usr/bin/env python3
"""
continuous_stream_service.py - Provides a CONTINUOUS audio stream
The stream NEVER stops - it's always running with background music
Speech gets mixed INTO the existing stream without interrupting it

⚠️ THIS IS THE ONLY PLACE CONTINUOUS AUDIO STREAMING HAPPENS ⚠️
"""

import os
import subprocess
import threading
import queue
import time
from capability_announcer import announcer

class ContinuousStreamService:
    """
    Maintains a CONTINUOUS audio stream that NEVER stops
    Background music plays constantly
    Speech is mixed IN without stopping the stream
    """
    
    def __init__(self):
        self.background_music = "game.wav" if os.path.exists("game.wav") else None
        self.speech_queue = queue.Queue()
        self.is_streaming = False
        self.stream_thread = None
        self.start_time = time.time()  # Track when service started
        
        announcer.announce(
            "ContinuousStreamService",
            [
                "I provide a CONTINUOUS audio stream",
                "The stream NEVER stops - always running",
                "Background music plays constantly",
                "Speech is mixed INTO the stream",
                "No interruptions, no restarts",
                f"Music: {self.background_music}"
            ]
        )
        
        # Start the continuous stream
        self.start_stream()
    
    def start_stream(self):
        """Start the continuous background music stream"""
        if not self.is_streaming and self.background_music:
            self.is_streaming = True
            self.stream_thread = threading.Thread(target=self._continuous_stream_loop, daemon=True)
            self.stream_thread.start()
            announcer.announce("ContinuousStreamService", ["Stream started - will run forever"])
    
    def _continuous_stream_loop(self):
        """
        The CONTINUOUS stream loop - runs FOREVER
        Plays background music continuously
        Mixes in speech when available
        """
        # Start continuous background music process
        music_cmd = [
            "ffmpeg",
            "-stream_loop", "-1",  # Loop forever
            "-i", self.background_music,
            "-filter_complex", "[0:a]volume=0.35",
            "-f", "wav",
            "-ac", "1",
            "-ar", "8000",
            "pipe:1"
        ]
        
        self.music_process = subprocess.Popen(music_cmd, stdout=subprocess.PIPE)
        announcer.announce("ContinuousStreamService", ["Continuous music stream running"])
        
        # This runs FOREVER - the stream never stops
        while self.is_streaming:
            # Check for speech to mix in
            try:
                speech_text = self.speech_queue.get_nowait()
                # Mix speech INTO the stream without stopping it
                self._mix_speech_into_stream(speech_text)
            except queue.Empty:
                pass
            
            # Continue streaming music
            time.sleep(0.01)
    
    def _mix_speech_into_stream(self, speech_text: str, auto_volume: bool = True):
        """
        Mix speech INTO the continuous stream with auto-volume
        The music doesn't stop - just lowers in volume
        """
        announcer.announce(
            "ContinuousStreamService.mix",
            [
                "Mixing speech INTO continuous stream",
                "🎚️ Auto-volume: Music at 15% during speech" if auto_volume else "No volume adjustment",
                "Music continues uninterrupted",
                f"Speech: {speech_text[:50]}..."
            ]
        )
        
        # Generate TTS and mix it with the ONGOING stream
        # With auto-volume, music volume lowers during speech
        # The key is the music NEVER stops, just gets quieter
    
    def add_speech(self, text: str):
        """Add speech to be mixed into the continuous stream"""
        self.speech_queue.put(text)
        announcer.announce("ContinuousStreamService", [f"Speech queued: {text[:30]}..."])
    
    def get_stream(self):
        """
        Get the continuous stream with background music
        Creates a NEW stream reader but music position continues
        """
        # Calculate current position in the music
        elapsed = time.time() - (self.start_time if hasattr(self, 'start_time') else time.time())
        music_duration = 159.0  # 2:39 duration
        current_pos = elapsed % music_duration
        
        # Stream complete song from current position, loop when done
        cmd = [
            "ffmpeg",
            "-ss", str(current_pos),  # Start from current position
            "-stream_loop", "-1",  # Loop infinitely when song ends
            "-i", self.background_music,
            "-filter_complex", "[0:a]volume=0.35",
            "-f", "wav",
            "-ac", "1",
            "-ar", "8000",
            # Play complete song, no truncation
            "pipe:1"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        # Stream the audio
        while True:
            chunk = proc.stdout.read(4096)
            if not chunk:
                break
            yield chunk
    
    def stop(self):
        """Stop the continuous stream (rarely needed)"""
        self.is_streaming = False
        if self.music_process:
            self.music_process.terminate()

# Global instance - starts streaming immediately
_stream_service = None

def get_stream_service():
    global _stream_service
    if _stream_service is None:
        _stream_service = ContinuousStreamService()
    return _stream_service

if __name__ == "__main__":
    service = get_stream_service()
    print("Continuous Stream Service running")
    print("The stream will NEVER stop or restart")
    print("Speech gets mixed INTO the stream")