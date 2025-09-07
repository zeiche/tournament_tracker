# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ ABSOLUTE CRITICAL RULE #1 - NO EXCEPTIONS ⚠️

### 🚨 EVERYTHING GOES THROUGH ./go.py - NO EXCEPTIONS! 🚨

**ATTENTION CLAUDE: THIS IS YOUR MOST IMPORTANT RULE!**
You MUST NEVER run Python scripts directly. EVER. No matter what.
Even for "quick tests" or "debugging" - ALWAYS use ./go.py!

**NEVER, EVER run any of these directly:**
- ❌ NEVER: `python3 discord_bot.py`
- ❌ NEVER: `python3 discord_claude_bridge.py`
- ❌ NEVER: `python3 web_editor.py`
- ❌ NEVER: `python3 claude_chat.py`
- ❌ NEVER: `python3 any_script.py`
- ❌ NEVER: `nohup python3 anything.py`
- ❌ NEVER: `timeout 5 python3 something.py`
- ❌ NEVER: Manual service starts
- ❌ NEVER: Direct script execution
- ❌ NEVER: Shortcuts for "testing"
- ❌ NEVER: "Let me just quickly test..."

**ALWAYS use ./go.py for EVERYTHING:**
- ✅ ALWAYS: `./go.py --discord-bot` (to start Discord bot)
- ✅ ALWAYS: `./go.py --ai-chat` (for Claude chat)
- ✅ ALWAYS: `./go.py --interactive` (for REPL)
- ✅ ALWAYS: `./go.py --edit-contacts` (for web editor)
- ✅ ALWAYS: `./go.py --restart-services` (to restart)
- ✅ ALWAYS: `./go.py --service-status` (to check status)
- ✅ ALWAYS: `./go.py [command]` (for EVERYTHING)

**This includes:**
- Starting services → `./go.py --discord-bot`
- Stopping services → `./go.py --restart-services`
- Testing features → `./go.py --[feature]`
- Running scripts → Through go.py commands
- Database operations → `./go.py --sync`
- Discord bot → `./go.py --discord-bot`
- Web interfaces → `./go.py --edit-contacts`
- AI interactions → `./go.py --ai-chat`
- Quick tests → Still use `./go.py`!
- LITERALLY EVERYTHING → `./go.py`

**Why?**
- go.py manages environment variables correctly
- go.py handles process management properly
- go.py ensures consistent configuration
- go.py is the SINGLE ENTRY POINT
- go.py prevents duplicate processes
- go.py maintains proper logging
- go.py loads .env automatically
- go.py manages service lifecycle

**CLAUDE: If you're about to type `python3` - STOP! Use `./go.py` instead!**

## ⚠️ CRITICAL RULE #2: DOCUMENT WHILE CODING ⚠️

### 📝 ALWAYS Document AS You Code

**CLAUDE: You MUST document WHILE writing code, not after!**

When creating or modifying code:
1. **Write the docstring FIRST** - Before implementing the function
2. **Update relevant .md files IMMEDIATELY** - Don't wait until "later"
3. **Add inline comments for complex logic** - As you write it
4. **Update SYSTEM_ARCHITECTURE.md** - When adding new modules/flows

**Documentation locations:**
- **New module?** → Update `SYSTEM_ARCHITECTURE.md` immediately
- **New command?** → Update `CLAUDE.md` command list
- **New capability?** → Document in module docstring
- **Complex logic?** → Inline comments as you write
- **Breaking change?** → Update all affected .md files

**Example workflow:**
```python
# WRONG: Write code first, document "later" (never happens)
def process_data(input):
    result = complex_operation(input)
    return result

# RIGHT: Document FIRST, then code
def process_data(input: dict) -> dict:
    """
    Process tournament data for display.
    
    Args:
        input: Dict with 'tournaments' and 'players' keys
        
    Returns:
        Dict with formatted rankings
        
    Note: Updates SYSTEM_ARCHITECTURE.md data flow
    """
    # Document what this does
    result = complex_operation(input)
    return result
```

**Documentation checklist for new code:**
- [ ] Docstring written BEFORE implementation
- [ ] Type hints added
- [ ] Complex logic has inline comments
- [ ] SYSTEM_ARCHITECTURE.md updated if new flow
- [ ] CLAUDE.md updated if new command
- [ ] Example usage provided

