# SQLAlchemy ORM Architecture Enhancements

## Overview
The database models have been refactored to properly leverage SQLAlchemy's ORM capabilities with rich methods, mixins, and query builders.

## Key Enhancements

### 1. LocationMixin
A reusable mixin for any model with geographic data:

```python
class LocationMixin:
    # Fields
    lat = Column(Float)
    lng = Column(Float)
    venue_name = Column(String)
    venue_address = Column(String)
    city = Column(String)
    addr_state = Column(String)
    country_code = Column(String)
    postal_code = Column(String)
    
    # Properties
    has_location -> bool
    coordinates -> Optional[Tuple[float, float]]
    location_dict -> Dict[str, Any]
    full_address -> str
    
    # Methods
    is_in_region(lat_min, lat_max, lng_min, lng_max) -> bool
    is_in_socal() -> bool
    distance_to(other_lat, other_lng) -> Optional[float]
    get_heatmap_weight() -> float
    
    # Class methods
    with_location() -> Query
    in_region(lat_min, lat_max, lng_min, lng_max) -> Query
    in_socal() -> Query
```

### 2. Enhanced Tournament Model
The Tournament model now inherits from LocationMixin and includes:

#### Time-based Methods
- `start_date` / `end_date` - Convert timestamps to datetime objects
- `is_active` / `is_upcoming` / `is_past` - Status properties
- `days_until()` - Days until tournament starts
- `upcoming(days)` - Get upcoming tournaments
- `recent(days)` - Get recent tournaments
- `by_year(year)` - Get tournaments for a specific year

#### Data Methods
- `get_heatmap_weight()` - Log-scaled weight for visualization
- `to_dict()` - Complete JSON serialization including location data
- `organization` - Smart property to find related organization

### 3. Enhanced Organization Model
Organizations now have rich analytics:

#### Statistics Methods
- `get_stats()` - Comprehensive statistics including:
  - Total/average attendance
  - Tournament counts
  - Location breakdowns
  - Recent/upcoming tournaments
  - City coverage

#### Location Methods
- `get_location_coverage()` - Tournament distribution by location
- `tournaments` - Smart property maintaining session context

#### Search Methods
- `search(query)` - Case-insensitive search by name
- `to_dict()` - JSON serialization with full stats

### 4. Enhanced Player Model
Players now have detailed analytics and comparisons:

#### Statistics Methods
- `get_stats()` - Comprehensive player statistics:
  - Placement breakdown
  - Win rates
  - Earnings tracking
  - Singles vs doubles performance

#### Results Methods
- `get_recent_results(limit)` - Recent tournament placements
- `get_head_to_head(other_player_id)` - H2H comparison

#### Class Methods
- `search(query)` - Search by gamer tag or name
- `top_earners(limit)` - Players ranked by prize money
- `most_wins(limit)` - Players ranked by tournament wins

### 5. Improved Session Management
- Auto-initialization when database isn't configured
- Proper session context handling to avoid detached instances
- Session-aware property access for relationships

## Usage Examples

### Location-based Queries
```python
# Get all SoCal tournaments
socal_tournaments = Tournament.in_socal().all()

# Get tournaments in LA area
la_tournaments = Tournament.in_region(33.5, 34.5, -118.5, -117.5).all()

# Check if tournament is in SoCal
if tournament.is_in_socal():
    print(f"{tournament.name} is in Southern California")

# Calculate distance between tournaments
distance = t1.distance_to(*t2.coordinates)
print(f"Distance: {distance:.1f} km")
```

### Time-based Queries
```python
# Get upcoming tournaments
upcoming = Tournament.upcoming(days=30)

# Get recent tournaments
recent = Tournament.recent(days=90)

# Get all 2024 tournaments
tournaments_2024 = Tournament.by_year(2024)

# Check tournament status
if tournament.is_upcoming:
    print(f"Starts in {tournament.days_until()} days")
```

### Organization Analytics
```python
# Get organization stats
stats = org.get_stats()
print(f"Total attendance: {stats['total_attendance']}")
print(f"Cities covered: {stats['unique_cities']}")

# Get location breakdown
coverage = org.get_location_coverage()
for city, count in coverage.items():
    print(f"{city}: {count} tournaments")
```

### Player Analytics
```python
# Get top earners
top_players = Player.top_earners(10)
for player in top_players:
    print(f"{player.gamer_tag}: ${player.total_winnings/100:.2f}")

# Get player stats
stats = player.get_stats()
print(f"Win rate: {stats['win_rate']}%")

# Get head-to-head
h2h = player1.get_head_to_head(player2.id)
print(f"vs {h2h['vs_player']}: {h2h['wins']}-{h2h['losses']}")
```

### Heatmap Integration
```python
# Objects with LocationMixin work seamlessly with heatmap generation
for tournament in Tournament.with_location():
    if tournament.has_location:
        weight = tournament.get_heatmap_weight()
        lat, lng = tournament.coordinates
        # Add to heatmap with proper weight
```

## Benefits

1. **Object-Oriented** - Models now have behavior, not just data
2. **Reusable** - LocationMixin can be added to any model needing geographic features
3. **Type-Safe** - Type hints throughout for better IDE support
4. **Session-Aware** - Proper handling of SQLAlchemy sessions prevents detached instance errors
5. **Analytics-Ready** - Built-in methods for common analytics queries
6. **JSON-Friendly** - to_dict() methods for easy API/export usage
7. **Heatmap-Ready** - Any object with LocationMixin can be visualized on a heatmap

## Testing
Run the test suite to verify all enhancements:
```bash
python3 test_enhanced_models.py
```

This will test:
- Location features and queries
- Tournament time-based methods
- Organization statistics
- Player analytics
- Heatmap integration