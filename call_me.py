#!/usr/bin/env python3
"""
call_me.py - Called by go.py --call to make outbound calls via Bonjour
"""

import sys
import os
import time
import requests

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from polymorphic_core import announcer, discover_capability
except ImportError:
    class DummyAnnouncer:
        def announce(self, *args, **kwargs):
            print(f"📢 ANNOUNCE: {args}")
    announcer = DummyAnnouncer()
    def discover_capability(name):
        return None

def make_bonjour_call(target):
    """Make a call using Bonjour-discovered services"""
    
    print(f"📞 Making Bonjour call to: {target}")
    
    # Announce call intent
    announcer.announce(
        "OUTBOUND_CALL_REQUEST",
        [
            f"TARGET: {target}",
            "METHOD: Bonjour discovery",
            "PURPOSE: Self-test call",
            "EXPECTED: Connect to our own transcription system"
        ]
    )
    
    # Try to discover calling capabilities
    print("🔍 Discovering calling services...")
    
    twilio_service = discover_capability('twilio')
    voice_service = discover_capability('voice')
    call_service = discover_capability('call')
    
    services_found = sum(1 for s in [twilio_service, voice_service, call_service] if s)
    print(f"   Found {services_found} calling services")
    
    # If target is localhost/ourselves, try to connect to our own webhook
    if target in ['localhost', '127.0.0.1', 'self', 'ourselves']:
        return call_ourselves()
    
    # Try using discovered services
    if twilio_service:
        return try_twilio_call(twilio_service, target)
    elif voice_service:
        return try_voice_call(voice_service, target)
    else:
        print("❌ No calling services found")
        return False

def call_ourselves():
    """Try to call our own webhook endpoint"""
    
    print("🔄 Attempting to call ourselves via webhook...")
    
    # Our TwiML endpoint
    webhook_url = "http://localhost:8086/voice-stream.xml"
    
    try:
        # Test if our webhook is responding
        print(f"   Testing webhook: {webhook_url}")
        response = requests.get(webhook_url, timeout=5)
        
        if response.status_code == 200:
            print("   ✅ Webhook responding")
            print(f"   📋 TwiML Response: {len(response.text)} bytes")
            
            # Parse the TwiML to see where it would connect
            if 'wss://' in response.text:
                ws_url = response.text.split('wss://')[1].split('"')[0]
                ws_url = 'wss://' + ws_url
                print(f"   🔗 Would connect WebSocket to: {ws_url}")
                
                # Announce successful "call" setup
                announcer.announce(
                    "SELF_CALL_SUCCESS",
                    [
                        "WEBHOOK: Responding correctly",
                        f"WEBSOCKET: {ws_url}",
                        "STATUS: Ready for real Twilio calls", 
                        "RESULT: Self-test successful"
                    ]
                )
                
                return True
            else:
                print("   ⚠️ No WebSocket URL in TwiML")
                return False
        else:
            print(f"   ❌ Webhook error: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"   ❌ Connection error: {e}")
        return False

def try_twilio_call(service, target):
    """Try calling via Twilio service"""
    
    print("📞 Attempting Twilio call...")
    
    try:
        if hasattr(service, 'do'):
            result = service.do(f"call {target}")
            print(f"   📋 Twilio result: {result}")
            return True
        else:
            print("   ❌ No 'do' method on Twilio service")
            return False
    except Exception as e:
        print(f"   ❌ Twilio call error: {e}")
        return False

def try_voice_call(service, target):
    """Try calling via voice service"""
    
    print("🎤 Attempting voice call...")
    
    try:
        if hasattr(service, 'call'):
            result = service.call(target)
            print(f"   📋 Voice result: {result}")
            return True
        else:
            print("   ❌ No 'call' method on voice service")
            return False
    except Exception as e:
        print(f"   ❌ Voice call error: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 call_me.py <target>")
        print("Examples:")
        print("  python3 call_me.py localhost")
        print("  python3 call_me.py +15551234567")
        return 1
    
    target = sys.argv[1]
    
    print("📞 Bonjour Call Service")
    print("=" * 30)
    print(f"Target: {target}")
    
    success = make_bonjour_call(target)
    
    if success:
        print(f"\n✅ Call attempt successful!")
        print("📞 Connection ready or established")
    else:
        print(f"\n❌ Call attempt failed")
        print("🔧 Check services and connectivity")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())