#!/usr/bin/env python3
"""
Demonstrate the TRUE power of polymorphic tabulation
"""
from polymorphic_tabulator import tabulate, PolymorphicTabulator
from database import get_session
from tournament_models import Player, Tournament, Organization
from datetime import datetime, timedelta
import random

print("=" * 80)
print("POLYMORPHIC TABULATOR - RANKING ANYTHING WITHOUT KNOWING WHAT IT IS")
print("=" * 80)

# DEMO 1: Completely mixed types in one ranking
print("\n🎯 DEMO 1: Ranking COMPLETELY DIFFERENT TYPES together:")
print("-" * 60)

class VideoGame:
    def __init__(self, title, score):
        self.title = title
        self.metacritic_score = score
        self.score = score  # The tabulator will find this!

mixed_bag = [
    # Numbers
    42,
    99.9,
    -17,
    
    # Strings  
    "Zebra",
    "Apple",
    
    # Dicts with scores
    {"name": "Dict Player", "score": 85},
    {"item": "Another Dict", "points": 73},
    
    # Custom objects
    VideoGame("Zelda", 97),
    VideoGame("Mario", 88),
    
    # Lists (will use length)
    [1, 2, 3, 4, 5],  # length 5
    ["a", "b"],  # length 2
    
    # Dates
    datetime.now(),
    datetime(2020, 1, 1),
    
    # Booleans and None
    True,  # scores as 1
    False,  # scores as 0
    None,  # scores as 0
]

print("Throwing 17 completely different objects at the tabulator...")
print("Watch it figure out how to rank them ALL:\n")

for rank, item, score in tabulate(mixed_bag)[:10]:
    item_type = type(item).__name__
    item_str = str(item)[:30] if item is not None else "None"
    print(f"  Rank {rank:2}: {item_type:12} | {item_str:30} | Score: {score}")

# DEMO 2: Natural language understanding
print("\n\n🧠 DEMO 2: Natural Language Understanding")
print("-" * 60)

with get_session() as session:
    tournaments = session.query(Tournament).limit(15).all()
    
    if tournaments:
        hints = [
            "most recent",
            "largest attendance", 
            "biggest",  # Should understand this means size
            "alphabetical",
        ]
        
        for hint in hints:
            print(f"\n  Hint: '{hint}'")
            for rank, t, score in tabulate(tournaments, hint)[:3]:
                # Format score based on hint
                if "recent" in hint:
                    score_str = datetime.fromtimestamp(score).strftime("%Y-%m-%d") if score else "N/A"
                elif "alpha" in hint:
                    score_str = f"Name: {score[:20]}"
                else:
                    score_str = f"Score: {score}"
                print(f"    {rank}. {t.name[:35]:35} | {score_str}")

# DEMO 3: Multi-criteria sorting (like SQL ORDER BY)
print("\n\n🎰 DEMO 3: Multi-Criteria Sorting (ORDER BY multiple columns)")
print("-" * 60)

# Create test data with ties
teams = [
    {"team": "Eagles", "wins": 10, "points": 250, "losses": 2},
    {"team": "Bears", "wins": 10, "points": 200, "losses": 2},  # Tie on wins
    {"team": "Lions", "wins": 10, "points": 200, "losses": 3},  # Tie on wins AND points
    {"team": "Packers", "wins": 8, "points": 300, "losses": 4},
    {"team": "Vikings", "wins": 8, "points": 180, "losses": 4},
]

print("\nRanking by: 1) wins, 2) points, 3) losses")
print("(Notice how ties are broken by subsequent criteria)\n")

for rank, team, scores in PolymorphicTabulator.multi_tabulate(
    teams, ["wins", "points", "losses"]
):
    print(f"  Rank {rank}: {team['team']:10} | Wins: {scores[0]}, Points: {scores[1]}, Losses: {scores[2]}")

# DEMO 4: Introspection magic
print("\n\n✨ DEMO 4: Automatic Introspection (no hints at all!)")
print("-" * 60)

class MysteryObject:
    """The tabulator has NEVER seen this class before!"""
    def __init__(self, id, desc):
        self.id = id
        self.description = desc
        self.secret_score = random.randint(50, 150)  # Hidden attribute!
        self.total_points = random.randint(100, 500)  # It will find this!
        self.rank = random.randint(1, 10)  # Another scoring attribute
    
    def __repr__(self):
        return f"Mystery#{self.id}"

mysteries = [MysteryObject(i, f"Object {i}") for i in range(1, 6)]

print("Created 5 MysteryObjects with random scoring attributes...")
print("The tabulator has NEVER seen this class before!")
print("\nWithout ANY hints, it finds scoreable attributes:\n")

for rank, obj, score in tabulate(mysteries):
    print(f"  Rank {rank}: {obj} | "
          f"Auto-detected score: {score} "
          f"(actual total_points: {obj.total_points})")

# DEMO 5: Working with database models
print("\n\n🏆 DEMO 5: Smart Database Model Handling")
print("-" * 60)

with get_session() as session:
    players = session.query(Player).limit(8).all()
    
    if players:
        # The tabulator understands these hints for Player objects:
        smart_hints = [
            "most wins",  # Finds first_places or calculates from placements
            "highest points",  # Finds total_points or calculates
            "most events",  # Counts placements
        ]
        
        for hint in smart_hints:
            print(f"\n  Ranking players by: '{hint}'")
            for rank, p, score in tabulate(players, hint)[:3]:
                print(f"    Rank {rank}: {p.gamer_tag:15} | {hint}: {score}")

# DEMO 6: The ultimate test - EVERYTHING AT ONCE
print("\n\n🚀 DEMO 6: THE ULTIMATE TEST - Everything at Once!")
print("-" * 60)

with get_session() as session:
    # Get a bit of everything
    everything = []
    
    # Add some database objects
    everything.extend(session.query(Player).limit(2).all())
    everything.extend(session.query(Tournament).limit(2).all())
    
    # Add raw data
    everything.extend([100, 50, "String", {"score": 75}])
    
    # Add custom objects
    everything.append(VideoGame("Tetris", 89))
    everything.append(MysteryObject(99, "Special"))
    
    # Add weird stuff
    everything.extend([
        datetime.now(),
        [1, 2, 3, 4],  # List
        None,
        True,
        3.14159,
    ])
    
    print(f"Ranking {len(everything)} objects of COMPLETELY DIFFERENT TYPES:")
    print("Players, Tournaments, numbers, strings, dicts, custom objects, dates...\n")
    
    for rank, item, score in tabulate(everything):
        # Identify what type it is
        if hasattr(item, '__tablename__'):
            type_name = item.__tablename__.rstrip('s').title()
            item_str = getattr(item, 'gamer_tag', getattr(item, 'name', str(item)))[:25]
        else:
            type_name = type(item).__name__
            item_str = str(item)[:25]
        
        print(f"  Rank {rank:2}: {type_name:12} | {item_str:25} | Score: {score}")

print("\n" + "=" * 80)
print("🎉 TRUE POLYMORPHISM ACHIEVED!")
print("One tabulator that ranks ANYTHING - no special cases, no type checking!")
print("It figures out how to score objects by:")
print("  • Natural language hints")
print("  • Automatic introspection") 
print("  • Multi-criteria sorting")
print("  • Smart type adaptation")
print("=" * 80)