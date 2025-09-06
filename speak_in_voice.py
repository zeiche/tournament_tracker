#!/usr/bin/env python3
"""Speak in the voice channel using TTS"""

import discord
import asyncio
import os
import subprocess
import tempfile
from pathlib import Path

async def speak_hi():
    # Load token
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DISCORD_BOT_TOKEN='):
                        token = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
    
    if not token:
        print("No token found!")
        return
    
    # Create client with voice support
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    intents.voice_states = True
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'Connected as {client.user}')
        
        # Find #General voice channel
        for guild in client.guilds:
            for vc in guild.voice_channels:
                if vc.name.lower() == 'general':
                    try:
                        # Connect to voice channel
                        voice_client = await vc.connect()
                        print(f'Connected to #{vc.name}')
                        
                        # Generate TTS audio file
                        text = "Hi everyone! Claude here in the voice channel!"
                        temp_wav = tempfile.mktemp(suffix='.wav')
                        
                        # Use espeak to generate audio
                        subprocess.run([
                            'espeak',
                            '-w', temp_wav,
                            '-s', '150',  # Speed
                            '-p', '50',   # Pitch
                            text
                        ], check=True)
                        
                        print(f'Generated audio: {temp_wav}')
                        
                        # Play the audio
                        audio_source = discord.FFmpegPCMAudio(temp_wav)
                        voice_client.play(
                            audio_source,
                            after=lambda e: print(f'Playback error: {e}') if e else print('Playback complete')
                        )
                        
                        # Wait for playback to finish
                        while voice_client.is_playing():
                            await asyncio.sleep(0.5)
                        
                        print('Finished speaking!')
                        
                        # Clean up
                        await asyncio.sleep(1)
                        await voice_client.disconnect()
                        os.remove(temp_wav)
                        
                    except Exception as e:
                        print(f'Error: {e}')
                    
                    await client.close()
                    return
        
        print("No #General voice channel found")
        await client.close()
    
    await client.start(token)

if __name__ == "__main__":
    print("Speaking 'Hi' in #General voice channel...")
    asyncio.run(speak_hi())