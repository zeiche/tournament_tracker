#!/usr/bin/env python3
"""
discord_service.py - SINGLE SOURCE OF TRUTH for Discord Bot
This is the ONLY place where Discord client and bot operations should be managed.
All Discord functionality MUST go through this service.
"""
import discord
import asyncio
import os
import sys
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

# Use the single database entry point
from database import session_scope, get_session
# Use the unified Claude AI service
import sys
sys.path.insert(0, '/home/ubuntu/claude')
from claude_ai_service import claude_ai, process_message_async


class BotMode(Enum):
    """Discord bot operation modes"""
    SIMPLE = "simple"           # Basic greetings and responses
    CONVERSATIONAL = "conversational"  # Tournament data queries
    CLAUDE_ENHANCED = "claude"  # Claude-powered responses
    HYBRID = "hybrid"           # Mix of all modes


@dataclass
class DiscordConfig:
    """Configuration for Discord service"""
    token: Optional[str] = None
    bot_name: str = "Tournament Tracker Bot"
    mode: BotMode = BotMode.CONVERSATIONAL
    command_prefix: str = "!"
    status_message: str = "Tracking FGC tournaments"
    log_messages: bool = True
    respond_to_mentions: bool = True
    
    def __post_init__(self):
        """Load token from environment if not provided"""
        if not self.token:
            # Try multiple environment variables
            self.token = (
                os.getenv('DISCORD_BOT_TOKEN') or
                os.getenv('DISCORD_TOKEN') or
                self._load_from_env_file()
            )
    
    def _load_from_env_file(self) -> Optional[str]:
        """Load token from .env.discord file"""
        env_files = [
            '/home/ubuntu/claude/.env.discord',
            '/home/ubuntu/claude/tournament_tracker/.env.discord',
            '.env.discord'
        ]
        
        for env_file in env_files:
            if os.path.exists(env_file):
                try:
                    with open(env_file, 'r') as f:
                        for line in f:
                            if line.startswith('DISCORD_BOT_TOKEN='):
                                return line.split('=', 1)[1].strip()
                except Exception:
                    continue
        return None
    
    @property
    def is_enabled(self) -> bool:
        """Check if Discord service is enabled"""
        return bool(self.token)


@dataclass
class MessageContext:
    """Context for processing a Discord message"""
    message: discord.Message
    content_lower: str
    is_mention: bool
    is_command: bool
    command: Optional[str] = None
    args: List[str] = None


