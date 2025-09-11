#!/usr/bin/env python3
"""
tournament_voice_handler.py - Handles tournament queries from voice
Connects to the Intelligence system (polymorphic_queries)
"""

from capability_announcer import announcer

def handle_tournament_speech(speech: str, from_number: str) -> str:
    """
    Handle tournament-related speech using Intelligence system
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
            "Ask me anything about tournaments! "
            "Try: top players, recent tournaments, player names, "
            "organization stats, or any tournament question."
        )
    
    try:
        # Use the Intelligence system - polymorphic_queries!
        from search.polymorphic_queries import PolymorphicQuery
        from database import get_session
        
        # Pass to Intelligence system
        with get_session() as session:
            # Intelligence figures out what they want
            if "player" in speech.lower():
                players = PolymorphicQuery.find_players(speech, session)
                if players:
                    # Format for voice
                    if len(players) <= 3:
                        response = "The top players are: "
                    else:
                        response = f"The top {len(players)} players are: "
                    
                    for i, p in enumerate(players[:8], 1):  # Up to 8 for voice
                        # Prefer gamer_tag/handle over real name
                        display_name = p.gamer_tag if p.gamer_tag else p.name
                        # Use first name/word only for brevity in voice
                        first_name = display_name.split()[0] if display_name else "Unknown"
                        if i == len(players[:8]):
                            response += f"and {first_name}."
                        else:
                            response += f"{first_name}, "
                else:
                    response = "No players found."
            elif "tournament" in speech.lower():
                tournaments = PolymorphicQuery.find_tournaments(speech, session)
                if tournaments:
                    response = "Recent tournaments: "
                    for t in tournaments[:3]:
                        response += f"{t.name}. "
                else:
                    response = "No tournaments found."
            else:
                # Default intelligence response
                response = PolymorphicQuery.process(speech, session)
        
        # Clean for voice (remove Discord formatting)
        import re
        response = re.sub(r'\*\*(.+?)\*\*', r'\1', response)  # Remove bold
        response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)  # Remove code blocks
        response = re.sub(r'[📊🏆🎮🥇🥈🥉👑]', '', response)  # Remove emojis
        
        # Truncate if too long for voice
        if len(response) > 400:
            # Find a good break point
            sentences = response[:400].split('. ')
            if len(sentences) > 1:
                response = '. '.join(sentences[:-1]) + '.'
            else:
                response = response[:397] + "..."
        
        return response
        
    except Exception as e:
        # Fallback if Intelligence system has issues
        announcer.announce(
            "VOICE_INTELLIGENCE_ERROR",
            [f"Error: {e}"]
        )
        return "I'm having trouble processing that question. Try asking differently."

# When imported, announce ourselves
announcer.announce(
    "TournamentVoiceHandler",
    [
        "I handle tournament queries from voice calls",
        "Register me with Twilio bridge to process speech",
        "I use polymorphic Claude for responses"
    ]
)