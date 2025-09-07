#!/usr/bin/env python3
"""
twiml_server.py - Simple TwiML server that actually works
"""

from flask import Flask, Response
import subprocess

app = Flask(__name__)

@app.route('/voice.xml', methods=['GET', 'POST'])
def voice():
    """Return TwiML for inbound calls"""
    
    # Get some tournament data
    tournament_info = "West Coast Warzone had 256 players"
    player_info = "Top player is West with 45 wins"
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hey! Welcome to the tournament tracker chat system!</Say>
    <Pause length="1"/>
    <Say voice="alice">I'm Claude, and I can tell you about fighting game tournaments.</Say>
    <Pause length="1"/>
    <Say voice="alice">Here's the latest: {tournament_info}</Say>
    <Pause length="1"/>
    <Say voice="alice">Player update: {player_info}</Say>
    <Pause length="1"/>
    <Say voice="alice">This call is being handled by our polymorphic system. Pretty cool, right?</Say>
    <Pause length="1"/>
    <Say voice="alice">Call back anytime for more tournament updates! Backyard try-hards forever!</Say>
</Response>'''
    
    return Response(twiml, mimetype='text/xml')

@app.route('/', methods=['GET'])
def index():
    return "Tournament Tracker TwiML Server Active"

if __name__ == "__main__":
    print("🎯 TwiML Server for Tournament Tracker")
    print("📞 Serves TwiML at /voice.xml")
    print("🔗 Running on port 8086")
    app.run(host='0.0.0.0', port=8086, debug=False)