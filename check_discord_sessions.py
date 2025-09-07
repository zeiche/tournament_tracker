#!/usr/bin/env python3
"""
Check Discord sessions and voice states
"""

import discord
import asyncio
import os
from pathlib import Path

# Load token
token = os.getenv('DISCORD_BOT_TOKEN')
if not token:
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('DISCORD_BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break

if not token:
    raise ValueError("No Discord token found!")

# Setup client with minimal intents
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print("=" * 60)
    print("🔍 Discord Session & Voice State Check")
    print("=" * 60)
    print(f"✅ Connected as: {client.user} (ID: {client.user.id})")
    print(f"📡 Session ID: {client.ws.session_id if client.ws else 'N/A'}")
    print()
    
    # Check all guilds
    for guild in client.guilds:
        print(f"📍 Guild: {guild.name} (ID: {guild.id})")
        print(f"   Members: {guild.member_count}")
        
        # Check if bot is in any voice channel
        bot_member = guild.get_member(client.user.id)
        if bot_member and bot_member.voice:
            print(f"   ⚠️  BOT IS IN VOICE: {bot_member.voice.channel.name}")
            print(f"      - Channel ID: {bot_member.voice.channel.id}")
            print(f"      - Self muted: {bot_member.voice.self_mute}")
            print(f"      - Self deafened: {bot_member.voice.self_deaf}")
        else:
            print("   ✅ Bot not in any voice channel")
        
        # Check for existing voice client
        if guild.voice_client:
            print(f"   ⚠️  VOICE CLIENT EXISTS!")
            print(f"      - Connected: {guild.voice_client.is_connected()}")
            print(f"      - Channel: {guild.voice_client.channel.name if guild.voice_client.channel else 'None'}")
            print(f"      - Playing: {guild.voice_client.is_playing()}")
            
            # Try to disconnect
            print("      - Attempting to disconnect...")
            try:
                await guild.voice_client.disconnect(force=True)
                print("      - ✅ Disconnected successfully")
            except Exception as e:
                print(f"      - ❌ Failed to disconnect: {e}")
        else:
            print("   ✅ No voice client exists")
        
        # List all voice channels
        print("   Voice Channels:")
        for vc in guild.voice_channels:
            members = len(vc.members)
            print(f"      - #{vc.name}: {members} members")
            if client.user in vc.members:
                print(f"        ⚠️  BOT IS IN THIS CHANNEL!")
        
        print()
    
    # Check for any active voice connections
    print("🔊 Voice Connection Summary:")
    voice_connections = client.voice_clients
    if voice_connections:
        print(f"   ⚠️  Found {len(voice_connections)} active voice connection(s)")
        for i, vc in enumerate(voice_connections, 1):
            print(f"   {i}. Guild: {vc.guild.name if vc.guild else 'Unknown'}")
            print(f"      Channel: {vc.channel.name if vc.channel else 'None'}")
            print(f"      Connected: {vc.is_connected()}")
    else:
        print("   ✅ No active voice connections")
    
    print()
    print("=" * 60)
    print("🧹 Cleanup Actions:")
    
    # Clean up any voice connections
    if voice_connections:
        print("   Disconnecting all voice clients...")
        for vc in voice_connections:
            try:
                await vc.disconnect(force=True)
                print(f"   ✅ Disconnected from {vc.guild.name}")
            except Exception as e:
                print(f"   ❌ Failed to disconnect from {vc.guild.name}: {e}")
    else:
        print("   No cleanup needed")
    
    print("=" * 60)
    print("✅ Check complete. Shutting down...")
    await client.close()

async def main():
    try:
        await client.start(token)
    except discord.LoginFailure:
        print("❌ Invalid Discord token!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())