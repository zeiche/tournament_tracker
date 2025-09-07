# twilio setup guide for asterisk integration

## step 1: twilio account basics

### 1.1 login to twilio console
1. go to https://www.twilio.com/console
2. log in with your account
3. you'll land on the dashboard

### 1.2 get your account credentials
from the dashboard, you'll see:
- **account sid**: starts with "AC..." (copy this)
- **auth token**: click to reveal and copy (keep secret!)

add these to your .env:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## step 2: buy a phone number

### 2.1 navigate to phone numbers
1. in console, go to: **phone numbers** → **manage** → **buy a number**
2. or direct link: https://console.twilio.com/us1/develop/phone-numbers/manage/search

### 2.2 search for a number
1. choose country (united states)
2. select capabilities:
   - ✅ voice
   - ✅ sms
   - ✅ mms (optional)
3. search for a number you like
4. click "buy" ($1.15/month for us numbers)

### 2.3 save your number
add to .env:
```bash
TWILIO_PHONE_NUMBER=+1234567890  # your actual number
```

## step 3: set up elastic sip trunking

### 3.1 enable elastic sip trunking
1. go to: **elastic sip trunking** in the console
2. or: https://console.twilio.com/us1/develop/elastic-sip-trunking/getting-started
3. click "create a sip trunk"

### 3.2 configure your trunk
1. **general settings**:
   - trunk name: "asterisk-trunk" (or your choice)
   - recording: disabled (for now)

2. **termination (receive calls)**:
   - termination sip uri: `your-trunk-name.pstn.twilio.com`
   - add your asterisk server ip as "ip access control list":
     - click "create new ip access control list"
     - name: "asterisk-server"
     - add your server's public ip
     - save

3. **origination (make calls)**:
   - add origination uri:
     - priority: 10
     - weight: 100
     - uri: `sip:your.server.ip:5060`
     - enable: yes

4. **authentication**:
   - click "credentials lists" → "create new"
   - list name: "asterisk-auth"
   - add credential:
     - username: choose something (e.g., "asterisk")
     - password: generate strong password
   - save

### 3.3 save sip credentials
add to .env:
```bash
TWILIO_SIP_DOMAIN=your-trunk-name.pstn.twilio.com
TWILIO_SIP_USERNAME=asterisk  # what you chose above
TWILIO_SIP_PASSWORD=your-strong-password
```

## step 4: configure phone number routing

### 4.1 route number to sip trunk
1. go to **phone numbers** → **manage** → **active numbers**
2. click on your purchased number
3. in **voice configuration**:
   - configure with: "sip trunk"
   - sip trunk: select your trunk ("asterisk-trunk")
4. save

## step 5: get your server's public ip

### 5.1 find your external ip
```bash
curl ifconfig.me
```

### 5.2 add to .env
```bash
ASTERISK_EXTERNAL_IP=your.public.ip.address
```

## step 6: optional - programmable voice (for webhooks)

if you want to use twilio's programmable voice api instead of/alongside sip:

### 6.1 create twiml app
1. go to **voice** → **twiml apps**
2. create new twiml app:
   - name: "asterisk-bridge"
   - voice url: `http://your.server.ip:8080/twilio/voice`
   - sms url: `http://your.server.ip:8080/twilio/sms`

### 6.2 update phone number
1. go back to your phone number
2. change configure with: "twiml app"
3. select your app
4. save

## final .env configuration

your complete .env should have:
```bash
# twilio credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890

# sip trunk settings
TWILIO_SIP_DOMAIN=your-trunk-name.pstn.twilio.com
TWILIO_SIP_USERNAME=asterisk
TWILIO_SIP_PASSWORD=your-strong-password

# server settings
ASTERISK_EXTERNAL_IP=your.public.ip.address
ASTERISK_LOCAL_NET=192.168.0.0/16  # adjust for your network

# optional webhook urls (if using programmable voice)
TWILIO_VOICE_URL=http://your.server.ip:8080/twilio/voice
TWILIO_SMS_URL=http://your.server.ip:8080/twilio/sms
```

## testing your setup

### test 1: verify credentials
```bash
./go.py --twilio-config
# should show "valid: True" if all credentials are set
```

### test 2: make a test call (after asterisk config)
```bash
# from asterisk cli
asterisk -rvvv
CLI> originate PJSIP/+1234567890@twilio application Echo
```

### test 3: receive a test call
call your twilio number from another phone - it should hit your asterisk server

## troubleshooting

### common issues:
1. **nat problems**: make sure asterisk_external_ip is correct
2. **firewall**: open udp ports 5060 (sip) and 10000-20000 (rtp)
3. **authentication**: double-check sip username/password
4. **routing**: ensure number is routed to sip trunk, not twiml

### useful twilio debugging:
- **debugger**: https://console.twilio.com/us1/monitor/logs/debugger
- **call logs**: https://console.twilio.com/us1/monitor/logs/calls
- **sip logs**: in elastic sip trunking → your trunk → logs

## pricing notes
- phone number: ~$1.15/month (us)
- inbound calls: $0.0085/minute
- outbound calls: $0.013/minute
- sip trunking: no additional charge
- transcription: $0.02/minute (if using twilio's)
- text-to-speech: varies by provider