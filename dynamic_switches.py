#!/usr/bin/env python3
"""
Dynamic Switch Discovery - Modules announce their own go.py switches via bonjour

This replaces the ugly static switches.py with dynamic discovery where each
module announces what go.py flags it provides, just like they announce capabilities.

Example usage in a module:
    from dynamic_switches import announce_switch
    
    announce_switch(
        flag="--discord-bot", 
        help="START Discord bot service",
        module_path="networking.bonjour_discord",
        start_function="_discord_process_manager.start_services"
    )
"""

import argparse
from typing import List, Dict, Callable, Any
from polymorphic_core import announcer


class SwitchRegistry:
    """Registry where modules announce their go.py switches"""
    
    def __init__(self):
        self.switches = {}
        self.switch_handlers = {}
    
    def announce_switch(self, flag: str, help: str, handler: Callable, 
                       action: str = 'store_true', **kwargs):
        """
        Module announces a go.py switch it provides
        
        Args:
            flag: The command line flag (e.g. '--discord-bot')
            help: Help text for argparse
            handler: Function to call when flag is used
            action: argparse action type
            **kwargs: Additional argparse arguments
        """
        self.switches[flag] = {
            'help': help,
            'action': action,
            'handler': handler,
            **kwargs
        }
        
        # Also announce via bonjour so it shows up in --advertisements
        service_name = f"GoSwitch{flag.replace('-', '_').replace('--', '')}"
        announcer.announce(service_name, [
            f"Provides go.py flag: {flag}",
            f"Help: {help}",
            f"Handler: {handler.__name__ if hasattr(handler, '__name__') else str(handler)}"
        ])
    
    def build_parser(self) -> argparse.ArgumentParser:
        """Build argparse parser from announced switches"""
        parser = argparse.ArgumentParser(
            description='Service STARTER - Discovers switches via bonjour'
        )
        
        for flag, config in self.switches.items():
            parser.add_argument(flag, **{k: v for k, v in config.items() if k != 'handler'})
        
        return parser
    
    def handle_args(self, args):
        """Execute handlers for active flags"""
        for flag, config in self.switches.items():
            flag_name = flag.lstrip('-').replace('-', '_')
            if hasattr(args, flag_name) and getattr(args, flag_name):
                handler = config['handler']
                if callable(handler):
                    return handler(args)
                else:
                    # String handler - dynamic import and call
                    return self._execute_string_handler(handler, args)
    
    def _execute_string_handler(self, handler_string: str, args):
        """Execute a string-based handler like 'module.function'"""
        if '.' in handler_string:
            module_path, func_name = handler_string.rsplit('.', 1)
            module = __import__(module_path, fromlist=[func_name])
            func = getattr(module, func_name)
            return func(args) if callable(func) else func
        else:
            # Simple function name - try to find it
            import sys
            for module_name, module in sys.modules.items():
                if hasattr(module, handler_string):
                    func = getattr(module, handler_string)
                    return func(args) if callable(func) else func


# Global registry
switch_registry = SwitchRegistry()


def announce_switch(flag: str, help: str, handler: Callable, **kwargs):
    """Convenience function for modules to announce switches"""
    switch_registry.announce_switch(flag, help, handler, **kwargs)


def discover_switches() -> argparse.ArgumentParser:
    """Discover all announced switches and build parser"""
    # Import modules to trigger switch announcements
    try:
        # Import key modules to trigger their switch announcements
        import networking.bonjour_discord  # Discord switches
        import services.polymorphic_web_editor  # Web editor switches
        import tournament_domain.services.sync_service  # Sync switches
        import report_service  # Report switches
        import bridges.interactive_bridge  # Interactive switch
        import services.claude_cli_service  # AI switches
        import twilio_service  # Twilio switches
        import bonjour_service  # Bonjour switches
        import process_service  # Essential process switches
        import service_locator_cli  # Service locator management switches
        # Add more module imports here as they announce switches
    except ImportError as e:
        # Don't fail if modules aren't available
        pass
    
    return switch_registry.build_parser()


def handle_discovered_args(args):
    """Handle arguments from discovered switches"""
    return switch_registry.handle_args(args)


def list_discovered_switches() -> Dict[str, Any]:
    """List all discovered switches for debugging"""
    return switch_registry.switches