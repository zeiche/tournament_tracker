#!/usr/bin/env python3
"""
discord_claude_bridge.py - Bridge between Discord and Claude with Bonjour

This bridge:
1. Receives messages from Discord
2. Routes them to Claude (with discovered context)
3. Returns Claude's responses
4. NO business logic - just message passing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude.services.claude_bonjour_service import claude_bonjour
from polymorphic_core import announcer
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DiscordClaudeBridge:
    """
    Thin bridge between Discord and Claude.
    Uses Bonjour-enhanced Claude for dynamic capabilities.
    """
    
    def __init__(self):
        self.claude = claude_bonjour
        self.message_count = 0
        
        # Announce ourselves
        announcer.announce(
            "Discord-Claude Bridge",
            [
                "Routes Discord messages to Claude",
                "Uses Bonjour discovery for context",
                "Returns Claude responses to Discord",
                "Pure message conduit - no business logic"
            ],
            [
                "bridge.process('user message')",
                "bridge.get_status()"
            ]
        )
        
        logger.info("Discord-Claude bridge initialized with Bonjour discovery")
    
    async def process_message(self, message: str, user_id: Optional[str] = None) -> str:
        """
        Process a Discord message through Claude.
        
        Args:
            message: The user's message from Discord
            user_id: Optional Discord user ID for context
            
        Returns:
            Claude's response as a string
        """
        self.message_count += 1
        
        try:
            # Use Claude with discovery - it will build its own context
            result = self.claude.ask_with_discovery(message)
            
            if result['success']:
                response = result['response']
                
                # Add service awareness footer if relevant services were used
                if result.get('relevant_services'):
                    services = result['relevant_services'][:3]
                    response += f"\n\n_[Used: {', '.join(services)}]_"
                
                return response
            else:
                error = result.get('error', 'Unknown error')
                return f"I encountered an error: {error}"
                
        except Exception as e:
            logger.error(f"Bridge error: {e}")
            return "I'm having trouble processing that request right now."
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status including Claude's discovered capabilities"""
        caps = self.claude.get_conversation_capabilities()
        
        return {
            'bridge_active': True,
            'messages_processed': self.message_count,
            'claude_status': {
                'discovered_services': caps['discovered_services'],
                'active_services': caps['active_services'],
                'can_handle': len(caps['can_handle'])
            }
        }
    
    async def handle_command(self, command: str) -> str:
        """
        Handle special Discord commands.
        
        Commands:
            !capabilities - Show what Claude can currently do
            !services - List discovered services
            !status - Show bridge status
        """
        command_lower = command.lower().strip()
        
        if command_lower == '!capabilities':
            caps = self.claude.get_conversation_capabilities()
            return (
                f"**Claude's Current Capabilities**\n"
                f"Services discovered: {caps['discovered_services']}\n"
                f"Currently active: {caps['active_services']}\n"
                f"Operations available: {len(caps['can_handle'])}\n\n"
                f"Ask me what I can do for a detailed list!"
            )
        
        elif command_lower == '!services':
            services = list(self.claude.discovered_services.keys())
            if services:
                return f"**Discovered Services:**\n" + "\n".join(f"• {s}" for s in services)
            else:
                return "No services discovered yet. Services announce themselves via Bonjour."
        
        elif command_lower == '!status':
            status = self.get_status()
            return (
                f"**Bridge Status**\n"
                f"Messages processed: {status['messages_processed']}\n"
                f"Claude services: {status['claude_status']['discovered_services']}\n"
                f"Active services: {status['claude_status']['active_services']}"
            )
        
        else:
            # Not a command, process as regular message
            return await self.process_message(command)


# Create global bridge instance
discord_claude_bridge = DiscordClaudeBridge()


# Convenience function for Discord bot
async def ask_claude_from_discord(message: str) -> str:
    """Simple wrapper for Discord bots to use"""
    if message.startswith('!'):
        return await discord_claude_bridge.handle_command(message)
    else:
        return await discord_claude_bridge.process_message(message)


if __name__ == "__main__":
    import asyncio
    
    async def test_bridge():
        print("Testing Discord-Claude Bridge with Bonjour")
        print("=" * 50)
        
        # Test regular message
        response = await ask_claude_from_discord("What services are available?")
        print(f"Response: {response[:200]}...")
        
        # Test commands
        caps = await ask_claude_from_discord("!capabilities")
        print(f"\nCapabilities: {caps}")
        
        status = await ask_claude_from_discord("!status")
        print(f"\nStatus: {status}")
    
    asyncio.run(test_bridge())