class DiscordService:
    """
    SINGLE SOURCE OF TRUTH for all Discord bot operations.
    This is the ONLY service that should create Discord clients or handle bot logic.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern - only ONE Discord service"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[DiscordConfig] = None):
        """Initialize Discord service (only runs once)"""
        if not self._initialized:
            self.config = config or DiscordConfig()
            self.client = None
            self.is_running = False
            
            # Message handlers by mode
            self._handlers = {
                BotMode.SIMPLE: self._handle_simple_message,
                BotMode.CONVERSATIONAL: self._handle_conversational_message,
                BotMode.CLAUDE_ENHANCED: self._handle_claude_message,
                BotMode.HYBRID: self._handle_hybrid_message
            }
            
            # Command handlers
            self._commands = {}
            self._register_default_commands()
            
            # Statistics
            self._stats = {
                'messages_received': 0,
                'messages_responded': 0,
                'commands_processed': 0,
                'errors': 0,
                'start_time': None,
                'guilds_connected': 0
            }
            
            # Setup logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger('discord_service')
            
            DiscordService._initialized = True
            
            if self.config.is_enabled:
                print("✅ Discord service initialized (SINGLE SOURCE OF TRUTH)")
                print(f"   Mode: {self.config.mode.value}")
                print(f"   Bot name: {self.config.bot_name}")
            else:
                print("⚠️  Discord service disabled (no token configured)")
    
    @property
    def is_enabled(self) -> bool:
        """Check if Discord service is enabled"""
        return self.config.is_enabled
    
    def _ensure_enabled(self):
        """Ensure Discord service is enabled"""
        if not self.is_enabled:
            raise RuntimeError(
                "Discord service is not enabled. "
                "Set DISCORD_BOT_TOKEN environment variable or configure token."
            )
    
    def _create_client(self) -> discord.Client:
        """Create Discord client with proper intents - ONLY place this happens"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        client = discord.Client(intents=intents)
        
        # Register event handlers
        @client.event
        async def on_ready():
            await self._on_ready()
        
        @client.event
        async def on_message(message):
            await self._on_message(message)
        
        @client.event
        async def on_guild_join(guild):
            await self._on_guild_join(guild)
        
        @client.event
        async def on_guild_remove(guild):
            await self._on_guild_remove(guild)
        
        return client
    
    # ========================================================================
    # BOT LIFECYCLE MANAGEMENT
    # ========================================================================
    
    async def start(self):
        """Start the Discord bot"""
        self._ensure_enabled()
        
        if self.is_running:
            self.logger.warning("Bot is already running")
            return
        
        self.client = self._create_client()
        self.is_running = True
        self._stats['start_time'] = datetime.now()
        
        try:
            await self.client.start(self.config.token)
        except Exception as e:
            self.is_running = False
            self.logger.error(f"Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the Discord bot"""
        if not self.is_running or not self.client:
            return
        
        self.logger.info("Stopping Discord bot...")
        await self.client.close()
        self.is_running = False
    
    def run_blocking(self):
        """Run the bot in blocking mode (for standalone scripts)"""
        self._ensure_enabled()
        
        if self.is_running:
            raise RuntimeError("Bot is already running")
        
        self.client = self._create_client()
        self.is_running = True
        self._stats['start_time'] = datetime.now()
        
        try:
            self.client.run(self.config.token)
        finally:
            self.is_running = False
    
    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================
    
    async def _on_ready(self):
        """Handle bot ready event"""
        self.logger.info(f"Bot is ready! Logged in as: {self.client.user.name}")
        self._stats['guilds_connected'] = len(self.client.guilds)
        
        # Log connected guilds
        for guild in self.client.guilds:
            self.logger.info(f"  Connected to: {guild.name} ({guild.id})")
        
        # Set status
        await self.client.change_presence(
            activity=discord.Game(name=self.config.status_message),
            status=discord.Status.online
        )
    
    async def _on_message(self, message: discord.Message):
        """Handle incoming message - SINGLE entry point for all messages"""
        # Don't respond to ourselves or other bots
        if message.author == self.client.user or message.author.bot:
            return
        
        self._stats['messages_received'] += 1
        
        # Log message if configured
        if self.config.log_messages:
            self.logger.info(f"[{message.guild}#{message.channel}] {message.author}: {message.content}")
        
        # Create message context
        context = MessageContext(
            message=message,
            content_lower=message.content.lower(),
            is_mention=self.client.user in message.mentions,
            is_command=message.content.startswith(self.config.command_prefix)
        )
        
        # Parse command if present
        if context.is_command:
            parts = message.content[len(self.config.command_prefix):].split()
            if parts:
                context.command = parts[0].lower()
                context.args = parts[1:]
        
        try:
            # Route to appropriate handler based on mode
            handler = self._handlers.get(self.config.mode, self._handle_simple_message)
            await handler(context)
            
        except Exception as e:
            self._stats['errors'] += 1
            self.logger.error(f"Error handling message: {e}")
            await message.channel.send(
                f"Sorry {message.author.mention}, I encountered an error processing your message."
            )
    
    async def _on_guild_join(self, guild: discord.Guild):
        """Handle joining a new guild"""
        self.logger.info(f"Joined new guild: {guild.name} ({guild.id})")
        self._stats['guilds_connected'] += 1
    
    async def _on_guild_remove(self, guild: discord.Guild):
        """Handle removal from a guild"""
        self.logger.info(f"Removed from guild: {guild.name} ({guild.id})")
        self._stats['guilds_connected'] -= 1
    
    # ========================================================================
    # MESSAGE HANDLERS BY MODE
    # ========================================================================
    
    async def _handle_simple_message(self, context: MessageContext):
        """Handle messages in simple mode (basic responses)"""
        message = context.message
        content = context.content_lower
        
        # Greetings
        if any(word in content for word in ['hello', 'hi', 'hey']):
            await message.channel.send(f"Hello {message.author.mention}! 👋")
            self._stats['messages_responded'] += 1
            return
        
        # Respond to mentions
        if context.is_mention and self.config.respond_to_mentions:
            await message.channel.send(
                f"You mentioned me, {message.author.mention}! How can I help?"
            )
            self._stats['messages_responded'] += 1
    
    async def _handle_conversational_message(self, context: MessageContext):
        """Handle messages in conversational mode (tournament queries)"""
        message = context.message
        content = context.content_lower
        
        # Check for tournament-related keywords
        tournament_keywords = [
            'tournament', 'attendance', 'ranking', 'organization',
            'top', 'stats', 'fgc', 'socal', 'leaderboard', 'player'
        ]
        
        if any(keyword in content for keyword in tournament_keywords):
            response = await self._get_tournament_response(content)
            await message.channel.send(response)
            self._stats['messages_responded'] += 1
            return
        
        # Fall back to simple handler
        await self._handle_simple_message(context)
    
    async def _handle_claude_message(self, context: MessageContext):
        """Handle messages using Claude AI - RESTRICTED TO DATABASE ONLY"""
        message = context.message
        
        # Only respond if Claude is enabled and mentioned or in DM
        if not claude_ai.is_enabled:
            await self._handle_conversational_message(context)
            return
        
        if context.is_mention or isinstance(message.channel, discord.DMChannel):
            # Get database context if needed
            db_context = None
            try:
                from enhanced_database_context import EnhancedDatabaseContext
                db_context = EnhancedDatabaseContext.get_comprehensive_context(message.content)
            except:
                pass
            
            # Use the unified AI service
            ai_context = {
                'discord_user': str(message.author),
                'channel': str(message.channel),
                'database_info': db_context.get('database_info') if db_context else None
            }
            
            # Process through unified AI service
            result = await process_message_async(message.content, ai_context)
            
            if result['success']:
                # Handle different response types
                if result.get('metadata') and result['metadata'].get('code'):
                    # Execute code if returned
                    try:
                        with session_scope() as session:
                            from tournament_models import Tournament, Organization, Player, TournamentPlacement
                            from sqlalchemy import func
                            from datetime import datetime, timedelta
                            
                            exec_globals = {
                                'session': session,
                                'Player': Player,
                                'Tournament': Tournament,
                                'TournamentPlacement': TournamentPlacement,
                                'Organization': Organization,
                                'func': func,
                                'datetime': datetime,
                                'timedelta': timedelta,
                                'output': None
                            }
                            
                            exec(result['metadata']['code'], exec_globals)
                            output = exec_globals.get('output', 'Query executed successfully')
                            await message.channel.send(str(output)[:2000])
                    except Exception as e:
                        await message.channel.send(f"Error executing query: {str(e)[:100]}")
                else:
                    # Send text response
                    await message.channel.send(result['response'][:2000])  # Discord message limit
            else:
                await message.channel.send(f"Sorry, I couldn't process that: {result.get('error', 'Unknown error')}")
            
            self._stats['messages_responded'] += 1
    
    async def _handle_hybrid_message(self, context: MessageContext):
        """Handle messages using all available modes"""
        message = context.message
        content = context.content_lower
        
        # Commands have priority
        if context.is_command:
            await self._handle_command(context)
            return
        
        # Tournament queries
        tournament_keywords = ['tournament', 'ranking', 'organization', 'player']
        if any(keyword in content for keyword in tournament_keywords):
            await self._handle_conversational_message(context)
            return
        
        # Claude for complex questions or mentions
        if context.is_mention and claude_ai.is_enabled:
            await self._handle_claude_message(context)
            return
        
        # Fall back to simple
        await self._handle_simple_message(context)
    
    # ========================================================================
    # TOURNAMENT DATA QUERIES
    # ========================================================================
    
    async def _get_tournament_response(self, query: str) -> str:
        """Get tournament data response for a query"""
        with session_scope() as session:
            # Check for specific queries
            if 'top' in query and 'organization' in query:
                from tournament_models import Organization, Tournament
                from sqlalchemy import func
                
                # Get top organizations
                results = session.query(
                    Organization.display_name,
                    func.count(Tournament.id).label('count'),
                    func.sum(Tournament.num_attendees).label('total')
                ).join(
                    Tournament,
                    Organization.normalized_key == Tournament.normalized_contact
                ).group_by(
                    Organization.id
                ).order_by(
                    func.sum(Tournament.num_attendees).desc()
                ).limit(10).all()
                
                if results:
                    response = "**Top 10 Organizations by Attendance:**\n"
                    for i, (name, count, total) in enumerate(results, 1):
                        response += f"{i}. {name}: {total or 0} total attendance ({count} tournaments)\n"
                    return response
                else:
                    return "No organization data available."
            
            elif 'stats' in query or 'statistic' in query:
                from tournament_models import Tournament, Organization, Player
                
                t_count = session.query(Tournament).count()
                o_count = session.query(Organization).count()
                p_count = session.query(Player).count()
                
                return (
                    f"**Tournament Tracker Statistics:**\n"
                    f"• Tournaments tracked: {t_count}\n"
                    f"• Organizations: {o_count}\n"
                    f"• Players: {p_count}"
                )
            
            else:
                return (
                    "I can help with tournament data! Try asking:\n"
                    "• 'show top organizations'\n"
                    "• 'tournament statistics'\n"
                    "• 'player rankings'"
                )
    
    # ========================================================================
    # COMMAND SYSTEM
    # ========================================================================
    
    def register_command(self, name: str, handler: Callable, description: str = ""):
        """Register a command handler"""
        self._commands[name.lower()] = {
            'handler': handler,
            'description': description
        }
    
    def _register_default_commands(self):
        """Register default commands"""
        self.register_command('help', self._cmd_help, "Show available commands")
        self.register_command('stats', self._cmd_stats, "Show bot statistics")
        self.register_command('mode', self._cmd_mode, "Change bot mode")
    
    async def _handle_command(self, context: MessageContext):
        """Handle command execution"""
        if not context.command:
            return
        
        command_info = self._commands.get(context.command)
        if command_info:
            self._stats['commands_processed'] += 1
            await command_info['handler'](context)
        else:
            await context.message.channel.send(
                f"Unknown command: `{context.command}`. Use `{self.config.command_prefix}help` for available commands."
            )
    
    async def _cmd_help(self, context: MessageContext):
        """Help command handler"""
        response = f"**Available Commands:**\n"
        for name, info in self._commands.items():
            response += f"`{self.config.command_prefix}{name}` - {info['description']}\n"
        await context.message.channel.send(response)
    
    async def _cmd_stats(self, context: MessageContext):
        """Stats command handler"""
        uptime = (datetime.now() - self._stats['start_time']).total_seconds() if self._stats['start_time'] else 0
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        response = (
            f"**Bot Statistics:**\n"
            f"• Mode: {self.config.mode.value}\n"
            f"• Uptime: {hours}h {minutes}m\n"
            f"• Messages received: {self._stats['messages_received']}\n"
            f"• Messages responded: {self._stats['messages_responded']}\n"
            f"• Commands processed: {self._stats['commands_processed']}\n"
            f"• Guilds connected: {self._stats['guilds_connected']}\n"
            f"• Errors: {self._stats['errors']}"
        )
        await context.message.channel.send(response)
    
    async def _cmd_mode(self, context: MessageContext):
        """Mode command handler"""
        if not context.args:
            await context.message.channel.send(
                f"Current mode: **{self.config.mode.value}**\n"
                f"Available modes: {', '.join(m.value for m in BotMode)}"
            )
            return
        
        try:
            new_mode = BotMode(context.args[0].lower())
            self.config.mode = new_mode
            await context.message.channel.send(f"Bot mode changed to: **{new_mode.value}**")
        except ValueError:
            await context.message.channel.send(
                f"Invalid mode. Available modes: {', '.join(m.value for m in BotMode)}"
            )
    
    # ========================================================================
    # STATISTICS AND MONITORING
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Discord service statistics"""
        return {
            'enabled': self.is_enabled,
            'running': self.is_running,
            'config': {
                'bot_name': self.config.bot_name,
                'mode': self.config.mode.value,
                'command_prefix': self.config.command_prefix
            },
            'stats': self._stats.copy()
        }
    
    def reset_statistics(self):
        """Reset statistics counters"""
        self._stats['messages_received'] = 0
        self._stats['messages_responded'] = 0
        self._stats['commands_processed'] = 0
        self._stats['errors'] = 0


# ============================================================================
# GLOBAL INSTANCE - The ONE and ONLY Discord service
# ============================================================================

discord_service = DiscordService()


# ============================================================================
# CONVENIENCE FUNCTIONS - These all go through the single service
# ============================================================================

def start_discord_bot(mode: Optional[str] = None):
    """Start the Discord bot"""
    if mode:
        try:
            discord_service.config.mode = BotMode(mode)
        except ValueError:
            print(f"Invalid mode: {mode}")
            return False
    
    if not discord_service.is_enabled:
        print("Discord bot is not enabled (no token configured)")
        return False
    
    print(f"Starting Discord bot in {discord_service.config.mode.value} mode...")
    discord_service.run_blocking()
    return True


def get_discord_stats() -> Dict[str, Any]:
    """Get Discord bot statistics"""
    return discord_service.get_statistics()


def is_discord_enabled() -> bool:
    """Check if Discord bot is enabled"""
    return discord_service.is_enabled


# ============================================================================
# MAIN - Run the bot if called directly
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Discord Bot Service (SINGLE SOURCE OF TRUTH)')
    parser.add_argument('--mode', choices=['simple', 'conversational', 'claude', 'hybrid'],
                       default='conversational', help='Bot operation mode')
    parser.add_argument('--token', help='Discord bot token (or use DISCORD_BOT_TOKEN env)')
    parser.add_argument('--stats', action='store_true', help='Show statistics and exit')
    
    args = parser.parse_args()
    
    if args.stats:
        stats = get_discord_stats()
        print("Discord Service Statistics:")
        print(f"  Enabled: {stats['enabled']}")
        print(f"  Running: {stats['running']}")
        print(f"  Mode: {stats['config']['mode']}")
        sys.exit(0)
    
    if args.token:
        discord_service.config.token = args.token
    
    # Start the bot
    if not start_discord_bot(args.mode):
        sys.exit(1)