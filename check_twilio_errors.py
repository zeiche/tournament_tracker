#!/usr/bin/env python3
"""
check_twilio_errors.py - Check for Twilio call errors
"""

from twilio.rest import Client
import os
from pathlib import Path
from datetime import datetime, timedelta

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

# Check recent calls
print("🔍 Recent calls (last 10 minutes):")
recent = datetime.utcnow() - timedelta(minutes=10)

calls = client.calls.list(
    start_time_after=recent,
    limit=5
)

for call in calls:
    print(f"\n📞 Call SID: {call.sid}")
    print(f"   From: {call.from_formatted}")
    print(f"   To: {call.to_formatted}")
    print(f"   Status: {call.status}")
    print(f"   Direction: {call.direction}")
    print(f"   Duration: {call.duration}s")
    
    if call.direction == 'inbound' and call.status in ['failed', 'busy', 'no-answer']:
        # Get error details
        print(f"   ❌ ERROR - checking details...")
        
# Check alerts/errors
print("\n🚨 Recent alerts:")
alerts = client.monitor.alerts.list(
    start_date=recent,
    limit=5
)

for alert in alerts:
    print(f"\n⚠️  Alert: {alert.alert_text}")
    print(f"   Error Code: {alert.error_code}")
    print(f"   Resource: {alert.resource_sid}")
    print(f"   Date: {alert.date_created}")
    
if not alerts:
    print("No recent alerts")