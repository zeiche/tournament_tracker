# TODO: Self-Managing Process Cleanup Refactor

## Problem
Currently go.py has hardcoded process management patterns. Every refactor breaks Twilio because the cleanup logic is centralized and brittle. Services should manage their own processes.

## Vision: Services Self-Announce Their Process Management

Each service module should announce:
1. **What processes it manages** (script names, PIDs)
2. **What ports it uses** (for conflict prevention)  
3. **How to clean it up** (cleanup methods)
4. **Dependencies** (what must start first)

## Current Hardcoded Patterns in go.py
```python
# These should become self-managing:
ProcessManager.kill_pattern('twilio_simple_voice_bridge')
ProcessManager.kill_pattern('twiml_stream_server') 
ProcessManager.kill_pattern('twilio_stream_server')
ProcessManager.kill_pattern('polymorphic_encryption')
ProcessManager.kill_port(8087)
ProcessManager.kill_port(8086) 
ProcessManager.kill_port(8443)
```

## Step 1: Create ProcessManagementMixin ✅
Created `polymorphic_core/process_management.py` with `ProcessManagementMixin` and `BaseProcessManager`.

## Step 1.5: Create Self-Documenting Bonjour Guide ✅
Created `polymorphic_core/process_management_guide.py` that announces:
- **ProcessManagementGuide** - The proven 5-step pattern
- **NextService_Discord** - Analysis of Discord service to implement next
- **NextService_WebEditor** - Analysis of Web Editor service after Discord
- **ValidationCommands** - Testing commands for each implementation

**Key Innovation**: Instead of static documentation, the system now self-documents the implementation pattern via Bonjour announcements. Run `python3 go.py --advertisements` to see the live guide.

## Step 2: Refactor Service Modules

### Twilio Services
Create `services/twilio_process_manager.py`:
```python
class TwilioProcessManager(ProcessManagementMixin):
    PROCESSES = [
        'twilio_stream_server.py',
        'twiml_stream_server.py', 
        'polymorphic_encryption_service.py',
        'experimental/telephony/twilio_simple_voice_bridge.py'
    ]
    PORTS = [8087, 8086, 8443]
    
    def __init__(self):
        self.announce_process_management(
            "Twilio", self.PROCESSES, self.PORTS, "cleanup_processes"
        )
    
    def cleanup_processes(self):
        for process in self.PROCESSES:
            ProcessManager.kill_script(process)
        for port in self.PORTS:
            ProcessManager.kill_port(port)
    
    def start_services(self):
        self.cleanup_processes()
        time.sleep(1)
        for process in self.PROCESSES:
            ProcessManager.start_service_safe(process, check_existing=False)
```

### Discord Services  
Create `services/discord_process_manager.py`:
```python
class DiscordProcessManager(ProcessManagementMixin):
    PROCESSES = ['bonjour_discord.py', 'discord_bridge.py']
    PORTS = []  # Discord doesn't use specific ports
    
    def cleanup_processes(self):
        ProcessManager.kill_pattern('discord')
        ProcessManager.kill_pattern('polymorphic_discord')
```

### Web Editor Services
Create `services/web_editor_process_manager.py`:
```python
class WebEditorProcessManager(ProcessManagementMixin):
    PROCESSES = ['services/web_editor.py']
    PORTS = [8081]
    
    def cleanup_processes(self):
        ProcessManager.kill_pattern('web_editor')
        ProcessManager.kill_port(8081)
```

## Step 3: Refactor go.py Service Discovery

Replace hardcoded patterns with service discovery:

```python
def restart_services():
    """Discover and restart all process managers"""
    # Find all process management services
    process_managers = announcer.discover_services_by_capability("PROCESS_MANAGER")
    
    for manager in process_managers:
        manager.cleanup_processes()
    
    time.sleep(1)
    
    for manager in process_managers:
        if hasattr(manager, 'start_services'):
            manager.start_services()

def start_twilio_bridge():
    """Start Twilio using its self-managing service"""
    twilio_manager = announcer.discover_service("TwilioProcessManager")
    if twilio_manager:
        twilio_manager.start_services()
    else:
        print("TwilioProcessManager not found")
```

## Step 4: Services to Refactor (from advertisements)

### Core Services Already Self-Managing
- ✅ ProcessManager (already announces itself)
- ✅ Database Service (no processes to manage)
- ✅ Start.gg Sync Service (no processes to manage)

