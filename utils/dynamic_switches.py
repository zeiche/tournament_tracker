#!/usr/bin/env python3
"""
Dynamic Switch Discovery - Modules announce their own go.py switches via bonjour

This replaces the ugly static switches.py with dynamic discovery where each
module announces what go.py flags it provides, just like they announce capabilities.

Example usage in a module:
    from utils.dynamic_switches import announce_switch
    
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

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.dynamic_switches")


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
            if hasattr(args, flag_name):
                value = getattr(args, flag_name)

                # Handle different argument types:
                # - store_true: value is True/False
                # - store with nargs='*': value is [] or [items...]
                # - store: value is the stored value or None
                should_execute = False
                if config.get('action') == 'store_true' and value:
                    should_execute = True
                elif config.get('nargs') == '*' and value is not None:
                    should_execute = True  # Execute even for empty list
                elif config.get('nargs') == '?' and value is not None:
                    should_execute = True  # Execute for optional arguments with const value
                elif value:
                    should_execute = True

                if should_execute:
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
    modules_to_import = [
        "networking.bonjour_discord",
        "services.polymorphic_web_editor", 
        "services.startgg_sync",
        "services.report_service",
        "bridges.interactive_bridge",
        "services.claude_cli_service",
        "twilio.twilio_service_refactored",
        "networking.bonjour_service",
        "services.process_service", 
        "utils.service_locator_cli",
        "services.polymorphic_web_editor_refactored",
        "services.interactive_service_refactored",
        "services.report_service_refactored", 
        "services.process_service_refactored",
        "services.claude_cli_service_refactored",
        "analytics.analytics_service_refactored",
        "logging_services.polymorphic_log_manager",
        "tournament_domain.services.sync_service",
        "utils.webdav_refactored_switch",
        "utils.webdav_bonjour_switch"
    ]
    
    for module_name in modules_to_import:
        try:
            __import__(module_name)
        except ImportError as e:
            # Skip modules that aren't available - this is expected
            continue
    
    return switch_registry.build_parser()


def handle_discovered_args(args):
    """Handle arguments from discovered switches"""
    return switch_registry.handle_args(args)


def list_discovered_switches() -> Dict[str, Any]:
    """List all discovered switches for debugging"""
    return switch_registry.switches