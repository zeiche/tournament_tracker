"""
discord_command_registry.py - Pythonic command handling for Discord bot
Replaces massive if-elif chains with command registry pattern
"""
from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re
import discord

from database import session_scope
from database_service import database_service
from tournament_models import Tournament, Organization, Player


class CommandType(Enum):
    """Types of Discord commands"""
    GREETING = "greeting"
    FAREWELL = "farewell"
    STATS = "stats"
    RANKING = "ranking"
    SEARCH = "search"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class CommandContext:
    """Context for command execution"""
    message: discord.Message
    content: str
    content_lower: str
    args: list
    
    @property
    def author(self):
        return self.message.author
    
    @property
    def channel(self):
        return self.message.channel


class CommandRegistry:
    """Registry pattern for Discord commands - No more if-elif chains!"""
    
    def __init__(self):
        self._commands: Dict[str, Callable] = {}
        self._patterns: Dict[re.Pattern, Callable] = {}
        self._register_default_commands()
    
    def command(self, *triggers: str):
        """Decorator to register a command with trigger words"""
        def decorator(func: Callable):
            for trigger in triggers:
                self._commands[trigger.lower()] = func
            return func
        return decorator
    
    def pattern(self, pattern: str):
        """Decorator to register a command with regex pattern"""
        def decorator(func: Callable):
            self._patterns[re.compile(pattern, re.IGNORECASE)] = func
            return func
        return decorator
    
    async def execute(self, message: discord.Message) -> Optional[Any]:
        """Execute the appropriate command based on message"""
        content = message.content
        content_lower = content.lower()
        args = content.split()
        
        ctx = CommandContext(
            message=message,
            content=content,
            content_lower=content_lower,
            args=args
        )
        
        # Check exact commands first
        first_word = args[0].lower() if args else ""
        if first_word in self._commands:
            return await self._commands[first_word](ctx)
        
        # Check patterns
        for pattern, handler in self._patterns.items():
            if pattern.search(content):
                return await handler(ctx)
        
        # Default to help
        return await self.help_command(ctx)
    
    def _register_default_commands(self):
        """Register default commands"""
        
        @self.command('hello', 'hi', 'hey', 'greetings', 'yo', 'sup')
        async def greeting(ctx: CommandContext):
            """Handle greetings"""
            greetings = [
                f"Hey {ctx.author.mention}! Ready to talk tournaments?",
                f"Hello {ctx.author.mention}! What tournament info do you need?",
                f"Hi there {ctx.author.mention}! Ask me about SoCal FGC tournaments!"
            ]
            import random
            await ctx.channel.send(random.choice(greetings))
        
        @self.command('bye', 'goodbye', 'later', 'farewell', 'cya')
        async def farewell(ctx: CommandContext):
            """Handle farewells"""
            farewells = [
                f"See you later {ctx.author.mention}! Keep grinding!",
                f"Goodbye {ctx.author.mention}! Good luck in your next tournament!",
                f"Later {ctx.author.mention}! Stay tournament ready!"
            ]
            import random
            await ctx.channel.send(random.choice(farewells))
        
        @self.pattern(r'(stats|statistics|summary|total)')
        async def stats_command(ctx: CommandContext):
            """Show statistics"""
            stats = database_service.get_summary_stats()
            
            embed = discord.Embed(
                title="Tournament Tracker Statistics",
                color=discord.Color.green()
            )
            embed.add_field(name="Organizations", value=stats.total_organizations)
            embed.add_field(name="Tournaments", value=stats.total_tournaments)
            embed.add_field(name="Players", value=stats.total_players)
            
            await ctx.channel.send(embed=embed)
        
        @self.pattern(r'top\s*(\d+)?|ranking|leaderboard')
        async def rankings_command(ctx: CommandContext):
            """Show rankings"""
            # Extract number from message
            numbers = re.findall(r'\d+', ctx.content)
            limit = int(numbers[0]) if numbers else 10
            limit = min(limit, 50)
            
            rankings = database_service.get_attendance_rankings(limit)
            
            if not rankings:
                await ctx.channel.send("No attendance data available yet.")
                return
            
            embed = discord.Embed(
                title=f"Top {len(rankings)} Organizations by Attendance",
                color=discord.Color.blue()
            )
            
            ranking_text = ""
            for i, org in enumerate(rankings, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                ranking_text += f"{emoji} **{org['display_name']}**\n"
                ranking_text += f"   Events: {org.get('tournament_count', 0)} | "
                ranking_text += f"Attendance: {org.get('total_attendance', 0):,}\n\n"
            
            embed.description = ranking_text
            embed.set_footer(text=f"Requested by {ctx.author}")
            
            await ctx.channel.send(embed=embed)
        
        @self.pattern(r'tournament.*?(\w+)|search\s+(\w+)|find\s+(\w+)')
        async def search_tournament(ctx: CommandContext):
            """Search for tournaments"""
            # Extract search term
            search_term = ctx.args[1] if len(ctx.args) > 1 else None
            
            if not search_term:
                await ctx.channel.send("Please specify what to search for.")
                return
            
            with session_scope() as session:
                tournaments = session.query(Tournament).filter(
                    Tournament.name.ilike(f'%{search_term}%')
                ).limit(5).all()
                
                if not tournaments:
                    await ctx.channel.send(f"No tournaments found matching '{search_term}'")
                    return
                
                embed = discord.Embed(
                    title=f"Tournaments matching '{search_term}'",
                    color=discord.Color.purple()
                )
                
                for t in tournaments:
                    embed.add_field(
                        name=t.name,
                        value=f"Date: {t.start_date}\nAttendees: {t.num_attendees}",
                        inline=False
                    )
                
                await ctx.channel.send(embed=embed)
        
        @self.command('help', '?', 'commands')
        async def help_command(ctx: CommandContext):
            """Show help"""
            embed = discord.Embed(
                title="Tournament Tracker Bot Commands",
                description="Here's what I can do:",
                color=discord.Color.gold()
            )
            
            commands = {
                "Greetings": "Say hello, hi, hey, etc.",
                "Statistics": "Ask for 'stats' or 'summary'",
                "Rankings": "Ask for 'top 10' or 'rankings'",
                "Search": "Search for tournaments: 'search <name>'",
                "Help": "Type 'help' or '?'"
            }
            
            for name, desc in commands.items():
                embed.add_field(name=name, value=desc, inline=False)
            
            await ctx.channel.send(embed=embed)
    
    async def help_command(self, ctx: CommandContext):
        """Default help command"""
        embed = discord.Embed(
            title="I didn't understand that",
            description="Try asking about rankings, stats, or searching for tournaments!",
            color=discord.Color.orange()
        )
        await ctx.channel.send(embed=embed)


# Global registry instance
discord_commands = CommandRegistry()