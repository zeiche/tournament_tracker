#!/usr/bin/env python3
"""
relationship_demo.py - Demonstrating the power of new object relationships
Shows what's now possible with the enhanced Python-centric models
"""

from database_utils import get_session
from tournament_models import Tournament, Organization, Player, TournamentPlacement
from collections import defaultdict
import json


def demonstrate_relationships():
    """Show the new relationship capabilities"""
    
    print("🚀 NEW RELATIONSHIP CAPABILITIES")
    print("=" * 60)
    
    with get_session() as session:
        
        # 1. TEMPORAL RELATIONSHIPS - Tournaments know about time
        print("\n1. TEMPORAL RELATIONSHIPS")
        print("-" * 40)
        
        recent_tournaments = session.query(Tournament).filter(
            Tournament.start_at.isnot(None)
        ).order_by(Tournament.start_at.desc()).limit(10).all()
        
        for t in recent_tournaments[:3]:
            print(f"\n{t.name}:")
            print(f"  📅 Year: {t.year}")
            print(f"  🗓️ Quarter: Q{t.quarter}")
            print(f"  🌸 Season: {t.season}")
            print(f"  📆 Month: {t.month_name}")
            print(f"  🕐 Time ago: {t.time_ago}")
            print(f"  ⏰ Is recent? {t.is_recent}")
            print(f"  🎉 Is weekend? {t.is_weekend}")
        
        # 2. GEOGRAPHIC RELATIONSHIPS - Objects know their location context
        print("\n\n2. GEOGRAPHIC RELATIONSHIPS")
        print("-" * 40)
        
        located_tournaments = session.query(Tournament).filter(
            Tournament.lat.isnot(None)
        ).limit(5).all()
        
        if len(located_tournaments) >= 2:
            t1 = located_tournaments[0]
            t2 = located_tournaments[1]
            
            print(f"\n{t1.name}:")
            print(f"  📍 Has location? {t1.has_location}")
            print(f"  🌐 Coordinates: {t1.coordinates}")
            print(f"  🏙️ City: {t1.city}")
            
            if t1.has_location and t2.has_location:
                distance = t1.distance_to(t2.lat, t2.lng)
                print(f"  📏 Distance to {t2.name}: {distance:.1f} km")
        
        # 3. ANALYTICAL RELATIONSHIPS - Built-in analytics
        print("\n\n3. ANALYTICAL RELATIONSHIPS")
        print("-" * 40)
        
        # Tournament analytics
        tournaments_with_attendance = session.query(Tournament).filter(
            Tournament.num_attendees > 0
        ).all()
        
        if tournaments_with_attendance:
            t = tournaments_with_attendance[0]
            print(f"\n{t.name}:")
            print(f"  👥 Attendance: {t.num_attendees}")
            print(f"  📈 Is major? {t.is_major}")
            print(f"  🎯 Competition level: {t.competition_level}")
            print(f"  ⚖️ Heatmap weight: {t.get_heatmap_weight()}")
        
        # 4. PLAYER RELATIONSHIPS - Players understand their performance context  
        print("\n\n4. PLAYER RELATIONSHIPS")
        print("-" * 40)
        
        top_players = session.query(Player).filter(
            Player.total_points > 0
        ).order_by(Player.total_points.desc()).limit(3).all()
        
        for player in top_players:
            print(f"\n{player.gamer_tag}:")
            print(f"  🏆 Total points: {player.total_points}")
            print(f"  📊 Average points: {player.avg_points:.1f}")
            print(f"  🥇 First places: {player.first_places}")
            print(f"  🥈 Second places: {player.second_places}")
            print(f"  🥉 Third places: {player.third_places}")
            print(f"  🏅 Win rate: {player.win_rate:.1%}")
            print(f"  📈 Points per event: {player.points_per_event:.1f}")
            
            # Show tournament locations this player has been to
            placements = session.query(TournamentPlacement).filter(
                TournamentPlacement.player_id == player.id
            ).join(Tournament).filter(
                Tournament.lat.isnot(None)
            ).limit(3).all()
            
            if placements:
                print(f"  📍 Recent locations:")
                for p in placements:
                    if p.tournament.has_location:
                        print(f"     • {p.tournament.city}: {p.tournament.venue_name}")
        
        # 5. ORGANIZATION RELATIONSHIPS - Organizations track their network
        print("\n\n5. ORGANIZATION RELATIONSHIPS")
        print("-" * 40)
        
        orgs = session.query(Organization).limit(3).all()
        
        for org in orgs:
            print(f"\n{org.display_name}:")
            
            # Count tournaments
            tournament_count = session.query(Tournament).filter(
                Tournament.primary_contact == org.display_name
            ).count()
            print(f"  🎮 Tournaments: {tournament_count}")
            
            # Get unique venues
            venues = session.query(Tournament.venue_name).filter(
                Tournament.primary_contact == org.display_name,
                Tournament.venue_name.isnot(None)
            ).distinct().all()
            print(f"  🏢 Unique venues: {len(venues)}")
            
            # Get date range
            date_range = session.query(
                Tournament.start_at
            ).filter(
                Tournament.primary_contact == org.display_name,
                Tournament.start_at.isnot(None)
            ).order_by(Tournament.start_at).all()
            
            if date_range:
                print(f"  📅 Active period: {date_range[0][0]} to {date_range[-1][0]}")
    
    print("\n" + "=" * 60)
    print("✨ KEY INSIGHTS:")
    print("""
The new OOP models enable:

1. TEMPORAL INTELLIGENCE
   - Tournaments understand their time context
   - Built-in seasonal, quarterly, monthly analysis
   - Relative time calculations (is_recent, time_ago)

2. GEOGRAPHIC AWARENESS
   - All location-based objects can calculate distances
   - Region filtering and geographic clustering
   - Coordinate-based relationships

3. ANALYTICAL METHODS
   - Competition level assessment
   - Automatic weight calculations for visualizations
   - Performance metrics built into objects

4. NETWORK RELATIONSHIPS
   - Players track their geographic footprint
   - Organizations understand their venue network
   - Cross-object relationship traversal

These weren't just difficult before - they were IMPOSSIBLE with
the old flat, C-style data model. Now every object is intelligent
and understands its context in the tournament ecosystem!
    """)


if __name__ == "__main__":
    demonstrate_relationships()