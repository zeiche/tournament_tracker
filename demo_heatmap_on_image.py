#!/usr/bin/env python3
"""
Demo: Heat maps on ANY image background - not just maps!
"""
from polymorphic_image_generator import heatmap, PolymorphicImageGenerator
import random
from PIL import Image, ImageDraw
import numpy as np

print("=" * 70)
print("POLYMORPHIC HEAT MAPS ON ANY IMAGE")
print("=" * 70)

# Create a sample image to use as background (like a game screenshot or diagram)
print("\n1. Creating a sample background image (game board)...")
img = Image.new('RGB', (800, 600), color='#2a2a2a')
draw = ImageDraw.Draw(img)

# Draw a grid pattern (like a game board)
for x in range(0, 800, 50):
    draw.line([(x, 0), (x, 600)], fill='#444444', width=1)
for y in range(0, 600, 50):
    draw.line([(0, y), (800, y)], fill='#444444', width=1)

# Add some features (like game elements)
draw.rectangle([100, 100, 200, 200], fill='#4a4a8a', outline='white')
draw.rectangle([600, 400, 700, 500], fill='#8a4a4a', outline='white')
draw.ellipse([350, 250, 450, 350], fill='#4a8a4a', outline='white')

img.save('game_board.png')
print("  ✅ Created game_board.png")

# Generate click/activity data on this image
print("\n2. Simulating player activity data on the game board...")
activity_data = []

# Cluster 1: Heavy activity around the blue square
for _ in range(20):
    x = random.gauss(150, 30)
    y = random.gauss(150, 30)
    activity_data.append({"x": x, "y": y, "weight": random.randint(5, 10)})

# Cluster 2: Moderate activity around the circle
for _ in range(15):
    x = random.gauss(400, 40)
    y = random.gauss(300, 40)
    activity_data.append({"x": x, "y": y, "weight": random.randint(3, 7)})

# Cluster 3: Light activity around the red square
for _ in range(10):
    x = random.gauss(650, 25)
    y = random.gauss(450, 25)
    activity_data.append({"x": x, "y": y, "weight": random.randint(1, 5)})

# Random scattered activity
for _ in range(15):
    x = random.uniform(50, 750)
    y = random.uniform(50, 550)
    activity_data.append({"x": x, "y": y, "weight": random.randint(1, 3)})

print(f"  Generated {len(activity_data)} activity points")

# Generate heat map on the custom image
print("\n3. Overlaying heat map on the game board...")
heatmap(activity_data,
        "game_activity_heatmap.png",
        background="game_board.png",  # Use our custom image!
        style="fire",
        hint="activity")

print("  ✅ Generated: game_activity_heatmap.png")

# Demo 2: UI/UX click tracking
print("\n4. Simulating UI click tracking...")

# Create a mock UI layout
ui_img = Image.new('RGB', (1024, 768), color='white')
draw = ImageDraw.Draw(ui_img)

# Draw UI elements
draw.rectangle([50, 50, 974, 100], fill='#333333')  # Header
draw.rectangle([50, 120, 250, 718], fill='#f0f0f0')  # Sidebar
draw.rectangle([270, 120, 974, 400], fill='#ffffff', outline='#cccccc')  # Main content
draw.rectangle([270, 420, 620, 718], fill='#ffffff', outline='#cccccc')  # Bottom left
draw.rectangle([640, 420, 974, 718], fill='#ffffff', outline='#cccccc')  # Bottom right

# Add some buttons
buttons = [
    (100, 65, 180, 85, '#4CAF50'),   # Header button 1
    (200, 65, 280, 85, '#2196F3'),   # Header button 2
    (100, 150, 200, 180, '#FF9800'),  # Sidebar button
    (100, 200, 200, 230, '#FF9800'),  # Sidebar button
]

for x1, y1, x2, y2, color in buttons:
    draw.rectangle([x1, y1, x2, y2], fill=color)

ui_img.save('ui_mockup.png')
print("  ✅ Created UI mockup")

# Generate realistic click data
clicks = []

# Heavy clicks on header buttons
for _ in range(30):
    x = random.gauss(140, 15)
    y = random.gauss(75, 5)
    clicks.append((x, y, 8))

for _ in range(25):
    x = random.gauss(240, 15)
    y = random.gauss(75, 5)
    clicks.append((x, y, 6))

# Moderate clicks in main content area
for _ in range(40):
    x = random.uniform(300, 940)
    y = random.uniform(150, 370)
    clicks.append((x, y, 3))

# Some sidebar navigation clicks
for _ in range(20):
    x = random.gauss(150, 30)
    y = random.uniform(150, 650)
    clicks.append((x, y, 4))

print(f"  Generated {len(clicks)} UI clicks")

# Generate heat map
print("\n5. Creating UI click heat map...")
heatmap(clicks,
        "ui_click_heatmap.png",
        background="ui_mockup.png",
        style="thermal",
        hint="clicks")

print("  ✅ Generated: ui_click_heatmap.png")

# Demo 3: Any data on any image
print("\n6. Overlaying tournament data on a custom map image...")

# Use existing tournament data but on a different background
from database import get_session
from tournament_models import Tournament

with get_session() as session:
    tournaments = session.query(Tournament).filter(
        Tournament.lat.isnot(None),
        Tournament.lng.isnot(None)
    ).limit(20).all()
    
    if tournaments:
        # Normalize coordinates to fit on our game board
        normalized_data = []
        
        # Get coordinate ranges (convert to float)
        lats = [float(t.lat) for t in tournaments if t.lat]
        lngs = [float(t.lng) for t in tournaments if t.lng]
        
        lat_min, lat_max = min(lats), max(lats)
        lng_min, lng_max = min(lngs), max(lngs)
        
        for t in tournaments:
            if not t.lat or not t.lng:
                continue
            # Map to image coordinates (800x600)
            x = ((float(t.lng) - lng_min) / (lng_max - lng_min)) * 700 + 50
            y = ((lat_max - float(t.lat)) / (lat_max - lat_min)) * 500 + 50  # Flip Y
            weight = t.num_attendees or 10
            
            normalized_data.append({"x": x, "y": y, "weight": weight})
        
        print(f"  Normalized {len(normalized_data)} tournament locations")
        
        # Overlay on game board for fun visualization
        heatmap(normalized_data,
                "tournaments_on_gameboard.png",
                background="game_board.png",
                style="plasma",
                hint="tournaments")
        
        print("  ✅ Generated: tournaments_on_gameboard.png")

print("\n" + "=" * 70)
print("POLYMORPHIC IMAGE GENERATOR CAPABILITIES:")
print("  ✅ Overlay heat maps on ANY image - not just maps!")
print("  ✅ Track user activity on game screens")
print("  ✅ Visualize UI/UX click patterns")
print("  ✅ Map any data to any coordinate space")
print("  ✅ Mix geographic and non-geographic visualizations")
print("=" * 70)