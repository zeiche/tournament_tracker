#!/usr/bin/env python3
"""
log_database_models.py - Database models for storing Python objects as logs
No more stupid files! Everything goes in the database as rich Python objects.
"""
import pickle
import json
from datetime import datetime
from typing import Any, Dict, Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, LargeBinary, Float, Index, desc
from sqlalchemy.ext.hybrid import hybrid_property
from database import Base


class LogEntry(Base):
    """
    Database model for storing log entries as Python objects.
    Each log is a rich object with full context, not just a string.
    """
    __tablename__ = 'log_entries'
    
    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(20), index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    module = Column(String(100), index=True)
    function = Column(String(100))
    line_number = Column(Integer)
    
    # Message and context
    message = Column(Text)
    context_stack = Column(Text)  # JSON list of context names
    
    # Rich Python object storage
    python_object = Column(LargeBinary)  # Pickled Python object
    extra_data = Column(Text)  # JSON for simple data
    
    # Performance metrics
    execution_time = Column(Float)  # For operations that have duration
    memory_usage = Column(Integer)  # Bytes of memory used
    
    # Classification
    category = Column(String(50), index=True)  # api, database, bonjour, etc.
    subcategory = Column(String(50))  # Specific type within category
    
    # Error tracking
    exception_type = Column(String(100))
    exception_message = Column(Text)
    traceback = Column(Text)
    
    # Correlation
    correlation_id = Column(String(100), index=True)  # To group related logs
    parent_id = Column(Integer)  # For nested operations
    
    # Search optimization
    search_text = Column(Text)  # Denormalized searchable text
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_timestamp_level', 'timestamp', 'level'),
        Index('ix_module_category', 'module', 'category'),
        Index('ix_correlation', 'correlation_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<LogEntry {self.id}: {self.level} - {self.message[:50]}>"
    
    @hybrid_property
    def is_error(self) -> bool:
        """Check if this is an error log"""
        return self.level in ['ERROR', 'CRITICAL']
    
    @hybrid_property
    def has_exception(self) -> bool:
        """Check if this log has exception info"""
        return self.exception_type is not None
    
    def get_python_object(self) -> Any:
        """Deserialize the stored Python object"""
        if self.python_object:
            try:
                return pickle.loads(self.python_object)
            except:
                return None
        return None
    
    def set_python_object(self, obj: Any):
        """Serialize and store a Python object"""
        try:
            self.python_object = pickle.dumps(obj)
        except:
            # If object can't be pickled, store its string representation
            self.python_object = pickle.dumps(str(obj))
    
    def get_extra_data(self) -> Dict:
        """Get extra data as dictionary"""
        if self.extra_data:
            try:
                return json.loads(self.extra_data)
            except:
                return {}
        return {}
    
    def set_extra_data(self, data: Dict):
        """Set extra data from dictionary"""
        try:
            self.extra_data = json.dumps(data)
        except:
            self.extra_data = json.dumps({"error": "Could not serialize data"})
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for easy viewing"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'level': self.level,
            'module': self.module,
            'function': self.function,
            'line': self.line_number,
            'message': self.message,
            'category': self.category,
            'subcategory': self.subcategory,
            'execution_time': self.execution_time,
            'has_exception': self.has_exception,
            'correlation_id': self.correlation_id
        }


class LogAggregation(Base):
    """
    Pre-computed aggregations for fast analytics.
    Updated periodically to provide instant statistics.
    """
    __tablename__ = 'log_aggregations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    period_start = Column(DateTime, index=True)
    period_end = Column(DateTime, index=True)
    aggregation_type = Column(String(50))  # hourly, daily, module, etc.
    
    # Counts by level
    debug_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    
    # Performance metrics
    avg_execution_time = Column(Float)
    max_execution_time = Column(Float)
    total_memory_usage = Column(Integer)
    
    # Top items (stored as JSON)
    top_modules = Column(Text)  # JSON list of top modules
    top_errors = Column(Text)  # JSON list of common errors
    top_categories = Column(Text)  # JSON list of top categories
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def get_top_modules(self) -> List[str]:
        """Get top modules list"""
        if self.top_modules:
            try:
                return json.loads(self.top_modules)
            except:
                return []
        return []
    
    def get_error_summary(self) -> Dict:
        """Get error summary"""
        return {
            'errors': self.error_count,
            'warnings': self.warning_count,
            'critical': self.critical_count,
            'error_rate': (self.error_count + self.critical_count) / 
                         (self.debug_count + self.info_count + self.warning_count + 
                          self.error_count + self.critical_count)
                         if (self.debug_count + self.info_count) > 0 else 0
        }


class LogSnapshot(Base):
    """
    Snapshots of system state at specific moments.
    Useful for debugging and understanding system behavior.
    """
    __tablename__ = 'log_snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    snapshot_type = Column(String(50))  # system, error, performance, etc.
    
    # System state
    active_modules = Column(Text)  # JSON list of active modules
    memory_usage = Column(Integer)  # Total memory usage
    active_connections = Column(Integer)  # Database connections, etc.
    
    # Bonjour announcements
    active_services = Column(Text)  # JSON list of announced services
    announcement_count = Column(Integer)
    
    # Performance
    recent_slow_queries = Column(Text)  # JSON list of slow operations
    error_rate = Column(Float)  # Errors per minute
    
    # Full Python state (be careful with size!)
    system_state = Column(LargeBinary)  # Pickled system state
    
    def get_system_state(self) -> Any:
        """Get the full system state"""
        if self.system_state:
            try:
                return pickle.loads(self.system_state)
            except:
                return None
        return None
    
    def capture_current_state(self):
        """Capture current system state"""
        import sys
        import gc
        import resource
        
        state = {
            'modules': list(sys.modules.keys()),
            'objects': len(gc.get_objects()),
            'memory': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            self.system_state = pickle.dumps(state)
        except:
            pass
        
        self.active_modules = json.dumps(state['modules'][:50])  # First 50 modules
        self.memory_usage = state['memory']