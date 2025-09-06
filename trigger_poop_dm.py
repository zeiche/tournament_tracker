#!/usr/bin/env python3
"""
Trigger the running polymorphic bot to send poop emoji
"""
import asyncio
import discord
import os
from PIL import Image, ImageDraw

async def trigger_poop_dm():
    """Connect and send a message to trigger the bot"""
    
    # First create the poop image
    print("💩 Creating poop emoji image...")
    
    # Create yellow background
    width, height = 800, 600
    img = Image.new('RGBA', (width, height), color=(255, 255, 0, 255))  # Bright yellow
    draw = ImageDraw.Draw(img)
    
    # Draw poop shape with brown circles
    brown = (101, 67, 33, 255)
    cx, cy = width // 2, height // 2
    
    # Bottom layer (biggest)
    draw.ellipse([cx - 150, cy + 50, cx + 150, cy + 150], fill=brown)
    
    # Middle layer
    draw.ellipse([cx - 120, cy - 20, cx + 120, cy + 80], fill=brown)
    
    # Top layer  
    draw.ellipse([cx - 90, cy - 80, cx + 90, cy + 20], fill=brown)
    
    # Swirl at top
    draw.ellipse([cx - 40, cy - 120, cx + 40, cy - 60], fill=brown)
    
    # Add googly eyes
    white = (255, 255, 255, 255)
    black = (0, 0, 0, 255)
    
    # Left eye white
    draw.ellipse([cx - 60, cy - 50, cx - 20, cy - 10], fill=white)
    # Left pupil
    draw.ellipse([cx - 45, cy - 40, cx - 30, cy - 25], fill=black)
    
    # Right eye white
    draw.ellipse([cx + 20, cy - 50, cx + 60, cy - 10], fill=white)
    # Right pupil
    draw.ellipse([cx + 30, cy - 40, cx + 45, cy - 25], fill=black)
    
    # Big smile
    draw.arc([cx - 70, cy - 30, cx + 70, cy + 50], start=0, end=180, fill=black, width=8)
    
    # Add some sparkles for fun
    sparkle = (255, 255, 255, 200)
    draw.ellipse([cx - 180, cy - 100, cx - 160, cy - 80], fill=sparkle)
    draw.ellipse([cx + 160, cy - 50, cx + 180, cy - 30], fill=sparkle)
    draw.ellipse([cx - 100, cy + 100, cx - 80, cy + 120], fill=sparkle)
    draw.ellipse([cx + 80, cy + 90, cx + 100, cy + 110], fill=sparkle)
    
    # Save it
    output_path = "/home/ubuntu/claude/tournament_tracker/big_poop_yellow.png"
    img.save(output_path)
    print(f"✅ Poop image created: {output_path}")
    
    # Now send a Discord message to the bot to trigger it
    print("\n📱 Connecting to Discord to trigger bot...")
    
    # Load token
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        env_file = '/home/ubuntu/claude/tournament_tracker/.env'
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('DISCORD_BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    
    # Create a temporary client just to send the trigger message
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"✅ Connected as {client.user}")
        
        # Find a channel to send in
        for guild in client.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    print(f"📤 Sending trigger in #{channel.name}")
                    
                    # Send command to trigger the polymorphic bot
                    await channel.send(f"!send @zeiche {output_path}")
                    
                    await asyncio.sleep(1)
                    
                    # Also try natural language
                    await channel.send(f"dm zeiche the file {output_path}")
                    
                    print("✅ Trigger messages sent!")
                    await asyncio.sleep(2)
                    await client.close()
                    return
        
        print("❌ No suitable channel found")
        await client.close()
    
    try:
        await client.start(token)
    except:
        pass

if __name__ == "__main__":
    print("=" * 60)
    print("TRIGGERING POOP EMOJI DM")
    print("=" * 60)
    
    asyncio.run(trigger_poop_dm())
    print("\n✅ Done! Check Discord DMs!")