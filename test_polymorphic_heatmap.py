#!/usr/bin/env python3
"""
Test the polymorphic image generator with real tournament data
"""
from polymorphic_image_generator import heatmap, PolymorphicImageGenerator, HeatStyle
from database import get_session
from tournament_models import Tournament, Player, Organization
import random

print("=" * 70)
print("TESTING POLYMORPHIC IMAGE GENERATOR")
print("=" * 70)

# Test 1: Tournament locations with auto-detection
print("\n1. TOURNAMENT HEAT MAP (auto-detects geographic data):")
with get_session() as session:
    # Get tournaments with location data
    tournaments = session.query(Tournament).filter(
        Tournament.lat.isnot(None),
        Tournament.lng.isnot(None)
    ).limit(50).all()
    
    if tournaments:
        print(f"  Found {len(tournaments)} tournaments with locations")
        print("  Generating heat map with auto-detected map background...")
        
        # Just pass the tournaments - it figures everything out!
        heatmap(tournaments, 
                "tournaments_heatmap.png", 
                hint="attendance",  # Use attendance for weights
                style="fire")
        
        print("  ✅ Generated: tournaments_heatmap.png")
    else:
        print("  No tournaments with location data found")

# Test 2: Multiple visualization styles
print("\n2. DIFFERENT HEAT STYLES:")
if tournaments:
    styles = ["classic", "cool", "ocean", "thermal"]
    for style in styles:
        output = f"tournaments_{style}.png"
        heatmap(tournaments[:20], output, style=style, hint="attendance")
        print(f"  ✅ Generated: {output}")

# Test 3: Non-geographic data (player performance)
print("\n3. NON-GEOGRAPHIC DATA (player skill distribution):")
with get_session() as session:
    # Create synthetic skill map data
    players = session.query(Player).limit(30).all()
    
    if players:
        # Create fake "skill positions" for visualization
        skill_points = []
        for player in players:
            # Calculate player stats
            wins = sum(1 for p in player.placements if p.placement == 1)
            events = len(player.placements)
            win_rate = (wins / events * 100) if events > 0 else 0
            
            # Map to 2D space (fake coordinates for demo)
            x = win_rate  # X-axis: win rate
            y = events    # Y-axis: number of events
            weight = wins # Weight: total wins
            
            skill_points.append({
                "x": x,
                "y": y, 
                "weight": weight,
                "name": player.gamer_tag
            })
        
        print(f"  Mapping {len(skill_points)} players to skill space")
        print("  X-axis: Win Rate, Y-axis: Events Played, Weight: Total Wins")
        
        heatmap(skill_points,
                "player_skill_distribution.png",
                background="blank",  # No map for non-geographic data
                style="plasma")
        
        print("  ✅ Generated: player_skill_distribution.png")

# Test 4: Mixed data types
print("\n4. MIXED DATA TYPES IN ONE IMAGE:")
mixed_data = []

# Add some tournaments
if tournaments:
    mixed_data.extend(tournaments[:10])

# Add raw coordinate tuples
mixed_data.extend([
    (34.0, -118.0, 5),  # Los Angeles area
    (33.0, -117.0, 3),  # San Diego area
])

# Add dicts with coordinates
mixed_data.extend([
    {"lat": 34.5, "lng": -118.5, "weight": 8},
    {"lat": 33.5, "lng": -117.5, "value": 6},
])

if mixed_data:
    print(f"  Combining {len(mixed_data)} items of different types")
    heatmap(mixed_data, "mixed_data_heatmap.png", style="thermal")
    print("  ✅ Generated: mixed_data_heatmap.png")

# Test 5: Custom objects
print("\n5. CUSTOM OBJECTS WITH AUTO-DETECTION:")

class VenueActivity:
    """Custom class the generator has never seen"""
    def __init__(self, name, lat, lng, events_hosted):
        self.venue_name = name
        self.lat = lat
        self.lng = lng
        self.event_count = events_hosted
        self.random_stat = random.randint(1, 100)

venues = [
    VenueActivity("Venue A", 34.05, -118.25, 25),
    VenueActivity("Venue B", 33.95, -118.15, 15),
    VenueActivity("Venue C", 34.10, -118.30, 30),
    VenueActivity("Venue D", 33.90, -118.20, 10),
]

print("  Created custom VenueActivity objects")
print("  The generator will auto-detect lat/lng and weight attributes...")

heatmap(venues, 
        "venue_activity.png",
        hint="frequency",  # Will look for event_count
        style="cool")

print("  ✅ Generated: venue_activity.png")

# Test 6: Multi-layer visualization
print("\n6. MULTI-LAYER HEAT MAP:")
if tournaments and len(tournaments) > 20:
    print("  Creating multi-layer visualization...")
    
    # Split tournaments into "recent" and "older"
    recent = tournaments[:10]
    older = tournaments[10:20]
    
    PolymorphicImageGenerator.generate_multi_layer([
        (recent, "fire", 0.7),   # Recent tournaments in red
        (older, "cool", 0.5),    # Older tournaments in blue
    ], "multi_layer_tournaments.png")
    
    print("  ✅ Generated: multi_layer_tournaments.png")

print("\n" + "=" * 70)
print("POLYMORPHIC IMAGE GENERATOR TEST COMPLETE!")
print("Generated heat maps from:")
print("  • Database models (Tournament, Player)")
print("  • Raw tuples and dictionaries")
print("  • Custom objects never seen before")
print("  • Mixed data types in single image")
print("  • Both geographic and non-geographic data")
print("=" * 70)