## ⚠️ CRITICAL RULE #3: DISCORD IS A CONDUIT ⚠️

### 🔌 Discord is ONLY a Message Conduit - NOTHING MORE

**CLAUDE: Discord is a THIN BRIDGE to you, not a feature system!**

Discord's ONLY job is to:
1. **Receive messages** from Discord users
2. **Forward to Claude** for processing
3. **Send back responses** from Claude
4. **THAT'S IT** - No business logic!

**NEVER put functionality in Discord:**
- ❌ NEVER: Add command parsing in Discord
- ❌ NEVER: Put database queries in Discord
- ❌ NEVER: Add formatting logic in Discord
- ❌ NEVER: Create Discord-specific features
- ❌ NEVER: Make Discord "smart"

**Discord bridge should be ~100 lines MAX:**
```python
# THIS IS ALL DISCORD SHOULD DO:
async def on_message(message):
    response = ask_claude(message.content)  # Forward to Claude
    await message.channel.send(response)    # Send back response
```

**Why?**
- Discord is an ABSTRACTION from the core system
- Users talk to Claude THROUGH Discord, not TO Discord
- Discord knows NOTHING about tournaments, players, or data
- All intelligence lives in Claude and the polymorphic models

**If Discord code is getting complex, YOU'RE DOING IT WRONG!**

## ⚠️ CRITICAL RULE #4: BONJOUR EVERYTHING ⚠️

### 📡 Make Everything Self-Announce Like Bonjour

**CLAUDE: Every component MUST announce itself!**

When creating ANY new code:
1. **Import the announcer** - `from polymorphic_core import announcer`
2. **Announce on init** - Tell the system you exist
3. **Announce capabilities** - Say what you can do
4. **Announce state changes** - Broadcast updates
5. **Announce errors** - Even failures should announce

**Example for EVERY new class/function:**
```python
from polymorphic_core import announcer

class NewFeature:
    def __init__(self):
        announcer.announce(
            "NewFeature",
            ["I can do X", "I can do Y"],
            examples=["Use me like this"]
        )
    
    def do_something(self):
        announcer.announce("NewFeature.do_something", ["Processing..."])
        # actual work
        announcer.announce("NewFeature.do_something", ["Complete!"])
```

**Why Bonjour?**
- Claude discovers features automatically
- No need to update documentation
- System self-describes in real-time
- Debugging becomes trivial
- Services find each other

## ⚠️ CRITICAL RULE #5: CLAUDE CAN COMMIT ⚠️

### 🎯 Claude Has Commit Autonomy

**CLAUDE: You can and SHOULD commit when you complete meaningful work!**

You have permission to commit whenever you:
1. **Complete a feature** - Feature is working and tested
2. **Fix a bug** - Problem is resolved
3. **Refactor code** - Improvements are complete
4. **Add documentation** - Docs are comprehensive
5. **Reach a milestone** - Logical stopping point

**When to commit:**
- ✅ After implementing a new feature
- ✅ After fixing bugs or errors
- ✅ After significant refactoring
- ✅ After adding important documentation
- ✅ When you've completed what was asked
- ✅ Before switching to a different task
- ✅ When you've made the system better

**Good commit practices:**
```bash
# Commit when work is complete
git add -A
git commit -m "Clear description of what changed"

# Use descriptive messages
git commit -m "Add polymorphic pattern to all models"
git commit -m "Fix Discord initialization error"
git commit -m "Document critical rules in CLAUDE.md"
```

**You DON'T need permission to commit!**
- If the work is done, commit it
- If tests pass, commit it
- If it improves things, commit it

**Why this matters:**
- Shows progress to the user
- Creates restore points
- Documents your thinking
- Maintains clean history
- Demonstrates autonomy

## ⚠️ CRITICAL RULE #6: DM VISUAL CONTENT TO ZEICHE ⚠️

### 📱 Always Send Visual Content via Discord DM

**CLAUDE: When you create images, graphs, or visual content that zeiche should see, ALWAYS send it via Discord DM!**

