#!/usr/bin/env python3
"""
tournament_voice_handler.py - Handles tournament queries from voice
Registers with the simple Twilio bridge
"""

from capability_announcer import announcer
from polymorphic_claude_voice import claude_voice_ask

def handle_tournament_speech(speech: str, from_number: str) -> str:
    """
    Handle tournament-related speech from phone calls
    This is what gets registered with the Twilio bridge
    """
    # Announce what we're processing
    announcer.announce(
        "TOURNAMENT_VOICE_HANDLER",
        [
            f"Processing: {speech}",
            f"From: {from_number}"
        ]
    )
    
    # Check for special commands
    if speech.lower() in ['goodbye', 'bye', 'hang up']:
        return "Thank you for calling Try Hard. Goodbye!"
    
    if speech.lower() in ['help', 'what can you do']:
        return (
            "I can tell you about top players, recent tournaments, "
            "or tournament statistics. Just ask!"
        )
    
    # Process through polymorphic Claude
    response = claude_voice_ask(speech)
    
    # Make sure response is voice-friendly
    if len(response) > 400:
        response = response[:397] + "..."
    
    return response

# When imported, announce ourselves
announcer.announce(
    "TournamentVoiceHandler",
    [
        "I handle tournament queries from voice calls",
        "Register me with Twilio bridge to process speech",
        "I use polymorphic Claude for responses"
    ]
)