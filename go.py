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
from polymorphic_core.process import ProcessManager

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
    parser.add_argument('--discord-lightweight', action='store_true',
                       help='START Discord with lightweight intelligence (no LLM)')
    parser.add_argument('--bridge', type=str, metavar='TYPE',
                       help='START a bridge service (use --list-bridges to see options)')
    parser.add_argument('--list-bridges', action='store_true',
                       help='List available bridge services')
    parser.add_argument('--edit-contacts', action='store_true',
                       help='START web editor service')
    parser.add_argument('--ai-chat', action='store_true',
                       help='START AI chat service')
    parser.add_argument('--interactive', action='store_true',
                       help='START interactive bridge (auto-selects backend)')
    parser.add_argument('--interactive-backend', type=str, 
                       choices=['auto', 'lightweight', 'claude'],
                       default='auto',
                       help='Backend for interactive mode (default: auto)')
    
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
                       help='Generate Twilio configs')
    parser.add_argument('--twilio-voice', action='store_true',
                       help='Start voice-enabled Twilio stream servers')
    parser.add_argument('--twilio-transcription', action='store_true',
                       help='START Twilio stream with polymorphic transcription')
    parser.add_argument('--inbound-calls', action='store_true',
                       help='START inbound call handler (tournament info via phone)')
    
    # Bonjour discovery
    parser.add_argument('--bonjour-monitor', action='store_true',
                       help='START Bonjour announcement monitor')
    parser.add_argument('--advertisements', action='store_true',
                       help='Show current bonjour advertisements (non-blocking)')
    parser.add_argument('--discover', action='store_true',
                       help='START dynamic command discovery')
    parser.add_argument('--bonjour-server', nargs='*', metavar='PORTS',
                       help='START Bonjour Universal Server on specified ports (or common ports if none given)')
    parser.add_argument('--lightweight', action='store_true',
                       help='START Lightweight pattern intelligence (no LLM needed)')
    
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
        # Start Discord using self-managing service
        try:
            from bonjour_discord import _discord_process_manager
            print("Starting Discord bot via integrated DiscordProcessManager...")
            pids = _discord_process_manager.start_services()
            print(f"Discord bot started with PIDs: {pids}")
        except (ImportError, NameError) as e:
            print(f"Integrated DiscordProcessManager not available: {e}")
            # Fallback to old method
            print("Falling back to manual process management...")
            ProcessManager.restart_service('bonjour_discord.py')
    
    elif args.discord_lightweight:
        # Start Discord with lightweight intelligence (using bridge module)
        subprocess.Popen([sys.executable, 'bridges/bridge_launcher.py', 'discord-lightweight'])
    
    elif args.bridge:
        # Start a specific bridge service
        subprocess.Popen([sys.executable, 'bridges/bridge_launcher.py', args.bridge])
    
    elif args.list_bridges:
        # List available bridges
        subprocess.run([sys.executable, 'bridges/bridge_launcher.py', '--list'])
    
    elif args.edit_contacts:
        # Start Web Editor using self-managing service
        try:
            from services.web_editor import _web_editor_process_manager
            print("Starting Web Editor via integrated WebEditorProcessManager...")
            pids = _web_editor_process_manager.start_services()
            print(f"Web Editor started with PIDs: {pids}")
        except (ImportError, NameError) as e:
            print(f"Integrated WebEditorProcessManager not available: {e}")
            # Fallback to old method
            print("Falling back to manual process management...")
            ProcessManager.restart_service('services/web_editor.py')
    
    elif args.ai_chat:
        # Start AI chat
        subprocess.Popen([sys.executable, 'claude_service.py'])
    
    elif args.interactive:
        # Start interactive bridge with selected backend
        backend = args.interactive_backend if hasattr(args, 'interactive_backend') else 'auto'
        subprocess.Popen([sys.executable, 'bridges/interactive_bridge.py', '--backend', backend])
    
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
        # Start Twilio using self-managing service from bridge
        try:
            # Import the bridge file to get access to its process manager
            sys.path.insert(0, 'experimental/telephony')
            from twilio_simple_voice_bridge import _twilio_process_manager
            print("Starting Twilio services via integrated TwilioProcessManager...")
            pids = _twilio_process_manager.start_services()
            print(f"Twilio services started with PIDs: {pids}")
        except (ImportError, NameError) as e:
            print(f"Integrated TwilioProcessManager not available: {e}")
            # Fallback to old method if needed
            print("Falling back to manual process management...")
            ProcessManager.kill_pattern('twilio_simple_voice_bridge')
            ProcessManager.kill_pattern('twiml_stream_server')
            ProcessManager.kill_pattern('twilio_stream_server')
            ProcessManager.kill_pattern('polymorphic_encryption')
            ProcessManager.kill_port(8087)
            ProcessManager.kill_port(8086)
            ProcessManager.kill_port(8443)
            import time
            time.sleep(1)
            ProcessManager.start_service_safe('twilio_stream_server.py', check_existing=False)
            ProcessManager.start_service_safe('twiml_stream_server.py', check_existing=False)
            ProcessManager.start_service_safe('polymorphic_encryption_service.py', '--proxy', '8443', '8087', check_existing=False)
            ProcessManager.start_service_safe('experimental/telephony/twilio_simple_voice_bridge.py', check_existing=False)
    
    elif args.call:
        # Make an outbound call
        subprocess.run([sys.executable, 'call_me.py', args.call])
    
    elif args.twilio_service:
        # Start Twilio service using ProcessManager
        ProcessManager.restart_service('bonjour_twilio.py')
    
    elif args.twilio_config:
        # Generate Twilio configs
        subprocess.run([sys.executable, 'twilio_config.py'])
    elif args.twilio_voice:
        # Start voice-enabled Twilio stream servers using ProcessManager
        ProcessManager.kill_pattern('twiml_stream_server')
        ProcessManager.kill_pattern('modern_stream_server')
        ProcessManager.start_service_safe('twiml_stream_server.py', check_existing=False)  # TwiML on 8086
        ProcessManager.start_service_safe('modern_stream_server.py', check_existing=False)  # Voice WebSocket on 8094
    
    elif args.twilio_transcription:
        # Start Twilio stream with polymorphic transcription integration using ProcessManager
        ProcessManager.kill_pattern('twilio_stream_polymorphic')
        ProcessManager.kill_pattern('twilio_transcription_bridge')
        ProcessManager.kill_pattern('twiml_stream_server')
        ProcessManager.start_service_safe('twiml_stream_server.py', check_existing=False)  # TwiML on 8086
        ProcessManager.start_service_safe('twilio_transcription_bridge.py', check_existing=False)  # Bridge
        ProcessManager.start_service_safe('twilio_stream_polymorphic.py', check_existing=False)  # WebSocket on 8088
    
    elif args.inbound_calls:
        # Start inbound call handler
        subprocess.Popen([sys.executable, 'inbound_call_handler.py'])
    
    elif args.bonjour_monitor:
        # Start Bonjour monitor
        subprocess.Popen([sys.executable, 'utils/bonjour_monitor.py', 'live'])
    
    elif args.advertisements:
        # Show current advertisements (non-blocking)
        subprocess.run([sys.executable, 'show_advertisements.py'])
    
    elif args.discover:
        # Start discovery service
        subprocess.run([sys.executable, 'utils/bonjour_discovery_service.py'])
    
    elif args.bonjour_server is not None:
        # Start Bonjour Universal Server
        if args.bonjour_server:
            # Specific ports provided
            subprocess.Popen([sys.executable, 'bonjour_universal_server.py'] + args.bonjour_server)
        else:
            # No ports specified, use defaults
            subprocess.Popen([sys.executable, 'bonjour_universal_server.py'])
    
    
    elif args.lightweight:
        # Start lightweight pattern intelligence (no LLM)
        subprocess.call([sys.executable, '-u', 'lightweight_bonjour.py'])
    
    elif args.screenshot:
        # Capture screenshot of URL
        subprocess.run([sys.executable, 'services/web_screenshot_service.py', args.screenshot])
    
    elif args.screenshot_service:
        # Start screenshot service using ProcessManager
        ProcessManager.restart_service('services/web_screenshot_service.py')
    
    elif args.restart_services:
        # Restart services using integrated process managers
        print("Restarting services via integrated ProcessManagers...")
        
        # Restart Discord using its process manager
        try:
            from bonjour_discord import _discord_process_manager
            discord_pids = _discord_process_manager.start_services()
            print(f"Discord restarted with PIDs: {discord_pids}")
        except (ImportError, NameError) as e:
            print(f"Discord ProcessManager not available, using fallback: {e}")
            killed_discord = ProcessManager.kill_pattern('discord')
            killed_polymorphic = ProcessManager.kill_pattern('polymorphic_discord')
            ProcessManager.start_service_safe('bonjour_discord.py', check_existing=False)
        
        # Restart Web Editor using its process manager
        try:
            from services.web_editor import _web_editor_process_manager
            web_pids = _web_editor_process_manager.start_services()
            print(f"Web Editor restarted with PIDs: {web_pids}")
        except (ImportError, NameError) as e:
            print(f"Web Editor ProcessManager not available, using fallback: {e}")
            killed_web = ProcessManager.kill_pattern('web_editor')
            killed_editor = ProcessManager.kill_pattern('editor_service')
            ProcessManager.start_service_safe('services/web_editor.py', check_existing=False)
        
        print("Services restarted")
    
    elif args.service_status:
        # Check status using bonjour signals
        print("=== Service Status (via Bonjour Signals) ===")
        
        try:
            sys.path.append('/home/ubuntu/claude/tournament_tracker')
            from polymorphic_core import announcer
            
            # Send status signal to all registered services
            print("Sending status signal to all services...")
            responses = announcer.send_signal('status')
            
            if responses:
                print("\n=== Service Responses ===")
                for service_name, response in responses.items():
                    if isinstance(response, dict) and 'error' in response:
                        print(f"{service_name}: ERROR - {response['error']}")
                    else:
                        print(f"{service_name}: {response}")
            else:
                print("No services responded to status signal")
            
            # Also show registered services
            if announcer.service_registry:
                print(f"\n=== Registered Services ({len(announcer.service_registry)}) ===")
                for service_name in announcer.service_registry:
                    print(f"  • {service_name}")
            
            # Show announcements
            context = announcer.get_announcements_for_claude()
            if context and "No services" not in context:
                print("\n=== Service Announcements ===")
                print(context)
                
        except Exception as e:
            print(f"Error checking service status: {e}")
            # Fallback to ProcessManager process check
            print("\n=== Fallback: Process Check via ProcessManager ===")
            processes = ProcessManager.list_tournament_processes()
            if processes:
                for pattern, pids in processes.items():
                    print(f"{pattern}: Running ({len(pids)} processes)")
            else:
                print("No tournament tracker processes found")
    
    elif args.test_env:
        # Test environment
        subprocess.run([sys.executable, 'test_env.py'])
    
    else:
        print("Specify a service to start. Use --help for options.")

if __name__ == "__main__":
    main()