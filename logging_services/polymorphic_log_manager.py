#!/usr/bin/env python3
"""
Polymorphic Log Manager - Database-backed logging with local bonjour
Stores polymorphic log entries in database "log" table
"""

import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional, Union, List
from polymorphic_core.local_bonjour import local_announcer
from polymorphic_core import register_capability

# Add parent directory to path for imports
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

class PolymorphicLogManager:
    """Database-backed polymorphic logging service with local bonjour"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self._database = None
        
        # Announce our polymorphic logging capabilities
        local_announcer.announce("PolymorphicLogManager", [
            "I log polymorphic data to database",
            "I store structured log entries in 'log' table",
            "I accept any data type: objects, dicts, strings, errors",
            "I provide ask/tell/do interface for log queries",
            "Use me for all structured logging needs"
        ])
        
        print("🗂️ Polymorphic Log Manager initialized with database backend")
    
    @property
    def database(self):
        """Lazy load database service via service locator"""
        if self._database is None:
            try:
                from polymorphic_core.service_locator import get_service
                self._database = get_service("database", prefer_network=False)
            except ImportError:
                # Fallback to direct import if service locator not available
                from utils.database_service import database_service
                self._database = database_service
        return self._database
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query log entries using natural language"""
        query_lower = query.lower().strip()
        
        if "recent" in query_lower or "latest" in query_lower:
            # Get recent log entries directly with IDs for web interface
            return self._get_recent_logs_with_ids(query)
        
        elif "errors" in query_lower or "error" in query_lower:
            return self.database.ask("log errors")
        
        elif "warnings" in query_lower or "warning" in query_lower:
            return self.database.ask("log warnings")
        
        elif "count" in query_lower or "stats" in query_lower:
            return self.database.ask("log stats")
        
        elif "today" in query_lower:
            return self.database.ask("log entries today")
        
        else:
            # Search in message content or data
            search_term = query.replace("search", "").replace("find", "").strip()
            if search_term:
                return self.database.ask(f"log entries containing {search_term}")
            
            return self.database.ask("recent log entries")
    
    def tell(self, format_type: str, data: Any = None) -> str:
        """Format log data for output"""
        format_lower = format_type.lower().strip()
        
        if data is None:
            data = self.ask("recent 10")
        
        if format_lower == "discord":
            return self._format_for_discord(data)
        elif format_lower == "json":
            return json.dumps(data, indent=2, default=str)
        elif format_lower == "summary":
            return self._format_summary(data)
        elif format_lower == "table":
            return self._format_as_table(data)
        else:
            return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform logging actions using natural language"""
        action_lower = action.lower().strip()
        
        if action_lower.startswith("log "):
            # Extract log level and message
            parts = action[4:].split(" ", 1)
            if len(parts) == 2:
                level, message = parts
                return self.log(level.upper(), message, **kwargs)
            else:
                return self.log("INFO", parts[0], **kwargs)
        
        elif action_lower.startswith("clear "):
            # Clear logs by criteria
            if "old" in action_lower or "older" in action_lower:
                return self.database.do("DELETE FROM log WHERE timestamp < datetime('now', '-30 days')")
            elif "all" in action_lower:
                return self.database.do("DELETE FROM log")
            elif "errors" in action_lower:
                return self.database.do("DELETE FROM log WHERE level = 'ERROR'")
        
        elif action_lower == "create table":
            return self._ensure_log_table()
        
        elif action_lower == "optimize":
            return self.database.do("VACUUM; REINDEX log;")
        
        elif action_lower.startswith("visualize "):
            # Get visualization data for a log entry
            log_id = action[10:].strip()
            return self._get_visualization_data(log_id)
        
        elif action_lower.startswith("delete "):
            # Delete a specific log entry by ID
            log_id = action[7:].strip()
            return self._delete_log_entry(log_id)
        
        else:
            return f"Unknown logging action: {action}"
    
    def log(self, level: str, message: str, data: Any = None, source: Optional[str] = None, **extra) -> bool:
        """Core polymorphic logging method"""
        try:
            # Ensure log table exists
            self._ensure_log_table()
            
            # Prepare log entry
            timestamp = datetime.now().isoformat()
            
            # Auto-detect source if not provided
            if source is None:
                frame = sys._getframe(1)
                source = frame.f_globals.get('__name__', 'unknown')
            
            # Serialize polymorphic data
            serialized_data = self._serialize_polymorphic_data(data)
            
            # Store extra metadata
            metadata = {
                'extra': extra,
                'python_type': type(data).__name__ if data is not None else 'None'
            }
            
            # Insert into database using direct session
            from utils.database import session_scope
            from sqlalchemy import text
            
            try:
                with session_scope() as session:
                    session.execute(text("""
                    INSERT INTO log (timestamp, level, message, source, data, metadata)
                    VALUES (:timestamp, :level, :message, :source, :data, :metadata)
                    """), {
                        'timestamp': timestamp,
                        'level': level,
                        'message': message,
                        'source': source,
                        'data': serialized_data,
                        'metadata': json.dumps(metadata)
                    })
                    session.commit()
            except Exception as e:
                print(f"🗂️ Failed to insert log entry: {e}")
            
            # Also print to console for immediate feedback
            print(f"🗂️ [{timestamp[:19]}] {level} {source}: {message}")
            if data is not None and level in ['ERROR', 'WARNING']:
                print(f"    Data: {serialized_data[:200]}...")
            
            return True
            
        except Exception as e:
            print(f"🗂️ LOG ERROR: Failed to log message: {e}")
            return False
    
    def _ensure_log_table(self):
        """Ensure the log table exists"""
        from utils.database import session_scope
        from sqlalchemy import text
        
        statements = [
            """CREATE TABLE IF NOT EXISTS log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                source TEXT,
                data TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            "CREATE INDEX IF NOT EXISTS idx_log_timestamp ON log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_log_level ON log(level)",
            "CREATE INDEX IF NOT EXISTS idx_log_source ON log(source)"
        ]
        
        try:
            with session_scope() as session:
                for stmt in statements:
                    session.execute(text(stmt))
                session.commit()
        except Exception as e:
            print(f"🗂️ Failed to create log table: {e}")
    
    def _serialize_polymorphic_data(self, data: Any) -> str:
        """Serialize any type of data for database storage"""
        if data is None:
            return ""
        
        try:
            # Check if this is a visualizable object
            from polymorphic_core.visualizable import VisualizableObject, is_visualizable
            
            if isinstance(data, VisualizableObject):
                # Store both the original data and visualization metadata
                return json.dumps({
                    'original_data': str(data),
                    'visualizable': True,
                    'visualization_data': data.visualize()
                })
            elif is_visualizable(data):
                # Auto-convert to visualizable and store
                from polymorphic_core.visualizable import make_visualizable
                visualizable = make_visualizable(data)
                return json.dumps({
                    'original_data': data if isinstance(data, (str, dict, list)) else str(data),
                    'visualizable': True,
                    'visualization_data': visualizable.visualize()
                })
            
            # Standard serialization for non-visualizable data
            if isinstance(data, str):
                return data
            elif isinstance(data, (dict, list)):
                return json.dumps(data, default=str)
            elif hasattr(data, '__dict__'):
                # Object with attributes
                return json.dumps(data.__dict__, default=str)
            elif isinstance(data, Exception):
                # Exception objects
                return f"{type(data).__name__}: {str(data)}"
            else:
                return str(data)
        except Exception as e:
            return f"[Serialization Error: {e}] {type(data).__name__}"
    
    def _get_visualization_data(self, log_id: str) -> Dict[str, Any]:
        """Retrieve visualization data for a log entry by ID"""
        try:
            from utils.database import session_scope
            from sqlalchemy import text
            
            with session_scope() as session:
                result = session.execute(text("""
                    SELECT data, metadata FROM log WHERE id = :log_id
                """), {'log_id': log_id}).fetchone()
                
                if not result:
                    return {'error': f'Log entry {log_id} not found'}
                
                data_str, metadata_str = result
                
                # Try to parse as JSON to see if it contains visualization data
                try:
                    data = json.loads(data_str)
                    if isinstance(data, dict) and data.get('visualizable'):
                        return data['visualization_data']
                except (json.JSONDecodeError, KeyError):
                    pass
                
                # If not visualizable, return basic info
                return {
                    'type': 'text',
                    'content': data_str,
                    'mime_type': 'text/plain',
                    'metadata': {'description': 'Non-visualizable log data'}
                }
                
        except Exception as e:
            return {'error': f'Failed to retrieve visualization data: {e}'}
    
    def _delete_log_entry(self, log_id: str) -> bool:
        """Delete a log entry by ID"""
        try:
            from utils.database import session_scope
            from sqlalchemy import text
            
            with session_scope() as session:
                # Check if log entry exists
                result = session.execute(text("""
                    SELECT id FROM log WHERE id = :log_id
                """), {'log_id': log_id}).fetchone()
                
                if not result:
                    print(f"🗂️ Log entry {log_id} not found")
                    return False
                
                # Delete the log entry
                session.execute(text("""
                    DELETE FROM log WHERE id = :log_id
                """), {'log_id': log_id})
                session.commit()
                
                print(f"🗂️ Log entry {log_id} deleted successfully")
                return True
                
        except Exception as e:
            print(f"🗂️ Failed to delete log entry {log_id}: {e}")
            return False
    
    def _get_recent_logs_with_ids(self, query: str) -> List[Dict[str, Any]]:
        """Get recent log entries including database IDs for web interface"""
        try:
            from utils.database import session_scope
            from sqlalchemy import text
            
            # Extract limit from query if specified
            limit = 50  # default
            if "recent" in query:
                words = query.split()
                for i, word in enumerate(words):
                    if word.isdigit():
                        limit = int(word)
                        break
            
            with session_scope() as session:
                result = session.execute(text("""
                    SELECT id, timestamp, level, message, source, data, metadata 
                    FROM log 
                    ORDER BY timestamp DESC 
                    LIMIT :limit
                """), {'limit': limit}).fetchall()
                
                logs = []
                for row in result:
                    log_entry = {
                        'id': row[0],
                        'timestamp': row[1],
                        'level': row[2],
                        'message': row[3],
                        'source': row[4],
                        'data': row[5],
                        'metadata': row[6]
                    }
                    logs.append(log_entry)
                
                return logs
                
        except Exception as e:
            print(f"🗂️ Failed to get recent logs: {e}")
            return []
    
    def _format_for_discord(self, data: Any) -> str:
        """Format log data for Discord output"""
        if not data:
            return "No log entries found"
        
        if isinstance(data, list):
            lines = ["**Recent Log Entries:**"]
            for i, entry in enumerate(data[:10]):
                if isinstance(entry, dict):
                    timestamp = entry.get('timestamp', '')[:16]  # YYYY-MM-DD HH:MM
                    level = entry.get('level', 'INFO')
                    message = entry.get('message', '')[:100]
                    source = entry.get('source', '')
                    lines.append(f"{i+1}. `{timestamp}` **{level}** `{source}`: {message}")
                else:
                    lines.append(f"{i+1}. {str(entry)[:100]}")
            return "\n".join(lines)
        else:
            return f"**Log Data:** {str(data)[:500]}"
    
    def _format_summary(self, data: Any) -> str:
        """Format log data as summary"""
        if not data or not isinstance(data, list):
            return "No log data to summarize"
        
        levels = {}
        sources = {}
        for entry in data:
            if isinstance(entry, dict):
                level = entry.get('level', 'UNKNOWN')
                source = entry.get('source', 'unknown')
                levels[level] = levels.get(level, 0) + 1
                sources[source] = sources.get(source, 0) + 1
        
        summary = [f"**Log Summary ({len(data)} entries):**"]
        summary.append("**By Level:**")
        for level, count in sorted(levels.items()):
            summary.append(f"  {level}: {count}")
        
        summary.append("**Top Sources:**")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
            summary.append(f"  {source}: {count}")
        
        return "\n".join(summary)
    
    def _format_as_table(self, data: Any) -> str:
        """Format log data as a simple table"""
        if not data or not isinstance(data, list):
            return "No log data"
        
        lines = ["Timestamp        | Level   | Source           | Message"]
        lines.append("-" * 70)
        
        for entry in data[:20]:  # Limit to 20 entries
            if isinstance(entry, dict):
                timestamp = entry.get('timestamp', '')[:16]
                level = entry.get('level', 'INFO')[:7]
                source = entry.get('source', 'unknown')[:15]
                message = entry.get('message', '')[:30]
                lines.append(f"{timestamp:<16} | {level:<7} | {source:<15} | {message}")
        
        return "\n".join(lines)
    
    # Convenience methods for common log levels
    def debug(self, message: str, data: Any = None, **kwargs):
        """Log debug message"""
        return self.log("DEBUG", message, data, **kwargs)
    
    def info(self, message: str, data: Any = None, **kwargs):
        """Log info message"""
        return self.log("INFO", message, data, **kwargs)
    
    def warning(self, message: str, data: Any = None, **kwargs):
        """Log warning message"""
        return self.log("WARNING", message, data, **kwargs)
    
    def error(self, message: str, data: Any = None, **kwargs):
        """Log error message"""
        return self.log("ERROR", message, data, **kwargs)
    
    def critical(self, message: str, data: Any = None, **kwargs):
        """Log critical message"""
        return self.log("CRITICAL", message, data, **kwargs)

