#!/usr/bin/env python3
"""
voice_example.py - Example of how to play audio in Discord voice channel
This shows how Claude/bot could play audio files
"""
import discord
import asyncio
import os

class VoiceBot(discord.Client):
    async def on_ready(self):
        print(f'Bot ready: {self.user}')
    
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Command: !join - Bot joins your voice channel
        if message.content == '!join':
            if message.author.voice:
                channel = message.author.voice.channel
                self.voice_client = await channel.connect()
                await message.channel.send(f"Joined {channel.name}")
            else:
                await message.channel.send("You're not in a voice channel!")
        
        # Command: !play <filename> - Play an audio file
        elif message.content.startswith('!play '):
            if hasattr(self, 'voice_client') and self.voice_client:
                filename = message.content[6:]  # Remove "!play "
                
                # Check if file exists
                audio_path = f"/home/ubuntu/claude/tournament_tracker/audio/{filename}"
                if os.path.exists(audio_path):
                    # Play the audio file
                    audio_source = discord.FFmpegPCMAudio(audio_path)
                    self.voice_client.play(audio_source)
                    await message.channel.send(f"Playing: {filename}")
                else:
                    await message.channel.send(f"File not found: {filename}")
            else:
                await message.channel.send("Bot not in voice channel! Use !join first")
        
        # Command: !tts <text> - Text to speech
        elif message.content.startswith('!tts '):
            if hasattr(self, 'voice_client') and self.voice_client:
                text = message.content[5:]  # Remove "!tts "
                
                # Generate TTS audio file (requires gTTS)
                try:
                    from gtts import gTTS
                    tts = gTTS(text=text, lang='en')
                    tts.save("/tmp/tts_temp.mp3")
                    
                    # Play the TTS
                    audio_source = discord.FFmpegPCMAudio("/tmp/tts_temp.mp3")
                    self.voice_client.play(audio_source)
                    await message.channel.send(f"Speaking: {text[:50]}...")
                except ImportError:
                    await message.channel.send("TTS not available (install gTTS)")
            else:
                await message.channel.send("Bot not in voice channel! Use !join first")
        
        # Command: !announce <message> - Claude announces tournament results
        elif message.content.startswith('!announce '):
            if hasattr(self, 'voice_client') and self.voice_client:
                announcement = message.content[10:]
                
                # Example: Announce tournament winner
                try:
                    from gtts import gTTS
                    tts = gTTS(text=f"Tournament announcement: {announcement}", lang='en')
                    tts.save("/tmp/announce.mp3")
                    
                    audio_source = discord.FFmpegPCMAudio("/tmp/announce.mp3")
                    self.voice_client.play(audio_source)
                    await message.channel.send(f"📢 Announcing: {announcement}")
                except Exception as e:
                    await message.channel.send(f"Announcement failed: {e}")
        
        # Command: !leave - Bot leaves voice channel
        elif message.content == '!leave':
            if hasattr(self, 'voice_client') and self.voice_client:
                await self.voice_client.disconnect()
                await message.channel.send("Left voice channel")
            else:
                await message.channel.send("Not in a voice channel")
        
        # Command: !tournament-winner - Announce from database
        elif message.content == '!tournament-winner':
            if hasattr(self, 'voice_client') and self.voice_client:
                # Get latest tournament winner from database
                try:
                    import sys
                    sys.path.append('/home/ubuntu/claude/tournament_tracker')
                    from polymorphic_queries import query as pq
                    
                    # Query for latest tournament
                    result = pq("latest tournament winner")
                    
                    # Convert to speech
                    from gtts import gTTS
                    tts = gTTS(text=f"The latest tournament winner is: {result[:100]}", lang='en')
                    tts.save("/tmp/winner.mp3")
                    
                    # Play announcement
                    audio_source = discord.FFmpegPCMAudio("/tmp/winner.mp3")
                    self.voice_client.play(audio_source)
                    await message.channel.send(f"🏆 Announcing winner...")
                except Exception as e:
                    await message.channel.send(f"Could not get winner: {e}")

# Example of how to run
if __name__ == "__main__":
    # Load token from .env
    import sys
    sys.path.append('/home/ubuntu/claude/tournament_tracker')
    
    env_file = '/home/ubuntu/claude/tournament_tracker/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('DISCORD_BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    break
    
    # Create bot with intents
    intents = discord.Intents.default()
    intents.message_content = True
    client = VoiceBot(intents=intents)
    
    print("Starting voice bot...")
    print("Commands: !join, !play <file>, !tts <text>, !announce <text>, !leave")
    client.run(token)