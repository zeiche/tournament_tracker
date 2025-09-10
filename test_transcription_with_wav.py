#!/usr/bin/env python3
"""
Test transcription services with the created WAV file
Sends audio to polymorphic transcription service through Bonjour
"""

import sys
import os
import wave
import time
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from polymorphic_core import announcer, discover_capability
    from polymorphic_core.audio.transcription import get_transcription_service
except ImportError:
    print("❌ Polymorphic core not available")
    sys.exit(1)

def test_transcription_with_wav(wav_file="test_transcription.wav"):
    """Test transcription service with the WAV file"""
    
    if not os.path.exists(wav_file):
        print(f"❌ WAV file not found: {wav_file}")
        return False
    
    print(f"🎵 Testing transcription with: {wav_file}")
    
    # 1. Load the WAV file
    try:
        with wave.open(wav_file, 'rb') as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            frames = wav.getnframes()
            audio_data = wav.readframes(frames)
            
        duration = frames / sample_rate
        print(f"📊 Audio info: {sample_rate}Hz, {channels}ch, {sample_width*8}bit, {duration:.1f}s")
        print(f"💾 Data size: {len(audio_data):,} bytes")
        
    except Exception as e:
        print(f"❌ Error loading WAV file: {e}")
        return False
    
    # 2. Get the transcription service
    transcription_service = get_transcription_service()
    if not transcription_service:
        print("❌ No transcription service available")
        return False
    
    print("✅ Found polymorphic transcription service")
    
    # 3. Prepare metadata
    metadata = {
        'type': 'test_audio',
        'format': 'wav',
        'sample_rate': sample_rate,
        'channels': channels,
        'sample_width': sample_width,
        'source_file': wav_file,
        'expected_text': 'this is a test',
        'test_silence': True  # This file has silence that should be ignored
    }
    
    print("📤 Sending audio to transcription service...")
    
    # 4. Announce audio availability
    announcer.announce(
        "AUDIO_AVAILABLE",
        [
            f"SOURCE: test_wav_{wav_file}",
            f"SIZE: {len(audio_data)} bytes",
            f"FORMAT: wav",
            f"RATE: {sample_rate}",
            f"CHANNELS: {channels}",
            "PURPOSE: Test transcription with silence detection",
            "EXPECTED: 'this is a test' (after 8s silence)"
        ]
    )
    
    # 5. Send to transcription service
    try:
        transcription_service.transcribe_audio(
            f"test_wav_{wav_file}",
            audio_data,
            metadata
        )
        
        print("✅ Audio sent to transcription service")
        print("⏳ Waiting for transcription result...")
        
        # Wait a bit for processing
        time.sleep(3)
        
        print("✅ Transcription request completed")
        print("📢 Check the system output for TRANSCRIPTION_COMPLETE announcements")
        
    except Exception as e:
        print(f"❌ Error sending to transcription service: {e}")
        return False
    
    return True

def test_silence_detection():
    """Test just the first 8 seconds (silence) to verify silence detection works"""
    wav_file = "test_transcription.wav"
    
    if not os.path.exists(wav_file):
        print(f"❌ WAV file not found: {wav_file}")
        return False
    
    print("🤫 Testing silence detection with first 8 seconds...")
    
    # Load WAV and extract just first 8 seconds
    try:
        with wave.open(wav_file, 'rb') as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            
            # Read 8 seconds worth of frames
            silence_frames = sample_rate * 8
            silence_data = wav.readframes(silence_frames)
            
        print(f"📊 Silence test: {sample_rate}Hz, {len(silence_data):,} bytes, 8.0s")
        
    except Exception as e:
        print(f"❌ Error loading silence: {e}")
        return False
    
    # Send silence to transcription
    transcription_service = get_transcription_service()
    if not transcription_service:
        print("❌ No transcription service available")
        return False
    
    metadata = {
        'type': 'silence_test',
        'format': 'wav',
        'sample_rate': sample_rate,
        'channels': channels,
        'sample_width': sample_width,
        'expected_result': 'no transcription (silence)'
    }
    
    print("📤 Sending silence to test voice activity detection...")
    
    try:
        transcription_service.transcribe_audio(
            "silence_test",
            silence_data,
            metadata
        )
        
        print("✅ Silence sent to transcription service")
        print("🤞 Should detect no speech and not transcribe")
        
        time.sleep(2)
        
    except Exception as e:
        print(f"❌ Error testing silence: {e}")
        return False
    
    return True

def main():
    print("🧪 Testing Transcription Services")
    print("=" * 40)
    
    # Test 1: Full audio (silence + speech)
    print("\n🎵 Test 1: Full audio (8s silence + 'this is a test')")
    success1 = test_transcription_with_wav("test_transcription.wav")
    
    # Test 2: Just silence
    print("\n🤫 Test 2: Silence detection (first 8 seconds only)")  
    success2 = test_silence_detection()
    
    print("\n📋 Test Summary:")
    print(f"   Full audio test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"   Silence test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All transcription tests completed successfully!")
        print("💡 Expected results:")
        print("   - Full audio: Should transcribe 'this is a test' after silence")
        print("   - Silence test: Should not transcribe anything (voice activity detection)")
        print("📢 Check system output for TRANSCRIPTION_COMPLETE announcements")
    else:
        print("\n❌ Some tests failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())