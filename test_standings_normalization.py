#!/usr/bin/env python3
"""
Test script to verify standings normalization
"""

from event_standardizer import EventStandardizer

# Test event names that might come from start.gg
test_events = [
    # Ultimate events that should be processed
    "Ultimate Singles",
    "Ultimate Doubles",
    "SSBU Singles",
    "Super Smash Bros. Ultimate Tournament",
    "Ultimate Squad Strike",
    "Ultimate 1v1",
    "Ultimate 2v2",
    "UAS Singles",
    "UAS: Doubles",
    "Smash Ultimate Singles Bracket",
    
    # Ultimate special events (should be marked as special)
    "Ultimate Arcadian",
    "Ultimate Elementary Bracket",
    "Ultimate High School Bracket",
    "Ultimate Crew Battle",
    "UAS: Last Apex Standing",
    
    # Non-Ultimate events that should be filtered out
    "Melee Singles",
    "SF6 Singles",
    "Tekken 8 Tournament",
    "Guilty Gear Strive",
    "DBFZ Teams",
]

print("Testing Event Normalization for Smash Ultimate")
print("=" * 80)
print()

ultimate_events = []
filtered_events = []

for event in test_events:
    result = EventStandardizer.standardize(event)
    
    if result['game'] == 'ultimate':
        ultimate_events.append({
            'original': event,
            'normalized': result['standard_name'],
            'format': result['format'],
            'is_special': result['is_special']
        })
    else:
        filtered_events.append({
            'original': event,
            'detected_game': result['game']
        })

print(f"ULTIMATE EVENTS ({len(ultimate_events)} found):")
print("-" * 40)
for event in ultimate_events:
    special_tag = " [SPECIAL]" if event['is_special'] else ""
    print(f"  {event['original']:<40} -> {event['normalized']}{special_tag}")

print()
print(f"FILTERED OUT ({len(filtered_events)} non-Ultimate events):")
print("-" * 40)
for event in filtered_events:
    print(f"  {event['original']:<40} (detected as: {event['detected_game']})")

print()
print("Summary:")
print(f"  - Total events tested: {len(test_events)}")
print(f"  - Ultimate events kept: {len(ultimate_events)}")
print(f"  - Non-Ultimate filtered: {len(filtered_events)}")

# Show unique normalized names
print()
print("Unique Normalized Event Categories:")
unique_names = set(e['normalized'] for e in ultimate_events)
for name in sorted(unique_names):
    count = sum(1 for e in ultimate_events if e['normalized'] == name)
    print(f"  - {name}: {count} events")