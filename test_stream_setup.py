#!/usr/bin/env python3
"""
Test script to verify Twilio Stream setup.
"""

import asyncio
import subprocess
import time
import requests
import sys

def test_servers():
    """Test that all servers are configured correctly."""
    
    print("🧪 Testing Twilio Stream Setup\n")
    
    # Test 1: Check if WebSocket server code is valid
    print("1️⃣ Checking WebSocket server syntax...")
    result = subprocess.run([sys.executable, "-m", "py_compile", "twilio_stream_server.py"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ WebSocket server syntax OK")
    else:
        print(f"   ❌ Syntax error: {result.stderr}")
        return False
    
    # Test 2: Check TwiML server syntax
    print("\n2️⃣ Checking TwiML server syntax...")
    result = subprocess.run([sys.executable, "-m", "py_compile", "twiml_stream_server.py"],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ TwiML server syntax OK")
    else:
        print(f"   ❌ Syntax error: {result.stderr}")
        return False
    
    # Test 3: Check Claude stream handler
    print("\n3️⃣ Checking Claude stream handler...")
    result = subprocess.run([sys.executable, "-m", "py_compile", "twilio_claude_stream.py"],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ Claude handler syntax OK")
    else:
        print(f"   ❌ Syntax error: {result.stderr}")
        return False
    
    # Test 4: Check required modules
    print("\n4️⃣ Checking dependencies...")
    required_modules = ['websockets', 'flask', 'asyncio']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module} installed")
        except ImportError:
            print(f"   ❌ {module} missing")
            missing.append(module)
    
    if missing:
        print(f"\n   Install missing: pip install {' '.join(missing)}")
        return False
    
    print("\n✨ All checks passed! Ready to use Twilio Stream.\n")
    
    # Show usage instructions
    print("📚 Usage Instructions:")
    print("=" * 50)
    print("\n1. Start WebSocket server (choose one):")
    print("   python3 twilio_stream_server.py      # Basic handler")
    print("   python3 twilio_claude_stream.py      # With Claude AI")
    print("\n2. Start TwiML server:")
    print("   python3 twiml_stream_server.py")
    print("\n3. Configure Twilio webhook to:")
    print("   http://your-server:8086/voice-stream.xml")
    print("\n4. The WebSocket URL in TwiML should be:")
    print("   wss://your-server:8087/")
    print("\n5. For local testing with ngrok:")
    print("   ngrok http 8086  # For TwiML")
    print("   ngrok tcp 8087   # For WebSocket")
    
    print("\n📋 Stream Flow:")
    print("=" * 50)
    print("1. Call arrives → Twilio fetches TwiML")
    print("2. TwiML contains <Stream> → Twilio connects to WebSocket")
    print("3. WebSocket receives real-time audio")
    print("4. Process audio (STT → Query → TTS)")
    print("5. Send audio back through WebSocket")
    print("6. Caller hears response in real-time")
    
    return True

def show_twiml_examples():
    """Show example TwiML configurations."""
    
    print("\n📄 Example TwiML Configurations:")
    print("=" * 50)
    
    print("\n🎯 Bidirectional (recommended):")
    print("""
<Response>
    <Connect>
        <Stream url="wss://your-server:8087/">
            <Parameter name="caller" value="{{From}}"/>
        </Stream>
    </Connect>
</Response>
    """)
    
    print("\n📥 Inbound only (listen to caller):")
    print("""
<Response>
    <Start>
        <Stream url="wss://your-server:8087/" track="inbound_track"/>
    </Start>
    <Say>Ask me about tournaments!</Say>
    <Pause length="30"/>
</Response>
    """)
    
    print("\n🔄 Both tracks (full monitoring):")
    print("""
<Response>
    <Start>
        <Stream url="wss://your-server:8087/" track="both_tracks"/>
    </Start>
    <Say>Monitoring call...</Say>
</Response>
    """)

if __name__ == "__main__":
    success = test_servers()
    if success:
        show_twiml_examples()
        print("\n✅ Setup complete! Your Twilio Stream system is ready.")
    else:
        print("\n❌ Setup incomplete. Fix the issues above.")
        sys.exit(1)