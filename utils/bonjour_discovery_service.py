#!/usr/bin/env python3
"""
bonjour_discovery_service.py - Dynamic command discovery service
This service listens to announcements and builds a dynamic list of available commands.
"""
import sys
import argparse
from polymorphic_core import announcer, list_capabilities
from bonjour_monitor import BonjourMonitor
from typing import Dict, List, Any, Optional

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.bonjour_discovery_service")


class DynamicCommandDiscovery:
    """
    Discovers available commands by listening to service announcements.
    """
    
    def __init__(self):
        self.available_commands = {}
        self.available_services = {}
        
        # Announce ourselves
        announcer.announce(
            "Dynamic Command Discovery",
            [
                "I discover available commands automatically",
                "Services announce their commands to me",
                "I provide a dynamic help system",
                "I route commands to the right services"
            ],
            ["discovery --list", "discovery --help", "discovery --run <command>"]
        )
        
        # Register as a listener
        announcer.add_listener(self._on_announcement)
    
    def _on_announcement(self, service_name: str, capabilities: List[str], examples: Optional[List[str]] = None):
        """Process service announcements to discover commands"""
        
        # Look for command patterns in capabilities
        for capability in capabilities:
            if "command:" in capability.lower():
                # Extract command name
                command_name = capability.split("command:")[-1].strip()
                self.available_commands[command_name] = {
                    'service': service_name,
                    'description': capability
                }
            
            # Look for service status announcements
            if "service" in service_name.lower():
                self.available_services[service_name] = {
                    'capabilities': capabilities,
                    'examples': examples or []
                }
    
    def list_commands(self):
        """List all discovered commands"""
        print("\n🔍 DISCOVERED COMMANDS")
        print("="*60)
        
        if not self.available_commands:
            print("No commands discovered yet. Services need to announce themselves.")
            return
        
        for command, info in sorted(self.available_commands.items()):
            print(f"  {command:20} - {info['service']}")
            print(f"    {info['description']}")
        
        print("\n📡 AVAILABLE SERVICES")
        print("-"*60)
        
        for service, info in sorted(self.available_services.items()):
            print(f"\n  {service}")
            for cap in info['capabilities'][:3]:  # First 3 capabilities
                print(f"    • {cap}")
    
    def show_dynamic_help(self):
        """Show dynamically discovered help"""
        print("\n🎯 DYNAMIC HELP - Based on Current System State")
        print("="*60)
        
        # Get current capabilities
        caps = list_capabilities()
        
        if caps['models']:
            print("\n📊 Data Models Available:")
            for model in caps['models']:
                print(f"  • {model}")
        
        if caps['services']:
            print("\n🔧 Services Available:")
            for service in caps['services']:
                print(f"  • {service}")
        
        if caps['functions']:
            print("\n🎨 Function Categories:")
            for category in caps['functions']:
                print(f"  • {category}")
        
        print("\n💡 The system discovers capabilities automatically.")
        print("   Services announce themselves when they start.")
        print("   Run 'bonjour_monitor.py live' to see announcements.")
    
    def discover_and_run(self, command: str, args: List[str]):
        """
        Discover which service can handle a command and run it.
        This is the ultimate polymorphic command routing.
        """
        # Announce we're looking for a handler
        announcer.announce(
            "Command Router",
            [f"Looking for handler for: {command}"],
            [f"Args: {args}"]
        )
        
        # Check if any service has announced this capability
        if command in self.available_commands:
            service = self.available_commands[command]['service']
            print(f"✅ Command '{command}' handled by {service}")
            
            # In a real implementation, we'd invoke the service here
            # For now, we'll just show what would happen
            print(f"   Would execute: {service}.{command}({args})")
        else:
            print(f"❌ No service has announced capability for '{command}'")
            print("   Available commands:")
            for cmd in self.available_commands:
                print(f"     • {cmd}")


def announce_go_commands():
    """
    Announce all the commands that go.py knows about.
    This makes them discoverable.
    """
    commands = {
        '--discord-bot': 'Start Discord bot service',
        '--edit-contacts': 'Start web editor service',
        '--ai-chat': 'Start AI chat service',
        '--sync': 'Sync tournaments from start.gg',
        '--console': 'Show console report',
        '--heatmap': 'Generate heat maps',
        '--stats': 'Show database statistics',
        '--voice-test': 'Test voice capabilities',
        '--twilio-bridge': 'Start Twilio bridge',
        '--call': 'Make outbound call',
        '--bonjour-monitor': 'Start announcement monitor',
        '--discover': 'Show discovered commands'
    }
    
    for command, description in commands.items():
        announcer.announce(
            "go.py Command",
            [f"Command: {command}", description]
        )


def main():
    """Run the discovery service"""
    parser = argparse.ArgumentParser(description='Dynamic Command Discovery')
    parser.add_argument('--list', action='store_true', help='List discovered commands')
    parser.add_argument('--help-dynamic', action='store_true', help='Show dynamic help')
    parser.add_argument('--announce-go', action='store_true', help='Announce go.py commands')
    parser.add_argument('--monitor', action='store_true', help='Monitor announcements')
    parser.add_argument('--run', nargs='+', help='Discover and run a command')
    
    args = parser.parse_args()
    
    discovery = DynamicCommandDiscovery()
    
    if args.announce_go:
        announce_go_commands()
        print("✅ Announced all go.py commands")
    
    if args.list:
        discovery.list_commands()
    
    elif args.help_dynamic:
        discovery.show_dynamic_help()
    
    elif args.monitor:
        monitor = BonjourMonitor()
        monitor.start_live_monitor()
    
    elif args.run:
        command = args.run[0]
        command_args = args.run[1:] if len(args.run) > 1 else []
        discovery.discover_and_run(command, command_args)
    
    else:
        # Default: show what's available
        discovery.list_commands()
        discovery.show_dynamic_help()


if __name__ == "__main__":
    main()