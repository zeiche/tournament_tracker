#!/usr/bin/env python3
"""
supercharged_logger_polymorphic.py - Logger using the 3-method database pattern
Shows how the polymorphic database simplifies the logger implementation.
"""
import sys
import traceback
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from collections import deque, Counter
from threading import Lock

from polymorphic_core import announcer
from utils.database_service_polymorphic import database_service


class SuperchargedLoggerPolymorphic:
    """
    A logger that uses the polymorphic database service.
    Much simpler than the original with 20+ query methods.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Thread-safe singleton"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the polymorphic logger"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._context_stack = []
        self._correlation_id = None
        self._buffer = deque(maxlen=100)
        self._stats = Counter()
        
        # Announce ourselves
        announcer.announce(
            "Polymorphic Logger",
            [
                "Simplified logger using 3-method database pattern",
                "No more complex queries - just ask(), tell(), do()",
                "Natural language log queries",
                "Automatic context tracking"
            ],
            [
                "logger.log('info', 'Something happened')",
                "logger.ask('errors in last hour')",
                "logger.tell('discord', recent_logs)"
            ]
        )
    
    def log(self, level: str, message: str, **kwargs) -> None:
        """
        Log a message with the polymorphic database
        """
        log_entry = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now(),
            'level': level,
            'message': message,
            'correlation_id': self._correlation_id,
            'context': self._get_context(),
            **kwargs
        }
        
        # Store in database using polymorphic pattern
        database_service.do(f"create log entry", data=log_entry)
        
        # Update stats
        self._stats[level] += 1
        
        # Announce significant events
        if level in ['error', 'critical']:
            announcer.announce(
                "Logger Alert",
                [f"{level.upper()}: {message[:100]}"]
            )
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.log('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.log('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with traceback"""
        kwargs['traceback'] = traceback.format_exc()
        self.log('error', message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.log('debug', message, **kwargs)
    
    def ask(self, query: str) -> Any:
        """
        Query logs using natural language
        Examples:
            ask("errors in last hour")
            ask("logs from tournament sync")
            ask("warnings about database")
            ask("logs with correlation id abc123")
        """
        # The database service interprets the query
        logs = database_service.ask(f"logs {query}")
        
        # If we got log entries, format them nicely
        if isinstance(logs, list):
            return [self._format_log(log) for log in logs]
        return logs
    
    def tell(self, format: str, logs: Optional[List] = None) -> str:
        """
        Format logs for output
        Examples:
            tell("discord")  # Recent logs for Discord
            tell("summary")  # Summary statistics
            tell("errors")   # Recent errors formatted
        """
        if logs is None:
            # Get appropriate logs based on format
            if "error" in format.lower():
                logs = self.ask("errors in last hour")
            elif "summary" in format.lower() or "stats" in format.lower():
                return self._format_stats()
            else:
                logs = self.ask("recent 20 logs")
        
        # Format the logs
        if "discord" in format.lower():
            return self._format_for_discord(logs)
        elif "json" in format.lower():
            return json.dumps(logs, default=str, indent=2)
        else:
            return "\n".join([str(log) for log in logs])
    
    def search(self, text: str) -> List[Dict]:
        """
        Search logs for text - simplified version
        """
        return self.ask(f"containing '{text}'")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get logger statistics - simplified version
        """
        stats = database_service.ask("log statistics")
        return {
            'counts_by_level': dict(self._stats),
            'database_stats': stats,
            'buffer_size': len(self._buffer)
        }
    
    def cleanup(self, days: int = 7) -> None:
        """
        Clean up old logs - simplified version
        """
        result = database_service.do(f"delete logs older than {days} days")
        self.info(f"Cleanup completed: {result}")
    
    @contextmanager
    def context(self, **kwargs):
        """Context manager for adding context to logs"""
        self._context_stack.append(kwargs)
        try:
            yield
        finally:
            self._context_stack.pop()
    
    @contextmanager
    def correlation(self, correlation_id: Optional[str] = None):
        """Context manager for correlation IDs"""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        old_id = self._correlation_id
        self._correlation_id = correlation_id
        try:
            yield correlation_id
        finally:
            self._correlation_id = old_id
    
    def _get_context(self) -> Dict:
        """Get current context"""
        context = {}
        for ctx in self._context_stack:
            context.update(ctx)
        return context
    
    def _format_log(self, log: Any) -> Dict:
        """Format a log entry"""
        if hasattr(log, '__dict__'):
            return log.__dict__
        if isinstance(log, dict):
            return log
        return {'message': str(log)}
    
    def _format_for_discord(self, logs: List) -> str:
        """Format logs for Discord output"""
        if not logs:
            return "No logs found"
        
        output = ["📋 **Recent Logs**\n"]
        for log in logs[:10]:  # Limit to 10 for Discord
            if isinstance(log, dict):
                level = log.get('level', 'info')
                message = log.get('message', '')
                timestamp = log.get('timestamp', '')
                
                # Use emoji for level
                emoji = {
                    'debug': '🔍',
                    'info': '📘',
                    'warning': '⚠️',
                    'error': '❌',
                    'critical': '🚨'
                }.get(level, '📝')
                
                output.append(f"{emoji} {timestamp} - {message[:100]}")
            else:
                output.append(f"• {str(log)[:100]}")
        
        return "\n".join(output)
    
    def _format_stats(self) -> str:
        """Format statistics"""
        stats = self.get_statistics()
        output = ["📊 **Logger Statistics**\n"]
        
        # Level counts
        for level, count in stats.get('counts_by_level', {}).items():
            output.append(f"{level}: {count}")
        
        return "\n".join(output)


# Global instance
logger = SuperchargedLoggerPolymorphic()


# Convenience functions
def info(message: str, **kwargs):
    """Log info message"""
    logger.info(message, **kwargs)

def warning(message: str, **kwargs):
    """Log warning message"""
    logger.warning(message, **kwargs)

def error(message: str, **kwargs):
    """Log error message"""
    logger.error(message, **kwargs)

def debug(message: str, **kwargs):
    """Log debug message"""
    logger.debug(message, **kwargs)


# Example usage showing the simplicity
if __name__ == "__main__":
    # Log some messages
    logger.info("Starting application")
    logger.warning("This is a warning")
    logger.error("Something went wrong!")
    
    # Query logs naturally
    recent_errors = logger.ask("errors in last hour")
    print(f"Found {len(recent_errors)} recent errors")
    
    # Format for output
    discord_output = logger.tell("discord")
    print(discord_output)
    
    # Get statistics
    stats = logger.tell("stats")
    print(stats)
    
    # Search logs
    results = logger.search("database")
    print(f"Found {len(results)} logs mentioning 'database'")