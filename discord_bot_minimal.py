#!/usr/bin/env python3
"""
discord_bot_minimal.py - ABSOLUTE MINIMAL Discord Bot
This is a pure message conduit. ZERO dependencies on other modules.
It just receives messages and sends responses.
"""
import os
import discord
import asyncio
import logging

# Simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinimalDiscordBot:
    """Absolute minimal Discord bot - pure conduit"""
    
    def __init__(self):
        """Initialize with token from environment"""
        # Get token from environment
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            logger.error("No DISCORD_BOT_TOKEN in environment")
            raise ValueError("DISCORD_BOT_TOKEN not set")
        
        # Create client with minimal intents
        intents = discord.Intents.default()
        intents.message_content = True  # Need this to see message content
        self.client = discord.Client(intents=intents)
        
        # Register event handlers directly
        @self.client.event
        async def on_ready():
            """Bot connected and ready"""
            logger.info(f"Bot ready: {self.client.user}")
            logger.info(f"Bot ID: {self.client.user.id}")
            logger.info("Guilds:")
            for guild in self.client.guilds:
                logger.info(f"  - {guild.name} (id: {guild.id})")
        
        @self.client.event
        async def on_message(message):
            """Handle incoming message - pure passthrough"""
            # Ignore bot's own messages
            if message.author == self.client.user:
                return
            
            # Ignore other bots
            if message.author.bot:
                return
            
            # Log the message
            logger.info(f"Message from {message.author}: {message.content}")
            
            # Simple echo response for testing
            # In production, this would call your message handler
            response = await self.process_message(message.content, message)
            
            # Send response if we have one
            if response:
                try:
                    await message.channel.send(response)
                except Exception as e:
                    logger.error(f"Failed to send response: {e}")
    
    async def process_message(self, content: str, message: discord.Message) -> str:
        """
        Process a message and return response.
        This is where you'd integrate with your actual message handler.
        For now, just a simple echo to verify the bot works.
        """
        # Simple test responses
        if content.lower() == "ping":
            return "pong!"
        elif content.lower() == "hello":
            return f"Hello {message.author.mention}!"
        elif content.lower().startswith("echo "):
            return content[5:]  # Echo everything after "echo "
        else:
            # In production, forward to your actual handler here
            # For now, just acknowledge
            return f"Received: {content[:50]}..." if len(content) > 50 else f"Received: {content}"
    
    def run(self):
        """Run the bot"""
        logger.info("Starting minimal Discord bot...")
        logger.info(f"Token present: {'Yes' if self.token else 'No'}")
        logger.info(f"Token length: {len(self.token) if self.token else 0}")
        
        try:
            self.client.run(self.token)
        except discord.LoginFailure:
            logger.error("Failed to login - check your DISCORD_BOT_TOKEN")
            raise
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise


def main():
    """Main entry point"""
    # Load .env file if it exists
    env_file = '/home/ubuntu/claude/tournament_tracker/.env'
    if os.path.exists(env_file):
        logger.info(f"Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Create and run bot
    try:
        bot = MinimalDiscordBot()
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())