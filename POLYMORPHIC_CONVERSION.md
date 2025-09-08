# Polymorphic Conversion Guide

## 🎯 The Goal: Just 3 Methods for EVERYTHING

We're converting the entire codebase from 200+ specific methods to just THREE universal methods:
- `ask()` - Query anything
- `tell()` - Format/explain anything  
- `do()` - Perform any action

## ✅ What's Been Converted

### 1. Universal Base Class (`universal_polymorphic.py`)
- Created `UniversalPolymorphic` base class
- All objects inherit from this
- Provides default implementations of ask/tell/do
- Subclasses override `_handle_ask()`, `_handle_tell()`, `_handle_do()`

### 2. Go Entry Point (`go_polymorphic.py`)
- Converted from 50+ command-line flags to polymorphic methods
- Examples:
  ```python
  # OLD: ./go.py --discord-bot
  # NEW: go.do("start discord bot")
  
  # OLD: ./go.py --sync
  # NEW: go.do("sync")
  
  # OLD: ./go.py --service-status
  # NEW: go.ask("running services")
  ```

### 3. Discord Bridge (`discord_polymorphic.py`)
- Converted from specific methods to polymorphic pattern
- Examples:
  ```python
  # OLD: discord.connect()
  # NEW: discord.do("connect")
  
  # OLD: discord.send_message(channel, text)
  # NEW: discord.do("send", message=text)
  
  # OLD: discord.is_connected()
  # NEW: discord.ask("connected")
  ```

### 4. Twilio Bridge (`twilio_polymorphic.py`)
- Converted telephony operations to polymorphic pattern
- Examples:
  ```python
  # OLD: twilio.make_call(number, message)
  # NEW: twilio.do("call 555-1234", message="Hello")
  
  # OLD: twilio.send_sms(to, body)
  # NEW: twilio.do("send sms", to="...", body="...")
  
  # OLD: twilio.get_phone_number()
  # NEW: twilio.ask("phone")
  ```

## 🔄 Conversion Pattern

### Step 1: Inherit from Universal Base
```python
# OLD
class MyService:
    def __init__(self):
        # initialization
    
    def get_status(self):
        return self.status
    
    def start_service(self):
        # start logic
    
    def stop_service(self):
        # stop logic

# NEW
from universal_polymorphic import UniversalPolymorphic

class MyService(UniversalPolymorphic):
    def __init__(self):
        # initialization
        super().__init__()  # IMPORTANT: Call parent init
    
    def _handle_ask(self, question, **kwargs):
        if 'status' in str(question).lower():
            return self.status
        return super()._handle_ask(question, **kwargs)
    
    def _handle_do(self, action, **kwargs):
        act = str(action).lower()
        if 'start' in act:
            # start logic
            return "Started"
        if 'stop' in act:
            # stop logic
            return "Stopped"
        return super()._handle_do(action, **kwargs)
```

### Step 2: Map Old Methods to Polymorphic Methods

| Old Method | New Polymorphic Call |
|------------|---------------------|
| `obj.get_winner()` | `obj.ask("winner")` |
| `obj.get_top_8()` | `obj.ask("top 8")` |
| `obj.calculate_stats()` | `obj.do("calculate stats")` |
| `obj.format_for_discord()` | `obj.tell("discord")` |
| `obj.to_json()` | `obj.tell("json")` |
| `obj.save()` | `obj.do("save")` |
| `obj.sync()` | `obj.do("sync")` |

### Step 3: Handle Intent Polymorphically

```python
def _handle_ask(self, question, **kwargs):
    """Parse natural language and figure out intent"""
    q = str(question).lower()
    
    # Check for keywords
    if any(word in q for word in ['winner', 'first', 'champion']):
        return self._get_winner()
    
    if any(word in q for word in ['top', 'placement']):
        # Extract number if present
        import re
        match = re.search(r'\d+', q)
        n = int(match.group()) if match else 8
        return self._get_top_n(n)
    
    # Default to parent handler
    return super()._handle_ask(question, **kwargs)
```

## 📝 TODO: Modules Still to Convert

### High Priority
1. **Tournament Models** (`tournament_models.py`)
   - 237 methods to consolidate into ask/tell/do
   - Make Tournament, Player, Organization inherit from PolymorphicModel
   
2. **Database Service** (`database_service.py`)
   - Convert all query methods to polymorphic pattern
   
3. **Sync Service** (`sync_service.py`)
   - Convert sync operations to do() method

### Medium Priority
4. **Editor Service** (`editor_service.py`)
5. **Claude Service** (`claude_service.py`)
6. **Heatmap Generator** (`heatmap_advanced.py`)

### Low Priority
7. Helper modules and utilities
8. Test files

## 🚀 Benefits of Polymorphic Pattern

1. **Simplicity**: Just 3 methods to remember instead of 200+
2. **Consistency**: Same interface for everything
3. **Natural Language**: Use intent instead of memorizing method names
4. **Discoverability**: Objects can list their capabilities
5. **Extensibility**: Easy to add new behaviors without new methods
6. **Self-Documenting**: Objects explain themselves via tell()

## 💡 Usage Examples

```python
# Everything uses the same 3 methods!

# Services
service.ask("status")          # Get status
service.tell("json")           # Get JSON representation
service.do("restart")          # Restart service

# Models
model.ask("data")              # Get data
model.tell("discord")          # Format for Discord
model.do("save")               # Save to database

# Bridges
bridge.ask("connected")        # Check connection
bridge.tell("status")          # Get full status
bridge.do("connect")           # Connect

# The pattern is UNIVERSAL!
```

## 🎯 End Goal

When complete, the ENTIRE codebase will use just these 3 methods:
- No more method proliferation
- No more documentation needed for method names
- Objects understand natural language intent
- True object-oriented polymorphism

This is the ULTIMATE simplification!