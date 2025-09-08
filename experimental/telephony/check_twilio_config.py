#!/usr/bin/env python3
"""
check_twilio_config.py - Check and update Twilio phone number configuration
"""

from twilio.rest import Client
import os
from pathlib import Path

def check_twilio_config():
    """Check current Twilio configuration"""
    
    print("=" * 60)
    print("CHECKING TWILIO CONFIGURATION")
    print("=" * 60)
    
    # Load credentials
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not account_sid or not auth_token:
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if 'TWILIO_ACCOUNT_SID=' in line:
                        account_sid = line.split('=', 1)[1].strip().strip('"')
                    elif 'TWILIO_AUTH_TOKEN=' in line:
                        auth_token = line.split('=', 1)[1].strip().strip('"')
                    elif 'TWILIO_PHONE_NUMBER=' in line:
                        phone_number = line.split('=', 1)[1].strip().strip('"')
    
    if not account_sid or not auth_token:
        print("❌ No Twilio credentials found!")
        return
    
    client = Client(account_sid, auth_token)
    
    print(f"\n📱 Phone Number: {phone_number}")
    print(f"   878-TRY-HARD (878-879-4273)")
    
    # Get the phone number configuration
    try:
        numbers = client.incoming_phone_numbers.list(phone_number=phone_number)
        
        if numbers:
            number = numbers[0]
            print(f"\n📞 Current Configuration:")
            print(f"   SID: {number.sid}")
            print(f"   Voice URL: {number.voice_url or 'Not set'}")
            print(f"   Voice Method: {number.voice_method}")
            print(f"   SMS URL: {number.sms_url or 'Not set'}")
            print(f"   SMS Method: {number.sms_method}")
            
            # Check capabilities
            print(f"\n✨ Capabilities:")
            print(f"   Voice: {number.capabilities.get('voice', False)}")
            print(f"   SMS: {number.capabilities.get('sms', False)}")
            print(f"   MMS: {number.capabilities.get('mms', False)}")
            
            # Check if webhooks are configured
            if not number.voice_url:
                print("\n⚠️  VOICE WEBHOOK NOT CONFIGURED!")
                print("   You need to set the voice URL in Twilio console:")
                print("   https://console.twilio.com/console/phone-numbers/incoming")
                print(f"   Set Voice Webhook to: http://YOUR_SERVER:8080/voice")
            
            # IMPORTANT: Check if speech recognition is available
            print(f"\n🎤 Speech Recognition:")
            print("   Twilio automatically includes speech recognition")
            print("   when you use gather(input='speech')")
            print("   No additional configuration needed!")
            
            print("\n📝 To enable speech recognition:")
            print("   1. Webhook must be configured (http://YOUR_SERVER:8080/voice)")
            print("   2. gather() must use input='speech' (already set)")
            print("   3. That's it! Twilio handles the rest")
            
        else:
            print(f"❌ Phone number {phone_number} not found in account!")
            
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
    
    print("\n" + "=" * 60)
    print("TROUBLESHOOTING DTMF vs SPEECH:")
    print("=" * 60)
    print("""
    If you're getting DTMF (keypad) instead of speech:
    
    1. Make sure webhook URL is configured in Twilio console
    2. The webhook server must be publicly accessible
    3. Use ngrok for local testing:
       ngrok http 8080
       Then use the ngrok URL in Twilio console
    
    4. Speech recognition works automatically when:
       - gather(input='speech') is used
       - Webhook is properly configured
       - Server is accessible from internet
    
    Current setup uses input='speech' with:
    - enhanced=True (better accuracy)
    - speechModel='phone_call' (optimized for calls)
    - hints for tournament-related words
    """)

if __name__ == "__main__":
    check_twilio_config()