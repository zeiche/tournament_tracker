#!/usr/bin/env python3
"""
Direct transcription test - feed WAV file directly to the transcription service
"""

import sys
import os
import wave
import audioop

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from polymorphic_core.audio.transcription import get_transcription_service
    from polymorphic_core import announcer
except ImportError:
    print("❌ Polymorphic core not available")
    sys.exit(1)

def test_direct_transcription(wav_file="better_test_transcription.wav"):
    """Test transcription directly without Twilio bridge"""
    
    if not os.path.exists(wav_file):
        print(f"❌ WAV file not found: {wav_file}")
        return False
    
    print(f"🎵 Direct transcription test: {wav_file}")
    
    # 1. Load WAV file
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
        print(f"❌ Error loading WAV: {e}")
        return False
    
    # 2. Convert to mulaw (what Twilio sends)
    print("🔄 Converting PCM to mulaw (Twilio format)...")
    try:
        mulaw_data = audioop.lin2ulaw(pcm_data, sample_width)
        print(f"📞 Mulaw data: {len(mulaw_data):,} bytes")
    except Exception as e:
        print(f"❌ Error converting to mulaw: {e}")
        return False
    
    # 3. Get transcription service
    transcription_service = get_transcription_service()
    if not transcription_service:
        print("❌ No transcription service")
        return False
    
    print("✅ Found transcription service")
    
    # 4. Test with PCM data first
    print("\n🧪 Test 1: PCM Audio (direct from WAV)")
    metadata_pcm = {
        'type': 'direct_test_pcm',
        'format': 'pcm_s16le',
        'sample_rate': sample_rate,
        'channels': channels,
        'decoded': True,
        'source': 'direct_wav_file'
    }
    
    # Set up transcription result capture
    original_announce = transcription_service.announce_transcription
    results = []
    
    def capture_result(source, text):
        results.append((source, text))
        print(f"🎤 TRANSCRIPTION RESULT: '{text}' from {source}")
        original_announce(source, text)
    
    transcription_service.announce_transcription = capture_result
    
    # Send PCM data
    transcription_service.transcribe_audio(
        "direct_test_pcm",
        pcm_data,
        metadata_pcm
    )
    
    # 5. Test with mulaw data
    print("\n🧪 Test 2: Mulaw Audio (Twilio format)")
    metadata_mulaw = {
        'type': 'direct_test_mulaw',
        'format': 'mulaw',
        'sample_rate': 8000,  # Mulaw is 8kHz
        'channels': 1,
        'source': 'direct_wav_mulaw'
    }
    
    # Send mulaw data
    transcription_service.transcribe_audio(
        "direct_test_mulaw", 
        mulaw_data,
        metadata_mulaw
    )
    
    # 6. Test silence (first 8 seconds)
    print("\n🧪 Test 3: Silence Detection (first 8 seconds)")
    silence_frames = sample_rate * 8
    silence_pcm = pcm_data[:silence_frames * channels * sample_width]
    
    metadata_silence = {
        'type': 'silence_test',
        'format': 'pcm_s16le',
        'sample_rate': sample_rate,
        'channels': channels,
        'decoded': True,
        'source': 'silence_only'
    }
    
    transcription_service.transcribe_audio(
        "silence_test",
        silence_pcm,
        metadata_silence
    )
    
    # 7. Test just the speech part
    print("\n🧪 Test 4: Speech Only (after 8 seconds)")
    speech_start = silence_frames * channels * sample_width
    speech_pcm = pcm_data[speech_start:]
    
    if len(speech_pcm) > 0:
        metadata_speech = {
            'type': 'speech_only_test',
            'format': 'pcm_s16le', 
            'sample_rate': sample_rate,
            'channels': channels,
            'decoded': True,
            'source': 'speech_only'
        }
        
        transcription_service.transcribe_audio(
            "speech_only_test",
            speech_pcm,
            metadata_speech
        )
    
    print(f"\n📋 Captured {len(results)} transcription results:")
    for source, text in results:
        print(f"   {source}: '{text}'")
    
    # Restore original function
    transcription_service.announce_transcription = original_announce
    
    return len(results) > 0

def main():
    print("🎙️ Direct Transcription Test")
    print("=" * 40)
    
    success = test_direct_transcription("better_test_transcription.wav")
    
    if success:
        print("\n✅ Direct transcription test completed")
        print("🎯 Expected: 'this is a test' transcribed from speech portion")
        print("🤫 Expected: Silence portions ignored (voice activity detection)")
    else:
        print("\n❌ Direct transcription test failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())