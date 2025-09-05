#!/usr/bin/env python3
"""
heatmap_advanced.py - Advanced heat map generation using object relationships
Generates heat maps that were impossible with the old flat data model
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from database_utils import get_session
from tournament_models import Tournament, Organization, Player, TournamentPlacement
from log_utils import log_info, log_error


class AdvancedHeatmapGenerator:
    """Generate advanced heat maps using the rich object relationships"""
    
    def __init__(self):
        self.session = get_session()
    
    def generate_player_skill_heatmap(self, output_file: str = 'heatmap_player_skill.html'):
        """
        Generate an interactive heat map showing skill concentration by geography
        Red = High skill concentration, Blue = Lower skill
        """
        import folium
        from folium.plugins import HeatMap
        
        log_info("Generating player skill concentration heat map", "heatmap")
        
        # Get skill data points
        skill_points = []
        
        placements = self.session.query(TournamentPlacement).join(
            Tournament
        ).filter(
            Tournament.lat.isnot(None),
            Tournament.lng.isnot(None)
        ).all()
        
        for p in placements:
            if p.tournament.has_location:
                lat, lng = p.tournament.coordinates
                # Weight by inverse placement (1st = 8 points, 8th = 1 point)
                weight = 9 - p.placement
                skill_points.append([lat, lng, weight])
        
        if not skill_points:
            log_error("No skill data points found", "heatmap")
            return False
        
        # Create map centered on SoCal
        m = folium.Map(location=[33.7, -117.8], zoom_start=9)
        
        # Add heat map layer
        HeatMap(skill_points, 
                name='Player Skill Concentration',
                min_opacity=0.4,
                radius=25,
                blur=20,
                gradient={
                    0.0: 'blue',
                    0.25: 'cyan',
                    0.5: 'yellow', 
                    0.75: 'orange',
                    1.0: 'red'
                }).add_to(m)
        
        # Add venue markers for context
        venues = {}
        for point in skill_points:
            lat, lng, weight = point
            key = (round(lat, 3), round(lng, 3))
            if key not in venues:
                venues[key] = {'total_weight': 0, 'count': 0}
            venues[key]['total_weight'] += weight
            venues[key]['count'] += 1
        
        # Add markers for top skill concentrations
        top_venues = sorted(venues.items(), key=lambda x: x[1]['total_weight'], reverse=True)[:10]
        for (lat, lng), data in top_venues:
            folium.CircleMarker(
                [lat, lng],
                radius=5,
                popup=f"Skill Score: {data['total_weight']}<br>Events: {data['count']}",
                color='red',
                fill=True,
                fillColor='red'
            ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save
        m.save(output_file)
        log_info(f"Player skill heat map saved to {output_file}", "heatmap")
        return True
    
    def generate_growth_velocity_heatmap(self, output_file: str = 'heatmap_growth_velocity.html'):
        """
        Generate heat map showing where the scene is growing fastest
        Uses temporal analysis from Tournament objects
        """
        import folium
        from folium.plugins import HeatMap
        from datetime import datetime, timedelta
        
        log_info("Generating growth velocity heat map", "heatmap")
        
        # Compare last 6 months to previous 6 months
        now = datetime.now()
        six_months_ago = now - timedelta(days=180)
        twelve_months_ago = now - timedelta(days=360)
        
        # Get recent period data
        recent_tournaments = self.session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.start_at >= six_months_ago.strftime('%Y-%m-%d')
        ).all()
        
        # Get previous period data
        previous_tournaments = self.session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.start_at >= twelve_months_ago.strftime('%Y-%m-%d'),
            Tournament.start_at < six_months_ago.strftime('%Y-%m-%d')
        ).all()
        
        # Calculate growth by location
        from collections import defaultdict
        recent_activity = defaultdict(int)
        previous_activity = defaultdict(int)
        
        for t in recent_tournaments:
            if t.has_location:
                lat, lng = t.coordinates
                grid_key = (round(lat, 2), round(lng, 2))
                recent_activity[grid_key] += t.num_attendees or 0
        
        for t in previous_tournaments:
            if t.has_location:
                lat, lng = t.coordinates
                grid_key = (round(lat, 2), round(lng, 2))
                previous_activity[grid_key] += t.num_attendees or 0
        
        # Calculate growth rates
        growth_points = []
        for location in recent_activity:
            recent = recent_activity[location]
            previous = previous_activity.get(location, 0)
            
            if previous > 0:
                growth_rate = (recent - previous) / previous
            else:
                growth_rate = 1.0 if recent > 0 else 0
            
            if growth_rate > 0:
                lat, lng = location
                # Weight by growth rate and recent activity
                weight = growth_rate * (recent / 100)
                growth_points.append([lat, lng, weight])
        
        if not growth_points:
            log_error("No growth data points found", "heatmap")
            return False
        
        # Create map
        m = folium.Map(location=[33.7, -117.8], zoom_start=9)
        
        # Add growth heat map
        HeatMap(growth_points,
                name='Growth Velocity',
                min_opacity=0.4,
                radius=30,
                blur=25,
                gradient={
                    0.0: 'purple',
                    0.25: 'blue',
                    0.5: 'green',
                    0.75: 'yellow',
                    1.0: 'red'
                }).add_to(m)
        
        # Add markers for highest growth areas
        top_growth = sorted(growth_points, key=lambda x: x[2], reverse=True)[:5]
        for lat, lng, weight in top_growth:
            folium.Marker(
                [lat, lng],
                popup=f"Growth Score: {weight:.2f}",
                icon=folium.Icon(color='green', icon='arrow-up')
            ).add_to(m)
        
        # Save
        m.save(output_file)
        log_info(f"Growth velocity heat map saved to {output_file}", "heatmap")
        return True
    
    def generate_player_journey_heatmap(self, player_tag: str, output_file: str = 'heatmap_player_journey.html'):
        """
        Generate a heat map showing a specific player's competitive journey
        Shows where they compete and how their performance changes geographically
        """
        import folium
        from folium.plugins import AntPath
        
        log_info(f"Generating journey heat map for {player_tag}", "heatmap")
        
        # Find the player
        player = self.session.query(Player).filter(
            Player.gamer_tag.ilike(f'%{player_tag}%')
        ).first()
        
        if not player:
            log_error(f"Player {player_tag} not found", "heatmap")
            return False
        
        # Get their placements in chronological order
        placements = player.get_placements_by_date()
        
        # Build journey data
        journey_points = []
        for p in placements:
            if p.tournament.has_location:
                lat, lng = p.tournament.coordinates
                journey_points.append({
                    'location': [lat, lng],
                    'date': p.tournament.start_at,
                    'tournament': p.tournament.name,
                    'placement': p.placement,
                    'event': p.event_name
                })
        
        if len(journey_points) < 2:
            log_error(f"Not enough location data for {player_tag}", "heatmap")
            return False
        
        # Create map centered on their activity
        center_lat = sum(p['location'][0] for p in journey_points) / len(journey_points)
        center_lng = sum(p['location'][1] for p in journey_points) / len(journey_points)
        m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
        
        # Add journey path (animated)
        path_coords = [p['location'] for p in journey_points]
        AntPath(path_coords, 
                color='blue',
                weight=3,
                opacity=0.8,
                delay=800).add_to(m)
        
        # Add markers for each tournament
        for i, point in enumerate(journey_points):
            # Color based on placement
            if point['placement'] == 1:
                color = 'gold'
                icon = 'trophy'
            elif point['placement'] <= 3:
                color = 'orange'
                icon = 'star'
            elif point['placement'] <= 8:
                color = 'blue'
                icon = 'circle'
            else:
                color = 'gray'
                icon = 'circle'
            
            folium.CircleMarker(
                point['location'],
                radius=8 if point['placement'] <= 3 else 5,
                popup=f"""
                <b>{point['tournament']}</b><br>
                Date: {point['date']}<br>
                Event: {point['event']}<br>
                Placement: {point['placement']}
                """,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
            
            # Add sequence numbers
            if i == 0:
                folium.Marker(
                    point['location'],
                    icon=folium.DivIcon(html=f'<div style="color: green; font-weight: bold;">START</div>')
                ).add_to(m)
            elif i == len(journey_points) - 1:
                folium.Marker(
                    point['location'],
                    icon=folium.DivIcon(html=f'<div style="color: red; font-weight: bold;">LATEST</div>')
                ).add_to(m)
        
        # Add title
        title_html = f'''
        <h3 style="position: fixed; top: 10px; left: 50px; z-index: 1000; 
                   background: white; padding: 10px; border-radius: 5px;">
            {player.gamer_tag}'s Tournament Journey ({len(journey_points)} events)
        </h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save
        m.save(output_file)
        log_info(f"Player journey heat map saved to {output_file}", "heatmap")
        return True
    
    def generate_community_network_heatmap(self, output_file: str = 'heatmap_community_network.html'):
        """
        Generate heat map showing community connections between venues
        Lines show player flow, heat shows activity concentration
        """
        import folium
        from folium.plugins import HeatMap
        from collections import defaultdict
        
        log_info("Generating community network heat map", "heatmap")
        
        # Build venue connection network
        venue_connections = defaultdict(lambda: defaultdict(set))
        venue_locations = {}
        
        players = self.session.query(Player).all()
        
        for player in players:
            player_venues = []
            
            for placement in player.get_placements():
                t = placement.tournament
                if t.venue_name and t.has_location:
                    venue_key = t.venue_name
                    venue_locations[venue_key] = t.coordinates
                    player_venues.append(venue_key)
            
            # Connect all venues this player has visited
            for i in range(len(player_venues)):
                for j in range(i + 1, len(player_venues)):
                    v1, v2 = player_venues[i], player_venues[j]
                    venue_connections[v1][v2].add(player.gamer_tag)
                    venue_connections[v2][v1].add(player.gamer_tag)
        
        if not venue_locations:
            log_error("No venue location data found", "heatmap")
            return False
        
        # Create map
        m = folium.Map(location=[33.7, -117.8], zoom_start=9)
        
        # Add heat map of venue activity
        heat_points = []
        for venue, coords in venue_locations.items():
            # Weight by number of connections
            weight = len(venue_connections[venue])
            if weight > 0:
                heat_points.append([coords[0], coords[1], weight])
        
        HeatMap(heat_points,
                name='Venue Activity',
                min_opacity=0.3,
                radius=20).add_to(m)
        
        # Add connection lines for strong connections (5+ shared players)
        drawn_connections = set()
        for v1, connections in venue_connections.items():
            if v1 in venue_locations:
                for v2, players in connections.items():
                    if v2 in venue_locations and len(players) >= 5:
                        # Avoid duplicate lines
                        connection_key = tuple(sorted([v1, v2]))
                        if connection_key not in drawn_connections:
                            drawn_connections.add(connection_key)
                            
                            # Draw line with width based on connection strength
                            folium.PolyLine(
                                [venue_locations[v1], venue_locations[v2]],
                                color='blue',
                                weight=min(len(players) / 5, 5),
                                opacity=0.3,
                                popup=f"{v1} ↔ {v2}<br>{len(players)} shared players"
                            ).add_to(m)
        
        # Add venue markers
        for venue, coords in venue_locations.items():
            connection_count = len(venue_connections[venue])
            if connection_count >= 3:  # Only show connected venues
                folium.CircleMarker(
                    coords,
                    radius=min(connection_count, 15),
                    popup=f"<b>{venue}</b><br>Connections: {connection_count}",
                    color='red',
                    fill=True,
                    fillColor='orange'
                ).add_to(m)
        
        # Save
        m.save(output_file)
        log_info(f"Community network heat map saved to {output_file}", "heatmap")
        return True


def generate_all_advanced_heatmaps():
    """Generate all advanced heat map types"""
    generator = AdvancedHeatmapGenerator()
    
    print("🗺️ Generating Advanced Heat Maps")
    print("=" * 60)
    
    # 1. Player Skill Concentration
    if generator.generate_player_skill_heatmap():
        print("✅ Generated: heatmap_player_skill.html")
    
    # 2. Growth Velocity
    if generator.generate_growth_velocity_heatmap():
        print("✅ Generated: heatmap_growth_velocity.html")
    
    # 3. Player Journey (example with a top player)
    top_player = generator.session.query(Player).order_by(
        Player.total_points.desc()
    ).first()
    
    if top_player:
        filename = f'heatmap_journey_{top_player.gamer_tag.replace(" ", "_")}.html'
        if generator.generate_player_journey_heatmap(top_player.gamer_tag, filename):
            print(f"✅ Generated: {filename}")
    
    # 4. Community Network
    if generator.generate_community_network_heatmap():
        print("✅ Generated: heatmap_community_network.html")
    
    print("\nThese advanced heat maps showcase:")
    print("  • Player skill geographic concentration")
    print("  • Growth velocity and trending areas")
    print("  • Individual player competitive journeys")
    print("  • Community network connections")
    print("\nAll powered by the new OOP model relationships!")


if __name__ == "__main__":
    generate_all_advanced_heatmaps()