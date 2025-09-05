#!/usr/bin/env python3
"""
tournament_heatmap.py - Generate heat map visualizations of tournament locations
Creates both static images and interactive HTML maps
"""

import json
import numpy as np
from database import session_scope
from tournament_models import Tournament
from log_utils import log_info, log_error

def generate_static_heatmap(output_file='tournament_heatmap.png', dpi=150, use_map_background=True):
    """
    Generate a static heat map image of tournament locations
    Focused on Southern California region
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        from matplotlib.colors import LinearSegmentedColormap
        from scipy.stats import gaussian_kde
        if use_map_background:
            import contextily as ctx
    except ImportError as e:
        log_error(f"Missing dependencies: {e}. Run: pip3 install matplotlib scipy contextily", "heatmap")
        return False
    
    log_info("Generating static heat map", "heatmap")
    
    # Get tournament data using new location methods
    lats = []
    lngs = []
    weights = []
    
    with session_scope() as session:
        # Get all tournaments with geographic data
        tournaments = session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.lng.isnot(None)
        ).all()
        
        if not tournaments:
            log_error("No tournaments with geographic data found", "heatmap")
            return False
        
        # Extract data using new methods
        for t in tournaments:
            if t.has_location and t.coordinates:
                lat, lng = t.coordinates
                lats.append(lat)
                lngs.append(lng)
                # Use the new get_heatmap_weight() method
                weights.append(t.get_heatmap_weight())
    
    if not lats:
        log_error("No valid tournament locations found", "heatmap")
        return False
    
    log_info(f"Processing {len(lats)} tournament locations", "heatmap")
    
    # Create figure
    if use_map_background:
        fig, ax = plt.subplots(figsize=(16, 12), facecolor='white')
        ax.set_facecolor('white')
    else:
        fig, ax = plt.subplots(figsize=(16, 12), facecolor='#1a1a1a')
        ax.set_facecolor('#1a1a1a')
    
    # Set map boundaries (SoCal region)
    lng_min, lng_max = -119, -116
    lat_min, lat_max = 32.5, 34.5
    
    # Set axis limits first
    ax.set_xlim(lng_min, lng_max)
    ax.set_ylim(lat_min, lat_max)
    
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
    
    # Create custom colormap
    if use_map_background:
        # Red/orange heat colors for map background
        colors = ['#00000000', '#ff000033', '#ff330066', '#ff660099',
                 '#ff9900cc', '#ffcc00ee', '#ffff00ff']
        cmap_alpha = 0.5
    else:
        # Original blue/white colors for dark background
        colors = ['#000033', '#000055', '#0000ff', '#0055ff', '#00ffff', 
                 '#55ff00', '#ffff00', '#ff5500', '#ff0000', '#ffffff']
        cmap_alpha = 0.8
        
    n_bins = 256
    cmap = LinearSegmentedColormap.from_list('tournament_heat', colors, N=n_bins)
    
    # Add map background if requested (after setting limits)
    if use_map_background:
        try:
            ctx.add_basemap(ax, 
                          crs='EPSG:4326',  # Lat/lng coordinate system
                          source=ctx.providers.CartoDB.Positron,  # Light map style
                          zoom=10,
                          alpha=1.0)
            log_info("Added map background", "heatmap")
        except Exception as e:
            log_error(f"Could not add map background: {e}", "heatmap")
            use_map_background = False  # Fall back to no background
    
    # Plot heat map on top of map
    im = ax.imshow(np.rot90(density), extent=[lng_min, lng_max, lat_min, lat_max],
                   cmap=cmap, alpha=cmap_alpha, aspect='auto', zorder=2)
    
    # Plot individual tournaments as points
    if use_map_background:
        scatter = ax.scatter(lngs, lats, c='red', s=weights, alpha=0.4, 
                           edgecolors='darkred', linewidth=0.5, zorder=3)
    else:
        scatter = ax.scatter(lngs, lats, c='white', s=weights, alpha=0.3, 
                           edgecolors='cyan', linewidth=0.5, zorder=3)
    
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
    
    # Styling - use appropriate colors based on background
    text_color = 'black' if use_map_background else 'white'
    grid_color = 'gray' if use_map_background else 'white'
    
    ax.set_xlabel('Longitude', color=text_color, fontsize=12)
    ax.set_ylabel('Latitude', color=text_color, fontsize=12)
    ax.set_title('Southern California FGC Tournament Heat Map', 
                color=text_color, fontsize=16, fontweight='bold', pad=20)
    
    # Grid
    ax.grid(True, alpha=0.2, color=grid_color, linestyle='--')
    ax.tick_params(colors=text_color)
    
    # Color bar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Tournament Density (weighted by attendance)', 
                   color=text_color, fontsize=10)
    cbar.ax.tick_params(colors=text_color)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=text_color)
    
    # Stats text
    stats_text = f"Total Tournaments: {len(lats)}\nTotal Attendance: {sum(10**w for w in weights):,.0f}"
    bg_color = 'white' if use_map_background else '#1a1a1a'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=11, color=text_color, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor=bg_color, alpha=0.8))
    
    # Save
    plt.tight_layout()
    save_bg = 'white' if use_map_background else '#1a1a1a'
    plt.savefig(output_file, dpi=dpi, facecolor=save_bg, edgecolor='none')
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
    
    # Get tournament data using new location methods
    with session_scope() as session:
        # Get all tournaments with location data
        tournaments = Tournament.with_location().all()
        
        if not tournaments:
            log_error("No tournaments with geographic data found", "heatmap")
            return False
        
        for t in tournaments:
            if t.has_location and t.coordinates:
                lat, lng = t.coordinates
                
                # Add to heat map data using new methods
                weight = t.get_heatmap_weight()
                heat_data.append([lat, lng, weight])
                
                # Add marker with popup info using new properties
                popup_html = f"""
                <div style='font-family: sans-serif; width: 250px;'>
                    <h4 style='margin: 0 0 10px 0;'>{t.name}</h4>
                    <p style='margin: 5px 0;'><b>Venue:</b> {t.venue_name or 'Unknown'}</p>
                    <p style='margin: 5px 0;'><b>Address:</b> {t.full_address}</p>
                    <p style='margin: 5px 0;'><b>Attendance:</b> {t.num_attendees or 0:,}</p>
                    <p style='margin: 5px 0;'><b>Date:</b> {t.start_date.strftime('%Y-%m-%d') if t.start_date else 'Unknown'}</p>
                    <p style='margin: 5px 0;'><b>Status:</b> {'Finished' if t.is_finished() else 'Upcoming' if t.is_upcoming else 'Active' if t.is_active else 'Past'}</p>
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

