#!/usr/bin/env python3
"""
TwiML HTTPS Server - Serves TwiML responses over HTTPS for Twilio webhooks.
Uses Let's Encrypt certificates for valid SSL.
"""

from flask import Flask, Response, request, jsonify
import ssl
import os
from pathlib import Path

app = Flask(__name__)

# Configuration
HTTPS_PORT = 8445  # Changed from 8443 which is in use
HTTP_PORT = 8088  # Changed from 8086 which is in use

# WebSocket URL for streaming (using SSL proxy)
WS_URL = os.environ.get('TWILIO_WS_URL', 'wss://www.danpeterson.net:8444/')

@app.route('/twiml/voice', methods=['GET', 'POST'])
def voice_webhook():
    """Main voice webhook endpoint for Twilio."""
    
    # Get call information
    from_number = request.values.get('From', 'Unknown')
    to_number = request.values.get('To', 'Unknown')
    call_sid = request.values.get('CallSid', '')
    
    print(f"📞 Incoming call from {from_number} to {to_number}")
    print(f"🆔 Call SID: {call_sid}")
    
    # Generate TwiML response
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Welcome to the tournament tracker system.</Say>
    <Gather input="speech dtmf" timeout="3" numDigits="1" action="/twiml/gather">
        <Say voice="alice">
            Press 1 or say tournaments for tournament information.
            Press 2 or say players for player rankings.
            Press 3 or say help for assistance.
        </Say>
    </Gather>
    <Say voice="alice">We didn't receive any input. Goodbye!</Say>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/twiml/gather', methods=['POST'])
def gather_webhook():
    """Handle gathered input from user."""
    
    # Get the digits or speech input
    digits = request.values.get('Digits', '')
    speech = request.values.get('SpeechResult', '')
    
    print(f"🎤 Received input - Digits: {digits}, Speech: {speech}")
    
    # Route based on input
    if '1' in digits or 'tournament' in speech.lower():
        response_text = "Getting latest tournament information..."
        # TODO: Query tournament data
    elif '2' in digits or 'player' in speech.lower():
        response_text = "Loading player rankings..."
        # TODO: Query player data
    elif '3' in digits or 'help' in speech.lower():
        response_text = "This system provides tournament and player information for the fighting game community."
    else:
        response_text = "I didn't understand that. Please try again."
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{response_text}</Say>
    <Redirect>/twiml/voice</Redirect>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/twiml/sms', methods=['POST'])
def sms_webhook():
    """Handle incoming SMS messages."""
    
    from_number = request.values.get('From', 'Unknown')
    body = request.values.get('Body', '')
    
    print(f"📱 SMS from {from_number}: {body}")
    
    # Process the message
    response_text = "Tournament Tracker: Message received. Reply HELP for commands."
    
    # TODO: Process SMS commands
    if body.upper() == 'HELP':
        response_text = "Commands: TOURNAMENTS, PLAYERS, NEXT, STATS"
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_text}</Message>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/twiml/stream', methods=['GET', 'POST'])
def stream_webhook():
    """WebSocket streaming endpoint for real-time audio."""
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Connecting to tournament tracker real-time system...</Say>
    <Connect>
        <Stream url="{WS_URL}">
            <Parameter name="service" value="tournament_tracker"/>
            <Parameter name="mode" value="interactive"/>
        </Stream>
    </Connect>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/twiml/status', methods=['POST'])
def status_callback():
    """Handle status callbacks from Twilio."""
    
    call_sid = request.values.get('CallSid', '')
    status = request.values.get('CallStatus', '')
    
    print(f"📊 Call {call_sid} status: {status}")
    
    return jsonify({"status": "received"})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "twiml_https_server",
        "https": True,
        "endpoints": [
            "/twiml/voice",
            "/twiml/gather", 
            "/twiml/sms",
            "/twiml/stream",
            "/twiml/status"
        ]
    })

@app.route('/', methods=['GET'])
def index():
    """Status page."""
    return f"""
    <h1>Tournament Tracker TwiML HTTPS Server</h1>
    <p>✅ HTTPS Enabled with Let's Encrypt</p>
    <h2>Available Endpoints:</h2>
    <ul>
        <li><a href="/twiml/voice">/twiml/voice</a> - Main voice webhook</li>
        <li>/twiml/gather - Handle user input</li>
        <li>/twiml/sms - SMS webhook</li>
        <li><a href="/twiml/stream">/twiml/stream</a> - WebSocket streaming</li>
        <li>/twiml/status - Status callbacks</li>
        <li><a href="/health">/health</a> - Health check</li>
    </ul>
    <h3>Configure in Twilio:</h3>
    <p>Voice URL: <code>https://64.111.98.139:{HTTPS_PORT}/twiml/voice</code></p>
    <p>SMS URL: <code>https://64.111.98.139:{HTTPS_PORT}/twiml/sms</code></p>
    <p>Status Callback: <code>https://64.111.98.139:{HTTPS_PORT}/twiml/status</code></p>
    """

def create_ssl_context():
    """Create SSL context with certificates."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Try IP certificate first (for Twilio)
    ip_cert_path = Path(__file__).parent / "ip_cert.pem"
    ip_key_path = Path(__file__).parent / "ip_key.pem"
    
    # Fallback to Let's Encrypt certificates
    le_cert_path = Path(__file__).parent / "fullchain.pem"
    le_key_path = Path(__file__).parent / "privkey.pem"
    
    if ip_cert_path.exists() and ip_key_path.exists():
        context.load_cert_chain(ip_cert_path, ip_key_path)
        print(f"✅ IP address certificates loaded (self-signed)")
        return context
    elif le_cert_path.exists() and le_key_path.exists():
        context.load_cert_chain(le_cert_path, le_key_path)
        print(f"✅ Let's Encrypt certificates loaded")
        return context
    else:
        print(f"❌ No certificates found")
        return None

if __name__ == "__main__":
    import sys
    
    # Check for --http flag to force HTTP mode
    use_http = '--http' in sys.argv
    
    # Try to create SSL context
    ssl_context = create_ssl_context() if not use_http else None
    
    if ssl_context and not use_http:
        print(f"🚀 Starting TwiML HTTPS Server")
        print(f"🔒 HTTPS enabled on port {HTTPS_PORT}")
        print(f"🌐 Configure Twilio webhook: https://www.danpeterson.net:{HTTPS_PORT}/twiml/voice")
        
        # Run with SSL
        app.run(
            host='0.0.0.0',
            port=HTTPS_PORT,
            ssl_context=ssl_context,
            debug=False
        )
    else:
        print(f"📡 Running TwiML HTTP Server (IP-accessible)")
        print(f"🌐 HTTP server on port {HTTP_PORT}")
        print(f"⚠️  Configure Twilio webhook: http://64.111.98.139:{HTTP_PORT}/twiml/voice")
        print(f"⚠️  Note: HTTP is less secure than HTTPS")
        app.run(
            host='0.0.0.0',
            port=HTTP_PORT,
            debug=False
        )