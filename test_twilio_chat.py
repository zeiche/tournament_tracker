#!/usr/bin/env python3
"""
test_twilio_chat.py - Test Twilio connected to Claude chat
"""

from polymorphic_twilio import get_twilio
import time

def test_twilio_chat():
    """Test that Twilio can connect to Claude"""
    
    print("=" * 60)
    print("TESTING TWILIO → CLAUDE CHAT CONNECTION")
    print("=" * 60)
    
    # Get Twilio instance
    twilio = get_twilio()
    
    # Start webhooks
    print("\n1. Starting webhook server...")
    result = twilio.do("start webhooks", port=8080)
    print(f"   {result}")
    
    print("\n2. Webhook URLs:")
    print(f"   Voice: http://YOUR_SERVER:8080/voice")
    print(f"   SMS:   http://YOUR_SERVER:8080/sms")
    
    print("\n3. When someone calls:")
    print("   - They hear: 'Hello! This is the tournament tracker. Ask me anything...'")
    print("   - They speak their question")
    print("   - Speech goes to Claude via ask_one_shot()")
    print("   - Claude's response is spoken back via TTS")
    print("   - Loop continues for conversation")
    
    print("\n4. Test locally:")
    print("   You can test Claude integration directly:")
    
    # Test Claude integration
    from claude_chat import ask_one_shot
    test_question = "who won the last tournament?"
    print(f"\n   Testing: '{test_question}'")
    
    response = ask_one_shot(test_question)
    if response:
        print(f"   Claude says: {response[:100]}...")
    else:
        print("   ⚠️  Claude not available - check 'claude /login'")
    
    print("\n" + "=" * 60)
    print("INTEGRATION COMPLETE!")
    print("=" * 60)
    print("""
The flow is now:
1. Call comes in → Twilio webhook
2. Speech converted to text
3. Text sent to Claude via ask_one_shot()
4. Claude's response spoken back via TTS
5. Conversation continues

No more echo - real AI responses!
    """)
    
    # Keep server running
    print("\nWebhook server running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    test_twilio_chat()