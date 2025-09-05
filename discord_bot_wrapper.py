#!/usr/bin/env python3
"""
discord_bot_wrapper.py - Example of using Discord service as SINGLE SOURCE OF TRUTH
This shows the CORRECT way to use Discord bot functionality - through discord_service ONLY
"""
import sys
import argparse

# ONLY import from discord_service - the SINGLE source of truth
from discord_service import discord_service, BotMode


def main():
    """Main entry point showing proper Discord service usage"""
    parser = argparse.ArgumentParser(
        description='Discord Bot Wrapper - Uses SINGLE SOURCE OF TRUTH'
    )
    parser.add_argument(
        '--mode', 
        choices=['simple', 'conversational', 'claude', 'hybrid'],
        default='conversational',
        help='Bot operation mode'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show Discord service statistics and exit'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if Discord service is enabled'
    )
    
    args = parser.parse_args()
    
    # Check if enabled
    if args.check:
        if discord_service.is_enabled:
            print("✅ Discord service is ENABLED")
            print(f"   Bot name: {discord_service.config.bot_name}")
            print(f"   Default mode: {discord_service.config.mode.value}")
            print(f"   Command prefix: {discord_service.config.command_prefix}")
        else:
            print("❌ Discord service is DISABLED")
            print("   Set DISCORD_BOT_TOKEN environment variable to enable")
        return 0
    
    # Show statistics
    if args.stats:
        stats = discord_service.get_statistics()
        print("\n=== Discord Service Statistics (SINGLE SOURCE OF TRUTH) ===")
        print(f"Enabled: {stats['enabled']}")
        print(f"Running: {stats['running']}")
        
        if stats['enabled']:
            print("\nConfiguration:")
            for key, value in stats['config'].items():
                print(f"  {key}: {value}")
            
            print("\nRuntime Statistics:")
            for key, value in stats['stats'].items():
                print(f"  {key}: {value}")
        
        return 0
    
    # Check if service is enabled
    if not discord_service.is_enabled:
        print("❌ Discord service is not enabled")
        print("   Set DISCORD_BOT_TOKEN environment variable or .env.discord file")
        print("\n   Example .env.discord:")
        print("   DISCORD_BOT_TOKEN=your_token_here")
        return 1
    
    # Set the mode
    try:
        discord_service.config.mode = BotMode(args.mode)
    except ValueError:
        print(f"❌ Invalid mode: {args.mode}")
        return 1
    
    print(f"🤖 Starting Discord bot in {discord_service.config.mode.value} mode...")
    print("   This is the ONLY approved way to run the Discord bot")
    print("   All Discord operations go through discord_service.py")
    print("\n   Press Ctrl+C to stop the bot")
    
    try:
        # Run the bot - this is the ONLY place we start it
        discord_service.run_blocking()
        print("\n✅ Discord bot stopped cleanly")
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Bot stopped by user")
        return 130
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())