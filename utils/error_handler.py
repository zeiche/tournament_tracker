#!/usr/bin/env python3
"""
error_handler.py - Comprehensive error handling with 3-method pattern
Provides consistent error handling, logging, and recovery across the system
"""
import sys
import os
import traceback
from typing import Any, Dict, List, Optional, Type, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.simple_logger import info, warning, error
from polymorphic_core import announcer


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"          # Non-critical, system continues normally
    MEDIUM = "medium"    # Important but recoverable
    HIGH = "high"        # Serious issue requiring attention
    CRITICAL = "critical"  # System-threatening error


@dataclass
class ErrorContext:
    """Context information for errors"""
    timestamp: datetime
    severity: ErrorSeverity
    module: str
    function: str
    error_type: str
    message: str
    traceback_lines: List[str] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    user_message: Optional[str] = None


class ErrorHandler:
    """
    Comprehensive error handling service with 3-method pattern
    """
    
    def __init__(self):
        self._error_history: List[ErrorContext] = []
        self._recovery_strategies: Dict[Type[Exception], Callable] = {}
        self._severity_mapping: Dict[Type[Exception], ErrorSeverity] = {
            ConnectionError: ErrorSeverity.MEDIUM,
            TimeoutError: ErrorSeverity.MEDIUM,
            FileNotFoundError: ErrorSeverity.HIGH,
            PermissionError: ErrorSeverity.HIGH,
            ImportError: ErrorSeverity.CRITICAL,
            KeyError: ErrorSeverity.MEDIUM,
            ValueError: ErrorSeverity.LOW,
            TypeError: ErrorSeverity.MEDIUM,
            AttributeError: ErrorSeverity.MEDIUM,
        }
        
        # Announce capabilities
        announcer.announce(
            "Error Handler Service",
            [
                "Comprehensive error handling with 3-method pattern",
                "ask('error history') - Query error logs and patterns",
                "tell('discord', errors) - Format error reports",
                "do('handle exception') - Process and recover from errors",
                "Automatic severity classification and recovery"
            ],
            [
                "error_handler.ask('recent errors')",
                "error_handler.do('clear history')",
                "error_handler.tell('json', error_data)"
            ]
        )
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query error information using natural language
        Examples:
            ask("error history")
            ask("recent errors")
            ask("critical errors")
            ask("error stats")
        """
        query = query.lower().strip()
        
        if "history" in query or "all errors" in query:
            return self._get_error_history()
        
        elif "recent" in query:
            limit = kwargs.get('limit', 10)
            return self._get_recent_errors(limit)
        
        elif "critical" in query:
            return self._get_errors_by_severity(ErrorSeverity.CRITICAL)
        
        elif "high" in query:
            return self._get_errors_by_severity(ErrorSeverity.HIGH)
        
        elif "stats" in query or "statistics" in query:
            return self._get_error_statistics()
        
        elif "pattern" in query:
            return self._get_error_patterns()
        
        else:
            return f"Unknown error query: {query}"
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format error information for output
        """
        if data is None:
            data = self._get_recent_errors(5)
        
        if format.lower() in ["json"]:
            import json
            return json.dumps([self._error_to_dict(err) for err in data], default=str, indent=2)
        
        elif format.lower() in ["discord", "text"]:
            if isinstance(data, list):
                if not data:
                    return "🟢 **No recent errors**"
                
                lines = ["🔴 **Recent Errors**"]
                for err in data[:5]:  # Limit to 5 for Discord
                    severity_emoji = {
                        ErrorSeverity.LOW: "🟡",
                        ErrorSeverity.MEDIUM: "🟠", 
                        ErrorSeverity.HIGH: "🔴",
                        ErrorSeverity.CRITICAL: "💥"
                    }.get(err.severity, "❓")
                    
                    time_str = err.timestamp.strftime("%H:%M:%S")
                    lines.append(f"{severity_emoji} [{time_str}] {err.module}.{err.function}: {err.message}")
                    
                    if err.recovery_attempted:
                        recovery_status = "✅" if err.recovery_successful else "❌"
                        lines.append(f"   Recovery: {recovery_status}")
                
                return "\n".join(lines)
            
            elif isinstance(data, dict):
                # Statistics format
                lines = ["📊 **Error Statistics**"]
                for key, value in data.items():
                    lines.append(f"• {key}: {value}")
                return "\n".join(lines)
            
            return str(data)
        
        else:
            return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform error handling actions
        Examples:
            do("handle exception", exception=e, context={})
            do("clear history")
            do("register recovery", exception_type=ValueError, handler=func)
        """
        action = action.lower().strip()
        
        if "handle" in action and "exception" in action:
            exception = kwargs.get('exception')
            context = kwargs.get('context', {})
            return self._handle_exception(exception, context)
        
        elif "clear" in action and "history" in action:
            count = len(self._error_history)
            self._error_history.clear()
            return f"Cleared {count} error records"
        
        elif "register" in action and "recovery" in action:
            exception_type = kwargs.get('exception_type')
            handler = kwargs.get('handler')
            if exception_type and handler:
                self._recovery_strategies[exception_type] = handler
                return f"Registered recovery strategy for {exception_type.__name__}"
            return "Missing exception_type or handler"
        
        else:
            return f"Unknown error action: {action}"
    
    def _handle_exception(self, exception: Exception, context: Dict[str, Any] = None) -> ErrorContext:
        """Handle an exception with full context"""
        if context is None:
            context = {}
        
        # Get caller info
        frame = sys._getframe(2)
        module_name = frame.f_globals.get('__name__', 'unknown')
        function_name = frame.f_code.co_name
        
        # Create error context
        error_context = ErrorContext(
            timestamp=datetime.now(),
            severity=self._get_severity(exception),
            module=module_name,
            function=function_name,
            error_type=type(exception).__name__,
            message=str(exception),
            traceback_lines=traceback.format_exc().split('\n'),
            context_data=context
        )
        
        # Log the error
        self._log_error(error_context)
        
        # Attempt recovery
        self._attempt_recovery(error_context, exception)
        
        # Store in history
        self._error_history.append(error_context)
        
        # Keep history manageable
        if len(self._error_history) > 1000:
            self._error_history = self._error_history[-500:]
        
        return error_context
    
    def _get_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity"""
        exception_type = type(exception)
        return self._severity_mapping.get(exception_type, ErrorSeverity.MEDIUM)
    
    def _log_error(self, error_context: ErrorContext):
        """Log error based on severity"""
        message = f"{error_context.module}.{error_context.function}: {error_context.message}"
        
        if error_context.severity == ErrorSeverity.CRITICAL:
            error(f"CRITICAL: {message}")
        elif error_context.severity == ErrorSeverity.HIGH:
            error(f"HIGH: {message}")
        elif error_context.severity == ErrorSeverity.MEDIUM:
            warning(f"MEDIUM: {message}")
        else:
            info(f"LOW: {message}")
    
    def _attempt_recovery(self, error_context: ErrorContext, exception: Exception):
        """Attempt to recover from the error"""
        exception_type = type(exception)
        
        if exception_type in self._recovery_strategies:
            error_context.recovery_attempted = True
            try:
                recovery_func = self._recovery_strategies[exception_type]
                recovery_func(exception, error_context)
                error_context.recovery_successful = True
                info(f"Recovery successful for {exception_type.__name__}")
            except Exception as recovery_error:
                error_context.recovery_successful = False
                error(f"Recovery failed for {exception_type.__name__}: {recovery_error}")
    
    def _get_error_history(self) -> List[ErrorContext]:
        """Get complete error history"""
        return self._error_history.copy()
    
    def _get_recent_errors(self, limit: int = 10) -> List[ErrorContext]:
        """Get recent errors"""
        return self._error_history[-limit:] if self._error_history else []
    
    def _get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorContext]:
        """Get errors by severity level"""
        return [err for err in self._error_history if err.severity == severity]
    
    def _get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self._error_history:
            return {"total_errors": 0}
        
        total = len(self._error_history)
        by_severity = {}
        by_type = {}
        by_module = {}
        
        for err in self._error_history:
            # By severity
            severity_key = err.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1
            
            # By type
            by_type[err.error_type] = by_type.get(err.error_type, 0) + 1
            
            # By module
            by_module[err.module] = by_module.get(err.module, 0) + 1
        
        recovery_attempted = sum(1 for err in self._error_history if err.recovery_attempted)
        recovery_successful = sum(1 for err in self._error_history if err.recovery_successful)
        
        return {
            "total_errors": total,
            "by_severity": by_severity,
            "most_common_types": dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)[:5]),
            "most_error_prone_modules": dict(sorted(by_module.items(), key=lambda x: x[1], reverse=True)[:5]),
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_successful,
            "recovery_rate": f"{(recovery_successful/recovery_attempted*100):.1f}%" if recovery_attempted > 0 else "N/A"
        }
    
    def _get_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns"""
        if not self._error_history:
            return {"message": "No error history to analyze"}
        
        # Find repeated errors
        error_counts = {}
        for err in self._error_history:
            key = f"{err.module}.{err.function}: {err.error_type}"
            error_counts[key] = error_counts.get(key, 0) + 1
        
        repeated_errors = {k: v for k, v in error_counts.items() if v > 1}
        
        return {
            "repeated_errors": dict(sorted(repeated_errors.items(), key=lambda x: x[1], reverse=True)),
            "total_unique_errors": len(error_counts),
            "repeated_error_count": len(repeated_errors)
        }
    
    def _error_to_dict(self, error_context: ErrorContext) -> Dict[str, Any]:
        """Convert ErrorContext to dictionary"""
        return {
            "timestamp": error_context.timestamp.isoformat(),
            "severity": error_context.severity.value,
            "module": error_context.module,
            "function": error_context.function,
            "error_type": error_context.error_type,
            "message": error_context.message,
            "recovery_attempted": error_context.recovery_attempted,
            "recovery_successful": error_context.recovery_successful,
            "context_data": error_context.context_data
        }


# Global instance
error_handler = ErrorHandler()


# Decorator for automatic error handling
def handle_errors(severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                  context: Dict[str, Any] = None,
                  reraise: bool = True,
                  default_return: Any = None):
    """
    Decorator for automatic error handling
    
    Args:
        severity: Override default severity classification
        context: Additional context to include
        reraise: Whether to reraise the exception after handling
        default_return: Value to return if exception caught and not reraised
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = error_handler._handle_exception(e, context or {})
                error_context.severity = severity  # Override if specified
                
                if reraise:
                    raise
                else:
                    return default_return
        return wrapper
    return decorator


# Convenience functions
def handle_exception(exception: Exception, context: Dict[str, Any] = None) -> ErrorContext:
    """Handle an exception with context"""
    return error_handler.do("handle exception", exception=exception, context=context)

def get_error_stats() -> Dict[str, Any]:
    """Get error statistics"""
    return error_handler.ask("error stats")

def clear_error_history() -> str:
    """Clear error history"""
    return error_handler.do("clear history")


if __name__ == "__main__":
    # Test the error handler
    print("🔴 Testing Error Handler...")
    
    # Test basic error handling
    try:
        raise ValueError("Test error")
    except Exception as e:
        context = handle_exception(e, {"test_data": "sample"})
        print(f"Handled error: {context.message}")
    
    # Test queries
    print("\nRecent errors:")
    print(error_handler.tell("discord"))
    
    print("\nError statistics:")
    stats = error_handler.ask("stats")
    print(error_handler.tell("discord", stats))
    
    print("\n✅ Error handler test complete!")