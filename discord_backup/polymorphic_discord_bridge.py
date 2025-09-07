#!/usr/bin/env python3
"""
polymorphic_discord_bridge.py - THE ONE TRUE DISCORD BRIDGE
This is the ONLY Discord bridge. It discovers and uses ALL capabilities.
"""

import discord
import asyncio
import os
import logging
from pathlib import Path
from capability_announcer import announcer
from capability_discovery import discover_capability
from shutdown_coordinator import on_shutdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolymorphicDiscordBridge:
    """
    The ONE bridge that connects Discord to ALL capabilities.
    It discovers what's available and uses it.
    """
    
    def __init__(self):
        # Announce ourselves
        announcer.announce(
            "PolymorphicDiscordBridge",
            [
                "I am the ONE Discord bridge",
                "I discover all available capabilities",
                "I route messages to appropriate handlers",
                "I manage voice connections if available",
                "I handle queries if available",
                "I am polymorphic - I adapt to what's available"
            ]
        )
        
        # Load token
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            env_file = Path(__file__).parent / '.env'
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('DISCORD_BOT_TOKEN='):
                            self.token = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
        
        if not self.token:
            raise ValueError("No Discord token found!")
        
        # Discover available capabilities
        self.capabilities = {}
        self.discover_capabilities()
        
        # Setup Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        intents.members = True
        intents.dm_messages = True
        
        self.client = discord.Client(intents=intents)
        self.setup_handlers()
        
        # Register for shutdown
        @on_shutdown
        async def shutdown_bridge():
            await self.shutdown()
            
        self.shutdown_handler = shutdown_bridge
        
    def discover_capabilities(self):
        """Discover all available capabilities"""
        
        # TEMPORARILY DISABLE VOICE IMPORTS TO TEST
        # These might be causing the heartbeat blocking
        announcer.announce("PolymorphicDiscordBridge", ["Voice imports disabled for testing"])
        
        # Try to discover voice service
        try:
            voice = discover_capability('voice')
            if voice:
                self.capabilities['voice'] = voice
                announcer.announce("PolymorphicDiscordBridge", ["✅ Voice capability discovered"])
        except Exception as e:
            announcer.announce("PolymorphicDiscordBridge", [f"Voice not available: {e}"])
        
        # Try to discover voice receiver
        try:
            voice_receiver = discover_capability('discord_voice_receiver')
            if voice_receiver:
                self.capabilities['voice_receiver'] = voice_receiver
                announcer.announce("PolymorphicDiscordBridge", ["✅ Voice receiver discovered"])
        except Exception as e:
            announcer.announce("PolymorphicDiscordBridge", [f"Voice receiver not available: {e}"])
        
        # Try to discover query handler
        try:
            from polymorphic_queries import query as pq
            self.capabilities['query'] = pq
            announcer.announce("PolymorphicDiscordBridge", ["✅ Query capability discovered"])
        except Exception as e:
            announcer.announce("PolymorphicDiscordBridge", [f"Query not available: {e}"])
        
        # Try to discover Claude service (lazy load to avoid blocking)
        try:
            # Don't instantiate ClaudeCLIService during init - it starts threads
            # Just mark it as available and create it lazily when needed
            from claude_cli_service import ClaudeCLIService
            self.capabilities['claude'] = 'lazy'  # Mark for lazy loading
            self._claude_class = ClaudeCLIService  # Store class for later
            announcer.announce("PolymorphicDiscordBridge", ["✅ Claude capability marked for lazy loading"])
        except Exception as e:
            announcer.announce("PolymorphicDiscordBridge", [f"Claude not available: {e}"])
        
        # Try to discover image capabilities
        try:
            from polymorphic_discord_sender import send_to_discord
            self.capabilities['send'] = send_to_discord
            announcer.announce("PolymorphicDiscordBridge", ["✅ Send capability discovered"])
        except Exception as e:
            announcer.announce("PolymorphicDiscordBridge", [f"Send not available: {e}"])
        
        announcer.announce(
            "PolymorphicDiscordBridge",
            [f"Discovered {len(self.capabilities)} capabilities: {list(self.capabilities.keys())}"]
        )
    
    async def _initialize_voice(self):
        """Initialize voice connections separately to avoid blocking"""
        try:
            voice = self.capabilities.get('voice')
            if not voice:
                return
                
            await voice.initialize_with_client(self.client)
            
            # Wait for connection to stabilize
            await asyncio.sleep(3)
            
            # Auto-join #General voice channel
            for guild in self.client.guilds:
                try:
                    # Clean up any existing connections first
                    if guild.voice_client:
                        logger.info(f"Cleaning up existing voice connection in {guild.name}...")
                        try:
                            await guild.voice_client.disconnect(force=True)
                        except:
                            pass  # Ignore errors on cleanup
                        await asyncio.sleep(1)
                    
                    # Find and join General channel
                    for channel in guild.voice_channels:
                        if channel.name.lower() == 'general':
                            logger.info(f"Attempting to join #{channel.name}...")
                            
                            success = await voice.join_channel(guild.id, channel.name)
                            if success:
                                announcer.announce(
                                    "PolymorphicDiscordBridge",
                                    [f"Auto-joined #{channel.name} in {guild.name}"]
                                )
                                # Don't block with TTS on startup
                                asyncio.create_task(voice.speak(
                                    guild.id,
                                    "Claude has connected to the General voice channel"
                                ))
                            break
                except Exception as e:
                    logger.error(f"Error joining voice in {guild.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing voice: {e}")
            announcer.announce(
                "PolymorphicDiscordBridge",
                [f"Voice initialization error: {e}"]
            )
    
    def setup_handlers(self):
        """Setup Discord event handlers"""
        
        @self.client.event
        async def on_ready():
            """When bot connects"""
            announcer.announce(
                "PolymorphicDiscordBridge",
                [f"Connected as {self.client.user}"]
            )
            logger.info(f"✅ Connected as {self.client.user}")
            logger.info(f"📡 Connected to {len(self.client.guilds)} guilds")
            
            # Voice auto-join disabled - use !voice-check to diagnose issues
            logger.info("Voice auto-join disabled. Use !join to connect, !voice-check to diagnose.")
        
        @self.client.event
        async def on_message(message: discord.Message):
            """Handle messages polymorphically"""
            
            # Skip bot messages
            if message.author.bot:
                return
            
            content = message.content.strip()
            if not content:
                return
            
            announcer.announce(
                "PolymorphicDiscordBridge",
                [f"Message from {message.author}: {content[:50]}..."]
            )
            
            # Voice simulation commands
            if content.lower().startswith('!voice '):
                # Simulate voice input through voice receiver
                if 'voice_receiver' in self.capabilities:
                    voice_receiver = self.capabilities['voice_receiver']
                    voice_text = content[7:].strip()
                    voice_receiver.simulate_voice_received(
                        message.author.id,
                        message.guild.id if hasattr(message, 'guild') else 0,
                        voice_text
                    )
                    await message.channel.send("🎤 Voice command processed")
                return
            
            # Check voice state command
            if content.lower() == '!voice-check':
                guild = message.guild
                if guild:
                    bot_member = guild.get_member(self.client.user.id)
                    response = "**Voice State Check:**\n"
                    
                    if bot_member and bot_member.voice:
                        response += f"⚠️ Bot shows as in voice channel: **{bot_member.voice.channel.name}**\n"
                        response += f"  - Channel ID: {bot_member.voice.channel.id}\n"
                        response += f"  - Muted: {bot_member.voice.self_mute}\n"
                        response += f"  - Deafened: {bot_member.voice.self_deaf}\n"
                        response += "\nAttempting to force disconnect..."
                        await message.channel.send(response)
                        
                        # Try to force disconnect
                        try:
                            await bot_member.move_to(None)
                            await message.channel.send("✅ Successfully disconnected from voice!")
                        except Exception as e:
                            await message.channel.send(f"❌ Failed to disconnect: {e}")
                    else:
                        response += "✅ Bot is NOT in any voice channel\n"
                    
                    if guild.voice_client:
                        response += f"⚠️ Voice client exists (connected: {guild.voice_client.is_connected()})\n"
                        try:
                            await guild.voice_client.disconnect(force=True)
                            response += "✅ Voice client disconnected\n"
                        except Exception as e:
                            response += f"❌ Failed to disconnect voice client: {e}\n"
                    else:
                        response += "✅ No voice client exists\n"
                    
                    await message.channel.send(response)
                return
            
            # Voice commands (if voice available)
            if 'voice' in self.capabilities and content.lower().startswith(('!join', '!leave', '!say')):
                voice = self.capabilities['voice']
                
                if content.lower() == '!join':
                    if hasattr(message, 'guild') and message.guild:
                        # Try to join user's channel
                        success = await voice.join_user_channel(
                            message.guild.id,
                            message.author.id
                        )
                        if success:
                            await message.channel.send("🎤 Joined your voice channel!")
                        else:
                            # Try to join #General
                            success = await voice.join_channel(message.guild.id, "General")
                            if success:
                                await message.channel.send("🎤 Joined #General voice channel!")
                            else:
                                await message.channel.send("❌ Could not join voice channel")
                
                elif content.lower() == '!leave':
                    if hasattr(message, 'guild') and message.guild:
                        success = await voice.leave_channel(message.guild.id)
                        if success:
                            await message.channel.send("👋 Left voice channel")
                        else:
                            await message.channel.send("❌ Not in a voice channel")
                
                elif content.lower().startswith('!say '):
                    text = content[5:].strip()
                    if hasattr(message, 'guild') and message.guild:
                        success = await voice.speak(message.guild.id, text)
                        if success:
                            await message.channel.send(f"🎙️ Said: {text}")
                        else:
                            await message.channel.send("❌ Not connected to voice")
                return
            
            # Claude handling (if available)
            if 'claude' in self.capabilities:
                # Lazy initialize Claude service on first use
                if self.capabilities['claude'] == 'lazy':
                    self.capabilities['claude'] = self._claude_class()
                    announcer.announce("PolymorphicDiscordBridge", ["Claude service initialized on first use"])
                
                claude = self.capabilities['claude']
                try:
                    response = await claude.ask_claude_async(content)
                    if response:
                        # Send response (handle long messages)
                        if len(response) > 2000:
                            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                            for chunk in chunks:
                                await message.channel.send(f"```\n{chunk}\n```")
                        else:
                            await message.channel.send(f"```\n{response}\n```")
                    else:
                        await message.channel.send("No response from Claude")
                except Exception as e:
                    logger.error(f"Claude error: {e}")
                    # Fall through to query handler
            
            # Query handling (if available and Claude didn't handle)
            elif 'query' in self.capabilities:
                query = self.capabilities['query']
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, query, content)
                    
                    if result:
                        # Send formatted response
                        if len(result) > 2000:
                            chunks = [result[i:i+1900] for i in range(0, len(result), 1900)]
                            for chunk in chunks:
                                await message.channel.send(f"```\n{chunk}\n```")
                        else:
                            await message.channel.send(f"```\n{result}\n```")
                    else:
                        await message.channel.send("No results found")
                except Exception as e:
                    logger.error(f"Query error: {e}")
                    await message.channel.send(f"Error: {str(e)[:200]}")
            
            # No handler available
            else:
                await message.channel.send(
                    "I'm connected but have no query capabilities available. "
                    "Try voice commands: !join, !leave, !say <text>"
                )
        
        @self.client.event
        async def on_voice_state_update(member, before, after):
            """Track voice state changes"""
            if 'voice' not in self.capabilities:
                return
            
            if member == self.client.user:
                return
            
            # Someone joined a channel with the bot
            if after.channel and self.client.user in after.channel.members:
                if before.channel != after.channel:
                    announcer.announce(
                        "PolymorphicDiscordBridge",
                        [f"{member.name} joined voice channel"]
                    )
                    
                    # Greet them
                    voice = self.capabilities['voice']
                    for guild in self.client.guilds:
                        if after.channel.guild == guild:
                            await voice.speak(
                                guild.id,
                                f"Welcome {member.name} to the voice channel!"
                            )
                            break
    
    async def shutdown(self):
        """Gracefully shutdown the bridge"""
        announcer.announce(
            "PolymorphicDiscordBridge",
            ["Shutting down Discord bridge..."]
        )
        
        try:
            # Disconnect from all voice channels
            for guild in self.client.guilds:
                if guild.voice_client:
                    try:
                        await guild.voice_client.disconnect(force=True)
                    except:
                        pass  # Ignore errors during shutdown
            
            # Also clean up via voice service if available
            if 'voice' in self.capabilities:
                voice = self.capabilities['voice']
                try:
                    status = voice.get_status()
                    for guild_id in list(status['connections'].keys()):
                        try:
                            # Quick goodbye without blocking
                            asyncio.create_task(voice.speak(guild_id, "Goodbye!"))
                        except:
                            pass
                        try:
                            await voice.leave_channel(guild_id)
                        except:
                            pass
                except:
                    pass  # Ignore errors during cleanup
        except Exception as e:
            logger.error(f"Error during voice cleanup: {e}")
        
        # Close Discord client
        if self.client:
            try:
                await self.client.close()
            except:
                pass
            
        logger.info("✅ Discord bridge shut down gracefully")
    
    async def run(self):
        """Run the bridge"""
        announcer.announce("PolymorphicDiscordBridge", ["Starting Discord bridge..."])
        logger.info("🚀 Starting Polymorphic Discord Bridge...")
        logger.info(f"📦 Available capabilities: {list(self.capabilities.keys())}")
        
        try:
            await self.client.start(self.token)
        except discord.LoginFailure:
            logger.error("❌ Invalid Discord token!")
        except Exception as e:
            logger.error(f"❌ Error: {e}")


def main():
    """Main entry point"""
    bridge = PolymorphicDiscordBridge()
    
    try:
        asyncio.run(bridge.run())
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down...")


if __name__ == "__main__":
    main()