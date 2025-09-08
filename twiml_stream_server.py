#!/usr/bin/env python3
"""
TwiML server with Stream support for real-time audio.
"""

from flask import Flask, Response, request
import os

app = Flask(__name__)

# Get WebSocket URL from environment or use default
# Note: Using ws:// (not wss://) since we don't have SSL configured
WS_URL = os.environ.get('TWILIO_WS_URL', 'ws://64.111.98.139:8087/')

@app.route('/voice-stream.xml', methods=['GET', 'POST'])
def voice_stream():
    """Return TwiML with bidirectional Stream for real-time interaction."""
    
    # Get caller info if available
    from_number = request.values.get('From', 'Unknown')
    call_sid = request.values.get('CallSid', '')
    
    # Use SSL proxy on port 8443 for secure WebSocket
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Connecting to tournament tracker real-time system...</Say>
    <Connect>
        <Stream url="wss://64.111.98.139:8443/">
            <Parameter name="caller" value="{from_number}"/>
            <Parameter name="mode" value="tournament_chat"/>
        </Stream>
    </Connect>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/voice-stream-inbound.xml', methods=['GET', 'POST'])
def voice_stream_inbound():
    """Inbound-only stream for listening to caller."""
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Start>
        <Stream url="{WS_URL}" track="inbound_track">
            <Parameter name="mode" value="listen_only"/>
        </Stream>
    </Start>
    <Say voice="alice">Tournament tracker is listening. Ask me about tournaments!</Say>
    <Pause length="10"/>
    <Say voice="alice">Thanks for calling!</Say>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/voice-stream-both.xml', methods=['GET', 'POST'])
def voice_stream_both():
    """Stream both inbound and outbound tracks."""
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Start>
        <Stream url="{WS_URL}" track="both_tracks">
            <Parameter name="mode" value="full_duplex"/>
        </Stream>
    </Start>
    <Say voice="alice">Full duplex streaming active. Tournament data loading...</Say>
    <Play>http://demo.twilio.com/docs/classic.mp3</Play>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/voice-legacy.xml', methods=['GET', 'POST'])
def voice_legacy():
    """Legacy TwiML without streaming (fallback)."""
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Tournament tracker voice system. Streaming not available.</Say>
    <Say voice="alice">Call back later for real-time updates!</Say>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/', methods=['GET'])
def index():
    """Status page."""
    return """
    <h1>Tournament Tracker TwiML Stream Server</h1>
    <h2>Available Endpoints:</h2>
    <ul>
        <li><a href="/voice-stream.xml">/voice-stream.xml</a> - Bidirectional streaming (recommended)</li>
        <li><a href="/voice-stream-inbound.xml">/voice-stream-inbound.xml</a> - Inbound only</li>
        <li><a href="/voice-stream-both.xml">/voice-stream-both.xml</a> - Both tracks</li>
        <li><a href="/voice-legacy.xml">/voice-legacy.xml</a> - Legacy without streaming</li>
    </ul>
    <p>WebSocket URL: {}</p>
    """.format(WS_URL)

if __name__ == "__main__":
    print("🎯 TwiML Stream Server for Tournament Tracker")
    print("📞 Bidirectional stream at /voice-stream.xml")
    print(f"🔗 WebSocket URL: {WS_URL}")
    print("🌐 Running on port 8086")
    app.run(host='0.0.0.0', port=8086, debug=False)