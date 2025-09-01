#!/usr/bin/env python3
"""
collect_geo_data.py - Collect and analyze geographic data from tournaments
"""

from database_utils import init_db, get_session
from tournament_models import Tournament
from collections import defaultdict
import json

def collect_tournament_geo_data():
    """Collect lat/lng from all tournaments in database"""
    # Initialize database
    init_db()
    
    geo_data = []
    missing_geo = []
    city_stats = defaultdict(int)
    
    with get_session() as session:
        # Get all tournaments
        tournaments = session.query(Tournament).all()
        
        print(f"Analyzing geographic data for {len(tournaments)} tournaments...\n")
        
        for t in tournaments:
            # Collect tournaments with geo data
            if t.lat and t.lng:
                try:
                    lat = float(t.lat)
                    lng = float(t.lng)
                    
                    geo_data.append({
                        'id': t.id,
                        'name': t.name,
                        'lat': lat,
                        'lng': lng,
                        'city': t.city,
                        'state': t.addr_state,
                        'venue': t.venue_name,
                        'address': t.venue_address,
                        'attendees': t.num_attendees or 0,
                        'date': t.start_at,
                        'slug': t.short_slug or t.slug
                    })
                    
                    # Track city statistics
                    if t.city:
                        city_stats[t.city] += 1
                        
                except (ValueError, TypeError):
                    # Invalid lat/lng values
                    missing_geo.append({
                        'id': t.id,
                        'name': t.name,
                        'city': t.city,
                        'invalid_coords': f"lat={t.lat}, lng={t.lng}"
                    })
            else:
                # No geo data
                missing_geo.append({
                    'id': t.id,
                    'name': t.name,
                    'city': t.city,
                    'venue': t.venue_name
                })
    
    # Print summary statistics
    print("=" * 60)
    print("GEOGRAPHIC DATA SUMMARY")
    print("=" * 60)
    print(f"Total tournaments: {len(tournaments)}")
    print(f"With geo coordinates: {len(geo_data)}")
    print(f"Missing/invalid coordinates: {len(missing_geo)}")
    print(f"Coverage: {len(geo_data)/len(tournaments)*100:.1f}%")
    print()
    
    # City distribution
    print("TOP CITIES BY TOURNAMENT COUNT:")
    print("-" * 40)
    for city, count in sorted(city_stats.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"{city:30} {count:4} tournaments")
    print()
    
    # Geographic bounds
    if geo_data:
        lats = [g['lat'] for g in geo_data]
        lngs = [g['lng'] for g in geo_data]
        
        print("GEOGRAPHIC BOUNDS:")
        print("-" * 40)
        print(f"Northernmost: {max(lats):.6f}")
        print(f"Southernmost: {min(lats):.6f}")
        print(f"Easternmost:  {max(lngs):.6f}")
        print(f"Westernmost:  {min(lngs):.6f}")
        print(f"Center point: {sum(lats)/len(lats):.6f}, {sum(lngs)/len(lngs):.6f}")
        print()
        
        # Save to JSON for potential mapping
        with open('tournament_geo_data.json', 'w') as f:
            json.dump({
                'tournaments': geo_data,
                'summary': {
                    'total': len(tournaments),
                    'with_coordinates': len(geo_data),
                    'missing_coordinates': len(missing_geo),
                    'bounds': {
                        'north': max(lats),
                        'south': min(lats),
                        'east': max(lngs),
                        'west': min(lngs),
                        'center': {
                            'lat': sum(lats)/len(lats),
                            'lng': sum(lngs)/len(lngs)
                        }
                    }
                }
            }, f, indent=2)
        print("Saved geo data to tournament_geo_data.json")
    
    # Show sample of tournaments with coordinates
    print("\nSAMPLE TOURNAMENTS WITH COORDINATES:")
    print("-" * 60)
    for t in geo_data[:5]:
        print(f"{t['name'][:40]:40} ({t['lat']:.4f}, {t['lng']:.4f})")
        print(f"  {t['city']}, {t['state']} - {t['attendees']} attendees")
    
    if len(missing_geo) > 0:
        print("\nSAMPLE TOURNAMENTS MISSING COORDINATES:")
        print("-" * 60)
        for t in missing_geo[:5]:
            print(f"{t['name'][:50]:50} - {t.get('city', 'Unknown city')}")
    
    return geo_data, missing_geo

def create_geojson(geo_data):
    """Create GeoJSON format for mapping tools"""
    features = []
    
    for t in geo_data:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [t['lng'], t['lat']]  # GeoJSON uses [lng, lat]
            },
            "properties": {
                "name": t['name'],
                "city": t['city'],
                "attendees": t['attendees'],
                "venue": t['venue'],
                "id": t['id']
            }
        }
        features.append(feature)
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open('tournament_map.geojson', 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"\nCreated GeoJSON with {len(features)} tournament locations")
    print("Saved to tournament_map.geojson (can be viewed at geojson.io)")

if __name__ == "__main__":
    geo_data, missing = collect_tournament_geo_data()
    
    if geo_data:
        create_geojson(geo_data)
        print(f"\n✅ Successfully collected {len(geo_data)} tournament locations")
    else:
        print("\n⚠️ No geographic data found in tournaments")