### Services Needing Process Management
1. **Audio Services** (from advertisements):
   - PolymorphicAudioPlayer
   - PolymorphicAudioProvider  
   - PolymorphicAudioRequest
   - PolymorphicOpusDecoder
   - PolymorphicTranscription
   - PolymorphicTTSService

2. **Web Services**:
   - Web Editor Service (port 8081)
   - OrganizationEditor  

3. **Telephony Services**:
   - Twilio bridge components (ports 8087, 8086, 8443)

4. **Math/Visualization Services** (likely no processes):
   - Statistical Math Service
   - Geometric Math Service  
   - Visualization Math Service
   - Data Transform Service
   - Heatmap Service
   - Chart Service
   - Map Service

## Step 5: Update go.py Command Handlers

Replace each hardcoded service starter:

```python
# OLD:
elif args.twilio_bridge:
    ProcessManager.kill_pattern('twilio_simple_voice_bridge')
    # ... lots of hardcoded patterns
    
# NEW:
elif args.twilio_bridge:
    service = discover_service("TwilioProcessManager")
    service.start_services()
```

## Step 6: Add Process Management Discovery

Add to `polymorphic_core/discovery.py`:

```python
def discover_process_managers() -> List[ProcessManagerProtocol]:
    """Find all services that can manage processes"""
    return discover_services_by_capability("PROCESS_MANAGER")

def cleanup_all_processes():
    """Emergency cleanup of all managed processes"""
    for manager in discover_process_managers():
        try:
            manager.cleanup_processes()
        except Exception as e:
            print(f"Error cleaning {manager}: {e}")
```

## Benefits

1. **Self-Documenting**: Services announce what they manage
2. **No More Hardcoding**: go.py discovers services dynamically
3. **Fault Isolation**: Each service knows how to clean itself up
4. **Extensible**: New services just implement the pattern
5. **Debuggable**: Process management is visible via advertisements

## Implementation Order

1. ✅ Create ProcessManagementMixin in polymorphic_core/
2. ✅ Implement TwilioProcessManager first (it's the most complex)  
3. ✅ Test Twilio service startup/cleanup
4. ✅ Refactor go.py to use integrated TwilioProcessManager from bridge file
5. ✅ Keep separate files but centralize process management in main service
6. ⬜ Implement DiscordProcessManager and WebEditorProcessManager
7. ⬜ Update other services that need process management
8. ⬜ Remove remaining hardcoded patterns from go.py
9. ⬜ Test full system restart

## Files to Create/Modify

### New Files:
- ✅ `polymorphic_core/process_management.py` - Base mixin and BaseProcessManager
- ✅ `polymorphic_core/process_management_guide.py` - Self-documenting Bonjour guide

### Modified Files:
- ✅ `experimental/telephony/twilio_simple_voice_bridge.py` - Added integrated TwilioProcessManager
- ✅ `go.py` - Updated --twilio-bridge to use integrated process manager 
- ✅ `polymorphic_core/__init__.py` - Import guide to trigger announcements
- ⬜ `bonjour_discord.py` - Add Discord process management
- ⬜ `services/web_editor.py` - Add web editor process management
- ⬜ `go.py` - Remove remaining hardcoded patterns for Discord/Web Editor

## Testing Strategy

1. Test each ProcessManager in isolation
2. Test service discovery from go.py
3. Test full system restart with `--restart-services`
4. Test individual service restarts (especially `--twilio-bridge`)
5. Test error handling when services fail to start

## Success Criteria

- ⬜ No hardcoded process patterns in go.py (Twilio ✅, Discord/Web Editor pending)
- ✅ Twilio services start reliably after any refactor
- ✅ Services self-describe their process management (Twilio ✅)
- ⬜ `python3 go.py --restart-services` works flawlessly 
- ✅ Individual service restarts work (--twilio-bridge ✅, --discord-bot pending, etc)
- ✅ Process cleanup is complete (no zombie processes)
- ✅ Port conflicts are prevented automatically

---

**CRITICAL**: This refactor must be implemented incrementally. Start with Twilio (the most problematic), prove it works, then generalize the pattern to other services.

## Live Implementation Guide

Instead of following this static TODO, use the live Bonjour guide:

```bash
# See current implementation guide and next steps:
python3 go.py --advertisements | grep -A 10 -E "ProcessManagementGuide|NextService"

# See testing commands:
python3 go.py --advertisements | grep -A 5 "ValidationCommands"
```

The system now self-documents what needs to be implemented next!