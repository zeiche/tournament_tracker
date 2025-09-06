# Bonjour-Style Service Discovery Integration

## Core Philosophy: Everything Announces Itself

Just like Bonjour/mDNS, every component in the system should announce:
- What it is
- What it can do
- What state it's in
- What it needs

## Integration Points - EVERYWHERE

### 1. Model Layer - Self-Announcing Models
```python
class Tournament(Base, AnnouncerMixin):
    """Tournament model that announces its capabilities"""
    
    def __init__(self):
        self.announce("Tournament instance created", 
                     capabilities=["track events", "calculate metrics"])
    
    @property
    def attendance(self):
        # When accessed, announce what's available
        self.announce_capability("attendance data available", value=self._attendance)
        return self._attendance
    
    def save(self):
        # Announce state changes
        self.announce_state_change("tournament saved", id=self.id)
        super().save()
```

### 2. Service Layer - Service Discovery
```python
class DiscordService:
    def __init__(self):
        self.announce_service(
            name="Discord Bot",
            capabilities=["receive messages", "send responses"],
            status="initializing"
        )
    
    async def on_ready(self):
        self.announce_status("ready", guilds=len(self.client.guilds))
```

### 3. Database Layer - Operation Announcements
```python
def get_session():
    announcer.announce("Database session requested")
    session = Session()
    session.info['announcer'] = SessionAnnouncer(session)
    return session

class SessionAnnouncer:
    def on_query(self, query):
        announcer.announce(f"Query executing: {query.statement[:50]}...")
    
    def on_commit(self):
        announcer.announce("Database changes committed")
```

### 4. Command Layer (go.py) - Command Discovery
```python
class TournamentCommand:
    def __init__(self):
        # Announce all available commands on init
        self.announce_commands()
    
    def announce_commands(self):
        for method_name in dir(self):
            if not method_name.startswith('_'):
                method = getattr(self, method_name)
                if callable(method):
                    announcer.announce_command(
                        name=method_name,
                        doc=method.__doc__,
                        available=True
                    )
```

### 5. Interactive Layer - Dynamic Discovery
```python
class InteractiveService:
    def start_repl(self):
        # Discover what's available RIGHT NOW
        announcements = announcer.get_current_announcements()
        print(f"Services available: {announcements}")
        
    def start_ai_chat(self):
        # Claude gets fresh announcements every time
        context = announcer.get_announcements_for_claude()
```

### 6. Query Layer - Query Capabilities
```python
def polymorphic_query(input_text):
    # Announce what patterns we can handle
    announcer.announce(
        "Query engine ready",
        patterns=["show top N", "player NAME", "recent tournaments"],
        current_capability="full" if db_connected else "limited"
    )
    # Process query...
```

## Implementation Strategy

### Phase 1: Core Announcer Infrastructure
- [x] Create capability_announcer.py
- [ ] Add AnnouncerMixin base class
- [ ] Create global announcement bus
- [ ] Add listeners/subscribers pattern

### Phase 2: Model Integration
- [ ] Add announcements to Tournament.__init__
- [ ] Add announcements to Player properties
- [ ] Add announcements to Organization methods
- [ ] Announce on all state changes

### Phase 3: Service Integration  
- [ ] Discord service announces connection status
- [ ] Database announces query patterns
- [ ] Claude service announces availability
- [ ] Web services announce endpoints

### Phase 4: Dynamic Discovery
- [ ] go.py discovers available commands at runtime
- [ ] Interactive mode shows live announcements
- [ ] Discord bot updates context per message
- [ ] Web UI shows service status

### Phase 5: State Broadcasting
- [ ] Models announce when data changes
- [ ] Services announce status changes
- [ ] Queries announce what they found
- [ ] Errors announce what went wrong

## Benefits of Deep Bonjour Integration

1. **Self-Documenting System**
   - Components explain themselves
   - No need for static documentation
   - Always up-to-date

2. **Dynamic Adaptation**
   - Claude knows what's available NOW
   - Services can come and go
   - Graceful degradation

3. **Debugging Paradise**
   - See what's happening in real-time
   - Trace operations through announcements
   - Understand system state

4. **Zero Configuration**
   - Services find each other
   - No hardcoded dependencies
   - Automatic discovery

## Example Flow

```
User: "Show top players"
   ↓
Discord receives message
   ↓
Discord announces: "Message received from user"
   ↓
Claude service announces: "Processing request"
   ↓
Query engine announces: "I can handle 'show top' patterns"
   ↓
Database announces: "Executing query for players"
   ↓
Player model announces: "Calculating rankings"
   ↓
Results announce: "Found 50 players"
   ↓
Claude announces: "Formatting response"
   ↓
Discord announces: "Sending response"
```

## Critical Integration Points

### MUST Have Announcements:
1. **Every model instantiation**
2. **Every service startup**
3. **Every database operation**
4. **Every state change**
5. **Every error/exception**
6. **Every successful operation**
7. **Every capability check**
8. **Every context switch**

### Announcement Format:
```python
{
    'timestamp': datetime.now(),
    'service': 'service_name',
    'event': 'what_happened',
    'capabilities': ['what_i_can_do'],
    'state': 'current_state',
    'context': {...},
    'available_to': ['claude', 'user', 'system']
}
```

## TODO for Full Integration

- [ ] Add announcer imports to ALL modules
- [ ] Create announcement decorators for methods
- [ ] Add state change hooks to SQLAlchemy
- [ ] Make go.py listen to announcements
- [ ] Create announcement viewer/debugger
- [ ] Add announcement filtering for Claude
- [ ] Create announcement history/replay
- [ ] Add announcement-based testing
- [ ] Document announcement patterns
- [ ] Create announcement dashboard

## The Vision

Every component in the system announces itself like a Bonjour service. Claude (and developers) can discover what's available in real-time without reading documentation or code. The system becomes self-aware and self-describing.

When you ask "what can you do?", Claude doesn't check documentation - it asks the services to announce themselves RIGHT NOW and tells you what's actually available.