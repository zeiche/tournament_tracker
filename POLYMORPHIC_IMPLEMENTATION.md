# Polymorphic Input System Implementation Guide

## Overview

We're implementing a universal input handling system that allows ALL functions across the entire codebase to seamlessly accept strings, lists, dictionaries, objects, or any combination - making the system incredibly flexible and user-friendly.

## Current Progress

### ✅ Completed

1. **Universal Input Handler (`polymorphic_inputs.py`)**
   - `InputHandler.parse()` - Intelligently converts any input type
   - `@accepts_anything` decorator - Makes functions polymorphic
   - `FlexibleQuery` - Builds database queries from any input
   - Helper functions: `to_list()`, `to_dict()`, `to_ids()`

2. **go.py sync_tournaments** - Now accepts:
   ```python
   sync_tournaments()                    # Default
   sync_tournaments(100)                  # Page size
   sync_tournaments("fetch standings")    # Natural language
   sync_tournaments({"page_size": 100})  # Dictionary
   sync_tournaments([100, True, 5])      # List parameters
   ```

3. **BaseModel.find()** - Now accepts:
   ```python
   Tournament.find(123)                   # By ID
   Tournament.find("123")                 # String ID
   Tournament.find({"name": "Summer"})    # By attributes
   Tournament.find(["123", "456"])        # Multiple IDs
   Tournament.find(tournament_obj)        # Object passthrough
   ```

## Implementation Patterns

### Pattern 1: Simple Decorator Usage
```python
@accepts_anything('expected_type')
def my_function(input_value):
    # input_value is automatically parsed
    # Access parsed data directly
    pass
```

### Pattern 2: Manual Parsing
```python
def my_function(input_value):
    parsed = InputHandler.parse(input_value, 'expected_type')
    
    if isinstance(parsed, dict):
        # Handle dictionary
        if 'id' in parsed:
            # Single ID lookup
        elif 'ids' in parsed:
            # Multiple ID lookup
        elif 'text' in parsed:
            # Text search
    elif isinstance(parsed, list):
        # Handle list
    # etc.
```

### Pattern 3: Model Methods
```python
class MyModel(BaseModel):
    @classmethod
    def search(cls, input_value):
        """Search with flexible input"""
        parsed = InputHandler.parse(input_value, cls.__name__)
        
        # Build query based on parsed input
        if FlexibleQuery:
            return FlexibleQuery.build(cls.session(), cls, parsed)
        
        # Manual fallback
        # ...
```

## Remaining Implementation Tasks

### 1. Core Functions in go.py

#### Report Functions
```python
# Current:
def generate_console_report(self, limit: Optional[int] = None)

# Should become:
@accepts_anything('report_config')
def generate_console_report(self, config=None)
# Accept: 20, "top 20", {"limit": 20}, [20, "console"]
```

#### HTML Generation
```python
# Current:
def generate_html_report(self, output_file: str, limit: Optional[int] = None)

# Should become:
@accepts_anything('html_config')
def generate_html_report(self, config=None)
# Accept: "report.html", {"file": "report.html", "limit": 20}, ["report.html", 20]
```

### 2. Tournament Model Methods

```python
class Tournament:
    @classmethod
    def all(cls, input_value=None):
        """Get all tournaments with optional filtering"""
        # Accept: None, {"city": "Riverside"}, "recent", 50 (limit)
        
    @classmethod
    def recent(cls, input_value=None):
        """Get recent tournaments"""
        # Accept: 30 (days), "last month", {"days": 30}
        
    def get_standings(self, input_value=None):
        """Get standings flexibly"""
        # Accept: None, 8 (top N), "top 8", {"limit": 8, "include_points": True}
```

### 3. Player Model Methods

```python
class Player:
    @classmethod
    def search(cls, input_value):
        """Search players flexibly"""
        # Accept: "Monte", {"tag": "Monte"}, ["Monte", "West"], regex patterns
        
    def get_tournaments(self, input_value=None):
        """Get player's tournaments"""
        # Accept: None, "recent", {"year": 2024}, date ranges
```

### 4. Organization Model Methods

```python
class Organization:
    @classmethod
    def top_by_attendance(cls, input_value=None):
        """Get top organizations"""
        # Accept: 10, "top 10", {"limit": 10, "min_events": 5}
        
    def merge_with(self, input_value):
        """Merge organizations"""
        # Accept: org_object, org_id, {"id": 123}, "Organization Name"
```

### 5. Formatters and Presenters

```python
class TournamentFormatter:
    @staticmethod
    def format(input_value):
        """Format tournament(s) for display"""
        # Accept: tournament, [tournaments], {"tournaments": list, "style": "table"}
        
class PlayerFormatter:
    @staticmethod
    def format_stats(input_value):
        """Format player statistics"""
        # Accept: player, {"player": player, "include": ["wins", "attendance"]}
```

## Benefits

1. **User-Friendly**: Users can pass data in whatever format they have
2. **Flexible**: Functions adapt to different input types automatically
3. **Maintainable**: Single parsing logic in one place
4. **Extensible**: Easy to add new input type handling
5. **Backward Compatible**: Falls back to original behavior if needed

## Usage Examples in Interactive Mode

```python
# All of these work!
>>> Tournament.find("Summer Showdown")
>>> Tournament.find({"city": "Riverside", "year": 2024})
>>> Tournament.find(recent_tournaments[:5])

>>> sync_tournaments("quick sync with standings")
>>> sync_tournaments({"page_size": 50, "fetch_standings": True})

>>> ask(Tournament.all()[:10])  # Claude analyzes 10 tournaments
>>> chat(player_stats)           # Start chat with player context
```

## Testing Strategy

1. **Unit Tests** - Test InputHandler with various input types
2. **Integration Tests** - Test model methods with polymorphic inputs
3. **End-to-End Tests** - Test complete workflows with mixed input types
4. **Interactive Testing** - Use interactive mode to test real scenarios

## Implementation Priority

1. ⭐ **High Priority** - Core functions users interact with most
   - Model.find() methods
   - Report generation
   - Search functions

2. **Medium Priority** - Frequently used operations
   - Sync operations
   - Stats calculations
   - Formatting functions

3. **Low Priority** - Internal/utility functions
   - Cache operations
   - Debug functions
   - Admin utilities

## Code Style Guidelines

1. Always provide examples in docstrings
2. Use type hints with Union types
3. Gracefully handle unexpected input
4. Log parsed input for debugging
5. Maintain backward compatibility

## Migration Path

1. Add polymorphic_inputs import
2. Update function signature to accept flexible input
3. Add parsing logic at function start
4. Test with various input types
5. Update documentation and examples

This polymorphic system transforms the entire codebase into a flexible, intelligent system that "just works" with whatever data format users provide!