# Polymorphic Visualizer Documentation

## Overview
The unified visualizer (`visualizer.py`) is the **SINGLE SOURCE OF TRUTH** for all visualization and HTML generation in the tournament tracker system. It follows the polymorphic paradigm - accepting ANY input type and intelligently determining how to visualize it.

## Core Philosophy
**"Accept anything, visualize everything"**

The visualizer doesn't care what you throw at it. String? List? Dictionary? Complex nested object? Database model? It will figure out the best way to visualize it.

## Architecture

### Single Entry Point
```python
from visualizer import UnifiedVisualizer

viz = UnifiedVisualizer()
```

This is the ONLY visualizer you need. There are no other visualization modules.

## Key Methods

### `visualize(input_data, output=None, **kwargs)`
The master method that routes to appropriate visualization based on input type.

```python
# Examples of polymorphic input
viz.visualize("Hello World")                    # Text display
viz.visualize([1, 2, 3, 4])                    # List visualization
viz.visualize({"lat": 34.0, "lng": -118.0})    # Geographic point
viz.visualize(tournament_object)                # Tournament heatmap
viz.visualize(player_stats)                     # Player analytics
```

### `heatmap(input_data, output=None, **kwargs)`
Geographic heatmap generation. Accepts:
- List of tournaments
- List of [lat, lng, weight] tuples
- Dictionary with 'locations' key
- Any object with location attributes

```python
# All of these work
viz.heatmap(tournaments)
viz.heatmap([[34.0, -118.0, 100], [33.9, -117.9, 80]])
viz.heatmap({"locations": tournament_list})
viz.heatmap("tournament_tracker.db")  # Loads from database
```

### `chart(input_data, output=None, chart_type='auto', **kwargs)`
Creates charts and graphs. Auto-detects best chart type.

```python
viz.chart([1, 2, 3, 4, 5])                    # Line chart
viz.chart({"A": 10, "B": 20})                 # Bar chart
viz.chart(player_performance_over_time)        # Time series
```

### `html(input_data, output=None, format='auto', **kwargs)`
HTML generation for web display.

```python
# Auto-detects format
viz.html("Simple text")                        # <p> wrapper
viz.html(["Item 1", "Item 2"])                # <ul> list
viz.html({"title": "Test", "body": "..."})    # Full page
viz.html(dataframe)                            # HTML table
```

### `table(input_data, title=None, subtitle=None, **kwargs)`
Specialized table generation.

```python
# Flexible input formats
viz.table({
    'headers': ['Name', 'Score'],
    'rows': [['Alice', 95], ['Bob', 87]]
})

viz.table([[1, 2], [3, 4]])  # Auto-generates headers

viz.table(tournament_standings)  # From model objects
```

### `report(input_data, title=None, format='html', **kwargs)`
Comprehensive report generation.

```python
viz.report(tournament_analytics)
viz.report({"summary": {...}, "details": [...]})
viz.report(player_journey_data)
```

## Polymorphic Input Examples

### String Input
```python
viz.visualize("SoCal FGC Tournament Data")
# Creates a text display or title card
```

### List Input
```python
viz.visualize([tournament1, tournament2, tournament3])
# Automatically creates appropriate visualization based on object types
```

### Dictionary Input
```python
viz.visualize({
    'type': 'heatmap',
    'data': tournament_list,
    'title': 'Tournament Density'
})
# Uses hints from dictionary structure
```

### Model Objects
```python
from tournament_models import Tournament, Player

tournament = Tournament.find("TNS Tuesday")
viz.visualize(tournament)  # Creates tournament-specific visualization

player = Player.find("Nephew")
viz.visualize(player)  # Creates player journey map
```

### Complex Nested Structures
```python
complex_data = {
    'tournaments': [...],
    'players': [...],
    'statistics': {
        'total': 1000,
        'average': 50
    },
    'locations': [[34.0, -118.0], ...]
}
viz.visualize(complex_data)  # Creates multi-panel dashboard
```

## Integration with go.py

The visualizer is fully integrated with the main command interface:

