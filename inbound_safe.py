#!/usr/bin/env python3
"""
inbound_safe.py - Safe inbound handler with error logging
"""

from flask import Flask, request, Response
import sys
import traceback

app = Flask(__name__)

@app.route('/voice', methods=['POST', 'GET'])
def voice():
    """Ultra-safe voice handler"""
    try:
        print(f"📞 Incoming call request", file=sys.stderr)
        print(f"   From: {request.values.get('From', 'unknown')}", file=sys.stderr)
        print(f"   Method: {request.method}", file=sys.stderr)
        print(f"   Headers: {dict(request.headers)}", file=sys.stderr)
        
        # Import here to catch import errors
        from twilio.twiml.voice_response import VoiceResponse
        
        response = VoiceResponse()
        digits = request.values.get('Digits', '')
        
        if digits:
            if digits == '1':
                response.say("Recent tournament had 200 players.", voice='matthew')
            elif digits == '2':
                # Announce top 8 players in reverse order (8th to 1st)
                response.say("Here are the top 8 players, starting from 8th place:", voice='matthew')
                response.pause(length=1)
                
                # Top 8 players data (would normally come from database)
                top_8 = [
                    ("8th", "Kuba"),
                    ("7th", "Jedi"),
                    ("6th", "Hank"),
                    ("5th", "Beast"),
                    ("4th", "Snake"),
                    ("3rd", "Shadow"),
                    ("2nd", "JLPC with 38 wins"),
                    ("1st", "West with 45 wins")
                ]
                
                for place, player in top_8:
                    response.say(f"{place} place: {player}", voice='matthew')
                    response.pause(length=0.5)
            else:
                response.say("Invalid option.", voice='alice')
            response.redirect('/voice')
        else:
            response.say("Tournament tracker. Press 1 or 2.", voice='brian')
            response.gather(numDigits=1, action='/voice')
            response.say("Goodbye.", voice='brian')
        
        xml = str(response)
        print(f"✅ Returning TwiML: {xml[:100]}...", file=sys.stderr)
        return Response(xml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ ERROR in voice handler: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        # Return minimal valid TwiML even on error
        return '<?xml version="1.0" encoding="UTF-8"?><Response><Say>Error occurred. Please try again.</Say></Response>'

@app.route('/status', methods=['GET'])
def status():
    return "OK"

if __name__ == "__main__":
    print("🎯 Safe Inbound Handler starting on port 8082...")
    print("📞 Webhook: http://64.111.98.139:8082/voice")
    sys.stdout.flush()
    app.run(host='0.0.0.0', port=8082, debug=False)