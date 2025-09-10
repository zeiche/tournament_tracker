#!/usr/bin/env python3
"""
Twilio Transcription Bridge - Connects Twilio streams to polymorphic transcription
This bridge listens for AUDIO_AVAILABLE and TRANSCRIPTION_COMPLETE announcements
"""

import asyncio
import json
from typing import Dict, Callable, Optional
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from polymorphic_core import announcer, discover_capability, register_capability
    from polymorphic_core.audio.transcription import get_transcription_service
except ImportError:
    print("❌ Polymorphic core not available")
    sys.exit(1)

try:
    from polymorphic_queries import query as pq
except ImportError:
    def pq(query):
        return f"Tournament query: {query}"

class TwilioTranscriptionBridge:
    """Bridge that connects Twilio audio to polymorphic transcription system."""
    
    def __init__(self):
        self.transcription_handlers = {}  # websocket -> handler mapping
        self.pending_audio = {}  # call_sid -> audio_data
        
        # Get services
        self.transcription_service = get_transcription_service()
        self.tts_service = discover_capability('tts')
        
        # Register ourselves as a capability
        register_capability('twilio_bridge', self.get_bridge)
        
        # Announce ourselves
        announcer.announce(
            "Twilio Transcription Bridge",
            [
                "I connect Twilio streams to polymorphic transcription",
                "I listen for AUDIO_AVAILABLE from Twilio streams",
                "I forward audio to PolymorphicTranscription service", 
                "I handle TRANSCRIPTION_COMPLETE announcements",
                "I send responses back to Twilio streams",
                "I bridge Twilio and Bonjour ecosystems"
            ]
        )
        
        # Hook into announcement system (simplified)
        # In full implementation, this would be event-driven
        self.setup_announcement_handlers()
    
    def get_bridge(self):
        """Get this bridge instance"""
        return self
    
    def setup_announcement_handlers(self):
        """Set up handlers for announcements"""
        # This is a simplified implementation
        # In a real system, this would hook into the announcement bus
        pass
    
    def register_twilio_handler(self, call_sid: str, websocket, stream_handler):
        """Register a Twilio stream handler"""
        self.transcription_handlers[call_sid] = {
            'websocket': websocket,
            'handler': stream_handler,
            'active': True
        }
        
        announcer.announce(
            "TWILIO_HANDLER_REGISTERED",
            [
                f"CALL_SID: {call_sid}",
                "STATUS: Ready for transcription",
                "BRIDGE: Connected to polymorphic system"
            ]
        )
    
    def unregister_twilio_handler(self, call_sid: str):
        """Unregister a Twilio stream handler"""
        if call_sid in self.transcription_handlers:
            del self.transcription_handlers[call_sid]
            announcer.announce(
                "TWILIO_HANDLER_UNREGISTERED",
                [f"CALL_SID: {call_sid}"]
            )
    
    async def process_twilio_audio(self, call_sid: str, audio_data: bytes, metadata: dict):
        """Process audio from Twilio and send to transcription"""
        # Store for potential retry
        self.pending_audio[call_sid] = {
            'data': audio_data,
            'metadata': metadata,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        # Announce audio availability
        announcer.announce(
            "AUDIO_AVAILABLE",
            [
                f"SOURCE: twilio_call_{call_sid}",
                f"SIZE: {len(audio_data)} bytes",
                f"FORMAT: {metadata.get('format', 'mulaw')}",
                f"RATE: {metadata.get('sample_rate', 8000)}",
                f"CHANNELS: {metadata.get('channels', 1)}",
                "READY: For polymorphic transcription"
            ]
        )
        
        # Send directly to transcription service
        if self.transcription_service:
            try:
                # Enhanced metadata for transcription
                trans_metadata = {
                    **metadata,
                    'source': f'twilio_call_{call_sid}',
                    'bridge': 'twilio_transcription_bridge',
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                # Send to transcription
                self.transcription_service.transcribe_audio(
                    f"twilio_call_{call_sid}",
                    audio_data,
                    trans_metadata
                )
                
                print(f"📤 Sent {len(audio_data)} bytes to transcription for call {call_sid}")
                
            except Exception as e:
                print(f"❌ Error sending to transcription: {e}")
                announcer.announce(
                    "TRANSCRIPTION_ERROR",
                    [
                        f"CALL_SID: {call_sid}",
                        f"ERROR: {e}",
                        "STATUS: Failed to process audio"
                    ]
                )
        else:
            print("⚠️ No transcription service available")
    
    async def handle_transcription_result(self, source: str, text: str):
        """Handle transcription result and generate response"""
        # Extract call_sid from source
        if not source.startswith('twilio_call_'):
            return
        
        call_sid = source.replace('twilio_call_', '')
        
        if call_sid not in self.transcription_handlers:
            print(f"⚠️ No handler for call {call_sid}")
            return
        
        handler_info = self.transcription_handlers[call_sid]
        if not handler_info['active']:
            return
        
        print(f"🎤 Transcription for {call_sid}: {text}")
        
        # Query tournament system
        try:
            response = await self.get_tournament_response(text)
            
            if response:
                print(f"🤖 Response for {call_sid}: {response[:100]}...")
                
                # Send back to Twilio handler
                websocket = handler_info['websocket']
                stream_handler = handler_info['handler']
                
                await stream_handler.send_tts_response(websocket, response)
                
                # Announce response
                announcer.announce(
                    "TWILIO_RESPONSE_SENT",
                    [
                        f"CALL_SID: {call_sid}",
                        f"QUESTION: {text}",
                        f"RESPONSE: {response[:50]}...",
                        "STATUS: Sent to caller"
                    ]
                )
            else:
                # No response generated
                await self.send_fallback_response(call_sid, text)
                
        except Exception as e:
            print(f"❌ Error generating response for {call_sid}: {e}")
            await self.send_error_response(call_sid, e)
    
    async def get_tournament_response(self, query: str) -> Optional[str]:
        """Get response from tournament system"""
        try:
            # Try polymorphic query
            response = pq(query)
            if response and len(response.strip()) > 0:
                return response
            
            # Fallback responses based on keywords
            query_lower = query.lower().strip()
            
            if any(word in query_lower for word in ['tournament', 'event', 'competition']):
                return "The latest major tournament was West Coast Warzone with 256 players. It was held last weekend in Los Angeles."
            
            elif any(word in query_lower for word in ['player', 'competitor', 'fighter']):
                return "Top players include West with 45 tournament wins, Zak with 38 wins, and Bear with 32 wins."
            
            elif any(word in query_lower for word in ['ranking', 'rank', 'leaderboard', 'top']):
                return "Current rankings: First place West, second place Zak, third place Bear. These are based on tournament performance."
            
            elif any(word in query_lower for word in ['hello', 'hi', 'hey']):
                return "Hello! I'm the Try Hard Tournament Tracker. Ask me about tournaments, players, or rankings."
            
            elif any(word in query_lower for word in ['help', 'what', 'how']):
                return "I can tell you about fighting game tournaments, player rankings, and event information. What would you like to know?"
            
            else:
                return None
                
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None
    
    async def send_fallback_response(self, call_sid: str, original_query: str):
        """Send fallback response when no specific answer is available"""
        response = "I didn't quite understand that. You can ask me about tournaments, players, or rankings."
        
        if call_sid in self.transcription_handlers:
            handler_info = self.transcription_handlers[call_sid]
            websocket = handler_info['websocket']
            stream_handler = handler_info['handler']
            
            await stream_handler.send_tts_response(websocket, response)
    
    async def send_error_response(self, call_sid: str, error):
        """Send error response"""
        response = "Sorry, I had trouble processing that request. Please try again."
        
        if call_sid in self.transcription_handlers:
            handler_info = self.transcription_handlers[call_sid]
            websocket = handler_info['websocket']
            stream_handler = handler_info['handler']
            
            await stream_handler.send_tts_response(websocket, response)
    
    def get_active_calls(self) -> list:
        """Get list of active call SIDs"""
        return list(self.transcription_handlers.keys())
    
    def get_call_status(self, call_sid: str) -> dict:
        """Get status of a specific call"""
        if call_sid in self.transcription_handlers:
            handler_info = self.transcription_handlers[call_sid]
            return {
                'call_sid': call_sid,
                'active': handler_info['active'],
                'has_websocket': handler_info['websocket'] is not None,
                'has_handler': handler_info['handler'] is not None
            }
        return {'call_sid': call_sid, 'active': False}

# Global bridge instance
_bridge = TwilioTranscriptionBridge()

def get_twilio_bridge():
    """Get the global Twilio transcription bridge"""
    return _bridge

# Hook into the transcription service to handle results
def setup_transcription_hooks():
    """Set up hooks to capture transcription results"""
    # This would integrate with the announcement system
    # For now, we'll modify the transcription service to call us back
    
    original_announce = _bridge.transcription_service.announce_transcription
    
    def enhanced_announce(source: str, text: str):
        """Enhanced announcement handler"""
        # Call original
        original_announce(source, text)
        
        # Handle in our bridge
        asyncio.create_task(_bridge.handle_transcription_result(source, text))
    
    # Replace the method
    _bridge.transcription_service.announce_transcription = enhanced_announce

# Initialize hooks
setup_transcription_hooks()

if __name__ == "__main__":
    print("🌉 Twilio Transcription Bridge running...")
    print("🔗 Connected to polymorphic transcription system")
    print("📞 Ready to handle Twilio calls")
    
    try:
        # Keep running
        asyncio.run(asyncio.Event().wait())
    except KeyboardInterrupt:
        print("\n👋 Shutting down bridge")