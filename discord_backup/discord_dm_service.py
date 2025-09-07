#!/usr/bin/env python3
"""
discord_dm_service.py - Discord bot with DM and image sending capabilities
Can send heat maps and other images to users via DM
"""
import os
import discord
import asyncio
import logging
from typing import Optional
from pathlib import Path

# Import our image generators
from polymorphic_image_generator import heatmap
from polymorphic_bitmap_layers import PolymorphicBitmapLayers
from database import get_session
from tournament_models import Tournament, Player

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiscordDMService:
    """Discord service with DM and image capabilities"""
    
    def __init__(self):
        self.client = None
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        
    async def start(self):
        """Start the Discord bot with DM capabilities"""
        if not self.token:
            logger.error("No Discord token found in environment")
            return False
        
        # Enable DMs and attachments
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        intents.members = True  # Need this to find users
        
        self.client = discord.Client(intents=intents)
        
        @self.client.event
        async def on_ready():
            logger.info(f'Bot logged in as {self.client.user}')
            print(f"✅ Discord bot ready! Logged in as {self.client.user}")
            print("Commands:")
            print("  !dm @user <image_type> - Send image to user via DM")
            print("  !heatmap - Generate and show tournament heat map")
            print("  !layers - Generate layered visualization")
        
        @self.client.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return
            
            content = message.content.strip()
            
            # DM command: !dm @user heatmap
            if content.startswith('!dm'):
                await self.handle_dm_command(message)
            
            # Generate heat map command
            elif content.startswith('!heatmap'):
                await self.handle_heatmap_command(message)
            
            # Generate layered image command
            elif content.startswith('!layers'):
                await self.handle_layers_command(message)
            
            # Help command
            elif content.startswith('!help'):
                help_text = """
**Discord Bot Commands:**
`!dm @user <type>` - Send image to user via DM
  Types: heatmap, layers, tournaments
`!heatmap` - Generate tournament heat map
`!layers` - Generate layered visualization
`!help` - Show this help
                """
                await message.channel.send(help_text)
    
    async def handle_dm_command(self, message: discord.Message):
        """Handle DM commands to send images to users"""
        parts = message.content.split()
        
        if len(parts) < 3:
            await message.channel.send("Usage: !dm @user <image_type>")
            return
        
        # Get mentioned user
        if not message.mentions:
            await message.channel.send("Please mention a user to DM")
            return
        
        target_user = message.mentions[0]
        image_type = parts[2] if len(parts) > 2 else "heatmap"
        
        # Generate appropriate image
        await message.channel.send(f"Generating {image_type} for {target_user.mention}...")
        
        try:
            image_path = await self.generate_image(image_type)
            
            if image_path and os.path.exists(image_path):
                # Send to user via DM
                try:
                    dm_channel = await target_user.create_dm()
                    
                    # Create embed with image
                    embed = discord.Embed(
                        title=f"Tournament Tracker Visualization",
                        description=f"Here's your {image_type} visualization!",
                        color=discord.Color.blue()
                    )
                    
                    # Send with file attachment
                    with open(image_path, 'rb') as f:
                        file = discord.File(f, filename=os.path.basename(image_path))
                        await dm_channel.send(
                            f"Hello {target_user.mention}! Here's the {image_type} you requested:",
                            embed=embed,
                            file=file
                        )
                    
                    await message.channel.send(f"✅ Sent {image_type} to {target_user.mention} via DM!")
                    
                except discord.Forbidden:
                    await message.channel.send(f"❌ Cannot DM {target_user.mention} (DMs may be disabled)")
                except Exception as e:
                    await message.channel.send(f"❌ Error sending DM: {e}")
            else:
                await message.channel.send(f"❌ Failed to generate {image_type}")
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            await message.channel.send(f"❌ Error: {e}")
    
    async def handle_heatmap_command(self, message: discord.Message):
        """Generate and send heat map in channel"""
        await message.channel.send("🔥 Generating tournament heat map...")
        
        try:
            image_path = await self.generate_image("heatmap")
            
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    file = discord.File(f, filename="tournament_heatmap.png")
                    
                    embed = discord.Embed(
                        title="Tournament Heat Map",
                        description="Geographic distribution of tournaments",
                        color=discord.Color.orange()
                    )
                    embed.set_image(url=f"attachment://tournament_heatmap.png")
                    
                    await message.channel.send(embed=embed, file=file)
            else:
                await message.channel.send("❌ Failed to generate heat map")
                
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.channel.send(f"❌ Error: {e}")
    
    async def handle_layers_command(self, message: discord.Message):
        """Generate and send layered visualization"""
        await message.channel.send("🎨 Generating layered visualization...")
        
        try:
            image_path = await self.generate_image("layers")
            
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    file = discord.File(f, filename="layers.png")
                    
                    embed = discord.Embed(
                        title="Layered Tournament Visualization",
                        description="Multi-layer data visualization with transparency",
                        color=discord.Color.purple()
                    )
                    embed.set_image(url=f"attachment://layers.png")
                    
                    await message.channel.send(embed=embed, file=file)
            else:
                await message.channel.send("❌ Failed to generate layers")
                
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.channel.send(f"❌ Error: {e}")
    
    async def generate_image(self, image_type: str) -> Optional[str]:
        """Generate the requested image type"""
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_image_sync, image_type)
    
    def _generate_image_sync(self, image_type: str) -> Optional[str]:
        """Synchronous image generation"""
        try:
            with get_session() as session:
                if image_type in ["heatmap", "tournaments", "heat"]:
                    # Generate tournament heat map
                    tournaments = session.query(Tournament).filter(
                        Tournament.lat.isnot(None),
                        Tournament.lng.isnot(None)
                    ).limit(50).all()
                    
                    if tournaments:
                        output = "discord_heatmap.png"
                        heatmap(tournaments, output, hint="attendance", style="fire")
                        return output
                
                elif image_type == "layers":
                    # Generate layered visualization
                    bitmap = PolymorphicBitmapLayers(800, 600, background=(20, 20, 30, 255))
                    
                    # Add grid layer
                    def draw_grid(draw):
                        for x in range(0, 800, 50):
                            draw.line([(x, 0), (x, 600)], fill=(100, 100, 100, 50))
                        for y in range(0, 600, 50):
                            draw.line([(0, y), (800, y)], fill=(100, 100, 100, 50))
                    
                    bitmap.draw_on_layer("Grid", draw_grid)
                    
                    # Add tournament points
                    tournaments = session.query(Tournament).filter(
                        Tournament.lat.isnot(None),
                        Tournament.lng.isnot(None)
                    ).limit(20).all()
                    
                    if tournaments:
                        points = []
                        for t in tournaments:
                            # Simple mapping to canvas
                            x = 400 + (float(t.lng) + 118) * 20
                            y = 300 - (float(t.lat) - 34) * 20
                            weight = (t.num_attendees or 10) / 5
                            points.append((x, y, weight))
                        
                        bitmap.apply_heat_map("Heat", points, colormap='plasma')
                    
                    output = "discord_layers.png"
                    bitmap.save(output)
                    return output
                
                elif image_type == "players":
                    # Generate player skill distribution
                    players = session.query(Player).limit(30).all()
                    
                    if players:
                        skill_points = []
                        for player in players:
                            wins = sum(1 for p in player.placements if p.placement == 1)
                            events = len(player.placements)
                            win_rate = (wins / events * 100) if events > 0 else 0
                            
                            # Map to visualization space
                            skill_points.append({
                                "x": win_rate * 8,
                                "y": events * 10,
                                "weight": wins
                            })
                        
                        output = "discord_players.png"
                        heatmap(skill_points, output, background="blank", style="cool")
                        return output
                
                # Default: return existing heat map if available
                existing = ["tournaments_heatmap.png", "multi_function_layers.png", "layered_demo.png"]
                for file in existing:
                    if os.path.exists(file):
                        return file
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
    
    async def run(self):
        """Run the Discord bot"""
        if not self.token:
            logger.error("No Discord token found")
            return
        
        # Start the bot (which initializes client)
        await self.start()
        
        try:
            if self.client:
                await self.client.start(self.token)
        except Exception as e:
            logger.error(f"Discord bot error: {e}")


async def main():
    """Main entry point"""
    service = DiscordDMService()
    await service.run()


if __name__ == "__main__":
    print("Starting Discord bot with DM and image capabilities...")
    asyncio.run(main())