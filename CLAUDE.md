# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tournament Tracker is an advanced Python application for tracking and managing Fighting Game Community (FGC) tournaments in Southern California. It features a sophisticated OOP architecture with intelligent data models, real-time synchronization from start.gg, and AI-powered analytics.

## Architecture Philosophy

### Object-Oriented Design
The system has been refactored from C-style flat data structures to a Python-centric OOP architecture where:
- **Models are intelligent**: Objects understand their context and relationships
- **Built-in analytics**: Methods for calculations live within the models
- **Relationship awareness**: Objects can traverse and analyze their connections
- **Type-safe**: Comprehensive type hints throughout

### Key Architectural Components

1. **Enhanced Models** (`tournament_models.py`)
   - 2600+ lines of sophisticated OOP code
   - 200+ methods across all models
   - LocationMixin for geographic intelligence
   - TimestampMixin for temporal tracking
   - Rich inter-object relationships

2. **Central Command Interface** (`go.py`)
   - Single entry point for ALL operations
   - ProcessManager for process control
   - ServiceManager for systemd services
   - TournamentCommand for business logic
   - CommandLineInterface for routing

3. **Intelligent Discord Bot** (`discord_conversational.py`)
   - Relationship-aware responses
   - Player journey analysis
   - Geographic calculations
   - Growth trend analysis

## Key Commands

### ALWAYS use ./go.py for everything:

```bash
# Main entry point - this is the ONLY way to run commands
./go.py [options]

# Service Management (use these, not systemctl directly!)
./go.py --restart-services      # Restart all services
./go.py --restart-discord        # Restart Discord bot only
./go.py --restart-web           # Restart web service only
./go.py --service-status        # Check service status with details

# Sync Operations
./go.py --sync                  # Sync tournaments from start.gg
./go.py --fetch-standings        # Fetch top 8 standings
./go.py --skip-sync             # Skip sync for other operations

# Reports & Output
./go.py --console               # Show console report
./go.py --html report.html      # Generate HTML report
./go.py --publish               # Publish to Shopify

# Analytics & Visualizations
./go.py --heatmap               # Generate all heat map types
./go.py --stats                 # Show database statistics
./go.py --identify-orgs         # Identify organizations

# Interactive Tools
./go.py --edit-contacts         # Launch web editor (port 8081)
./go.py --interactive           # Interactive mode
./go.py --ai-chat              # Terminal AI chat
./go.py --ai-web               # Web AI interface (port 8082)
./go.py --ai-ask "question"    # Ask AI a single question
```

## Enhanced Model Capabilities

### Tournament Model
```python
# Geographic intelligence
tournament.has_location          # Property: checks if coordinates exist
tournament.coordinates           # Property: returns (lat, lng) tuple
tournament.distance_to(lat, lng) # Method: calculates distance in km
tournament.get_heatmap_weight()  # Method: calculates visualization weight
tournament.is_major()            # Method: determines if major event

# These enable heat maps like:
# - Distance-based clustering
# - Weighted density maps
# - Geographic relationships
```

### Player Model
```python
# Performance analytics
player.win_rate           # Property: percentage of first places
player.podium_rate        # Property: top 3 finish rate
player.points_per_event   # Property: average points per tournament
player.consistency_score  # Property: performance consistency metric

# Enables analytics like:
# - Player journey tracking
# - Skill progression mapping
# - Performance geography
```

### Organization Model
```python
# Network analysis
org.get_tournaments(session)  # Method: retrieve all org tournaments
org.get_contacts()            # Method: get all contact info
org.add_contact(type, value)  # Method: add new contact
org.merge_into(target_org)    # Method: merge organizations

# Powers features like:
# - Organization growth tracking
# - Venue network analysis
# - Contact consolidation
```

## New Heat Map Types

The enhanced OOP models enable entirely new visualizations:

1. **Player Skill Geography** - Concentration of elite players
2. **Growth Velocity Maps** - Where the scene is expanding
3. **Player Journey Paths** - Individual competitive trajectories
4. **Community Networks** - Venue connections via players
5. **Venue Quality Scoring** - Based on usage and growth
6. **Temporal Flow Maps** - Seasonal patterns
7. **Competitive Clusters** - High-skill density areas

Generate with: `./go.py --heatmap`

## Services

