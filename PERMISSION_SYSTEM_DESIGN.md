# Permission System Design

## Overview
We need a deep, object-level permission system that makes objects adapt their behavior based on who's asking. This is NOT about authentication - it's about what players can do once they're in the system.

## Core Concept
**Objects themselves check permissions and adapt responses** - not enforced at Discord/bridge level but deep in the polymorphic model itself.

## Permission Structure

### Storage: Simple Dictionary in Database
```python
# Each player has a dictionary of permissions
player_permissions = {
    player_id: {
        "can_ask": True,
        "can_tell": True, 
        "can_do": False,
        "can_sync": False,
        "can_write": False,
        "can_delete": False,
        "can_calculate": True,
        "max_results": 100,
        "allowed_formats": ["discord", "brief"]
    }
}
```

### Default Permissions (for unknown users)
```python
DEFAULT_PERMISSIONS = {
    "can_ask": True,      # Can query information
    "can_tell": True,     # Can format output
    "can_do": False,      # Cannot perform actions
    "max_results": 50     # Limited results
}
```

## Adaptive Response Strategy (KEY DECISION: #3)

Objects should **adapt their responses** based on permission level, not just deny:

### Examples of Adaptive Responses:

1. **ask("statistics")**
   - Developer: Full internal stats, database IDs, error counts
   - Viewer: Public-safe summary, no internal details

2. **ask("player email")**
   - Developer: "player@email.com"
   - Viewer: "Contact info hidden"

3. **tell("discord")**
   - Developer: Includes debug info and IDs
   - Viewer: Clean public format only

4. **do("sync")**
   - Developer: Executes sync
   - Viewer: Returns "This would sync data (requires permission)"

## Implementation Approach

### 1. Permission Context Flow
Permission context should flow through the **database session**:
```python
session.player_id = player_id
session.permissions = get_player_permissions(player_id)
```

### 2. Modify PolymorphicModel Base
The base `ask()`, `tell()`, `do()` methods need to:
1. Check current permissions from session
2. Route to permission-appropriate internal methods
3. Return adapted responses

### 3. Permission Checking Pattern
```python
def ask(self, question, session=None):
    perms = session.permissions if session else DEFAULT_PERMISSIONS
    
    if not perms.get("can_ask", False):
        return "Viewing not permitted"
    
    # Route to permission-aware internal method
    if "statistics" in question:
        if perms.get("can_see_internal", False):
            return self._ask_statistics_full()
        else:
            return self._ask_statistics_public()
```

## Discord Integration

### Player Mapping
- Discord user sends message
- Look up their Discord ID → Player ID mapping
- Load player's permissions from database
- Pass permission context through to objects

### No SSO/OAuth/MFA needed!
Just a simple database lookup: "What can this player do?"

## Next Steps for Implementation

1. **Create Permission Storage**
   - Add permissions JSON column to players table OR
   - Create separate player_permissions table

2. **Modify Polymorphic Base**
   - Update ask/tell/do to check permissions
   - Add permission-aware internal methods

3. **Test Permission Levels**
   - Create test players with different permissions
   - Verify adaptive responses work correctly

4. **Document for Discord Users**
   - Explain what different permission levels can do
   - Show examples of adapted responses

## Critical Design Decisions Made

1. ✅ **Object-level enforcement** (not bridge/Claude level)
2. ✅ **Dictionary of granular permissions** (not simple roles)
3. ✅ **Adaptive responses** (not just deny)
4. ✅ **Pythonic approach** (explicit, clear, dictionary-based)
5. ✅ **Session-based context** (permissions flow with database session)

## What This Enables

- Discord users get appropriate level of access
- Developers keep full power through Discord
- Objects protect themselves automatically
- No complex authentication needed
- Easy to add new permission types
- Per-player granular control

## Remember: Keep It Pythonic!
- Explicit permission names (`can_write` not `write`)
- Dictionary lookups with defaults
- Clear, readable code over clever solutions
- Simple is better than complex