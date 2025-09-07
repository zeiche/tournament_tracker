#!/usr/bin/env python3
"""
Simple Discord bot without voice to test connection
"""

import discord
import asyncio
import os
from pathlib import Path

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
    raise ValueError("No Discord token found!")

# Setup client
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Bot connected as {client.user}')
    print(f'📡 Connected to {len(client.guilds)} guilds')
    for guild in client.guilds:
        print(f'  - {guild.name} (ID: {guild.id})')

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.lower() == '!test':
        await message.channel.send('✅ Bot is working!')
    elif message.content.lower() == '!status':
        await message.channel.send(f'Connected as {client.user}')

print('🚀 Starting simple Discord bot...')
client.run(token)