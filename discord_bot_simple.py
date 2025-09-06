#!/usr/bin/env python3
"""
discord_bot_simple.py - Simple Discord Bot with Database Queries
A minimal Discord bot that forwards messages to the polymorphic query system.
NO complex dependencies, just Discord + database queries.
"""
import os
import sys
import discord
import asyncio
import logging

# Add path for imports (minimal - just what we need)
sys.path.append('/home/ubuntu/claude/tournament_tracker')

# Simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleDiscordBot:
    """Simple Discord bot - forwards to polymorphic queries"""
    
    def __init__(self):
        """Initialize with token from environment"""
        # Get token
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            raise ValueError("DISCORD_BOT_TOKEN not set in environment")
        
        # Create Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        # Try to import query handler (optional)
        self.query_handler = None
        try:
            from polymorphic_queries import query as pq
            self.query_handler = pq
            logger.info("Polymorphic query handler loaded")
        except ImportError:
            logger.warning("Polymorphic queries not available - using echo mode")
        
        # Register events
        @self.client.event
        async def on_ready():
            logger.info(f"Bot connected: {self.client.user}")
            for guild in self.client.guilds:
                logger.info(f"  Guild: {guild.name}")
        
        @self.client.event
        async def on_message(message):
            # Skip bot messages
            if message.author.bot:
                return
            
            # Process the message
            await self.handle_message(message)
    
    async def handle_message(self, message: discord.Message):
        """Handle a Discord message"""
        content = message.content.strip()
        
        # Log it
        logger.info(f"[{message.author}]: {content}")
        
        # Skip empty messages
        if not content:
            return
        
        # Process with query handler if available
        if self.query_handler:
            try:
                # Run query in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    self.query_handler, 
                    content
                )
                
                # Send result
                if result:
                    # Handle long messages
                    if len(result) > 2000:
                        # Split into chunks
                        for i in range(0, len(result), 1900):
                            chunk = result[i:i+1900]
                            await message.channel.send(f"```\n{chunk}\n```")
                    else:
                        await message.channel.send(f"```\n{result}\n```")
                else:
                    await message.channel.send("No results found.")
                    
            except Exception as e:
                logger.error(f"Query error: {e}")
                await message.channel.send(f"Error: {str(e)[:200]}")
        else:
            # Echo mode (no query handler)
            await message.channel.send(f"Echo: {content}")
    
    def run(self):
        """Run the bot"""
        logger.info("Starting simple Discord bot...")
        self.client.run(self.token)


def load_env():
    """Load environment variables from .env file"""
    env_file = '/home/ubuntu/claude/tournament_tracker/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key] = value
        logger.info("Environment loaded from .env")


def main():
    """Main entry point"""
    # Load environment
    load_env()
    
    # Check token
    if not os.getenv('DISCORD_BOT_TOKEN'):
        logger.error("DISCORD_BOT_TOKEN not found in environment")
        logger.error("Please set it in .env file")
        return 1
    
    # Run bot
    try:
        bot = SimpleDiscordBot()
        bot.run()
    except discord.LoginFailure:
        logger.error("Discord login failed - token may be invalid")
        logger.error("Please check DISCORD_BOT_TOKEN in .env file")
        return 1
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Bot failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())