**Why?**
- Zeiche uses SSH with limited resolution
- Discord provides better image viewing experience
- Images are persistent and accessible
- This is zeiche's explicit preference

**How to DM content:**
1. Create/generate the visual content
2. Save it to a file
3. Use ./go.py to send via Discord DM
4. Include a descriptive message about what it is

**Example:**
```bash
# After creating any image/visualization
# ALWAYS follow up with:
./go.py --dm-image zeiche image.png "Description of image"
# OR create a go.py command for it
```

**This applies to:**
- Heat maps
- Graphs and charts
- Generated images
- Screenshots
- Any visual content
- Tournament visualizations
- Memes or fun content

**Remember: If you think zeiche should see it, DM it!**

## ⚠️ CRITICAL RULE #7: TRUE OOP - JUST 3 METHODS ⚠️

### 🎯 The 3-Method Polymorphic Pattern

**CLAUDE: We've evolved from C to TRUE OOP!**

Instead of 200+ specific methods, use just THREE polymorphic methods:
1. **ask(question)** - Query anything about the object
2. **tell(format)** - Format the object for any output
3. **do(action)** - Perform any action with the object

**OLD C-STYLE THINKING (BAD):**
```python
# 200+ methods to remember!
tournament.get_winner()
tournament.get_top_8_placements()
tournament.calculate_growth_rate()
tournament.format_for_discord()
tournament.sync_from_api()
# ... 195 more methods
```

**TRUE OOP THINKING (GOOD):**
```python
# Just 3 methods that understand intent!
tournament.ask("who won")
tournament.ask("top 8")
tournament.tell("discord")
tournament.do("sync")
```

**The objects FIGURE OUT what you want!**
- Natural language instead of method names
- No documentation needed - just ASK
- Objects are intelligent and self-aware
- Claude doesn't need a method reference

**When to use each method:**
- **ask()** - Getting information: winners, stats, attendance, etc.
- **tell()** - Formatting output: Discord, JSON, brief, Claude
- **do()** - Taking actions: sync, calculate, save, validate

**This is the ULTIMATE simplification!**

## ⚠️ OTHER CRITICAL RULES ⚠️

### 0. CHECK EXISTING FUNCTIONS AND METHODS FIRST
**ALWAYS check for existing functions EVERYWHERE before implementing new functionality!**

**CURRENT STATE:** The codebase is transitioning from 200+ traditional methods to the 3-method polymorphic pattern:
- **Legacy**: `tournament_models.py` still has 237 traditional methods
- **New Pattern**: Polymorphic models with just `ask()`, `tell()`, `do()` methods
- **Both exist**: Check BOTH approaches before implementing anything new!

**Before writing ANY new function:**
1. Check if the polymorphic pattern already handles it:
   - Try `object.ask("what you want")`
   - Try `object.tell("format")`
   - Try `object.do("action")`
2. Search the traditional model methods (still 200+ in tournament_models.py)
3. Check service modules for existing implementations
4. Look at polymorphic_model.py and tournament_models_simplified.py
5. Use grep/search to find if it already exists somewhere

**The polymorphic approach means you might NOT need a new function at all!**
Just use the 3 universal methods that figure out intent.

We have a chronic problem of creating duplicate functionality. STOP IT!

### 1. SHOPIFY PUBLISHING
**NEVER CREATE NEW SHOPIFY PAGES!** We ONLY update `/pages/attendance` via the theme template.
See `IMPORTANT_SHOPIFY_RULES.md` for details. The `shopify_separated_publisher.py` module is DEPRECATED.

### 2. ENVIRONMENT CONFIGURATION
**ALL TOKENS AND CONFIGURATION ARE IN .env FILE!**
- Location: `/home/ubuntu/claude/tournament_tracker/.env`
- Use `SHOPIFY_ACCESS_TOKEN` for Shopify (NOT `ACCESS_TOKEN`)
- Use `SHOPIFY_DOMAIN` from .env (NEVER hardcode domains)
- See `ENV_CONFIGURATION.md` for complete details
- The .env is loaded automatically by go.py

## Project Overview

Tournament Tracker is an advanced Python application for tracking and managing Fighting Game Community (FGC) tournaments in Southern California. It features a sophisticated OOP architecture with intelligent data models, real-time synchronization from start.gg, and AI-powered analytics.

