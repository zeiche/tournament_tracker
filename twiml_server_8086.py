#!/usr/bin/env python3
"""
Simple TwiML server on port 8086 to serve voice-stream.xml
"""

from flask import Flask, Response
import os

app = Flask(__name__)

@app.route("/voice-stream.xml", methods=['GET', 'POST'])
def voice_stream():
    """Serve the voice stream XML that connects to our WebSocket server"""
    
    # Read our tournament_inbound.xml content
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://0-page.com:8088/" />
    </Connect>
</Response>"""
    
    return Response(xml_content, mimetype='application/xml')

@app.route("/", methods=['GET', 'POST'])
def root():
    """Root endpoint redirects to voice-stream.xml"""
    return voice_stream()

if __name__ == "__main__":
    print("🔗 Starting TwiML server on port 8086")
    print("📄 Serving voice-stream.xml that connects to WebSocket stream server")
    print(f"🌐 URL: http://64.111.98.139:8086/voice-stream.xml")
    
    app.run(host='0.0.0.0', port=8086, debug=False)