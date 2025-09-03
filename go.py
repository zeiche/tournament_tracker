#!/home/ubuntu/claude/tournament_tracker/venv/bin/python3
"""
go - Tournament Tracker Entry Point
CLI interface for the tournament tracker system
"""
import sys
import os
import argparse
from datetime import datetime
import subprocess
import signal
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import tracker modules
from tournament_tracker import TournamentTracker

def find_process(name):
    """Find running processes by name"""
    processes = []
    try:
        result = subprocess.run(['pgrep', '-f', name], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    processes.append(int(pid))
    except Exception:
        pass
    return processes

def kill_process(name, exclude_self=True):
    """Kill all processes matching name"""
    current_pid = os.getpid()
    killed = 0
    
    for pid in find_process(name):
        if exclude_self and pid == current_pid:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            killed += 1
            print(f"Killed process {pid} ({name})")
        except ProcessLookupError:
            pass
        except PermissionError:
            print(f"Permission denied to kill {pid}")
    
    if killed > 0:
        time.sleep(1)  # Give processes time to terminate
    return killed

def ensure_single_instance(service_name):
    """Ensure only one instance of a service is running"""
    processes = find_process(service_name)
    current_pid = os.getpid()
    
    for pid in processes:
        if pid != current_pid:
            print(f"Found existing {service_name} process (PID: {pid}), killing it...")
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
            except:
                pass

def restart_service(service_name):
    """Restart a systemd service"""
    try:
        # Stop service
        subprocess.run(['sudo', 'systemctl', 'stop', service_name], 
                      capture_output=True, check=False)
        time.sleep(1)
        
        # Start service
        result = subprocess.run(['sudo', 'systemctl', 'start', service_name], 
                              capture_output=True, check=False)
        
        if result.returncode == 0:
            print(f"✓ Restarted {service_name}")
            return True
        else:
            print(f"✗ Failed to restart {service_name}")
            return False
    except Exception as e:
        print(f"Error restarting {service_name}: {e}")
        return False

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Tournament Tracker - SoCal FGC Edition')
    
    # Sync options
    parser.add_argument('--sync', action='store_true', help='Sync tournaments from start.gg')
    parser.add_argument('--skip-sync', action='store_true', help='Skip start.gg sync')
    parser.add_argument('--fetch-standings', action='store_true', help='Fetch top 8 standings for major tournaments')
    parser.add_argument('--standings-limit', type=int, default=5, help='Limit standings fetch to N major tournaments (default: 5)')
    parser.add_argument('--page-size', type=int, default=250, help='Queue page size (default: 250)')
    
    # Output options
    parser.add_argument('--console', action='store_true', help='Show console report')
    parser.add_argument('--html', metavar='FILE', help='Generate HTML report to file')
    parser.add_argument('--publish', action='store_true', help='Publish to Shopify')
    parser.add_argument('--limit', type=int, help='Limit number of results')
    
    # Utility options
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--interactive', '-i', action='store_true', help='Start interactive mode')
    parser.add_argument('--database-url', help='Database URL (default: SQLite)')
    
    # Editor options
    parser.add_argument('--edit-contacts', action='store_true', help='Launch web editor for contact management')
    parser.add_argument('--editor-port', type=int, default=8081, help='Port for web editor (default: 8081)')
    
    # Service management options
    parser.add_argument('--setup-discord', metavar='TOKEN', help='Setup Discord bot service with token')
    parser.add_argument('--setup-services', metavar='TOKEN', help='Setup both web and Discord services')
    parser.add_argument('--service-status', action='store_true', help='Check status of services')
    parser.add_argument('--restart-discord', action='store_true', help='Restart Discord bot service')
    parser.add_argument('--restart-services', action='store_true', help='Restart all services')
    
    # AI interface options
    parser.add_argument('--ai-chat', action='store_true', help='Launch terminal AI chat interface')
    parser.add_argument('--ai-web', action='store_true', help='Launch web-based AI chat interface')
    parser.add_argument('--ai-web-port', type=int, default=8082, help='Port for AI web chat (default: 8082)')
    parser.add_argument('--ai-ask', metavar='QUESTION', help='Ask AI a single question')
    parser.add_argument('--heatmap', action='store_true', help='Generate and display heat map visualizations')
    
    args = parser.parse_args()
    
    # Handle help case FIRST - before any database operations
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Handle service management first (before database operations)
    if args.setup_discord:
        result = subprocess.run(['/home/ubuntu/claude/setup_services.sh', 'setup-discord', args.setup_discord])
        return result.returncode
    
    if args.setup_services:
        result = subprocess.run(['/home/ubuntu/claude/setup_services.sh', 'setup-all', args.setup_services])
        return result.returncode
    
    if args.service_status:
        result = subprocess.run(['/home/ubuntu/claude/setup_services.sh', 'status'])
        return result.returncode
    
    if args.restart_discord:
        print("Restarting Discord bot...")
        
        # Stop the service first (this prevents auto-restart)
        subprocess.run(['sudo', 'systemctl', 'stop', 'discord-bot'], 
                      capture_output=True, check=False)
        time.sleep(2)
        
        # Now kill any remaining processes
        killed = kill_process('discord_ai_bot')
        if killed > 0:
            print(f"Killed {killed} stray Discord bot process(es)")
            time.sleep(1)
        
        # Start the service cleanly
        result = subprocess.run(['sudo', 'systemctl', 'start', 'discord-bot'], 
                              capture_output=True, check=False)
        
        if result.returncode == 0:
            print("✅ Discord bot restarted successfully")
            
            # Wait and verify only one instance
            time.sleep(2)
            processes = find_process('discord_ai_bot')
            if len(processes) == 1:
                print(f"✓ Single instance running (PID: {processes[0]})")
            elif len(processes) > 1:
                print(f"⚠️  Warning: {len(processes)} instances detected, cleaning up...")
                # Kill all but the first one
                for pid in processes[1:]:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        print(f"Killed extra instance {pid}")
                    except:
                        pass
            return 0
        else:
            print("❌ Failed to restart Discord bot")
            return 1
    
    if args.restart_services:
        print("Restarting all services...")
        
        # Kill any stray processes first
        services = [
            ('discord_ai_bot', 'discord-bot'),
            ('editor_web', 'tournament-web'),
        ]
        
        success = True
        for process_name, service_name in services:
            killed = kill_process(process_name)
            if killed > 0:
                print(f"Killed {killed} stray {process_name} process(es)")
            
            if not restart_service(service_name):
                success = False
        
        if success:
            print("✅ All services restarted successfully")
            return 0
        else:
            print("❌ Some services failed to restart")
            return 1
    
    # Handle AI interface options
    if args.ai_chat:
        print("Launching AI chat interface...")
        result = subprocess.run([sys.executable, 'ai_curses_chat.py'])
        return result.returncode
    
    if args.ai_web:
        print(f"Starting AI web chat on port {args.ai_web_port}...")
        print(f"Access at: http://localhost:{args.ai_web_port}")
        env = os.environ.copy()
        env['AI_CHAT_PORT'] = str(args.ai_web_port)
        result = subprocess.run([sys.executable, 'ai_web_chat.py'], env=env)
        return result.returncode
    
    if args.ai_ask:
        from ai_service import get_ai_service, ChannelType
        import os
        import re
        
        ai = get_ai_service()
        if not ai.enabled:
            print("⚠️  AI service not enabled. Set ANTHROPIC_API_KEY to enable.")
            return 1
        print("Getting AI response...")
        response = ai.get_response_sync(args.ai_ask, ChannelType.GENERAL)
        
        # Check if response mentions heatmap files
        msg_lower = args.ai_ask.lower()
        if any(word in msg_lower for word in ['heat map', 'heatmap', 'heat-map']):
            # Generate heatmaps if requested
            if any(word in msg_lower for word in ['make', 'create', 'generate', 'update', 'refresh']):
                print("\n🔄 Generating heat maps...")
                from tournament_heatmap import generate_static_heatmap, generate_attendance_heatmap
                
                # Generate both with and without map background
                if generate_static_heatmap('tournament_heatmap.png', use_map_background=False):
                    print("✓ Created tournament_heatmap.png")
                if generate_static_heatmap('tournament_heatmap_with_map.png', use_map_background=True):
                    print("✓ Created tournament_heatmap_with_map.png")
                if generate_attendance_heatmap():
                    print("✓ Created attendance_heatmap.png")
            
            # Display the heatmap files
            heatmap_files = [
                'tournament_heatmap.png',
                'tournament_heatmap_with_map.png',
                'attendance_heatmap.png'
            ]
            
            print("\n📍 Heat Map Files:")
            for filename in heatmap_files:
                filepath = f'/home/ubuntu/claude/tournament_tracker/{filename}'
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath) / 1024  # Size in KB
                    print(f"   • {filename} ({size:.1f} KB)")
                    print(f"     View with: display {filepath}")
            
            print("\n💡 Tip: To view images in terminal, use:")
            print("   • GUI: display <filename>")
            print("   • Terminal: imgcat <filename> (if installed)")
            print("   • Web: Open tournament_heatmap.html in browser")
            print("\nAI Response:")
        
        print("\n" + response)
        return 0
    
    if args.heatmap:
        print("🗺️  Generating Tournament Heat Maps...\n")
        from tournament_heatmap import generate_static_heatmap, generate_attendance_heatmap, generate_interactive_heatmap
        import os
        
        # Generate all heatmap types
        files_created = []
        
        if generate_static_heatmap('tournament_heatmap.png', use_map_background=False):
            files_created.append(('tournament_heatmap.png', 'Tournament density heat map'))
        
        if generate_static_heatmap('tournament_heatmap_with_map.png', use_map_background=True):
            files_created.append(('tournament_heatmap_with_map.png', 'Heat map with street map overlay'))
        
        if generate_attendance_heatmap():
            files_created.append(('attendance_heatmap.png', 'Attendance-weighted density map'))
        
        if generate_interactive_heatmap():
            files_created.append(('tournament_heatmap.html', 'Interactive zoomable web map'))
        
        # Display results
        print("\n✅ Heat Maps Generated:\n")
        for filename, description in files_created:
            filepath = f'/home/ubuntu/claude/tournament_tracker/{filename}'
            if os.path.exists(filepath):
                size = os.path.getsize(filepath) / 1024  # Size in KB
                print(f"   📍 {filename}")
                print(f"      {description}")
                print(f"      Size: {size:.1f} KB")
                
                if filename.endswith('.png'):
                    print(f"      View: display {filepath}")
                elif filename.endswith('.html'):
                    print(f"      Open: firefox {filepath} (or any browser)")
                print()
        
        print("💡 Viewing Options:")
        print("   • GUI:      display <filename>.png")
        print("   • Terminal: imgcat <filename>.png (if installed)")
        print("   • Web:      Open tournament_heatmap.html in browser")
        print("   • Remote:   scp the files to local machine to view")
        
        return 0
    
    try:
        # Create TournamentTracker for database operations
        tracker = TournamentTracker(database_url=args.database_url)
        
        # Sync unless skipped
        if not args.skip_sync and (args.sync or args.fetch_standings or args.publish or not any([args.console, args.html, args.stats, args.interactive])):
            success = tracker.sync_tournaments(
                page_size=args.page_size, 
                fetch_standings=args.fetch_standings,
                standings_limit=args.standings_limit
            )
            if not success and not args.interactive:
                sys.exit(1)
        
        # Generate outputs
        if args.console:
            tracker.show_console_report(limit=args.limit)
        
        if args.html:
            tracker.generate_html_report(limit=args.limit, output_file=args.html)
        
        if args.publish:
            tracker.publish_to_shopify()
        
        if args.stats:
            tracker.show_statistics()
        
        if args.interactive:
            from go_interactive import start_interactive_mode
            start_interactive_mode(database_url=args.database_url)
        
        if args.edit_contacts:
            # Kill any existing editor_web processes
            ensure_single_instance('editor_web')
            # Ensure database is initialized
            tracker._ensure_db_initialized()
            from editor_web import run_server
            print(f"Starting web editor on port {args.editor_port}...")
            run_server(port=args.editor_port)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