```python
class TournamentCommand:
    def generate_heatmaps(self, config=None):
        viz = UnifiedVisualizer()
        
        # Accepts string, dict, or config object
        result = viz.heatmap(config)
        
        return CommandResult(
            success=True,
            data=result
        )
```

## HTML Generation Features

### Embedded Styles
All HTML includes embedded CSS for standalone display:
```python
html = viz.html(data)  # Includes <style> tags
```

### Responsive Design
Generated HTML is mobile-friendly:
```python
html = viz.table(data, responsive=True)  # Default
```

### Theming
```python
viz.html(data, theme='dark')   # Dark mode
viz.html(data, theme='light')  # Light mode
viz.html(data, theme='auto')   # System preference
```

## Advanced Features

### Lazy Loading
```python
viz.visualize("tournaments")  # String triggers database load
```

### Format Detection
```python
viz.visualize(unknown_data)  # Examines structure and chooses format
```

### Chaining
```python
result = viz.start_page("Report") \
           .add_table(data1) \
           .add_chart(data2) \
           .add_map(data3) \
           .finish()
```

## Migration Guide

### Old Way (Multiple Modules)
```python
# DON'T DO THIS ANYMORE
from html_utils import format_table
from html_renderer import HTMLRenderer
from heatmap_advanced import generate_heatmap
from heatmap_venues import create_venue_map

html = format_table(data)
renderer = HTMLRenderer()
heatmap = generate_heatmap(tournaments)
venue_map = create_venue_map(venues)
```

### New Way (Unified Visualizer)
```python
# DO THIS INSTEAD
from visualizer import UnifiedVisualizer

viz = UnifiedVisualizer()
html = viz.table(data)
heatmap = viz.heatmap(tournaments)
venue_map = viz.heatmap(venues)  # Same method, different input
```

## Key Benefits

1. **Single Source of Truth**: One module for ALL visualization
2. **Polymorphic**: Accepts any input type seamlessly
3. **Intelligent**: Auto-detects best visualization format
4. **Consistent**: Uniform API across all visualization types
5. **Extensible**: Easy to add new visualization types
6. **Maintainable**: All visualization code in one place

## Common Patterns

### Database Models
```python
with get_session() as session:
    tournaments = session.query(Tournament).all()
    viz.heatmap(tournaments)  # Works directly with SQLAlchemy objects
```

### Mixed Data
```python
viz.visualize({
    'map': tournament_locations,
    'stats': attendance_stats,
    'trends': growth_data
})  # Creates comprehensive dashboard
```

### Export Options
```python
viz.heatmap(data, output='map.html')  # Save to file
viz.chart(data, output='chart.png')   # Different formats
viz.report(data, format='pdf')        # PDF generation
```

## Error Handling

The visualizer is resilient and provides helpful feedback:

```python
viz.visualize(None)  # Returns empty visualization with message
viz.visualize(corrupted_data)  # Best effort visualization
viz.visualize(huge_dataset)  # Automatic sampling/aggregation
```

## Testing

```python
# Test polymorphic input
test_inputs = [
    "string",
    [1, 2, 3],
    {"key": "value"},
    Tournament(),
    None,
    12345
]

for input_data in test_inputs:
    result = viz.visualize(input_data)
    assert result is not None  # Always returns something
```

## Future Extensions

The visualizer is designed to be extended:

```python
# Register custom visualizations
viz.register('custom_type', custom_visualization_function)

# Add new output formats
viz.add_format('yaml', yaml_formatter)

# Plugin system
viz.use_plugin('3d_maps')
```

## Remember

- **ALWAYS** use the unified visualizer for ANY visualization need
- **NEVER** create separate visualization modules
- **TRUST** the polymorphic input handling
- **LEVERAGE** the intelligent format detection
- The visualizer is the **SINGLE SOURCE OF TRUTH** for all visualization

## Quick Reference

```python
from visualizer import UnifiedVisualizer

viz = UnifiedVisualizer()

# Everything just works
viz.visualize(anything)
viz.heatmap(anything)
viz.chart(anything)
viz.html(anything)
viz.table(anything)
viz.report(anything)
```

That's it. That's the entire API. It accepts anything and figures out what to do.