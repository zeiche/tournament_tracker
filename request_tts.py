#!/usr/bin/env python3
"""
request_tts.py - Request TTS through the voice service
This discovers the voice service and asks it to speak
"""

import asyncio
from capability_discovery import discover_capability
from capability_announcer import announcer

async def say_hi_through_service():
    """Discover voice service and request TTS"""
    
    # Discover the voice service
    announcer.announce("TTSRequester", ["Looking for voice service..."])
    
    # Import voice service to ensure it's registered
    import voice_service
    voice = discover_capability('voice')
    
    if not voice:
        print("❌ Voice service not available!")
        return
    
    announcer.announce("TTSRequester", ["Found voice service!"])
    
    # The bot should already be connected with a guild
    # We need to find which guild ID the bot is in
    # For now, we'll use a known guild ID or find it from the voice service
    
    # Check if voice service is connected anywhere
    status = voice.get_status()
    print(f"Voice service status: {status}")
    
    if status['connected_guilds'] > 0:
        # Get the first connected guild
        guild_id = list(status['connections'].keys())[0]
        channel_name = status['connections'][guild_id]['channel']
        
        print(f"Found connection in guild {guild_id}, channel: {channel_name}")
        
        # Request TTS
        announcer.announce("TTSRequester", [f"Requesting TTS in guild {guild_id}"])
        
        success = await voice.speak(
            guild_id,
            "Hi everyone! This is Claude speaking in the voice channel through the polymorphic system!"
        )
        
        if success:
            print("✅ Successfully spoke in voice channel!")
            announcer.announce("TTSRequester", ["TTS request successful!"])
        else:
            print("❌ Failed to speak")
            announcer.announce("TTSRequester", ["TTS request failed"])
    else:
        print("❌ Voice service is not connected to any guilds")
        announcer.announce("TTSRequester", ["No voice connections found"])

if __name__ == "__main__":
    print("Requesting TTS through voice service...")
    asyncio.run(say_hi_through_service())