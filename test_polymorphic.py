#!/usr/bin/env python3
"""
Test the TRULY polymorphic tabulator with various object types
"""
from polymorphic_tabulator import tabulate, PolymorphicTabulator
from database import get_session
from tournament_models import Player, Tournament, Organization
from datetime import datetime
import random

print("=" * 70)
print("TESTING TRUE POLYMORPHIC TABULATION")
print("=" * 70)

# Test 1: Raw numbers
print("\n1. RAW NUMBERS (no hint needed):")
numbers = [42, 17, 99, 17, 3, 88, 42, 100]
for rank, num, score in tabulate(numbers)[:6]:
    print(f"  Rank {rank}: {num}")

# Test 2: Strings 
print("\n2. STRINGS (auto-detects alphabetical):")
words = ["zebra", "apple", "banana", "Apple", "cherry", "banana"]
for rank, word, score in tabulate(words, "alphabetical")[:5]:
    print(f"  Rank {rank}: {word}")

# Test 3: Database objects with natural language hints
print("\n3. PLAYERS WITH NATURAL LANGUAGE HINTS:")
try:
    with get_session() as session:
        players = session.query(Player).limit(10).all()
        
        if players:
            print("\n  A) 'most wins':")
            for rank, player, score in tabulate(players, "most wins")[:5]:
                print(f"    Rank {rank}: {player.gamer_tag} ({score} wins)")
            
            print("\n  B) 'highest points':")
            for rank, player, score in tabulate(players, "highest points")[:5]:
                print(f"    Rank {rank}: {player.gamer_tag} ({score} points)")
except Exception as e:
    print(f"  Database error: {e}")

# Test 4: Custom objects
print("\n4. CUSTOM OBJECTS:")
class CustomThing:
    def __init__(self, name, value, priority):
        self.name = name
        self.value = value
        self.priority = priority
    
    def __str__(self):
        return f"{self.name}(v={self.value})"

things = [
    CustomThing("Alpha", 100, 3),
    CustomThing("Beta", 50, 1),
    CustomThing("Gamma", 75, 1),
]

print("\n  Auto-detection finds scoring attribute:")
for rank, thing, score in tabulate(things):
    print(f"    Rank {rank}: {thing} - score: {score}")

print("\n" + "=" * 70)
print("TRUE POLYMORPHISM - One tabulator for EVERYTHING!")
print("=" * 70)
