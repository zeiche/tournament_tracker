#!/usr/bin/env python3
"""
Demo: True layer-based bitmap where each function writes to its own layer
Just like you originally envisioned - functions write to a shared bitmap!
"""
from polymorphic_bitmap_layers import PolymorphicBitmapLayers, BlendMode
from database import get_session
from tournament_models import Tournament, Player
import random
import math

print("=" * 70)
print("TRUE LAYER-BASED BITMAP SYSTEM")
print("Each function writes to its own transparent layer!")
print("=" * 70)

# Create the shared bitmap that all functions will write to
bitmap = PolymorphicBitmapLayers(1024, 768, background=(20, 20, 30, 255))

# Function 1: Draw a map outline
def draw_map_outline(bitmap):
    """This function draws to the 'Map' layer"""
    print("\n1. Function drawing map outline...")
    
    def draw_func(draw):
        # Draw a simplified California outline
        points = [
            (700, 100), (750, 150), (780, 250), (790, 350),
            (780, 450), (750, 550), (700, 600), (650, 580),
            (600, 550), (550, 500), (500, 450), (480, 350),
            (490, 250), (520, 150), (580, 100), (700, 100)
        ]
        draw.polygon(points, outline=(100, 200, 100, 200), fill=(50, 100, 50, 50), width=2)
        
        # Add some city markers
        cities = [
            (650, 400, "LA"), (600, 300, "SB"), (680, 480, "SD"),
            (550, 200, "SF"), (600, 250, "SJ")
        ]
        for x, y, name in cities:
            draw.ellipse([x-5, y-5, x+5, y+5], fill=(200, 200, 100, 150))
    
    bitmap.draw_on_layer("Map Outline", draw_func)
    bitmap.adjust_layer_opacity("Map Outline", 0.6)

# Function 2: Add tournament heat map
def add_tournament_heat(bitmap):
    """This function writes to the 'Tournament Heat' layer"""
    print("2. Function adding tournament heat map...")
    
    with get_session() as session:
        tournaments = session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.lng.isnot(None)
        ).limit(30).all()
        
        if tournaments:
            # Convert to heat points
            heat_points = []
            for t in tournaments:
                # Simple coordinate mapping (not accurate, just for demo)
                x = 650 + (float(t.lng) + 118) * 50
                y = 400 - (float(t.lat) - 34) * 50
                weight = (t.num_attendees or 10) / 10
                heat_points.append((x, y, weight))
            
            bitmap.apply_heat_map("Tournament Heat", heat_points, 
                                colormap='hot', blur_radius=20, opacity=0.8)
            
            print(f"   Added {len(heat_points)} tournament heat points")

# Function 3: Add player locations
def add_player_clusters(bitmap):
    """This function writes to the 'Player Clusters' layer"""
    print("3. Function adding player cluster visualization...")
    
    # Generate synthetic player clusters
    clusters = [
        (650, 400, 30, (255, 100, 100, 100)),  # LA cluster - red
        (680, 480, 20, (100, 100, 255, 100)),  # SD cluster - blue
        (600, 250, 15, (100, 255, 100, 100)),  # SJ cluster - green
    ]
    
    def draw_func(draw):
        for cx, cy, size, color in clusters:
            # Draw cluster as gradient circles
            for r in range(size, 0, -2):
                alpha = int(color[3] * (r / size))
                c = (*color[:3], alpha)
                draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=c)
    
    bitmap.draw_on_layer("Player Clusters", draw_func)
    print("   Added 3 player cluster regions")

# Function 4: Add activity indicators
def add_activity_pulses(bitmap):
    """This function writes to the 'Activity' layer"""
    print("4. Function adding activity pulses...")
    
    def draw_func(draw):
        # Add pulsing activity indicators
        for _ in range(20):
            x = random.randint(500, 750)
            y = random.randint(200, 550)
            size = random.randint(3, 10)
            intensity = random.randint(100, 255)
            
            # Draw pulse rings
            for ring in range(3):
                r = size + ring * 5
                alpha = max(0, intensity - ring * 80)
                draw.ellipse([x-r, y-r, x+r, y+r], 
                           outline=(255, 255, 100, alpha), width=2)
    
    bitmap.draw_on_layer("Activity Pulses", draw_func)
    bitmap.adjust_layer_opacity("Activity Pulses", 0.5)
    print("   Added 20 activity pulse indicators")

