#!/usr/bin/env python3
"""
discord_service.py - Minimal Discord Service
Pure message conduit - receives messages, sends to query handler, returns response.
NO complex dependencies. Just Discord + optional query handler.
"""
import os
import sys
import discord
import asyncio
import logging
from typing import Optional

# Simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordService:
    """Minimal Discord service - pure message conduit"""
    
    def __init__(self):
        """Initialize service"""
        self.client = None
        self.running = False
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        
        # Try to load query handler (optional)
        self.query_handler = None
        try:
            # Add path if needed
            if '/home/ubuntu/claude/tournament_tracker' not in sys.path:
                sys.path.append('/home/ubuntu/claude/tournament_tracker')
            from polymorphic_queries import query as pq
            self.query_handler = pq
            logger.info("Query handler loaded")
        except ImportError as e:
            logger.warning(f"Query handler not available: {e}")
    
    async def start(self, token: Optional[str] = None):
        """Start the Discord bot"""
        bot_token = token or self.token
        if not bot_token:
            logger.error("No Discord token provided")
            return False
        
        # Create client with DM support
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True  # Enable DM messages
        self.client = discord.Client(intents=intents)
        
        # Register handlers
        @self.client.event
        async def on_ready():
            logger.info(f"Bot ready: {self.client.user}")
            self.running = True
        
        @self.client.event
        async def on_message(message: discord.Message):
            # Skip bot messages
            if message.author.bot:
                return
            
            # Process message
            content = message.content.strip()
            if not content:
                return
            
            logger.info(f"[{message.author}]: {content}")
            
            # Handle with query system if available
            if self.query_handler:
                try:
                    # Run query in executor to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, self.query_handler, content)
                    
                    if result:
                        # Format as code block for readability
                        response = f"```\n{result}\n```"
                        
                        # Handle long messages
                        if len(response) > 2000:
                            # Split into chunks
                            chunks = []
                            lines = result.split('\n')
                            current_chunk = []
                            current_size = 0
                            
                            for line in lines:
                                line_size = len(line) + 1  # +1 for newline
                                if current_size + line_size > 1900:
                                    # Send current chunk
                                    chunks.append("```\n" + '\n'.join(current_chunk) + "\n```")
                                    current_chunk = [line]
                                    current_size = line_size
                                else:
                                    current_chunk.append(line)
                                    current_size += line_size
                            
                            # Add last chunk
                            if current_chunk:
                                chunks.append("```\n" + '\n'.join(current_chunk) + "\n```")
                            
                            # Send all chunks
                            for chunk in chunks:
                                await message.channel.send(chunk)
                        else:
                            await message.channel.send(response)
                    else:
                        await message.channel.send("No results found.")
                        
                except Exception as e:
                    logger.error(f"Query error: {e}")
                    error_msg = str(e)
                    if len(error_msg) > 200:
                        error_msg = error_msg[:200] + "..."
                    await message.channel.send(f"Error: {error_msg}")
            else:
                # No query handler - echo mode
                await message.channel.send(f"Echo: {content}")
        
        # Run the bot
        try:
            await self.client.start(bot_token)
        except discord.LoginFailure:
            logger.error("Discord login failed - invalid token")
            return False
        except Exception as e:
            logger.error(f"Bot start failed: {e}")
            return False
        
        return True
    
    def stop(self):
        """Stop the bot"""
        if self.client and self.running:
            asyncio.create_task(self.client.close())
            self.running = False
            logger.info("Bot stopped")
    
    def get_statistics(self):
        """Get statistics"""
        return {
            'enabled': bool(self.token),
            'running': self.running,
            'query_handler': self.query_handler is not None
        }


# Global instance
discord_service = DiscordService()


# Compatibility functions
def start_discord_bot(mode: str = None) -> bool:
    """Start Discord bot - now using Claude bridge by default"""
    # Load .env if needed
    env_file = '/home/ubuntu/claude/tournament_tracker/.env'
    if os.path.exists(env_file) and not os.getenv('DISCORD_BOT_TOKEN'):
        logger.info("Loading .env file")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    value = value.strip('"').strip("'")
                    if not key.startswith('export'):
                        os.environ[key] = value
    
    # Use Claude bridge bot for natural conversation
    try:
        logger.info("Starting Discord Claude bridge bot...")
        from discord_claude_bridge import ClaudeBridgeBot
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            logger.error("DISCORD_BOT_TOKEN not set")
            return False
        bot = ClaudeBridgeBot(token)
        bot.run()
        return True
    except ImportError as e:
        logger.warning(f"Claude bridge not available, falling back to basic bot: {e}")
        # Fall back to basic bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(discord_service.start())
        except KeyboardInterrupt:
            logger.info("Stopped by user")
            return True
    except KeyboardInterrupt:
        logger.info("Stopped by user")
        return True
    except Exception as e:
        logger.error(f"Bot failed: {e}")
        return False


def stop_discord_bot():
    """Stop Discord bot"""
    discord_service.stop()


def get_discord_stats():
    """Get Discord statistics"""
    return discord_service.get_statistics()


def is_discord_enabled():
    """Check if Discord is enabled"""
    # Load token if not loaded
    if not discord_service.token:
        env_file = '/home/ubuntu/claude/tournament_tracker/.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DISCORD_BOT_TOKEN='):
                        value = line.split('=', 1)[1].strip().strip('"').strip("'")
                        os.environ['DISCORD_BOT_TOKEN'] = value
                        discord_service.token = value
                        break
    
    return bool(discord_service.token)


# Main entry point
if __name__ == "__main__":
    if not start_discord_bot():
        sys.exit(1)