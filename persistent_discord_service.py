#!/usr/bin/env python3
"""
persistent_discord_service.py - Minimal persistent Discord bot service

This service:
1. Runs persistently (doesn't exit)
2. Connects to Discord via try-hard#8718 bot
3. Advertises as discord.local via mDNS
4. Provides Discord chat integration with Claude
"""

import asyncio
import sys
import os
import time
import threading
from polymorphic_core import announcer

# Load environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class PersistentDiscordService:
    """Persistent Discord service"""

    def __init__(self):
        self.running = False
        self.bot = None

    def start(self):
        """Start the persistent Discord service"""
        print(f"🤖 Starting persistent Discord bot service")

        # Announce via mDNS as discord.local
        announcer.announce(
            "discord.local",
            [
                "Discord Bot Service",
                "try-hard#8718 Bot Integration",
                "Claude Chat Bridge",
                "Persistent Discord Connection"
            ],
            examples=[
                "Message the bot in Discord",
                "Natural language queries supported",
                "Connects to Claude AI"
            ]
        )

        # Also advertise the hostname directly via zeroconf
        try:
            from zeroconf import ServiceInfo, Zeroconf
            import socket

            # Create hostname service info
            hostname_info = ServiceInfo(
                "_discord._tcp.local.",
                "discord._discord._tcp.local.",
                addresses=[socket.inet_aton("10.0.0.1")],
                port=6667,
                properties={
                    'hostname': 'discord.local',
                    'bot': 'try-hard#8718',
                    'description': 'Discord Bot Service'
                },
                server="discord.local."
            )

            # Get or create zeroconf instance
            if hasattr(announcer, 'zeroconf') and announcer.zeroconf:
                announcer.zeroconf.register_service(hostname_info)
                print(f"🤖 Registered discord.local hostname via mDNS")
            else:
                print("⚠️  Could not register hostname - using service announcement only")

        except Exception as e:
            print(f"⚠️  Hostname registration failed: {e}")

        # Start Discord bot
        try:
            self.running = True
            print(f"✅ Discord bot service running persistently")
            print(f"🤖 Bot: try-hard#8718")
            print(f"🏃 Service running persistently - press Ctrl+C to stop")

            # Import and run the Discord bot
            from discord_bridge import main as discord_main
            discord_main()

        except Exception as e:
            print(f"❌ Failed to start Discord service: {e}")
            self.running = False

    def stop(self):
        """Stop the Discord service"""
        if self.bot:
            print("🛑 Stopping Discord bot service...")
            self.running = False

def main():
    """Main entry point"""
    service = PersistentDiscordService()

    try:
        service.start()
    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
        service.stop()
        print("✅ Discord bot service stopped")

if __name__ == "__main__":
    main()