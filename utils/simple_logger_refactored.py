#!/usr/bin/env python3
"""
simple_logger_refactored.py - REFACTORED Logger service using service locator

BEFORE: Simple function-based logging
AFTER: Service-based logging with 3-method pattern and service locator

Key changes:
1. Converted to service class with ask/tell/do methods
2. Uses service locator for config and error handling dependencies  
3. Supports both local and network operation
4. Maintains backward compatibility with function interface
5. Can be distributed across network for centralized logging

This demonstrates refactoring utility services to the new pattern.
"""
import sys
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.simple_logger_refactored")
import json

from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service

class RefactoredLoggerService:
    """
    REFACTORED Logger service using service locator pattern.
    
    This version:
    - Uses service locator for dependencies (config, error handler)
    - Follows 3-method pattern (ask/tell/do)
    - Can operate over network for distributed logging
    - Maintains simple interface for backward compatibility
    """
    
    _instance: Optional['RefactoredLoggerService'] = None
    
    def __new__(cls, prefer_network: bool = False) -> 'RefactoredLoggerService':
        """Singleton pattern with service preference"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.prefer_network = prefer_network
            cls._instance._config = None
            cls._instance._error_handler = None
            cls._instance.log_history = []  # Store recent logs
            cls._instance.max_history = 1000  # Configurable
            
            # Announce ourselves
            announcer.announce(
                "Logger Service (Refactored)",
                [
                    "REFACTORED: Uses service locator for dependencies",
                    "Distributed logging with 3-method pattern",
                    "ask('recent logs') - get log history",
                    "tell('json', logs) - format log output",
                    "do('log info message') - log messages",
                    "Backward compatible with function interface"
                ],
                [
                    "logger.ask('last 10 errors')",
                    "logger.tell('discord', log_data)",
                    "logger.do('log error Something failed')",
                    "logger.info('Still works like before')"
                ]
            )
        return cls._instance
    
    @property
    def config(self):
        """Lazy-loaded config service via service locator"""
        if self._config is None:
            self._config = get_service("config", self.prefer_network)
        return self._config
    
    @property
    def error_handler(self):
        """Lazy-loaded error handler service via service locator"""
        if self._error_handler is None:
            self._error_handler = get_service("error_handler", self.prefer_network)
        return self._error_handler
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query log data using natural language.
        
        Examples:
            ask("recent logs")
            ask("last 10 errors")
            ask("logs from today")
            ask("warning messages")
            ask("log stats")
        """
        query_lower = query.lower().strip()
        
        try:
            if "recent logs" in query_lower or "recent" in query_lower:
                limit = self._extract_number(query, default=50)
                return self._get_recent_logs(limit)
            
            elif "error" in query_lower:
                limit = self._extract_number(query, default=20)
                return self._get_logs_by_level("ERROR", limit)
            
            elif "warning" in query_lower:
                limit = self._extract_number(query, default=20)
                return self._get_logs_by_level("WARN", limit)
            
            elif "info" in query_lower:
                limit = self._extract_number(query, default=20)
                return self._get_logs_by_level("INFO", limit)
            
            elif "stats" in query_lower:
                return self._get_log_stats()
            
            elif "today" in query_lower:
                return self._get_logs_from_today()
            
            else:
                return {"error": f"Don't know how to handle query: {query}"}
                
        except Exception as e:
            return {"error": f"Log query failed: {str(e)}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """
        Format log data for output.
        
        Formats: json, discord, text, csv, html
        """
        if data is None:
            data = {}
        
        try:
            if format_type == "json":
                return json.dumps(data, indent=2, default=str)
            
            elif format_type == "discord":
                return self._format_discord(data)
            
            elif format_type == "text":
                return self._format_text(data)
            
            elif format_type == "csv":
                return self._format_csv(data)
            
            elif format_type == "html":
                return self._format_html(data)
            
            else:
                return str(data)
                
        except Exception as e:
            return f"Format error: {e}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform logging operations using natural language.
        
        Examples:
            do("log info Started processing")
            do("log error Database connection failed")
            do("log warning Memory usage high")
            do("clear history")
            do("set max history 500")
        """
        action_lower = action.lower().strip()
        
        try:
            if action_lower.startswith("log "):
                return self._handle_log_command(action)
            
            elif "clear history" in action_lower:
                return self._clear_history()
            
            elif "set max history" in action_lower:
                max_val = self._extract_number(action)
                return self._set_max_history(max_val)
            
            else:
                return {"error": f"Don't know how to: {action}"}
                
        except Exception as e:
            return {"error": f"Log action failed: {str(e)}"}
    
    # Backward compatibility methods
    def info(self, message: str, **kwargs):
        """Log info message (backward compatible)"""
        return self._log('INFO', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message (backward compatible)"""
        return self._log('WARN', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message (backward compatible)"""
        return self._log('ERROR', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message (backward compatible)"""
        return self._log('DEBUG', message, **kwargs)
    
    # Core logging implementation
    def _log(self, level: str, message: str, **kwargs):
        """Core logging function with history tracking"""
        timestamp = datetime.now()
        caller = sys._getframe(2).f_globals.get('__name__', 'unknown')
        
        # Create log entry
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "caller": caller,
            "message": message,
            "kwargs": kwargs
        }
        
        # Add to history
        self.log_history.append(log_entry)
        
        # Trim history if too long
        if len(self.log_history) > self.max_history:
            self.log_history = self.log_history[-self.max_history:]
        
        # Console output (same as before)
        time_str = timestamp.strftime("%H:%M:%S")
        print(f"[{time_str}] {level} {caller}: {message}")
        
        # Use discovered error handler for critical errors
        if level == "ERROR" and self.error_handler:
            try:
                self.error_handler.handle_exception(Exception(message), "MEDIUM")
            except:
                pass  # Don't fail if error handler unavailable
        
        return log_entry
    
    # Query implementation methods
    def _get_recent_logs(self, limit: int) -> Dict:
        """Get recent log entries"""
        recent = self.log_history[-limit:] if limit < len(self.log_history) else self.log_history
        return {
            "logs": recent,
            "count": len(recent),
            "total_history": len(self.log_history)
        }
    
    def _get_logs_by_level(self, level: str, limit: int) -> Dict:
        """Get logs filtered by level"""
        filtered = [log for log in self.log_history if log["level"] == level]
        limited = filtered[-limit:] if limit < len(filtered) else filtered
        return {
            "logs": limited,
            "level": level,
            "count": len(limited),
            "total_level": len(filtered)
        }
    
    def _get_log_stats(self) -> Dict:
        """Get logging statistics"""
        stats = {"total": len(self.log_history)}
        
        for level in ["INFO", "WARN", "ERROR", "DEBUG"]:
            count = len([log for log in self.log_history if log["level"] == level])
            stats[level.lower()] = count
        
        return stats
    
    def _get_logs_from_today(self) -> Dict:
        """Get logs from today"""
        today = datetime.now().date()
        today_logs = []
        
        for log in self.log_history:
            log_date = datetime.fromisoformat(log["timestamp"]).date()
            if log_date == today:
                today_logs.append(log)
        
        return {
            "logs": today_logs,
            "date": today.isoformat(),
            "count": len(today_logs)
        }
    
    # Action implementation methods
    def _handle_log_command(self, action: str) -> Dict:
        """Handle 'log LEVEL message' commands"""
        parts = action.split(" ", 2)
        if len(parts) < 3:
            return {"error": "Invalid log command format. Use: log LEVEL message"}
        
        level = parts[1].upper()
        message = parts[2]
        
        if level not in ["INFO", "WARN", "ERROR", "DEBUG"]:
            return {"error": f"Invalid log level: {level}"}
        
        log_entry = self._log(level, message)
        return {"action": "logged", "entry": log_entry}
    
    def _clear_history(self) -> Dict:
        """Clear log history"""
        old_count = len(self.log_history)
        self.log_history.clear()
        return {"action": "cleared", "removed_entries": old_count}
    
    def _set_max_history(self, max_val: int) -> Dict:
        """Set maximum history size"""
        if max_val <= 0:
            return {"error": "Max history must be positive"}
        
        old_max = self.max_history
        self.max_history = max_val
        
        # Trim current history if needed
        if len(self.log_history) > max_val:
            self.log_history = self.log_history[-max_val:]
        
        return {
            "action": "set_max_history",
            "old_max": old_max,
            "new_max": max_val,
            "current_entries": len(self.log_history)
        }
    
    # Format methods
    def _format_discord(self, data: Dict) -> str:
        """Format logs for Discord"""
        if "logs" in data:
            lines = [f"📝 **Recent Logs ({data['count']}):**"]
            for log in data["logs"][-10:]:  # Last 10 for Discord
                time_str = datetime.fromisoformat(log["timestamp"]).strftime("%H:%M:%S")
                emoji = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌", "DEBUG": "🐛"}.get(log["level"], "📋")
                lines.append(f"{emoji} `{time_str}` {log['message'][:50]}{'...' if len(log['message']) > 50 else ''}")
            return "\n".join(lines)
        
        elif "total" in data:  # Stats
            return f"📊 **Log Stats:** {data['total']} total | ❌ {data.get('error', 0)} errors | ⚠️ {data.get('warn', 0)} warnings"
        
        return f"📝 {data}"
    
    def _format_text(self, data: Dict) -> str:
        """Format logs as plain text"""
        if "logs" in data:
            lines = []
            for log in data["logs"]:
                time_str = datetime.fromisoformat(log["timestamp"]).strftime("%H:%M:%S")
                lines.append(f"[{time_str}] {log['level']} {log['caller']}: {log['message']}")
            return "\n".join(lines)
        
        return str(data)
    
    def _format_csv(self, data: Dict) -> str:
        """Format logs as CSV"""
        if "logs" in data:
            lines = ["timestamp,level,caller,message"]
            for log in data["logs"]:
                message = log['message'].replace(',', ';').replace('\n', ' ')
                lines.append(f"{log['timestamp']},{log['level']},{log['caller']},{message}")
            return "\n".join(lines)
        
        return str(data)
    
    def _format_html(self, data: Dict) -> str:
        """Format logs as HTML"""
        if "logs" in data:
            html = "<table border='1'><tr><th>Time</th><th>Level</th><th>Caller</th><th>Message</th></tr>"
            for log in data["logs"]:
                time_str = datetime.fromisoformat(log["timestamp"]).strftime("%H:%M:%S")
                color = {"INFO": "#007acc", "WARN": "#ff8c00", "ERROR": "#dc3545", "DEBUG": "#6c757d"}.get(log["level"], "#000")
                html += f"<tr><td>{time_str}</td><td style='color:{color}'>{log['level']}</td><td>{log['caller']}</td><td>{log['message']}</td></tr>"
            html += "</table>"
            return html
        
        return f"<pre>{data}</pre>"
    
    # Helper methods
    def _extract_number(self, text: str, default: int = 10) -> int:
        """Extract number from text"""
        import re
        match = re.search(r'\b(\d+)\b', text)
        return int(match.group(1)) if match else default

# Create service instances
logger_service = RefactoredLoggerService(prefer_network=False)  # Local-first
logger_service_network = RefactoredLoggerService(prefer_network=True)  # Network-first

# Backward compatibility functions (same interface as before)
def info(message: str, **kwargs):
    """Log info message (backward compatible)"""
    return logger_service.info(message, **kwargs)

def warning(message: str, **kwargs):
    """Log warning message (backward compatible)"""
    return logger_service.warning(message, **kwargs)

def error(message: str, **kwargs):
    """Log error message (backward compatible)"""
    return logger_service.error(message, **kwargs)

def debug(message: str, **kwargs):
    """Log debug message (backward compatible)"""
    return logger_service.debug(message, **kwargs)

if __name__ == "__main__":
    # Test the refactored logger service
    print("🧪 Testing Refactored Logger Service")
    
    # Test local-first service
    print("\n1. Testing local-first logger service:")
    logger_local = RefactoredLoggerService(prefer_network=False)
    
    # Test logging
    logger_local.info("Test info message")
    logger_local.warning("Test warning message")
    logger_local.error("Test error message")
    
    # Test queries
    recent = logger_local.ask("recent logs")
    print(f"Recent logs: {logger_local.tell('discord', recent)}")
    
    # Test backward compatibility
    print("\n2. Testing backward compatibility:")
    info("This still works like before")
    warning("Backward compatible warning")
    
    # Test network-first service
    print("\n3. Testing network-first logger service:")
    logger_network = RefactoredLoggerService(prefer_network=True)
    
    stats = logger_network.ask("log stats")
    print(f"Log stats: {logger_network.tell('text', stats)}")
    
    print("\n✅ Refactored logger service test complete!")
    print("💡 Same logging interface, but now with service locator and 3-method pattern!")