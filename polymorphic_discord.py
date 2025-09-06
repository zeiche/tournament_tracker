#!/usr/bin/env python3
"""
polymorphic_discord.py - TRULY polymorphic Discord sender

Sends ANYTHING to ANYWHERE in Discord!
- Any content type (text, images, files, embeds, reactions, etc.)
- Any destination (DM, channel, thread, forum, voice text)
- Figures out what to do based on what you give it

TRUE POLYMORPHISM: It doesn't care what you're sending or where!
"""
import os
import discord
import asyncio
import logging
from typing import Any, Union, Optional, List
from pathlib import Path
import io
import json
import pickle
from datetime import datetime

# Import our generators
from polymorphic_image_generator import heatmap
from polymorphic_bitmap_layers import PolymorphicBitmapLayers
from polymorphic_tabulator import tabulate
from database import get_session
from tournament_models import Tournament, Player, Organization

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolymorphicDiscord:
    """
    The TRULY polymorphic Discord handler.
    Give it ANYTHING and ANY destination - it figures out how to send it!
    """
    
    def __init__(self):
        self.client = None
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        self.ready = False
        
    async def start(self):
        """Initialize Discord client with all capabilities"""
        if not self.token:
            logger.error("No Discord token")
            return False
        
        # Enable necessary intents
        intents = discord.Intents.default()
        intents.message_content = True  # To read message content
        intents.dm_messages = True      # To handle DMs
        self.client = discord.Client(intents=intents)
        
        @self.client.event
        async def on_ready():
            self.ready = True
            logger.info(f'Polymorphic Discord ready as {self.client.user}')
            print(f"✅ POLYMORPHIC DISCORD READY!")
            print("I can send ANYTHING to ANYWHERE!")
            print("\nCommands:")
            print("  !send <destination> <content>")
            print("  !broadcast <content> - Send to all channels")
            print("  !dm everyone <content> - DM all users")
            print("  !show <what> in <where> - Natural language")
        
        @self.client.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return
            
            content = message.content.strip()
            
            # Polymorphic send command
            if content.startswith('!send'):
                await self.handle_polymorphic_send(message)
            
            # Broadcast to all channels
            elif content.startswith('!broadcast'):
                await self.handle_broadcast(message)
            
            # Natural language sending
            elif 'send' in content.lower() or 'show' in content.lower() or 'dm' in content.lower():
                await self.handle_natural_language(message)
            
            # Generate and send anything
            elif content.startswith('!generate'):
                await self.handle_generate(message)
    
    async def send_anything_anywhere(self, 
                                    content: Any, 
                                    destination: Any,
                                    context: Optional[discord.Message] = None) -> bool:
        """
        THE CORE POLYMORPHIC METHOD!
        Send ANYTHING to ANYWHERE in Discord.
        
        Args:
            content: LITERALLY ANYTHING - string, image, object, list, database model, etc.
            destination: LITERALLY ANYWHERE - channel, user, guild, role, thread, etc.
            context: Optional message for context
            
        Returns:
            Success boolean
        """
        try:
            # Figure out the destination
            target = await self._resolve_destination(destination, context)
            if not target:
                logger.error(f"Could not resolve destination: {destination}")
                return False
            
            # Figure out what to send
            to_send = await self._prepare_content(content)
            
            # Send it!
            return await self._send_to_target(to_send, target)
            
        except Exception as e:
            logger.error(f"Error in polymorphic send: {e}")
            return False
    
    async def _resolve_destination(self, destination: Any, context: Optional[discord.Message] = None) -> Any:
        """Figure out where to send - accepts ANYTHING"""
        
        # Already a sendable Discord object
        if hasattr(destination, 'send'):
            return destination
        
        # Discord User
        if isinstance(destination, discord.User) or isinstance(destination, discord.Member):
            return await destination.create_dm()
        
        # String destination
        if isinstance(destination, str):
            dest_lower = destination.lower()
            
            # "here" means current channel
            if dest_lower == "here" and context:
                return context.channel
            
            # "dm" or "@username" means DM
            if dest_lower.startswith("dm ") or dest_lower.startswith("@"):
                username = dest_lower.replace("dm ", "").replace("@", "").strip()
                # Find user
                for guild in self.client.guilds:
                    for member in guild.members:
                        if username.lower() in member.name.lower() or \
                           username.lower() in str(member.nick).lower():
                            return await member.create_dm()
            
            # "#channel" means channel
            if dest_lower.startswith("#"):
                channel_name = dest_lower[1:]
                for guild in self.client.guilds:
                    for channel in guild.text_channels:
                        if channel_name in channel.name.lower():
                            return channel
            
            # "all" or "everyone" means all channels
            if dest_lower in ["all", "everyone", "broadcast"]:
                return "BROADCAST"  # Special marker
            
            # Try to find channel by name
            for guild in self.client.guilds:
                for channel in guild.text_channels:
                    if destination.lower() in channel.name.lower():
                        return channel
        
        # Channel ID
        if isinstance(destination, int):
            channel = self.client.get_channel(destination)
            if channel:
                return channel
        
        # List of destinations (send to multiple)
        if isinstance(destination, list):
            return ["MULTI", [await self._resolve_destination(d, context) for d in destination]]
        
        # Default to context channel if available
        if context:
            return context.channel
        
        return None
    
    async def _prepare_content(self, content: Any) -> dict:
        """
        Prepare ANY content for sending.
        Returns dict with 'type' and prepared content.
        """
        prepared = {'type': None, 'content': None, 'embed': None, 'file': None}
        
        # String content
        if isinstance(content, str):
            # Check if it's a file path
            if os.path.exists(content):
                return await self._prepare_file(content)
            else:
                prepared['type'] = 'text'
                prepared['content'] = content
                return prepared
        
        # Discord Embed
        if isinstance(content, discord.Embed):
            prepared['type'] = 'embed'
            prepared['embed'] = content
            return prepared
        
        # Discord File
        if isinstance(content, discord.File):
            prepared['type'] = 'file'
            prepared['file'] = content
            return prepared
        
        # PIL Image
        if hasattr(content, 'save') and hasattr(content, 'mode'):  # PIL Image
            buffer = io.BytesIO()
            content.save(buffer, format='PNG')
            buffer.seek(0)
            prepared['type'] = 'file'
            prepared['file'] = discord.File(buffer, filename='image.png')
            return prepared
        
        # Bytes (raw image data)
        if isinstance(content, bytes):
            prepared['type'] = 'file'
            prepared['file'] = discord.File(io.BytesIO(content), filename='data.bin')
            return prepared
        
        # Path object
        if isinstance(content, Path):
            return await self._prepare_file(str(content))
        
        # Dictionary - create embed
        if isinstance(content, dict):
            if 'embed' in content:
                prepared['embed'] = content['embed']
            if 'file' in content:
                prepared['file'] = content['file']
            if 'content' in content:
                prepared['content'] = content['content']
            
            # Auto-create embed from dict
            if not prepared['embed'] and not prepared['file']:
                embed = discord.Embed(
                    title=content.get('title', 'Data'),
                    description=content.get('description', ''),
                    color=content.get('color', discord.Color.blue())
                )
                for key, value in content.items():
                    if key not in ['title', 'description', 'color']:
                        embed.add_field(name=key, value=str(value)[:1024], inline=True)
                prepared['embed'] = embed
            
            prepared['type'] = 'mixed'
            return prepared
        
        # List - send multiple items or create list embed
        if isinstance(content, list):
            if len(content) == 1:
                return await self._prepare_content(content[0])
            
            # Create embed with list
            embed = discord.Embed(
                title="List Data",
                description=f"{len(content)} items",
                color=discord.Color.green()
            )
            for i, item in enumerate(content[:25]):  # Discord field limit
                embed.add_field(
                    name=f"Item {i+1}",
                    value=str(item)[:1024],
                    inline=True
                )
            prepared['type'] = 'embed'
            prepared['embed'] = embed
            return prepared
        
        # Database models (Tournament, Player, etc.)
        if hasattr(content, '__tablename__'):
            return await self._prepare_database_model(content)
        
        # Tuple (might be ranked data from tabulator)
        if isinstance(content, tuple) and len(content) == 3:
            rank, item, score = content
            embed = discord.Embed(
                title=f"Rank #{rank}",
                description=str(item),
                color=discord.Color.gold()
            )
            embed.add_field(name="Score", value=str(score))
            prepared['type'] = 'embed'
            prepared['embed'] = embed
            return prepared
        
        # Function - call it and send result
        if callable(content):
            result = content()
            if asyncio.iscoroutine(result):
                result = await result
            return await self._prepare_content(result)
        
        # Numpy array or matplotlib figure
        if hasattr(content, 'shape') or hasattr(content, 'savefig'):
            return await self._prepare_scientific_content(content)
        
        # Default: convert to string
        prepared['type'] = 'text'
        prepared['content'] = str(content)
        return prepared
    
    async def _prepare_file(self, filepath: str) -> dict:
        """Prepare a file for sending"""
        prepared = {'type': 'file', 'content': None, 'embed': None, 'file': None}
        
        if not os.path.exists(filepath):
            prepared['type'] = 'text'
            prepared['content'] = f"File not found: {filepath}"
            return prepared
        
        # Determine file type and create appropriate embed
        ext = os.path.splitext(filepath)[1].lower()
        filename = os.path.basename(filepath)
        
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            # Image file
            embed = discord.Embed(
                title="Image",
                color=discord.Color.blue()
            )
            embed.set_image(url=f"attachment://{filename}")
            prepared['embed'] = embed
        elif ext in ['.txt', '.md', '.log']:
            # Text file - read and send content
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    if len(content) < 2000:
                        prepared['content'] = f"```\n{content}\n```"
                    else:
                        prepared['content'] = f"File: {filename}"
            except:
                pass
        
        # Attach the file
        prepared['file'] = discord.File(filepath, filename=filename)
        return prepared
    
    async def _prepare_database_model(self, model: Any) -> dict:
        """Prepare a database model for sending"""
        prepared = {'type': 'embed', 'content': None, 'embed': None, 'file': None}
        
        model_type = model.__class__.__name__
        
        # Create appropriate embed based on model type
        if model_type == "Tournament":
            embed = discord.Embed(
                title=f"🏆 {model.name}",
                description=f"Tournament at {model.venue_name or 'Unknown'}",
                color=discord.Color.red()
            )
            embed.add_field(name="Attendees", value=str(model.num_attendees or 0))
            embed.add_field(name="Date", value=str(datetime.fromtimestamp(model.start_at) if model.start_at else "Unknown"))
            if model.lat and model.lng:
                embed.add_field(name="Location", value=f"{model.lat}, {model.lng}")
            
        elif model_type == "Player":
            wins = sum(1 for p in model.placements if p.placement == 1)
            events = len(model.placements)
            
            embed = discord.Embed(
                title=f"🎮 {model.gamer_tag}",
                description=model.name or "Player",
                color=discord.Color.green()
            )
            embed.add_field(name="Events", value=str(events))
            embed.add_field(name="Wins", value=str(wins))
            embed.add_field(name="Win Rate", value=f"{(wins/events*100):.1f}%" if events > 0 else "0%")
            
        elif model_type == "Organization":
            embed = discord.Embed(
                title=f"🏢 {model.display_name}",
                description="Tournament Organizer",
                color=discord.Color.purple()
            )
            embed.add_field(name="ID", value=str(model.id))
            
        else:
            # Generic model
            embed = discord.Embed(
                title=model_type,
                description=str(model),
                color=discord.Color.blurple()
            )
        
        prepared['embed'] = embed
        return prepared
    
    async def _prepare_scientific_content(self, content: Any) -> dict:
        """Prepare numpy arrays, matplotlib figures, etc."""
        prepared = {'type': 'file', 'content': None, 'embed': None, 'file': None}
        
        try:
            import io
            import matplotlib.pyplot as plt
            
            # Matplotlib figure
            if hasattr(content, 'savefig'):
                buffer = io.BytesIO()
                content.savefig(buffer, format='png')
                buffer.seek(0)
                prepared['file'] = discord.File(buffer, filename='plot.png')
                
                embed = discord.Embed(title="Plot", color=discord.Color.blue())
                embed.set_image(url="attachment://plot.png")
                prepared['embed'] = embed
                
            # Numpy array - create simple visualization
            elif hasattr(content, 'shape'):
                fig, ax = plt.subplots()
                if len(content.shape) == 2:
                    ax.imshow(content)
                else:
                    ax.plot(content)
                
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png')
                buffer.seek(0)
                plt.close(fig)
                
                prepared['file'] = discord.File(buffer, filename='array.png')
                embed = discord.Embed(title="Array Visualization", color=discord.Color.blue())
                embed.set_image(url="attachment://array.png")
                prepared['embed'] = embed
                
        except Exception as e:
            logger.error(f"Error preparing scientific content: {e}")
            prepared['type'] = 'text'
            prepared['content'] = f"Data shape: {content.shape if hasattr(content, 'shape') else 'Unknown'}"
        
        return prepared
    
    async def _send_to_target(self, prepared: dict, target: Any) -> bool:
        """Send prepared content to target"""
        try:
            # Handle broadcast
            if target == "BROADCAST":
                success = True
                for guild in self.client.guilds:
                    for channel in guild.text_channels:
                        try:
                            await self._send_single(prepared, channel)
                        except:
                            success = False
                return success
            
            # Handle multiple targets
            if isinstance(target, list) and target[0] == "MULTI":
                success = True
                for t in target[1]:
                    if t:
                        try:
                            await self._send_single(prepared, t)
                        except:
                            success = False
                return success
            
            # Single target
            return await self._send_single(prepared, target)
            
        except Exception as e:
            logger.error(f"Error sending to target: {e}")
            return False
    
    async def _send_single(self, prepared: dict, target: Any) -> bool:
        """Send to a single target"""
        kwargs = {}
        
        if prepared.get('content'):
            kwargs['content'] = prepared['content']
        if prepared.get('embed'):
            kwargs['embed'] = prepared['embed']
        if prepared.get('file'):
            kwargs['file'] = prepared['file']
        
        if not kwargs:
            kwargs['content'] = "Empty message"
        
        await target.send(**kwargs)
        return True
    
    async def handle_polymorphic_send(self, message: discord.Message):
        """Handle !send command"""
        parts = message.content.split(maxsplit=2)
        
        if len(parts) < 3:
            await message.channel.send("Usage: !send <destination> <content>")
            return
        
        destination = parts[1]
        content = parts[2]
        
        # Check if content is a generation request
        if content.startswith("generate"):
            content = await self.generate_content(content)
        
        success = await self.send_anything_anywhere(content, destination, message)
        
        if success:
            await message.add_reaction("✅")
        else:
            await message.add_reaction("❌")
    
    async def handle_broadcast(self, message: discord.Message):
        """Handle broadcast to all channels"""
        content = message.content.replace("!broadcast", "").strip()
        
        if not content:
            await message.channel.send("Usage: !broadcast <content>")
            return
        
        await message.channel.send("📢 Broadcasting to all channels...")
        
        count = 0
        for guild in self.client.guilds:
            for channel in guild.text_channels:
                try:
                    await self.send_anything_anywhere(content, channel, message)
                    count += 1
                except:
                    pass
        
        await message.channel.send(f"✅ Broadcasted to {count} channels!")
    
    async def handle_natural_language(self, message: discord.Message):
        """Handle natural language commands"""
        content = message.content.lower()
        
        # Parse natural language
        # "send heatmap to #general"
        # "dm zeiche a tournament list"
        # "show top players in this channel"
        
        # Extract action, what, and where
        what = None
        where = None
        
        if "heatmap" in content or "heat map" in content:
            what = await self.generate_content("heatmap")
        elif "players" in content:
            what = await self.generate_content("players")
        elif "tournaments" in content:
            what = await self.generate_content("tournaments")
        elif "layers" in content:
            what = await self.generate_content("layers")
        else:
            what = content  # Just send the text
        
        # Find destination
        if "dm" in content:
            # Extract username after "dm"
            words = content.split()
            dm_index = words.index("dm") if "dm" in words else -1
            if dm_index >= 0 and dm_index < len(words) - 1:
                username = words[dm_index + 1]
                where = f"@{username}"
        elif "#" in content:
            # Channel mentioned
            channel_start = content.index("#")
            channel_end = content.find(" ", channel_start)
            if channel_end == -1:
                channel_end = len(content)
            where = content[channel_start:channel_end]
        elif "here" in content or "this channel" in content:
            where = "here"
        elif "everywhere" in content or "all" in content:
            where = "all"
        else:
            where = "here"  # Default to current channel
        
        # Send it!
        success = await self.send_anything_anywhere(what, where, message)
        
        if success:
            await message.add_reaction("✅")
    
    async def handle_generate(self, message: discord.Message):
        """Handle content generation requests"""
        request = message.content.replace("!generate", "").strip()
        
        await message.channel.send(f"🎨 Generating {request}...")
        
        content = await self.generate_content(request)
        
        if content:
            await self.send_anything_anywhere(content, message.channel, message)
        else:
            await message.channel.send("❌ Failed to generate content")
    
    async def generate_content(self, request: str) -> Any:
        """Generate content based on request - POLYMORPHIC!"""
        request_lower = request.lower()
        
        try:
            # Generate heat map
            if "heat" in request_lower or "heatmap" in request_lower:
                with get_session() as session:
                    tournaments = session.query(Tournament).filter(
                        Tournament.lat.isnot(None),
                        Tournament.lng.isnot(None)
                    ).limit(50).all()
                    
                    if tournaments:
                        output = "generated_heatmap.png"
                        heatmap(tournaments, output, hint="attendance", style="fire")
                        return output
            
            # Generate layers
            elif "layer" in request_lower:
                bitmap = PolymorphicBitmapLayers(800, 600, background=(20, 20, 30, 255))
                
                # Add some layers
                def draw_circles(draw):
                    import random
                    for _ in range(20):
                        x = random.randint(50, 750)
                        y = random.randint(50, 550)
                        r = random.randint(10, 50)
                        color = (
                            random.randint(100, 255),
                            random.randint(100, 255),
                            random.randint(100, 255),
                            random.randint(50, 150)
                        )
                        draw.ellipse([x-r, y-r, x+r, y+r], fill=color)
                
                bitmap.draw_on_layer("Random", draw_circles)
                output = "generated_layers.png"
                bitmap.save(output)
                return output
            
            # Generate player ranking
            elif "player" in request_lower or "ranking" in request_lower:
                with get_session() as session:
                    players = session.query(Player).limit(10).all()
                    
                    if players:
                        # Use our polymorphic tabulator
                        ranked = tabulate(players, "highest points")
                        
                        # Create embed with rankings
                        embed = discord.Embed(
                            title="🏆 Top Players",
                            color=discord.Color.gold()
                        )
                        
                        for rank, player, score in ranked[:10]:
                            embed.add_field(
                                name=f"#{rank} {player.gamer_tag}",
                                value=f"{score} points",
                                inline=False
                            )
                        
                        return embed
            
            # Generate tournament list
            elif "tournament" in request_lower:
                with get_session() as session:
                    tournaments = session.query(Tournament).order_by(
                        Tournament.start_at.desc()
                    ).limit(5).all()
                    
                    embed = discord.Embed(
                        title="📅 Recent Tournaments",
                        color=discord.Color.blue()
                    )
                    
                    for t in tournaments:
                        date_str = datetime.fromtimestamp(t.start_at).strftime("%Y-%m-%d") if t.start_at else "Unknown"
                        embed.add_field(
                            name=t.name[:50],
                            value=f"{t.num_attendees or 0} attendees | {date_str}",
                            inline=False
                        )
                    
                    return embed
            
            # Default: generate text
            else:
                return f"Generated content for: {request}"
                
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return None
    
    async def run(self):
        """Run the polymorphic Discord bot"""
        if not self.token:
            logger.error("No Discord token")
            return
        
        await self.start()
        
        try:
            if self.client:
                await self.client.start(self.token)
        except Exception as e:
            logger.error(f"Error running bot: {e}")


# Convenience function
async def send_to_discord(content: Any, destination: Any) -> bool:
    """Quick function to send anything to Discord"""
    bot = PolymorphicDiscord()
    await bot.start()
    return await bot.send_anything_anywhere(content, destination)


if __name__ == "__main__":
    print("=" * 70)
    print("POLYMORPHIC DISCORD SENDER")
    print("=" * 70)
    print("\nThis bot can send ANYTHING to ANYWHERE in Discord!")
    print("\nExamples:")
    print("  !send #general 'Hello world'")
    print("  !send @zeiche tournaments_heatmap.png")
    print("  !send dm zeiche generate heatmap")
    print("  !broadcast 'Server announcement!'")
    print("  !generate heatmap")
    print("  'show heatmap in #general'")
    print("  'dm zeiche the player rankings'")
    print("\nThe bot figures out:")
    print("  • What type of content you're sending")
    print("  • Where to send it (channel, DM, everywhere)")
    print("  • How to format it (text, embed, file)")
    print("\nTRUE POLYMORPHISM - It handles ANYTHING!")
    print("=" * 70)
    
    bot = PolymorphicDiscord()
    asyncio.run(bot.run())