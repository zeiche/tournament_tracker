#!/usr/bin/env python3
"""
start_audio_stream.py - Start the continuous audio stream service
This runs independently of Twilio and provides continuous music
"""

from continuous_stream_service import get_stream_service
from capability_announcer import announcer
import time

def start_continuous_audio():
    """Start the continuous audio streaming service"""
    
    # Get the stream service (starts automatically)
    stream_service = get_stream_service()
    
    announcer.announce(
        "AUDIO_STREAM_START",
        [
            "Starting continuous audio stream",
            "Music will play continuously",
            "This runs INDEPENDENTLY of Twilio",
            "Bot speech will be mixed INTO this stream"
        ]
    )
    
    # The stream service is already running in background
    # Just keep the script alive
    print("🎵 Continuous audio stream running...")
    print("🔊 Music playing from current position")
    print("🎤 Bot speech will be mixed in when needed")
    print("✨ This is INDEPENDENT of Twilio API")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping audio stream...")
        stream_service.stop()

if __name__ == "__main__":
    start_continuous_audio()