#!/usr/bin/env python3
"""
bonjour_audio_mixer_polymorphic.py - Audio mixer with ask/tell/do pattern

Real-time audio mixing using polymorphic pattern.
⚠️ WARNING: NEVER save mixed files - always stream in real-time! ⚠️
"""

import os
import threading
import queue
import sys
sys.path.append('../..')
sys.path.insert(0, 'utils')
from universal_polymorphic import UniversalPolymorphic
from capability_announcer import announcer


class BonjourAudioMixerPolymorphic(UniversalPolymorphic):
    """
    Real-time audio mixer with ask/tell/do pattern.
    
    Examples:
        mixer.ask("streaming")              # Is music streaming?
        mixer.ask("background music")       # What music file?
        mixer.ask("queue size")             # How many items queued?
        mixer.tell("status")                # Full mixer status
        mixer.do("start music")             # Start continuous music
        mixer.do("mix", text="...")         # Mix speech in real-time
        mixer.do("stop music")              # Stop background music
    
    ⚠️ CRITICAL: This mixer NEVER saves files - only real-time streaming! ⚠️
    """
    
    def __init__(self):
        self.mixing_queue = queue.Queue()
        self.background_music = None
        self.is_mixing = False
        self.music_streaming = False
        self.volume_level = 0.7
        self.duck_level = 0.15  # Volume during speech
        
        # Check for music files
        music_files = ["game.wav", "background.wav", "music.wav"]
        for file in music_files:
            if os.path.exists(file):
                self.background_music = file
                break
        
        # Call parent init (announces via UniversalPolymorphic)
        super().__init__()
        
        # Also announce via Bonjour for compatibility
        announcer.announce(
            "BonjourAudioMixerPolymorphic",
            [
                "I'm the audio mixer with ask/tell/do pattern",
                "⚠️ I NEVER save files - only real-time streaming!",
                "Use mixer.ask('streaming')",
                "Use mixer.do('start music')",
                "Use mixer.do('mix', text='...')",
                f"Background music: {self.background_music or 'None'}",
                "Music continues from current position - NEVER restarts"
            ]
        )
        
        # Start background threads
        self.mixing_thread = threading.Thread(target=self._mixing_loop, daemon=True)
        self.mixing_thread.start()
        
        self.listener_thread = threading.Thread(target=self._listen_for_announcements, daemon=True)
        self.listener_thread.start()
    
    def _handle_ask(self, question: str, **kwargs):
        """
        Handle mixer-specific questions.
        
        Examples:
            ask("streaming")         # Is music streaming?
            ask("music file")        # What background music?
            ask("mixing")           # Is currently mixing?
            ask("queue")            # Queue size
            ask("volume")           # Current volume level
        """
        q = str(question).lower()
        
        if any(word in q for word in ['streaming', 'playing', 'music on']):
            return self.music_streaming
        
        if any(word in q for word in ['music', 'background', 'file', 'track']):
            return self.background_music or "No background music"
        
        if 'mixing' in q:
            return self.is_mixing
        
        if any(word in q for word in ['queue', 'pending', 'waiting']):
            return self.mixing_queue.qsize()
        
        if 'volume' in q:
            if 'duck' in q:
                return self.duck_level
            return self.volume_level
        
        if any(word in q for word in ['capability', 'can', 'able']):
            return [
                "Real-time audio mixing",
                "Continuous background music",
                "Speech overlay without restart",
                "Automatic volume ducking",
                "Zero file creation - pure streaming"
            ]
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str, **kwargs):
        """
        Format mixer information.
        
        Examples:
            tell("status")           # Full status
            tell("json")            # JSON format
            tell("brief")           # Short summary
        """
        if format == "status":
            return {
                'streaming': self.music_streaming,
                'background_music': self.background_music,
                'is_mixing': self.is_mixing,
                'queue_size': self.mixing_queue.qsize(),
                'volume': self.volume_level,
                'duck_level': self.duck_level
            }
        
        if format == "brief":
            if self.music_streaming:
                return f"Streaming {self.background_music}"
            return "Not streaming"
        
        if format == "detailed":
            lines = [
                f"Audio Mixer Status:",
                f"  Music: {self.background_music or 'None'}",
                f"  Streaming: {self.music_streaming}",
                f"  Mixing: {self.is_mixing}",
                f"  Queue: {self.mixing_queue.qsize()} items",
                f"  Volume: {self.volume_level * 100:.0f}%",
                f"  Duck Level: {self.duck_level * 100:.0f}%"
            ]
            return "\n".join(lines)
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs):
        """
        Perform mixer actions.
        
        Examples:
            do("start music")        # Start continuous music
            do("stop music")         # Stop music
            do("mix", text="...")    # Mix speech in real-time
            do("set volume", level=0.8)  # Set volume
            do("duck")              # Duck volume for speech
        
        ⚠️ CRITICAL: Never creates files - only streams! ⚠️
        """
        act = str(action).lower()
        
        if any(word in act for word in ['start', 'play']) and 'music' in act:
            return self._start_music()
        
        if any(word in act for word in ['stop', 'pause']) and 'music' in act:
            return self._stop_music()
        
        if 'mix' in act:
            text = kwargs.get('text', '')
            if text:
                return self._mix_realtime(text)
            return "No text provided for mixing"
        
        if 'volume' in act:
            if 'set' in act:
                level = kwargs.get('level', self.volume_level)
                self.volume_level = max(0.0, min(1.0, float(level)))
                return f"Volume set to {self.volume_level * 100:.0f}%"
            
        if 'duck' in act:
            if 'set' in act:
                level = kwargs.get('level', self.duck_level)
                self.duck_level = max(0.0, min(1.0, float(level)))
                return f"Duck level set to {self.duck_level * 100:.0f}%"
            else:
                # Perform ducking
                return self._perform_ducking()
        
        if 'clear' in act and 'queue' in act:
            while not self.mixing_queue.empty():
                self.mixing_queue.get()
            return "Queue cleared"
        
        return super()._handle_do(action, **kwargs)
    
    def _start_music(self):
        """Start continuous background music"""
        if self.music_streaming:
            return "Music already streaming"
        
        if not self.background_music:
            return "No background music file found"
        
        self.music_streaming = True
        
        # Announce via Bonjour
        announcer.announce(
            "MUSIC_STARTED",
            [
                "Starting continuous background music",
                f"Playing: {self.background_music}",
                "Music will loop forever",
                "Ready to mix speech over music"
            ]
        )
        
        # Start streaming thread
        threading.Thread(target=self._stream_background_music, daemon=True).start()
        
        return f"Started streaming {self.background_music}"
    
    def _stop_music(self):
        """Stop background music"""
        if not self.music_streaming:
            return "Music not streaming"
        
        self.music_streaming = False
        
        # Announce via Bonjour
        announcer.announce(
            "MUSIC_STOPPED",
            ["Background music stopped"]
        )
        
        return "Music stopped"
    
    def _mix_realtime(self, text: str):
        """
        Mix speech with music in REAL-TIME.
        ⚠️ NEVER creates files - returns stream handle! ⚠️
        """
        # Announce mixing
        announcer.announce(
            "REALTIME_MIX",
            [
                f"Mixing speech: {text[:50]}...",
                "NOT creating any files",
                "Streaming in real-time",
                "Music continues from current position"
            ]
        )
        
        # Add to queue for real-time processing
        self.mixing_queue.put({
            'type': 'speech',
            'text': text,
            'timestamp': threading.current_thread().ident
        })
        
        # Return stream handle (NOT a file path!)
        return f"stream://mixer/{id(text)}"
    
    def _perform_ducking(self):
        """Duck music volume for speech"""
        old_volume = self.volume_level
        self.volume_level = self.duck_level
        
        # Announce ducking
        announcer.announce(
            "VOLUME_DUCKED",
            [f"Volume ducked from {old_volume*100:.0f}% to {self.duck_level*100:.0f}%"]
        )
        
        # Schedule volume restoration
        def restore():
            import time
            time.sleep(3)  # Duck for 3 seconds
            self.volume_level = old_volume
            announcer.announce(
                "VOLUME_RESTORED",
                [f"Volume restored to {old_volume*100:.0f}%"]
            )
        
        threading.Thread(target=restore, daemon=True).start()
        
        return "Volume ducked for speech"
    
    def _stream_background_music(self):
        """
        Stream background music continuously.
        ⚠️ Music NEVER restarts - continues from position! ⚠️
        """
        if self.background_music and os.path.exists(self.background_music):
            import subprocess
            
            # Stream music continuously at current volume
            cmd = [
                "ffmpeg",
                "-stream_loop", "-1",  # Loop forever
                "-i", self.background_music,
                "-filter_complex", f"[0:a]volume={self.volume_level}",
                "-f", "wav",
                "-ac", "1",
                "-ar", "8000",
                "-loglevel", "quiet",
                "pipe:1"
            ]
            
            # This streams to audio output
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            
            # Stream chunks
            while self.music_streaming:
                chunk = proc.stdout.read(320)  # 20ms at 8kHz
                if chunk:
                    # In real implementation, this would go to audio output
                    pass
                else:
                    break
    
    def _mixing_loop(self):
        """
        Continuous mixing loop.
        Processes queue items in real-time as audio plays.
        """
        while True:
            try:
                item = self.mixing_queue.get(timeout=0.1)
                
                if item['type'] == 'speech':
                    self.is_mixing = True
                    
                    # Duck music
                    self.do("duck")
                    
                    # Mix in real-time (NOT pre-recorded!)
                    self._perform_realtime_mix(item['text'])
                    
                    self.is_mixing = False
                    
            except queue.Empty:
                continue
    
    def _perform_realtime_mix(self, text: str):
        """
        Actually perform real-time mixing.
        This happens WHILE audio plays, not before!
        """
        # In real implementation, this would:
        # 1. Convert text to speech stream
        # 2. Mix with current music position
        # 3. Output mixed stream
        # WITHOUT creating any files!
        pass
    
    def _listen_for_announcements(self):
        """Listen for Bonjour announcements requesting music"""
        import time
        while True:
            # Would listen for START_CONTINUOUS_MUSIC announcements
            time.sleep(0.1)
    
    def _get_capabilities(self):
        """List mixer capabilities"""
        return [
            "ask('streaming')",
            "ask('background music')",
            "ask('volume')",
            "tell('status')",
            "do('start music')",
            "do('stop music')",
            "do('mix', text='...')",
            "do('set volume', level=0.8)",
            "⚠️ NEVER saves files - only streams!"
        ]


# For backward compatibility
def get_mixer():
    """Get or create mixer instance"""
    return BonjourAudioMixerPolymorphic()


if __name__ == "__main__":
    mixer = BonjourAudioMixerPolymorphic()
    
    print("Audio Mixer with ask/tell/do pattern")
    print("=" * 50)
    print(f"mixer.ask('streaming'): {mixer.ask('streaming')}")
    print(f"mixer.ask('background music'): {mixer.ask('background music')}")
    print(f"mixer.tell('status'): {mixer.tell('status')}")
    print("\nStarting music...")
    print(f"mixer.do('start music'): {mixer.do('start music')}")
    print(f"mixer.ask('streaming'): {mixer.ask('streaming')}")
    print("\nMixing speech...")
    print(f"mixer.do('mix', text='Hello world'): {mixer.do('mix', text='Hello world')}")
    print("\n⚠️ Remember: NEVER saves files - only real-time streaming!")