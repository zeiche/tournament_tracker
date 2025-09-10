#!/usr/bin/env python3
"""
Twilio Rickroll Fallback Server
When the main script fails, Twilio falls back to this and rickrolls the caller
"""

from flask import Flask, Response
import sys
import os

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
@app.route("/rickroll", methods=['GET', 'POST'])
def rickroll():
    """Ultimate rickroll fallback when main script fails"""
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">We're no strangers to love. You know the rules and so do I.</Say>
    <Play>https://www.soundjay.com/misc/sounds/never-gonna-give-you-up.mp3</Play>
    <Say voice="alice">Never gonna give you up, never gonna let you down!</Say>
    <Hangup/>
</Response>"""
    return Response(twiml, mimetype='application/xml')

@app.route("/health")
def health():
    """Health check"""
    return "Rickroll fallback ready! 🎵"

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8089
    print(f"🎵 Starting Rickroll Fallback Server on port {port}")
    print(f"📞 When main script fails, callers get rickrolled!")
    print(f"🔗 Fallback URL: http://your-domain:{port}/rickroll")
    
    app.run(host='0.0.0.0', port=port, debug=False)