#!/usr/bin/env python3
"""
twilio_simple_voice_bridge.py - Minimal Twilio bridge (like Discord)
Just receives speech and forwards to handlers. That's it.
Uses audio service for continuous streaming.
"""

from flask import Flask, request, Response, send_file
from twilio.twiml.voice_response import VoiceResponse, Connect, Start, Stream
from twilio.rest import Client
import os
import asyncio
import websockets
import json
import base64
import threading
from pathlib import Path
from capability_announcer import announcer
from bonjour_audio_mixer import BonjourAudioMixer
from audio_service import AudioService

class SimpleTwilioBridge:
    """Minimal Twilio bridge with audio service integration"""
    
    def __init__(self, gather_timeout=30):
        # Configurable timeout for speech gathering
        self.gather_timeout = gather_timeout
        
        # Load credentials
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not self.account_sid or not self.auth_token:
            env_file = Path(__file__).parent / '.env'
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if 'TWILIO_ACCOUNT_SID=' in line:
                            self.account_sid = line.split('=', 1)[1].strip().strip('"')
                        elif 'TWILIO_AUTH_TOKEN=' in line:
                            self.auth_token = line.split('=', 1)[1].strip().strip('"')
                        elif 'TWILIO_PHONE_NUMBER=' in line:
                            self.phone_number = line.split('=', 1)[1].strip().strip('"')
        
        # Flask app for webhooks
        self.app = Flask(__name__)
        
        # Speech handlers - anyone can register
        self.speech_handlers = []
        
        # Queue for speech to be sent via WebSocket
        import queue
        self.speech_queue = queue.Queue()
        
        # Get BONJOUR audio mixer - IT handles everything!
        self.audio_mixer = BonjourAudioMixer()
        
        # Get audio service for mixing
        self.audio_service = AudioService()
        
        # Initialize Twilio client for making calls
        self.twilio_client = Client(self.account_sid, self.auth_token) if self.account_sid and self.auth_token else None
        
        # Announce to start continuous music via bonjour
        announcer.announce(
            "TWILIO_NEEDS_MUSIC",
            [
                "Requesting continuous background music",
                "Using BonjourAudioMixer for LOCAL mixing - NOT Twilio API!",
                "Music should start streaming automatically",
                "NO play() API calls - just bonjour announcements!"
            ]
        )
        
        # Announce that we want continuous music (bonjour services will respond)
        announcer.announce(
            "START_CONTINUOUS_MUSIC",
            [
                "Starting continuous background music stream",
                "Music will play in background during calls",
                "Audio mixer will handle mixing speech over music"
            ]
        )
        
        # Announce ourselves with ALL capabilities
        announcer.announce(
            "SimpleTwilioBridge",
            [
                "I'm a Twilio bridge with full phone capabilities",
                "I forward speech to handlers",
                f"Phone: {self.phone_number}",
                f"⏰ Speech timeout: {self.gather_timeout} seconds (configurable!)",
                "Audio service streams music via bonjour",
                "🆕 I can MAKE phone calls!",
                "🆕 Claude can call you: bridge.make_call(phone_number, message)",
                "🆕 Try: 'Claude, call me at 555-1234 and tell me about tournaments'",
                "I handle incoming and outgoing calls",
                "Methods: make_call(), send_sms(), get_call_status()",
                "Create with SimpleTwilioBridge(gather_timeout=60) for longer calls"
            ]
        )
        
        @self.app.route('/voice', methods=['POST'])
        def handle_voice():
            """Handle voice with Twilio response"""
            call_sid = request.values.get('CallSid')
            from_number = request.values.get('From')
            speech = request.values.get('SpeechResult')
            
            response = VoiceResponse()
            
            # FIRST: Start music BEFORE any speech via bonjour announcement
            if not speech:  # First time on call
                announcer.announce(
                    "CALL_STARTED_NEED_MUSIC",
                    [
                        "New call started - need background music NOW",
                        "Music must play BEFORE bot speaks",
                        "Using bonjour audio services"
                    ]
                )
                # Tell audio mixer to start music immediately
                self.audio_mixer.start_continuous_music()
            
            # Announce what we received
            announcer.announce(
                "TWILIO_SPEECH",
                [
                    f"From: {from_number}",
                    f"Said: {speech or 'No speech yet'}",
                    f"CallSid: {call_sid}"
                ]
            )
            
            # Process speech if we have it
            response_text = None
            if speech:
                for handler in self.speech_handlers:
                    try:
                        handler_response = handler(speech, from_number)
                        if handler_response:
                            response_text = handler_response
                            break
                    except Exception as e:
                        print(f"Handler error: {e}")
            
            # First time on call - play welcome with background music
            if not speech:
                # Play welcome message with background music mixed in
                welcome_text = "Welcome to Try Hard Tournament Tracker. Say something to test the audio mixing."
                
                # Stream the mixed audio directly
                import urllib.parse
                encoded_text = urllib.parse.quote(welcome_text)
                response.play(url=f'http://64.111.98.139:8082/mixed/{encoded_text}')
                
                # Announce we're playing audio
                announcer.announce(
                    "TWILIO_AUDIO_PLAYING",
                    [
                        "Playing welcome message with background music",
                        "Audio mixed in real-time via streaming",
                        "Using HTTP streaming endpoint"
                    ]
                )
            
            # Process responses - play with background music
            if response_text:
                # Play the response with background music
                import urllib.parse
                encoded_response = urllib.parse.quote(response_text)
                response.play(url=f'http://64.111.98.139:8082/mixed/{encoded_response}')
            
            # Set up speech gathering with configurable timeout
            gather = response.gather(
                input='speech',
                timeout=self.gather_timeout,  # Use configurable timeout
                speech_timeout='auto',
                action='/voice',
                language='en-US',
                enhanced=True,
                speechModel='phone_call'
            )
            
            # NO PLAY API - bonjour mixer handles audio locally!
            
            return str(response)
        
        @self.app.route('/continuous_music', methods=['GET'])
        def stream_continuous_music():
            """Stream from BONJOUR mixer - NOT Twilio!"""
            def generate():
                # Get mixed stream from bonjour mixer
                for chunk in self.audio_mixer.get_mixed_stream():
                    yield chunk
            
            return Response(generate(), mimetype='audio/wav')
        
        @self.app.route('/mixed/<text>', methods=['GET'])
        def serve_mixed_audio(text):
            """Generate and serve mixed audio (speech + music) on the fly"""
            # Use audio service to mix text with background music - returns generator
            def generate():
                for chunk in self.audio_service.mix_audio(
                    speech_text=text,
                    output_format='wav',
                    ducking=True,
                    duck_level=0.3
                ):
                    yield chunk
            
            return Response(generate(), mimetype='audio/wav')
        
        @self.app.route('/serve_mixed/<filename>', methods=['GET'])
        def serve_audio_file(filename):
            """Serve pre-generated mixed audio files"""
            import tempfile
            file_path = os.path.join(tempfile.gettempdir(), filename)
            if os.path.exists(file_path):
                return send_file(file_path, mimetype='audio/wav')
            # If not in temp, check audio service temp dir
            file_path = os.path.join(self.audio_service.temp_dir, filename)
            if os.path.exists(file_path):
                return send_file(file_path, mimetype='audio/wav')
            return "Audio file not found", 404
        
        @self.app.route('/outbound_message', methods=['GET', 'POST'])
        def outbound_message():
            """Handle outbound call with custom message"""
            message = request.values.get('message', 'Hello! This is Claude calling from Try Hard Tournament Tracker.')
            
            response = VoiceResponse()
            
            # Stream mixed audio directly from the URL endpoint
            # The /mixed/<text> endpoint now streams the audio
            import urllib.parse
            encoded_message = urllib.parse.quote(message)
            response.play(url=f'http://64.111.98.139:8082/mixed/{encoded_message}')
            
            # Pause and ask if they want to hear more
            response.pause(length=2)
            response.say("Press 1 to hear about recent tournaments, or hang up.", voice='alice')
            
            return str(response)
    
    def make_call(self, to_number: str, message: str = None, url: str = None):
        """
        Make an outbound phone call
        Claude can use this to call users!
        """
        if not self.twilio_client:
            return {"error": "Twilio client not configured"}
        
        try:
            # Clean phone number
            to_number = ''.join(filter(str.isdigit, to_number))
            if not to_number.startswith('+'):
                if not to_number.startswith('1'):
                    to_number = '1' + to_number
                to_number = '+' + to_number
            
            # Use provided URL or create TwiML for message
            if not url:
                url = f'http://64.111.98.139:8082/outbound_message?message={message or "Hello from Claude!"}'
            
            # Make the call
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=url
            )
            
            # Announce the call
            announcer.announce(
                "OUTBOUND_CALL",
                [
                    f"📞 Making call to: {to_number}",
                    f"Message: {message[:50] if message else 'Default greeting'}...",
                    f"Call SID: {call.sid}",
                    "Claude is calling someone!"
                ]
            )
            
            return {
                "status": "success",
                "call_sid": call.sid,
                "to": to_number,
                "message": message
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def send_sms(self, to_number: str, body: str):
        """Send an SMS message"""
        if not self.twilio_client:
            return {"error": "Twilio client not configured"}
        
        try:
            message = self.twilio_client.messages.create(
                body=body,
                from_=self.phone_number,
                to=to_number
            )
            
            announcer.announce(
                "SMS_SENT",
                [f"📱 SMS sent to {to_number}", f"Message: {body[:50]}..."]
            )
            
            return {"status": "success", "message_sid": message.sid}
        except Exception as e:
            return {"error": str(e)}
    
    def register_handler(self, handler):
        """Register a speech handler"""
        self.speech_handlers.append(handler)
        announcer.announce(
            "SimpleTwilioBridge",
            [f"Registered handler: {handler.__name__}"]
        )
    
    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connection from Twilio for bidirectional audio streaming"""
        announcer.announce(
            "WEBSOCKET_CONNECTED",
            ["WebSocket connected - starting bidirectional audio stream"]
        )
        
        # Start streaming background music immediately
        music_task = asyncio.create_task(self.stream_background_music(websocket))
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data['event'] == 'connected':
                    print("WebSocket connected to Twilio")
                    
                elif data['event'] == 'start':
                    print(f"Stream started: {data['streamSid']}")
                    # Music is already streaming via the background task
                    
                elif data['event'] == 'media':
                    # Received audio from caller (we can ignore for now)
                    pass
                    
                elif data['event'] == 'stop':
                    print("Stream stopped")
                    break
                    
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            music_task.cancel()
    
    async def stream_background_music(self, websocket):
        """Stream continuous background music via WebSocket"""
        try:
            # Get continuous stream from audio service
            for chunk in self.audio_service.get_continuous_stream():
                # Convert to mulaw and base64 for Twilio
                mulaw_audio = self.convert_to_mulaw(chunk)
                encoded = base64.b64encode(mulaw_audio).decode('utf-8')
                
                # Send media message to Twilio
                media_msg = {
                    "event": "media",
                    "streamSid": "outbound",
                    "media": {
                        "payload": encoded
                    }
                }
                await websocket.send(json.dumps(media_msg))
                
                # Check for speech to mix in
                if not self.speech_queue.empty():
                    text = self.speech_queue.get()
                    # Mix speech with music via audio service - returns generator
                    for chunk in self.audio_service.mix_audio(
                        speech_text=text,
                        output_format='wav',
                        ducking=True,
                        duck_level=0.3
                    ):
                        # Convert to mulaw and send via WebSocket
                        mulaw_chunk = self.convert_to_mulaw(chunk)
                        encoded = base64.b64encode(mulaw_chunk).decode('utf-8')
                        media_msg = {
                            "event": "media",
                            "streamSid": "outbound",
                            "media": {
                                "payload": encoded
                            }
                        }
                        await websocket.send(json.dumps(media_msg))
                        await asyncio.sleep(0.02)  # 20ms chunks
                    
                await asyncio.sleep(0.02)  # 20ms chunks
        except asyncio.CancelledError:
            pass
    
    def convert_to_mulaw(self, pcm_data):
        """Convert PCM audio to mulaw format for Twilio"""
        # This would use audioop or similar to convert
        # For now, return the data as-is
        return pcm_data
    
    async def send_audio_file(self, websocket, file_path):
        """Send an audio file via WebSocket"""
        with open(file_path, 'rb') as f:
            audio_data = f.read()
            # Send in chunks
            chunk_size = 320  # 20ms at 8kHz
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                encoded = base64.b64encode(chunk).decode('utf-8')
                media_msg = {
                    "event": "media",
                    "streamSid": "outbound",
                    "media": {
                        "payload": encoded
                    }
                }
                await websocket.send(json.dumps(media_msg))
                await asyncio.sleep(0.02)
    
    def run(self, port=8082, ws_port=8083):
        """Run the webhook server and WebSocket server"""
        print(f"🔌 Simple Twilio bridge running on port {port}")
        print(f"🌐 WebSocket server on port {ws_port}")
        print(f"📱 Phone: {self.phone_number}")
        print(f"🎤 Voice recognition: ENABLED")
        print(f"🎵 Music: Streaming via WebSocket from audio service")
        
        # Start WebSocket server in a thread
        def run_websocket():
            async def start():
                await websockets.serve(self.handle_websocket, '0.0.0.0', ws_port)
                await asyncio.Future()  # Run forever
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start())
        
        ws_thread = threading.Thread(target=run_websocket, daemon=True)
        ws_thread.start()
        
        # Run Flask app
        self.app.run(host='0.0.0.0', port=port, debug=False)

# Global instance
_bridge = None

def get_bridge():
    """Get or create bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = SimpleTwilioBridge()
    return _bridge

if __name__ == "__main__":
    bridge = get_bridge()
    
    # Register the tournament handler that uses gamer_tags
    from tournament_voice_handler import handle_tournament_speech
    bridge.register_handler(handle_tournament_speech)
    print("✅ Tournament handler registered")
    
    print("📱 Call 878-TRY-HARD to test!")
    bridge.run(port=8082)