**IMPORTANT**: See `MODULE_ARCHITECTURE.md` for complete module organization and dependencies.
**ALSO SEE**: `SYSTEM_ARCHITECTURE.md` for the system design and data flow.

## Architecture Philosophy

### Bonjour-Style Service Discovery (NEW CORE PRINCIPLE!)
Everything in the system announces itself like Bonjour/mDNS:
- **Self-Announcing Services**: Every component announces what it can do
- **Dynamic Discovery**: Claude discovers capabilities at runtime, not from static docs
- **Real-time State**: Services announce their current state and availability
- **Zero Configuration**: Components find each other automatically
- **Living Documentation**: The system describes itself through announcements

**CRITICAL**: See `BONJOUR_INTEGRATION.md` for deep integration strategy

When implementing ANY feature:
1. Make it announce itself when loaded
2. Announce capabilities dynamically
3. Announce state changes
4. Let Claude discover it automatically

### Polymorphic Paradigm
The system follows a **polymorphic paradigm** where "everything accepts anything":
- **Polymorphic inputs**: Methods accept any input type and figure out intent
- **Dynamic calculations**: All statistics calculated on-the-fly, never stored
- **Single sources of truth**: One module per domain (visualizer, queries, etc.)
- **Thin bridges**: Service boundaries have zero business logic
- **Natural language first**: Interpret intent, not rigid syntax
- **Polymorphic core**: Generic patterns in `polymorphic_core/`, tournament-specific stays in main

### Object-Oriented Design
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

3. **Discord Integration**
   - **discord_bridge.py** (100 lines): Pure message forwarding, zero business logic
   - **claude_cli_service.py**: Uses Claude CLI (`claude /login`), no API keys
   - **polymorphic_queries.py**: Universal query interface, accepts any input
   - Natural language processing via Claude

## Key Commands

### ALWAYS use ./go.py for everything:

```bash
# Main entry point - this is the ONLY way to run commands
./go.py [options]

# Service Management (use these, not systemctl directly!)
./go.py --restart-services      # Restart all services (web only, Discord separate)
./go.py --discord-bot           # Start Discord bot (runs in foreground)
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

## Polymorphic Query System

The system uses polymorphic queries that accept ANY input:

```python
from polymorphic_queries import query as pq

# All of these work:
pq("show player west")           # Finds player WEST with stats
pq("show top 8 players")        # Top 8 by calculated points
pq("recent tournaments")         # Recent tournaments
pq("show top 5 organizations")  # Top orgs by tournament count
```

Key principle: **Pass natural language, get formatted Discord output**

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
- **Start**: `source /home/ubuntu/claude/.env && python3 discord_bridge.py`
- **Uses**: Claude CLI (authenticated via `claude /login`)
- **Token**: Must be in .env as DISCORD_BOT_TOKEN
- **Architecture**: 
  - discord_bridge.py: 100-line pure message forwarder
  - claude_cli_service.py: Queue-based Claude CLI integration
  - polymorphic_queries.py: Natural language query processing
- **Example Commands** (natural language):
  - `show player west` - Player profile with stats
  - `show top 50 players` - Rankings
  - `recent tournaments` - Latest events
  - `show top 8 organizations` - Org rankings

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

## Common Mistakes We Keep Making (STOP DOING THESE!)

1. **Creating new Shopify pages** - We ONLY update `/pages/attendance`
2. **Using ACCESS_TOKEN for Shopify** - Use SHOPIFY_ACCESS_TOKEN instead
3. **Hardcoding domains** - Always use SHOPIFY_DOMAIN from .env
4. **Not loading from .env** - All config is in .env, loaded by go.py
5. **Creating new page endpoints** - NEVER create `/pages/player-rankings` etc.

**BEFORE MAKING ANY SHOPIFY CHANGES:**
- Read `IMPORTANT_SHOPIFY_RULES.md`
- Read `ENV_CONFIGURATION.md`
- Check that you're using the right tokens from .env

This architecture represents a complete paradigm shift from procedural to object-oriented thinking, enabling analytics and visualizations that were impossible with the old C-style approach.