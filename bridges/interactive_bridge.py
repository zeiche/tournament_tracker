#!/usr/bin/env python3
"""
Interactive Bridge - Connects terminal input to various services
Polymorphically routes to lightweight, Ollama, or Claude based on what's available
"""

import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bridges.base_bridge import BaseBridge, BridgeRegistry
from polymorphic_core import announcer
from utils.dynamic_switches import announce_switch


class InteractiveBridge(BaseBridge):
    """Bridge terminal/stdin to various intelligence services"""
    
    def __init__(self, backend: str = "auto"):
        """
        Initialize interactive bridge.
        
        Args:
            backend: Which backend to use (lightweight, ollama, claude, auto)
        """
        # Determine backend
        self.backend = self._select_backend(backend)
        
        super().__init__(
            name=f"Interactive-{self.backend.title()} Bridge",
            source="Terminal",
            target=self.backend.title()
        )
        
        # Initialize the selected backend
        self.service = self._init_backend()
        
        # Register with bridge registry
        BridgeRegistry.register(self)
        
        # Additional announcement
        announcer.announce(self.name, [
            f"Interactive terminal bridge to {self.backend}",
            "Polymorphic - automatically selects best backend",
            "Type queries and get instant responses",
            "No configuration needed"
        ])
    
    def _select_backend(self, requested: str) -> str:
        """Select which backend to use"""
        requested = requested.lower()
        
        if requested == "auto":
            # Try in order of speed/simplicity
            try:
                from utils.database_service import DatabaseService
                return "lightweight"
            except:
                pass
            
            
            try:
                from claude.services.claude_service import ClaudeService
                return "claude"
            except:
                pass
            
            raise RuntimeError("No backend available!")
        
        elif requested in ["lightweight", "light", "db", "database"]:
            return "lightweight"
        elif requested in ["claude", "anthropic"]:
            return "claude"
        else:
            return "lightweight"  # Default
    
    def _init_backend(self):
        """Initialize the selected backend service"""
        if self.backend == "lightweight":
            from utils.database_service import DatabaseService
            from services.startgg_sync import StartGGSync
            # Return a dict with both services for lightweight
            return {
                "db": DatabaseService(),
                "sync": StartGGSync()
            }
        
        elif self.backend == "ollama":
            from ollama_bonjour import get_ollama_bonjour
            return get_ollama_bonjour()
        
        elif self.backend == "claude":
            from claude.services.claude_service import ClaudeService
            return ClaudeService()
        
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    async def process(self, message: str, **kwargs) -> str:
        """Process a message through the selected backend"""
        message = message.strip()
        message_lower = message.lower()
        
        self.message_count += 1
        
        # Handle based on backend
        if self.backend == "lightweight":
            # Lightweight processing (same as lightweight_bonjour.py)
            db = self.service["db"]
            sync = self.service["sync"]
            
            # Special commands
            if 'sync' in message_lower:
                result = sync.do('sync tournaments')
                return f"Sync complete: {result}"
            
            elif message_lower in ['help', '?', 'help me', 'what can you do']:
                return """I understand:
• top players / rankings / leaderboard
• recent tournaments
• player [name]
• tournament [id]
• all / everything
• stats
• sync"""
            
            # Everything else goes to database
            else:
                try:
                    result = db.ask(message)
                    if result:
                        return db.tell('discord', result)
                    else:
                        return "No results found. Try 'help' for examples."
                except Exception as e:
                    return f"Error: {str(e)}\nTry 'help' for examples."
        
        elif self.backend == "ollama":
            # Ollama processing
            response = self.service.ask(message)
            return response if response else "No response from Ollama"
        
        elif self.backend == "claude":
            # Claude processing
            response = self.service.ask(message)
            return response if response else "No response from Claude"
        
        else:
            return f"Backend {self.backend} not implemented"
    
    def run_interactive(self):
        """Run in interactive mode with stdin/stdout"""
        print("\n" + "="*60)
        print(f"🌉 Interactive Bridge - {self.backend.title()} Backend")
        print("="*60)
        
        # Backend-specific info
        if self.backend == "lightweight":
            print("⚡ Using lightweight intelligence (no LLM)")
            print("📊 Direct database queries - instant responses")
        elif self.backend == "ollama":
            print("🤖 Using Ollama (local LLM)")
        elif self.backend == "claude":
            print("🧠 Using Claude (Anthropic)")
        
        print("\nType 'help' for commands, 'quit' to exit\n")
        
        # Check if we have stdin
        if not sys.stdin.isatty():
            print("🔧 Running in service mode (no stdin detected)")
            print("📡 Bridge is listening...")
            
            # Keep running as service
            import time
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\n👋 Shutting down")
            return
        
        # Interactive loop
        prompt = "⚡ > " if self.backend == "lightweight" else "🌉 > "
        
        while True:
            try:
                query = input(prompt)
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Process synchronously (convert async to sync)
                import asyncio
                response = asyncio.run(self.process(query))
                print(response)
                print()  # Blank line for readability
                
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\n👋 Goodbye!")


def start_interactive_service(args=None):
    """Handler for --interactive switch"""
    backend = "auto"  # default
    
    if hasattr(args, 'interactive') and args.interactive:
        backend = args.interactive
    
    print(f"Starting interactive bridge with backend: {backend}")
    
    try:
        bridge = InteractiveBridge(backend=backend)
        bridge.run_interactive()
    except Exception as e:
        print(f"Interactive bridge failed: {e}")


announce_switch(
    flag="--interactive",
    help="START interactive bridge/repl (auto|lightweight|claude)",
    handler=start_interactive_service,
    action="store",
    nargs="?",
    const="auto",
    metavar="BACKEND"
)


# Make it runnable directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Interactive Bridge - Terminal to services"
    )
    parser.add_argument(
        '--backend',
        default='auto',
        choices=['auto', 'lightweight', 'ollama', 'claude'],
        help='Which backend to use (default: auto)'
    )
    
    args = parser.parse_args()
    
    bridge = InteractiveBridge(backend=args.backend)
    bridge.run_interactive()