### Web Editor Service
- **Port**: 8081
- **Start**: `./go.py --edit-contacts`
- **Restart**: `./go.py --restart-web`
- **Features**:
  - Edit organization names
  - Merge organizations
  - Manage contacts
  - Assign tournaments to orgs

### Discord Bot Service
- **Bot**: try-hard#8718
- **Start**: Runs as systemd service
- **Restart**: `./go.py --restart-discord`
- **New Commands**:
  - `nearby tournaments [location]` - Geographic search
  - `player journey [name]` - Travel analysis
  - `venue analysis` - Venue quality metrics
  - `growth analysis` - Trend detection

## Database

- **Type**: SQLite with SQLAlchemy ORM
- **Location**: `tournament_tracker.db`
- **Models**: Enhanced with 200+ methods
- **Sessions**: Centralized management via context managers
- **Migrations**: Alembic for schema changes

## Testing

```bash
# Test enhanced models
python3 test_all_models.py

# Test relationships
python3 relationship_demo.py

# Test analytics
python3 analytics_showcase.py

# Generate advanced heat maps
python3 heatmap_advanced.py
```

## Development Guidelines

### When Adding Features:
1. **ALWAYS use ./go.py** - Never call services or scripts directly
2. **Leverage model methods** - Don't write external calculations
3. **Use type hints** - Maintain type safety
4. **Follow OOP patterns** - Methods belong in models
5. **Test relationships** - Ensure cross-object interactions work

### Model Enhancement Pattern:
```python
class Tournament(Base, BaseModel, LocationMixin):
    # Properties for computed values
    @property
    def is_recent(self) -> bool:
        return self.days_ago <= 30 if self.days_ago else False
    
    # Methods for complex operations
    def calculate_growth(self, other: 'Tournament') -> float:
        if not self.num_attendees or not other.num_attendees:
            return 0.0
        return (self.num_attendees - other.num_attendees) / other.num_attendees
    
    # Class methods for queries
    @classmethod
    def get_major_tournaments(cls, session) -> List['Tournament']:
        return session.query(cls).filter(
            cls.num_attendees > 100
        ).all()
```

### Service Management Pattern:
```python
# ALWAYS use go.py methods
./go.py --restart-services  # NOT: sudo systemctl restart tournament-web
./go.py --service-status    # NOT: systemctl status
```

## External Dependencies

```bash
# Core
pip3 install --break-system-packages sqlalchemy alembic httpx

# Discord bot
pip3 install --break-system-packages discord.py

# Visualizations
pip3 install --break-system-packages matplotlib scipy contextily folium numpy

# Web services
# (FastAPI/Flask if added)
```

## Environment Variables

- `ANTHROPIC_API_KEY` - For AI features (optional)
- `ACCESS_TOKEN` - Shopify API access
- Discord token in `.env.discord`

## Architecture Benefits

The new Python-centric OOP architecture provides:

1. **Intelligent Objects**: Data with behavior, not just fields
2. **Relationship Traversal**: Navigate complex connections naturally
3. **Built-in Analytics**: Calculations live where they belong
4. **Type Safety**: IDE support and error prevention
5. **Maintainability**: Clear separation of concerns
6. **Extensibility**: Easy to add new methods and relationships

## Common Tasks

### Add a new heat map type:
```python
# In tournament_models.py - add method to model
class Tournament:
    def get_custom_metric(self) -> float:
        return self.some_calculation()

# In heatmap_advanced.py - use the method
for tournament in tournaments:
    weight = tournament.get_custom_metric()
    heatmap_data.append([tournament.lat, tournament.lng, weight])
```

### Add Discord command:
```python
# In discord_conversational.py
class RelationshipResponder:
    @staticmethod
    async def new_analysis(message, param):
        with get_session() as session:
            # Use model methods directly
            tournaments = session.query(Tournament).all()
            for t in tournaments:
                result = t.some_new_method()  # Use model intelligence
```

### Restart everything:
```bash
./go.py --restart-services  # That's it!
```

## Important Notes

- **go.py is the entry point for EVERYTHING** - Do not bypass it
- **Models contain business logic** - Not external functions
- **Services are managed via go.py** - Not systemctl directly
- **Heat maps use model methods** - Not manual calculations
- **Discord bot uses relationships** - Not flat queries

This architecture represents a complete paradigm shift from procedural to object-oriented thinking, enabling analytics and visualizations that were impossible with the old C-style approach.