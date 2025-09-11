"""
log_manager.py - Unified Logging Service
Modern OOP replacement for log_utils.py
Centralized, context-aware logging with multiple handlers and formatting
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json
from contextlib import contextmanager


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogManager:
    """Centralized logging service with context awareness and multiple handlers"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern for log manager"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 log_file: Optional[str] = 'tournament_tracker.log',
                 level: LogLevel = LogLevel.INFO,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 json_format: bool = False):
        """Initialize log manager (only runs once due to singleton)"""
        if not self._initialized:
            self.log_file = log_file
            self.level = level
            self.enable_console = enable_console
            self.enable_file = enable_file
            self.json_format = json_format
            
            # Statistics tracking
            self._stats = {
                'debug': 0,
                'info': 0,
                'warning': 0,
                'error': 0,
                'critical': 0,
                'api_calls': 0,
                'db_queries': 0
            }
            
            # Context stack for nested operations
            self._context_stack = []
            
            # Module-specific loggers
            self._loggers = {}
            
            # Initialize root logger
            self._setup_root_logger()
            
            LogManager._initialized = True
    
    def _setup_root_logger(self):
        """Setup root logger with handlers"""
        self.root_logger = logging.getLogger('tournament_tracker')
        self.root_logger.setLevel(self.level.value)
        
        # Clear existing handlers
        self.root_logger.handlers = []
        
        # Create formatters
        if self.json_format:
            formatter = JSONFormatter()
        else:
            formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Add console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.root_logger.addHandler(console_handler)
        
        # Add file handler
        if self.enable_file and self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.root_logger.addHandler(file_handler)
    
    def get_logger(self, module_name: str) -> 'ModuleLogger':
        """Get or create a module-specific logger"""
        if module_name not in self._loggers:
            self._loggers[module_name] = ModuleLogger(self, module_name)
        return self._loggers[module_name]
    
    def set_level(self, level: LogLevel, module: Optional[str] = None):
        """Set logging level globally or for specific module"""
        if module:
            if module in self._loggers:
                self._loggers[module].set_level(level)
        else:
            self.level = level
            self.root_logger.setLevel(level.value)
    
    @contextmanager
    def context(self, context_name: str, **extra_fields):
        """Context manager for nested logging contexts"""
        context_info = {'name': context_name, 'start': datetime.now()}
        context_info.update(extra_fields)
        
        self._context_stack.append(context_info)
        self.debug(f"Entering context: {context_name}")
        
        try:
            yield self
        finally:
            elapsed = (datetime.now() - context_info['start']).total_seconds()
            self.debug(f"Exiting context: {context_name} (elapsed: {elapsed:.3f}s)")
            self._context_stack.pop()
    
    def _format_message(self, message: str) -> str:
        """Format message with context information"""
        if self._context_stack:
            contexts = ' > '.join(c['name'] for c in self._context_stack)
            return f"[{contexts}] {message}"
        return message
    
    def _log(self, level: LogLevel, message: str, module: Optional[str] = None, **extra):
        """Core logging method"""
        # Update statistics
        self._stats[level.name.lower()] += 1
        
        # Get appropriate logger
        logger = self.root_logger
        if module and module in self._loggers:
            logger = self._loggers[module].logger
        
        # Format message with context
        formatted_message = self._format_message(message)
        
        # Add extra fields
        if extra:
            logger.log(level.value, formatted_message, extra=extra)
        else:
            logger.log(level.value, formatted_message)
    
    # Convenience methods
    
    def debug(self, message: str, module: Optional[str] = None, **extra):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, module, **extra)
    
    def info(self, message: str, module: Optional[str] = None, **extra):
        """Log info message"""
        self._log(LogLevel.INFO, message, module, **extra)
    
    def warning(self, message: str, module: Optional[str] = None, **extra):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, module, **extra)
    
    def error(self, message: str, module: Optional[str] = None, **extra):
        """Log error message"""
        self._log(LogLevel.ERROR, message, module, **extra)
    
    def critical(self, message: str, module: Optional[str] = None, **extra):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, module, **extra)
    
    # Specialized logging methods
    
    def log_api_call(self, service: str, endpoint: str, 
                     response_time: float, status_code: int, **extra):
        """Log API call with metrics"""
        self._stats['api_calls'] += 1
        
        message = f"API Call: {service} {endpoint} - {status_code} ({response_time:.3f}s)"
        
        if status_code >= 400:
            self.error(message, 'api', service=service, endpoint=endpoint, 
                      response_time=response_time, status_code=status_code, **extra)
        else:
            self.info(message, 'api', service=service, endpoint=endpoint, 
                     response_time=response_time, status_code=status_code, **extra)
    
    def log_database_query(self, query_type: str, table: str, 
                          execution_time: float, rows_affected: int = 0, **extra):
        """Log database query with metrics"""
        self._stats['db_queries'] += 1
        
        message = f"DB Query: {query_type} {table} - {rows_affected} rows ({execution_time:.3f}s)"
        self.debug(message, 'database', query_type=query_type, table=table,
                  execution_time=execution_time, rows_affected=rows_affected, **extra)
    
    def log_operation(self, operation: str, status: str, 
                     duration: Optional[float] = None, **extra):
        """Log operation with status"""
        message = f"Operation: {operation} - {status}"
        if duration:
            message += f" ({duration:.3f}s)"
        
        if status.lower() in ['failed', 'error']:
            self.error(message, 'operations', operation=operation, status=status, **extra)
        else:
            self.info(message, 'operations', operation=operation, status=status, **extra)
    
    def log_exception(self, exception: Exception, context: str = ""):
        """Log exception with traceback"""
        import traceback
        
        tb = traceback.format_exc()
        message = f"Exception in {context}: {str(exception)}" if context else str(exception)
        
        self.error(message, 'exceptions', exception_type=type(exception).__name__,
                  traceback=tb)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return {
            'log_counts': self._stats.copy(),
            'total_logs': sum(v for k, v in self._stats.items() 
                            if k in ['debug', 'info', 'warning', 'error', 'critical']),
            'api_calls': self._stats['api_calls'],
            'db_queries': self._stats['db_queries'],
            'active_contexts': len(self._context_stack),
            'module_loggers': list(self._loggers.keys())
        }
    
    def clear_statistics(self):
        """Clear logging statistics"""
        for key in self._stats:
            self._stats[key] = 0
    
    def rotate_log_file(self):
        """Rotate log file"""
        if self.log_file and Path(self.log_file).exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{self.log_file}.{timestamp}"
            Path(self.log_file).rename(backup_name)
            
            # Reinitialize file handler
            self._setup_root_logger()
            self.info(f"Log file rotated to {backup_name}")
    
    def add_handler(self, handler: logging.Handler):
        """Add custom handler to root logger"""
        self.root_logger.addHandler(handler)
    
    def remove_handler(self, handler: logging.Handler):
        """Remove handler from root logger"""
        self.root_logger.removeHandler(handler)


