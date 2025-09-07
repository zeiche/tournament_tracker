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
    """Handle calls by processing speech through Claude"""
    from_number = call_data.get('From', '')
    speech_result = call_data.get('SpeechResult', '')
    
    announcer.announce(
        "TWILIO_CLAUDE_CALL",
        [f"Processing call from {from_number}", f"Speech: {speech_result}"]
    )
    
    # If we have speech input, process it
    if speech_result:
        # Try polymorphic query first
        try:
            response = pq(speech_result)
            if response and response != "I don't understand that query.":
                # Make response more conversational for voice
                if len(response) > 200:
                    response = response[:200] + "... Text me for the full details."
                return response
        except:
            pass
        
        # Simple responses for common questions
        speech_lower = speech_result.lower()
        if "hello" in speech_lower or "hi" in speech_lower:
            return "Hello! Ask me about tournaments, players, or recent events."
        elif "tournament" in speech_lower:
            return "We track Fighting Game Community tournaments in Southern California. What would you like to know?"
        elif "player" in speech_lower:
            return "I can tell you about player rankings and statistics. Which player interests you?"
        elif "bye" in speech_lower or "goodbye" in speech_lower:
            return "Goodbye! Text this number anytime for more information."
        else:
            return f"I heard you say: {speech_result}. I can help with tournament info, player stats, and rankings."
    
    # No speech yet, return None to use default greeting
    return None

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