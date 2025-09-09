#!/usr/bin/env python3
"""
Discord-Lightweight Bridge - Connects Discord to lightweight intelligence
Uses pattern matching instead of LLM for instant responses
"""

import discord
import asyncio
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridges.base_bridge import BaseBridge, BridgeRegistry
from utils.database_service import DatabaseService
from services.startgg_sync import StartGGSync
from polymorphic_core import announcer


class DiscordLightweightBridge(BaseBridge):
    """Bridge Discord messages to lightweight intelligence"""
    
    def __init__(self):
        super().__init__(
            name="Discord-Lightweight Bridge",
            source="Discord", 
            target="Lightweight Intelligence"
        )
        
        # Get Discord token
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            raise ValueError("No Discord token! Set DISCORD_BOT_TOKEN")
        
        # Create services
        self.db = DatabaseService()
        self.sync = StartGGSync()
        
        # Discord client will be created when started
        self.client = None
        
        # Register with bridge registry
        BridgeRegistry.register(self)
        
        # Additional announcement
        announcer.announce(self.name, [
            "I connect Discord to lightweight intelligence",
            "No LLM needed - pure pattern matching",
            "Instant responses using database queries",
            "Ask about tournaments, players, rankings"
        ])
    
    async def process(self, message: Any, **kwargs) -> str:
        """Process a message through lightweight intelligence"""
        # Handle different message types polymorphically
        if isinstance(message, str):
            query = message
        elif hasattr(message, 'content'):  # Discord message
            query = message.content
        else:
            query = str(message)
        
        query_lower = query.lower()
        
        # Process with lightweight intelligence
        try:
            # Special handling for sync
            if 'sync' in query_lower:
                result = self.sync.do('sync tournaments')
                return f"Sync complete: {result}"
            
            # Help
            elif query_lower in ['help', '?', 'help me', 'what can you do']:
                return """I understand:
• top players / rankings / leaderboard
• recent tournaments
• player [name]
• tournament [id]
• all / everything
• stats
• sync"""
            
            # Visualization requests - route to proper visualization services
            elif 'heatmap' in query_lower or 'heat map' in query_lower:
                return await self._handle_heatmap_request(message, query)
            
            # Everything else - let database handle it (pure data queries)
            else:
                result = self.db.ask(query)
                
                if result:
                    # Format for Discord
                    formatted = self.db.tell('discord', result)
                    
                    # Discord has 2000 char limit
                    if len(formatted) > 1990:
                        formatted = formatted[:1987] + "..."
                    
                    self.message_count += 1
                    return formatted
                else:
                    return "No results found. Try 'help' for examples."
                    
        except Exception as e:
            return f"Error: {str(e)}\nTry 'help' for examples."
    
    async def _handle_heatmap_request(self, message, query: str) -> str:
        """Handle heatmap requests with potential image upload"""
        try:
            from visualization_services import heatmap_service
            import discord
            import os
            
            query_lower = query.lower()
            
            # Check if user wants an image/picture
            wants_image = any(word in query_lower for word in ['picture', 'image', 'png', 'generate']) or ('show' in query_lower and 'me' in query_lower)
            
            if wants_image:
                # Request image generation
                result = heatmap_service.ask("generate image for tournament heatmap")
                
                if isinstance(result, dict) and 'image_path' in result:
                    # Upload the image to Discord
                    image_path = result['image_path']
                    if os.path.exists(image_path):
                        try:
                            # Send the image file
                            with open(image_path, 'rb') as f:
                                discord_file = discord.File(f, filename='tournament_heatmap.png')
                                await message.channel.send(
                                    f"🗺️ **{result.get('title', 'Tournament Heatmap')}**\n"
                                    f"📊 {result.get('data_points', 0)} tournament locations\n"
                                    f"📁 {result.get('size', 0):,} bytes",
                                    file=discord_file
                                )
                            
                            # Clean up temporary file
                            try:
                                os.unlink(image_path)
                            except:
                                pass
                            
                            self.message_count += 1
                            return None  # Already sent the response with image
                        
                        except Exception as upload_error:
                            return f"Image generated but upload failed: {upload_error}"
                    else:
                        return "Image generation completed but file not found"
                        
                elif isinstance(result, dict) and 'error' in result:
                    return f"Image generation failed: {result['error']}"
                else:
                    return "Image generation returned unexpected result"
            
            else:
                # User wants data, not image
                result = heatmap_service.ask(query)
                
                if result:
                    formatted = f"Generated heatmap with {len(result)} tournament locations"
                    self.message_count += 1
                    return formatted
                else:
                    return "No heatmap data available"
                    
        except ImportError:
            return "Visualization services not available"
        except Exception as e:
            return f"Heatmap request failed: {str(e)}"
    
    def start_discord_bot(self):
        """Start the Discord bot connection"""
        if self.active:
            return "Already running"
        
        # Setup Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        # Register event handlers
        @self.client.event
        async def on_ready():
            print(f'✅ {self.name} connected as {self.client.user}')
            self.active = True
            self._announce()
        
        @self.client.event
        async def on_message(message):
            # Ignore own messages
            if message.author == self.client.user:
                return
            
            # Process with the bridge
            response = await self.process(message)
            
            # Only send text response if we got one (None means already handled)
            if response is not None:
                await message.channel.send(response)
        
        # Start the bot
        print(f"🚀 Starting {self.name}...")
        print("⚡ No LLM needed - using lightweight intelligence!")
        self.client.run(self.token)
    
    def start(self):
        """Start the bridge (for programmatic use)"""
        self.start_discord_bot()
        return super().start()


# Make it runnable directly
if __name__ == "__main__":
    bridge = DiscordLightweightBridge()
    bridge.start_discord_bot()