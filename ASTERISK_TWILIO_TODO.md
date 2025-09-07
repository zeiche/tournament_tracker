# asterisk + twilio integration todo

## immediate next steps

### 0. set up twilio account (see TWILIO_SETUP_GUIDE.md) ✅ READY
   a. log into twilio console: https://www.twilio.com/console
   b. get account sid and auth token from dashboard
   c. buy a phone number ($1.15/month)
   d. set up elastic sip trunking
   e. create sip credentials
   f. route phone number to sip trunk
   
   **status**: template added to .env with placeholders
   **server ip**: 64.111.98.139 (already configured)
   **next**: uncomment and fill in twilio values in .env

### 1. add twilio credentials to .env file:
   - TWILIO_ACCOUNT_SID=ACxxxx... (from dashboard)
   - TWILIO_AUTH_TOKEN=xxxxx... (from dashboard)
   - TWILIO_PHONE_NUMBER=+1234567890 (your purchased number)
   - TWILIO_SIP_DOMAIN=your-trunk.pstn.twilio.com (from sip trunk)
   - TWILIO_SIP_USERNAME=asterisk (you choose this)
   - TWILIO_SIP_PASSWORD=xxxxx (you set this)
   - ASTERISK_EXTERNAL_IP=your.ip (run: curl ifconfig.me)

2. configure asterisk with generated configs:
   - review asterisk_config/pjsip_twilio.conf
   - review asterisk_config/extensions_twilio.conf
   - copy to /etc/asterisk/ when ready
   - include in main pjsip.conf and extensions.conf
   - reload asterisk

3. set up audio transcription service:
   - option a: openai whisper api
   - option b: google speech-to-text
   - option c: aws transcribe
   - add api keys to .env

4. implement text-to-speech service:
   - option a: elevenlabs api
   - option b: google cloud tts
   - option c: aws polly
   - add api keys to .env

5. test basic connectivity:
   - test asterisk can reach twilio
   - test inbound call routing
   - test outbound call placement
   - verify audio path works

## phase 1: core setup
- [x] review current asterisk configuration and setup
- [x] create bonjour-style twilio module
- [ ] set up twilio sip trunk configuration
- [ ] configure asterisk sip settings for twilio
- [ ] create dialplan for inbound calls from twilio
- [ ] create dialplan for outbound calls to twilio

## phase 2: claude ai integration
- [ ] set up claude ai integration with asterisk agi
- [ ] configure audio transcription for incoming calls
- [ ] implement text-to-speech for claude responses
- [ ] create bridge between asterisk and claude service

## phase 3: testing & validation
- [ ] test inbound call flow with twilio number
- [ ] test outbound call functionality
- [ ] verify audio quality and latency
- [ ] test claude ai response flow end-to-end

## phase 4: production features
- [ ] set up call recording and logging
- [ ] create monitoring and debugging tools
- [ ] implement call queue management
- [ ] add failover and error handling

## technical requirements
- asterisk 18+ with pjsip
- twilio sip trunk account
- ssl certificates for secure sip
- audio codecs: g711u, g711a, opus
- transcription service (whisper/google/aws)
- tts service (elevenlabs/google/aws)

## key files to create/modify
- `/etc/asterisk/pjsip.conf` - sip trunk configuration
- `/etc/asterisk/extensions.conf` - dialplan logic
- `/etc/asterisk/agi-bin/claude_handler.py` - agi script for claude
- `twilio_bridge.py` - service to handle twilio webhooks
- `call_manager.py` - call state and session management