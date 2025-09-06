#!/usr/bin/env python3
"""
go_lightweight.py - The PROPER go.py that follows Bonjour principles

This is just a ROUTER that:
1. Parses command line arguments
2. Routes to the appropriate module
3. Each module initializes itself and announces capabilities
4. NO central initialization, NO dependencies, NO database setup
"""

import sys
import argparse
from capability_announcer import announcer

class LightweightRouter:
    """Ultra-light router that just dispatches commands"""
    
    def __init__(self):
        # Announce ourselves
        announcer.announce(
            "LightweightRouter",
            ["I route commands to appropriate modules", "I don't initialize anything"],
            examples=["./go.py --discord-bot --discord-mode voice"]
        )
        
    def route(self, args):
        """Route to appropriate module based on arguments"""
        
        # Discord bot (any mode)
        if args.get('discord_bot'):
            mode = args.get('discord_mode', 'conversational')
            
            if mode == 'voice':
                # Voice bot handles its own setup
                announcer.announce("Router", ["Routing to voice bot"])
                from fire_voice_bot import main as voice_main
                import asyncio
                asyncio.run(voice_main())
                
            else:
                # Text bot handles its own setup
                announcer.announce("Router", ["Routing to text Discord bot"])
                from discord_service import start_discord_bot
                start_discord_bot(mode)
        
        # Web editor
        elif args.get('edit_contacts'):
            announcer.announce("Router", ["Routing to web editor"])
            from editor_service import EditorService
            editor = EditorService()  # It initializes itself
            editor.start(port=args.get('editor_port', 8081))
        
        # Tournament sync
        elif args.get('sync'):
            announcer.announce("Router", ["Routing to sync service"])
            from sync_service import SyncService
            sync = SyncService()  # It initializes itself
            sync.sync_tournaments()
        
        # Console report
        elif args.get('console'):
            announcer.announce("Router", ["Routing to report generator"])
            from tournament_report import generate_console_report
            generate_console_report()  # It handles its own DB
        
        # Heatmap
        elif args.get('heatmap'):
            announcer.announce("Router", ["Routing to heatmap generator"])
            from tournament_heatmap import generate_all_heatmaps
            generate_all_heatmaps()  # It handles its own setup
        
        # AI chat
        elif args.get('ai_chat'):
            announcer.announce("Router", ["Routing to AI chat"])
            from claude_service import ClaudeService
            claude = ClaudeService()  # It initializes itself
            claude.start_terminal_chat()
        
        # DM image
        elif args.get('dm_image'):
            user, image, message = args['dm_image']
            announcer.announce("Router", ["Routing to Discord DM sender"])
            from polymorphic_discord_sender import send_to_discord
            send_to_discord(user, image, title=message)
        
        # Service management
        elif args.get('restart_services'):
            announcer.announce("Router", ["Routing to service manager"])
            import subprocess
            # Kill existing processes
            subprocess.run(['pkill', '-f', 'discord'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'bot'], stderr=subprocess.DEVNULL)
            subprocess.run(['pkill', '-f', 'web_editor'], stderr=subprocess.DEVNULL)
            print("✅ Services restarted")
        
        # Stats
        elif args.get('stats'):
            announcer.announce("Router", ["Routing to stats viewer"])
            from database_service import DatabaseService
            db = DatabaseService()  # It initializes itself
            db.show_stats()
        
        else:
            print("No valid command specified. Use --help for options.")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Tournament Tracker Router - Routes commands to services',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Discord options
    parser.add_argument('--discord-bot', action='store_true',
                       help='Start Discord bot')
    parser.add_argument('--discord-mode', choices=['voice', 'text', 'claude'],
                       default='text', help='Discord bot mode')
    
    # Services
    parser.add_argument('--edit-contacts', action='store_true',
                       help='Start web editor')
    parser.add_argument('--editor-port', type=int, default=8081,
                       help='Web editor port')
    
    # Sync
    parser.add_argument('--sync', action='store_true',
                       help='Sync tournaments')
    parser.add_argument('--skip-sync', action='store_true',
                       help='Skip sync (for other operations)')
    
    # Reports
    parser.add_argument('--console', action='store_true',
                       help='Show console report')
    parser.add_argument('--heatmap', action='store_true',
                       help='Generate heatmaps')
    
    # AI
    parser.add_argument('--ai-chat', action='store_true',
                       help='Start AI chat')
    
    # Discord utilities
    parser.add_argument('--dm-image', nargs=3,
                       metavar=('USER', 'IMAGE', 'MESSAGE'),
                       help='Send image via Discord DM')
    
    # Service management
    parser.add_argument('--restart-services', action='store_true',
                       help='Restart all services')
    
    # Stats
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    
    return vars(parser.parse_args())


def main():
    """Main entry point"""
    args = parse_args()
    
    # Skip sync unless explicitly requested
    if not args.get('sync') and not args.get('skip_sync'):
        announcer.announce("Main", ["Skipping sync (use --sync to sync)"])
    
    # Create router and route
    router = LightweightRouter()
    router.route(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)