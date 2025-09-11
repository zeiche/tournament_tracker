#!/usr/bin/env python3
"""
error_handler_refactored.py - REFACTORED Error handler using service locator

BEFORE: Direct imports of logger and other services
AFTER: Uses service locator for all dependencies

Key changes:
1. Removed direct import of simple_logger
2. Uses service locator to discover logger at runtime
3. Works with local OR network services transparently
4. Same error handling functionality as original
5. Can be distributed for centralized error handling

This demonstrates refactoring a critical system service.
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

from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service

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

class RefactoredErrorHandler:
    """
    REFACTORED Error handling service using service locator pattern.
    
    This version discovers its dependencies (logger, config) via service locator
    instead of direct imports. Can operate over network for distributed error handling.
    """
    
    _instance: Optional['RefactoredErrorHandler'] = None
    
    def __new__(cls, prefer_network: bool = False) -> 'RefactoredErrorHandler':
        """Singleton pattern with service preference"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.prefer_network = prefer_network
            cls._instance._logger = None
            cls._instance._config = None
            cls._instance._error_history: List[ErrorContext] = []
            cls._instance._recovery_strategies: Dict[Type[Exception], Callable] = {}
            cls._instance._severity_mapping: Dict[Type[Exception], ErrorSeverity] = {
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
                "Error Handler Service (Refactored)",
                [
                    "REFACTORED: Uses service locator for dependencies",
                    "Distributed error handling with 3-method pattern",
                    "ask('error history') - Query error logs and patterns",
                    "tell('discord', errors) - Format error reports",
                    "do('handle exception') - Process and recover from errors",
                    "Works with local OR network logger service"
                ],
                [
                    "error_handler.ask('recent errors')",
                    "error_handler.do('clear history')",
                    "error_handler.tell('json', error_data)",
                    "Works transparently with network services"
                ]
            )
        return cls._instance
    
    @property
    def logger(self):
        """Lazy-loaded logger service via service locator"""
        if self._logger is None:
            self._logger = get_service("logger", self.prefer_network)
        return self._logger
    
    @property
    def config(self):
        """Lazy-loaded config service via service locator"""
        if self._config is None:
            self._config = get_service("config", self.prefer_network)
        return self._config
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query error information using natural language.
        
        Examples:
            ask("error history")
            ask("recent errors")
            ask("critical errors")
            ask("error stats")
            ask("errors by type")
        """
        query_lower = query.lower().strip()
        
        try:
            if "history" in query_lower or "all errors" in query_lower:
                return self._get_error_history()
            
            elif "recent" in query_lower:
                limit = kwargs.get('limit', self._extract_number(query, 10))
                return self._get_recent_errors(limit)
            
            elif "critical" in query_lower:
                return self._get_errors_by_severity(ErrorSeverity.CRITICAL)
            
            elif "high" in query_lower:
                return self._get_errors_by_severity(ErrorSeverity.HIGH)
            
            elif "medium" in query_lower:
                return self._get_errors_by_severity(ErrorSeverity.MEDIUM)
            
            elif "low" in query_lower:
                return self._get_errors_by_severity(ErrorSeverity.LOW)
            
            elif "stats" in query_lower:
                return self._get_error_stats()
            
            elif "by type" in query_lower:
                return self._get_errors_by_type()
            
            elif "patterns" in query_lower:
                return self._analyze_error_patterns()
            
            else:
                return {"error": f"Don't know how to handle query: {query}"}
                
        except Exception as e:
            return {"error": f"Error query failed: {str(e)}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """
        Format error data for output.
        
        Formats: json, discord, text, html, csv, summary
        """
        if data is None:
            data = {}
        
        try:
            if format_type == "json":
                return self._format_json(data)
            
            elif format_type == "discord":
                return self._format_discord(data)
            
            elif format_type == "text":
                return self._format_text(data)
            
            elif format_type == "html":
                return self._format_html(data)
            
            elif format_type == "csv":
                return self._format_csv(data)
            
            elif format_type == "summary":
                return self._format_summary(data)
            
            else:
                return str(data)
                
        except Exception as e:
            return f"Format error: {e}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform error handling operations using natural language.
        
        Examples:
            do("handle exception ValueError('test')")
            do("clear history")
            do("set severity FileNotFoundError HIGH")
            do("register recovery strategy")
        """
        action_lower = action.lower().strip()
        
        try:
            if "handle exception" in action_lower:
                exception = kwargs.get('exception')
                severity = kwargs.get('severity', ErrorSeverity.MEDIUM)
                return self._handle_exception_action(exception, severity)
            
            elif "clear history" in action_lower:
                return self._clear_error_history()
            
            elif "set severity" in action_lower:
                return self._set_severity_mapping(action)
            
            elif "register recovery" in action_lower:
                return self._register_recovery_strategy(action, kwargs)
            
            else:
                return {"error": f"Don't know how to: {action}"}
                
        except Exception as e:
            return {"error": f"Error action failed: {str(e)}"}
    
    def handle_exception(self, exception: Exception, severity: Union[ErrorSeverity, str] = None, **context) -> ErrorContext:
        """
        Handle an exception with full context and recovery (backward compatible).
        
        Args:
            exception: The exception to handle
            severity: Error severity (auto-detected if None)
            **context: Additional context data
        """
        # Convert severity if string
        if isinstance(severity, str):
            severity = ErrorSeverity(severity.lower())
        
        # Auto-detect severity if not provided
        if severity is None:
            severity = self._severity_mapping.get(type(exception), ErrorSeverity.MEDIUM)
        
        # Get caller information
        frame = sys._getframe(1)
        module = frame.f_globals.get('__name__', 'unknown')
        function = frame.f_code.co_name
        
        # Create error context
        error_context = ErrorContext(
            timestamp=datetime.now(),
            severity=severity,
            module=module,
            function=function,
            error_type=type(exception).__name__,
            message=str(exception),
            traceback_lines=traceback.format_exception(type(exception), exception, exception.__traceback__),
            context_data=context
        )
        
        # Log using discovered logger service
        if self.logger:
            try:
                log_message = f"{error_context.error_type} in {module}.{function}: {error_context.message}"
                if severity == ErrorSeverity.CRITICAL:
                    self.logger.error(log_message)
                elif severity == ErrorSeverity.HIGH:
                    self.logger.error(log_message)
                elif severity == ErrorSeverity.MEDIUM:
                    self.logger.warning(log_message)
                else:
                    self.logger.info(log_message)
            except:
                # Fallback if logger unavailable
                print(f"ERROR: {error_context.message}")
        
        # Attempt recovery
        if type(exception) in self._recovery_strategies:
            try:
                error_context.recovery_attempted = True
                recovery_result = self._recovery_strategies[type(exception)](exception, error_context)
                error_context.recovery_successful = recovery_result is not False
            except Exception as recovery_error:
                if self.logger:
                    try:
                        self.logger.error(f"Recovery failed: {recovery_error}")
                    except:
                        pass
        
        # Add to history
        self._error_history.append(error_context)
        
        # Trim history if too long
        max_history = 1000  # Could be configurable via discovered config service
        if len(self._error_history) > max_history:
            self._error_history = self._error_history[-max_history:]
        
        return error_context
    
    # Query implementation methods
    def _get_error_history(self) -> Dict:
        """Get full error history"""
        return {
            "errors": [self._error_context_to_dict(ctx) for ctx in self._error_history],
            "count": len(self._error_history)
        }
    
    def _get_recent_errors(self, limit: int) -> Dict:
        """Get recent errors"""
        recent = self._error_history[-limit:] if limit < len(self._error_history) else self._error_history
        return {
            "errors": [self._error_context_to_dict(ctx) for ctx in recent],
            "count": len(recent),
            "limit": limit
        }
    
    def _get_errors_by_severity(self, severity: ErrorSeverity) -> Dict:
        """Get errors filtered by severity"""
        filtered = [ctx for ctx in self._error_history if ctx.severity == severity]
        return {
            "errors": [self._error_context_to_dict(ctx) for ctx in filtered],
            "severity": severity.value,
            "count": len(filtered)
        }
    
    def _get_error_stats(self) -> Dict:
        """Get error statistics"""
        stats = {
            "total": len(self._error_history),
            "by_severity": {},
            "by_type": {},
            "recovery_rate": 0
        }
        
        # Count by severity
        for severity in ErrorSeverity:
            count = len([ctx for ctx in self._error_history if ctx.severity == severity])
            stats["by_severity"][severity.value] = count
        
        # Count by type
        type_counts = {}
        recovery_attempts = 0
        recovery_successes = 0
        
        for ctx in self._error_history:
            type_counts[ctx.error_type] = type_counts.get(ctx.error_type, 0) + 1
            if ctx.recovery_attempted:
                recovery_attempts += 1
                if ctx.recovery_successful:
                    recovery_successes += 1
        
        stats["by_type"] = type_counts
        
        # Calculate recovery rate
        if recovery_attempts > 0:
            stats["recovery_rate"] = recovery_successes / recovery_attempts
        
        return stats
    
    def _get_errors_by_type(self) -> Dict:
        """Get errors grouped by type"""
        by_type = {}
        for ctx in self._error_history:
            if ctx.error_type not in by_type:
                by_type[ctx.error_type] = []
            by_type[ctx.error_type].append(self._error_context_to_dict(ctx))
        
        return {"errors_by_type": by_type}
    
    def _analyze_error_patterns(self) -> Dict:
        """Analyze error patterns"""
        patterns = {
            "common_modules": {},
            "common_functions": {},
            "time_patterns": {},
            "severity_trends": []
        }
        
        # Common modules and functions
        for ctx in self._error_history:
            patterns["common_modules"][ctx.module] = patterns["common_modules"].get(ctx.module, 0) + 1
            patterns["common_functions"][ctx.function] = patterns["common_functions"].get(ctx.function, 0) + 1
        
        return patterns
    
    # Action implementation methods
    def _handle_exception_action(self, exception: Exception, severity: ErrorSeverity) -> Dict:
        """Handle exception via action interface"""
        if exception is None:
            return {"error": "No exception provided"}
        
        error_context = self.handle_exception(exception, severity)
        return {
            "action": "handled_exception",
            "error_context": self._error_context_to_dict(error_context)
        }
    
    def _clear_error_history(self) -> Dict:
        """Clear error history"""
        old_count = len(self._error_history)
        self._error_history.clear()
        return {"action": "cleared_history", "removed_errors": old_count}
    
    def _set_severity_mapping(self, action: str) -> Dict:
        """Set severity mapping for exception type"""
        # Parse action like "set severity FileNotFoundError HIGH"
        parts = action.split()
        if len(parts) < 4:
            return {"error": "Invalid severity command"}
        
        exception_name = parts[2]
        severity_name = parts[3].upper()
        
        try:
            severity = ErrorSeverity(severity_name.lower())
            # This is simplified - in real implementation, would need proper exception type lookup
            return {
                "action": "set_severity",
                "exception_type": exception_name,
                "severity": severity.value,
                "status": "would_be_set"
            }
        except ValueError:
            return {"error": f"Invalid severity: {severity_name}"}
    
    def _register_recovery_strategy(self, action: str, kwargs: Dict) -> Dict:
        """Register recovery strategy for exception type"""
        strategy = kwargs.get('strategy')
        exception_type = kwargs.get('exception_type')
        
        if not strategy or not exception_type:
            return {"error": "Need both strategy and exception_type"}
        
        # In real implementation, would register the strategy
        return {
            "action": "register_recovery",
            "exception_type": str(exception_type),
            "status": "would_be_registered"
        }
    
    # Format methods
    def _format_json(self, data: Dict) -> str:
        """Format as JSON"""
        import json
        return json.dumps(data, indent=2, default=str)
    
    def _format_discord(self, data: Dict) -> str:
        """Format errors for Discord"""
        if "errors" in data:
            lines = [f"🚨 **Error Report ({data['count']}):**"]
            for error in data["errors"][-5:]:  # Last 5 for Discord
                severity_emoji = {"critical": "💥", "high": "🔥", "medium": "⚠️", "low": "ℹ️"}
                emoji = severity_emoji.get(error["severity"], "❌")
                time_str = error["timestamp"][:19]  # Remove microseconds
                lines.append(f"{emoji} `{time_str}` **{error['error_type']}** in {error['module']}")
                lines.append(f"   {error['message'][:80]}{'...' if len(error['message']) > 80 else ''}")
            return "\n".join(lines)
        
        elif "total" in data:  # Stats
            return f"📊 **Error Stats:** {data['total']} total | 💥 {data.get('by_severity', {}).get('critical', 0)} critical | 🔥 {data.get('by_severity', {}).get('high', 0)} high"
        
        return f"🚨 {data}"
    
    def _format_text(self, data: Dict) -> str:
        """Format as plain text"""
        if "errors" in data:
            lines = []
            for error in data["errors"]:
                time_str = error["timestamp"][:19]
                lines.append(f"[{time_str}] {error['severity'].upper()} {error['error_type']} in {error['module']}.{error['function']}")
                lines.append(f"  Message: {error['message']}")
                lines.append("")
            return "\n".join(lines)
        
        return str(data)
    
    def _format_html(self, data: Dict) -> str:
        """Format as HTML"""
        if "errors" in data:
            html = "<table border='1'><tr><th>Time</th><th>Severity</th><th>Type</th><th>Module</th><th>Message</th></tr>"
            for error in data["errors"]:
                color = {"critical": "#dc3545", "high": "#fd7e14", "medium": "#ffc107", "low": "#28a745"}.get(error["severity"], "#6c757d")
                time_str = error["timestamp"][:19]
                html += f"<tr><td>{time_str}</td><td style='color:{color}'>{error['severity']}</td><td>{error['error_type']}</td><td>{error['module']}</td><td>{error['message'][:100]}</td></tr>"
            html += "</table>"
            return html
        
        return f"<pre>{data}</pre>"
    
    def _format_csv(self, data: Dict) -> str:
        """Format as CSV"""
        if "errors" in data:
            lines = ["timestamp,severity,error_type,module,function,message"]
            for error in data["errors"]:
                message = error['message'].replace(',', ';').replace('\n', ' ')
                lines.append(f"{error['timestamp']},{error['severity']},{error['error_type']},{error['module']},{error['function']},{message}")
            return "\n".join(lines)
        
        return str(data)
    
    def _format_summary(self, data: Dict) -> str:
        """Format as summary"""
        if "errors" in data:
            return f"Error report: {data['count']} errors"
        elif "total" in data:
            return f"Error stats: {data['total']} total errors, {data.get('by_severity', {}).get('critical', 0)} critical"
        
        return str(data)
    
    # Helper methods
    def _error_context_to_dict(self, ctx: ErrorContext) -> Dict:
        """Convert ErrorContext to dictionary"""
        return {
            "timestamp": ctx.timestamp.isoformat(),
            "severity": ctx.severity.value,
            "module": ctx.module,
            "function": ctx.function,
            "error_type": ctx.error_type,
            "message": ctx.message,
            "recovery_attempted": ctx.recovery_attempted,
            "recovery_successful": ctx.recovery_successful,
            "context_data": ctx.context_data
        }
    
    def _extract_number(self, text: str, default: int) -> int:
        """Extract number from text"""
        import re
        match = re.search(r'\b(\d+)\b', text)
        return int(match.group(1)) if match else default

