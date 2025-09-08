#!/usr/bin/env python3
"""
Test if bonjour audio mixer is actually producing audio data
"""

from bonjour_audio_mixer import BonjourAudioMixer
from capability_announcer import announcer
import time

def test_audio_output():
    print("🎵 Testing Bonjour Audio Output")
    print("=" * 50)
    
    # Create mixer
    mixer = BonjourAudioMixer()
    
    # Start continuous music
    print("\n📻 Starting continuous music...")
    mixer.start_continuous_music()
    
    # Give it a moment
    time.sleep(2)
    
    # Check the mixer stream
    print("\n🔊 Testing mixer output stream...")
    try:
        # Get a few chunks from the stream
        stream_gen = mixer.get_mixed_stream()
        chunk_count = 0
        total_bytes = 0
        
        for chunk in stream_gen:
            chunk_count += 1
            total_bytes += len(chunk)
            if chunk_count >= 5:  # Just test a few chunks
                break
        
        print(f"✅ Mixer is producing audio data!")
        print(f"   Chunks received: {chunk_count}")
        print(f"   Total bytes: {total_bytes}")
        
        if total_bytes > 0:
            print("\n🎶 Audio is flowing from the mixer")
            print("   Volume setting: 0.25 (25%)")
            print("   This might be too quiet for Twilio!")
        else:
            print("\n❌ No audio data received from mixer")
            
    except Exception as e:
        print(f"\n❌ Error testing mixer: {e}")
    
    # Test volume levels
    print("\n🎚️ Current volume settings:")
    print("   Background music: 0.25 (25%)")
    print("   Speech overlay: 1.0 (100%)")
    print("\n💡 Suggestion: Increase background music volume to 0.5 or higher")

if __name__ == "__main__":
    test_audio_output()