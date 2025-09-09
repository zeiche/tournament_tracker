#!/usr/bin/env python3
"""
claude/interactive.py - Async interactive Claude with Bonjour discovery

This provides an interactive REPL where you can:
1. Talk to Claude naturally
2. Claude uses discovered services to answer
3. Services announce themselves in real-time
4. Everything is async for responsiveness
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import aioconsole
from typing import Optional, Dict, Any
from datetime import datetime
from claude.services.claude_bonjour_service import claude_bonjour
from polymorphic_core import announcer
import json


class AsyncClaudeInteractive:
    """
    Async interactive Claude interface with live Bonjour discovery.
    """
    
    def __init__(self):
        self.claude = claude_bonjour
        self.running = False
        self.command_history = []
        self.announcement_queue = asyncio.Queue()
        
        # Register to receive announcements
        announcer.add_listener(self._on_announcement)
        
        # Announce ourselves
        announcer.announce(
            "Claude Interactive Mode",
            [
                "Natural language conversation with Claude",
                "Live service discovery via Bonjour",
                "Async processing for responsiveness",
                "Services announce as they start",
                "Type 'help' for commands"
            ]
        )
    
    def _on_announcement(self, service_name: str, capabilities: list, examples: list = None):
        """Called when services announce - queue for async display"""
        if self.running and "Claude" not in service_name:
            # Queue announcement for async display
            asyncio.create_task(self.announcement_queue.put({
                'service': service_name,
                'capabilities': len(capabilities),
                'timestamp': datetime.now()
            }))
    
    async def display_announcements(self):
        """Background task to display service announcements"""
        while self.running:
            try:
                announcement = await asyncio.wait_for(
                    self.announcement_queue.get(), 
                    timeout=1.0
                )
                
                # Display announcement in a non-intrusive way
                print(f"\n📡 [Service Discovered: {announcement['service']} "
                      f"with {announcement['capabilities']} capabilities]")
                print("claude> ", end="", flush=True)  # Restore prompt
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                pass  # Silent fail for announcements
    
    async def process_command(self, command: str) -> Optional[str]:
        """
        Process special commands or return None for Claude to handle.
        
        Commands:
            /help - Show available commands
            /services - List discovered services
            /capabilities - Show Claude's current capabilities
            /context - Show current context
            /clear - Clear screen
            /quit - Exit interactive mode
        """
        command_lower = command.lower().strip()
        
        if command_lower in ['/help', 'help']:
            return """
🤖 Claude Interactive Mode - Commands:

Natural Language:
  Just type normally and Claude will respond using discovered services.

Special Commands:
  /services     - List all discovered services
  /capabilities - Show what Claude can currently do
  /context      - Display Claude's current context
  /history      - Show conversation history
  /clear        - Clear the screen
  /quit         - Exit interactive mode

Examples:
  "What tournaments happened last month?"
  "Show me top 10 players"
  "How do I edit organization names?"
  
Services announce themselves as they start, so Claude's abilities grow!
"""
        
        elif command_lower == '/services':
            services = list(self.claude.discovered_services.keys())
            if services:
                result = "📡 Discovered Services:\n"
                for service in services:
                    svc = self.claude.discovered_services[service]
                    fresh = "✅" if svc.is_fresh() else "⏸️"
                    result += f"  {fresh} {service} ({len(svc.capabilities)} capabilities)\n"
                return result
            else:
                return "No services discovered yet. Start services with ./go.py commands."
        
        elif command_lower == '/capabilities':
            caps = self.claude.get_conversation_capabilities()
            return f"""
🎯 Claude's Current Capabilities:
  • Services discovered: {caps['discovered_services']}
  • Currently active: {caps['active_services']}
  • Available patterns: {', '.join(caps['available_patterns'][:10])}
  • Can handle {len(caps['can_handle'])} different operations

Type /services for details or just ask me what I can do!
"""
        
        elif command_lower == '/context':
            context = self.claude.get_dynamic_context()
            return f"📝 Current Context:\n{context[:1000]}..."
        
        elif command_lower == '/history':
            if self.command_history:
                return "📜 Recent Commands:\n" + "\n".join(
                    f"  {i+1}. {cmd[:80]}" 
                    for i, cmd in enumerate(self.command_history[-10:])
                )
            else:
                return "No command history yet."
        
        elif command_lower == '/clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            return "Screen cleared."
        
        elif command_lower in ['/quit', 'quit', 'exit']:
            self.running = False
            return "Goodbye! 👋"
        
        else:
            # Not a command, let Claude handle it
            return None
    
    async def ask_claude_async(self, message: str) -> str:
        """Ask Claude asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Run the synchronous Claude call in executor
        result = await loop.run_in_executor(
            None,
            self.claude.ask_with_discovery,
            message
        )
        
        if result['success']:
            response = result['response']
            
            # Add metadata if services were used
            if result.get('relevant_services'):
                services = result['relevant_services'][:3]
                response += f"\n\n[Used: {', '.join(services)}]"
            
            return response
        else:
            return f"Error: {result.get('error', 'Unknown error')}"
    
    async def run(self):
        """Main async interactive loop"""
        self.running = True
        
        print("=" * 60)
        print("🤖 Claude Interactive Mode - Async with Bonjour Discovery")
        print("=" * 60)
        print()
        print("I'm Claude, enhanced with dynamic service discovery.")
        print("As services start, I automatically learn what they can do!")
        print()
        print("Type 'help' for commands or just chat naturally.")
        print("Services will announce themselves as they start.")
        print()
        
        # Start background announcement display
        announcement_task = asyncio.create_task(self.display_announcements())
        
        try:
            while self.running:
                # Get input asynchronously
                try:
                    user_input = await aioconsole.ainput("claude> ")
                except EOFError:
                    break
                
                if not user_input.strip():
                    continue
                
                # Add to history
                self.command_history.append(user_input)
                
                # Check for special commands
                command_result = await self.process_command(user_input)
                
                if command_result is not None:
                    # It was a command, display result
                    print(command_result)
                else:
                    # Send to Claude
                    print("🤔 Thinking...", end="", flush=True)
                    
                    try:
                        response = await self.ask_claude_async(user_input)
                        print("\r" + " " * 20 + "\r", end="")  # Clear "Thinking..."
                        print(f"\n{response}\n")
                    except Exception as e:
                        print(f"\r❌ Error: {e}\n")
                
                # Check if we should exit
                if not self.running:
                    break
        
        finally:
            # Cancel background task
            announcement_task.cancel()
            try:
                await announcement_task
            except asyncio.CancelledError:
                pass
            
            print("\n👋 Thanks for chatting!")


async def main():
    """Entry point for interactive mode"""
    interactive = AsyncClaudeInteractive()
    await interactive.run()


def run_interactive():
    """Synchronous wrapper for go.py to call"""
    try:
        # Check if aioconsole is available
        import aioconsole
    except ImportError:
        print("Installing aioconsole for async interactive mode...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "aioconsole"])
        import aioconsole
    
    # Run the async interactive mode
    asyncio.run(main())


if __name__ == "__main__":
    run_interactive()