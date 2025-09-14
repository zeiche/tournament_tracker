#!/usr/bin/env python3
"""
polymorphic_transcription.py - Transcribes ANY audio it hears about
Listens for AUDIO_AVAILABLE announcements and transcribes them
Pure Bonjour - discovers audio through announcements
"""

from polymorphic_core.local_bonjour import local_announcer
from polymorphic_core import register_capability, discover_capability
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
        local_announcer.announce(
            "PolymorphicTranscription",
            [
                "I transcribe ANY audio with voice activity detection",
                "I listen for AUDIO_AVAILABLE announcements",
                "I use Vosk (offline) with built-in silence detection",
                "I announce TRANSCRIPTION_COMPLETE only when speech detected",
                "I ignore silence automatically",
                "I am the universal offline transcriber"
            ]
        )
        
        # Register as audio handler
        self.register_for_audio()
    
    def register_for_audio(self):
        """Register to receive audio"""
        audio_requester = discover_capability('audio_request')
        if audio_requester:
            audio_requester.register_audio_handler(self.transcribe_audio)
            local_announcer.announce(
                "PolymorphicTranscription",
                ["Registered as audio handler"]
            )
    
    def transcribe_audio(self, source: str, audio_data: bytes, metadata: dict):
        """Transcribe any audio we receive"""
        local_announcer.announce(
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
        
        # Try Vosk first (offline with silence detection)
        transcription = self.transcribe_with_vosk(audio_data)
        if transcription:
            self.announce_transcription(source, transcription)
            return
        
        # No speech detected or transcription failed
        local_announcer.announce(
            "NO_SPEECH_DETECTED",
            [
                f"No speech detected in audio from {source}",
                "Either silence or transcription failed"
            ]
        )
    
    def transcribe_with_vosk(self, audio_data: bytes) -> str:
        """Transcribe with vosk (offline with built-in silence detection)"""
        try:
            import vosk
            import json
            import audioop
            import numpy as np
            
            # Convert mulaw to linear PCM if needed
            if len(audio_data) > 0:
                try:
                    # Try treating as mulaw first
                    linear_data = audioop.ulaw2lin(audio_data, 2)
                except audioop.error:
                    # Already linear, use as-is
                    linear_data = audio_data
                
                # Convert to numpy array for analysis
                audio_array = np.frombuffer(linear_data, dtype=np.int16)
                
                # Simple voice activity detection using RMS
                rms = np.sqrt(np.mean(audio_array.astype(np.float64)**2))
                silence_threshold = 10  # Very low threshold for testing
                
                # Debug logging
                local_announcer.announce("VoskDebug", [f"RMS: {rms:.1f}, Threshold: {silence_threshold}"])
                
                if rms < silence_threshold:
                    local_announcer.announce("VoskDebug", [f"Silence: RMS {rms:.1f} < {silence_threshold}"])
                    return None  # Silence detected, don't transcribe
                else:
                    local_announcer.announce("VoskDebug", [f"Speech detected: RMS {rms:.1f} >= {silence_threshold}"])
                
                # Initialize vosk model if not already done
                if not hasattr(self, '_vosk_model'):
                    model_path = "/home/ubuntu/claude/tournament_tracker/models/vosk-model-small-en-us-0.15"
                    self._vosk_model = vosk.Model(model_path)
                    self._vosk_rec = vosk.KaldiRecognizer(self._vosk_model, 16000)  # Model expects 16kHz
                
                # Proper upsampling from 8kHz to 16kHz using scipy
                try:
                    from scipy import signal
                    # Use scipy for proper resampling
                    upsampled = signal.resample(audio_array, len(audio_array) * 2)
                    vosk_data = upsampled.astype(np.int16).tobytes()
                except ImportError:
                    # Fallback to simple duplication if scipy not available
                    upsampled = np.repeat(audio_array, 2)
                    vosk_data = upsampled.astype(np.int16).tobytes()
                
                # Process audio with vosk
                if self._vosk_rec.AcceptWaveform(vosk_data):
                    result = json.loads(self._vosk_rec.Result())
                    return result.get('text', '').strip()
                else:
                    # Partial result
                    partial = json.loads(self._vosk_rec.PartialResult())
                    return partial.get('partial', '').strip()
            
        except Exception as e:
            local_announcer.announce("PolymorphicTranscription", [f"Vosk error: {e}"])
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
    
    
    def announce_transcription(self, source: str, text: str):
        """Announce completed transcription"""
        local_announcer.announce(
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
            local_announcer.announce(
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
    local_announcer.announce("PolymorphicTranscription", ["Registered as discoverable capability"])
except ImportError:
    pass