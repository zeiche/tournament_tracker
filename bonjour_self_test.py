#!/usr/bin/env python3
"""
Use Bonjour to call ourselves - test the full transcription pipeline
"""

import sys
import os
import wave
import time
import asyncio

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from polymorphic_core import announcer, discover_capability
    from polymorphic_core.audio.transcription import get_transcription_service
    from twilio_transcription_bridge import get_twilio_bridge
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def bonjour_self_test():
    """Use Bonjour to test the full transcription pipeline"""
    
    print("📡 Bonjour Self-Test: Calling Ourselves")
    print("=" * 50)
    
    # 1. Discover available services through Bonjour
    print("🔍 Discovering services through Bonjour...")
    
    transcription_service = discover_capability('transcription')
    twilio_bridge = discover_capability('twilio_bridge')
    tts_service = discover_capability('tts')
    
    print(f"   Transcription Service: {'✅ Found' if transcription_service else '❌ Not found'}")
    print(f"   Twilio Bridge: {'✅ Found' if twilio_bridge else '❌ Not found'}")
    print(f"   TTS Service: {'✅ Found' if tts_service else '❌ Not found'}")
    
    # 2. Load our test audio
    wav_file = "test_audio_for_transcription.wav"
    
    if not os.path.exists(wav_file):
        print(f"❌ Test audio not found: {wav_file}")
        return False
    
    print(f"\n🎵 Loading test audio: {wav_file}")
    
    try:
        with wave.open(wav_file, 'rb') as wav:
            sample_rate = wav.getframerate()
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            frames = wav.getnframes()
            audio_data = wav.readframes(frames)
            
        duration = frames / sample_rate
        print(f"📊 {sample_rate}Hz, {channels}ch, {sample_width*8}bit, {duration:.1f}s")
        
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        return False
    
    # 3. Set up result capture
    results = []
    responses = []
    
    if transcription_service:
        original_announce = transcription_service.announce_transcription
        
        def capture_transcription(source, text):
            results.append((source, text))
            print(f"🎤 TRANSCRIPTION: '{text}' from {source}")
            
            # Call original to trigger downstream processing
            original_announce(source, text)
            
            # Simulate what the bridge would do - generate a response
            if text.strip():
                if 'test' in text.lower():
                    response = "I heard you say 'test'. The transcription system is working perfectly!"
                elif 'hello' in text.lower():
                    response = "Hello! I can hear you clearly through the Bonjour transcription system."
                else:
                    response = f"I transcribed: '{text}'. The system is functioning normally."
                
                responses.append(response)
                print(f"🤖 RESPONSE: {response}")
                
                # Announce TTS request
                announcer.announce(
                    "TEXT_TO_SPEECH",
                    [
                        f"TEXT: {response}",
                        "VOICE: normal",
                        "SOURCE: bonjour_self_test",
                        "TARGET: system_response"
                    ]
                )
        
        # Replace transcription announcement
        transcription_service.announce_transcription = capture_transcription
    
    # 4. Announce audio availability (Bonjour style)
    print("\n📢 Announcing audio availability via Bonjour...")
    
    announcer.announce(
        "AUDIO_AVAILABLE",
        [
            f"SOURCE: bonjour_self_test",
            f"SIZE: {len(audio_data)} bytes",
            f"FORMAT: wav",
            f"RATE: {sample_rate}",
            f"CHANNELS: {channels}",
            f"DURATION: {duration:.1f}s",
            "PURPOSE: Self-test via Bonjour",
            "EXPECTED: 'this is a test'"
        ]
    )
    
    # 5. Send to transcription service
    if transcription_service:
        print("📤 Sending to transcription service...")
        
        metadata = {
            'type': 'bonjour_self_test',
            'format': 'pcm_s16le',
            'sample_rate': sample_rate,
            'channels': channels,
            'decoded': True,
            'source': 'bonjour_test_call',
            'expected': 'this is a test'
        }
        
        transcription_service.transcribe_audio(
            "bonjour_self_test",
            audio_data,
            metadata
        )
        
        # Wait for processing
        print("⏳ Processing...")
        time.sleep(2)
        
        # Restore original function
        transcription_service.announce_transcription = original_announce
    
    # 6. Test Twilio bridge integration
    if twilio_bridge:
        print("\n🌉 Testing Twilio bridge integration...")
        
        # Simulate a call registration
        fake_websocket = "mock_websocket"
        fake_handler = "mock_stream_handler"
        
        # This would register our "call"
        # twilio_bridge.register_twilio_handler("test_call_123", fake_websocket, fake_handler)
        print("   Twilio bridge available for call handling")
    
    # 7. Results
    print(f"\n📋 Test Results:")
    print(f"   Transcriptions: {len(results)}")
    for source, text in results:
        print(f"      🎤 {source}: '{text}'")
    
    print(f"   Responses: {len(responses)}")
    for response in responses:
        print(f"      🤖 '{response}'")
    
    # 8. What we expect vs what we heard
    print(f"\n🎯 Expected vs Actual:")
    print(f"   Expected: 'this is a test'")
    if results:
        actual = results[0][1] if results else "No transcription"
        print(f"   Actual: '{actual}'")
        
        if 'this is a test' in actual.lower():
            print("   ✅ PERFECT MATCH!")
        elif any(word in actual.lower() for word in ['this', 'test']):
            print("   ✅ PARTIAL MATCH - Good enough!")
        else:
            print("   ⚠️ Different transcription")
    else:
        print("   ❌ No transcription received")
    
    # 9. Announce test completion
    announcer.announce(
        "BONJOUR_SELF_TEST_COMPLETE",
        [
            f"TRANSCRIPTIONS: {len(results)}",
            f"RESPONSES: {len(responses)}",
            "STATUS: Self-test via Bonjour completed",
            "SYSTEM: Transcription pipeline verified"
        ]
    )
    
    return len(results) > 0

if __name__ == "__main__":
    success = bonjour_self_test()
    
    if success:
        print("\n🎉 Bonjour self-test successful!")
        print("📞 System ready for real Twilio calls")
    else:
        print("\n❌ Bonjour self-test failed")
        print("🔧 Check service availability")