# Create service instances
error_handler = RefactoredErrorHandler(prefer_network=False)  # Local-first
error_handler_network = RefactoredErrorHandler(prefer_network=True)  # Network-first

# Backward compatibility functions
def handle_exception(exception: Exception, severity: Union[ErrorSeverity, str] = None, **context) -> ErrorContext:
    """Handle exception (backward compatible)"""
    return error_handler.handle_exception(exception, severity, **context)

def handle_errors(severity: Union[ErrorSeverity, str] = ErrorSeverity.MEDIUM):
    """Decorator for automatic error handling (backward compatible)"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_exception(e, severity)
                raise
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the refactored error handler service
    print("🧪 Testing Refactored Error Handler Service")
    
    # Test local-first service
    print("\n1. Testing local-first error handler:")
    eh_local = RefactoredErrorHandler(prefer_network=False)
    
    # Simulate some errors
    try:
        raise ValueError("Test error message")
    except Exception as e:
        eh_local.handle_exception(e, ErrorSeverity.MEDIUM)
    
    try:
        raise ConnectionError("Network timeout")
    except Exception as e:
        eh_local.handle_exception(e, ErrorSeverity.HIGH)
    
    # Test queries
    recent = eh_local.ask("recent errors")
    print(f"Recent errors: {eh_local.tell('discord', recent)}")
    
    stats = eh_local.ask("error stats")
    print(f"Error stats: {eh_local.tell('summary', stats)}")
    
    # Test network-first service
    print("\n2. Testing network-first error handler:")
    eh_network = RefactoredErrorHandler(prefer_network=True)
    
    critical_errors = eh_network.ask("critical errors")
    print(f"Critical errors: {eh_network.tell('text', critical_errors)}")
    
    # Test backward compatibility
    print("\n3. Testing backward compatibility:")
    try:
        raise FileNotFoundError("Missing config file")
    except Exception as e:
        handle_exception(e, "HIGH")
    
    print("\n✅ Refactored error handler test complete!")
    print("💡 Same error handling, but now with service locator and distributed capabilities!")