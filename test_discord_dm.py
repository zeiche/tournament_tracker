#!/usr/bin/env python3
"""
Test script to demonstrate Discord DM with image functionality
This shows how the bot can send heat map images via DM
"""
import os
import sys

print("=" * 70)
print("DISCORD DM IMAGE TEST")
print("=" * 70)

print("\n📋 Instructions to test Discord DM with images:")
print("-" * 50)

print("\n1. START THE BOT:")
print("   ./go.py --discord-bot")
print("   OR")
print("   python3 discord_dm_service.py")

print("\n2. IN DISCORD, USE THESE COMMANDS:")
print("   !help                    - Show all commands")
print("   !heatmap                 - Generate heat map in channel")
print("   !layers                  - Generate layered visualization")
print("   !dm @zeiche heatmap      - Send heat map to zeiche via DM")
print("   !dm @zeiche layers       - Send layers to zeiche via DM")
print("   !dm @zeiche tournaments  - Send tournament viz to zeiche via DM")

print("\n3. THE BOT WILL:")
print("   • Generate the requested visualization")
print("   • Send it as an embedded image in a DM")
print("   • Confirm in the channel that DM was sent")

print("\n4. FEATURES DEMONSTRATED:")
print("   ✅ Polymorphic image generation (heat maps, layers)")
print("   ✅ Discord file attachments")
print("   ✅ Direct messaging with embeds")
print("   ✅ Multiple visualization types")
print("   ✅ Tournament data from database")

print("\n5. IMAGE TYPES AVAILABLE:")
print("   • heatmap - Geographic heat map of tournaments")
print("   • layers - Multi-layer transparent visualization")
print("   • players - Player skill distribution")
print("   • tournaments - Tournament locations")

print("\n" + "=" * 70)

# Check if Discord token is set
if os.getenv('DISCORD_BOT_TOKEN'):
    print("✅ Discord token found in environment")
else:
    print("❌ No Discord token found - set DISCORD_BOT_TOKEN")

# Check if images exist
images = [
    "tournaments_heatmap.png",
    "multi_function_layers.png", 
    "layered_demo.png"
]

print("\n📁 Available images for sending:")
for img in images:
    if os.path.exists(img):
        size = os.path.getsize(img) / 1024
        print(f"   ✅ {img} ({size:.1f} KB)")
    else:
        print(f"   ❌ {img} (not found)")

print("\n" + "=" * 70)
print("Ready to test Discord DM with images!")
print("The bot will DM zeiche (or any mentioned user) with heat maps!")
print("=" * 70)