#!/usr/bin/env python3
"""
twilio_claude_handler.py - Connect Twilio to Claude
Registers handlers with TwilioBridge to process calls/SMS through Claude
"""

from twilio_bridge import get_bridge
from polymorphic_queries import query as pq
from capability_announcer import announcer
import subprocess

def sms_to_claude(sms_data):
    """Handle SMS by sending to Claude"""
    body = sms_data.get('Body', '')
    from_number = sms_data.get('From', '')
    
    announcer.announce(
        "TWILIO_CLAUDE_SMS",
        [f"Processing SMS from {from_number}: {body}"]
    )
    
    # Try polymorphic query first
    try:
        response = pq(body)
        if response and response != "I don't understand that query.":
            return response[:160]  # SMS limit
    except:
        pass
    
    # Fallback to go.py AI chat
    try:
        result = subprocess.run(
            ['./go.py', '--ai-ask', body],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()[:160]
    except:
        pass
    
    return "Message received. Reply HELP for commands."

def call_to_claude(call_data):
    """Handle calls by speaking Claude's response"""
    from_number = call_data.get('From', '')
    
    announcer.announce(
        "TWILIO_CLAUDE_CALL",
        [f"Processing call from {from_number}"]
    )
    
    # Simple greeting for now
    return "Hello! This is the tournament tracker AI. Text this number for assistance."

def register_handlers():
    """Register our handlers with the bridge"""
    bridge = get_bridge()
    bridge.register_sms_handler(sms_to_claude)
    bridge.register_call_handler(call_to_claude)
    
    announcer.announce(
        "TWILIO_CLAUDE_READY",
        ["Claude handlers registered for Twilio"]
    )

if __name__ == "__main__":
    # Register handlers
    register_handlers()
    
    # Run the bridge on port 8082
    bridge = get_bridge()
    bridge.run(port=8082)