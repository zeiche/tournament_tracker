#!/usr/bin/env python3
"""
Discord-Lightweight Bridge - Connects Discord to lightweight intelligence
When Discord messages arrive, passes them to lightweight intelligence
"""

import discord
import asyncio
import os
from utils.database_service import DatabaseService
from services.startgg_sync import StartGGSync
from polymorphic_core import announcer

class DiscordLightweightBridge:
    """Bridge Discord messages to lightweight intelligence"""
    
    def __init__(self):
        # Get Discord token
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            raise ValueError("No Discord token! Set DISCORD_BOT_TOKEN")
        
        # Create services
        self.db = DatabaseService()
        self.sync = StartGGSync()
        
        # Setup Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        # Register event handlers
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        
        # Announce ourselves
        announcer.announce("Discord-Lightweight Bridge", [
            "I connect Discord to lightweight intelligence",
            "No LLM needed - pure pattern matching",
            "Ask me about tournaments, players, rankings",
            "I respond instantly with database queries"
        ])
    
    async def on_ready(self):
        """Called when Discord bot connects"""
        print(f'✅ Discord-Lightweight Bridge connected as {self.client.user}')
        announcer.announce("Discord Connected", [f"Bot: {self.client.user}"])
    
    async def on_message(self, message):
        """Handle Discord messages with lightweight intelligence"""
        # Ignore own messages
        if message.author == self.client.user:
            return
        
        # Get the query
        query = message.content.lower()
        
        # Process with lightweight intelligence (same logic as lightweight_bonjour.py)
        try:
            # Special handling for sync
            if 'sync' in query:
                await message.channel.send("Starting sync...")
                result = self.sync.do('sync tournaments')
                await message.channel.send(f"Sync complete: {result}")
            
            # Help
            elif query in ['help', '?', 'help me', 'what can you do']:
                help_text = """I understand:
• top players / rankings / leaderboard
• recent tournaments
• player [name]
• tournament [id]
• all / everything
• stats
• sync"""
                await message.channel.send(help_text)
            
            # Everything else - let database handle it
            else:
                result = self.db.ask(message.content)  # Use original case
                
                if result:
                    # Format for Discord
                    formatted = self.db.tell('discord', result)
                    
                    # Discord has 2000 char limit
                    if len(formatted) > 1990:
                        formatted = formatted[:1987] + "..."
                    
                    await message.channel.send(formatted)
                else:
                    await message.channel.send("No results found. Try 'help' for examples.")
                    
        except Exception as e:
            await message.channel.send(f"Error: {str(e)}\nTry 'help' for examples.")
    
    def run(self):
        """Start the Discord bot"""
        print("🚀 Starting Discord-Lightweight Bridge...")
        print("⚡ No LLM needed - using lightweight intelligence!")
        self.client.run(self.token)

if __name__ == "__main__":
    bridge = DiscordLightweightBridge()
    bridge.run()