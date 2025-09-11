#!/usr/bin/env python3
"""
claude_context.py - Dynamic context builder for Claude
Discovers available capabilities at runtime
"""
import os
import sys
import importlib
import inspect

def get_dynamic_context():
    """Build context dynamically based on what's available"""
    context = {
        'environment': 'Discord chat via tournament tracker',
        'role': 'FGC tournament assistant',
        'capabilities': []
    }
    
    # Check what modules are available
    available_modules = []
    
    try:
        import tournament_models
        available_modules.append('tournament_models - Database models')
        context['capabilities'].append('Can discuss tournaments, players, organizations')
    except:
        pass
    
    try:
        import polymorphic_queries
        available_modules.append('polymorphic_queries - Natural language queries')
        context['capabilities'].append('Can help with database queries')
    except:
        pass
    
    try:
        from database import get_session
        context['capabilities'].append('Database access available')
    except:
        pass
    
    # Build simple context string
    context_str = f"""You are a tournament tracker assistant. 
You're currently in Discord chat mode.
You can discuss FGC tournaments, players, and events.
When asked for data, explain what you would show and suggest relevant ./go.py commands.
Available: {', '.join(available_modules) if available_modules else 'Conversation mode only'}"""
    
    return context_str


def get_available_commands():
    """Return list of available go.py commands"""
    # This could parse go.py --help dynamically
    return [
        "./go.py --sync - Sync tournaments",
        "./go.py --console - Show rankings", 
        "./go.py --interactive - Enter REPL",
        "./go.py --discord-bot - Start this bot"
    ]