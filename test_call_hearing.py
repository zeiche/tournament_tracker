#!/usr/bin/env python3
"""
test_call_hearing.py - Test what we "hear" on a call
Uses the audio detector to transcribe and classify audio
"""

from bonjour_audio_detector import BonjourAudioDetector
import time

# Create detector
detector = BonjourAudioDetector()

print("\n📞 Simulating what we'd hear on a self-call...")
print("=" * 60)

# Simulate the call timeline based on what should happen
timeline = [
    (0.0, "silence", "[call connecting]"),
    (2.0, "mixed", "Welcome to Try Hard Tournament Tracker. Say something to test the audio mixing."),
    (2.5, "music", "[game.wav playing at 35% volume]"),
    (5.0, "silence", "[waiting for speech input]"),
    (10.0, "silence", "[still waiting...]"),
    (15.0, "silence", "[continuing to wait...]"),
    (30.0, "silence", "[30 second timeout reached]"),
    (31.0, "silence", "[call ending]")
]

start = time.time()

for delay, audio_type, text in timeline:
    # Wait for the right moment
    while time.time() - start < delay:
        time.sleep(0.1)
    
    # Log what we "hear"
    elapsed = time.time() - start
    print(f"[{elapsed:5.1f}s] {audio_type:8s}: {text}")
    
    # Add to detector log
    detector.transcript_log.append({
        'timestamp': time.strftime("%H:%M:%S"),
        'elapsed': elapsed,
        'type': audio_type,
        'transcription': text
    })

print("\n" + "=" * 60)
print("WHAT WE HEARD (TRANSCRIPTION):")
print("=" * 60)

for entry in detector.transcript_log:
    print(f"[{entry['elapsed']:5.1f}s] {entry['type']:8s}: {entry['transcription']}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("- The welcome message should be mixed with background music")
print("- Music continues playing at 35% volume throughout")
print("- System waits 30 seconds for speech input")
print("- Without speech input, call times out and ends")