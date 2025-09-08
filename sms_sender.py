#!/usr/bin/env python3
"""
sms_sender.py - Send SMS messages via Twilio
"""

import os
import sys
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

# Get credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_PHONE_NUMBER')

def send_sms(to_number, message):
    """Send an SMS message"""
    
    # Create client
    client = Client(account_sid, auth_token)
    
    # Send message
    msg = client.messages.create(
        body=message,
        from_=from_number,
        to=to_number
    )
    
    print(f"📱 SMS sent to {to_number}")
    print(f"Message SID: {msg.sid}")
    print(f"Status: {msg.status}")
    print(f"Message: {message[:50]}...")
    
    return msg.sid

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 sms_sender.py <phone_number> [message]")
        sys.exit(1)
    
    to_number = sys.argv[1]
    
    # Ensure number has country code
    if not to_number.startswith('+'):
        if to_number.startswith('1'):
            to_number = '+' + to_number
        else:
            to_number = '+1' + to_number
    
    # Default message or custom
    if len(sys.argv) > 2:
        message = ' '.join(sys.argv[2:])
    else:
        message = "🏆 Tournament Update: Top players are Monte, Gamer Ace, and ForeignSkies! Recent event: West Coast Warzone (256 players). Reply for more info or call 878-TRY-HARD!"
    
    send_sms(to_number, message)