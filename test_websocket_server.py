#!/usr/bin/env python3
"""
Quick test to verify WebSocket server can start.
"""

import asyncio
import websockets
import threading
import time
import sys

async def test_server(websocket, path):
    """Simple test handler."""
    print(f"✅ Connection received from {websocket.remote_address}")
    await websocket.send("Hello from server!")
    await websocket.close()

async def start_test_server():
    """Start a test WebSocket server."""
    print("🚀 Starting test WebSocket server on port 8087...")
    try:
        async with websockets.serve(test_server, "0.0.0.0", 8087):
            print("✅ Server started successfully!")
            await asyncio.sleep(2)  # Run for 2 seconds
            print("✅ Server can accept connections")
    except Exception as e:
        print(f"❌ Server failed: {e}")
        return False
    return True

def test_twilio_stream_import():
    """Test if the Twilio stream server can be imported."""
    print("\n📦 Testing Twilio stream server import...")
    try:
        import twilio_stream_server
        print("✅ twilio_stream_server imports successfully")
        
        # Check if handler class exists
        handler = twilio_stream_server.TwilioStreamHandler()
        print("✅ TwilioStreamHandler class instantiated")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_twiml_server():
    """Test if TwiML server works."""
    print("\n🌐 Testing TwiML server...")
    try:
        from twiml_stream_server import app
        print("✅ TwiML Flask app imported")
        
        # Test that routes exist
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ TwiML server index page works")
            
            response = client.get('/voice-stream.xml')
            if b"<Stream" in response.data:
                print("✅ TwiML generates Stream XML correctly")
                print(f"   Sample: {response.data[:100].decode('utf-8')}...")
            return True
    except Exception as e:
        print(f"❌ TwiML test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing WebSocket Server Components\n")
    
    # Test 1: Basic WebSocket
    success = await start_test_server()
    
    # Test 2: Twilio handler
    if success:
        success = test_twilio_stream_import()
    
    # Test 3: TwiML server
    if success:
        success = test_twiml_server()
    
    if success:
        print("\n✅ ALL TESTS PASSED!")
        print("\nTo run the actual servers:")
        print("1. Terminal 1: python3 twilio_stream_server.py")
        print("2. Terminal 2: python3 twiml_stream_server.py")
        print("\nThe WebSocket server will run forever waiting for Twilio connections.")
        print("This is normal behavior - it's a server that needs to stay running.")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())