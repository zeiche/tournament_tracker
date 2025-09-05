#!/usr/bin/env python3
"""
discord_bridge.py - Minimal Discord Bridge
Pure message forwarding with ZERO business logic.
All logic happens in claude_ai_service.
"""
import os
import sys
import discord
import asyncio
import logging
from typing import Optional

# Add parent directory to path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')
from claude_cli_service import process_message_async

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordBridge:
    """Minimal Discord bridge - just forwards messages to AI service"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize bridge with token"""
        self.token = token or os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            raise ValueError("No Discord token provided")
        
        # Create client with necessary intents
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        # Register handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
    
    async def on_ready(self):
        """Bot is ready"""
        logger.info(f"Discord bridge ready: {self.client.user}")
        for guild in self.client.guilds:
            logger.info(f"  Connected to: {guild.name}")
    
    async def on_message(self, message: discord.Message):
        """
        Handle incoming message - pure bridge, no logic
        
        Just forward to AI service and send response back
        """
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Log for debugging
        logger.info(f"[{message.guild}#{message.channel}] {message.author}: {message.content}")
        
        # Build context for AI service
        context = {
            'source': 'discord',
            'user': str(message.author),
            'channel': str(message.channel),
            'guild': str(message.guild) if message.guild else 'DM',
            'is_dm': isinstance(message.channel, discord.DMChannel),
            'is_mention': self.client.user in message.mentions,
            'message_id': str(message.id)
        }
        
        # Send to AI service
        try:
            result = await process_message_async(message.content, context)
            
            if result['success']:
                # Send response back to Discord
                response = result['response']
                
                # Handle long messages (Discord limit is 2000 chars)
                if len(response) > 2000:
                    # Split into chunks
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(response)
                    
            else:
                # Error response
                error = result.get('error', 'Unknown error')
                await message.channel.send(f"Sorry, I couldn't process that: {error}")
                
        except Exception as e:
            logger.error(f"Bridge error: {e}")
            await message.channel.send("Sorry, I encountered an error processing your message.")
    
    def run(self):
        """Run the bridge"""
        logger.info("Starting Discord bridge...")
        self.client.run(self.token)


def main():
    """Main entry point"""
    bridge = DiscordBridge()
    bridge.run()


if __name__ == "__main__":
    main()