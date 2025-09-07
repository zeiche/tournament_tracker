#!/usr/bin/env python3
"""
voice_receiver_sidecar.py - Dedicated voice receiver using py-cord
Runs alongside main bot, only handles voice receiving
Announces audio via Bonjour for transcription
"""

import os
import sys
import asyncio
import io
from capability_announcer import announcer

# Import discord - we'll detect which version we have
import discord

# Check if we have py-cord (has Bot class) or discord.py (doesn't)
HAS_VOICE_RECORDING = hasattr(discord, 'Bot')

if not HAS_VOICE_RECORDING:
    print("WARNING: Using discord.py which doesn't support voice recording")
    print("Consider installing py-cord instead for voice support")
    # For now, we'll create a mock that just announces it can't record
    WaveSink = None
else:
    from discord.sinks import WaveSink

class VoiceReceiverSidecar:
    """Minimal voice receiver that only connects to receive audio"""
    
    def __init__(self):
        # Announce ourselves
        announcer.announce(
            "VoiceReceiverSidecar",
            [
                "I am a dedicated voice receiver",
                "I use py-cord for voice recording",
                "I announce AUDIO_AVAILABLE when I hear voice",
                "I work alongside the main Discord bot",
                "I am minimal and focused"
            ]
        )
        
        # Get token
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            # Try loading from .env
            env_file = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(env_file):
                with open(env_file) as f:
                    for line in f:
                        if line.startswith('DISCORD_BOT_TOKEN='):
                            self.token = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
        
        # Setup minimal bot
        intents = discord.Intents.default()
        intents.voice_states = True
        
        if HAS_VOICE_RECORDING:
            # Use py-cord's Bot class
            self.bot = discord.Bot(intents=intents)
        else:
            # Use discord.py's Client class
            self.bot = discord.Client(intents=intents)
        
        # Track voice connection
        self.voice_client = None
        self.setup_events()
        
    def setup_events(self):
        """Setup bot events"""
        
        @self.bot.event
        async def on_ready():
            print(f"Voice Receiver Sidecar connected as {self.bot.user}")
            announcer.announce(
                "VoiceReceiverSidecar",
                [f"Connected as {self.bot.user}", "Ready to receive voice"]
            )
            
            # Auto-join General voice channel
            for guild in self.bot.guilds:
                for channel in guild.voice_channels:
                    if channel.name.lower() == 'general':
                        try:
                            self.voice_client = await channel.connect()
                            print(f"Joined {channel.name}")
                            
                            # Start recording immediately
                            self.start_recording()
                            
                        except Exception as e:
                            print(f"Could not join voice: {e}")
                        break
                        
    def start_recording(self):
        """Start recording voice"""
        if not self.voice_client:
            return
            
        try:
            # Create custom sink that announces audio
            sink = AnnouncingSink()
            
            # Start recording with the sink
            self.voice_client.start_recording(
                sink,
                self.recording_finished,
                check=lambda m: True  # Record everyone
            )
            
            print("🎤 Started recording voice!")
            announcer.announce(
                "VoiceReceiverSidecar",
                ["Started recording voice audio"]
            )
            
        except Exception as e:
            print(f"Recording failed: {e}")
            
    def recording_finished(self, sink, error):
        """Called when recording stops"""
        if error:
            print(f"Recording error: {error}")
        else:
            print("Recording stopped")
            
    async def run(self):
        """Run the sidecar bot"""
        try:
            await self.bot.start(self.token)
        except Exception as e:
            print(f"Sidecar failed: {e}")


class AnnouncingSink(WaveSink if WaveSink else object):
    """Custom sink that announces audio via Bonjour"""
    
    def __init__(self):
        if WaveSink:
            super().__init__()
        self.audio_buffers = {}
        
    def write(self, data, user):
        """Called when audio is received"""
        # Store audio for user
        if user not in self.audio_buffers:
            self.audio_buffers[user] = io.BytesIO()
            
        self.audio_buffers[user].write(data)
        
        # Every 1 second worth of audio (48000 Hz * 2 bytes * 2 channels = 192000 bytes)
        if self.audio_buffers[user].tell() > 192000:
            # Get the audio data
            audio_data = self.audio_buffers[user].getvalue()
            
            # Announce it's available
            announcer.announce(
                "AUDIO_AVAILABLE",
                {
                    'source': f'discord_voice_{user}',
                    'user_id': str(user),
                    'audio_data': audio_data,
                    'format': 'pcm_s16le',
                    'channels': 2,
                    'sample_rate': 48000
                }
            )
            
            print(f"📢 Announced audio from user {user} ({len(audio_data)} bytes)")
            
            # Reset buffer
            self.audio_buffers[user] = io.BytesIO()


if __name__ == "__main__":
    print("Starting Voice Receiver Sidecar...")
    sidecar = VoiceReceiverSidecar()
    
    try:
        asyncio.run(sidecar.run())
    except KeyboardInterrupt:
        print("\nSidecar stopped")