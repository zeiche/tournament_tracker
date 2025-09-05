#!/usr/bin/env python3
"""
discord_service.py - Simple Discord Service Wrapper
THIS IS A THIN WRAPPER - All logic handled by claude_cli_service
"""
import os
import sys
import discord
import asyncio
import logging
from typing import Optional

# Add path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')
from claude_cli_service import process_message_async

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordService:
    """Simple Discord wrapper - forwards everything to Claude"""
    
    def __init__(self):
        """Initialize the Discord service"""
        self.client = None
        self.running = False
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        
    async def start(self, token: Optional[str] = None):
        """Start the Discord bot"""
        # Use provided token or environment variable
        bot_token = token or self.token
        if not bot_token:
            logger.error("No Discord token provided")
            return False
            
        # Create client with intents
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        # Register event handlers
        @self.client.event
        async def on_ready():
            logger.info(f"Discord bot ready: {self.client.user}")
            self.running = True
            
        @self.client.event
        async def on_message(message: discord.Message):
            # Ignore bot messages
            if message.author.bot:
                return
                
            # Log message
            logger.debug(f"[{message.channel}] {message.author}: {message.content}")
            
            # Forward to Claude service
            try:
                context = {
                    'source': 'discord',
                    'user': str(message.author),
                    'channel': str(message.channel),
                    'guild': str(message.guild) if message.guild else 'DM'
                }
                
                # Process through Claude
                result = await process_message_async(message.content, context)
                
                if result['success']:
                    response = result['response']
                    # Handle long messages
                    if len(response) > 2000:
                        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                        for chunk in chunks:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(response)
                else:
                    await message.channel.send(f"Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.channel.send("Sorry, I encountered an error.")
        
        # Start the bot
        try:
            await self.client.start(bot_token)
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            return False
            
        return True
    
    def stop(self):
        """Stop the Discord bot"""
        if self.client and self.running:
            asyncio.create_task(self.client.close())
            self.running = False
            logger.info("Discord bot stopped")
    
    def get_statistics(self):
        """Get service statistics"""
        return {
            'enabled': bool(self.token),
            'running': self.running,
            'config': {
                'mode': 'claude_cli',
                'wrapper': True
            }
        }


# Global instance
discord_service = DiscordService()


# Convenience functions for compatibility
def start_discord_bot(mode: str = 'claude') -> bool:
    """Start the Discord bot (mode ignored - always uses Claude)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(discord_service.start())


def stop_discord_bot():
    """Stop the Discord bot"""
    discord_service.stop()


def get_discord_stats():
    """Get Discord statistics"""
    return discord_service.get_statistics()


def is_discord_enabled():
    """Check if Discord is enabled"""
    return bool(discord_service.token)


# Main entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Discord Service (THIN WRAPPER)')
    parser.add_argument('--token', help='Discord bot token')
    parser.add_argument('--mode', help='Ignored - always uses Claude')
    
    args = parser.parse_args()
    
    if args.token:
        os.environ['DISCORD_BOT_TOKEN'] = args.token
    
    # Start the bot
    if not start_discord_bot():
        sys.exit(1)