#!/usr/bin/env python3
"""
Test the simple speech file directly
"""

import sys
import os
import wave

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from polymorphic_core.audio.transcription import get_transcription_service
    from polymorphic_core import announcer
except ImportError:
    print("❌ Polymorphic core not available")
    sys.exit(1)

def test_simple_speech():
    """Test the simple speech file"""
    
    wav_file = "simple_speech_test.wav"
    
    if not os.path.exists(wav_file):
        print(f"❌ File not found: {wav_file}")
        return False
    
    print(f"🎵 Testing: {wav_file}")
    
    # Load WAV
    try:
        with wave.open(wav_file, 'rb') as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            frames = wav.getnframes()
            pcm_data = wav.readframes(frames)
            
        duration = frames / sample_rate
        print(f"📊 {sample_rate}Hz, {channels}ch, {sample_width*8}bit, {duration:.1f}s, {len(pcm_data):,} bytes")
        
    except Exception as e:
        print(f"❌ Error loading: {e}")
        return False
    
    # Get transcription service
    transcription_service = get_transcription_service()
    if not transcription_service:
        print("❌ No transcription service")
        return False
    
    # Set up result capture
    results = []
    original_announce = transcription_service.announce_transcription
    
    def capture_result(source, text):
        results.append((source, text))
        print(f"🎤 TRANSCRIPTION: '{text}' from {source}")
        original_announce(source, text)
    
    transcription_service.announce_transcription = capture_result
    
    # Test transcription
    metadata = {
        'type': 'simple_speech_test',
        'format': 'pcm_s16le',
        'sample_rate': sample_rate,
        'channels': channels,
        'decoded': True,
        'source': 'simple_speech_file',
        'expected': 'hello world test'
    }
    
    print("📤 Sending to transcription service...")
    
    transcription_service.transcribe_audio(
        "simple_speech_test",
        pcm_data,
        metadata
    )
    
    # Restore original function
    transcription_service.announce_transcription = original_announce
    
    print(f"\n📋 Results: {len(results)} transcriptions")
    for source, text in results:
        print(f"   {source}: '{text}'")
    
    return len(results) > 0

if __name__ == "__main__":
    print("🗣️ Simple Speech Test")
    print("=" * 30)
    
    success = test_simple_speech()
    
    if success:
        print("\n✅ Simple speech test completed")
    else:
        print("\n❌ Simple speech test failed")