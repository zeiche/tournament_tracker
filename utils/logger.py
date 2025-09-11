#!/usr/bin/env python3
"""
logger.py - Clean, simple logger using 3-method pattern
"""
import sys
import traceback
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from threading import Lock

from utils.database_service_polymorphic import database_service


class Logger:
    """
    Clean logger using the 3-method pattern: ask(), tell(), do()
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce after init to avoid circular imports
        try:
            from polymorphic_core import announcer
            announcer.announce(
                "Logger",
                [
                    "Simple logging with ask(), tell(), do() pattern",
                    "Database-backed log storage", 
                    "Natural language log queries"
                ]
            )
        except ImportError:
            pass  # Skip announcement if circular import
    
    def ask(self, query: str) -> Any:
        """
        Query logs using natural language
        Examples:
            ask("errors today")
            ask("logs from sync")  
            ask("recent warnings")
        """
        return database_service.ask(f"logs {query}")
    
    def tell(self, format: str, logs: Optional[List] = None) -> str:
        """
        Format logs for output
        Examples:
            tell("discord")
            tell("json")
            tell("summary")
        """
        if logs is None:
            logs = self.ask("recent 10")
        
        if "discord" in format.lower():
            return self._format_discord(logs)
        elif "json" in format.lower():
            return json.dumps(logs, default=str, indent=2)
        else:
            return "\n".join([str(log) for log in logs])
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform logging actions
        Examples:
            do("log info message")
            do("log error Something failed")
            do("cleanup old logs")
        """
        action = action.lower().strip()
        
        if action.startswith("log "):
            parts = action[4:].split(" ", 1)
            if len(parts) == 2:
                level, message = parts
                return self._create_log(level, message, **kwargs)
        
        elif "cleanup" in action:
            return database_service.do("delete old logs")
        
        return f"Unknown action: {action}"
    
    def _create_log(self, level: str, message: str, **kwargs):
        """Create a log entry"""
        log_entry = {
            'timestamp': datetime.now(),
            'level': level.upper(),
            'message': message,
            'module': self._get_caller_module(),
            **kwargs
        }
        
        database_service.do("create log", data=log_entry)
        
        # Announce errors (try to import announcer if available)
        if level.upper() in ['ERROR', 'CRITICAL']:
            try:
                from polymorphic_core import announcer
                announcer.announce("Log Error", [f"{level.upper()}: {message}"])
            except ImportError:
                pass  # Skip announcement if not available
    
    def _get_caller_module(self) -> str:
        """Get calling module name"""
        frame = sys._getframe(3)
        return frame.f_globals.get('__name__', 'unknown')
    
    def _format_discord(self, logs: List) -> str:
        """Format logs for Discord"""
        if not logs:
            return "No logs found"
        
        output = ["📋 **Logs**"]
        for log in logs[:5]:
            if isinstance(log, dict):
                level = log.get('level', 'info')
                message = log.get('message', '')
                emoji = {'DEBUG': '🔍', 'INFO': '📘', 'WARNING': '⚠️', 
                        'ERROR': '❌', 'CRITICAL': '🚨'}.get(level, '📝')
                output.append(f"{emoji} {message[:100]}")
        
        return "\n".join(output)


# Global instance
logger = Logger()


# Convenience functions
def info(message: str, **kwargs):
    logger.do(f"log info {message}", **kwargs)

def warning(message: str, **kwargs):
    logger.do(f"log warning {message}", **kwargs)

def error(message: str, **kwargs):
    kwargs['traceback'] = traceback.format_exc()
    logger.do(f"log error {message}", **kwargs)

def debug(message: str, **kwargs):
    logger.do(f"log debug {message}", **kwargs)