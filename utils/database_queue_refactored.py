#!/usr/bin/env python3
"""
database_queue_refactored.py - Database Queue System with Service Locator Pattern

This module provides paged queue operations using the service locator pattern
for transparent local/network service access.
"""

import time
import sys
import os
from collections import defaultdict, deque
from contextlib import contextmanager
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.database_queue_refactored")

from polymorphic_core.service_locator import get_service
from polymorphic_core.network_service_wrapper import NetworkServiceWrapper
from polymorphic_core import announcer


class OperationType(Enum):
    CREATE = "create"
    UPDATE = "update" 
    DELETE = "delete"
    CUSTOM = "custom"


@dataclass
class QueuedOperation:
    """Represents a queued database operation"""
    operation_type: OperationType
    model_class: Any
    data: Dict[str, Any]
    primary_key: Optional[str] = None
    callback: Optional[Callable] = None
    priority: int = 0  # Lower = higher priority (deletes first)


class DatabaseQueueRefactored:
    """
    Database queue system using service locator pattern.
    
    Provides queue operations with 3-method pattern:
    - ask(query): Query queue status and information
    - tell(format, data): Format queue data for output  
    - do(action): Perform queue operations
    """
    
    def __init__(self, page_size=250, auto_commit=True, prefer_network: bool = False):
        """Initialize with service locator dependencies"""
        self.page_size = page_size
        self.auto_commit = auto_commit
        self.prefer_network = prefer_network
        self.current_page = []
        self.error_queue = []
        
        # Service locator dependencies
        self._logger = None
        self._error_handler = None
        self._config = None
        self._database = None
        
        # Queue statistics
        self.stats = {
            'pages_processed': 0,
            'operations_successful': 0,
            'operations_failed': 0,
            'total_processing_time': 0,
            'items_processed': 0,
            'errors': [],
            'queue_size': 0,
            'last_operation': None,
            'last_operation_time': None
        }
    
    @property
    def logger(self):
        """Get logger service via service locator"""
        if self._logger is None:
            self._logger = get_service("logger", self.prefer_network)
        return self._logger
    
    @property
    def error_handler(self):
        """Get error handler service via service locator"""
        if self._error_handler is None:
            self._error_handler = get_service("error_handler", self.prefer_network)
        return self._error_handler
    
    @property
    def config(self):
        """Get config service via service locator"""
        if self._config is None:
            self._config = get_service("config", self.prefer_network)
        return self._config
    
    @property
    def database(self):
        """Get database service via service locator"""
        if self._database is None:
            self._database = get_service("database", self.prefer_network)
        return self._database
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query queue service information using natural language.
        
        Args:
            query: Natural language query about queue
            **kwargs: Additional query parameters
            
        Returns:
            Relevant queue information
        """
        query_lower = query.lower().strip()
        
        try:
            if "status" in query_lower or "health" in query_lower:
                return self._get_service_status()
            elif "stats" in query_lower or "statistics" in query_lower:
                return self.stats
            elif "queue size" in query_lower or "size" in query_lower:
                return {"queue_size": len(self.current_page), "page_size": self.page_size}
            elif "errors" in query_lower or "error queue" in query_lower:
                return {"error_queue": self.error_queue, "error_count": len(self.error_queue)}
            elif "history" in query_lower or "recent" in query_lower:
                return self._get_operation_history()
            elif "configuration" in query_lower or "config" in query_lower:
                return self._get_queue_configuration()
            elif "capabilities" in query_lower or "help" in query_lower:
                return self._get_capabilities()
            else:
                self.logger.warning(f"Unknown queue query: {query}")
                return {"error": f"Unknown query: {query}", "suggestions": self._get_capabilities()}
                
        except Exception as e:
            error_msg = f"Queue query failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"query": query})
            self.stats['errors'].append({"error": error_msg, "timestamp": datetime.now().isoformat()})
            return {"error": error_msg}
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """
        Format queue data for output.
        
        Args:
            format_type: Output format (discord, json, text, html)
            data: Data to format (uses current stats if None)
            
        Returns:
            Formatted string
        """
        if data is None:
            data = self.stats
            
        try:
            if format_type == "discord":
                return self._format_for_discord(data)
            elif format_type == "json":
                import json
                return json.dumps(data, indent=2, default=str)
            elif format_type == "text" or format_type == "console":
                return self._format_for_text(data)
            elif format_type == "html":
                return self._format_for_html(data)
            else:
                return str(data)
                
        except Exception as e:
            error_msg = f"Queue formatting failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"format": format_type, "data": data})
            return f"Error formatting data: {error_msg}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform queue operations using natural language.
        
        Args:
            action: Natural language action to perform
            **kwargs: Additional action parameters
            
        Returns:
            Action result
        """
        action_lower = action.lower().strip()
        self.stats['last_operation'] = action
        self.stats['last_operation_time'] = datetime.now().isoformat()
        
        try:
            if "add" in action_lower or "queue" in action_lower:
                operation_data = kwargs.get('operation_data', {})
                return self._add_operation(**operation_data)
            elif "process" in action_lower or "commit" in action_lower:
                return self._process_current_page()
            elif "flush" in action_lower or "process all" in action_lower:
                return self._flush_all_pages()
            elif "clear" in action_lower:
                if "errors" in action_lower:
                    return self._clear_error_queue()
                else:
                    return self._clear_queue()
            elif "retry errors" in action_lower or "retry" in action_lower:
                return self._retry_failed_operations()
            elif "reset stats" in action_lower:
                return self._reset_statistics()
            elif "test" in action_lower:
                return self._test_queue_system()
            else:
                self.logger.warning(f"Unknown queue action: {action}")
                return {"error": f"Unknown action: {action}", "suggestions": self._get_action_suggestions()}
                
        except Exception as e:
            error_msg = f"Queue action failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"action": action, "kwargs": kwargs})
            self.stats['errors'].append({"error": error_msg, "timestamp": datetime.now().isoformat()})
            return {"error": error_msg}
    
    def _add_operation(self, operation_type: str, model_class: Any = None, 
                      data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Add operation to queue"""
        try:
            # Convert string to enum
            if isinstance(operation_type, str):
                operation_type = OperationType(operation_type.lower())
            
            operation = QueuedOperation(
                operation_type=operation_type,
                model_class=model_class,
                data=data or {},
                primary_key=kwargs.get('primary_key'),
                callback=kwargs.get('callback'),
                priority=kwargs.get('priority', 0)
            )
            
            self.current_page.append(operation)
            self.stats['queue_size'] = len(self.current_page)
            
            # Auto-process if page is full
            if self.auto_commit and len(self.current_page) >= self.page_size:
                return self._process_current_page()
            
            return {
                "success": True,
                "operation_added": True,
                "queue_size": len(self.current_page),
                "will_auto_process": self.auto_commit and len(self.current_page) >= self.page_size
            }
            
        except Exception as e:
            error_msg = f"Failed to add operation: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg, {"operation_type": operation_type, "data": data})
            return {"error": error_msg}
    
    def _process_current_page(self) -> Dict[str, Any]:
        """Process current page of operations"""
        if not self.current_page:
            return {"success": True, "message": "No operations to process"}
        
        start_time = time.time()
        processed = 0
        failed = 0
        errors = []
        
        try:
            if self.logger:
                self.logger.info(f"Processing page with {len(self.current_page)} operations")
            
            # Sort by priority (deletes first)
            sorted_operations = sorted(self.current_page, key=lambda op: op.priority)
            
            for operation in sorted_operations:
                try:
                    success = self._process_single_operation(operation)
                    if success:
                        processed += 1
                    else:
                        failed += 1
                        self.error_queue.append(operation)
                except Exception as e:
                    failed += 1
                    error_info = {
                        "operation": operation,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    errors.append(error_info)
                    self.error_queue.append(operation)
                    if self.error_handler:
                        self.error_handler.handle_error(f"Operation failed: {e}", {"operation": operation})
            
            # Clear processed page
            self.current_page = []
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats['pages_processed'] += 1
            self.stats['operations_successful'] += processed
            self.stats['operations_failed'] += failed
            self.stats['total_processing_time'] += processing_time
            self.stats['items_processed'] += processed + failed
            self.stats['queue_size'] = 0
            self.stats['errors'].extend(errors)
            
            return {
                "success": True,
                "processed": processed,
                "failed": failed,
                "processing_time": processing_time,
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Page processing failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _process_single_operation(self, operation: QueuedOperation) -> bool:
        """Process a single queued operation"""
        try:
            if not self.database:
                return False
            
            if operation.operation_type == OperationType.CREATE:
                result = self.database.do("create", 
                                        model_class=operation.model_class,
                                        data=operation.data)
            elif operation.operation_type == OperationType.UPDATE:
                result = self.database.do("update",
                                        model_class=operation.model_class,
                                        primary_key=operation.primary_key,
                                        data=operation.data)
            elif operation.operation_type == OperationType.DELETE:
                result = self.database.do("delete",
                                        model_class=operation.model_class,
                                        primary_key=operation.primary_key)
            elif operation.operation_type == OperationType.CUSTOM:
                # For custom operations, expect a callable in the data
                custom_func = operation.data.get('function')
                if custom_func and callable(custom_func):
                    result = custom_func(**operation.data.get('args', {}))
                else:
                    result = {"error": "Custom operation requires callable function"}
            else:
                result = {"error": f"Unknown operation type: {operation.operation_type}"}
            
            # Call callback if provided
            if operation.callback and callable(operation.callback):
                try:
                    operation.callback(result)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Callback failed: {e}")
            
            return result and result.get('success', False)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Single operation failed: {e}")
            return False
    
    def _flush_all_pages(self) -> Dict[str, Any]:
        """Process all remaining operations"""
        try:
            if not self.current_page:
                return {"success": True, "message": "No operations to flush"}
            
            result = self._process_current_page()
            
            # Also process error queue if requested
            if self.error_queue:
                retry_result = self._retry_failed_operations()
                result["retry_result"] = retry_result
            
            return result
            
        except Exception as e:
            error_msg = f"Flush operation failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _clear_queue(self) -> Dict[str, Any]:
        """Clear the current queue"""
        try:
            cleared_count = len(self.current_page)
            self.current_page = []
            self.stats['queue_size'] = 0
            
            return {
                "success": True,
                "cleared_operations": cleared_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Queue clear failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _clear_error_queue(self) -> Dict[str, Any]:
        """Clear the error queue"""
        try:
            cleared_count = len(self.error_queue)
            self.error_queue = []
            
            return {
                "success": True,
                "cleared_errors": cleared_count,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Error queue clear failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _retry_failed_operations(self) -> Dict[str, Any]:
        """Retry failed operations from error queue"""
        try:
            if not self.error_queue:
                return {"success": True, "message": "No failed operations to retry"}
            
            retry_operations = self.error_queue.copy()
            self.error_queue = []
            
            # Add retry operations back to current page
            self.current_page.extend(retry_operations)
            self.stats['queue_size'] = len(self.current_page)
            
            # Process them
            result = self._process_current_page()
            result["retried_operations"] = len(retry_operations)
            
            return result
            
        except Exception as e:
            error_msg = f"Retry operation failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _reset_statistics(self) -> Dict[str, Any]:
        """Reset queue statistics"""
        try:
            old_stats = self.stats.copy()
            self.stats = {
                'pages_processed': 0,
                'operations_successful': 0,
                'operations_failed': 0,
                'total_processing_time': 0,
                'items_processed': 0,
                'errors': [],
                'queue_size': len(self.current_page),
                'last_operation': None,
                'last_operation_time': None
            }
            
            return {
                "success": True,
                "message": "Statistics reset",
                "previous_stats": old_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Statistics reset failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _test_queue_system(self) -> Dict[str, Any]:
        """Test the queue system"""
        try:
            if self.logger:
                self.logger.info("Testing queue system...")
            
            test_results = {}
            
            # Test service dependencies
            try:
                service_tests = {}
                service_tests["logger"] = self.logger is not None
                service_tests["error_handler"] = self.error_handler is not None
                service_tests["config"] = self.config is not None
                service_tests["database"] = self.database is not None
                test_results["services"] = service_tests
            except Exception as e:
                test_results["services"] = {"error": str(e)}
            
            # Test database connection if available
            if self.database:
                try:
                    db_test = self.database.ask("health")
                    test_results["database_connection"] = {"status": "ok", "result": db_test}
                except Exception as e:
                    test_results["database_connection"] = {"status": "error", "error": str(e)}
            
            # Test queue operations
            try:
                # Test adding an operation
                test_op_result = self._add_operation(
                    operation_type="create",
                    model_class="TestModel",
                    data={"test": "data"}
                )
                test_results["add_operation"] = test_op_result
                
                # Test queue status
                status = self.ask("queue size")
                test_results["queue_status"] = status
                
                # Clear test operation
                self._clear_queue()
                
            except Exception as e:
                test_results["queue_operations"] = {"error": str(e)}
            
            return {
                "success": True,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Queue system test failed: {e}"
            if self.error_handler:
                self.error_handler.handle_error(error_msg)
            return {"error": error_msg}
    
    def _get_service_status(self) -> Dict[str, Any]:
        """Get current queue service status"""
        try:
            return {
                "status": "running",
                "queue_size": len(self.current_page),
                "error_queue_size": len(self.error_queue),
                "page_size": self.page_size,
                "auto_commit": self.auto_commit,
                "stats": self.stats,
                "dependencies": {
                    "logger": self.logger is not None,
                    "error_handler": self.error_handler is not None,
                    "config": self.config is not None,
                    "database": self.database is not None
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Status check failed: {e}"}
    
    def _get_operation_history(self) -> Dict[str, Any]:
        """Get operation history"""
        return {
            "last_operation": self.stats.get('last_operation'),
            "last_operation_time": self.stats.get('last_operation_time'),
            "total_operations": self.stats.get('items_processed', 0),
            "successful_operations": self.stats.get('operations_successful', 0),
            "failed_operations": self.stats.get('operations_failed', 0),
            "pages_processed": self.stats.get('pages_processed', 0),
            "total_processing_time": self.stats.get('total_processing_time', 0),
            "recent_errors": self.stats.get('errors', [])[-10:]  # Last 10 errors
        }
    
    def _get_queue_configuration(self) -> Dict[str, Any]:
        """Get queue configuration"""
        return {
            "page_size": self.page_size,
            "auto_commit": self.auto_commit,
            "prefer_network": self.prefer_network,
            "current_queue_size": len(self.current_page),
            "error_queue_size": len(self.error_queue)
        }
    
    def _get_capabilities(self) -> List[str]:
        """Get list of available capabilities"""
        return [
            "add operation - Add operation to queue",
            "process - Process current page of operations",
            "flush - Process all remaining operations",
            "clear - Clear current queue",
            "clear errors - Clear error queue",
            "retry errors - Retry failed operations",
            "reset stats - Reset queue statistics",
            "test - Test queue system"
        ]
    
    def _get_action_suggestions(self) -> List[str]:
        """Get action suggestions"""
        return self._get_capabilities()
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, dict):
            if "error" in data:
                return f"❌ **Queue Error:** {data['error']}"
            elif "success" in data and data["success"]:
                if "processed" in data:
                    return f"⚙️ **Queue Processed:** {data['processed']} operations completed, {data.get('failed', 0)} failed"
                else:
                    return f"✅ **Queue Success:** Operation completed"
            elif "queue_size" in data or "pages_processed" in data:
                stats = data
                return f"""⚙️ **Database Queue Status:**
• Current Queue: {stats.get('queue_size', 0)} operations
• Pages Processed: {stats.get('pages_processed', 0)}
• Successful: {stats.get('operations_successful', 0)}
• Failed: {stats.get('operations_failed', 0)}
• Error Queue: {len(data.get('error_queue', []))} operations
• Total Time: {stats.get('total_processing_time', 0):.2f}s"""
        return f"⚙️ Queue: {str(data)}"
    
    def _format_for_text(self, data: Any) -> str:
        """Format data for text/console output"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{key}:")
                    for subkey, subvalue in value.items():
                        lines.append(f"  {subkey}: {subvalue}")
                elif isinstance(value, list):
                    lines.append(f"{key}: {len(value)} items")
                    for i, item in enumerate(value[:3]):  # Show first 3 items
                        lines.append(f"  {i+1}: {item}")
                    if len(value) > 3:
                        lines.append(f"  ... and {len(value)-3} more")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        return str(data)
    
    def _format_for_html(self, data: Any) -> str:
        """Format data for HTML output"""
        if isinstance(data, dict):
            html = "<table border='1'>"
            for key, value in data.items():
                if isinstance(value, dict):
                    html += f"<tr><td><strong>{key}</strong></td><td>"
                    html += "<table border='1'>"
                    for subkey, subvalue in value.items():
                        html += f"<tr><td>{subkey}</td><td>{subvalue}</td></tr>"
                    html += "</table></td></tr>"
                else:
                    html += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
            html += "</table>"
            return html
        return f"<pre>{str(data)}</pre>"