# Function 5: Add data overlay
def add_data_overlay(bitmap):
    """This function writes to the 'Data Overlay' layer"""
    print("5. Function adding data visualization overlay...")
    
    def draw_func(draw):
        # Draw connection lines between cities
        connections = [
            ((650, 400), (680, 480)),  # LA to SD
            ((650, 400), (600, 250)),  # LA to SJ
            ((600, 300), (650, 400)),  # SB to LA
            ((550, 200), (600, 250)),  # SF to SJ
        ]
        
        for (x1, y1), (x2, y2) in connections:
            # Draw connection with gradient
            steps = 20
            for i in range(steps):
                t = i / steps
                x = x1 + (x2 - x1) * t
                y = y1 + (y2 - y1) * t
                alpha = int(100 * (1 - abs(t - 0.5) * 2))
                draw.ellipse([x-1, y-1, x+1, y+1], fill=(100, 200, 255, alpha))
    
    bitmap.draw_on_layer("Data Connections", draw_func)
    print("   Added data connection paths")

# Function 6: Add UI elements
def add_ui_elements(bitmap):
    """This function writes to the 'UI' layer"""
    print("6. Function adding UI elements...")
    
    def draw_func(draw):
        # Title bar
        draw.rectangle([0, 0, 1024, 60], fill=(0, 0, 0, 180))
        draw.rectangle([0, 60, 1024, 62], fill=(100, 200, 255, 200))
        
        # Legend box
        draw.rectangle([20, 80, 220, 280], fill=(0, 0, 0, 150))
        draw.rectangle([20, 80, 220, 280], outline=(100, 200, 255, 200), width=2)
        
        # Info panel
        draw.rectangle([804, 80, 1004, 280], fill=(0, 0, 0, 150))
        draw.rectangle([804, 80, 1004, 280], outline=(255, 200, 100, 200), width=2)
    
    bitmap.draw_on_layer("UI Elements", draw_func)
    print("   Added UI overlay elements")

# Function 7: Add effects layer
def add_glow_effects(bitmap):
    """This function adds glow effects on its own layer"""
    print("7. Function adding glow effects...")
    
    def draw_func(draw):
        # Add glow around hot spots
        glow_spots = [(650, 400), (680, 480), (600, 250)]
        
        for x, y in glow_spots:
            for r in range(50, 0, -5):
                alpha = int(50 * (1 - r/50))
                draw.ellipse([x-r, y-r, x+r, y+r], 
                           fill=(255, 255, 200, alpha))
    
    layer = bitmap.add_layer("Glow Effects", blend_mode=BlendMode.ADD)
    bitmap.draw_on_layer("Glow Effects", draw_func)
    bitmap.adjust_layer_opacity("Glow Effects", 0.3)
    print("   Added glow effects with ADD blend mode")

# Now call all functions - each writes to its own layer!
print("\n🎨 Each function writes to its own transparent layer:")
draw_map_outline(bitmap)
add_tournament_heat(bitmap)
add_player_clusters(bitmap)
add_activity_pulses(bitmap)
add_data_overlay(bitmap)
add_ui_elements(bitmap)
add_glow_effects(bitmap)

# Show the layer stack
print("\n📚 Final layer stack:")
bitmap.list_layers()

# Save the composite
print("\n💾 Saving final composited image...")
bitmap.save("multi_function_layers.png")

# Save individual layers to show transparency
print("\n💾 Saving individual transparent layers...")
bitmap.save_layers("function_layers")

# Demonstrate layer manipulation
print("\n🔧 Demonstrating layer manipulation:")

# Turn off some layers
print("   Hiding UI and Activity layers...")
bitmap.get_layer("UI Elements").visible = False
bitmap.get_layer("Activity Pulses").visible = False
bitmap.save("layers_without_ui.png")

# Change blend modes
print("   Changing Tournament Heat to MULTIPLY blend...")
bitmap.get_layer("Tournament Heat").blend_mode = BlendMode.MULTIPLY
bitmap.save("layers_multiply_blend.png")

# Reorder layers
print("   Moving Map Outline to top...")
bitmap.reorder_layer("Map Outline", len(bitmap.layers) - 1)
bitmap.save("layers_reordered.png")

print("\n" + "=" * 70)
print("✅ TRUE LAYER SYSTEM DEMONSTRATED!")
print("Key features shown:")
print("  • Each function writes to its own transparent layer")
print("  • Full alpha channel support (RGBA)")
print("  • Photoshop-style blend modes (Normal, Add, Multiply, etc.)")
print("  • Layer management (show/hide, reorder, merge)")
print("  • Independent opacity control per layer")
print("  • Save individual layers or composited result")
print("\nThis is exactly what you envisioned:")
print("A bitmap that functions write to, with true transparency!")
print("=" * 70)