# Ollama Bonjour Module

## Claude's Little Brother - Offline Intelligence for Service Discovery

This module provides complete integration between Ollama (local LLM) and Bonjour service discovery, creating an intelligent service router that works completely offline.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 User Query                      │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│            Bonjour Router                       │
│         (Natural Language → Service)            │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│            Bonjour Bridge                       │
│    (Connects Announcements ← → Intelligence)    │
└────────┬──────────────────────────┬─────────────┘
         ↓                          ↓
┌──────────────────┐      ┌───────────────────────┐
│  Service Memory  │      │   Ollama Service      │
│  (Persistent)    │      │   (Local LLM)         │
└──────────────────┘      └───────────────────────┘
         ↑                          
┌─────────────────────────────────────────────────┐
│          Bonjour Announcements                  │
│     (Services announcing capabilities)          │
└─────────────────────────────────────────────────┘
```

## Components

### 1. OllamaBonjour (`ollama_service.py`)
- Main service integrating Ollama with Bonjour
- Subscribes to all service announcements
- Provides ask/tell/do polymorphic interface
- Auto-starts Ollama if needed
- Works with any Ollama model (mistral, llama2, phi, etc.)

### 2. ServiceMemory (`service_memory.py`)
- Persistent storage of discovered services
- Learns relationships between services
- Records interaction history
- Pattern matching for service categorization
- Finds relevant services for user goals

### 3. BonjourBridge (`bonjour_bridge.py`)
- Real-time monitoring of Bonjour announcements
- Feeds announcements to Ollama's knowledge base
- Routes queries with service context
- Builds service relationship graphs
- Natural language request routing

## Usage

### Start the Service

```bash
# Via go.py (recommended)
./go.py --ollama-bonjour

# Or directly
python3 -m ollama_bonjour.ollama_service

# Or as async bridge
python3 -m ollama_bonjour.bonjour_bridge
```

### Python API

```python
from ollama_bonjour import get_ollama_bonjour

# Get the service instance
ollama = get_ollama_bonjour()

# Ask about services
response = ollama.ask("How do I sync tournaments?")
print(response)
# "Use the StartGG Sync service with sync.do('sync tournaments')"

# Format for Discord
formatted = ollama.tell('discord', response)

# Analyze service landscape
analysis = ollama.do("analyze services")
print(f"Found {analysis['total_services']} services")

# Get service memory
from ollama_bonjour import ServiceMemory
memory = ServiceMemory()
stats = memory.get_statistics()
print(f"Tracking {stats['total_services']} services")
```

### Natural Language Routing

```python
from ollama_bonjour import BonjourRouter

router = BonjourRouter()

# Route natural language to services
print(router.route("I need to update tournament data"))
# "Route to: sync.do('sync tournaments')"

print(router.route("Show me player rankings"))
# "Route to: database.ask('top 50 players')"

print(router.route("Create a heat map"))
# "Route to: visualizer.do('generate heatmap')"
```

## Features

### Service Discovery
- Automatically discovers all Bonjour services
- Remembers service capabilities over time
- Learns relationships between services
- Categories services (database, sync, visualization, etc.)

### Intelligent Routing
- Natural language → Service method mapping
- Suggests which service to use for goals
- Remembers successful interactions
- Works completely offline

### Persistent Memory
- Saves discovered services to disk
- Tracks announcement history
- Records user interactions
- Builds knowledge over time

### Polymorphic Interface
- `ask(query)` - Natural language questions
- `tell(format, data)` - Format responses (json, discord, html)
- `do(action)` - Perform actions (analyze, discover, refresh)

## Requirements

### Ollama Installation

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (mistral recommended for speed)
ollama pull mistral

# Or use other models
ollama pull llama2
ollama pull phi
```

### Python Dependencies

```bash
# Core dependencies (already installed)
pip install requests

# Optional for better performance
pip install aiohttp  # For async operations
```

## Configuration

### Environment Variables

```bash
# Model selection (default: mistral)
export OLLAMA_MODEL=mistral

# Ollama server URL (default: http://localhost:11434)
export OLLAMA_URL=http://localhost:11434

# Memory file location
export OLLAMA_MEMORY_FILE=ollama_bonjour/service_memory.json
```

### Memory Persistence

Service memory is saved to `ollama_bonjour/service_memory.json` and includes:
- All discovered services
- Service relationships
- Interaction history
- Capability changes over time

## How It Works

1. **Service Announcement**: A service announces via Bonjour
2. **Bridge Captures**: BonjourBridge captures the announcement
3. **Memory Storage**: ServiceMemory stores the service info
4. **Context Building**: When user asks a question, relevant services are added to context
5. **Ollama Processing**: Ollama receives context + question
6. **Intelligent Response**: Ollama responds with service-aware answer
7. **Learning**: Successful interactions are recorded for future use

## Examples

### Finding Services

```python
ollama = get_ollama_bonjour()

# List all services
response = ollama.ask("What services are available?")

# Find specific functionality
response = ollama.ask("How do I generate reports?")

# Get service relationships
analysis = ollama.do("analyze")
print(f"Categories: {analysis['service_categories']}")
```

### Service Memory

```python
from ollama_bonjour import ServiceMemory

memory = ServiceMemory()

# Find services for a goal
services = memory.find_services_for_goal("sync tournament data")
print(f"Relevant services: {services}")

# Get service context
context = memory.get_service_context("Database Service")
print(f"Related services: {context['related_services']}")
```

### Pattern Matching (No LLM)

```python
from ollama_bonjour import ServicePatternMatcher

matcher = ServicePatternMatcher()

# Categorize a service
category = matcher.categorize("StartGG Sync", ["Syncs tournaments"])
print(f"Category: {category}")  # 'sync'

# Match query to category
categories = matcher.match_query_to_category("I need to sync data")
print(f"Relevant categories: {categories}")  # ['sync', 'database']
```

## Troubleshooting

### Ollama Not Starting
```bash
# Check if Ollama is installed
which ollama

# Start manually
ollama serve

# Check status
curl http://localhost:11434/api/tags
```

### Model Not Available
```bash
# List available models
ollama list

# Pull model
ollama pull mistral
```

### Memory Not Persisting
```bash
# Check file permissions
ls -la ollama_bonjour/

# Create directory if needed
mkdir -p ollama_bonjour
```

## Integration with Tournament Tracker

This module integrates seamlessly with the tournament tracker's Bonjour ecosystem:

1. **Discovers all services** automatically
2. **Understands tournament domain** (players, orgs, tournaments)
3. **Routes to appropriate services** (database, sync, visualizer)
4. **Works offline** - no internet required
5. **Learns from usage** - gets smarter over time

## Future Enhancements

- [ ] WebSocket support for real-time announcement monitoring
- [ ] Vector embeddings for semantic service search
- [ ] Multi-model support (switch models based on query type)
- [ ] Service health monitoring
- [ ] Query caching for common questions
- [ ] Visual service graph generation

## Summary

Ollama Bonjour is "Claude's little brother" - a local, offline intelligence that:
- Understands your service landscape
- Routes requests intelligently
- Learns from interactions
- Works without internet
- Provides natural language interface to all services

It's the missing piece that connects Bonjour service discovery to intelligent routing!