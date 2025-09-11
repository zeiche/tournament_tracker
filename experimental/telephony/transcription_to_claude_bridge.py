#!/usr/bin/env python3
"""
transcription_to_claude_bridge.py - THE MISSING LINK!
Listens for TRANSCRIPTION_COMPLETE announcements and connects to Claude
"""

import asyncio
import threading
from typing import Optional, Dict, Any
from capability_announcer import announcer
from capability_discovery import register_capability, discover_capability

class TranscriptionToClaudeBridge:
    """The bridge that connects transcriptions to Claude and back to Discord"""
    
    _instance = None
    _listener_thread = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce ourselves
        announcer.announce(
            "TranscriptionToClaudeBridge",
            [
                "I am THE MISSING LINK in the voice pipeline!",
                "I listen for TRANSCRIPTION_COMPLETE announcements",
                "I send transcriptions to Claude",
                "I get Claude's response",
                "I have Discord bot speak the response",
                "I complete the voice conversation loop"
            ]
        )
        
        self.active_sessions = {}
        self.discord_bot = None
        self.start_listening()
        
    def start_listening(self):
        """Start listening for transcription announcements"""
        # Hook into the announcer to get notifications
        # We'll override the announce method to intercept TRANSCRIPTION_COMPLETE
        original_announce = announcer.announce
        
        def intercepted_announce(service_name: str, capabilities: list, examples: list = None):
            # Call original first (non-blocking)
            result = original_announce(service_name, capabilities, examples)
            
            # Check if it's a transcription completion
            if service_name == "TRANSCRIPTION_COMPLETE":
                # Process in a separate thread to avoid blocking
                import threading
                def process():
                    # Parse the transcription from capabilities
                    for cap in capabilities:
                        if cap.startswith("USER") and "said:" in cap:
                            # Extract user ID and transcription
                            parts = cap.split("said:")
                            if len(parts) == 2:
                                user_part = parts[0].strip()
                                transcription = parts[1].strip().strip("'\"")
                                
                                # Extract user ID
                                user_id = None
                                if "USER" in user_part:
                                    try:
                                        user_id = int(user_part.split()[-1])
                                    except:
                                        pass
                                
                                # Process the transcription
                                if transcription:
                                    self.on_transcription_complete(user_id, transcription)
                                break
                
                # Start the processing thread
                thread = threading.Thread(target=process, daemon=True)
                thread.start()
            
            return result
        
        # Replace the announce method
        announcer.announce = intercepted_announce
        
        announcer.announce(
            "TranscriptionToClaudeBridge",
            ["Now listening for TRANSCRIPTION_COMPLETE announcements"]
        )
    
    def on_transcription_complete(self, user_id: Optional[int], transcription: str):
        """Called when a transcription is complete"""
        # Run async processing in a separate thread to avoid blocking
        import threading
        thread = threading.Thread(
            target=self._process_transcription_sync,
            args=(user_id, transcription),
            daemon=True
        )
        thread.start()
    
    def _process_transcription_sync(self, user_id: Optional[int], transcription: str):
        """Process transcription in a separate thread"""
        announcer.announce(
            "BRIDGE_PROCESSING",
            [
                f"Received transcription: '{transcription}'",
                f"From user: {user_id}",
                "Sending to Claude..."
            ]
        )
        
        # Get Claude's response
        response = self.get_claude_response(transcription, user_id)
        
        if response:
            # Have Discord bot speak the response
            self.speak_response(response, user_id)
    
    def get_claude_response(self, transcription: str, user_id: Optional[int]) -> str:
        """Get Claude's response to the transcription"""
        try:
            # Use the proper go.py AI system
            import subprocess
            import tempfile
            import os
            
            # Write the transcription to a temp file for go.py to process
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Voice message from user {user_id}: {transcription}")
                temp_file = f.name
            
            try:
                # Use go.py AI chat - write question to stdin
                # Use Popen for non-blocking subprocess
                import subprocess
                result = subprocess.run(
                    ['./go.py', '--ai-chat'],
                    cwd='/home/ubuntu/claude/tournament_tracker',
                    input=transcription + '\nexit\n',
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    response = result.stdout.strip()
                    # Keep response short for voice
                    if len(response) > 300:
                        lines = response.split('\n')
                        response = '\n'.join(lines[:3])
                        if len(response) > 300:
                            response = response[:300] + "..."
                    
                    announcer.announce(
                        "BRIDGE_CLAUDE",
                        [f"Claude responded via go.py: '{response[:100]}...'"]
                    )
                    return response
                else:
                    # Try polymorphic query as fallback
                    from search.polymorphic_queries import query as pq
                    response = pq(transcription)
                    announcer.announce(
                        "BRIDGE_CLAUDE", 
                        [f"Claude responded via polymorphic fallback: '{response[:100]}...'"]
                    )
                    return response
                    
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            
        except Exception as e:
            announcer.announce(
                "BRIDGE_ERROR",
                [f"Error getting Claude response: {e}"]
            )
            return f"I heard you say: '{transcription}'. Voice processing is working, but Claude had an error."
    
    def speak_response(self, response: str, user_id: Optional[int]):
        """Have Discord bot speak the response"""
        announcer.announce(
            "BRIDGE_SPEAK",
            [
                f"Speaking response: '{response[:100]}...'",
                f"To user: {user_id}",
                "Through Discord voice"
            ]
        )
        
        # Use registered Discord bot if available
        if self.discord_bot:
            try:
                # Get the Discord bot's event loop
                if hasattr(self.discord_bot, 'say_in_voice') and hasattr(self.discord_bot, 'bot'):
                    # Schedule speech on Discord's event loop
                    bot = self.discord_bot.bot
                    bot.loop.create_task(self._speak_async(response))
                    announcer.announce(
                        "BRIDGE_SPEAK",
                        ["Response scheduled for Discord speech"]
                    )
                else:
                    announcer.announce(
                        "BRIDGE_SPEAK_ERROR",
                        ["Discord bot missing required methods"]
                    )
            except Exception as e:
                announcer.announce(
                    "BRIDGE_SPEAK_ERROR",
                    [f"Could not schedule speech: {e}"]
                )
                # Fallback: try to speak without async
                self._speak_fallback(response)
        else:
            announcer.announce(
                "BRIDGE_SPEAK",
                ["Discord bot not registered - cannot speak response"]
            )
    
    async def _speak_async(self, response: str):
        """Async helper to speak response"""
        try:
            await self.discord_bot.say_in_voice(response)
            announcer.announce(
                "BRIDGE_SPEAK",
                ["Response spoken successfully!"]
            )
        except Exception as e:
            announcer.announce(
                "BRIDGE_SPEAK_ERROR",
                [f"Error in async speech: {e}"]
            )
    
    async def _speak_with_bot(self, bot, response: str):
        """Speak using discovered bot"""
        try:
            await bot.say_in_voice(response)
            announcer.announce(
                "BRIDGE_SPEAK",
                ["Response spoken via discovered bot!"]
            )
        except Exception as e:
            announcer.announce(
                "BRIDGE_SPEAK_ERROR",
                [f"Error with discovered bot: {e}"]
            )
    
    def _speak_fallback(self, response: str):
        """Fallback speech method using espeak directly"""
        try:
            import subprocess
            import tempfile
            import os
            
            # Generate audio with espeak
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_wav = f.name
            
            subprocess.run(['espeak', '-w', temp_wav, response], check=False)
            
            announcer.announce(
                "BRIDGE_SPEAK_FALLBACK",
                [f"Generated fallback audio: {temp_wav}", f"Text: '{response[:50]}...'"]
            )
            
            # Clean up after a delay
            os.unlink(temp_wav)
            
        except Exception as e:
            announcer.announce(
                "BRIDGE_SPEAK_FALLBACK_ERROR",
                [f"Fallback speech failed: {e}"]
            )
    
    def register_discord_bot(self, bot):
        """Register the Discord bot for speaking responses"""
        self.discord_bot = bot
        announcer.announce(
            "TranscriptionToClaudeBridge",
            ["Discord bot registered for voice responses"]
        )

# Create global instance
bridge = TranscriptionToClaudeBridge()

# Register as discoverable
register_capability('transcription_bridge', lambda: bridge)

announcer.announce(
    "TranscriptionToClaudeBridge",
    [
        "Bridge initialized and listening!",
        "Voice pipeline is now complete:",
        "1. Discord captures audio",
        "2. Audio sink transcribes",
        "3. Bridge sends to Claude",
        "4. Claude responds",
        "5. Discord speaks response"
    ]
)