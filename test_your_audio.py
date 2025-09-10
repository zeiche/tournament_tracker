#!/usr/bin/env python3
"""
Test the audio file you provided: test_audio_for_transcription.wav
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

def test_your_audio():
    """Test your provided audio file"""
    
    wav_file = "test_audio_for_transcription.wav"
    
    if not os.path.exists(wav_file):
        print(f"❌ File not found: {wav_file}")
        return False
    
    print(f"🎵 Testing your audio file: {wav_file}")
    
    # Load WAV and show details
    try:
        with wave.open(wav_file, 'rb') as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            frames = wav.getnframes()
            pcm_data = wav.readframes(frames)
            
        duration = frames / sample_rate
        file_size = os.path.getsize(wav_file)
        
        print(f"📊 Audio Info:")
        print(f"   Sample Rate: {sample_rate}Hz")
        print(f"   Channels: {channels}")
        print(f"   Bit Depth: {sample_width*8}bit")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Frames: {frames:,}")
        print(f"   Data Size: {len(pcm_data):,} bytes")
        print(f"   File Size: {file_size:,} bytes")
        
    except Exception as e:
        print(f"❌ Error loading: {e}")
        return False
    
    # Get transcription service
    transcription_service = get_transcription_service()
    if not transcription_service:
        print("❌ No transcription service")
        return False
    
    print("✅ Found transcription service")
    
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
        'type': 'user_provided_audio',
        'format': 'pcm_s16le',
        'sample_rate': sample_rate,
        'channels': channels,
        'decoded': True,
        'source': 'user_audio_file',
        'original_file': wav_file
    }
    
    print("📤 Sending to transcription service...")
    print("⏳ Processing audio (this may take a moment for longer files)...")
    
    # Announce audio availability for the Bonjour system
    announcer.announce(
        "AUDIO_AVAILABLE",
        [
            f"SOURCE: user_provided_{wav_file}",
            f"SIZE: {len(pcm_data)} bytes",
            f"FORMAT: wav",
            f"RATE: {sample_rate}",
            f"CHANNELS: {channels}",
            f"DURATION: {duration:.1f}s",
            "PURPOSE: Test user-provided audio"
        ]
    )
    
    transcription_service.transcribe_audio(
        "user_provided_audio",
        pcm_data,
        metadata
    )
    
    # Restore original function
    transcription_service.announce_transcription = original_announce
    
    print(f"\n📋 Transcription Results:")
    if results:
        for source, text in results:
            print(f"   🎤 '{text}'")
            
            # Also announce the result
            announcer.announce(
                "TRANSCRIPTION_COMPLETE",
                [
                    f"SOURCE: {wav_file}",
                    f"TEXT: '{text}'",
                    f"DURATION: {duration:.1f}s",
                    "STATUS: User audio transcribed successfully"
                ]
            )
    else:
        print("   ⚠️ No transcription results (may be silence or unclear audio)")
    
    return len(results) > 0

if __name__ == "__main__":
    print("🎙️ Testing Your Audio File")
    print("=" * 40)
    
    success = test_your_audio()
    
    if success:
        print("\n✅ Your audio file transcription completed successfully!")
        print("🎯 The transcription system is working with your audio")
    else:
        print("\n⚠️ No transcription detected")
        print("💡 This could mean:")
        print("   - The audio contains only silence")
        print("   - The speech is unclear or very quiet")
        print("   - The audio format needs conversion")
        print("   - Voice activity detection filtered it out")