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

# Load .env files for services (check parent directory first, then local)
# This ensures we get the API keys from the parent claude directory
parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
local_env = os.path.join(os.path.dirname(__file__), '.env')

for env_file in [parent_env, local_env]:
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already set (parent takes precedence)
                    if key.strip() not in os.environ or not os.environ[key.strip()]:
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
    parser.add_argument('--interactive', action='store_true',
                       help='START async interactive Claude with Bonjour discovery')
    
    # Sync/report flags (just start the process)
    parser.add_argument('--sync', action='store_true',
                       help='START sync process')
    parser.add_argument('--sync-and-publish', action='store_true',
                       help='START sync and publish to Shopify')
    parser.add_argument('--console', action='store_true',
                       help='START console report')
    parser.add_argument('--heatmap', action='store_true',
                       help='START heatmap generation')
    parser.add_argument('--stats', action='store_true',
                       help='START stats display')
    parser.add_argument('--voice-test', action='store_true',
                       help='START polymorphic voice test')
    parser.add_argument('--demo-polymorphic', action='store_true',
                       help='START ask/tell/do pattern demonstration')
    
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
    
    # Bonjour discovery
    parser.add_argument('--bonjour-monitor', action='store_true',
                       help='START Bonjour announcement monitor')
    parser.add_argument('--discover', action='store_true',
                       help='START dynamic command discovery')
    
    # Web screenshot service
    parser.add_argument('--screenshot', type=str, metavar='URL',
                       help='Capture screenshot of URL')
    parser.add_argument('--screenshot-service', action='store_true',
                       help='START web screenshot service')
    
    # Process management
    parser.add_argument('--restart-services', action='store_true',
                       help='Kill existing services')
    parser.add_argument('--service-status', action='store_true',
                       help='Check service status')
    parser.add_argument('--test-env', action='store_true',
                       help='Test environment variables')
    
    args = parser.parse_args()
    
    # Start requested services - NO LOGIC, just subprocess calls
    if args.discord_bot:
        # Start discord bot
        subprocess.run([sys.executable, 'bonjour_discord.py'])
    
    elif args.edit_contacts:
        # Start web editor
        subprocess.run([sys.executable, 'services/web_editor.py'])
    
    elif args.ai_chat:
        # Start AI chat
        subprocess.run([sys.executable, 'claude_service.py'])
    
    elif args.interactive:
        # Start async interactive Claude
        subprocess.run([sys.executable, 'claude/interactive.py'])
    
    elif args.sync:
        # Start sync
        subprocess.run([sys.executable, 'tournament_domain/services/sync_service.py'])
    
    elif args.sync_and_publish:
        # Start sync and publish
        subprocess.run([sys.executable, 'tournament_domain/services/sync_and_publish.py'])
    
    elif args.console:
        # Start report
        subprocess.run([sys.executable, 'tournament_domain/analytics/tournament_report.py'])
    
    elif args.heatmap:
        # Start heatmap
        subprocess.run([sys.executable, 'tournament_domain/analytics/tournament_heatmap.py'])
    
    elif args.stats:
        # Start stats
        subprocess.run([sys.executable, 'utils/database_service.py', '--stats'])
    
    elif args.voice_test:
        # Start polymorphic voice test
        subprocess.run([sys.executable, 'polymorphic_voice_test.py'])
    
    elif args.demo_polymorphic:
        # Start ask/tell/do demonstration
        subprocess.run([sys.executable, 'polymorphic_demo.py'])
    
    elif args.twilio_bridge:
        # Start Twilio with Stream WebSocket servers and SSL proxy
        # Kill old processes first
        subprocess.run(['pkill', '-f', 'twilio_simple_voice_bridge'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'twiml_stream_server'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'twilio_stream_server'], stderr=subprocess.DEVNULL)
        subprocess.run(['pkill', '-f', 'polymorphic_encryption'], stderr=subprocess.DEVNULL)
        
        # Start new Stream servers with SSL proxy
        subprocess.Popen([sys.executable, 'twilio_stream_server.py'])  # WebSocket on 8087
        subprocess.Popen([sys.executable, 'twiml_stream_server.py'])   # TwiML on 8086
        subprocess.Popen([sys.executable, 'polymorphic_encryption_service.py', '--proxy', '8443', '8087'])  # SSL proxy
        subprocess.run([sys.executable, 'experimental/telephony/twilio_simple_voice_bridge.py'])  # Main bridge
    
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
    
    elif args.bonjour_monitor:
        # Start Bonjour monitor
        subprocess.run([sys.executable, 'utils/bonjour_monitor.py', 'live'])
    
    elif args.discover:
        # Start discovery service
        subprocess.run([sys.executable, 'utils/bonjour_discovery_service.py'])
    
    elif args.screenshot:
        # Capture screenshot of URL
        subprocess.run([sys.executable, 'services/web_screenshot_service.py', args.screenshot])
    
    elif args.screenshot_service:
        # Start screenshot service
        subprocess.run([sys.executable, 'services/web_screenshot_service.py'])
    
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
    
    elif args.test_env:
        # Test environment
        subprocess.run([sys.executable, 'test_env.py'])
    
    else:
        print("Specify a service to start. Use --help for options.")

if __name__ == "__main__":
    main()