#!/usr/bin/env python3
"""
analytics_showcase.py - Demonstrating the power of new object relationships
Shows how the enhanced OOP models enable entirely new types of analysis and visualizations
"""

from database_utils import get_session
from tournament_models import Tournament, Organization, Player, TournamentPlacement
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
from collections import defaultdict


class RelationshipAnalytics:
    """Showcase the new analytical capabilities from enhanced models"""
    
    def __init__(self):
        pass
    
    def player_geography_heatmap(self) -> Dict:
        """
        Heat map of where top players compete most frequently
        This wasn't possible before - now Player objects know their tournament locations
        """
        heatmap_data = defaultdict(lambda: {'players': set(), 'events': 0, 'avg_placement': 0})
        
        # Get top players
        with get_session() as session:
            top_players = session.query(Player).order_by(
                Player.total_points.desc()
            ).limit(50).all()
            
            for player in top_players:
                # Each player now has methods to get their tournament locations
                for placement in player.get_placements():
                    tournament = placement.tournament
                    if tournament.has_location:
                        lat, lng = tournament.coordinates
                        # Round to create grid cells
                        grid_key = (round(lat, 2), round(lng, 2))
                        heatmap_data[grid_key]['players'].add(player.gamer_tag)
                        heatmap_data[grid_key]['events'] += 1
                        heatmap_data[grid_key]['avg_placement'] += placement.placement
        
        # Convert to list for visualization
        return {
            'type': 'player_geography',
            'description': 'Where top players compete',
            'data': [
                {
                    'lat': k[0],
                    'lng': k[1], 
                    'player_count': len(v['players']),
                    'total_events': v['events'],
                    'avg_placement': v['avg_placement'] / v['events'] if v['events'] > 0 else 0,
                    'top_players': list(v['players'])[:5]
                }
                for k, v in heatmap_data.items()
            ]
        }
    
    def organization_growth_heatmap(self) -> Dict:
        """
        Heat map showing organizational growth patterns over time and space
        Uses the new temporal methods on Tournament objects
        """
        growth_data = defaultdict(lambda: defaultdict(int))
        
        orgs = self.session.query(Organization).all()
        
        for org in orgs:
            # Get tournaments for this org using the new relationship methods
            tournaments = org.get_tournaments(self.session)
            
            for tournament in tournaments:
                if tournament.has_location and tournament.date:
                    # Use the new quarter/year methods
                    time_key = f"{tournament.year}-Q{tournament.quarter}"
                    lat, lng = tournament.coordinates
                    grid_key = (round(lat, 1), round(lng, 1))
                    
                    growth_data[time_key][grid_key] += tournament.num_attendees or 0
        
        return {
            'type': 'organization_growth',
            'description': 'Organizational growth patterns over time',
            'data': {
                time: [
                    {
                        'lat': loc[0],
                        'lng': loc[1],
                        'attendance': attendance,
                        'period': time
                    }
                    for loc, attendance in locations.items()
                ]
                for time, locations in growth_data.items()
            }
        }
    
    def competitive_cluster_analysis(self) -> Dict:
        """
        Identify competitive clusters - areas with high-skill player concentration
        Uses Player ranking methods and Tournament location methods together
        """
        cluster_data = defaultdict(lambda: {
            'total_skill_points': 0,
            'player_count': 0,
            'tournaments': set(),
            'avg_attendance': 0,
            'top_player': None,
            'max_points': 0
        })
        
        # Get all placements with location data
        placements = self.session.query(TournamentPlacement).join(
            Tournament
        ).filter(
            Tournament.lat.isnot(None)
        ).all()
        
        for placement in placements:
            if placement.player and placement.tournament.has_location:
                lat, lng = placement.tournament.coordinates
                grid_key = (round(lat, 2), round(lng, 2))
                
                # Use the new points calculation methods
                points = placement.get_points()
                cluster_data[grid_key]['total_skill_points'] += points
                cluster_data[grid_key]['player_count'] += 1
                cluster_data[grid_key]['tournaments'].add(placement.tournament.name)
                
                # Track top player in each cluster
                if points > cluster_data[grid_key]['max_points']:
                    cluster_data[grid_key]['max_points'] = points
                    cluster_data[grid_key]['top_player'] = placement.player.gamer_tag
        
        return {
            'type': 'competitive_clusters',
            'description': 'High-skill player concentration areas',
            'data': [
                {
                    'lat': k[0],
                    'lng': k[1],
                    'skill_density': v['total_skill_points'] / max(v['player_count'], 1),
                    'total_points': v['total_skill_points'],
                    'unique_players': v['player_count'],
                    'tournament_count': len(v['tournaments']),
                    'top_player': v['top_player']
                }
                for k, v in cluster_data.items()
                if v['player_count'] >= 3  # Minimum cluster size
            ]
        }
    
    def venue_quality_heatmap(self) -> Dict:
        """
        Heat map of venue quality based on repeat tournaments and attendance growth
        """
        venue_data = defaultdict(lambda: {
            'tournaments': [],
            'total_attendance': 0,
            'growth_rate': 0,
            'repeat_rate': 0
        })
        
        tournaments = self.session.query(Tournament).filter(
            Tournament.venue_name.isnot(None),
            Tournament.lat.isnot(None)
        ).all()
        
        # Group by venue
        for t in tournaments:
            if t.has_location:
                venue_key = (t.venue_name, t.venue_address)
                venue_data[venue_key]['tournaments'].append({
                    'date': t.date,
                    'attendance': t.num_attendees or 0,
                    'lat': t.lat,
                    'lng': t.lng
                })
                venue_data[venue_key]['total_attendance'] += t.num_attendees or 0
        
        # Calculate venue metrics
        quality_venues = []
        for venue, data in venue_data.items():
            if len(data['tournaments']) >= 2:  # Repeat venues only
                # Sort by date
                sorted_events = sorted(data['tournaments'], key=lambda x: x['date'] or '')
                
                # Calculate growth
                if sorted_events[0]['attendance'] > 0:
                    growth = (sorted_events[-1]['attendance'] - sorted_events[0]['attendance']) / sorted_events[0]['attendance']
                else:
                    growth = 0
                
                quality_venues.append({
                    'venue': venue[0],
                    'address': venue[1],
                    'lat': sorted_events[0]['lat'],
                    'lng': sorted_events[0]['lng'],
                    'event_count': len(data['tournaments']),
                    'total_attendance': data['total_attendance'],
                    'avg_attendance': data['total_attendance'] / len(data['tournaments']),
                    'growth_rate': growth,
                    'quality_score': len(data['tournaments']) * (1 + growth) * (data['total_attendance'] / 100)
                })
        
        return {
            'type': 'venue_quality',
            'description': 'Venue quality based on usage and growth',
            'data': sorted(quality_venues, key=lambda x: x['quality_score'], reverse=True)
        }
    
    def temporal_flow_map(self) -> Dict:
        """
        Show how tournament activity flows across the region by time of year
        This uses the new seasonal analysis methods
        """
        seasonal_data = defaultdict(lambda: defaultdict(list))
        
        tournaments = self.session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.start_at.isnot(None)
        ).all()
        
        for t in tournaments:
            # Use the new season property
            season = t.season
            if season and t.has_location:
                lat, lng = t.coordinates
                grid_key = (round(lat, 1), round(lng, 1))
                seasonal_data[season][grid_key].append({
                    'attendance': t.num_attendees or 0,
                    'month': t.month,
                    'org': t.primary_contact
                })
        
        # Aggregate seasonal patterns
        seasonal_patterns = {}
        for season, locations in seasonal_data.items():
            seasonal_patterns[season] = [
                {
                    'lat': loc[0],
                    'lng': loc[1],
                    'total_attendance': sum(e['attendance'] for e in events),
                    'event_count': len(events),
                    'peak_month': max(set(e['month'] for e in events if e['month']), 
                                     key=lambda x: sum(1 for e in events if e['month'] == x))
                        if any(e['month'] for e in events) else None
                }
                for loc, events in locations.items()
            ]
        
        return {
            'type': 'temporal_flow',
            'description': 'Tournament activity flow by season',
            'data': seasonal_patterns
        }
    
    def network_strength_map(self) -> Dict:
        """
        Map showing the strength of connections between venues based on 
        shared players and organizations
        """
        connections = defaultdict(lambda: defaultdict(int))
        
        # Find players who compete at multiple venues
        players = self.session.query(Player).all()
        
        for player in players:
            venues = set()
            for placement in player.get_placements():
                if placement.tournament.venue_name and placement.tournament.has_location:
                    venues.add((
                        placement.tournament.venue_name,
                        placement.tournament.lat,
                        placement.tournament.lng
                    ))
            
            # Create connections between all venue pairs this player has visited
            venue_list = list(venues)
            for i in range(len(venue_list)):
                for j in range(i + 1, len(venue_list)):
                    v1, v2 = venue_list[i], venue_list[j]
                    connection_key = tuple(sorted([v1[0], v2[0]]))
                    connections[connection_key]['shared_players'] += 1
                    connections[connection_key]['coords'] = [
                        (v1[1], v1[2]), (v2[1], v2[2])
                    ]
        
        # Convert to visualization format
        network_data = []
        for (venue1, venue2), data in connections.items():
            if data['shared_players'] >= 5:  # Minimum threshold
                network_data.append({
                    'venue1': venue1,
                    'venue2': venue2,
                    'strength': data['shared_players'],
                    'coords': data['coords']
                })
        
        return {
            'type': 'network_strength',
            'description': 'Venue connections based on shared players',
            'data': sorted(network_data, key=lambda x: x['strength'], reverse=True)
        }
    
    def skill_progression_geography(self) -> Dict:
        """
        Show how player skill levels progress geographically over time
        Track where players improve most rapidly
        """
        progression_data = defaultdict(lambda: {
            'improvement_scores': [],
            'player_journeys': []
        })
        
        # Track each player's journey
        players = self.session.query(Player).filter(
            Player.total_points > 0
        ).all()
        
        for player in players:
            placements = player.get_placements_by_date()
            
            if len(placements) >= 3:  # Need multiple events to track progression
                for i in range(1, len(placements)):
                    prev = placements[i-1]
                    curr = placements[i]
                    
                    if curr.tournament.has_location:
                        # Calculate improvement
                        improvement = (prev.placement - curr.placement) / prev.placement if prev.placement > 0 else 0
                        
                        lat, lng = curr.tournament.coordinates
                        grid_key = (round(lat, 2), round(lng, 2))
                        
                        progression_data[grid_key]['improvement_scores'].append(improvement)
                        progression_data[grid_key]['player_journeys'].append({
                            'player': player.gamer_tag,
                            'from_placement': prev.placement,
                            'to_placement': curr.placement,
                            'improvement': improvement
                        })
        
        # Aggregate data
        return {
            'type': 'skill_progression_geography',
            'description': 'Where players improve most rapidly',
            'data': [
                {
                    'lat': k[0],
                    'lng': k[1],
                    'avg_improvement': sum(v['improvement_scores']) / len(v['improvement_scores']),
                    'player_count': len(set(j['player'] for j in v['player_journeys'])),
                    'total_progressions': len(v['player_journeys']),
                    'top_improvements': sorted(v['player_journeys'], 
                                              key=lambda x: x['improvement'], 
                                              reverse=True)[:3]
                }
                for k, v in progression_data.items()
                if len(v['improvement_scores']) >= 3
            ]
        }


