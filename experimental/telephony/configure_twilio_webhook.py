#!/usr/bin/env python3
"""
configure_twilio_webhook.py - Set up webhook for inbound calls
"""

from twilio.rest import Client
import os
from pathlib import Path

# Load .env
env_file = Path('.env')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value.strip('"')

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
phone_number = os.getenv('TWILIO_PHONE_NUMBER')

# Your server's public IP
server_url = "http://64.111.98.139:8083/inbound-voice"

client = Client(account_sid, auth_token)

# Find the phone number
numbers = client.incoming_phone_numbers.list(phone_number=phone_number)

if numbers:
    number = numbers[0]
    print(f"📞 Configuring {phone_number}...")
    print(f"🔗 Old voice URL: {number.voice_url}")
    
    # Update the voice webhook
    number.update(
        voice_url=server_url,
        voice_method="POST",
        status_callback="",  # Clear status callback
        status_callback_method="POST"
    )
    
    print(f"✅ Updated voice URL to: {server_url}")
    print(f"📱 Call {phone_number} to test!")
else:
    print(f"❌ Phone number {phone_number} not found in your Twilio account")
    
    # List available numbers
    print("\nAvailable numbers:")
    for num in client.incoming_phone_numbers.list():
        print(f"  - {num.phone_number} (current webhook: {num.voice_url})")