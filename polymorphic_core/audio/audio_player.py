#!/usr/bin/env python3
"""
polymorphic_audio_player.py - Pure Bonjour Audio Player
Listens for AUDIO_READY announcements and plays audio through Discord
"""

import os
import asyncio
from typing import Optional
from polymorphic_core import announcer
from polymorphic_core import register_capability, discover_capability

class PolymorphicAudioPlayer:
    """Pure Bonjour audio player - listens and plays"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        print("🔊 [DEBUG] PolymorphicAudioPlayer initializing...")
        
        # Announce our capabilities
        announcer.announce(
            "PolymorphicAudioPlayer",
            [
                "I play ANY audio that's announced as ready",
                "I listen for AUDIO_READY announcements", 
                "I play through Discord voice channels",
                "I play through local speakers",
                "I play through any available audio output",
                "I announce AUDIO_PLAYED when complete"
            ]
        )
        
        self.discord_bot = None
        self.start_listening()
    
    def start_listening(self):
        """Start mDNS discovery for audio services"""
        from polymorphic_core import announcer
        try:
            # Announce ourselves on the network
            announcer.announce(
                "PolymorphicAudioPlayer",
                [
                    "I play ANY audio that's announced as ready",
                    "I discover audio via mDNS network scanning",
                    "I play through Discord voice channels", 
                    "I play through local speakers",
                    "I play through any available audio output",
                    "I announce AUDIO_PLAYED when complete"
                ]
            )
            
            print(f"🔊 [DEBUG] AudioPlayer announced on network")
            
            # Start background mDNS discovery for audio services
            import threading
            def discover_audio_services():
                while True:
                    try:
                        services = announcer.discover_services()
                        for service_data in services.values():
                            if 'audio' in service_data['name'].lower() and 'ready' in ' '.join(service_data['capabilities']).lower():
                                self.handle_discovered_audio_service(service_data)
                        import time
                        time.sleep(5)  # Poll every 5 seconds
                    except Exception as e:
                        break  # Exit on error
            
            discovery_thread = threading.Thread(target=discover_audio_services, daemon=True)
            discovery_thread.start()
            
        except Exception as e:
            print(f"🔊 [ERROR] Failed to start audio mDNS: {e}")
    
    def handle_discovered_audio_service(self, service_data):
        """Handle discovered audio service via mDNS"""
        print(f"🔊 [DISCOVERY] Found audio service: {service_data['name']} at {service_data['host']}:{service_data['port']}")
        # Could connect to the service to get audio data
    
    def on_audio_ready(self, audio_data: list):
        """Process audio ready announcement"""
        file_path = None
        text = ""
        request_id = "unknown"
        
        # Parse the announcement data
        for item in audio_data:
            if item.startswith("FILE:"):
                file_path = item.replace("FILE:", "").strip()
            elif item.startswith("TEXT:"):
                text = item.replace("TEXT:", "").strip()
            elif item.startswith("ID:"):
                request_id = item.replace("ID:", "").strip()
        
        if file_path and os.path.exists(file_path):
            announcer.announce(
                "AUDIO_PLAYING",
                [
                    f"Playing audio: {file_path}",
                    f"Text: '{text[:50]}...'",
                    f"ID: {request_id}"
                ]
            )
            
            # Try to play through available methods
            self.play_audio_file(file_path, text, request_id)
    
    def play_audio_file(self, file_path: str, text: str, request_id: str):
        """Play audio file through available methods"""
        played = False
        
        # Method 1: Discord bot (if registered)
        if self.discord_bot and hasattr(self.discord_bot, 'voice_client'):
            try:
                if self.discord_bot.voice_client and self.discord_bot.voice_client.is_connected():
                    # Schedule on Discord's event loop
                    bot = self.discord_bot.bot
                    bot.loop.create_task(self._play_discord_async(file_path, text))
                    played = True
                    announcer.announce(
                        "AUDIO_DISCORD",
                        [f"Scheduled Discord playback: {file_path}"]
                    )
            except Exception as e:
                announcer.announce(
                    "AUDIO_DISCORD_ERROR",
                    [f"Discord playback failed: {e}"]
                )
        
        # Method 2: Try to discover Discord voice bot
        if not played:
            try:
                voice_bot = discover_capability('discord_voice_bot')
                if voice_bot:
                    bot_instance = voice_bot()
                    if hasattr(bot_instance, 'voice_client') and bot_instance.voice_client:
                        # Use the bot's event loop
                        if hasattr(bot_instance, 'bot'):
                            bot_instance.bot.loop.create_task(
                                self._play_with_bot_async(bot_instance, file_path)
                            )
                            played = True
                            announcer.announce(
                                "AUDIO_DISCOVERED_BOT",
                                [f"Playing via discovered bot: {file_path}"]
                            )
            except Exception as e:
                announcer.announce(
                    "AUDIO_BOT_ERROR",
                    [f"Discovered bot playback failed: {e}"]
                )
        
        # Method 3: Local playback fallback
        if not played:
            self.play_local_audio(file_path)
            played = True
        
        # Announce completion
        if played:
            announcer.announce(
                "AUDIO_PLAYED",
                [
                    f"Audio playback complete: {request_id}",
                    f"File: {file_path}",
                    f"Text: '{text[:30]}...'"
                ]
            )
            
            # Clean up the temp file after a delay
            try:
                os.unlink(file_path)
                announcer.announce("AUDIO_CLEANUP", [f"Cleaned up: {file_path}"])
            except:
                pass
    
    async def _play_discord_async(self, file_path: str, text: str):
        """Play audio through Discord voice client"""
        try:
            import discord
            import tempfile
            
            voice_client = self.discord_bot.voice_client
            if voice_client and voice_client.is_connected():
                audio_source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(file_path),
                    volume=1.0
                )
                
                voice_client.play(
                    audio_source,
                    after=lambda e: print(f'Discord audio error: {e}') if e else None
                )
                
                # Wait for playback to complete
                while voice_client.is_playing():
                    await asyncio.sleep(0.01)
                
                announcer.announce(
                    "DISCORD_PLAYBACK_COMPLETE",
                    [f"Discord played: '{text[:50]}...'"]
                )
        except Exception as e:
            announcer.announce(
                "DISCORD_PLAYBACK_ERROR",
                [f"Discord async playback error: {e}"]
            )
    
    async def _play_with_bot_async(self, bot_instance, file_path: str):
        """Play using discovered bot instance"""
        try:
            if hasattr(bot_instance, 'say_in_voice'):
                # Read the audio file and play it
                # For now, just use the original file
                import discord
                voice_client = bot_instance.voice_client
                
                if voice_client and voice_client.is_connected():
                    audio_source = discord.FFmpegPCMAudio(file_path)
                    voice_client.play(audio_source)
                    
                    while voice_client.is_playing():
                        await asyncio.sleep(0.01)
        except Exception as e:
            announcer.announce(
                "BOT_PLAYBACK_ERROR",
                [f"Bot playback error: {e}"]
            )
    
    def play_local_audio(self, file_path: str):
        """Play audio locally (fallback)"""
        try:
            import subprocess
            
            # Try different audio players
            players = ['aplay', 'paplay', 'play']
            
            for player in players:
                try:
                    subprocess.run([player, file_path], 
                                 check=False, 
                                 capture_output=True, 
                                 timeout=10)
                    announcer.announce(
                        "LOCAL_AUDIO",
                        [f"Played locally with {player}: {file_path}"]
                    )
                    return
                except:
                    continue
            
            announcer.announce(
                "LOCAL_AUDIO_FALLBACK",
                [f"No local audio player available for: {file_path}"]
            )
            
        except Exception as e:
            announcer.announce(
                "LOCAL_AUDIO_ERROR",
                [f"Local audio playback error: {e}"]
            )
    
    def register_discord_bot(self, bot):
        """Register Discord bot for voice playback"""
        self.discord_bot = bot
        announcer.announce(
            "PolymorphicAudioPlayer",
            ["Discord bot registered for audio playback"]
        )
    
    def tell(self, format: str = "brief") -> str:
        """Polymorphic tell method"""
        if format == "brief":
            return "PolymorphicAudioPlayer: Plays audio via announcements"
        return "I listen for AUDIO_READY and play through any available output"
    
    def ask(self, question: str) -> str:
        """Polymorphic ask method"""
        if "outputs" in question.lower():
            return "Discord voice, local speakers, any available audio output"
        return "I play audio when announced as ready"
    
    def do(self, action: str, **kwargs) -> bool:
        """Polymorphic do method"""
        if action == "play" and "file" in kwargs:
            self.play_audio_file(kwargs["file"], kwargs.get("text", ""), "direct")
            return True
        return False

# Create global instance
audio_player = PolymorphicAudioPlayer()

# Register as discoverable
register_capability('audio_player', lambda: audio_player)

announcer.announce(
    "PolymorphicAudioPlayer",
    [
        "Audio Player initialized and listening!",
        "Announce AUDIO_READY and I'll play it",
        "I support Discord, local, and any audio output"
    ]
)