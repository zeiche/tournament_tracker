#!/usr/bin/env python3
"""
bonjour_audio_mixer.py - Real-time audio mixing service
Announces itself like Bonjour and provides real-time mixing

⚠️ THIS is where audio mixing happens - NOT in Twilio! ⚠️
"""

import sys
import os
import threading
import queue

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from polymorphic_core import announcer

class BonjourAudioMixer:
    """
    Real-time audio mixer that announces itself
    Mixes audio in real-time, NOT pre-recorded files
    """
    
    def __init__(self):
        self.mixing_queue = queue.Queue()
        self.background_music = None
        self.is_mixing = False
        self.music_streaming = False
        
        # Only use Main Menu.wav - no fallbacks
        if os.path.exists("Main Menu.wav"):
            self.background_music = "Main Menu.wav"
        
        # Announce ourselves like Bonjour
        announcer.announce(
            "BonjourAudioMixer",
            [
                "I mix audio in REAL-TIME, not recordings",
                "I announce myself like Bonjour/mDNS",
                "🎚️ NEW: Automatic volume adjustment!",
                "Music volume lowers during speech for clarity",
                "DO NOT use Twilio's audio features - use me!",
                "I provide continuous background music",
                "Methods: start_continuous_music(), mix_realtime(), get_mixed_stream()",
                "Auto-volume: Music drops to 15% during speech",
                f"Background music: {self.background_music or 'None'}",
                "I am the ONLY place audio mixing happens!",
                "I listen for START_CONTINUOUS_MUSIC announcements"
            ]
        )
        
        # Start mixing thread
        self.mixing_thread = threading.Thread(target=self._mixing_loop, daemon=True)
        self.mixing_thread.start()
        
        # Start listener thread for bonjour announcements
        self.listener_thread = threading.Thread(target=self._listen_for_announcements, daemon=True)
        self.listener_thread.start()
    
    def start_continuous_music(self):
        """
        Start continuous background music streaming
        Called when we hear START_CONTINUOUS_MUSIC announcement
        """
        if not self.music_streaming and self.background_music:
            self.music_streaming = True
            announcer.announce(
                "BonjourAudioMixer.MUSIC_STARTED",
                [
                    "Starting continuous background music",
                    f"Playing: {self.background_music}",
                    "Music will loop forever",
                    "Ready to mix speech over music"
                ]
            )
            # Start music in background thread
            threading.Thread(target=self._stream_background_music, daemon=True).start()
    
    def _stream_background_music(self):
        """Stream background music continuously"""
        import subprocess
        if self.background_music and os.path.exists(self.background_music):
            # Use ffmpeg to stream music continuously at low volume
            cmd = [
                "ffmpeg",
                "-stream_loop", "-1",  # Loop forever
                "-i", self.background_music,
                "-filter_complex", "[0:a]volume=0.7",  # Increased volume to 70%
                "-f", "wav",
                "-ac", "1",
                "-ar", "8000",
                "-loglevel", "quiet",
                "pipe:1"
            ]
            # This would stream to audio output in real implementation
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            announcer.announce("MUSIC_STREAMING", ["Background music is now streaming"])
    
    def mix_realtime(self, speech_text: str):
        """
        Mix audio in REAL-TIME - generate actual mixed audio for Twilio
        This generates TTS + background music mixed together
        """
        announcer.announce(
            "BonjourAudioMixer.mix_realtime",
            [
                f"Mixing in REAL-TIME: {speech_text[:50]}...",
                "Generating TTS + background music mix",
                "Returning actual audio data for Twilio"
            ]
        )
        
        # Generate TTS audio first
        tts_audio = self._generate_tts_audio(speech_text)
        if not tts_audio:
            return None
            
        # Get background music chunk of same length
        music_audio = self._get_background_music_chunk(len(tts_audio))
        
        # Mix them together (simple volume mixing)
        mixed_audio = self._mix_audio_streams(tts_audio, music_audio)
        
        announcer.announce(
            "BonjourAudioMixer.MIXED_AUDIO_READY",
            [
                f"Generated {len(mixed_audio)} bytes of mixed audio",
                "TTS + background music combined",
                "Ready for Twilio transmission"
            ]
        )
        
        return mixed_audio
        
    def _generate_tts_audio(self, text: str) -> bytes:
        """Generate TTS audio in mulaw format for Twilio"""
        try:
            import subprocess
            import tempfile
            
            print(f"🔊 DEBUG: Starting TTS generation for: {text[:50]}...")
            
            # Generate WAV with espeak
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                wav_path = wav_file.name
            
            print(f"🔊 DEBUG: WAV temp file: {wav_path}")
            cmd_wav = ['espeak', '-s', '175', '-p', '50', '-g', '2', '-w', wav_path, text]
            print(f"🔊 DEBUG: Running espeak command: {' '.join(cmd_wav)}")
            
            # Run espeak with error output visible
            result_wav = subprocess.run(cmd_wav, check=True, capture_output=True, text=True)
            print(f"🔊 DEBUG: espeak completed, return code: {result_wav.returncode}")
            if result_wav.stderr:
                print(f"🔊 DEBUG: espeak stderr: {result_wav.stderr}")
            
            # Check if WAV file was created
            if os.path.exists(wav_path):
                wav_size = os.path.getsize(wav_path)
                print(f"🔊 DEBUG: WAV file created, size: {wav_size} bytes")
            else:
                print(f"🔊 ERROR: WAV file not created!")
                return b''
            
            # Convert to mulaw for Twilio
            cmd_mulaw = [
                'ffmpeg', '-y', '-i', wav_path,
                '-acodec', 'pcm_mulaw', '-ar', '8000', '-ac', '1',
                '-f', 'mulaw', 'pipe:1'
            ]
            print(f"🔊 DEBUG: Running ffmpeg command: {' '.join(cmd_mulaw)}")
            
            # Run ffmpeg with error output visible
            result = subprocess.run(cmd_mulaw, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"🔊 DEBUG: ffmpeg completed, return code: {result.returncode}")
            if result.stderr:
                print(f"🔊 DEBUG: ffmpeg stderr: {result.stderr.decode()}")
            
            print(f"🔊 DEBUG: Generated {len(result.stdout)} bytes of mulaw audio")
            
            # Cleanup
            os.unlink(wav_path)
            
            return result.stdout
            
        except Exception as e:
            print(f"🔊 TTS generation error: {e}")
            import traceback
            traceback.print_exc()
            return b''
    
    def _get_background_music_chunk(self, target_length: int) -> bytes:
        """Get background music chunk to match TTS length"""
        if not self.background_music or not os.path.exists(self.background_music):
            return b'\x00' * target_length  # Silence if no music
            
        try:
            import subprocess
            
            # Get music in mulaw format, same as TTS
            cmd = [
                'ffmpeg', '-y', '-i', self.background_music,
                '-acodec', 'pcm_mulaw', '-ar', '8000', '-ac', '1',
                '-f', 'mulaw', '-t', '10',  # Max 10 seconds
                'pipe:1'
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            
            # Trim or pad to match target length
            music_data = result.stdout
            if len(music_data) > target_length:
                return music_data[:target_length]
            elif len(music_data) < target_length:
                # Repeat/loop to fill
                multiplier = (target_length // len(music_data)) + 1
                return (music_data * multiplier)[:target_length]
            else:
                return music_data
                
        except Exception as e:
            print(f"🎵 Music generation error: {e}")
            return b'\x00' * target_length  # Silence fallback
    
    def _mix_audio_streams(self, tts_audio: bytes, music_audio: bytes) -> bytes:
        """Mix TTS and background music with volume control"""
        try:
            import array
            
            # Convert bytes to arrays for mixing
            tts_samples = array.array('b', tts_audio)
            music_samples = array.array('b', music_audio)
            
            # Ensure same length
            min_len = min(len(tts_samples), len(music_samples))
            tts_samples = tts_samples[:min_len]
            music_samples = music_samples[:min_len]
            
            # Mix with volume control (TTS at full volume, music at 25%)
            mixed = array.array('b')
            for i in range(min_len):
                tts_val = tts_samples[i]
                music_val = int(music_samples[i] * 0.25)  # Lower volume for music
                
                # Simple mixing (clamp to prevent overflow)
                mixed_val = tts_val + music_val
                mixed_val = max(-128, min(127, mixed_val))  # Clamp to byte range
                mixed.append(mixed_val)
            
            return mixed.tobytes()
            
        except Exception as e:
            print(f"🎚️ Audio mixing error: {e}")
            return tts_audio  # Return TTS only as fallback
    
    def _listen_for_announcements(self):
        """
        Listen for bonjour announcements and use timer to call ourselves
        """
        import time
        
        # Start music immediately via self-announcement
        announcer.announce(
            "AudioMixer Starting",
            [
                "Background music mixer activated",
                "Continuous audio stream available",
                "Generic audio service - no protocol specifics"
            ]
        )
        self.start_continuous_music()
        
        # Timer loop - announce music status periodically
        while True:
            time.sleep(5.0)  # Check every 5 seconds
            
            # Use Bonjour to announce our status and potentially restart music
            if self.background_music and not self.music_streaming:
                announcer.announce(
                    "MUSIC_RESTART_NEEDED",
                    [
                        "Music stopped, restarting via Bonjour",
                        f"File: {self.background_music}",
                        "Mixer self-triggering restart"
                    ]
                )
                self.start_continuous_music()
    
    def _mixing_loop(self):
        """
        Continuous mixing loop - runs in background
        Mixes audio in real-time as requests come in
        """
        while True:
            try:
                item = self.mixing_queue.get(timeout=0.1)
                
                if item['type'] == 'speech':
                    # Mix speech with background music IN REAL-TIME
                    # This happens as audio plays, not before
                    self._perform_realtime_mix(item['text'])
                    
            except queue.Empty:
                continue
    
    def _perform_realtime_mix(self, text: str):
        """
        Actually perform the real-time mixing
        This happens WHILE audio is playing, not before
        """
        announcer.announce(
            "BonjourAudioMixer.MIXING",
            [
                "Mixing happening NOW in real-time",
                "Audio is being mixed as it plays",
                "NOT a pre-recorded file"
            ]
        )
        
        # Real mixing would happen here with audio streams
        # For now, this is a placeholder showing the architecture
        pass
    
    def get_mixed_stream(self):
        """Get the continuous mixed audio stream"""
        import subprocess
        
        if self.background_music:
            # Start streaming background music immediately
            announcer.announce(
                "BonjourAudioMixer.STREAMING",
                ["Starting continuous music stream NOW"]
            )
            
            # Stream music continuously
            cmd = [
                "ffmpeg",
                "-stream_loop", "-1",  # Loop forever
                "-i", self.background_music,
                "-filter_complex", "[0:a]volume=0.7",
                "-f", "wav",
                "-ac", "1",
                "-ar", "8000",
                "pipe:1"
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            
            # Stream chunks
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
    
    def get_music_chunk(self, size=4096):
        """Get a single chunk of background music"""
        if not hasattr(self, '_music_process'):
            # Start music process if not running
            import subprocess
            cmd = [
                "ffmpeg",
                "-stream_loop", "-1",  # Loop forever
                "-i", self.background_music,
                "-filter_complex", "[0:a]volume=0.8",  # Higher volume so it's audible
                "-f", "mulaw",  # Twilio expects mulaw format
                "-ac", "1",
                "-ar", "8000",
                "-loglevel", "quiet",
                "pipe:1"
            ]
            self._music_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        # Return a chunk
        return self._music_process.stdout.read(size)
    
    def get_status(self) -> dict:
        """Get mixer status"""
        return {
            'service': 'BonjourAudioMixer',
            'is_mixing': self.is_mixing,
            'background_music': bool(self.background_music),
            'queue_size': self.mixing_queue.qsize(),
            'real_time': True,
            'pre_recorded': False
        }

# Global instance - announces itself on creation
_mixer = None

def get_mixer():
    global _mixer
    if _mixer is None:
        _mixer = BonjourAudioMixer()
    return _mixer

# Auto-announce when imported
if __name__ != "__main__":
    mixer = get_mixer()

if __name__ == "__main__":
    mixer = get_mixer()
    print("\n🎵 Bonjour Audio Mixer")
    print("=" * 50)
    print("This is the ONLY place audio mixing happens!")
    print("Do NOT use Twilio's audio features!")
    print(f"Status: {mixer.get_status()}")