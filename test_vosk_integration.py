#!/usr/bin/env python3
"""
Test vosk integration with the transcription service
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.audio.transcription import get_transcription_service
from polymorphic_core import announcer
import time

def test_vosk_transcription():
    """Test the vosk transcription with simulated audio"""
    print("🧪 Testing vosk integration...")
    
    # Get the transcription service
    service = get_transcription_service()
    
    # Test with empty audio (should detect silence)
    print("\n1️⃣ Testing silence detection...")
    silence_audio = b'\x00' * 3200  # 200ms of silence
    result = service.transcribe_with_vosk(silence_audio)
    print(f"Silence result: {result} (should be None)")
    
    # Test with some noise (simulated speech level audio)
    print("\n2️⃣ Testing with audio data...")
    import numpy as np
    
    # Generate some random audio data that would pass the RMS threshold
    sample_rate = 8000
    duration = 2.0  # 2 seconds
    samples = int(sample_rate * duration)
    
    # Generate noise that exceeds silence threshold
    audio_data = np.random.randint(-2000, 2000, samples, dtype=np.int16)
    audio_bytes = audio_data.tobytes()
    
    # Try transcription
    result = service.transcribe_with_vosk(audio_bytes)
    print(f"Audio result: '{result}' (should attempt transcription)")
    
    print("\n✅ Vosk integration test complete!")
    print("📡 Check Bonjour announcements for transcription events")

if __name__ == "__main__":
    test_vosk_transcription()