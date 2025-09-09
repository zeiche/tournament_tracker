# Bonjour Implementation Guide

## What is Bonjour Pattern?

The Bonjour pattern is a self-announcing, zero-configuration service discovery system inspired by Apple's Bonjour/mDNS. Every component in our system:

1. **Announces itself** when it starts
2. **Broadcasts capabilities** in real-time
3. **Discovers other services** automatically
4. **Reports state changes** as they happen

## Core Principle: Everything Announces Everything

```python
# Traditional approach - silent and opaque
def process_data(data):
    result = transform(data)
    return result

# Bonjour approach - self-announcing and transparent
def process_data(data):
    announcer.announce("Processing data", [f"Size: {len(data)}"])
    result = transform(data)
    announcer.announce("Data processed", [f"Result size: {len(result)}"])
    return result
```

## Current Implementations

### 1. Bonjour Multi-Port Server (`bonjour_multi_server.py`)
Serves multiple HTTP services on different ports with unified announcement:

```python
# Serves on multiple ports simultaneously
sudo python3 bonjour_multi_server.py --ports 80 8080 8081 8443

# Port 80: ACME challenges for Let's Encrypt
# Port 8080: Webhooks and TwiML
# Port 8081: Status and monitoring
# Port 8443: HTTPS services
```

**Features:**
- Multi-threaded port handling
- Unified announcement across all ports
- Port-specific request routing
- Real-time activity broadcasting

### 2. Bonjour ACME Server (`bonjour_acme_server.py`)
Specialized server for Let's Encrypt certificate validation:

```python
# Announces every ACME challenge request
# Shows Let's Encrypt validation in real-time
sudo python3 bonjour_acme_server.py
```

### 3. Bonjour Twilio Service (`bonjour_twilio.py`)
Self-announcing telephony service:

```python
# Announces call events, SMS, transcriptions
# Auto-discovers Claude for AI responses
python3 experimental/telephony/bonjour_twilio.py
```

### 4. Capability Announcer (`capability_announcer.py`)
Core announcement infrastructure:

```python
from capability_announcer import CapabilityAnnouncer

announcer = CapabilityAnnouncer("my_service")
announcer.announce(
    "Service started",
    ["I can process data", "I can handle requests"],
    ["Example: process('data')", "Example: handle('/api')"]
)
```

## Implementation Patterns

### Pattern 1: Service Initialization
Every service announces itself on startup:

```python
class MyService:
    def __init__(self):
        self.announcer = CapabilityAnnouncer(self.__class__.__name__)
        self.announcer.announce(
            "Service initializing",
            [
                "I handle X functionality",
                "I integrate with Y service",
                "I listen on port Z"
            ]
        )
```

### Pattern 2: Operation Announcement
Every significant operation is announced:

```python
def fetch_data(self, query):
    self.announcer.announce("Fetching data", [f"Query: {query}"])
    
    try:
        data = self._execute_query(query)
        self.announcer.announce("Data fetched", [f"Rows: {len(data)}"])
        return data
    except Exception as e:
        self.announcer.announce("Fetch failed", [f"Error: {e}"])
        raise
```

### Pattern 3: State Change Broadcasting
State changes are immediately announced:

```python
def update_status(self, new_status):
    old_status = self.status
    self.status = new_status
    self.announcer.announce(
        "Status changed",
        [f"From: {old_status}", f"To: {new_status}"]
    )
```

### Pattern 4: Service Discovery
Services discover each other through announcements:

```python
def find_available_services():
    # Services announce their availability
    # Other services can discover them
    announcements = announcer.get_recent_announcements()
    available = [a for a in announcements if a['status'] == 'ready']
    return available
```

## Benefits of Bonjour Pattern

### 1. **Self-Documenting System**
- No need to read code to understand what's happening
- Services explain themselves in real-time
- Current state always visible

### 2. **Zero Configuration**
- Services find each other automatically
- No hardcoded dependencies
- Dynamic adaptation to available services

### 3. **Perfect Debugging**
- See exactly what's happening when
- Trace requests through the system
- Understand failures immediately

### 4. **Claude Integration**
- Claude can discover capabilities dynamically
- No need to update Claude's knowledge of services
- Real-time awareness of system state

## How to Add Bonjour to Your Code

### Step 1: Import the Announcer
```python
from capability_announcer import CapabilityAnnouncer
# or
from polymorphic_core import announcer
```

### Step 2: Initialize in Your Class
```python
def __init__(self):
    self.announcer = CapabilityAnnouncer(self.__class__.__name__)
    self._announce_capabilities()
```

### Step 3: Announce Capabilities
```python
def _announce_capabilities(self):
    self.announcer.announce(
        f"{self.__class__.__name__} ready",
        ["List what you can do"],
        ["Provide examples"]
    )
```

### Step 4: Announce Operations
```python
def important_method(self):
    self.announcer.announce("Starting important operation")
    # ... do work ...
    self.announcer.announce("Operation complete")
```

## Real-World Example: TwiML Server

```python
class BonjourTwiMLServer:
    def handle_call(self, request):
        # Announce incoming call
        self.announcer.announce(
            "Incoming call",
            [
                f"From: {request.get('From')}",
                f"To: {request.get('To')}",
                f"CallSid: {request.get('CallSid')}"
            ]
        )
        
        # Generate response
        response = self.generate_twiml(request)
        
        # Announce response
        self.announcer.announce(
            "TwiML response generated",
            [f"Response length: {len(response)}"]
        )
        
        return response
```

## Testing Bonjour Services

### Check if Service is Announcing:
```python
# In Python
from capability_announcer import CapabilityAnnouncer
announcer = CapabilityAnnouncer("test")
recent = announcer.get_recent_announcements()
print(recent)
```

### Monitor Announcements:
```bash
# Watch announcement log
tail -f storage/capability_announcements.log
```

### Test Multi-Port Server:
```bash
# Test different ports
curl http://localhost:80/.well-known/acme-challenge/test
curl http://localhost:8080/webhook
curl http://localhost:8081/status
```

## Best Practices

### DO:
- ✅ Announce service initialization
- ✅ Announce significant operations
- ✅ Announce errors and failures
- ✅ Announce state changes
- ✅ Keep announcements concise
- ✅ Include relevant context

### DON'T:
- ❌ Announce every tiny detail
- ❌ Include sensitive data in announcements
- ❌ Forget to announce failures
- ❌ Make announcements too verbose

## Future Enhancements

### 1. Announcement Filtering
- Filter by service
- Filter by type
- Filter by time range

### 2. Announcement Replay
- Replay announcements for debugging
- Time-travel debugging
- Event sourcing

### 3. Announcement Dashboard
- Web UI showing all announcements
- Real-time activity monitor
- Service health dashboard

### 4. Cross-Network Discovery
- Announcements over network
- Multi-machine service discovery
- Distributed system coordination

## Summary

The Bonjour pattern transforms our codebase from a silent, opaque system into a self-announcing, self-documenting, self-discovering ecosystem. Every component broadcasts what it is, what it can do, and what it's doing right now.

When you ask "what's happening?", the system tells you. When you ask "what can you do?", the services announce themselves. When something goes wrong, the failure announces itself.

This is the future of observable, debuggable, maintainable systems.