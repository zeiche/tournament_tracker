"""
log_utils.py - Centralized Logging for Tournament Tracker
Simple, consistent logging interface for the entire codebase
"""
import os
import sys
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3

class Logger:
    """Simple logger with file and console output"""
    
    def __init__(self, log_file=None, console=True, level=LogLevel.INFO, debug_file="debug.txt"):
        self.log_file = log_file or os.getenv('LOG_FILE', 'tournament_tracker.log')
        self.debug_file = debug_file
        self.console = console
        self.level = level
        self.colors = {
            LogLevel.DEBUG: '\033[36m',  # Cyan
            LogLevel.INFO: '\033[32m',   # Green
            LogLevel.WARN: '\033[33m',   # Yellow
            LogLevel.ERROR: '\033[31m'   # Red
        }
        self.reset_color = '\033[0m'
        
        # Clear debug file on initialization
        if self.debug_file:
            try:
                with open(self.debug_file, 'w') as f:
                    f.write("")  # Clear the file
            except Exception:
                pass
    
    def _should_log(self, level):
        """Check if message should be logged based on level"""
        return level.value >= self.level.value
    
    def _format_message(self, level, message, context=None):
        """Format log message with level and optional context"""
        level_str = level.name.ljust(5)
        
        if context:
            return f"{level_str} [{context}] {message}"
        else:
            return f"{level_str} {message}"
    
    def _write_message(self, level, formatted_message):
        """Write message to console, log file, and debug file"""
        # Console output with colors
        if self.console:
            color = self.colors.get(level, '')
            print(f"{color}{formatted_message}{self.reset_color}")
        
        # Main log file output without colors
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{formatted_message}\n")
            except Exception:
                # Don't let logging errors break the application
                pass
        
        # Debug file output without colors (replace mode)
        if self.debug_file:
            try:
                with open(self.debug_file, 'a', encoding='utf-8') as f:
                    f.write(f"{formatted_message}\n")
            except Exception:
                # Don't let logging errors break the application
                pass
    
    def debug(self, message, context=None):
        """Log debug message"""
        if self._should_log(LogLevel.DEBUG):
            formatted = self._format_message(LogLevel.DEBUG, message, context)
            self._write_message(LogLevel.DEBUG, formatted)
    
    def info(self, message, context=None):
        """Log info message"""
        if self._should_log(LogLevel.INFO):
            formatted = self._format_message(LogLevel.INFO, message, context)
            self._write_message(LogLevel.INFO, formatted)
    
    def warn(self, message, context=None):
        """Log warning message"""
        if self._should_log(LogLevel.WARN):
            formatted = self._format_message(LogLevel.WARN, message, context)
            self._write_message(LogLevel.WARN, formatted)
    
    def error(self, message, context=None):
        """Log error message"""
        if self._should_log(LogLevel.ERROR):
            formatted = self._format_message(LogLevel.ERROR, message, context)
            self._write_message(LogLevel.ERROR, formatted)

# Global logger instance
_logger = None

def init_logging(log_file=None, console=True, level=LogLevel.INFO, debug_file="debug.txt"):
    """Initialize global logger"""
    global _logger
    _logger = Logger(log_file=log_file, console=console, level=level, debug_file=debug_file)
    return _logger

def get_logger():
    """Get the global logger (initializes with defaults if needed)"""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger

# Convenience functions for global logger
def log_debug(message, context=None):
    """Log debug message using global logger"""
    get_logger().debug(message, context)

def log_info(message, context=None):
    """Log info message using global logger"""
    get_logger().info(message, context)

def log_warn(message, context=None):
    """Log warning message using global logger"""
    get_logger().warn(message, context)

def log_error(message, context=None):
    """Log error message using global logger"""
    get_logger().error(message, context)

# Context manager for logging operations
class LogContext:
    """Context manager for logging operations with automatic timing"""
    
    def __init__(self, operation_name, level=LogLevel.INFO):
        self.operation_name = operation_name
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        if self.level == LogLevel.INFO:
            log_info(f"Starting {self.operation_name}...")
        elif self.level == LogLevel.DEBUG:
            log_debug(f"Starting {self.operation_name}...")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        
        if exc_type is None:
            if self.level == LogLevel.INFO:
                log_info(f"Completed {self.operation_name} ({duration.total_seconds():.2f}s)")
            elif self.level == LogLevel.DEBUG:
                log_debug(f"Completed {self.operation_name} ({duration.total_seconds():.2f}s)")
        else:
            log_error(f"Failed {self.operation_name} after {duration.total_seconds():.2f}s: {exc_val}")

# Database operation logging helpers
def log_db_operation(operation_name, affected_count=None, context=None):
    """Log database operation result"""
    if affected_count is not None:
        message = f"{operation_name}: {affected_count} records"
    else:
        message = operation_name
    
    log_info(message, context or "database")

def log_api_call(endpoint, duration_seconds, success=True, context=None):
    """Log API call result"""
    status = "SUCCESS" if success else "FAILED"
    message = f"{endpoint} - {status} ({duration_seconds:.2f}s)"
    
    if success:
        log_info(message, context or "api")
    else:
        log_error(message, context or "api")

# Session cache logging (for debugging the specific issue)
def log_session_operation(operation, organization_key, before_name, after_name=None):
    """Log session cache operations for debugging"""
    if after_name:
        message = f"{operation}: '{organization_key}' '{before_name}' -> '{after_name}'"
    else:
        message = f"{operation}: '{organization_key}' '{before_name}'"
    
    log_debug(message, "session")

if __name__ == "__main__":
    # Test the logging system
    print("Testing logging system...")
    
    # Initialize with debug level
    init_logging(level=LogLevel.DEBUG, log_file="test.log")
    
    # Test different log levels
    log_debug("This is a debug message")
    log_info("This is an info message") 
    log_warn("This is a warning message")
    log_error("This is an error message")
    
    # Test context logging
    log_info("Database operation completed", "database")
    log_error("API call failed", "startgg")
    
    # Test operation context manager
    with LogContext("test operation"):
        import time
        time.sleep(0.1)
    
    # Test database and API helpers
    log_db_operation("Organizations updated", 5)
    log_api_call("/tournaments", 1.23, success=True)
    log_api_call("/standings", 0.85, success=False)
    
    # Test session debugging
    log_session_operation("LOAD", "test@example.com", "test@example.com") 
    log_session_operation("SAVE", "test@example.com", "test@example.com", "Test Organization")
    
    print("Logging test completed!")

