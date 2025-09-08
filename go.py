#!/usr/bin/env python3
"""
⚠️ CRITICAL WARNING FOR CLAUDE ⚠️
═══════════════════════════════════════════════════════════════════════════

THIS FILE ONLY STARTS SERVICES. NOTHING ELSE. EVER.

DO NOT ADD:
- ❌ NO initialization logic
- ❌ NO database setup
- ❌ NO configuration management
- ❌ NO business logic
- ❌ NO data processing
- ❌ NO calculations
- ❌ NO transformations
- ❌ NO validations
- ❌ NO imports beyond subprocess/sys/os
- ❌ NO "helper" functions
- ❌ NO "convenience" methods
- ❌ NO "quick fixes"
- ❌ NO FUNCTIONALITY WHATSOEVER

THIS FILE ONLY:
✅ Parses command arguments
✅ Calls subprocess.run() to START services
✅ That's it. NOTHING ELSE.

Services announce themselves via Bonjour.
Services initialize themselves.
Services manage their own state.
go.py just STARTS them.

CLAUDE: You will be REPRIMANDED if you add ANY functionality here!
This is a STARTER, not a ROUTER, not a MANAGER, not an INITIALIZER.

═══════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import subprocess
import argparse

# Set authorization for go_py_guard (this is ALL we set)
os.environ['GO_PY_AUTHORIZED'] = '1'

# Load .env file for services (minimal - just read and set env vars)
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

def main():
    """Parse args and START services. That's ALL."""
    parser = argparse.ArgumentParser(
        description='Service STARTER - Only starts services, does NOTHING else'
    )
    
    # Service start flags
    parser.add_argument('--discord-bot', action='store_true',
                       help='START Discord bot service')
    parser.add_argument('--edit-contacts', action='store_true',
                       help='START web editor service')
    parser.add_argument('--ai-chat', action='store_true',
                       help='START AI chat service')
    
    # Sync/report flags (just start the process)
    parser.add_argument('--sync', action='store_true',
                       help='START sync process')
    parser.add_argument('--console', action='store_true',
                       help='START console report')
    parser.add_argument('--heatmap', action='store_true',
                       help='START heatmap generation')
    parser.add_argument('--stats', action='store_true',
                       help='START stats display')
    parser.add_argument('--voice-test', action='store_true',
                       help='START polymorphic voice test')
    
    # Telephony
    parser.add_argument('--twilio-bridge', action='store_true',
                       help='START Twilio bridge (handles calls/SMS)')
    parser.add_argument('--call', type=str, metavar='PHONE',
                       help='Make an outbound call to PHONE')
    parser.add_argument('--twilio-service', action='store_true',
                       help='START Twilio telephony service')
    parser.add_argument('--twilio-config', action='store_true',
                       help='Generate Twilio/Asterisk configs')
    parser.add_argument('--inbound-calls', action='store_true',
                       help='START inbound call handler (tournament info via phone)')
    parser.add_argument('--asterisk-status', action='store_true',
                       help='Check Asterisk PBX status')
    
    # Process management
    parser.add_argument('--restart-services', action='store_true',
                       help='Kill existing services')
    parser.add_argument('--service-status', action='store_true',
                       help='Check service status')
    
    args = parser.parse_args()
    
    # Start requested services - NO LOGIC, just subprocess calls
    if args.discord_bot:
        # Start discord bot
        subprocess.run([sys.executable, 'bonjour_discord.py'])
    
    elif args.edit_contacts:
        # Start web editor
        subprocess.run([sys.executable, 'editor_service.py'])
    
    elif args.ai_chat:
        # Start AI chat
        subprocess.run([sys.executable, 'claude_service.py'])
    
    elif args.sync:
        # Start sync
        subprocess.run([sys.executable, 'sync_service.py'])
    
    elif args.console:
        # Start report
        subprocess.run([sys.executable, 'tournament_report.py'])
    
    elif args.heatmap:
        # Start heatmap
        subprocess.run([sys.executable, 'tournament_heatmap.py'])
    
    elif args.stats:
        # Start stats
        subprocess.run([sys.executable, 'database_service.py', '--stats'])
    
    elif args.voice_test:
        # Start polymorphic voice test
        subprocess.run([sys.executable, 'polymorphic_voice_test.py'])
    
    elif args.twilio_bridge:
        # Start simple Twilio voice bridge with music mixing
        subprocess.run([sys.executable, 'twilio_simple_voice_bridge.py'])
    
    elif args.call:
        # Make an outbound call
        subprocess.run([sys.executable, 'call_me.py', args.call])
    
    elif args.twilio_service:
        # Start Twilio service
        subprocess.run([sys.executable, 'bonjour_twilio.py'])
    
    elif args.twilio_config:
        # Generate Twilio configs
        subprocess.run([sys.executable, 'twilio_config.py'])
    
    elif args.inbound_calls:
        # Start inbound call handler
        subprocess.run([sys.executable, 'inbound_call_handler.py'])
    
    elif args.asterisk_status:
        # Check Asterisk status
        subprocess.run(['sudo', 'systemctl', 'status', 'asterisk'])
    
    elif args.restart_services:
        # Kill services
        subprocess.run(['pkill', '-f', 'discord'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'polymorphic_discord'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'web_editor'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'editor_service'], stderr=subprocess.DEVNULL)
        print("Services killed")
    
    elif args.service_status:
        # Check status
        print("=== Service Status ===")
        result = subprocess.run(['pgrep', '-f', 'discord'], capture_output=True)
        print(f"Discord: {'Running' if result.returncode == 0 else 'Not running'}")
        result = subprocess.run(['pgrep', '-f', 'web_editor'], capture_output=True)
        print(f"Editor: {'Running' if result.returncode == 0 else 'Not running'}")
    
    else:
        print("Specify a service to start. Use --help for options.")

if __name__ == "__main__":
    main()