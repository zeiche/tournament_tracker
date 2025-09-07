#!/usr/bin/env python3
"""
test_polymorphic_twilio.py - Test the polymorphic Twilio implementation
Shows how natural and simple it is to use just ask(), tell(), do()
"""

from polymorphic_twilio import get_twilio
from capability_announcer import announcer

def test_polymorphic_twilio():
    """Test the polymorphic Twilio interface"""
    
    print("=" * 60)
    print("TESTING POLYMORPHIC TWILIO - Just 3 Methods!")
    print("=" * 60)
    
    # Get the Twilio instance
    twilio = get_twilio()
    
    # Test ask() - Query information
    print("\n1. TESTING ask() - Natural language queries:")
    print("-" * 40)
    
    queries = [
        "what's your phone number",
        "recent messages",
        "active calls",
        "capabilities",
        "status"
    ]
    
    for query in queries:
        print(f"Q: {query}")
        result = twilio.ask(query)
        print(f"A: {result}\n")
    
    # Test tell() - Format output
    print("\n2. TESTING tell() - Different formats:")
    print("-" * 40)
    
    formats = ["default", "discord", "brief", "json"]
    
    for fmt in formats:
        print(f"Format: {fmt}")
        result = twilio.tell(fmt)
        if isinstance(result, dict):
            import json
            print(json.dumps(result, indent=2))
        else:
            print(result)
        print()
    
    # Test do() - Perform actions
    print("\n3. TESTING do() - Natural language actions:")
    print("-" * 40)
    
    # Note: These are examples that would work with real credentials
    print("Examples of natural language actions:")
    print("  twilio.do('send sms to 555-1234: Hello!')")
    print("  twilio.do('call 555-1234 with tournament update')")
    print("  twilio.do('text', to='555-1234', body='Meeting at 3pm')")
    print("  twilio.do('start webhooks')")
    
    # Start webhooks (safe to actually run)
    print("\nStarting webhooks...")
    result = twilio.do("start webhooks", port=8081)
    print(f"Result: {result}")
    
    # Show the beauty of polymorphism
    print("\n" + "=" * 60)
    print("THE POWER OF POLYMORPHISM")
    print("=" * 60)
    print("""
Instead of remembering:
  - client.messages.create(to=..., from_=..., body=...)
  - client.calls.create(to=..., from_=..., twiml=...)
  - app.route('/voice', methods=['POST'])
  - response.gather(input='speech', ...)
  
You just use:
  - twilio.ask("anything")  
  - twilio.tell("format")
  - twilio.do("action")
  
The object FIGURES OUT what you want!
    """)
    
    print("\n" + "=" * 60)
    print("COMPARE TO OLD WAY:")
    print("=" * 60)
    print("""
OLD (200+ methods to remember):
  twilio.send_sms(to, body)
  twilio.make_call(to, message)
  twilio.get_phone_number()
  twilio.get_recent_messages()
  twilio.get_active_calls()
  twilio.start_webhook_server()
  twilio.handle_voice_webhook()
  twilio.handle_sms_webhook()
  ... and 192 more methods!
  
NEW (just 3 methods):
  twilio.ask("phone number")
  twilio.tell("discord")
  twilio.do("call 555-1234")
  
Natural language -> Natural code!
    """)

if __name__ == "__main__":
    test_polymorphic_twilio()