def demonstrate_new_capabilities():
    """Show what's now possible with the enhanced models"""
    
    print("🚀 Demonstrating New Analytical Capabilities")
    print("=" * 60)
    
    analytics = RelationshipAnalytics()
    
    # 1. Player Geography Heat Map
    print("\n1. Player Geography Heat Map")
    print("-" * 40)
    player_geo = analytics.player_geography_heatmap()
    print(f"Found {len(player_geo['data'])} geographic clusters")
    if player_geo['data']:
        top_cluster = max(player_geo['data'], key=lambda x: x['player_count'])
        print(f"Hottest spot: ({top_cluster['lat']}, {top_cluster['lng']}) with {top_cluster['player_count']} top players")
    
    # 2. Organization Growth Patterns
    print("\n2. Organization Growth Heat Map")
    print("-" * 40)
    org_growth = analytics.organization_growth_heatmap()
    quarters = list(org_growth['data'].keys())
    print(f"Tracking growth across {len(quarters)} time periods")
    if quarters:
        latest = sorted(quarters)[-1]
        print(f"Latest period {latest}: {len(org_growth['data'][latest])} active locations")
    
    # 3. Competitive Clusters
    print("\n3. Competitive Cluster Analysis")
    print("-" * 40)
    clusters = analytics.competitive_cluster_analysis()
    print(f"Identified {len(clusters['data'])} competitive clusters")
    if clusters['data']:
        top_skill = max(clusters['data'], key=lambda x: x['skill_density'])
        print(f"Highest skill density: {top_skill['skill_density']:.1f} pts/player at ({top_skill['lat']}, {top_skill['lng']})")
        print(f"  Top player there: {top_skill['top_player']}")
    
    # 4. Venue Quality
    print("\n4. Venue Quality Heat Map")
    print("-" * 40)
    venues = analytics.venue_quality_heatmap()
    print(f"Analyzed {len(venues['data'])} repeat venues")
    if venues['data']:
        best_venue = venues['data'][0]  # Already sorted by quality
        print(f"Top venue: {best_venue['venue']}")
        print(f"  Events: {best_venue['event_count']}, Growth: {best_venue['growth_rate']:.1%}")
    
    # 5. Temporal Flow
    print("\n5. Temporal Flow Map")
    print("-" * 40)
    temporal = analytics.temporal_flow_map()
    for season, data in temporal['data'].items():
        total_attendance = sum(d['total_attendance'] for d in data)
        print(f"{season}: {len(data)} locations, {total_attendance:,} total attendance")
    
    # 6. Network Strength
    print("\n6. Venue Network Strength Map")
    print("-" * 40)
    network = analytics.network_strength_map()
    print(f"Found {len(network['data'])} strong venue connections")
    if network['data']:
        strongest = network['data'][0]
        print(f"Strongest connection: {strongest['venue1']} ↔ {strongest['venue2']}")
        print(f"  Shared players: {strongest['strength']}")
    
    # 7. Skill Progression Geography
    print("\n7. Skill Progression Geography")
    print("-" * 40)
    progression = analytics.skill_progression_geography()
    print(f"Found {len(progression['data'])} improvement zones")
    if progression['data']:
        best_zone = max(progression['data'], key=lambda x: x['avg_improvement'])
        print(f"Best improvement zone: ({best_zone['lat']}, {best_zone['lng']})")
        print(f"  Average improvement: {best_zone['avg_improvement']:.1%}")
    
    print("\n" + "=" * 60)
    print("These heat maps were impossible with the old C-style flat data!")
    print("The new OOP models expose rich relationships between:")
    print("  • Players ↔ Locations ↔ Time")
    print("  • Organizations ↔ Venues ↔ Growth")  
    print("  • Skills ↔ Geography ↔ Competition")
    print("  • Networks ↔ Communities ↔ Progression")


if __name__ == "__main__":
    demonstrate_new_capabilities()