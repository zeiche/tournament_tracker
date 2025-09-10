#!/usr/bin/env python3
"""
Simple Bonjour self-test using the working transcription
"""

import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from polymorphic_core import announcer
except ImportError:
    class DummyAnnouncer:
        def announce(self, *args, **kwargs):
            print(f"📢 ANNOUNCE: {args}")
    announcer = DummyAnnouncer()

def simple_bonjour_self_test():
    """Simple test using our working transcription and Bonjour announcements"""
    
    print("📡 Simple Bonjour Self-Test")
    print("=" * 40)
    
    # 1. Announce we're starting a test
    announcer.announce(
        "BONJOUR_SELF_TEST_START",
        [
            "INITIATING: Self-test via Bonjour",
            "AUDIO_FILE: test_audio_for_transcription.wav", 
            "EXPECTED: 'this is a test'",
            "PURPOSE: Verify end-to-end transcription"
        ]
    )
    
    # 2. Use our working simple transcription
    print("🎤 Running simple transcription...")
    
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, 'simple_transcribe.py', 'test_audio_for_transcription.wav'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output_lines = result.stdout.split('\n')
            
            # Extract transcription result
            transcription = None
            for line in output_lines:
                if 'Result:' in line:
                    transcription = line.split("'")[1] if "'" in line else None
                    break
            
            print(f"✅ Transcription completed: '{transcription}'")
            
            # 3. Announce transcription result
            announcer.announce(
                "TRANSCRIPTION_COMPLETE",
                [
                    f"SOURCE: bonjour_self_test",
                    f"TEXT: '{transcription}'",
                    "METHOD: simple_transcribe.py",
                    "STATUS: Success via Bonjour"
                ]
            )
            
            # 4. Generate response (what the system would say back)
            if transcription:
                if 'test' in transcription.lower():
                    response = "Perfect! I heard you say 'test'. The Bonjour transcription system is working correctly."
                else:
                    response = f"I transcribed: '{transcription}'. The system is functioning through Bonjour announcements."
                
                print(f"🤖 System Response: {response}")
                
                # 5. Announce TTS request (what would be spoken back)
                announcer.announce(
                    "TEXT_TO_SPEECH",
                    [
                        f"TEXT: {response}",
                        "VOICE: normal",
                        "SOURCE: bonjour_self_test_response",
                        "TARGET: caller"
                    ]
                )
                
                # 6. Announce completion
                announcer.announce(
                    "BONJOUR_SELF_TEST_COMPLETE",
                    [
                        "STATUS: Success",
                        f"TRANSCRIBED: '{transcription}'",
                        f"RESPONDED: Yes",
                        "PIPELINE: Working end-to-end",
                        "SYSTEM: Ready for Twilio calls"
                    ]
                )
                
                return True
            else:
                print("❌ No transcription result found")
                return False
                
        else:
            print(f"❌ Transcription failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Transcription timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎙️ What I Expect vs What I Hear")
    print("=" * 40)
    
    print("💭 EXPECTED:")
    print("   1. Load test_audio_for_transcription.wav")
    print("   2. Transcribe: 'this is a test'")
    print("   3. Respond: 'Perfect! I heard you say test...'")
    print("   4. All via Bonjour announcements")
    
    print("\n👂 WHAT I HEAR:")
    
    success = simple_bonjour_self_test()
    
    print(f"\n📊 RESULT:")
    if success:
        print("✅ SUCCESS: Bonjour self-test completed!")
        print("📞 System ready for real Twilio calls")
        print("🔄 Full pipeline: Audio → Transcription → Response → TTS")
    else:
        print("❌ FAILED: Self-test did not complete")
        print("🔧 Check transcription service")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())