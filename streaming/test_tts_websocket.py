#!/usr/bin/env python3
"""
Test TTS by simulating a Twilio WebSocket connection
This mimics what Twilio would send to test our TTS response
"""

import asyncio
import websockets
import json
import ssl
import sys
import base64

async def test_tts_websocket():
    """Test TTS by connecting to our WebSocket server like Twilio would"""
    
    # Connect to our WebSocket server with SSL disabled for testing
    uri = "wss://localhost:8088/"
    
    # Create SSL context that ignores certificate errors for testing
    ssl_context = ssl.SSLContext()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("🔌 Connected to WebSocket server")
            
            # Send connected message (like Twilio does)
            connected_msg = {
                "event": "connected",
                "protocol": "Call"
            }
            await websocket.send(json.dumps(connected_msg))
            print("📡 Sent connected message")
            
            # Send start message (like Twilio does when call begins)
            start_msg = {
                "event": "start",
                "start": {
                    "callSid": "TEST_CALL_123",
                    "streamSid": "TEST_STREAM_456", 
                    "customParameters": {
                        "caller": "TEST_CALLER",
                        "mode": "polymorphic_transcription"
                    }
                }
            }
            await websocket.send(json.dumps(start_msg))
            print("🎙️ Sent start message - this should trigger TTS intro")
            
            # Wait a bit for TTS to process
            print("⏳ Waiting for TTS audio...")
            
            # Listen for responses
            timeout_count = 0
            while timeout_count < 10:  # Wait up to 10 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    event = data.get('event')
                    
                    if event == 'media':
                        payload = data.get('media', {}).get('payload', '')
                        print(f"🔊 Received TTS audio! Length: {len(payload)} chars (base64)")
                        
                        # Decode a small sample to verify it's audio data
                        if payload:
                            try:
                                audio_bytes = base64.b64decode(payload[:100])  # First 100 chars
                                print(f"🔊 Audio sample: {len(audio_bytes)} bytes of audio data")
                                print("✅ TTS is working! Real audio received")
                                return True
                            except:
                                print("⚠️ Could not decode audio payload")
                    
                    print(f"📨 Response: {event}")
                    
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"⏳ Waiting... ({timeout_count}/10)")
                    continue
            
            print("❌ No TTS audio received in 10 seconds")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket connection error: {e}")
        return False

async def main():
    print("🧪 Testing TTS WebSocket Connection")
    print("=" * 40)
    
    success = await test_tts_websocket()
    
    if success:
        print("\n✅ TTS Test PASSED - Bot will speak during calls!")
    else:
        print("\n❌ TTS Test FAILED - Bot still silent")
    
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)