class ModuleLogger:
    """Module-specific logger wrapper"""
    
    def __init__(self, manager: LogManager, module_name: str):
        """Initialize module logger"""
        self.manager = manager
        self.module_name = module_name
        self.logger = logging.getLogger(f'tournament_tracker.{module_name}')
        self.logger.setLevel(manager.level.value)
    
    def set_level(self, level: LogLevel):
        """Set module-specific log level"""
        self.logger.setLevel(level.value)
    
    def debug(self, message: str, **extra):
        """Log debug message"""
        self.manager.debug(message, self.module_name, **extra)
    
    def info(self, message: str, **extra):
        """Log info message"""
        self.manager.info(message, self.module_name, **extra)
    
    def warning(self, message: str, **extra):
        """Log warning message"""
        self.manager.warning(message, self.module_name, **extra)
    
    def error(self, message: str, **extra):
        """Log error message"""
        self.manager.error(message, self.module_name, **extra)
    
    def critical(self, message: str, **extra):
        """Log critical message"""
        self.manager.critical(message, self.module_name, **extra)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        """Format record with colors"""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record):
        """Format record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            import traceback
            log_data['exception'] = traceback.format_exception(*record.exc_info)
        
        return json.dumps(log_data)


# Global log manager instance
log_manager = LogManager()

# Convenience functions for backward compatibility
def get_logger(module_name: str) -> ModuleLogger:
    """Get module-specific logger"""
    return log_manager.get_logger(module_name)

# Direct logging functions
log_debug = log_manager.debug
log_info = log_manager.info
log_warn = log_manager.warning
log_error = log_manager.error
log_critical = log_manager.critical
log_api_call = log_manager.log_api_call

# Context manager
LogContext = log_manager.context