# Global instance
_log_manager = None

def get_log_manager():
    """Get or create the global log manager instance"""
    global _log_manager
    if _log_manager is None:
        _log_manager = PolymorphicLogManager()
    return _log_manager

# Register as discoverable capability
register_capability("logger", get_log_manager)
register_capability("log_manager", get_log_manager)

# Create global instance to announce capabilities
log_manager = get_log_manager()

# Convenience functions for direct use
def log_info(message: str, data: Any = None, **kwargs):
    """Log info message"""
    return log_manager.info(message, data, **kwargs)

def log_warning(message: str, data: Any = None, **kwargs):
    """Log warning message"""
    return log_manager.warning(message, data, **kwargs)

def log_error(message: str, data: Any = None, **kwargs):
    """Log error message"""
    return log_manager.error(message, data, **kwargs)

def log_debug(message: str, data: Any = None, **kwargs):
    """Log debug message"""
    return log_manager.debug(message, data, **kwargs)

def log_critical(message: str, data: Any = None, **kwargs):
    """Log critical message"""
    return log_manager.critical(message, data, **kwargs)

# Go.py switch for testing log entries
def add_test_logs(args=None):
    """Handler for --test-logs switch - adds custom log entry or sample entries"""
    import random
    from datetime import datetime, timedelta
    
    # Check if custom text was provided
    if args and hasattr(args, 'test_logs') and args.test_logs is not None and len(args.test_logs) > 0:
        # User provided custom text - log it as INFO
        custom_text = ' '.join(args.test_logs)
        print(f"📝 Logging custom message: {custom_text}")
        
        log_manager.info(
            message=custom_text,
            source="user_input",
            data={"via": "go.py --test-logs", "timestamp": datetime.now().isoformat()}
        )
        
        print(f"✅ Added custom log entry")
        return f"Added custom log entry: {custom_text}"
    
    # No custom text - add sample test entries
    print("🧪 Adding sample test log entries...")
    
    # Sample messages for testing
    test_messages = [
        ("INFO", "System startup completed", {"startup_time": "2.3s", "modules": 15}),
        ("WARNING", "Discord connection slow", {"latency": "350ms", "retry_count": 2}),
        ("ERROR", "Database connection failed", {"error": "timeout", "retry_in": "30s"}),
        ("DEBUG", "Processing tournament data", {"tournaments": 42, "players": 156}),
        ("INFO", "Web service started", {"port": 8081, "interface": "0.0.0.0"}),
        ("CRITICAL", "Service memory limit reached", {"memory": "98%", "pid": 12345}),
        ("WARNING", "API rate limit approaching", {"requests": 485, "limit": 500}),
        ("INFO", "Log rotation completed", {"old_size": "50MB", "new_size": "2MB"}),
        ("ERROR", "Authentication failed", {"user": "test_user", "attempts": 3}),
        ("DEBUG", "Cache cleanup", {"removed": 234, "remaining": 1567})
    ]
    
    # Add test entries with slight time variations
    base_time = datetime.now()
    for i, (level, message, data) in enumerate(test_messages):
        # Vary the timestamp slightly for each entry
        timestamp = base_time - timedelta(minutes=random.randint(1, 60))
        
        log_manager.log(
            level=level,
            message=message,
            data=data,
            source=f"test_source_{i % 3}",  # Vary source
            timestamp=timestamp.isoformat()
        )
    
    print(f"✅ Added {len(test_messages)} sample test log entries")
    return f"Added {len(test_messages)} sample test log entries to database"

# Register the switch with dynamic_switches
try:
    from utils.dynamic_switches import announce_switch
    announce_switch(
        flag="--test-logs",
        help="Add sample log entries (or custom message: --test-logs 'your message')",
        handler=add_test_logs,
        action='store',
        nargs='*'  # Accept zero or more arguments
    )
    print("🔧 Registered --test-logs switch")
except ImportError:
    print("⚠️  Could not register --test-logs switch (dynamic_switches not available)")