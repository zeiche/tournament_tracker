# Process Management Migration Guide

## 🚀 Unified Service Identity System

This guide explains how to migrate existing services and create new services using the unified process management system with database-backed tracking.

## ✅ System Overview

The tournament tracker now uses a **unified service identity system** that provides:
- **Database-backed process tracking** via `ServiceState` model  
- **Process titles** visible in `ps` (e.g., `tournament-web-editor`)
- **Automatic service registration/unregistration**
- **Process discovery** without relying on PID tables
- **Graceful shutdown** with context managers
- **Service hunting** to find and kill processes by name

## 🏗️ Architecture Components

### Core Components:
- **`polymorphic_core/service_identity.py`** - Main system implementation
- **`database/tournament_models.py`** - ServiceState model for tracking
- **`utils/service_management.py`** - CLI tools for service management
- **`ManagedService`** - Base class for all services
- **`ProcessKiller`** - Process hunting and termination utilities

### Database Schema:
```sql
CREATE TABLE service_state (
    id INTEGER PRIMARY KEY,
    service_name VARCHAR UNIQUE NOT NULL,
    pid INTEGER,
    status VARCHAR DEFAULT 'stopped',
    started_at TIMESTAMP,
    data JSON,  -- polymorphic storage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Migration Pattern

### Before (Old Pattern):
```python
#!/usr/bin/env python3
"""old_service.py - Old style service"""

from http.server import HTTPServer, BaseHTTPRequestHandler

