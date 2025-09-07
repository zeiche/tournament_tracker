#!/usr/bin/env python3
"""
voice_conversation_listener.py - Listens for Discord voice announcements
Processes voice events and responds through Claude
"""

from capability_announcer import announcer
from capability_discovery import register_capability, discover_capability

class VoiceConversationListener:
    """Listens for Discord voice announcements and processes them"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce capabilities
        announcer.announce(
            "VoiceConversationListener",
            [
                "I listen for Discord voice announcements",
                "I process voice events through Claude",
                "I respond to voice commands",
                "I maintain conversation context",
                "I connect voice to intelligence"
            ]
        )
        
        self.active_conversations = {}
        self.register_with_voice_receiver()
        
    def register_with_voice_receiver(self):
        """Register to receive voice events"""
        # Discover the voice receiver
        voice_receiver = discover_capability('discord_voice_receiver')
        if voice_receiver:
            voice_receiver.register_listener(self.on_voice_received)
            announcer.announce(
                "VoiceConversationListener",
                ["Registered with Discord voice receiver"]
            )
        else:
            announcer.announce(
                "VoiceConversationListener",
                ["Voice receiver not found - will retry on next message"]
            )
    
    def on_voice_received(self, user_id: int, guild_id: int, audio_data):
        """Called when voice is received from Discord"""
        announcer.announce(
            "CONVERSATION",
            [
                f"Processing voice from user {user_id}",
                f"Guild: {guild_id}",
                f"Data size: {len(audio_data) if isinstance(audio_data, bytes) else 'text'}"
            ]
        )
        
        # If it's text (simulated voice), process it
        if isinstance(audio_data, bytes):
            try:
                text = audio_data.decode('utf-8')
                self.process_voice_command(user_id, guild_id, text)
            except:
                # Real audio would need transcription
                announcer.announce(
                    "CONVERSATION",
                    ["Audio transcription needed - install Whisper for real audio"]
                )
        else:
            self.process_voice_command(user_id, guild_id, str(audio_data))
    
    def process_voice_command(self, user_id: int, guild_id: int, text: str):
        """Process a voice command through Claude"""
        announcer.announce(
            "CONVERSATION_PROCESSING",
            [
                f"Command: '{text}'",
                f"User: {user_id}",
                "Routing to Claude..."
            ]
        )
        
        # Check for Claude triggers
        if any(trigger in text.lower() for trigger in ['claude', 'hey', 'ok', 'computer']):
            # Get Claude service
            claude = discover_capability('claude')
            if not claude:
                # Use polymorphic query system as fallback
                try:
                    from polymorphic_queries import query as pq
                    response = pq(text)
                except:
                    response = "Claude service not available"
            else:
                response = claude.process(text)
            
            # Announce the response
            announcer.announce(
                "CONVERSATION_RESPONSE",
                [
                    f"Response: '{response[:100]}...'",
                    f"For user: {user_id}",
                    "Ready to speak"
                ]
            )
            
            # Get voice service to speak response
            voice_service = discover_capability('voice')
            if voice_service:
                import asyncio
                asyncio.create_task(voice_service.speak(guild_id, response))
            
            return response
    
    def start_listening(self):
        """Start listening for voice events"""
        announcer.announce(
            "VoiceConversationListener",
            [
                "Started listening for voice events",
                "Ready to process Discord voice",
                "Waiting for announcements..."
            ]
        )
        
        # Re-register in case voice receiver wasn't ready before
        self.register_with_voice_receiver()

# Global instance
_conversation_listener = VoiceConversationListener()

def get_conversation_listener():
    """Get the global conversation listener instance"""
    return _conversation_listener

# Register with capability discovery
try:
    register_capability("voice_conversation", get_conversation_listener)
    announcer.announce("VoiceConversationListener", ["Registered as discoverable capability"])
except ImportError:
    pass

# Auto-start listening
_conversation_listener.start_listening()