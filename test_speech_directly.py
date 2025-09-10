#!/usr/bin/env python3
"""
Test speech recognition directly by triggering transcription service
"""
import sys
import os
import asyncio
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.audio.transcription import get_transcription_service
from polymorphic_core import announcer
import numpy as np

def test_speech_transcription():
    """Test transcription with fake speech that says 'top 8 players'"""
    print("🎤 Testing speech transcription directly...")
    
    # Get transcription service
    service = get_transcription_service()
    
    # Generate audio that exceeds silence threshold
    sample_rate = 8000
    duration = 2.0  # 2 seconds
    samples = int(sample_rate * duration)
    
    # Generate speech-like patterns with higher amplitude
    t = np.linspace(0, duration, samples)
    speech_signal = (
        np.sin(2 * np.pi * 200 * t) * 3000 +    # Low frequency
        np.sin(2 * np.pi * 800 * t) * 2000 +    # Mid frequency  
        np.sin(2 * np.pi * 1600 * t) * 1000 +   # High frequency
        np.random.normal(0, 500, samples)        # Speech noise
    )
    
    # Ensure it's loud enough to pass silence detection
    speech_signal = np.clip(speech_signal, -15000, 15000).astype(np.int16)
    audio_bytes = speech_signal.tobytes()
    
    print(f"📊 Generated {len(audio_bytes)} bytes of 'speech' audio")
    
    # Calculate RMS to verify it passes silence threshold  
    rms = np.sqrt(np.mean(speech_signal.astype(np.float64)**2))
    print(f"📈 RMS level: {rms:.1f} (threshold: 500)")
    
    # Call transcription directly with metadata
    print("🔄 Calling transcription service...")
    service.transcribe_audio("test_source", audio_bytes, {
        'type': 'audio',
        'format': 'pcm_s16le',
        'channels': 1,
        'sample_rate': 8000
    })
    
    print("✅ Transcription call complete!")
    print("📡 Check for TRANSCRIPTION_COMPLETE or NO_SPEECH_DETECTED announcements")

if __name__ == "__main__":
    test_speech_transcription()