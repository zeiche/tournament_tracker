#!/usr/bin/env python3
"""
discord_claude_bridge.py - Simple Discord to Claude bridge
Routes ALL Discord messages directly to Claude for natural conversation
"""
import os
import sys
import discord
import asyncio
import logging
from discord.ext import commands

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')


class ClaudeBridgeBot:
    """Discord bot that bridges all messages to Claude"""
    
    def __init__(self, token: str):
        self.token = token
        
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.guild_messages = True
        
        self.client = discord.Client(intents=intents)
        
        # Try to load Claude CLI service directly
        try:
            from claude_cli_service import ask_claude as process_message
            self.process_message = process_message
            logger.info("Claude CLI service loaded successfully")
        except ImportError as e:
            logger.error(f"Failed to load Claude CLI service: {e}")
            self.process_message = None
        
        # Store conversation history per channel
        self.conversations = {}
        
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
        """Handle a Discord message by sending it to Claude"""
        content = message.content.strip()
        
        # Log it
        logger.info(f"[{message.author}]: {content}")
        
        # Skip empty messages
        if not content:
            return
        
        # Send typing indicator
        async with message.channel.typing():
            try:
                if self.process_message:
                    # Get or create conversation history for this channel
                    channel_id = str(message.channel.id)
                    if channel_id not in self.conversations:
                        self.conversations[channel_id] = []
                    
                    # Add to conversation history
                    self.conversations[channel_id].append(f"{message.author.name}: {content}")
                    
                    # Keep only last 10 messages for context
                    self.conversations[channel_id] = self.conversations[channel_id][-10:]
                    
                    # Get dynamic capability announcements AND enable polymorphic models
                    try:
                        from capability_announcer import get_full_context
                        
                        # Enable polymorphic models for Claude to discover
                        from tournament_models_simplified import simplify_existing_models
                        simplify_existing_models()
                        
                        capabilities = get_full_context()
                    except Exception as e:
                        logger.warning(f"Could not get full capabilities: {e}")
                        capabilities = "Running in basic mode."
                    
                    # Build context with system knowledge
                    system_prompt = f"""You are a tournament tracker assistant in Discord.
You help users understand FGC tournaments, players, and events.
You're talking to Discord users who want tournament information.

{capabilities}

Use these announced capabilities to help answer user questions."""
                    
                    context = {
                        'source': 'discord',
                        'user': message.author.name,
                        'channel': message.channel.name if hasattr(message.channel, 'name') else 'DM',
                        'conversation_history': self.conversations[channel_id],
                        'system_prompt': system_prompt
                    }
                    
                    # Get Claude's response
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        self.process_message,
                        content,
                        context
                    )
                    
                    # Handle the response (ask_claude returns a string)
                    if result and not result.startswith("Error:"):
                        response = result
                        
                        # Add to conversation history
                        self.conversations[channel_id].append(f"Claude: {response}")
                        
                        # Send response (handle long messages)
                        if len(response) > 2000:
                            # Split into chunks
                            for i in range(0, len(response), 1900):
                                chunk = response[i:i+1900]
                                await message.channel.send(chunk)
                        else:
                            await message.channel.send(response)
                    else:
                        error_msg = result if result else "No response"
                        await message.channel.send(f"Sorry, I had trouble processing that: {error_msg[:200]}")
                else:
                    # Fallback if Claude not available
                    await message.channel.send("Claude service is not available. Please check the setup.")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.channel.send(f"Error: {str(e)[:200]}")
    
    def run(self):
        """Run the bot"""
        logger.info("Starting Claude bridge bot...")
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
                    # Don't export, just set for this process
                    if not key.startswith('export'):
                        os.environ[key] = value
        logger.info("Environment loaded from .env")
    else:
        logger.warning(f"No .env file found at {env_file}")


if __name__ == "__main__":
    # Load environment
    load_env()
    
    # Get token
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment")
        sys.exit(1)
    
    # Run bot
    bot = ClaudeBridgeBot(token)
    bot.run()