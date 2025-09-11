#!/usr/bin/env python3
"""
Use Bonjour to actually call ourselves - discover calling services and place a call
"""

import sys
import os
import time

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

def discover_calling_services():
    """Discover what calling services are available through Bonjour"""
    
    print("🔍 Discovering calling services through Bonjour...")
    
    services_to_try = [
        'twilio_bridge',
        'twilio', 
        'voice',
        'call',
        'phone',
        'audio',
        'sip',
    ]
    
    found_services = {}
    
    for service_name in services_to_try:
        service = discover_capability(service_name)
        if service:
            found_services[service_name] = service
            print(f"   ✅ Found: {service_name}")
            
            # Try to get capabilities if available
            if hasattr(service, '_get_capabilities'):
                try:
                    caps = service._get_capabilities()
                    print(f"      Capabilities: {caps}")
                except:
                    pass
        else:
            print(f"   ❌ Not found: {service_name}")
    
    return found_services

def try_twilio_call(twilio_service):
    """Try to make a call using discovered Twilio service"""
    
    print("\n📞 Attempting call via Twilio service...")
    
    # Our own number/endpoint
    our_webhook_url = "http://64.111.98.139:8086/voice-stream.xml"
    
    # Try different call methods
    call_methods = ['do', 'call', 'make_call', '_make_call']
    
    for method_name in call_methods:
        if hasattr(twilio_service, method_name):
            print(f"   🔧 Trying method: {method_name}")
            
            try:
                method = getattr(twilio_service, method_name)
                
                if method_name == 'do':
                    # Try polymorphic do() method
                    result = method("call ourselves", webhook=our_webhook_url)
                elif method_name == 'call':
                    result = method(our_webhook_url)
                else:
                    result = method("test_call", our_webhook_url)
                
                print(f"   📋 Result: {result}")
                return result
                
            except Exception as e:
                print(f"   ❌ Error with {method_name}: {e}")
                continue
    
    print("   ⚠️ No working call methods found")
    return None

def try_voice_call():
    """Try to initiate a call through voice services"""
    
    print("\n🎤 Attempting call via voice services...")
    
    # Announce a call request through Bonjour
    announcer.announce(
        "CALL_REQUEST",
        [
            "DESTINATION: ourselves",
            "TYPE: test_call",
            "WEBHOOK: http://64.111.98.139:8086/voice-stream.xml",
            "PURPOSE: Self-test call via Bonjour",
            "EXPECTED: Should connect to our transcription system"
        ]
    )
    
    # Try to discover and use any voice/call services
    voice_service = discover_capability('voice')
    if voice_service:
        print("   ✅ Found voice service")
        try:
            if hasattr(voice_service, 'call'):
                result = voice_service.call("self_test")
                print(f"   📋 Voice call result: {result}")
                return result
        except Exception as e:
            print(f"   ❌ Voice call error: {e}")
    
    return None

def simulate_call_connection():
    """Simulate what would happen if a call connected"""
    
    print("\n📡 Simulating call connection to our system...")
    
    # This is what would happen when Twilio connects to our webhook
    print("   1. Twilio would call: http://64.111.98.139:8086/voice-stream.xml")
    print("   2. Our TwiML server would respond with Stream directive")
    print("   3. WebSocket would connect to: wss://0-page.com:8088/")
    print("   4. Audio streaming would begin")
    print("   5. Transcription service would process speech")
    print("   6. Tournament queries would be answered")
    
    # Announce what we expect
    announcer.announce(
        "SIMULATED_CALL_FLOW",
        [
            "STEP_1: TwiML webhook called",
            "STEP_2: WebSocket stream established", 
            "STEP_3: Audio chunks received",
            "STEP_4: Transcription processing",
            "STEP_5: Query response generated",
            "STEP_6: TTS audio sent back",
            "RESULT: Two-way voice conversation about tournaments"
        ]
    )

def main():
    print("📞 Bonjour: Calling Myself")
    print("=" * 40)
    
    # 1. Discover available calling services
    services = discover_calling_services()
    
    if not services:
        print("\n❌ No calling services found through Bonjour")
        print("💡 Available services seem to be transcription-focused")
        simulate_call_connection()
        return 1
    
    # 2. Try to make a call using discovered services
    call_success = False
    
    if 'twilio_bridge' in services:
        result = try_twilio_call(services['twilio_bridge'])
        if result:
            call_success = True
    
    if not call_success:
        result = try_voice_call()
        if result:
            call_success = True
    
    # 3. If we can't make an actual call, simulate what would happen
    if not call_success:
        print("\n🎭 No actual calling capability found")
        print("🔄 The system is set up to RECEIVE calls, not make them")
        simulate_call_connection()
    
    # 4. Announce completion
    announcer.announce(
        "BONJOUR_CALL_TEST_COMPLETE",
        [
            f"SERVICES_FOUND: {len(services)}",
            f"CALL_ATTEMPTED: Yes",
            f"CALL_SUCCESS: {call_success}",
            "DISCOVERY: System designed for inbound calls",
            "CONCLUSION: Ready to receive Twilio calls"
        ]
    )
    
    print(f"\n📊 Result:")
    print(f"   Services discovered: {len(services)}")
    print(f"   Call capability: {'✅ Found' if call_success else '❌ Not available'}")
    print(f"   System design: Inbound call receiver")
    print(f"   Status: Ready for external Twilio calls")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())