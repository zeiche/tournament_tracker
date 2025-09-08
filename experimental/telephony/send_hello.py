#!/usr/bin/env python3
"""Send a hello message to #general channel"""

import discord
import asyncio
import os
from pathlib import Path

async def send_hello():
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
    
    # Create client
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'Connected as {client.user}')
        
        # Find #general channel and send message
        for guild in client.guilds:
            for channel in guild.text_channels:
                if channel.name.lower() == 'general':
                    await channel.send("👋 Hi everyone! Claude here, now connected with voice capabilities! I'm in the #General voice channel and ready to help with tournament tracking and answer questions!")
                    print(f"Sent hello message to #{channel.name}")
                    await client.close()
                    return
        
        print("No #general channel found")
        await client.close()
    
    await client.start(token)

if __name__ == "__main__":
    asyncio.run(send_hello())