#!/usr/bin/env python3
"""Check status of recent calls"""

import os
from pathlib import Path
from twilio.rest import Client

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')

client = Client(account_sid, auth_token)

# Get recent calls
calls = client.calls.list(limit=5)

print("📞 Recent Calls:")
print("=" * 60)
for call in calls:
    print(f"SID: {call.sid}")
    print(f"To: {call.to}")
    print(f"From: {call._from}")
    print(f"Status: {call.status}")
    print(f"Direction: {call.direction}")
    print(f"Duration: {call.duration}s")
    print(f"Created: {call.date_created}")
    if call.price:
        print(f"Price: ${call.price}")
    print("-" * 60)