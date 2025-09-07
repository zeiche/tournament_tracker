#!/usr/bin/env python3
"""
polymorphic_transcription.py - Transcribes ANY audio it hears about
Listens for AUDIO_AVAILABLE announcements and transcribes them
Pure Bonjour - discovers audio through announcements
"""

from capability_announcer import announcer
from capability_discovery import register_capability, discover_capability
import subprocess
import tempfile
import os

class PolymorphicTranscription:
    """Service that transcribes any audio it hears about"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce what we do
        announcer.announce(
            "PolymorphicTranscription",
            [
                "I transcribe ANY audio",
                "I listen for AUDIO_AVAILABLE announcements",
                "I use Whisper, Google Speech, or simulation",
                "I announce TRANSCRIPTION_COMPLETE when done",
                "I don't care where audio comes from",
                "I am the universal transcriber"
            ]
        )
        
        # Register as audio handler
        self.register_for_audio()
    
    def register_for_audio(self):
        """Register to receive audio"""
        audio_requester = discover_capability('audio_request')
        if audio_requester:
            audio_requester.register_audio_handler(self.transcribe_audio)
            announcer.announce(
                "PolymorphicTranscription",
                ["Registered as audio handler"]
            )
    
    def transcribe_audio(self, source: str, audio_data: bytes, metadata: dict):
        """Transcribe any audio we receive"""
        announcer.announce(
            "TRANSCRIPTION_START",
            [
                f"Transcribing audio from: {source}",
                f"Size: {len(audio_data)} bytes",
                f"Type: {metadata.get('type', 'unknown')}",
                f"Format: {metadata.get('format', 'unknown')}"
            ]
        )
        
        # Check if it's already text (simulated)
        if metadata.get('type') == 'simulated' or metadata.get('text'):
            text = metadata.get('text') or audio_data.decode('utf-8', errors='ignore')
            self.announce_transcription(source, text)
            return
        
        # For PCM audio from WaveSink, save as WAV first
        if metadata.get('format') == 'pcm_s16le' or metadata.get('decoded'):
            audio_data = self.pcm_to_wav(audio_data, metadata)
        
        # Try Whisper first if available (most accurate)
        transcription = self.transcribe_with_whisper(audio_data)
        if transcription:
            self.announce_transcription(source, transcription)
            return
        
        # Try SpeechRecognition as fallback
        transcription = self.transcribe_with_speech_recognition(audio_data)
        if transcription:
            self.announce_transcription(source, transcription)
            return
        
        # Try Google Speech
        transcription = self.transcribe_with_google(audio_data)
        if transcription:
            self.announce_transcription(source, transcription)
            return
        
        # Fallback
        announcer.announce(
            "TRANSCRIPTION_FAILED",
            [
                f"Could not transcribe audio from {source}",
                "Install Whisper: pip install openai-whisper"
            ]
        )
    
    def transcribe_with_speech_recognition(self, audio_data: bytes) -> str:
        """Try to transcribe with SpeechRecognition"""
        try:
            import speech_recognition as sr
            import io
            
            recognizer = sr.Recognizer()
            
            # Create audio file in memory
            audio_file = io.BytesIO(audio_data)
            
            # Try to read as audio
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
                
            # Try Google Speech Recognition
            try:
                text = recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                announcer.announce("PolymorphicTranscription", [f"Google Speech error: {e}"])
                return None
                
        except Exception as e:
            announcer.announce("PolymorphicTranscription", [f"SpeechRecognition error: {e}"])
            return None
    
    def pcm_to_wav(self, pcm_data: bytes, metadata: dict) -> bytes:
        """Convert PCM audio to WAV format"""
        import wave
        import io
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        
        # Get audio parameters from metadata
        channels = metadata.get('channels', 2)
        sample_rate = metadata.get('sample_rate', 48000)
        sample_width = 2  # 16-bit audio
        
        # Write WAV file
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        # Return WAV data
        wav_buffer.seek(0)
        return wav_buffer.getvalue()
    
    def transcribe_with_whisper(self, audio_data: bytes) -> str:
        """Try to transcribe with Whisper"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            result = subprocess.run(
                ['whisper', temp_path, '--model', 'base', '--language', 'en', '--output_format', 'txt'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                with open(temp_path + '.txt', 'r') as f:
                    transcription = f.read().strip()
                
                # Cleanup
                os.remove(temp_path)
                if os.path.exists(temp_path + '.txt'):
                    os.remove(temp_path + '.txt')
                
                return transcription
        except:
            pass
        return None
    
    def transcribe_with_google(self, audio_data: bytes) -> str:
        """Try to transcribe with Google Speech"""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            with sr.AudioFile(temp_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
            
            os.remove(temp_path)
            return text
        except:
            pass
        return None
    
    def announce_transcription(self, source: str, text: str):
        """Announce completed transcription"""
        announcer.announce(
            "TRANSCRIPTION_COMPLETE",
            [
                f"SOURCE: {source}",
                f"TEXT: '{text}'",
                "READY: For Claude processing",
                "ANYONE: Can use this transcription"
            ]
        )
        
        # Also send to Claude if available
        claude = discover_capability('claude')
        if claude:
            response = claude.process(text)
            announcer.announce(
                "CLAUDE_RESPONSE",
                [
                    f"QUESTION: '{text}'",
                    f"RESPONSE: '{response}'",
                    "READY: For voice output"
                ]
            )
            
            # Send response to voice
            voice = discover_capability('voice')
            if voice:
                # Get guild ID from somewhere (would need proper context)
                voice.speak(0, response)

# Global instance
_transcription_service = PolymorphicTranscription()

def get_transcription_service():
    """Get the global transcription service"""
    return _transcription_service

# Register with capability discovery
try:
    register_capability("transcription", get_transcription_service)
    announcer.announce("PolymorphicTranscription", ["Registered as discoverable capability"])
except ImportError:
    pass