def generate_attendance_heatmap(output_file='attendance_heatmap.png', use_map_background=True):
    """
    Generate a heat map specifically showing attendance density
    Larger circles for higher attendance tournaments
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.collections import PatchCollection
        if use_map_background:
            import contextily as ctx
    except ImportError as e:
        log_error(f"Missing dependencies: {e}", "heatmap")
        return False
    
    log_info("Generating attendance density map", "heatmap")
    
    # Create figure
    if use_map_background:
        fig, ax = plt.subplots(figsize=(16, 12))
    else:
        fig, ax = plt.subplots(figsize=(16, 12), facecolor='black')
        ax.set_facecolor('#0a0a0a')
    
    # Set boundaries
    lng_min, lng_max = -119, -116
    lat_min, lat_max = 32.5, 34.5
    
    # Create circles for each tournament
    circles = []
    colors = []
    
    # Get tournament data and process within session
    with session_scope() as session:
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
    
    # Add map background if requested
    if use_map_background:
        try:
            ctx.add_basemap(ax, crs='EPSG:4326', source=ctx.providers.CartoDB.Positron, zoom=10)
            log_info("Added map background", "heatmap")
            text_color = 'black'
        except Exception as e:
            log_error(f"Could not add map background: {e}", "heatmap") 
            text_color = 'white'
    else:
        text_color = 'white'
    
    ax.set_xlabel('Longitude', color=text_color, fontsize=12)
    ax.set_ylabel('Latitude', color=text_color, fontsize=12)
    ax.set_title('Tournament Attendance Density Map\n(Circle size = attendance)', 
                color=text_color, fontsize=16, fontweight='bold')
    
    # Legend
    legend_elements = [
        patches.Patch(color='#ff0000', label='Major (200+)', alpha=0.6),
        patches.Patch(color='#ff8800', label='Regional (100-200)', alpha=0.6),
        patches.Patch(color='#ffff00', label='Local (50-100)', alpha=0.6),
        patches.Patch(color='#00ffff', label='Weekly (<50)', alpha=0.6)
    ]
    
    if use_map_background:
        ax.legend(handles=legend_elements, loc='upper right', 
                 facecolor='white', edgecolor='black', labelcolor='black')
        ax.grid(True, alpha=0.2, color='gray', linestyle=':')
    else:
        ax.legend(handles=legend_elements, loc='upper right', 
                 facecolor='black', edgecolor='white', labelcolor='white')
        ax.grid(True, alpha=0.2, color='white', linestyle=':')
    ax.tick_params(colors=text_color)
    
    plt.tight_layout()
    if use_map_background:
        plt.savefig(output_file, dpi=150)
    else:
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