# Context manager for batch operations (backward compatibility)
@contextmanager
def batch_operations(page_size=250, prefer_network=False):
    """Context manager for batch database operations"""
    queue = DatabaseQueueRefactored(page_size=page_size, auto_commit=False, prefer_network=prefer_network)
    try:
        yield queue
    finally:
        # Process remaining operations on exit
        if queue.current_page:
            queue.do("process")


# Announce service capabilities
announcer.announce(
    "Database Queue Service (Refactored)",
    [
        "Database queue operations with 3-method pattern",
        "ask('queue size') - Query queue status and information",
        "tell('discord', data) - Format queue data for output",
        "do('add operation') - Perform queue operations",
        "Batch processing with page-based operations",
        "Uses service locator for transparent local/network operation"
    ],
    [
        "queue.ask('status')",
        "queue.do('add operation', operation_data={'operation_type': 'create', 'data': {}})",
        "queue.do('process')",
        "queue.tell('discord')"
    ]
)

# Singleton instance
database_queue_refactored = DatabaseQueueRefactored()

# Create network service wrapper for remote access
if __name__ != "__main__":
    try:
        wrapper = NetworkServiceWrapper(
            service=database_queue_refactored,
            service_name="database_queue_refactored",
            port_range=(9500, 9600)
        )
        # Auto-start network service in background
        wrapper.start_service_thread()
    except Exception as e:
        # Gracefully handle if network service fails
        pass


if __name__ == "__main__":
    # Test the refactored queue service
    print("🧪 Testing Refactored Database Queue Service")
    
    # Test local-first service
    print("\n1. Testing local-first service:")
    queue_service = DatabaseQueueRefactored(prefer_network=False)
    
    status = queue_service.ask("status")
    print(f"Status: {queue_service.tell('json', status)}")
    
    # Test adding operations
    print("\n2. Testing queue operations:")
    add_result = queue_service.do("add operation", 
                                 operation_data={
                                     'operation_type': 'create',
                                     'data': {'test': 'data'}
                                 })
    print(f"Add operation: {queue_service.tell('text', add_result)}")
    
    # Test queue status
    print("\n3. Testing queue status:")
    queue_status = queue_service.ask("queue size")
    print(f"Queue size: {queue_service.tell('text', queue_status)}")
    
    print("\n✅ Refactored queue service test complete!")
    print("💡 Same code works with local or network services!")
    print("🔥 Database queue with service locator pattern!")