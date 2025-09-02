#!/usr/bin/env python3
"""
tournament_heatmap.py - Generate heat map visualizations of tournament locations
Creates both static images and interactive HTML maps
"""

import json
import numpy as np
from database_utils import get_session
from tournament_models import Tournament
from log_utils import log_info, log_error

def generate_static_heatmap(output_file='tournament_heatmap.png', dpi=150):
    """
    Generate a static heat map image of tournament locations
    Focused on Southern California region
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        from matplotlib.colors import LinearSegmentedColormap
        from scipy.stats import gaussian_kde
    except ImportError:
        log_error("matplotlib or scipy not installed. Run: pip3 install matplotlib scipy", "heatmap")
        return False
    
    log_info("Generating static heat map", "heatmap")
    
    # Get tournament data and extract coordinates within session
    lats = []
    lngs = []
    weights = []
    
    with get_session() as session:
        tournaments = session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.lng.isnot(None)
        ).all()
        
        if not tournaments:
            log_error("No tournaments with geographic data found", "heatmap")
            return False
        
        # Extract data while in session
        for t in tournaments:
            try:
                lat = float(t.lat)
                lng = float(t.lng)
                
                # Focus on SoCal region (rough boundaries)
                if 32.5 <= lat <= 34.5 and -119 <= lng <= -116:
                    lats.append(lat)
                    lngs.append(lng)
                    # Weight by attendance (log scale to prevent outliers from dominating)
                    weight = np.log10(max(t.num_attendees or 1, 1))
                    weights.append(weight)
            except (ValueError, TypeError):
                continue
    
    if not lats:
        log_error("No valid SoCal tournament locations found", "heatmap")
        return False
    
    log_info(f"Processing {len(lats)} tournament locations", "heatmap")
    
    # Create figure with dark background
    fig, ax = plt.subplots(figsize=(16, 12), facecolor='#1a1a1a')
    ax.set_facecolor('#1a1a1a')
    
    # Set map boundaries (SoCal region)
    lng_min, lng_max = -119, -116
    lat_min, lat_max = 32.5, 34.5
    
    # Create density estimation
    xy = np.vstack([lngs, lats])
    
    # Create grid for heat map
    xx, yy = np.mgrid[lng_min:lng_max:200j, lat_min:lat_max:200j]
    positions = np.vstack([xx.ravel(), yy.ravel()])
    
    # Calculate kernel density with weights
    if len(weights) > 1:
        kernel = gaussian_kde(xy, weights=weights)
        density = np.reshape(kernel(positions).T, xx.shape)
    else:
        # Fallback for single point
        density = np.zeros_like(xx)
        density[len(density)//2, len(density[0])//2] = 1
    
    # Create custom colormap (dark to bright heat)
    colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
              '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
    n_bins = 256
    cmap = LinearSegmentedColormap.from_list('tournament_heat', colors, N=n_bins)
    
    # Plot heat map
    im = ax.imshow(np.rot90(density), extent=[lng_min, lng_max, lat_min, lat_max],
                   cmap=cmap, alpha=0.8, aspect='auto')
    
    # Plot individual tournaments as points
    scatter = ax.scatter(lngs, lats, c='white', s=weights, alpha=0.3, edgecolors='cyan', linewidth=0.5)
    
    # Add city labels for reference
    cities = {
        'Los Angeles': (34.0522, -118.2437),
        'San Diego': (32.7157, -117.1611),
        'Long Beach': (33.7701, -118.1937),
        'Anaheim': (33.8366, -117.9143),
        'Santa Ana': (33.7455, -117.8677),
        'Riverside': (33.9533, -117.3962),
        'Irvine': (33.6846, -117.8265)
    }
    
    for city, (lat, lng) in cities.items():
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            ax.plot(lng, lat, 'w*', markersize=10, markeredgecolor='gold', markeredgewidth=1)
            ax.text(lng, lat + 0.03, city, color='white', fontsize=10, 
                   ha='center', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#1a1a1a', alpha=0.7))
    
    # Styling
    ax.set_xlabel('Longitude', color='white', fontsize=12)
    ax.set_ylabel('Latitude', color='white', fontsize=12)
    ax.set_title('Southern California FGC Tournament Heat Map', 
                color='white', fontsize=16, fontweight='bold', pad=20)
    
    # Grid
    ax.grid(True, alpha=0.2, color='white', linestyle='--')
    ax.tick_params(colors='white')
    
    # Color bar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Tournament Density (weighted by attendance)', 
                   color='white', fontsize=10)
    cbar.ax.tick_params(colors='white')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
    
    # Stats text
    stats_text = f"Total Tournaments: {len(lats)}\nTotal Attendance: {sum(10**w for w in weights):,.0f}"
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=11, color='white', verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='#1a1a1a', alpha=0.8))
    
    # Save
    plt.tight_layout()
    plt.savefig(output_file, dpi=dpi, facecolor='#1a1a1a', edgecolor='none')
    plt.close()
    
    log_info(f"Heat map saved to {output_file}", "heatmap")
    return True

def generate_interactive_heatmap(output_file='tournament_heatmap.html'):
    """
    Generate an interactive heat map using folium
    Users can zoom, pan, and click on tournaments for details
    """
    try:
        import folium
        from folium.plugins import HeatMap, MarkerCluster
    except ImportError:
        log_error("folium not installed. Run: pip3 install folium", "heatmap")
        return False
    
    log_info("Generating interactive heat map", "heatmap")
    
    # Create base map centered on LA
    center_lat, center_lng = 33.8, -117.9
    m = folium.Map(location=[center_lat, center_lng], 
                   zoom_start=9,
                   tiles='CartoDB dark_matter')
    
    # Prepare data for heat map
    heat_data = []
    marker_cluster = MarkerCluster().add_to(m)
    
    # Get tournament data and process within session
    with get_session() as session:
        tournaments = session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.lng.isnot(None)
        ).all()
        
        if not tournaments:
            log_error("No tournaments with geographic data found", "heatmap")
            return False
        
        for t in tournaments:
            try:
                lat = float(t.lat)
                lng = float(t.lng)
                
                # Add to heat map data (lat, lng, weight)
                weight = np.log10(max(t.num_attendees or 1, 1))
                heat_data.append([lat, lng, weight])
                
                # Add marker with popup info
                popup_html = f"""
                <div style='font-family: sans-serif; width: 250px;'>
                    <h4 style='margin: 0 0 10px 0;'>{t.name}</h4>
                    <p style='margin: 5px 0;'><b>Venue:</b> {t.venue_name or 'Unknown'}</p>
                    <p style='margin: 5px 0;'><b>City:</b> {t.city or 'Unknown'}</p>
                    <p style='margin: 5px 0;'><b>Attendance:</b> {t.num_attendees or 0:,}</p>
                    <p style='margin: 5px 0;'><b>Date:</b> {t.start_at or 'Unknown'}</p>
                </div>
                """
                
                # Color based on attendance
                if t.num_attendees and t.num_attendees > 100:
                    icon_color = 'red'
                elif t.num_attendees and t.num_attendees > 50:
                    icon_color = 'orange'
                else:
                    icon_color = 'blue'
                
                folium.Marker(
                    [lat, lng],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{t.name} ({t.num_attendees or 0} attendees)",
                    icon=folium.Icon(color=icon_color, icon='gamepad', prefix='fa')
                ).add_to(marker_cluster)
                    
            except (ValueError, TypeError):
                continue
    
    # Add heat map layer
    if heat_data:
        HeatMap(heat_data, 
                radius=15,
                blur=10,
                gradient={
                    0.0: 'blue',
                    0.25: 'cyan',
                    0.5: 'lime',
                    0.75: 'yellow',
                    1.0: 'red'
                }).add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50%; transform: translateX(-50%);
                z-index: 1000;
                background-color: rgba(0,0,0,0.8);
                color: white;
                padding: 10px 20px;
                border-radius: 10px;
                font-family: sans-serif;">
        <h3 style="margin: 0;">SoCal FGC Tournament Heat Map</h3>
        <p style="margin: 5px 0 0 0; font-size: 12px;">
            {count} tournaments • Click markers for details • Red = High attendance
        </p>
    </div>
    '''.format(count=len(heat_data))
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save map
    m.save(output_file)
    log_info(f"Interactive heat map saved to {output_file}", "heatmap")
    return True

def generate_attendance_heatmap(output_file='attendance_heatmap.png'):
    """
    Generate a heat map specifically showing attendance density
    Larger circles for higher attendance tournaments
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.collections import PatchCollection
    except ImportError:
        log_error("matplotlib not installed", "heatmap")
        return False
    
    log_info("Generating attendance density map", "heatmap")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 12), facecolor='black')
    ax.set_facecolor('#0a0a0a')
    
    # Set boundaries
    lng_min, lng_max = -119, -116
    lat_min, lat_max = 32.5, 34.5
    
    # Create circles for each tournament
    circles = []
    colors = []
    
    # Get tournament data and process within session
    with get_session() as session:
        tournaments = session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.lng.isnot(None),
            Tournament.num_attendees > 0
        ).all()
        
        if not tournaments:
            return False
        
        for t in tournaments:
            try:
                lat = float(t.lat)
                lng = float(t.lng)
                
                if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
                    # Circle size based on attendance
                    radius = np.sqrt(t.num_attendees) / 500
                    circle = patches.Circle((lng, lat), radius, alpha=0.6)
                    circles.append(circle)
                    
                    # Color based on attendance tiers
                    if t.num_attendees > 200:
                        colors.append('#ff0000')  # Red for major
                    elif t.num_attendees > 100:
                        colors.append('#ff8800')  # Orange for regional
                    elif t.num_attendees > 50:
                        colors.append('#ffff00')  # Yellow for local
                    else:
                        colors.append('#00ffff')  # Cyan for weekly
                            
            except (ValueError, TypeError):
                continue
    
    # Add circles to plot
    p = PatchCollection(circles, alpha=0.4)
    p.set_facecolor(colors)
    p.set_edgecolor('white')
    p.set_linewidth(0.5)
    ax.add_collection(p)
    
    # Styling
    ax.set_xlim(lng_min, lng_max)
    ax.set_ylim(lat_min, lat_max)
    ax.set_xlabel('Longitude', color='white', fontsize=12)
    ax.set_ylabel('Latitude', color='white', fontsize=12)
    ax.set_title('Tournament Attendance Density Map\n(Circle size = attendance)', 
                color='white', fontsize=16, fontweight='bold')
    
    # Legend
    legend_elements = [
        patches.Patch(color='#ff0000', label='Major (200+)', alpha=0.6),
        patches.Patch(color='#ff8800', label='Regional (100-200)', alpha=0.6),
        patches.Patch(color='#ffff00', label='Local (50-100)', alpha=0.6),
        patches.Patch(color='#00ffff', label='Weekly (<50)', alpha=0.6)
    ]
    ax.legend(handles=legend_elements, loc='upper right', 
             facecolor='black', edgecolor='white', labelcolor='white')
    
    ax.grid(True, alpha=0.2, color='white', linestyle=':')
    ax.tick_params(colors='white')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, facecolor='black')
    plt.close()
    
    log_info(f"Attendance density map saved to {output_file}", "heatmap")
    return True

if __name__ == "__main__":
    print("Generating tournament heat maps...")
    
    # Generate all three types
    if generate_static_heatmap():
        print("✓ Static heat map created: tournament_heatmap.png")
    
    if generate_interactive_heatmap():
        print("✓ Interactive map created: tournament_heatmap.html")
    
    if generate_attendance_heatmap():
        print("✓ Attendance density map created: attendance_heatmap.png")
    
    print("\nView the .png files with an image viewer")
    print("Open tournament_heatmap.html in a browser for interactive map")