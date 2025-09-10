# Process Management Template

## Pattern: Add Self-Management to Existing Services

For any service that needs to manage multiple processes, follow this template:

### Step 1: Add imports to the service file

```python
#!/usr/bin/env python3
"""
[existing docstring - ADD SELF-MANAGEMENT NOTE]
Self-manages all [SERVICE_NAME] processes.
"""

import sys
import os
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

# [existing imports...]

try:
    from polymorphic_core import announcer
    from polymorphic_core.process_management import BaseProcessManager
except ImportError:
    # Fallback for compatibility
    class DummyAnnouncer:
        def announce(self, *args, **kwargs): pass
    announcer = DummyAnnouncer()
    BaseProcessManager = object
```

### Step 2: Add ProcessManager class to the service file

```python
class [ServiceName]ProcessManager(BaseProcessManager):
    """Process manager for [service description]"""
    
    SERVICE_NAME = "[ServiceName]"
    PROCESSES = [
        'script1.py',
        'script2.py',
        'subdirectory/script3.py'  # Can include subdirectories
    ]
    PORTS = [8080, 8081, 8082]  # List all ports used
    
    # If you need custom startup logic, override start_services():
    def start_services(self):
        """Custom startup if needed, otherwise use default"""
        # Clean up first
        self.cleanup_processes()
        
        # Wait for processes to die and ports to be released  
        import time
        time.sleep(1)
        
        # Custom startup logic here...
        from polymorphic_core.process import ProcessManager
        
        started_pids = []
        try:
            # Start services with custom args if needed
            proc1 = ProcessManager.start_service_safe('script1.py', check_existing=False)
            started_pids.append(proc1.pid)
            
            # Special args example:
            proc2 = ProcessManager.start_service_safe(
                'script2.py', '--special', 'args', 
                check_existing=False
            )
            started_pids.append(proc2.pid)
            
            announcer.announce(
                f"{self.SERVICE_NAME}ProcessManager",
                [f"Successfully started {len(started_pids)} processes: {started_pids}"]
            )
            
        except Exception as e:
            announcer.announce(
                f"{self.SERVICE_NAME}ProcessManager", 
                [f"Error during startup: {e}"]
            )
        
        return started_pids
```

### Step 3: Create global instance at end of service file

```python
# Create global process manager instance to announce capabilities
if BaseProcessManager != object:  # Only if we have the real class
    _[service]_process_manager = [ServiceName]ProcessManager()

# [rest of existing file...]
```

### Step 4: Update go.py to use the process manager

Find the relevant args handler and replace hardcoded patterns:

```python
elif args.[service_flag]:
    # Start [service] using self-managing service
    try:
        # Import the service file to get access to its process manager
        from [service_file] import _[service]_process_manager
        print("Starting [Service] services via integrated ProcessManager...")
        pids = _[service]_process_manager.start_services()
        print(f"[Service] services started with PIDs: {pids}")
    except (ImportError, NameError) as e:
        print(f"Integrated ProcessManager not available: {e}")
        # Fallback to old method if needed
        print("Falling back to manual process management...")
        # [existing hardcoded patterns as fallback]
```

## Next Service: Discord

### Analysis of current Discord patterns in go.py:

```python
# Found in --discord-bot:
ProcessManager.restart_service('bonjour_discord.py')

# Found in --restart-services:
ProcessManager.kill_pattern('discord')
ProcessManager.kill_pattern('polymorphic_discord')
ProcessManager.start_service_safe('bonjour_discord.py', check_existing=False)
```

### Discord Service Details:
- **Main file**: `bonjour_discord.py` 
- **Processes**: `['bonjour_discord.py']` (single process)
- **Ports**: `[]` (Discord uses WebSocket, no specific ports)
- **go.py flags**: `--discord-bot`, `--restart-services`

### Implementation for Discord:
1. Add ProcessManager to `bonjour_discord.py`
2. Update `--discord-bot` in go.py
3. Update `--restart-services` in go.py

## Next Service After Discord: Web Editor

### Analysis of current Web Editor patterns:

```python
# Found in --edit-contacts:
ProcessManager.restart_service('services/web_editor.py')

# Found in --restart-services:
ProcessManager.kill_pattern('web_editor')
ProcessManager.kill_pattern('editor_service')
ProcessManager.start_service_safe('services/web_editor.py', check_existing=False)
```

### Web Editor Service Details:
- **Main file**: `services/web_editor.py`
- **Processes**: `['services/web_editor.py']` (single process)
- **Ports**: `[8081]` (from advertisements: "port 8081")
- **go.py flags**: `--edit-contacts`, `--restart-services`

## Testing Checklist for Each Service:

1. ✅ Service file imports work without errors
2. ✅ ProcessManager instance is created successfully  
3. ✅ Service announces itself in advertisements
4. ✅ go.py can import and use the process manager
5. ✅ Service starts/stops cleanly via go.py
6. ✅ Fallback works if process manager fails
7. ✅ No zombie processes left behind

## Validation Commands:

```bash
# Test service announces itself:
python3 go.py --advertisements | grep -A 5 "[ServiceName]ProcessManager"

# Test service startup:
python3 go.py --[service-flag]

# Verify processes running:
ps aux | grep -E "[process patterns]" | grep -v grep

# Test cleanup:
python3 -c "from [service_file] import _[service]_process_manager; _[service]_process_manager.cleanup_processes()"
```