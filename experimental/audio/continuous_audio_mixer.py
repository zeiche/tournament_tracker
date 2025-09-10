#!/usr/bin/env python3
"""
continuous_audio_mixer.py - Maintains continuous background music
The music NEVER stops or restarts - we just overlay speech on top

⚠️ WARNING: DO NOT RECORD OR SAVE MIXED FILES! ⚠️
- NEVER create temporary files for mixing
- NEVER save mixed audio to disk
- ALWAYS stream in real-time using pipes
- The mix must be REAL-TIME, not pre-recorded
"""

import os
import time
import subprocess
import threading
from collections import deque
from capability_announcer import announcer

class CircularAudioBuffer:
    """Circular buffer for smooth audio streaming"""
    
    def __init__(self, max_size_mb=5):
        self.buffer = deque()
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.current_size = 0
        self.lock = threading.Lock()
    
    def add_chunk(self, chunk: bytes):
        """Add audio chunk to buffer"""
        with self.lock:
            self.buffer.append(chunk)
            self.current_size += len(chunk)
            
            # Remove old chunks if buffer is too large
            while self.current_size > self.max_size and self.buffer:
                old_chunk = self.buffer.popleft()
                self.current_size -= len(old_chunk)
    
    def get_chunk(self) -> bytes:
        """Get next chunk from buffer"""
        with self.lock:
            if self.buffer:
                chunk = self.buffer.popleft()
                self.current_size -= len(chunk)
                return chunk
            return b''
    
    def has_data(self) -> bool:
        """Check if buffer has data"""
        with self.lock:
            return len(self.buffer) > 0

class ContinuousAudioMixer:
    """
    Maintains a continuous music stream that NEVER restarts
    Speech is overlaid on top without affecting the music position
    """
    
    def __init__(self):
        self.music_position = 0.0  # Current position in music file
        self.music_start_time = time.time()  # When we started playing
        self.background_music = "game.wav" if os.path.exists("game.wav") else None
        self.lock = threading.Lock()
        self.audio_buffer = CircularAudioBuffer(max_size_mb=2)  # 2MB buffer
        
        announcer.announce(
            "ContinuousAudioMixer",
            [
                "I maintain CONTINUOUS background music",
                "Music NEVER restarts - just keeps playing",
                "Speech is overlaid WITHOUT restarting music",
                "The music position is tracked continuously",
                f"Music file: {self.background_music}"
            ]
        )
    
    def get_current_music_position(self):
        """Calculate current position in the music file"""
        elapsed = time.time() - self.music_start_time
        # Music duration is about 159 seconds (2:39)
        music_duration = 159.0
        # Loop the position if we've exceeded the duration
        return elapsed % music_duration
    
    def stream_realtime_mix(self, speech_text: str):
        """
        Stream REAL-TIME mix without creating files
        The music doesn't restart - we use the current position
        """
        with self.lock:
            current_position = self.get_current_music_position()
            
            announcer.announce(
                "ContinuousAudioMixer.REALTIME",
                [
                    f"Music position: {current_position:.1f}s",
                    "REAL-TIME streaming - no files",
                    "Music continues from current position"
                ]
            )
            
            # Generate TTS and mix in REAL-TIME using pipes
            if self.background_music:
                # TTS to stdout - use stdout directly
                tts_cmd = ["espeak", "--stdout", speech_text]
                
                # Mix in REAL-TIME with music from current position
                mix_cmd = [
                    "ffmpeg",
                    "-f", "wav",  # Input format
                    "-i", "pipe:0",  # TTS from stdin
                    "-ss", str(current_position),  # START FROM CURRENT POSITION
                    "-i", self.background_music,
                    "-filter_complex",
                    "[1:a]volume=0.35[bg];[0:a]volume=1.0[fg];[fg][bg]amix=inputs=2:duration=first",
                    "-f", "wav",
                    "-ac", "1",
                    "-ar", "8000",
                    "pipe:1"  # Output to stdout
                ]
                
                # Pipe TTS directly to mixer - REAL-TIME!
                tts_proc = subprocess.Popen(tts_cmd, stdout=subprocess.PIPE)
                mix_proc = subprocess.Popen(mix_cmd, stdin=tts_proc.stdout, stdout=subprocess.PIPE)
                
                # Read the REAL-TIME stream in chunks for better streaming
                audio_chunks = []
                chunk_size = 4096
                
                while True:
                    chunk = mix_proc.stdout.read(chunk_size)
                    if not chunk:
                        break
                    audio_chunks.append(chunk)
                    
                    # Prevent excessive memory usage
                    if len(audio_chunks) > 100:  # Limit buffer size
                        break
                
                # Wait for processes to complete
                tts_proc.wait()
                mix_proc.wait()
                
                return b''.join(audio_chunks)
            
            # Fallback - just TTS
            tts_cmd = ["espeak", "-w", "-", speech_text]
            proc = subprocess.Popen(tts_cmd, stdout=subprocess.PIPE)
            return proc.stdout.read()
    
    def stream_continuous(self, speech_text: str):
        """Stream mixed audio with continuous music - REAL-TIME"""
        # Use the REAL-TIME streaming method
        return self.stream_realtime_mix(speech_text)

# Global instance
_continuous_mixer = None

def get_continuous_mixer():
    global _continuous_mixer
    if _continuous_mixer is None:
        _continuous_mixer = ContinuousAudioMixer()
    return _continuous_mixer

if __name__ == "__main__":
    mixer = get_continuous_mixer()
    print("Continuous Audio Mixer initialized")
    print(f"Music position: {mixer.get_current_music_position():.1f}s")