#!/usr/bin/env python3
"""
Test call simulation - simulates a call flow with speech
"""
import sys
import os
import asyncio
import json
import base64
import websockets
import audioop
import numpy as np
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def simulate_twilio_call():
    """Simulate a Twilio WebSocket call to test the speech flow"""
    print("📞 Simulating Twilio call to test vosk integration...")
    
    # Connect to the WebSocket server (SSL required)
    uri = "wss://localhost:8094"
    
    try:
        print(f"🔌 Connecting to {uri}...")
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Send connected event
            connected_event = {
                "event": "connected",
                "protocol": "Call",
                "version": "1.0.0"
            }
            await websocket.send(json.dumps(connected_event))
            print("📡 Sent connected event")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Send start event
            start_event = {
                "event": "start",
                "sequenceNumber": "1",
                "start": {
                    "callSid": "test-call-123",
                    "streamSid": "test-stream-456",
                    "accountSid": "test-account",
                    "customParameters": {}
                },
                "streamSid": "test-stream-456"
            }
            await websocket.send(json.dumps(start_event))
            print("📡 Sent start event - waiting for announcement to end...")
            
            # Wait for announcement to end (simulate listening)
            await asyncio.sleep(5)
            print("🤐 Announcement should be done, now 'saying' something...")
            
            # Generate speech-like audio (higher amplitude than silence)
            sample_rate = 8000
            duration = 3.0  # 3 seconds of "speech"
            samples = int(sample_rate * duration)
            
            # Generate audio that simulates speech pattern
            t = np.linspace(0, duration, samples)
            speech_audio = (np.sin(2 * np.pi * 300 * t) * 0.3 +  # base tone
                           np.sin(2 * np.pi * 500 * t) * 0.2 +   # harmonic
                           np.random.normal(0, 0.1, samples)     # noise
                          ) * 10000  # scale up
            
            speech_audio = speech_audio.astype(np.int16)
            
            # Convert to mulaw
            speech_mulaw = audioop.lin2ulaw(speech_audio.tobytes(), 2)
            
            # Send audio in chunks (160 bytes each, like Twilio)
            chunk_size = 160
            sequence = 1
            
            for i in range(0, len(speech_mulaw), chunk_size):
                chunk = speech_mulaw[i:i + chunk_size]
                if len(chunk) < chunk_size:
                    # Pad last chunk
                    chunk += b'\xff' * (chunk_size - len(chunk))
                
                # Encode as base64
                payload = base64.b64encode(chunk).decode('utf-8')
                
                media_event = {
                    "event": "media",
                    "sequenceNumber": str(sequence),
                    "media": {
                        "track": "inbound",
                        "chunk": str(sequence),
                        "timestamp": str(int(time.time() * 1000)),
                        "payload": payload
                    },
                    "streamSid": "test-stream-456"
                }
                
                await websocket.send(json.dumps(media_event))
                sequence += 1
                
                # Small delay between chunks
                await asyncio.sleep(0.02)  # 20ms
            
            print("🎤 Finished sending 'speech' audio")
            print("⏳ Waiting for transcription...")
            
            # Wait for transcription processing
            await asyncio.sleep(5)
            
            # Send stop event
            stop_event = {
                "event": "stop",
                "sequenceNumber": str(sequence),
                "streamSid": "test-stream-456"
            }
            await websocket.send(json.dumps(stop_event))
            print("📡 Sent stop event")
            
            print("✅ Call simulation complete!")
            print("📡 Check Bonjour announcements and lightweight service for transcription results")
            
    except Exception as e:
        print(f"❌ Error during call simulation: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_twilio_call())