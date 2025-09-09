#!/usr/bin/env python3
"""
Bridge Launcher - Unified launcher for all bridge services
"""

import sys
import argparse
from typing import Optional


def launch_bridge(bridge_type: str) -> Optional[str]:
    """
    Launch a specific bridge type.
    
    Args:
        bridge_type: Type of bridge to launch
        
    Returns:
        Status message or None if bridge not found
    """
    bridge_type = bridge_type.lower()
    
    if bridge_type in ['discord-lightweight', 'lightweight']:
        from bridges.discord_lightweight import DiscordLightweightBridge
        bridge = DiscordLightweightBridge()
        bridge.start_discord_bot()
        
    elif bridge_type in ['discord-claude', 'claude']:
        # Import when we move it
        return "Discord-Claude bridge not yet migrated to bridges module"
        
    elif bridge_type in ['discord-ollama', 'ollama']:
        # Import when we create it
        return "Discord-Ollama bridge not yet implemented"
        
    elif bridge_type in ['bonjour', 'bonjour-monitor']:
        from ollama_bonjour.bonjour_bridge import run_bridge
        run_bridge()
        
    else:
        return f"Unknown bridge type: {bridge_type}"
    
    return f"Started {bridge_type} bridge"


def list_bridges():
    """List all available bridges"""
    bridges = [
        "discord-lightweight - Discord ↔ Lightweight Intelligence (no LLM)",
        "discord-claude - Discord ↔ Claude (requires API key)",
        "discord-ollama - Discord ↔ Ollama (local LLM)",
        "bonjour - Bonjour service monitor"
    ]
    
    print("Available bridges:")
    for bridge in bridges:
        print(f"  • {bridge}")


def main():
    """Main entry point for bridge launcher"""
    parser = argparse.ArgumentParser(
        description="Bridge Launcher - Start bridge services"
    )
    
    parser.add_argument(
        'bridge',
        nargs='?',
        help='Bridge type to launch (e.g., discord-lightweight)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available bridges'
    )
    
    args = parser.parse_args()
    
    if args.list or not args.bridge:
        list_bridges()
    else:
        result = launch_bridge(args.bridge)
        if result:
            print(result)


if __name__ == "__main__":
    main()