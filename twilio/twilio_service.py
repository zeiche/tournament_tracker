#!/usr/bin/env python3
"""
twilio_service.py - Twilio audio sink for tournament tracker

This module acts as an audio sink for the audio mixer, receiving mixed audio
streams and transmitting them via Twilio Voice calls. The play() command is
blocked to force usage of real-time streaming from the audio mixer.
"""

import os
import sys
import threading
import queue
import asyncio
from typing import Any, Dict, List, Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Stream

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from polymorphic_core import announcer

# Import audio mixer for sink integration
try:
    from experimental.audio.bonjour_audio_mixer import get_mixer
except ImportError:
    get_mixer = None


class TwilioService:
    """
    Twilio audio sink service that receives mixed audio from the audio mixer.
    Acts as the final output stage for tournament audio streaming.
    Blocks play() commands to force real-time streaming patterns.
    """
    
    def __init__(self):
        """Initialize Twilio service as audio sink with bonjour announcements"""
        self.client = None
        self.account_sid = None
        self.auth_token = None
        self.phone_number = None
        
        # Audio sink properties
        self.audio_mixer = None
        self.active_calls = {}
        self.streaming_threads = {}
        self.audio_queue = queue.Queue()
        
        # Self-hosted SSL configuration  
        self.server_domain = os.getenv('TWILIO_SERVER_DOMAIN', 'www.zilogo.com')
        self.ssl_port = os.getenv('TWILIO_SSL_PORT', '8444')
        self.base_url = f"https://{self.server_domain}:{self.ssl_port}"
        self.websocket_url = f"wss://{self.server_domain}:{self.ssl_port}"
        
        self._initialize_client()
        self._initialize_audio_sink()
        self._announce_service()
    
    def _initialize_client(self):
        """Initialize Twilio client from environment variables"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            announcer.announce(
                "Twilio Configuration Error",
                [
                    "Missing required Twilio environment variables",
                    "Required: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER",
                    "Audio sink will run in demo mode"
                ]
            )
            return
        
        try:
            self.client = Client(self.account_sid, self.auth_token)
            announcer.announce(
                "Twilio Audio Sink Initialized",
                [f"Connected with SID: {self.account_sid[:8]}...", "Ready to receive audio streams"]
            )
        except Exception as e:
            announcer.announce(
                "Twilio Audio Sink Error",
                [f"Failed to initialize: {str(e)}"]
            )
    
    def _initialize_audio_sink(self):
        """Initialize connection to audio mixer as sink"""
        if get_mixer:
            try:
                self.audio_mixer = get_mixer()
                announcer.announce(
                    "Audio Sink Connection Established",
                    [
                        "Connected to BonjourAudioMixer",
                        "Ready to receive mixed audio streams",
                        "Twilio acts as final output stage"
                    ]
                )
                
                # Start audio processing thread
                self.audio_thread = threading.Thread(target=self._process_audio_stream, daemon=True)
                self.audio_thread.start()
                
            except Exception as e:
                announcer.announce(
                    "Audio Sink Connection Failed",
                    [f"Failed to connect to audio mixer: {str(e)}"]
                )
        else:
            announcer.announce(
                "Audio Mixer Not Available",
                ["Audio mixer module not found", "Running without audio sink capabilities"]
            )
    
    def _announce_service(self):
        """Announce service capabilities via bonjour"""
        capabilities = [
            "🎚️ AUDIO SINK - Receives mixed audio from BonjourAudioMixer",
            "🚫 play() command is BLOCKED - streams only from mixer",
            "📞 Transmits mixed audio via Twilio Voice calls", 
            "🎤 Real-time audio streaming via <stream> TwiML",
            "📋 Generates TwiML responses for voice calls",
            "🔄 Acts as final output stage in audio pipeline",
            f"🔗 Connected to mixer: {bool(self.audio_mixer)}",
            f"🔒 Self-hosted SSL: {self.base_url}",
            f"🌐 WebSocket endpoint: {self.websocket_url}"
        ]
        
        examples = [
            "twilio.ask('sink status') - Check audio sink status",
            "twilio.ask('active calls') - List active streaming calls",
            "twilio.tell('twiml', call_data) - Generate TwiML with mixed audio", 
            "twilio.do('call +15551234567') - Make call with mixed audio",
            "twilio.do('stream mixed audio') - Start streaming from mixer"
        ]
        
        announcer.announce(
            "Twilio Audio Sink Service",
            capabilities,
            examples
        )
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query Twilio audio sink for data using natural language
        
        Args:
            query: Natural language query about audio sink state or capabilities
            
        Returns:
            Relevant data based on query intent
        """
        query_lower = query.lower().strip()
        
        if 'sink' in query_lower and ('status' in query_lower or 'health' in query_lower):
            return self._get_audio_sink_status()
        elif 'status' in query_lower or 'health' in query_lower:
            return self._get_service_status()
        elif 'active calls' in query_lower or 'streaming calls' in query_lower:
            return self._get_active_calls()
        elif 'calls' in query_lower or 'call history' in query_lower:
            return self._get_recent_calls()
        elif 'mixer' in query_lower or 'audio mixer' in query_lower:
            return self._get_mixer_status()
        elif 'ssl' in query_lower or 'certificate' in query_lower or 'hosting' in query_lower:
            return self._get_ssl_config()
        elif 'config' in query_lower or 'settings' in query_lower:
            return self._get_configuration()
        elif 'capabilities' in query_lower or 'features' in query_lower:
            return self._get_capabilities()
        else:
            return f"Unknown query: {query}. Try 'sink status', 'active calls', 'ssl', or 'capabilities'"
    
    def tell(self, format: str, data: Any = None) -> str:
        """
        Format Twilio data for output
        
        Args:
            format: Output format (twiml, json, text, discord)
            data: Data to format
            
        Returns:
            Formatted string
        """
        if format.lower() == 'twiml':
            return self._generate_twiml(data)
        elif format.lower() == 'json':
            import json
            return json.dumps(data if data else self._get_service_status(), indent=2)
        elif format.lower() == 'discord':
            return self._format_for_discord(data)
        elif format.lower() == 'text':
            return str(data) if data else "Twilio service ready"
        else:
            return f"Unknown format: {format}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform Twilio actions using natural language
        
        Args:
            action: Natural language action to perform
            
        Returns:
            Result of the action
        """
        action_lower = action.lower().strip()
        
        # BLOCK play() commands explicitly
        if 'play(' in action_lower or action_lower.startswith('play '):
            error_msg = "🚫 BLOCKED: play() command not allowed. Use <stream> instead!"
            announcer.announce(
                "Twilio Command Blocked",
                [
                    "Attempted to use blocked play() command",
                    "Use streaming audio with <stream> TwiML element",
                    f"Blocked action: {action}"
                ]
            )
            return error_msg
        
        if action_lower.startswith('call '):
            phone = action.split(' ', 1)[1] if ' ' in action else None
            return self._make_call_with_mixed_audio(phone)
        elif 'stream mixed audio' in action_lower:
            return self._start_mixed_audio_stream()
        elif 'stream' in action_lower:
            return self._setup_audio_stream(action)
        elif 'twiml' in action_lower or 'response' in action_lower:
            return self._generate_twiml_with_mixed_audio()
        elif 'test' in action_lower:
            return self._test_connection()
        elif 'stop stream' in action_lower:
            return self._stop_audio_streams()
        else:
            return f"Unknown action: {action}. Try 'call +1234567890', 'stream mixed audio', or 'test'"
    
    def _get_service_status(self) -> Dict:
        """Get current service status"""
        return {
            "service": "Twilio Voice",
            "client_initialized": self.client is not None,
            "account_sid": self.account_sid[:8] + "..." if self.account_sid else None,
            "phone_number": self.phone_number,
            "play_blocked": True,
            "streaming_enabled": True
        }
    
    def _get_recent_calls(self) -> List[Dict]:
        """Get recent call history"""
        if not self.client:
            return [{"error": "Twilio client not initialized"}]
        
        try:
            calls = self.client.calls.list(limit=10)
            return [
                {
                    "sid": call.sid,
                    "to": call.to,
                    "from": call.from_,
                    "status": call.status,
                    "date_created": str(call.date_created)
                }
                for call in calls
            ]
        except Exception as e:
            return [{"error": f"Failed to fetch calls: {str(e)}"}]
    
    def _get_configuration(self) -> Dict:
        """Get service configuration"""
        return {
            "account_sid_set": bool(self.account_sid),
            "auth_token_set": bool(self.auth_token), 
            "phone_number": self.phone_number,
            "client_ready": bool(self.client),
            "audio_method": "streaming only (play blocked)",
            "ssl_configured": True,
            "server_domain": self.server_domain,
            "ssl_port": self.ssl_port,
            "base_url": self.base_url,
            "websocket_url": self.websocket_url
        }
    
    def _get_ssl_config(self) -> Dict:
        """Get SSL and self-hosting configuration"""
        return {
            "ssl_hosting": "self-hosted",
            "server_domain": self.server_domain,
            "ssl_port": self.ssl_port,
            "https_base_url": self.base_url,
            "websocket_base_url": self.websocket_url,
            "twiml_endpoint": f"{self.base_url}/twiml/mixed",
            "audio_stream_endpoint": f"{self.websocket_url}/audio/mixed-stream",
            "certificate_source": "tournament tracker hosted"
        }
    
    def _get_capabilities(self) -> List[str]:
        """Get service capabilities"""
        return [
            "Make outbound voice calls",
            "Generate TwiML responses",
            "Stream audio in real-time using <stream>",
            "Block deprecated play() commands",
            "Handle incoming call webhooks",
            "Integrate with tournament audio systems"
        ]
    
    def _make_call(self, to_number: str) -> Dict:
        """Make an outbound call"""
        if not self.client:
            return {"error": "Twilio client not initialized"}
        
        if not to_number:
            return {"error": "Phone number required"}
        
        try:
            # Generate TwiML URL for the call
            twiml_url = "http://your-server.com/twiml"  # Replace with actual URL
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=twiml_url
            )
            
            announcer.announce(
                "Twilio Call Initiated",
                [f"Call SID: {call.sid}", f"To: {to_number}", f"Status: {call.status}"]
            )
            
            return {
                "call_sid": call.sid,
                "to": to_number,
                "from": self.phone_number,
                "status": call.status
            }
        except Exception as e:
            return {"error": f"Call failed: {str(e)}"}
    
    def _setup_audio_stream(self, action: str) -> Dict:
        """Setup audio streaming configuration with self-hosted SSL"""
        # Extract WebSocket URL from action if provided, otherwise use self-hosted
        ws_url = None
        if 'ws://' in action or 'wss://' in action:
            parts = action.split()
            for part in parts:
                if part.startswith(('ws://', 'wss://')):
                    ws_url = part
                    break
        
        # Default to self-hosted WebSocket URL
        if not ws_url:
            ws_url = f"{self.websocket_url}/audio/stream"
        
        announcer.announce(
            "Twilio Audio Stream Setup",
            [
                "Configuring real-time audio streaming",
                f"WebSocket URL: {ws_url}",
                "Using self-hosted SSL certificate",
                "Use <stream> TwiML element for audio"
            ]
        )
        
        return {
            "streaming_configured": True,
            "websocket_url": ws_url,
            "ssl_hosted": True,
            "server_domain": self.server_domain,
            "audio_method": "streaming",
            "play_method": "blocked"
        }
    
    def _generate_twiml(self, data: Any = None) -> str:
        """Generate TwiML response with self-hosted streaming support"""
        response = VoiceResponse()
        
        # Example TwiML with self-hosted streaming (no play commands)
        if data and isinstance(data, dict):
            if 'message' in data:
                response.say(data['message'])
            
            if 'stream_url' in data:
                # Use Stream instead of Play
                stream = Stream(url=data['stream_url'])
                response.append(stream)
        else:
            # Default response with self-hosted streaming capability
            response.say("Welcome to tournament audio streaming.")
            
            # Add stream element for real-time audio from self-hosted server
            stream_url = f"{self.websocket_url}/audio/stream"
            stream = Stream(url=stream_url)
            response.append(stream)
        
        return str(response)
    
    def _format_for_discord(self, data: Any) -> str:
        """Format data for Discord output"""
        if isinstance(data, dict):
            if 'error' in data:
                return f"❌ Twilio Error: {data['error']}"
            elif 'call_sid' in data:
                return f"📞 Call initiated: {data['call_sid']}\n└ To: {data['to']}\n└ Status: {data['status']}"
            else:
                status = data.get('service', 'Twilio')
                return f"🎙️ {status} - {'✅ Ready' if data.get('client_initialized') else '❌ Not Ready'}"
        
        return f"🎙️ Twilio: {str(data)}"
    
    def _test_connection(self) -> Dict:
        """Test Twilio connection"""
        if not self.client:
            return {"test": "failed", "reason": "Client not initialized"}
        
        try:
            # Test by fetching account info
            account = self.client.api.accounts(self.account_sid).fetch()
            return {
                "test": "passed",
                "account_status": account.status,
                "account_type": account.type
            }
        except Exception as e:
            return {"test": "failed", "reason": str(e)}
    
    # Audio Sink Methods
    
    def _get_audio_sink_status(self) -> Dict:
        """Get audio sink specific status"""
        return {
            "service": "Twilio Audio Sink",
            "mixer_connected": bool(self.audio_mixer),
            "active_streams": len(self.streaming_threads),
            "active_calls": len(self.active_calls),
            "audio_queue_size": self.audio_queue.qsize(),
            "sink_ready": bool(self.client and self.audio_mixer)
        }
    
    def _get_active_calls(self) -> List[Dict]:
        """Get currently active streaming calls"""
        return [
            {
                "call_sid": call_id,
                "phone": call_info.get("phone", "unknown"),
                "streaming": call_id in self.streaming_threads,
                "started": call_info.get("started", "unknown")
            }
            for call_id, call_info in self.active_calls.items()
        ]
    
    def _get_mixer_status(self) -> Dict:
        """Get status of connected audio mixer"""
        if not self.audio_mixer:
            return {"error": "No audio mixer connected"}
        
        try:
            return {
                "mixer_connected": True,
                "mixer_type": "BonjourAudioMixer",
                "mixer_status": self.audio_mixer.get_status()
            }
        except Exception as e:
            return {"error": f"Failed to get mixer status: {str(e)}"}
    
    def _make_call_with_mixed_audio(self, to_number: str) -> Dict:
        """Make an outbound call with mixed audio from the mixer"""
        if not self.client:
            return {"error": "Twilio client not initialized"}
        
        if not self.audio_mixer:
            return {"error": "Audio mixer not connected - cannot stream mixed audio"}
        
        if not to_number:
            return {"error": "Phone number required"}
        
        try:
            # Generate self-hosted TwiML URL that will stream mixed audio
            twiml_url = f"{self.base_url}/twiml/mixed"
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=twiml_url
            )
            
            # Track this call for streaming
            self.active_calls[call.sid] = {
                "phone": to_number,
                "started": threading.current_thread().ident,
                "mixed_audio": True
            }
            
            announcer.announce(
                "Mixed Audio Call Initiated",
                [
                    f"Call SID: {call.sid}",
                    f"To: {to_number}",
                    f"Status: {call.status}",
                    "Will stream mixed audio from BonjourAudioMixer"
                ]
            )
            
            return {
                "call_sid": call.sid,
                "to": to_number,
                "from": self.phone_number,
                "status": call.status,
                "mixed_audio": True
            }
        except Exception as e:
            return {"error": f"Mixed audio call failed: {str(e)}"}
    
    def _start_mixed_audio_stream(self) -> Dict:
        """Start streaming mixed audio from the mixer"""
        if not self.audio_mixer:
            return {"error": "Audio mixer not connected"}
        
        try:
            # Start a streaming thread to pull audio from mixer
            stream_id = f"stream_{len(self.streaming_threads)}"
            
            stream_thread = threading.Thread(
                target=self._stream_mixed_audio_worker,
                args=(stream_id,),
                daemon=True
            )
            
            self.streaming_threads[stream_id] = stream_thread
            stream_thread.start()
            
            announcer.announce(
                "Mixed Audio Stream Started",
                [
                    f"Stream ID: {stream_id}",
                    "Pulling audio from BonjourAudioMixer",
                    "Ready to transmit via Twilio calls"
                ]
            )
            
            return {
                "stream_id": stream_id,
                "streaming": True,
                "mixer_connected": True
            }
        except Exception as e:
            return {"error": f"Failed to start mixed audio stream: {str(e)}"}
    
    def _stop_audio_streams(self) -> Dict:
        """Stop all active audio streams"""
        stopped_count = 0
        
        # Clear streaming threads (they're daemon threads so will stop)
        stopped_count += len(self.streaming_threads)
        self.streaming_threads.clear()
        
        # Clear active calls tracking
        self.active_calls.clear()
        
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        announcer.announce(
            "Audio Streams Stopped",
            [f"Stopped {stopped_count} streams", "All calls cleared", "Audio queue emptied"]
        )
        
        return {
            "stopped_streams": stopped_count,
            "active_calls": 0,
            "queue_cleared": True
        }
    
    def _generate_twiml_with_mixed_audio(self, data: Any = None) -> str:
        """Generate TwiML response that streams mixed audio from the mixer"""
        response = VoiceResponse()
        
        if not self.audio_mixer:
            response.say("Audio mixer not available.")
            return str(response)
        
        # Add Say element if there's a message
        if data and isinstance(data, dict) and 'message' in data:
            response.say(data['message'])
        
        # Set up streaming from the self-hosted audio mixer
        if data and 'stream_url' in data:
            stream_url = data['stream_url']
        else:
            stream_url = f"{self.websocket_url}/audio/mixed-stream"
        
        # Use Stream element to stream mixed audio from self-hosted endpoint
        stream = Stream(url=stream_url)
        response.append(stream)
        
        announcer.announce(
            "TwiML Generated for Mixed Audio",
            [
                "TwiML includes <stream> element",
                f"Stream URL: {stream_url}",
                "Will receive mixed audio from BonjourAudioMixer"
            ]
        )
        
        return str(response)
    
    def _process_audio_stream(self):
        """Background thread that processes audio from the mixer"""
        while True:
            try:
                if self.audio_mixer and self.active_calls:
                    # Get audio chunk from mixer
                    try:
                        audio_chunk = self.audio_mixer.get_music_chunk(320)  # 20ms at 8kHz
                        if audio_chunk:
                            # Queue audio for active calls
                            self.audio_queue.put({
                                'type': 'mixed_audio',
                                'data': audio_chunk,
                                'timestamp': threading.current_thread().ident
                            })
                    except Exception as e:
                        # Audio mixer error, continue silently
                        pass
                
                # Small delay to prevent high CPU usage
                import time
                time.sleep(0.02)  # 20ms
                
            except Exception as e:
                announcer.announce(
                    "Audio Processing Error",
                    [f"Error in audio stream processing: {str(e)}"]
                )
                import time
                time.sleep(1)  # Wait before retrying
    
    def _stream_mixed_audio_worker(self, stream_id: str):
        """Worker thread that streams mixed audio to Twilio"""
        announcer.announce(
            f"Audio Stream Worker Started",
            [f"Stream ID: {stream_id}", "Processing mixed audio from queue"]
        )
        
        while stream_id in self.streaming_threads:
            try:
                # Get audio from queue
                audio_item = self.audio_queue.get(timeout=0.1)
                
                if audio_item['type'] == 'mixed_audio':
                    # In real implementation, this would stream to Twilio
                    # For now, just process the audio data
                    audio_data = audio_item['data']
                    # Would send audio_data to active Twilio calls
                    
            except queue.Empty:
                continue
            except Exception as e:
                announcer.announce(
                    f"Stream Worker Error",
                    [f"Stream {stream_id} error: {str(e)}"]
                )
                break
        
        announcer.announce(
            f"Audio Stream Worker Stopped",
            [f"Stream ID: {stream_id}"]
        )


# Global service instance
twilio_service = TwilioService()

# Convenience functions for external use
def ask(query: str, **kwargs) -> Any:
    """Query Twilio service"""
    return twilio_service.ask(query, **kwargs)

def tell(format: str, data: Any = None) -> str:
    """Format Twilio data"""
    return twilio_service.tell(format, data)

def do(action: str, **kwargs) -> Any:
    """Perform Twilio action"""
    return twilio_service.do(action, **kwargs)


if __name__ == "__main__":
    """Test the Twilio service"""
    print("🎙️ Twilio Service Test")
    print("=" * 40)
    
    # Test service status
    print("\n📊 Service Status:")
    print(tell('text', ask('status')))
    
    # Test blocked play command
    print("\n🚫 Testing blocked play() command:")
    result = do("play audio.mp3")
    print(result)
    
    # Test TwiML generation
    print("\n📋 Sample TwiML:")
    twiml = tell('twiml', {'message': 'Hello from tournament tracker'})
    print(twiml)
    
    # Test configuration
    print("\n⚙️ Configuration:")
    config = ask('config')
    print(tell('json', config))