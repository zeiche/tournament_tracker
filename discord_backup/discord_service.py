#!/usr/bin/env python3
"""
discord_service.py - Minimal Discord Service
Pure message conduit - receives messages, sends to query handler, returns response.
NO complex dependencies. Just Discord + optional query handler.
"""

# ENFORCE THE RULE: Everything goes through go.py!
import go_py_guard

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
        self.voice_service = None
        
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
        
        # Discover services via Bonjour pattern
        try:
            from capability_discovery import discover_capability
            
            # Import services so they register themselves
            import polymorphic_async  # Async service for everyone!
            import voice_service
            import voice_listener
            import discord_voice_receiver
            import voice_conversation_listener
            import polymorphic_storage
            import discord_audio_sink
            
            # Discover voice service
            self.voice_service = discover_capability('voice')
            if self.voice_service:
                logger.info("Voice service discovered and available")
            else:
                logger.info("Voice service not discovered")
                
            # Discover voice listener service
            self.voice_listener = discover_capability('voice_listener')
            if self.voice_listener:
                logger.info("Voice listener service discovered and available")
            else:
                logger.info("Voice listener service not discovered")
                
        except ImportError as e:
            logger.info(f"Capability discovery not available: {e}")
    
    async def start(self, token: Optional[str] = None):
        """Start the Discord bot"""
        bot_token = token or self.token
        if not bot_token:
            logger.error("No Discord token provided")
            return False
        
        # Create client with DM and voice support
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True  # Enable DM messages
        intents.voice_states = True  # Enable voice support
        intents.guilds = True
        self.client = discord.Client(intents=intents)
        
        # Register handlers
        @self.client.event
        async def on_ready():
            logger.info(f"Bot ready: {self.client.user}")
            self.running = True
            
            # Initialize voice service with our client if available
            if self.voice_service:
                await self.voice_service.initialize_with_client(self.client)
                
                # Auto-join #General voice channel if it exists
                for guild in self.client.guilds:
                    for channel in guild.voice_channels:
                        if channel.name.lower() == 'general':
                            success = await self.voice_service.join_channel(guild.id, channel.name)
                            if success:
                                logger.info(f"Auto-joined #{channel.name} in {guild.name}")
                                await self.voice_service.speak(
                                    guild.id, 
                                    "Claude is now connected to the General voice channel"
                                )
                                
                                # Enable voice mode if listener is available
                                if self.voice_listener:
                                    self.voice_listener.enable_voice_mode(guild.id, channel.id)
                                    logger.info(f"Voice mode enabled in #{channel.name}")
                                
                                # Setup voice receiver to announce audio events
                                voice_receiver = discover_capability('discord_voice_receiver')
                                if voice_receiver and guild.id in self.voice_service.voice_clients:
                                    vc = self.voice_service.voice_clients[guild.id]
                                    voice_receiver.setup_voice_client(vc, guild.id)
                                    logger.info(f"Voice receiver setup for #{channel.name}")
        
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
            
            # Check for voice simulation commands
            if content.lower().startswith('!voice '):
                # Announce simulated voice through the voice receiver
                voice_receiver = discover_capability('discord_voice_receiver')
                if voice_receiver:
                    voice_text = content[7:].strip()
                    voice_receiver.simulate_voice_received(
                        message.author.id,
                        message.guild.id if hasattr(message, 'guild') else 0,
                        voice_text
                    )
                    await message.channel.send("🎤 Voice command announced to system")
                else:
                    # Fallback to old method
                    if self.voice_listener:
                        voice_text = content[7:].strip()
                        response = await self.voice_listener.process_voice_command(
                            message.guild.id if hasattr(message, 'guild') else 0,
                            message.author.id,
                            voice_text
                        )
                        
                        if response:
                            await message.channel.send(f"🎤 Claude says: {response}")
                            if self.voice_service and hasattr(message, 'guild'):
                                await self.voice_service.speak(message.guild.id, response)
                return
            
            # Check for voice commands
            if self.voice_service and content.lower().startswith(('!join', '!leave', '!say')):
                if content.lower() == '!join':
                    # Join the user's voice channel
                    if hasattr(message, 'guild') and message.guild:
                        success = await self.voice_service.join_user_channel(
                            message.guild.id, 
                            message.author.id
                        )
                        if success:
                            await message.channel.send("🎤 Joined your voice channel!")
                        else:
                            await message.channel.send("❌ Could not join voice channel")
                            
                elif content.lower() == '!leave':
                    # Leave voice channel
                    if hasattr(message, 'guild') and message.guild:
                        success = await self.voice_service.leave_channel(message.guild.id)
                        if success:
                            await message.channel.send("👋 Left voice channel")
                        else:
                            await message.channel.send("❌ Not in a voice channel")
                            
                elif content.lower().startswith('!say '):
                    # Say something in voice
                    text = content[5:].strip()
                    if hasattr(message, 'guild') and message.guild:
                        success = await self.voice_service.speak(message.guild.id, text)
                        if success:
                            await message.channel.send(f"🎙️ Said: {text}")
                        else:
                            await message.channel.send("❌ Not connected to voice")
                return
            
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
    
    # Use THE polymorphic bridge - the ONE true bridge
    try:
        logger.info("Starting Polymorphic Discord Bridge...")
        from polymorphic_discord_bridge import main
        main()
        return True
    except ImportError as e:
        logger.error(f"Polymorphic bridge not available: {e}")
        return False
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