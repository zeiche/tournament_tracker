#!/usr/bin/env python3
"""
test_ducking.py - Test audio ducking functionality
"""

import os
import sys
from audio_service import get_audio_service
from capability_announcer import announcer

def test_ducking():
    """Test the audio ducking feature"""
    
    print("\n🎚️ Testing Audio Ducking")
    print("=" * 50)
    
    # Get audio service
    audio = get_audio_service()
    
    # Test different ducking levels
    test_cases = [
        ("Testing with heavy ducking", 0.10),  # 10% volume
        ("Testing with normal ducking", 0.15),  # 15% volume (default)
        ("Testing with light ducking", 0.25),  # 25% volume
        ("Testing with minimal ducking", 0.35),  # 35% volume
    ]
    
    for text, duck_level in test_cases:
        print(f"\n📢 {text} (duck to {int(duck_level*100)}%)")
        
        # Test with ducking
        print("  With ducking:")
        audio_data = audio.stream_with_ducking(text, duck_level=duck_level)
        if audio_data:
            print(f"  ✅ Generated {len(audio_data)} bytes")
        else:
            print("  ❌ No audio generated")
        
        # Save sample for listening
        sample_file = f"ducking_test_{int(duck_level*100)}.wav"
        if audio_data:
            with open(sample_file, 'wb') as f:
                f.write(audio_data)
            print(f"  💾 Saved to {sample_file}")
    
    # Test without ducking for comparison
    print("\n📢 Testing WITHOUT ducking (constant 35% music)")
    audio_data = audio.mix_audio(
        "This is without ducking - music stays constant",
        ducking=False
    )
    if audio_data and os.path.exists(audio_data):
        print(f"  ✅ Generated file: {audio_data}")
        # Copy to test directory
        import shutil
        shutil.copy(audio_data, "no_ducking_test.wav")
        print("  💾 Saved to no_ducking_test.wav")
    
    print("\n✨ Ducking test complete!")
    print("Listen to the generated files to hear the difference")
    print("The music should dip when speech plays, then return to normal")

if __name__ == "__main__":
    test_ducking()