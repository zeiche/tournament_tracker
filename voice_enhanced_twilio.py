#!/usr/bin/env python3
"""
voice_enhanced_twilio.py - Enhanced voice interactions for 878-TRY-HARD
Making phone calls more natural and tournament-focused
"""

from typing import Dict, Any, Optional
from twilio.twiml.voice_response import VoiceResponse, Gather
from capability_announcer import announcer
import re
import json

class VoiceEnhancedTwilio:
    """
    Enhanced voice interaction handler for tournament tracker calls
    878-TRY-HARD (878-879-4273)
    """
    
    def __init__(self):
        # Track call state for each caller
        self.call_states = {}  # CallSid -> context
        
        # Voice shortcuts/commands
        self.voice_commands = {
            "help": self._handle_help,
            "main menu": self._handle_main_menu,
            "top players": self._handle_top_players,
            "recent tournaments": self._handle_recent,
            "stats": self._handle_stats,
            "repeat": self._handle_repeat,
        }
        
        # Announce ourselves
        announcer.announce(
            "VoiceEnhancedTwilio",
            [
                "📞 Enhanced voice interactions for 878-TRY-HARD",
                "🎯 Natural tournament conversations",
                "💬 Context-aware responses",
                "🔊 Optimized for phone TTS"
            ]
        )
    
    def process_call(self, call_data: Dict[str, Any]) -> VoiceResponse:
        """
        Process incoming call with enhanced interactions
        """
        call_sid = call_data.get('CallSid')
        from_number = call_data.get('From', 'Unknown')
        speech = call_data.get('SpeechResult')
        
        # Initialize or get call state
        if call_sid not in self.call_states:
            self.call_states[call_sid] = {
                'history': [],
                'caller': from_number,
                'turn_count': 0,
                'last_response': None
            }
        
        state = self.call_states[call_sid]
        response = VoiceResponse()
        
        if not speech:
            # Initial greeting - ANNOUNCE TOP 8 IMMEDIATELY!
            top8_greeting = self._get_top8_greeting()
            response.say(top8_greeting, voice='alice', language='en-US')
            response.pause(length=1)
            self._gather_speech(response, "Would you like more details about any player, recent tournaments, or other stats?")
        else:
            # Check if we got silence (empty speech)
            if not speech or speech.strip() == "":
                # User was silent - gentle re-prompt
                state['silence_count'] = state.get('silence_count', 0) + 1
                
                if state['silence_count'] >= 3:
                    # Too much silence, end call politely
                    response.say("I haven't heard anything. Call back when you're ready. Goodbye!", voice='alice')
                    response.hangup()
                elif state['silence_count'] == 2:
                    response.say("Are you still there?", voice='alice')
                    self._gather_speech(response)  # No prompt, just listen
                else:
                    response.say("I didn't catch that.", voice='alice')
                    self._gather_speech(response, "What would you like to know?")
            else:
                # Got speech - reset silence counter
                state['silence_count'] = 0
                state['turn_count'] += 1
                state['history'].append(speech)
                
                # Announce for bonjour
                announcer.announce(
                    "VOICE_INPUT",
                    [
                        f"📞 Caller: {from_number}",
                        f"💬 Said: {speech}",
                        f"🔄 Turn: {state['turn_count']}"
                    ]
                )
                
                # Check for goodbye/hangup
                if any(word in speech.lower() for word in ['goodbye', 'bye', 'hang up', 'end call']):
                    response.say("Thank you for calling Try Hard! Goodbye!", voice='alice')
                    response.hangup()
                    return response
                
                # Check for voice commands first
                command_response = self._check_voice_commands(speech.lower(), state)
                if command_response:
                    response.say(command_response, voice='alice')
                else:
                    # Process through Claude with voice context
                    claude_response = self._get_voice_optimized_response(speech, state)
                    state['last_response'] = claude_response
                    response.say(claude_response, voice='alice')
                
                # Smart follow-up based on context
                response.pause(length=0.5)
                
                # Don't always prompt - sometimes just listen
                if state['turn_count'] % 3 == 0:
                    # Every 3rd turn, just listen without prompting
                    self._gather_speech(response)
                else:
                    # Context-aware prompts
                    if state['turn_count'] == 1:
                        self._gather_speech(response, "Anything else?")
                    elif state['turn_count'] >= 5:
                        self._gather_speech(response, "What else?")
                    else:
                        # Sometimes no prompt for natural flow
                        self._gather_speech(response)
        
        return response
    
    def _gather_speech(self, response: VoiceResponse, prompt: str = None):
        """Add speech gathering to response with proper silence detection"""
        # Say prompt BEFORE gathering (not during!)
        if prompt:
            response.say(prompt, voice='alice')
            response.pause(length=0.5)  # Brief pause after prompt
        
        # Now gather speech WITHOUT interrupting
        gather = response.gather(
            input='speech',  # Speech recognition ONLY
            timeout=3,  # Wait 3 seconds for speech to start
            speech_timeout='auto',  # Auto-detect when speech ends
            action='/voice',
            language='en-US',
            hints='tournament,player,Tekken,Street Fighter,winner,top eight,standings,recent,stats,help,repeat',
            enhanced=True,  # Use enhanced speech model
            speechModel='phone_call',  # Optimized for phone calls
            actionOnEmptyResult=True,  # Still process even if no speech
            profanityFilter=False  # Don't filter FGC terminology
        )
        # DON'T say anything inside gather - just listen!
    
    def _check_voice_commands(self, speech: str, state: Dict) -> Optional[str]:
        """Check for voice command shortcuts"""
        for command, handler in self.voice_commands.items():
            if command in speech:
                return handler(state)
        return None
    
    def _handle_help(self, state: Dict) -> str:
        """Help menu for voice"""
        return (
            "Here's what you can ask me: "
            "Say 'top players' for rankings. "
            "Say 'recent tournaments' for latest events. "
            "Say 'stats' for database statistics. "
            "Or just ask any question about the FGC!"
        )
    
    def _handle_main_menu(self, state: Dict) -> str:
        """Return to main menu"""
        state['history'].clear()
        state['turn_count'] = 0
        return "Back to main menu. What would you like to know about tournaments?"
    
    def _handle_top_players(self, state: Dict) -> str:
        """Quick top players response"""
        from polymorphic_queries import query as pq
        result = pq("show top 5 players")
        # Format for voice
        return self._format_for_voice(result)
    
    def _handle_recent(self, state: Dict) -> str:
        """Quick recent tournaments"""
        from polymorphic_queries import query as pq
        result = pq("recent tournaments limit 3")
        return self._format_for_voice(result)
    
    def _handle_stats(self, state: Dict) -> str:
        """Quick stats"""
        from polymorphic_queries import query as pq
        result = pq("database stats")
        return self._format_for_voice(result)
    
    def _handle_repeat(self, state: Dict) -> str:
        """Repeat last response"""
        if state.get('last_response'):
            return "I said: " + state['last_response']
        return "I haven't said anything yet. What would you like to know?"
    
    def _get_top8_greeting(self) -> str:
        """Get top 8 singles rankings for initial greeting"""
        try:
            from database import get_session
            from tournament_models import TournamentPlacement
            
            with get_session() as session:
                # Get all placements
                placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.placement != None
                ).all()
                
                # Calculate points
                player_points = {}
                for p in placements:
                    if p.player_id not in player_points:
                        player_points[p.player_id] = {
                            'name': p.player.name,
                            'points': 0
                        }
                    
                    # Point system
                    if p.placement == 1:
                        player_points[p.player_id]['points'] += 10
                    elif p.placement == 2:
                        player_points[p.player_id]['points'] += 7
                    elif p.placement == 3:
                        player_points[p.player_id]['points'] += 5
                    elif p.placement == 4:
                        player_points[p.player_id]['points'] += 3
                    elif p.placement <= 8:
                        player_points[p.player_id]['points'] += 1
                
                # Sort by points
                rankings = [(data['name'], data['points']) 
                           for data in player_points.values()]
                rankings.sort(key=lambda x: x[1], reverse=True)
                
                # Format for voice - CONCISE!
                greeting = "Welcome to Try Hard! Here are the top 8 singles players: "
                
                for i, (name, points) in enumerate(rankings[:8], 1):
                    # Simplify names for TTS
                    name = name.split()[0] if name else "Unknown"  # First name only
                    
                    if i == 1:
                        greeting += f"Number 1, {name} with {points} points. "
                    elif i == 8:
                        greeting += f"And number 8, {name} with {points} points."
                    else:
                        greeting += f"Number {i}, {name}, {points} points. "
                
                return greeting
                
        except Exception as e:
            # Fallback if database error
            announcer.announce("TOP8_ERROR", [f"Error getting top 8: {e}"])
            return (
                "Welcome to Try Hard tournament tracker! "
                "I can tell you about top players and recent tournaments."
            )
    
    def _get_voice_optimized_response(self, speech: str, state: Dict) -> str:
        """Get Claude response optimized for voice"""
        try:
            from claude_chat import ask_one_shot
            
            # Add voice context to the query
            voice_context = f"""
            [VOICE CALL CONTEXT]
            This is a phone conversation. Keep responses:
            - Brief (under 300 chars ideal)
            - Natural for speech
            - No markdown or special formatting
            - Use "Try Hard" not "878-TRY-HARD"
            - Pronounce player names clearly
            
            Caller history: {state['history'][-3:] if len(state['history']) > 1 else 'First question'}
            
            Question: {speech}
            """
            
            response = ask_one_shot(voice_context)
            
            if response:
                # Clean up for TTS
                response = self._clean_for_tts(response)
                
                # Truncate if needed
                if len(response) > 400:
                    response = response[:397] + "..."
                
                announcer.announce(
                    "VOICE_RESPONSE",
                    [f"🤖 Response: {response[:100]}..."]
                )
                
                return response
            else:
                return "I couldn't process that. Could you try asking differently?"
                
        except Exception as e:
            announcer.announce(
                "VOICE_ERROR",
                [f"Error: {e}"]
            )
            return "Sorry, I'm having trouble right now. Please try again."
    
    def _format_for_voice(self, text: str) -> str:
        """Format text for voice output"""
        # Remove Discord formatting
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Code blocks
        text = re.sub(r'`(.+?)`', r'\1', text)  # Inline code
        text = re.sub(r'[📊🏆🎮🥇🥈🥉👑🎯📈💪🔥⭐️✨🌟💫⚡️🚀]', '', text)  # Emojis
        
        # Make numbers more natural
        text = re.sub(r'#(\d+)', r'number \1', text)
        text = re.sub(r'(\d+)\.(\d+)%', r'\1 point \2 percent', text)
        
        # Truncate lists for voice
        lines = text.split('\n')
        if len(lines) > 5:
            text = '\n'.join(lines[:5]) + "\n...and more"
        
        return text.strip()
    
    def _clean_for_tts(self, text: str) -> str:
        """Clean text for TTS engine"""
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove special characters that TTS struggles with
        text = re.sub(r'[<>{}[\]|\\]', '', text)
        
        # Expand abbreviations
        text = text.replace('FGC', 'F G C')
        text = text.replace('SF6', 'Street Fighter 6')
        text = text.replace('T8', 'Tekken 8')
        text = text.replace('MK', 'Mortal Kombat')
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text
    
    def cleanup_call(self, call_sid: str):
        """Clean up call state when done"""
        if call_sid in self.call_states:
            announcer.announce(
                "CALL_ENDED",
                [
                    f"📞 Call ended: {call_sid}",
                    f"🔄 Total turns: {self.call_states[call_sid]['turn_count']}"
                ]
            )
            del self.call_states[call_sid]

# Global instance
_enhanced = None

def get_enhanced():
    """Get enhanced voice handler"""
    global _enhanced
    if _enhanced is None:
        _enhanced = VoiceEnhancedTwilio()
    return _enhanced