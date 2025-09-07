#!/usr/bin/env python3
"""
Minimal Discord bot to test if heartbeat issues persist without polymorphic imports
"""

import discord
import asyncio
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Setup client with minimal intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    logger.info(f'✅ Minimal bot connected as {client.user}')
    logger.info(f'📡 Connected to {len(client.guilds)} guilds')

@client.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.lower() == '!ping':
        await message.channel.send('Pong! Minimal bot is working')

logger.info('🚀 Starting minimal Discord bot...')

async def main():
    await client.start(token)

if __name__ == "__main__":
    asyncio.run(main())