def run_server():
    server = HTTPServer(('0.0.0.0', 8080), MyHandler)
    print("Starting server...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    run_server()
```

### After (New Pattern):
```python
#!/usr/bin/env python3
"""
new_service.py - Unified service with identity system
Now uses ManagedService for process tracking and management.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import os

# Add path for imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')
from polymorphic_core.service_identity import ManagedService


class MyServiceManaged(ManagedService):
    """
    Managed version of MyService with unified service identity.
    Provides automatic process tracking and graceful shutdown.
    """
    
    def __init__(self, port: int = 8080, host: str = '0.0.0.0'):
        # Service name must be unique, process title for ps visibility
        super().__init__("my-service", "tournament-my-service")
        self.port = port
        self.host = host
        self.server = None
    
    def run(self):
        """Run the service - implement your service logic here"""
        self.server = HTTPServer((self.host, self.port), MyHandler)
        print(f"🚀 Starting MyService on port {self.port}")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("🛑 Shutting down MyService...")
            if self.server:
                self.server.shutdown()


def main():
    """Main function for running as a managed service"""
    import argparse
    parser = argparse.ArgumentParser(description='My Service')
    parser.add_argument('--port', type=int, default=8080, help='Port')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host')
    args = parser.parse_args()
    
    # Context manager handles registration/cleanup automatically
    with MyServiceManaged(args.port, args.host) as service:
        service.run()


if __name__ == '__main__':
    main()
```

## 🎯 Step-by-Step Migration Checklist

### 1. Add Imports
```python
from polymorphic_core.service_identity import ManagedService
```

### 2. Create Managed Service Class
- Inherit from `ManagedService`
- Choose unique `service_name` (used in database)
- Choose descriptive `process_title` (visible in `ps`)

### 3. Implement `run()` Method
- Move existing service logic to `run()` method
- Add proper error handling and cleanup

### 4. Update `main()` Function
- Use context manager pattern: `with MyServiceManaged() as service:`
- Add argument parsing if needed

### 5. Test the Service
```bash
# Start service
python3 services/my_service.py

# Check status (in another terminal)
python3 utils/service_management.py --service-status

# Kill service
python3 utils/service_management.py --kill my-service
```

## 🔍 Process Management Commands

### Service Status
```bash
# Via go.py
./go.py --service-status

# Direct
python3 utils/service_management.py --service-status
```

### Kill Services
```bash
# Kill specific service
python3 utils/service_management.py --kill service-name

# Kill all services
python3 utils/service_management.py --restart-services
```

### Process Discovery
The system can find processes multiple ways:
1. **Database lookup** - Fastest, for managed services
2. **Process title matching** - Finds `tournament-*` processes  
3. **Command line pattern matching** - Finds by script names
4. **Comprehensive discovery** - Scans for all tournament-related processes

## 📋 Naming Conventions

### Service Names (Database):
- Use **kebab-case**: `web-editor`, `claude-service`, `sync-service`
- Must be **unique** across the system
- Used for database tracking and service commands

### Process Titles (ps visibility):  
- Use **tournament-** prefix: `tournament-web-editor`
- Descriptive: `tournament-claude-service`
- Visible in `ps aux` output for easy identification

### Examples:
```python
# Good
super().__init__("web-editor", "tournament-web-editor")
super().__init__("claude-chat", "tournament-claude-chat") 
super().__init__("sync-service", "tournament-sync-service")

# Bad  
super().__init__("WebEditor", "web_editor")  # Wrong case
super().__init__("service", "service")       # Not descriptive
super().__init__("web-editor", "web-editor") # Missing prefix
```

## ⚡ Advanced Features

### Custom Service Data
Store additional metadata in the database:
```python
def run(self):
    # Register with custom data
    self.register(
        port=self.port,
        version="1.0.0",
        features=["search", "analytics"]
    )
```

### Service Dependencies
Check if other services are running:
```python
from polymorphic_core.service_identity import ProcessKiller

def run(self):
    # Check if dependency is running
    if not ProcessKiller.list_services():
        print("⚠️ No database service found")
        return
```

### Background Services
For services that should run in background:
```python
import threading

class BackgroundService(ManagedService):
    def run(self):
        # Start background threads
        worker = threading.Thread(target=self._background_worker)
        worker.daemon = True
        worker.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
```

## 🚨 Common Migration Issues

### 1. Import Errors
**Problem**: Module import failures
**Solution**: Add proper path configuration:
```python
sys.path.append('/home/ubuntu/claude/tournament_tracker')
```

### 2. Database Connection Issues  
**Problem**: ServiceState table doesn't exist
**Solution**: Run database migration:
```python
from database.tournament_models import ServiceState, get_session
from utils.database import engine
ServiceState.metadata.create_all(engine)
```

### 3. Duplicate Service Names
**Problem**: `IntegrityError: UNIQUE constraint failed`
**Solution**: Choose unique service names or the system will handle updates automatically

### 4. Permission Errors
**Problem**: Cannot kill processes
**Solution**: Ensure services run with proper permissions

## 📊 Migration Status

### ✅ Already Migrated:
- `services/polymorphic_web_editor.py` ✅
- `services/claude_cli_service.py` ✅  
- `services/interactive_service.py` ✅
- `services/startgg_sync.py` ✅
- `services/web_services.py` ✅
- `services/web_search.py` ✅

### 🔄 Needs Migration:
- `services/web_editor.py`
- `services/message_handler.py` (if needed as standalone)
- `services/report_service.py` (if needed as standalone)
- Background daemons in `experimental/`
- Network services in `networking/`
- Audio services in `polymorphic_core/audio/`

### 🚀 Testing Your Migration:

1. **Start service**: `python3 services/your_service.py`
2. **Check database**: Service should appear in `./go.py --service-status`
3. **Check process title**: `ps aux | grep tournament-` should show your service
4. **Test killing**: `./go.py --restart-services` should terminate it
5. **Test discovery**: System should find it even if not in database

## 🎯 Best Practices

1. **Always use context managers**: `with MyService() as service:`
2. **Handle cleanup gracefully**: Stop servers, close connections
3. **Use descriptive names**: Make services easy to identify  
4. **Add proper logging**: Include service name in log messages
5. **Test thoroughly**: Verify registration, discovery, and termination
6. **Document dependencies**: Note what other services are required

## 🔮 Future Enhancements

- **Service health checks**: Automatic monitoring and restart
- **Service dependencies**: Automatic startup ordering
- **Load balancing**: Multiple instances of same service
- **Remote management**: Kill services across multiple machines
- **Performance metrics**: Track CPU, memory usage per service
- **Service discovery**: Automatic endpoint discovery for networking

This unified system eliminates the "process management is a bitch" problem by providing consistent, reliable, database-backed service tracking across the entire tournament tracker codebase!