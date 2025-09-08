#!/usr/bin/env python3
"""
supercharged_logger.py - Database-backed Python object logger
No more files! Store rich Python objects, full context, and make everything queryable.
"""
import sys
import traceback
import pickle
import json
import uuid
import inspect
import gc
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
from collections import deque, Counter
from threading import Lock

from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import Session

from database import session_scope, get_session
from log_database_models import LogEntry, LogAggregation, LogSnapshot
from polymorphic_core import announcer


class SuperchargedLogger:
    """
    A logger that stores Python objects in the database instead of writing to files.
    Every log entry is a rich, queryable object with full context.
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
        """Initialize the supercharged logger"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._context_stack = []
        self._correlation_id = None
        self._parent_stack = []
        self._buffer = deque(maxlen=100)  # Buffer for batch writes
        self._write_batch_size = 10
        self._stats = Counter()
        
        # Create tables if they don't exist
        self._ensure_tables()
        
        # Announce ourselves via Bonjour
        announcer.announce(
            "Supercharged Logger",
            [
                "I store logs as Python objects in the database",
                "No more stupid files!",
                "Full object serialization",
                "Rich querying and analytics",
                "Automatic performance tracking"
            ],
            ["logger.log_object(my_complex_object)", "logger.query(level='ERROR')"]
        )
    
    def _ensure_tables(self):
        """Ensure log tables exist"""
        from database import engine, Base
        from log_database_models import LogEntry, LogAggregation, LogSnapshot
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine, tables=[
            LogEntry.__table__,
            LogAggregation.__table__,
            LogSnapshot.__table__
        ])
    
    @contextmanager
    def context(self, name: str, **extra):
        """Context manager for nested operations"""
        context_info = {
            'name': name,
            'start': datetime.utcnow(),
            'extra': extra
        }
        self._context_stack.append(context_info)
        
        # Log context entry
        self.debug(f"→ Entering: {name}", category='context')
        
        try:
            yield self
        finally:
            elapsed = (datetime.utcnow() - context_info['start']).total_seconds()
            self.debug(f"← Exiting: {name} ({elapsed:.3f}s)", 
                      category='context', execution_time=elapsed)
            self._context_stack.pop()
    
    @contextmanager
    def correlation(self, correlation_id: Optional[str] = None):
        """Group related log entries with a correlation ID"""
        old_correlation = self._correlation_id
        self._correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            yield self._correlation_id
        finally:
            self._correlation_id = old_correlation
    
    def _get_caller_info(self) -> Dict[str, Any]:
        """Get information about the calling function"""
        frame = inspect.currentframe()
        # Go up the stack to find the actual caller (skip logger methods)
        for _ in range(3):
            if frame.f_back:
                frame = frame.f_back
        
        return {
            'module': frame.f_globals.get('__name__', 'unknown'),
            'function': frame.f_code.co_name,
            'line_number': frame.f_lineno,
            'filename': frame.f_code.co_filename
        }
    
    def _create_log_entry(self, level: str, message: str, 
                         obj: Any = None, **kwargs) -> LogEntry:
        """Create a log entry with all context"""
        caller = self._get_caller_info()
        
        entry = LogEntry(
            level=level,
            message=message,
            module=caller['module'],
            function=caller['function'],
            line_number=caller['line_number'],
            timestamp=datetime.utcnow(),
            correlation_id=self._correlation_id
        )
        
        # Add context stack
        if self._context_stack:
            contexts = [c['name'] for c in self._context_stack]
            entry.context_stack = json.dumps(contexts)
        
        # Store Python object if provided
        if obj is not None:
            entry.set_python_object(obj)
        
        # Add extra data
        extra_data = {}
        for key, value in kwargs.items():
            if key in ['category', 'subcategory', 'execution_time', 'memory_usage']:
                setattr(entry, key, value)
            else:
                extra_data[key] = value
        
        if extra_data:
            entry.set_extra_data(extra_data)
        
        # Create searchable text
        search_parts = [message, level, caller['module']]
        if 'category' in kwargs:
            search_parts.append(kwargs['category'])
        entry.search_text = ' '.join(str(p) for p in search_parts)
        
        # Update stats
        self._stats[level] += 1
        
        return entry
    
    def _write_entry(self, entry: LogEntry):
        """Write entry to database (with buffering)"""
        self._buffer.append(entry)
        
        # Flush if buffer is full
        if len(self._buffer) >= self._write_batch_size:
            self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush buffered entries to database"""
        if not self._buffer:
            return
        
        try:
            with session_scope() as session:
                while self._buffer:
                    entry = self._buffer.popleft()
                    session.add(entry)
                session.commit()
        except Exception as e:
            # Announce error but don't fail
            announcer.announce(
                "Logger Error",
                [f"Failed to write logs to database: {e}"]
            )
    
    # Main logging methods
    
    def debug(self, message: str, obj: Any = None, **kwargs):
        """Log debug message with optional Python object"""
        entry = self._create_log_entry('DEBUG', message, obj, **kwargs)
        self._write_entry(entry)
    
    def info(self, message: str, obj: Any = None, **kwargs):
        """Log info message with optional Python object"""
        entry = self._create_log_entry('INFO', message, obj, **kwargs)
        self._write_entry(entry)
    
    def warning(self, message: str, obj: Any = None, **kwargs):
        """Log warning message with optional Python object"""
        entry = self._create_log_entry('WARNING', message, obj, **kwargs)
        self._write_entry(entry)
    
    def error(self, message: str, obj: Any = None, **kwargs):
        """Log error message with optional Python object"""
        entry = self._create_log_entry('ERROR', message, obj, **kwargs)
        self._write_entry(entry)
    
    def critical(self, message: str, obj: Any = None, **kwargs):
        """Log critical message with optional Python object"""
        entry = self._create_log_entry('CRITICAL', message, obj, **kwargs)
        self._write_entry(entry)
    
    def exception(self, message: str, exc: Optional[Exception] = None, **kwargs):
        """Log exception with full traceback"""
        if exc is None:
            exc_info = sys.exc_info()
            exc = exc_info[1]
        
        entry = self._create_log_entry('ERROR', message, exc, **kwargs)
        
        # Add exception details
        entry.exception_type = type(exc).__name__ if exc else 'Unknown'
        entry.exception_message = str(exc) if exc else ''
        entry.traceback = traceback.format_exc()
        
        self._write_entry(entry)
    
    def log_object(self, name: str, obj: Any, level: str = 'INFO', **kwargs):
        """Log any Python object with full serialization"""
        message = f"Object logged: {name}"
        entry = self._create_log_entry(level, message, obj, **kwargs)
        entry.category = 'object'
        entry.subcategory = type(obj).__name__
        self._write_entry(entry)
    
    def log_bonjour(self, service: str, announcement: List[str]):
        """Log Bonjour announcements"""
        message = f"Service announcement: {service}"
        obj = {'service': service, 'announcements': announcement}
        entry = self._create_log_entry('INFO', message, obj, 
                                     category='bonjour', subcategory=service)
        self._write_entry(entry)
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """Log performance metrics"""
        message = f"Performance: {operation} took {duration:.3f}s"
        entry = self._create_log_entry('INFO', message, metrics,
                                     category='performance',
                                     execution_time=duration)
        self._write_entry(entry)
    
    # Query methods
    
    def query(self, level: Optional[str] = None,
             module: Optional[str] = None,
             category: Optional[str] = None,
             since: Optional[datetime] = None,
             limit: int = 100,
             correlation_id: Optional[str] = None) -> List[Dict]:
        """Query logs from database - returns dicts to avoid session issues"""
        with session_scope() as session:
            query = session.query(LogEntry)
            
            if level:
                query = query.filter(LogEntry.level == level)
            if module:
                query = query.filter(LogEntry.module.like(f'%{module}%'))
            if category:
                query = query.filter(LogEntry.category == category)
            if since:
                query = query.filter(LogEntry.timestamp >= since)
            if correlation_id:
                query = query.filter(LogEntry.correlation_id == correlation_id)
            
            results = query.order_by(desc(LogEntry.timestamp)).limit(limit).all()
            # Convert to dicts before session closes
            return [r.to_dict() for r in results]
    
    def get_errors(self, since: Optional[datetime] = None, limit: int = 50) -> List[Dict]:
        """Get recent errors as dictionaries"""
        return self.query(level='ERROR', since=since, limit=limit)
    
    def get_by_correlation(self, correlation_id: str) -> List[Dict]:
        """Get all logs for a correlation ID as dictionaries"""
        return self.query(correlation_id=correlation_id, limit=1000)
    
    def search(self, text: str, limit: int = 100) -> List[Dict]:
        """Full text search in logs - returns dicts"""
        with session_scope() as session:
            results = session.query(LogEntry).filter(
                LogEntry.search_text.like(f'%{text}%')
            ).order_by(desc(LogEntry.timestamp)).limit(limit).all()
            return [r.to_dict() for r in results]
    
    def get_statistics(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get logging statistics"""
        with session_scope() as session:
            query = session.query(LogEntry)
            if since:
                query = query.filter(LogEntry.timestamp >= since)
            
            # Count by level
            level_counts = {}
            for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                count = query.filter(LogEntry.level == level).count()
                level_counts[level.lower()] = count
            
            # Top modules
            top_modules = session.query(
                LogEntry.module,
                func.count(LogEntry.id).label('count')
            ).group_by(LogEntry.module).order_by(desc('count')).limit(10).all()
            
            # Top categories
            top_categories = session.query(
                LogEntry.category,
                func.count(LogEntry.id).label('count')
            ).filter(LogEntry.category.isnot(None)).group_by(
                LogEntry.category
            ).order_by(desc('count')).limit(10).all()
            
            # Performance stats
            perf_stats = session.query(
                func.avg(LogEntry.execution_time).label('avg_time'),
                func.max(LogEntry.execution_time).label('max_time'),
                func.min(LogEntry.execution_time).label('min_time')
            ).filter(LogEntry.execution_time.isnot(None)).first()
            
            return {
                'level_counts': level_counts,
                'total_logs': sum(level_counts.values()),
                'top_modules': [(m, c) for m, c in top_modules],
                'top_categories': [(c, count) for c, count in top_categories],
                'performance': {
                    'avg_execution_time': perf_stats.avg_time if perf_stats else 0,
                    'max_execution_time': perf_stats.max_time if perf_stats else 0
                },
                'memory_stats': self._stats
            }
    
    def cleanup_old_logs(self, days: int = 30):
        """Remove logs older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with session_scope() as session:
            deleted = session.query(LogEntry).filter(
                LogEntry.timestamp < cutoff
            ).delete()
            session.commit()
            
            self.info(f"Cleaned up {deleted} old log entries", 
                     category='maintenance')
    
    def take_snapshot(self, snapshot_type: str = 'system'):
        """Take a snapshot of current system state"""
        snapshot = LogSnapshot(
            snapshot_type=snapshot_type,
            announcement_count=len(announcer.announcements) if hasattr(announcer, 'announcements') else 0,
            error_rate=self._stats['ERROR'] / max(sum(self._stats.values()), 1)
        )
        
        # Capture current state
        snapshot.capture_current_state()
        
        with session_scope() as session:
            session.add(snapshot)
            session.commit()
        
        self.info(f"System snapshot taken: {snapshot_type}", category='snapshot')
    
    def __del__(self):
        """Flush buffer on destruction"""
        if hasattr(self, '_buffer'):
            self._flush_buffer()


# Global instance
logger = SuperchargedLogger()

# Convenience functions
log = logger.info
log_error = logger.error
log_object = logger.log_object
log_performance = logger.log_performance
with_context = logger.context
with_correlation = logger.correlation

# Hook into Bonjour announcements
def _log_announcement(service_name: str, capabilities: List[str], examples: Optional[List[str]] = None):
    """Automatically log all Bonjour announcements"""
    logger.log_bonjour(service_name, capabilities)

# Register as Bonjour listener
announcer.add_listener(_log_announcement)