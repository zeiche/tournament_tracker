# Asterisk VoIP Setup for Calling Claude

## Current Status
- **Disk space issue**: System has only 2.9G total, currently 100% full
- **Asterisk requires**: ~144MB additional space for installation
- **Solution needed**: Either clean up space or use larger instance

## Architecture Created

### Polymorphic AGI Interface
- `/polymorphic_core/telephony/asterisk_agi.py` - Complete AGI interface
- Handles calls polymorphically - figures out what caller wants
- Integrates with bonjour announcements
- Supports transcription (Whisper) and TTS (espeak)

### Dialplan Configuration
- `/asterisk_config/extensions.conf` - Routes all calls to Claude
- Extension 2583 (CLUD) - Direct line to Claude
- All incoming calls go through AGI

## Installation Steps (when space available)

```bash
# 1. Install Asterisk and dependencies
sudo apt update
sudo apt install -y asterisk asterisk-core-sounds-en sox espeak

# 2. Install Whisper for transcription
pip install openai-whisper

# 3. Copy config files
sudo cp asterisk_config/*.conf /etc/asterisk/

# 4. Set AGI permissions
chmod +x polymorphic_core/telephony/asterisk_agi.py

# 5. Restart Asterisk
sudo systemctl restart asterisk
```

## VoIP Provider Options

### Twilio (Recommended for ease)
- Elastic SIP Trunking
- ~$0.007/min incoming
- Good API integration
- Instant provisioning

### Telnyx
- Mission Control Portal
- ~$0.005/min
- Good for developers
- WebRTC support

### VoIP.ms
- Traditional provider
- ~$0.01/min
- Lots of features
- More complex setup

### Bandwidth.com
- Enterprise focused
- Good rates
- Requires approval

## PJSIP Configuration (template)

```ini
[voip-provider]
type=registration
transport=transport-udp
outbound_auth=voip-provider
server_uri=sip:your-sip-server.com
client_uri=sip:your-username@your-sip-server.com
contact_user=your-username

[voip-provider]
type=auth
auth_type=userpass
password=your-password
username=your-username

[voip-provider]
type=endpoint
transport=transport-udp
context=incoming
disallow=all
allow=ulaw
allow=alaw
outbound_auth=voip-provider
aors=voip-provider
from_user=your-username
from_domain=your-sip-server.com

[voip-provider]
type=aor
contact=sip:your-sip-server.com
```

## Firewall Configuration

```bash
# SIP signaling
sudo ufw allow 5060/udp
sudo ufw allow 5061/tcp

# RTP media (voice)
sudo ufw allow 10000:20000/udp
```

## How It Works

1. **Call comes in** → Asterisk answers
2. **Dialplan routes** → AGI script (asterisk_agi.py)
3. **AGI answers** → "Hello, this is Claude"
4. **Caller speaks** → Recorded as WAV
5. **Whisper transcribes** → Text from audio
6. **Announcement** → "TRANSCRIPTION_COMPLETE"
7. **Claude processes** → Via announcement system
8. **Response generated** → Claude's answer
9. **TTS creates audio** → espeak generates WAV
10. **Play to caller** → Stream audio file
11. **Repeat** → Until caller hangs up

## Advantages Over Discord

- **No heartbeat issues** - We control the connection
- **No API limits** - Direct telephony
- **Real phone numbers** - Call from any phone
- **Better audio quality** - Direct RTP streams
- **No middleman** - Direct caller to Claude
- **Scalable** - Can handle multiple calls
- **Reliable** - Telephony-grade infrastructure

## Next Steps

1. **Free up disk space** or get larger instance
2. **Choose VoIP provider** and get account
3. **Install Asterisk** and dependencies
4. **Configure PJSIP** with provider credentials
5. **Test locally** with softphone
6. **Get DID** (phone number) from provider
7. **Test incoming calls** to Claude

## Testing Without Provider

Can test locally first:
```bash
# Register a SIP softphone (Zoiper, Linphone, etc.)
# Extension: 100
# Password: test123
# Server: your-server-ip
# Call extension 2583 to reach Claude
```

The polymorphic architecture means Claude doesn't care if calls come from Discord, Asterisk, or any other source - it all goes through the announcement system.