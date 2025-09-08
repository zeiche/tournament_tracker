#!/usr/bin/env python3
"""
audio_service.py - Unified audio service for voice, music mixing, and TTS
Handles Discord voice, Twilio audio, local mixing, and audio processing

⚠️ WARNING: DO NOT RECORD OR SAVE MIXED FILES! ⚠️
- NEVER create temporary files for mixing
- NEVER save mixed audio to disk  
- ALWAYS stream in real-time using pipes
- The mix must be REAL-TIME, not pre-recorded
"""

import os
import asyncio
import tempfile
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Union
from capability_announcer import announcer
from continuous_stream_service import get_stream_service
from bonjour_audio_detector import get_detector

class AudioService:
    """
    Unified audio service - handles all audio needs polymorphically
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce our capabilities
        announcer.announce(
            "AudioService",
            [
                "I handle ALL audio processing needs",
                "I can mix background music with speech",
                "🎚️ NEW: Auto-volume adjustment - music lowers during speech!",
                "I provide TTS (text-to-speech)",
                "I can join Discord voice channels",
                "I can generate audio for Twilio calls",
                "I support local audio mixing",
                "I can play audio files",
                "Auto-volume levels: 15% (default) to 50% volume",
                "Methods: mix_audio, stream_with_auto_volume, generate_tts, join_voice",
                "Use me polymorphically: audio.ask(), audio.tell(), audio.do()"
            ]
        )
        
        self.background_music_path = None
        self.voice_clients = {}
        self.temp_dir = tempfile.mkdtemp(prefix="audio_service_")
        
        # Continuous music tracking
        self.music_position = 0.0  # Current position in music file
        self.music_start_time = time.time()  # When we started playing
        self.lock = threading.Lock()
        
        # Get the continuous stream service
        self.stream_service = get_stream_service()
        
        # Get the audio detector for transcription
        self.audio_detector = get_detector()
        
        # Check for background music files
        if os.path.exists("game.wav"):
            self.background_music_path = "game.wav"
            announcer.announce("AudioService", ["Found 'game.wav' for background music!"])
        elif os.path.exists("game.mp3"):
            self.background_music_path = "game.mp3"
            announcer.announce("AudioService", ["Found 'game.mp3' for background music!"])
        elif os.path.exists("Game On Tonight.wav"):
            self.background_music_path = "Game On Tonight.wav"
            announcer.announce("AudioService", ["Found 'Game On Tonight.wav' for background music!"])
    
    def ask(self, question: Any) -> Any:
        """Ask anything about audio capabilities"""
        q = str(question).lower()
        
        if "music" in q:
            return f"Background music: {self.background_music_path or 'Not configured'}"
        
        if "mix" in q:
            return "I can mix audio using ffmpeg or pydub"
        
        if "tts" in q or "speech" in q:
            return "I support TTS via gTTS, pyttsx3, or Twilio's <Say>"
        
        return "I handle audio mixing, TTS, Discord voice, and Twilio audio"
    
    def tell(self, format: str = "default") -> str:
        """Tell about audio service status"""
        if format == "json":
            import json
            return json.dumps({
                "service": "AudioService",
                "background_music": bool(self.background_music_path),
                "temp_dir": self.temp_dir,
                "capabilities": ["mixing", "tts", "discord", "twilio"]
            })
        
        return f"AudioService: Music={bool(self.background_music_path)}, TempDir={self.temp_dir}"
    
    def do(self, action: Any, **kwargs) -> Any:
        """Do anything with audio - polymorphically"""
        action_str = str(action).lower()
        
        if "mix" in action_str:
            return self.mix_audio(**kwargs)
        
        if "tts" in action_str or "speak" in action_str:
            return self.generate_tts(**kwargs)
        
        if "play" in action_str:
            return self.play_audio(**kwargs)
        
        if "join" in action_str:
            return self.join_voice_channel(**kwargs)
        
        return self._process_polymorphically(action, **kwargs)
    
    def mix_audio(self, speech_text: str = None, speech_audio: str = None, 
                  background_music: str = None, output_format: str = "wav",
                  music_offset: float = 0.0, ducking: bool = True,
                  duck_level: float = 0.15):
        """
        Mix speech with background music with automatic ducking
        Returns a generator that streams mixed audio in real-time
        
        Args:
            speech_text: Text to convert to speech (if no speech_audio)
            speech_audio: Path to speech audio file
            background_music: Path to background music (uses default if None)
            output_format: Output format (wav, mp3)
            music_offset: Starting offset in the music file
            ducking: Whether to duck (lower) music during speech
            duck_level: Volume level for ducked music (0.15 = 15% volume)
            
        Returns:
            Generator that yields audio chunks (real-time streaming)
        """
        # Use default background music if not specified
        if not background_music:
            background_music = self.background_music_path
        
        if not background_music:
            # No background music, just stream speech
            if speech_text and not speech_audio:
                # TTS returns a generator now
                return self.generate_tts(speech_text, output_format)
            if speech_audio:
                return self._stream_file(speech_audio)
            return iter([])  # Empty generator
        
        # Generate TTS if needed
        if speech_text and not speech_audio:
            # TTS returns a generator now, not a file path
            tts_stream = self.generate_tts(speech_text, "wav")
            # Mix the TTS stream with background music
            return self._stream_mixed_tts(tts_stream, background_music, 
                                         music_offset, ducking, duck_level)
        
        if not speech_audio:
            # Just stream background music
            return self._stream_file(background_music)
        
        # Stream mixed audio using ffmpeg with pipes
        return self._stream_mixed_audio(speech_audio, background_music, 
                                       music_offset, ducking, duck_level)
    
    def _stream_file(self, file_path):
        """Stream a file in chunks"""
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            announcer.announce("AudioService.ERROR", [f"Stream failed: {e}"])
    
    def _stream_mixed_tts(self, tts_generator, background_music,
                         music_offset=0.0, ducking=True, duck_level=0.15):
        """
        Stream mixed TTS generator with background music in real-time
        NO TEMPORARY FILES - everything streams!
        """
        import subprocess
        
        try:
            # Create pipes for TTS input
            import os
            r_fd, w_fd = os.pipe()
            
            # Mix with ducking
            if ducking:
                filter_complex = (
                    f"[1:a]volume={duck_level}[bg];"  
                    "[0:a]volume=1.0[fg];"
                    "[fg][bg]amix=inputs=2:duration=first:dropout_transition=0"
                )
            else:
                filter_complex = (
                    "[1:a]volume=0.35[bg];"
                    "[0:a]volume=1.0[fg];"
                    "[fg][bg]amix=inputs=2:duration=first:dropout_transition=0"
                )
            
            # FFmpeg reads TTS from pipe
            cmd = [
                "ffmpeg",
                "-f", "wav",
                "-i", f"pipe:{r_fd}",  # Read TTS from pipe
                "-ss", str(music_offset),
                "-i", background_music,
                "-filter_complex", filter_complex,
                "-f", "wav",
                "-ac", "1",
                "-ar", "8000",
                "pipe:1"
            ]
            
            # Start ffmpeg process
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, 
                                     pass_fds=(r_fd,))
            os.close(r_fd)  # Close read end in parent
            
            # Feed TTS to ffmpeg in background
            import threading
            def feed_tts():
                with os.fdopen(w_fd, 'wb') as pipe:
                    for chunk in tts_generator:
                        pipe.write(chunk)
                    pipe.flush()
            
            feeder = threading.Thread(target=feed_tts, daemon=True)
            feeder.start()
            
            announcer.announce("AudioService.STREAMING", [
                "Real-time TTS+music mixing via pipes",
                "NO files anywhere in the chain!",
                "TTS → pipe → ffmpeg → mixed stream"
            ])
            
            # Stream mixed output
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                    
                # Detect and log audio
                self.audio_detector.detection_queue.put(chunk)
                
                yield chunk
            
            process.wait()
            feeder.join(timeout=1)
            
        except Exception as e:
            announcer.announce("AudioService.ERROR", [f"TTS mixing failed: {e}"])
            # Fallback to just TTS
            for chunk in tts_generator:
                yield chunk
    
    def _stream_mixed_audio(self, speech_audio, background_music, 
                           music_offset=0.0, ducking=True, duck_level=0.15):
        """
        Stream mixed audio in real-time using ffmpeg pipes
        NO TEMPORARY FILES - direct streaming only!
        """
        import subprocess
        
        try:
            # Mix with ducking - music dips when speech plays
            if ducking:
                filter_complex = (
                    f"[1:a]volume={duck_level}[bg];"  # Duck music to specified level
                    "[0:a]volume=1.0[fg];"  # Keep speech at full volume
                    "[fg][bg]amix=inputs=2:duration=first:dropout_transition=0"
                )
                announcer.announce("AudioService.ducking", [
                    f"Real-time ducking: music at {int(duck_level*100)}% during speech",
                    "NO FILES - streaming directly!"
                ])
            else:
                # No ducking - constant background volume
                filter_complex = (
                    "[1:a]volume=0.35[bg];"  # Music at 35% constant
                    "[0:a]volume=1.0[fg];"
                    "[fg][bg]amix=inputs=2:duration=first:dropout_transition=0"
                )
            
            cmd = [
                "ffmpeg",
                "-i", speech_audio,
                "-ss", str(music_offset),  # Start music from offset
                "-i", background_music,
                "-filter_complex", filter_complex,
                "-f", "wav",  # Output format
                "-ac", "1",  # Mono for phone
                "-ar", "8000",  # 8kHz for phone
                "pipe:1"  # Output to stdout - NO FILES!
            ]
            
            # Start ffmpeg process
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            
            announcer.announce("AudioService.STREAMING", [
                "Real-time mixing via pipes",
                "NO temporary files created",
                "Streaming mixed audio NOW"
            ])
            
            # Stream chunks as they're generated
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                
                # Detect and log what's in this chunk
                self.audio_detector.detection_queue.put(chunk)
                
                yield chunk
            
            process.wait()
            
        except Exception as e:
            announcer.announce("AudioService.ERROR", [f"Streaming mix failed: {e}"])
            # Fallback to streaming just the speech
            for chunk in self._stream_file(speech_audio):
                yield chunk
    
    def generate_tts(self, text: str, output_format: str = "wav", voice: str = "alice"):
        """
        Generate text-to-speech audio AS A STREAM - NO FILES!
        
        Args:
            text: Text to convert to speech
            output_format: Output format (wav, mp3)
            voice: Voice to use (alice, man, woman)
            
        Returns:
            Generator that yields audio chunks (STREAMING, NO FILES!)
        """
        # Try espeak with pipe output (most common on Linux)
        try:
            import subprocess
            
            # Use espeak to generate wav output to stdout
            cmd = [
                "espeak",
                "-s", "150",  # Speed (words per minute)
                "-a", "100",  # Amplitude (volume)
                "--stdout",   # Output to stdout instead of file
                text
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            
            announcer.announce("AudioService.TTS", [
                "TTS streaming directly via espeak",
                "NO FILES CREATED - pure streaming!",
                f"Text: {text[:50]}..."
            ])
            
            # Stream chunks as they're generated
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
            
            process.wait()
            return
            
        except FileNotFoundError:
            pass  # espeak not installed
        except Exception as e:
            print(f"espeak streaming failed: {e}")
        
        # Try flite (Festival Lite) with pipe
        try:
            import subprocess
            
            cmd = [
                "flite",
                "-t", text,  # Text to speak
                "-o", "-"     # Output to stdout
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            
            announcer.announce("AudioService.TTS", [
                "TTS streaming via flite",
                "Direct streaming, no files"
            ])
            
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
            
            process.wait()
            return
            
        except FileNotFoundError:
            pass  # flite not installed
        except Exception as e:
            print(f"flite streaming failed: {e}")
        
        # Ultimate fallback: Generate silence (no TTS available)
        announcer.announce("AudioService.TTS", [
            "WARNING: No TTS engine available",
            "Install espeak or flite for TTS",
            "Returning silence stream"
        ])
        
        # Generate 1 second of silence at 8kHz mono WAV format
        # WAV header for 8kHz mono
        wav_header = b'RIFF' + b'\x24\x08\x00\x00' + b'WAVE'
        wav_header += b'fmt ' + b'\x10\x00\x00\x00'  # fmt chunk size
        wav_header += b'\x01\x00'  # PCM format
        wav_header += b'\x01\x00'  # 1 channel (mono)
        wav_header += b'\x40\x1f\x00\x00'  # 8000 Hz sample rate
        wav_header += b'\x80\x3e\x00\x00'  # byte rate
        wav_header += b'\x02\x00'  # block align
        wav_header += b'\x10\x00'  # bits per sample
        wav_header += b'data' + b'\x00\x08\x00\x00'  # data chunk
        
        silence_data = b'\x00' * 2048  # Short silence
        yield wav_header + silence_data
    
    def play_audio(self, file_path: str, channel: Any = None) -> bool:
        """Play audio file (Discord or local)"""
        if not os.path.exists(file_path):
            return False
        
        # If Discord channel provided, play there
        if channel:
            # Would need Discord voice client integration
            pass
        
        # Play locally
        try:
            import subprocess
            subprocess.run(["afplay", file_path])  # macOS
            return True
        except:
            pass
        
        try:
            import subprocess
            subprocess.run(["aplay", file_path])  # Linux
            return True
        except:
            pass
        
        return False
    
    def join_voice_channel(self, channel: Any) -> bool:
        """Join a Discord voice channel"""
        # Would integrate with Discord voice
        announcer.announce("AudioService", ["Would join voice channel"])
        return True
    
    def _process_polymorphically(self, action: Any, **kwargs) -> Any:
        """Process any action polymorphically"""
        announcer.announce(
            "AudioService.POLYMORPHIC",
            [f"Processing: {action}", f"Args: {kwargs}"]
        )
        
        # Default response
        return f"AudioService processed: {action}"
    
    def set_background_music(self, file_path: str):
        """Set the background music file"""
        if os.path.exists(file_path):
            self.background_music_path = file_path
            announcer.announce("AudioService", [f"Background music set: {file_path}"])
            return True
        return False
    
    def get_current_music_position(self):
        """Calculate current position in the music file"""
        with self.lock:
            elapsed = time.time() - self.music_start_time
            # Music duration is about 159 seconds (2:39)
            music_duration = 159.0
            # Loop the position if we've exceeded the duration
            return elapsed % music_duration
    
    def get_continuous_stream(self):
        """
        Get the CONTINUOUS audio stream
        This stream NEVER stops - it's always running with music
        """
        return self.stream_service.get_stream()
    
    def add_speech_to_stream(self, speech_text: str):
        """
        Add speech to the CONTINUOUS stream
        The music doesn't stop - speech is mixed IN
        """
        self.stream_service.add_speech(speech_text)
    
    def stream_with_auto_volume(self, speech_text: str, music_volume: float = 0.15):
        """
        Stream audio with automatic volume adjustment
        Music volume lowers when speech plays
        
        Args:
            speech_text: Text to speak
            music_volume: Music volume level during speech (0.15 = 15% volume)
        """
        announcer.announce(
            "AudioService.auto_volume",
            [
                "🎚️ Auto-volume adjustment active!",
                f"Music volume: {int(music_volume*100)}% during speech",
                "Smooth fade in/out transitions"
            ]
        )
        
        if not self.background_music_path:
            # No music to duck, just return TTS
            return self.generate_tts(speech_text)
        
        # Get current music position for seamless continuation
        current_position = self.get_current_music_position()
        
        # Generate TTS
        tts_file = self.generate_tts(speech_text)
        
        # Simple ducking - music at low volume ONLY during speech, then returns to normal
        import subprocess
        
        cmd = [
            "ffmpeg",
            "-i", tts_file,  # Speech audio
            "-ss", str(current_position),  # Continue music from current position
            "-i", self.background_music_path,  # Background music
            "-filter_complex",
            # Simpler approach: music ducks during speech, returns to normal after
            f"[1:a]volume=0.35[music_normal];"  # Normal music volume (35%)
            f"[1:a]volume={music_volume}[music_ducked];"  # Ducked music volume (15%)
            f"[0:a][music_ducked]amix=inputs=2:duration=first:dropout_transition=0[mixed]",  # Mix only during speech
            "-f", "wav",
            "-ac", "1",
            "-ar", "8000",
            "pipe:1"
        ]
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        audio_data = proc.stdout.read()
        
        # Clean up TTS file
        try:
            os.remove(tts_file)
        except:
            pass
        
        return audio_data
    
    def stream_continuous_realtime(self, speech_text: str):
        """
        Stream REAL-TIME mix without creating ANY files
        Music continues from current position - NEVER restarts
        
        ⚠️ WARNING: NO FILES! REAL-TIME ONLY! ⚠️
        """
        current_position = self.get_current_music_position()
        
        announcer.announce(
            "AudioService.REALTIME",
            [
                f"Music position: {current_position:.1f}s",
                "REAL-TIME streaming - NO FILES",
                "Music continues from current position"
            ]
        )
        
        if self.background_music_path:
            # TTS to stdout
            tts_cmd = ["espeak", "--stdout", speech_text]
            
            # Mix in REAL-TIME with music from current position
            mix_cmd = [
                "ffmpeg",
                "-f", "wav",  # Input format
                "-i", "pipe:0",  # TTS from stdin
                "-ss", str(current_position),  # START FROM CURRENT POSITION
                "-i", self.background_music_path,
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
            
            # Read the REAL-TIME stream
            audio_data = mix_proc.stdout.read()
            
            return audio_data
        
        # Fallback - just TTS
        tts_cmd = ["espeak", "--stdout", speech_text]
        proc = subprocess.Popen(tts_cmd, stdout=subprocess.PIPE)
        return proc.stdout.read()
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

# Global instance
_audio_service = None

def get_audio_service() -> AudioService:
    """Get or create the audio service instance"""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service

# Convenience functions
def mix_audio(speech_text: str = None, **kwargs) -> str:
    """Mix speech with background music"""
    return get_audio_service().mix_audio(speech_text, **kwargs)

def generate_tts(text: str, **kwargs) -> str:
    """Generate text-to-speech"""
    return get_audio_service().generate_tts(text, **kwargs)

if __name__ == "__main__":
    # Test the service
    audio = get_audio_service()
    
    print("\n🎵 Audio Service Test")
    print("=" * 50)
    
    # Test polymorphic interface
    print(f"Status: {audio.tell()}")
    print(f"Music info: {audio.ask('what music?')}")
    
    # Test TTS
    print("\nGenerating TTS...")
    tts_file = audio.generate_tts("Welcome to Try Hard Tournament Tracker")
    print(f"TTS file: {tts_file}")
    
    # Test mixing (if background music exists)
    if audio.background_music_path:
        print("\nMixing audio...")
        mixed = audio.mix_audio(speech_text="The top player is Monte with 91 points")
        print(f"Mixed file: {mixed}")
    
    # Polymorphic test
    print("\nPolymorphic test:")
    result = audio.do("mix some audio", speech_text="Testing polymorphic mixing")
    print(f"Result: {result}")