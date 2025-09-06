#!/usr/bin/env python3
"""
Direct DM sender for poop emoji to zeiche
"""
import discord
import asyncio
import os

async def dm_poop():
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        with open('/home/ubuntu/claude/tournament_tracker/.env', 'r') as f:
            for line in f:
                if line.startswith('DISCORD_BOT_TOKEN='):
                    token = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.dm_messages = True
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'✅ Logged in as {client.user}')
        
        # Find zeiche
        zeiche = None
        for guild in client.guilds:
            for member in guild.members:
                if 'zeiche' in member.name.lower():
                    zeiche = member
                    print(f"Found zeiche: {member.name}#{member.discriminator}")
                    break
            if zeiche:
                break
        
        if not zeiche:
            print("❌ Can't find zeiche! Available users:")
            for guild in client.guilds:
                print(f"Guild: {guild.name}")
                for member in guild.members[:20]:
                    print(f"  - {member.name}")
            await client.close()
            return
        
        # Create DM
        dm = await zeiche.create_dm()
        
        # Send the poop image
        embed = discord.Embed(
            title="💩 Big Poop on Yellow Background",
            description="As requested - a majestic poop emoji!",
            color=discord.Color.gold()
        )
        embed.set_image(url="attachment://poop.png")
        
        with open('poop_emoji_yellow.png', 'rb') as f:
            file = discord.File(f, filename='poop.png')
            await dm.send(
                content="Here's your poop emoji on yellow background! 💩",
                embed=embed,
                file=file
            )
        
        print("✅ DM sent with poop image!")
        await asyncio.sleep(2)
        await client.close()
    
    await client.start(token)

if __name__ == "__main__":
    print("Sending poop emoji to zeiche...")
    asyncio.run(dm_poop())