#!/usr/bin/env python3
"""Send a !say command to the Discord bot to trigger TTS"""

import discord
import asyncio
import os
from pathlib import Path

async def trigger_tts():
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
    
    # Create a temporary client just to send a message
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'Connected as {client.user}')
        
        # Find a text channel to send the command
        for guild in client.guilds:
            # Try #general first
            for channel in guild.text_channels:
                if channel.name.lower() in ['general', 'bot-commands', 'bots']:
                    print(f"Sending !say command to #{channel.name}")
                    await channel.send("!say Hi everyone! Claude here, speaking through the polymorphic voice system!")
                    await asyncio.sleep(2)
                    await client.close()
                    return
            
            # Use first available text channel
            if guild.text_channels:
                channel = guild.text_channels[0]
                print(f"Sending !say command to #{channel.name}")
                await channel.send("!say Hi everyone! Claude here, speaking through the polymorphic voice system!")
                await asyncio.sleep(2)
                await client.close()
                return
        
        print("No text channels found")
        await client.close()
    
    await client.start(token)

if __name__ == "__main__":
    print("Triggering TTS through Discord bot...")
    asyncio.run(trigger_tts())