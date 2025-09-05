#!/usr/bin/env python3
"""Test HTML data generation"""

from database_utils import init_db, get_attendance_rankings
from tournament_report import get_legacy_attendance_data

# Initialize database
init_db()

# Get the data
rankings = get_attendance_rankings()
print("Rankings data sample:")
for r in rankings[:3]:
    print(f"  {r['display_name']}: events={r.get('num_events', 0)}, attendance={r.get('total_attendance', 0)}")

print("\nLegacy data format:")
attendance_tracker, org_names = get_legacy_attendance_data()
for i, (key, data) in enumerate(list(attendance_tracker.items())[:3]):
    print(f"  {key}: tournaments={len(data['tournaments'])}, attendance={data['total_attendance']}")