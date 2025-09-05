#!/home/ubuntu/claude/tournament_tracker/venv/bin/python3
"""
go.py - Tournament Tracker Central Command Interface
Python-centric OOP approach to tournament tracker management
"""
import sys
import os
import argparse
import subprocess
import signal
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import tracker modules
from tournament_tracker import TournamentTracker
from log_manager import LogManager

# Get logger for this module
_logger = LogManager().get_logger('go')
log_info = _logger.info
log_error = _logger.error
log_debug = _logger.debug


class ServiceType(Enum):
    """Service types managed by the system"""
    DISCORD = "discord-bot"
    WEB = "tournament-web"
    AI_WEB = "ai-web"
    ALL = "all"


class CommandType(Enum):
    """Types of commands that can be executed"""
    SYNC = "sync"
    REPORT = "report"
    SERVICE = "service"
    HEATMAP = "heatmap"
    EDITOR = "editor"
    AI = "ai"
    UTILITY = "utility"


@dataclass
class ServiceStatus:
    """Status of a system service"""
    name: str
    service_name: str
    running: bool
    pid: Optional[int] = None
    uptime: Optional[str] = None
    memory: Optional[str] = None


@dataclass
class CommandResult:
    """Result of a command execution"""
    success: bool
    message: str
    data: Optional[Any] = None
    return_code: int = 0


class ProcessManager:
    """Manages system processes and services"""
    
    @staticmethod
    def find_processes(name: str) -> List[int]:
        """Find running processes by name"""
        processes = []
        try:
            result = subprocess.run(['pgrep', '-f', name], capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                processes = [int(pid) for pid in pids if pid]
        except Exception as e:
            log_debug(f"Error finding processes: {e}", "process")
        return processes
    
    @staticmethod
    def kill_process(pid: int) -> bool:
        """Kill a specific process"""
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            log_error(f"Permission denied to kill process {pid}", "process")
            return False
    
    @classmethod
    def kill_all_processes(cls, name: str, exclude_self: bool = True) -> int:
        """Kill all processes matching name"""
        current_pid = os.getpid()
        killed = 0
        
        for pid in cls.find_processes(name):
            if exclude_self and pid == current_pid:
                continue
            if cls.kill_process(pid):
                killed += 1
                log_info(f"Killed process {pid} ({name})", "process")
        
        if killed > 0:
            time.sleep(1)  # Give processes time to terminate
        return killed
    
    @classmethod
    def ensure_single_instance(cls, service_name: str) -> bool:
        """Ensure only one instance of a service is running"""
        processes = cls.find_processes(service_name)
        current_pid = os.getpid()
        
        for pid in processes:
            if pid != current_pid:
                log_info(f"Found existing {service_name} process (PID: {pid}), killing it...", "process")
                cls.kill_process(pid)
                time.sleep(1)
        
        return True


class ServiceManager:
    """Manages systemd services"""
    
    SERVICE_MAP = {
        ServiceType.DISCORD: ("discord-bot", "discord_service.py"),  # SINGLE SOURCE OF TRUTH
        ServiceType.WEB: ("tournament-web", "go.py --edit-contacts"),
        ServiceType.AI_WEB: ("ai-web", "ai_web_chat"),
    }
    
    @classmethod
    def get_service_status(cls, service_type: ServiceType) -> ServiceStatus:
        """Get status of a service"""
        if service_type not in cls.SERVICE_MAP:
            return ServiceStatus(
                name=service_type.value,
                service_name="unknown",
                running=False
            )
        
        service_name, process_name = cls.SERVICE_MAP[service_type]
        
        try:
            # Check systemd status
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True, text=True
            )
            running = result.stdout.strip() == 'active'
            
            # Get process info
            processes = ProcessManager.find_processes(process_name)
            pid = processes[0] if processes else None
            
            # Get additional info if running
            uptime = None
            memory = None
            if running and pid:
                # Get uptime
                try:
                    result = subprocess.run(
                        ['ps', '-o', 'etime=', '-p', str(pid)],
                        capture_output=True, text=True
                    )
                    uptime = result.stdout.strip()
                except Exception:
                    pass
                
                # Get memory usage
                try:
                    result = subprocess.run(
                        ['ps', '-o', 'rss=', '-p', str(pid)],
                        capture_output=True, text=True
                    )
                    mem_kb = int(result.stdout.strip())
                    memory = f"{mem_kb / 1024:.1f} MB"
                except Exception:
                    pass
            
            return ServiceStatus(
                name=service_type.value,
                service_name=service_name,
                running=running,
                pid=pid,
                uptime=uptime,
                memory=memory
            )
            
        except Exception as e:
            log_error(f"Error getting service status: {e}", "service")
            return ServiceStatus(
                name=service_type.value,
                service_name=service_name,
                running=False
            )
    
    @classmethod
    def restart_service(cls, service_type: ServiceType) -> CommandResult:
        """Restart a service"""
        if service_type not in cls.SERVICE_MAP:
            return CommandResult(False, f"Unknown service: {service_type.value}")
        
        service_name, process_name = cls.SERVICE_MAP[service_type]
        
        try:
            # Stop service
            subprocess.run(['sudo', 'systemctl', 'stop', service_name], 
                          capture_output=True, check=False)
            time.sleep(1)
            
            # Kill any stray processes
            killed = ProcessManager.kill_all_processes(process_name)
            if killed > 0:
                log_info(f"Killed {killed} stray {process_name} process(es)", "service")
                time.sleep(1)
            
            # Start service
            result = subprocess.run(['sudo', 'systemctl', 'start', service_name], 
                                  capture_output=True, check=False)
            
            if result.returncode == 0:
                # Verify single instance - Discord bot takes longer to start
                wait_time = 5 if 'discord' in process_name else 3
                time.sleep(wait_time)  # Give service time to start
                processes = ProcessManager.find_processes(process_name)
                
                if len(processes) == 1:
                    return CommandResult(
                        True,
                        f"Service {service_name} restarted successfully (PID: {processes[0]})"
                    )
                elif len(processes) > 1:
                    # Clean up extra instances
                    for pid in processes[1:]:
                        ProcessManager.kill_process(pid)
                    return CommandResult(
                        True,
                        f"Service {service_name} restarted (cleaned up {len(processes)-1} extra instances)"
                    )
                else:
                    return CommandResult(
                        False,
                        f"Service {service_name} started but no process found"
                    )
            else:
                return CommandResult(
                    False,
                    f"Failed to start service {service_name}"
                )
                
        except Exception as e:
            return CommandResult(
                False,
                f"Error restarting service: {e}"
            )
    
    @classmethod
    def restart_all_services(cls) -> CommandResult:
        """Restart all services"""
        results = []
        success = True
        
        for service_type in [ServiceType.DISCORD, ServiceType.WEB]:
            result = cls.restart_service(service_type)
            results.append(f"{service_type.value}: {result.message}")
            if not result.success:
                success = False
        
        return CommandResult(
            success,
            "\n".join(results)
        )
    
    @classmethod
    def setup_service(cls, service_type: ServiceType, token: Optional[str] = None) -> CommandResult:
        """Setup a service with systemd"""
        script_path = '/home/ubuntu/claude/setup_services.sh'
        
        if service_type == ServiceType.DISCORD:
            if not token:
                return CommandResult(False, "Discord token required")
            result = subprocess.run([script_path, 'setup-discord', token])
        elif service_type == ServiceType.ALL:
            if not token:
                return CommandResult(False, "Discord token required for full setup")
            result = subprocess.run([script_path, 'setup-all', token])
        else:
            return CommandResult(False, f"Setup not available for {service_type.value}")
        
        return CommandResult(
            result.returncode == 0,
            f"Setup {'successful' if result.returncode == 0 else 'failed'}"
        )
    
    @classmethod
    def get_discord_service_status(cls) -> Dict[str, Any]:
        """Get Discord service status from the SINGLE source"""
        try:
            from discord_service import discord_service
            return discord_service.get_statistics()
        except Exception:
            return {'enabled': False, 'running': False, 'error': 'Discord service not available'}
    
    @classmethod
    def show_all_status(cls) -> str:
        """Get formatted status of all services"""
        services = [ServiceType.DISCORD, ServiceType.WEB]
        output = ["Service Status:"]
        output.append("-" * 60)
        
        for service_type in services:
            status = cls.get_service_status(service_type)
            status_str = "✅ RUNNING" if status.running else "❌ STOPPED"
            output.append(f"{status.service_name:20} {status_str}")
            
            if status.running and status.pid:
                output.append(f"  PID: {status.pid}")
                if status.uptime:
                    output.append(f"  Uptime: {status.uptime}")
                if status.memory:
                    output.append(f"  Memory: {status.memory}")
        
        return "\n".join(output)


class TournamentCommand:
    """Main command interface for tournament tracker"""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the command interface"""
        self.tracker = None
        self.database_url = database_url
        self._ensure_tracker()
    
    def _ensure_tracker(self):
        """Ensure tracker is initialized"""
        if not self.tracker:
            self.tracker = TournamentTracker(database_url=self.database_url)
    
    # Sync Operations
    def sync_tournaments(self, 
                        page_size: int = 250, 
                        fetch_standings: bool = False,
                        standings_limit: int = 5) -> CommandResult:
        """Sync tournaments from start.gg"""
        self._ensure_tracker()
        try:
            success = self.tracker.sync_tournaments(
                page_size=page_size,
                fetch_standings=fetch_standings,
                standings_limit=standings_limit
            )
            
            if success:
                message = "Tournament sync completed successfully"
                
                # Auto-identify organizations after sync
                from identify_orgs_simple import analyze_and_auto_create
                try:
                    newly_identified = analyze_and_auto_create(
                        auto_mode=True, 
                        confidence_threshold=0.8
                    )
                    if newly_identified > 0:
                        message += f"\n✓ Automatically identified {newly_identified} new organizations"
                except Exception as e:
                    log_debug(f"Organization identification failed: {e}", "sync")
                
                return CommandResult(True, message)
            else:
                return CommandResult(False, "Tournament sync failed")
                
        except Exception as e:
            return CommandResult(False, f"Sync error: {e}")
    
    # Report Operations
    def generate_console_report(self, limit: Optional[int] = None) -> CommandResult:
        """Generate console report"""
        self._ensure_tracker()
        try:
            self.tracker.show_console_report(limit=limit)
            return CommandResult(True, "Console report generated")
        except Exception as e:
            return CommandResult(False, f"Report error: {e}")
    
    def generate_html_report(self, 
                           output_file: str, 
                           limit: Optional[int] = None) -> CommandResult:
        """Generate HTML report"""
        self._ensure_tracker()
        try:
            self.tracker.generate_html_report(limit=limit, output_file=output_file)
            return CommandResult(True, f"HTML report saved to {output_file}")
        except Exception as e:
            return CommandResult(False, f"HTML generation error: {e}")
    
    # Shopify Operations - ALL using the SINGLE shopify_service
    def publish_to_shopify(self, format: str = "html") -> CommandResult:
        """Publish to Shopify using shopify_service"""
        from shopify_service import shopify_service, PublishFormat
        
        if not shopify_service.is_enabled:
            return CommandResult(
                False,
                "Shopify service not enabled. Set SHOPIFY_DOMAIN and SHOPIFY_ACCESS_TOKEN."
            )
        
        try:
            format_enum = PublishFormat(format.lower())
        except ValueError:
            return CommandResult(False, f"Invalid format: {format}. Use html, json, markdown, or csv")
        
        result = shopify_service.publish_tournament_rankings(format=format_enum)
        
        if result.success:
            return CommandResult(
                True,
                f"Published to Shopify successfully (ID: {result.resource_id}, Size: {result.data_size} bytes)"
            )
        else:
            return CommandResult(False, f"Shopify publishing failed: {result.error}")
    
    def show_shopify_stats(self) -> CommandResult:
        """Show Shopify service statistics"""
        from shopify_service import shopify_service
        
        stats = shopify_service.get_statistics()
        
        # Format statistics for display
        output = "\n=== Shopify Service Statistics (SINGLE SOURCE OF TRUTH) ===\n"
        output += f"Enabled: {stats['enabled']}\n"
        
        if stats['enabled']:
            output += f"Store: {stats['config']['store_domain']}\n"
            output += f"API Version: {stats['config']['api_version']}\n"
            output += f"\nPublishing Statistics:\n"
            for key, value in stats['statistics'].items():
                if isinstance(value, dict):
                    output += f"  {key}:\n"
                    for k, v in value.items():
                        output += f"    {k}: {v}\n"
                else:
                    output += f"  {key}: {value}\n"
        
        print(output)
        return CommandResult(True, "Shopify statistics displayed")
    
    # Heatmap Operations
    def generate_heatmaps(self) -> CommandResult:
        """Generate all heatmap visualizations"""
        try:
            from tournament_heatmap import (
                generate_static_heatmap, 
                generate_attendance_heatmap, 
                generate_interactive_heatmap
            )
            
            files_created = []
            
            # Generate heatmaps
            if generate_static_heatmap('tournament_heatmap.png', use_map_background=True):
                files_created.append('tournament_heatmap.png')
            
            if generate_static_heatmap('tournament_heatmap_with_map.png', use_map_background=True):
                files_created.append('tournament_heatmap_with_map.png')
            
            if generate_attendance_heatmap():
                files_created.append('attendance_heatmap.png')
            
            if generate_interactive_heatmap():
                files_created.append('tournament_heatmap.html')
            
            return CommandResult(
                True,
                f"Generated {len(files_created)} heatmap files",
                data=files_created
            )
            
        except Exception as e:
            return CommandResult(False, f"Heatmap generation error: {e}")
    
    # Editor Operations  
    def launch_web_search(self, port: int = 8083) -> CommandResult:
        """Launch web search interface"""
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, 'web_search.py', '--port', str(port)],
                cwd='/home/ubuntu/claude/tournament_tracker'
            )
            return CommandResult(
                result.returncode == 0,
                f"Web search interface stopped"
            )
        except Exception as e:
            return CommandResult(False, f"Web search error: {e}")
    
    def launch_web_editor(self, port: int = 8081) -> CommandResult:
        """Launch web editor for contact management"""
        try:
            # Ensure single instance
            ProcessManager.ensure_single_instance('editor_web')
            
            # Ensure database is initialized
            self._ensure_tracker()
            self.tracker._ensure_db_initialized()
            
            # Start editor
            from editor_service import editor_service
            print(f"Starting web editor on port {port}...")
            print(f"Access at: http://localhost:{port}")
            editor_service.config.port = port
            editor_service.run_blocking()
            
            return CommandResult(True, "Web editor started")
            
        except KeyboardInterrupt:
            return CommandResult(True, "Web editor stopped by user")
        except Exception as e:
            return CommandResult(False, f"Editor error: {e}")
    
    # Claude/AI Operations - ALL using the SINGLE claude_service
    def launch_ai_chat(self) -> CommandResult:
        """Launch terminal AI chat interface using claude_service"""
        from claude_service import claude_service
        
        if not claude_service.is_enabled:
            return CommandResult(
                False,
                "Claude service not enabled. Set ANTHROPIC_API_KEY to enable."
            )
        
        result = claude_service.start_terminal_chat()
        return CommandResult(
            result.success,
            result.response or result.error
        )
    
    def launch_ai_web(self, port: int = 8082) -> CommandResult:
        """Launch web-based AI chat interface using claude_service"""
        from claude_service import claude_service
        
        if not claude_service.is_enabled:
            return CommandResult(
                False,
                "Claude service not enabled. Set ANTHROPIC_API_KEY to enable."
            )
        
        result = claude_service.start_web_chat(port=port)
        return CommandResult(
            result.success,
            result.response or result.error
        )
    
    def ask_ai(self, question: str) -> CommandResult:
        """Ask Claude a single question using claude_service"""
        from claude_service import claude_service
        
        if not claude_service.is_enabled:
            return CommandResult(
                False,
                "Claude service not enabled. Set ANTHROPIC_API_KEY to enable."
            )
        
        # Check if this is a heatmap-related question
        if any(word in question.lower() for word in ['heat map', 'heatmap', 'heat-map']):
            if any(word in question.lower() for word in ['make', 'create', 'generate', 'update']):
                # Generate heatmaps first
                heatmap_result = self.generate_heatmaps()
                
                # Ask Claude with context about heatmaps
                result = claude_service.ask_question(
                    question,
                    context={'heatmap_generated': True, 'heatmap_result': heatmap_result.message}
                )
                
                if result.success:
                    response = f"{result.response}\n\n{heatmap_result.message}"
                    return CommandResult(True, response)
                else:
                    return CommandResult(False, result.error)
        
        # Regular question
        result = claude_service.ask_question(question)
        return CommandResult(
            result.success,
            result.response or result.error
        )
    
    def show_claude_stats(self) -> CommandResult:
        """Show Claude service statistics"""
        from claude_service import claude_service
        
        stats = claude_service.get_statistics()
        
        # Format statistics for display
        output = "\n=== Claude Service Statistics ===\n"
        output += f"Enabled: {stats['enabled']}\n"
        
        if stats['enabled']:
            output += f"Model: {stats['config']['model']}\n"
            output += f"\nUsage:\n"
            for key, value in stats['usage'].items():
                output += f"  {key}: {value}\n"
            output += f"\nHistory size: {stats['history_size']} conversations\n"
        
        print(output)
        return CommandResult(True, "Claude statistics displayed")
    
    # Discord Bot Operations - ALL using the SINGLE discord_service
    def show_discord_stats(self) -> CommandResult:
        """Show Discord service statistics"""
        from discord_service import discord_service
        
        stats = discord_service.get_statistics()
        
        # Format statistics for display
        output = "\n=== Discord Service Statistics (SINGLE SOURCE OF TRUTH) ===\n"
        output += f"Enabled: {stats['enabled']}\n"
        output += f"Running: {stats['running']}\n"
        
        if stats['enabled']:
            output += f"\nConfiguration:\n"
            for key, value in stats['config'].items():
                output += f"  {key}: {value}\n"
            
            output += f"\nStatistics:\n"
            for key, value in stats['stats'].items():
                output += f"  {key}: {value}\n"
        
        print(output)
        return CommandResult(True, "Discord statistics displayed")
    
    def start_discord_bot(self, mode: Optional[str] = None) -> CommandResult:
        """Start Discord bot using discord_service"""
        from discord_service import discord_service, BotMode
        
        if not discord_service.is_enabled:
            return CommandResult(
                False,
                "Discord service not enabled. Set DISCORD_BOT_TOKEN to enable."
            )
        
        if mode:
            try:
                discord_service.config.mode = BotMode(mode)
            except ValueError:
                return CommandResult(False, f"Invalid mode: {mode}")
        
        try:
            print(f"Starting Discord bot in {discord_service.config.mode.value} mode...")
            discord_service.run_blocking()
            return CommandResult(True, "Discord bot stopped")
        except Exception as e:
            return CommandResult(False, f"Discord bot error: {e}")
    
    # Utility Operations
    def show_statistics(self) -> CommandResult:
        """Show database statistics"""
        self._ensure_tracker()
        try:
            self.tracker.show_statistics()
            return CommandResult(True, "Statistics displayed")
        except Exception as e:
            return CommandResult(False, f"Statistics error: {e}")
    
    def identify_organizations(self) -> CommandResult:
        """Launch organization identification tool"""
        try:
            result = subprocess.run([sys.executable, 'identify_orgs_simple.py'])
            return CommandResult(
                result.returncode == 0,
                "Organization identification completed"
            )
        except Exception as e:
            return CommandResult(False, f"Identification error: {e}")
    
    def launch_interactive_mode(self) -> CommandResult:
        """Launch interactive mode"""
        try:
            from go_interactive import start_interactive_mode
            start_interactive_mode(database_url=self.database_url)
            return CommandResult(True, "Interactive mode ended")
        except Exception as e:
            return CommandResult(False, f"Interactive mode error: {e}")


class CommandLineInterface:
    """Main CLI interface for the tournament tracker"""
    
    def __init__(self):
        """Initialize CLI"""
        self.parser = self._create_parser()
        self.command = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all options"""
        parser = argparse.ArgumentParser(
            description='Tournament Tracker - SoCal FGC Edition',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  ./go.py --sync                    # Sync tournaments from start.gg
  ./go.py --console                  # Show console report
  ./go.py --html report.html        # Generate HTML report
  ./go.py --restart-services         # Restart all services
  ./go.py --edit-contacts            # Launch web editor
  ./go.py --heatmap                  # Generate heat maps
  ./go.py --ai-ask "Show me the top 10"  # Ask AI a question
            """
        )
        
        # Sync options
        sync_group = parser.add_argument_group('Sync Options')
        sync_group.add_argument('--sync', action='store_true', 
                                help='Sync tournaments from start.gg')
        sync_group.add_argument('--skip-sync', action='store_true', 
                                help='Skip start.gg sync')
        sync_group.add_argument('--fetch-standings', action='store_true', 
                                help='Fetch top 8 standings for major tournaments')
        sync_group.add_argument('--standings-limit', type=int, default=5, 
                                help='Limit standings fetch (default: 5)')
        sync_group.add_argument('--page-size', type=int, default=250, 
                                help='Queue page size (default: 250)')
        
        # Output options
        output_group = parser.add_argument_group('Output Options')
        output_group.add_argument('--console', action='store_true', 
                                 help='Show console report')
        output_group.add_argument('--html', metavar='FILE', 
                                 help='Generate HTML report to file')
        output_group.add_argument('--publish', action='store_true', 
                                 help='Publish to Shopify (legacy)')
        output_group.add_argument('--limit', type=int, 
                                 help='Limit number of results')
        
        # Service management
        service_group = parser.add_argument_group('Service Management')
        service_group.add_argument('--setup-discord', metavar='TOKEN', 
                                  help='Setup Discord bot service')
        service_group.add_argument('--setup-services', metavar='TOKEN', 
                                  help='Setup all services')
        service_group.add_argument('--service-status', action='store_true', 
                                  help='Check service status')
        service_group.add_argument('--restart-discord', action='store_true', 
                                  help='Restart Discord bot')
        service_group.add_argument('--restart-web', action='store_true', 
                                  help='Restart web service')
        service_group.add_argument('--restart-services', action='store_true', 
                                  help='Restart all services')
        
        # Discord Bot Options - ALL through discord_service (SINGLE SOURCE OF TRUTH)
        discord_group = parser.add_argument_group('Discord Bot (SINGLE SOURCE OF TRUTH)')
        discord_group.add_argument('--discord-bot', action='store_true',
                                  help='Start Discord bot')
        discord_group.add_argument('--discord-mode', choices=['simple', 'conversational', 'claude', 'hybrid'],
                                  default='conversational', help='Discord bot mode')
        discord_group.add_argument('--discord-stats', action='store_true',
                                  help='Show Discord service statistics')
        
        # Shopify Options - ALL through shopify_service (SINGLE SOURCE OF TRUTH)
        shopify_group = parser.add_argument_group('Shopify Publishing (SINGLE SOURCE OF TRUTH)')
        shopify_group.add_argument('--shopify-publish', action='store_true',
                                  help='Publish tournament rankings to Shopify')
        shopify_group.add_argument('--shopify-format', choices=['html', 'json', 'markdown', 'csv'],
                                  default='html', help='Publishing format')
        shopify_group.add_argument('--shopify-stats', action='store_true',
                                  help='Show Shopify service statistics')
        shopify_group.add_argument('--shopify-test', action='store_true',
                                  help='Test Shopify connection')
        
        # Editor options
        editor_group = parser.add_argument_group('Editor Options')
        editor_group.add_argument('--web-search', action='store_true',
                                 help='Launch web search interface')
        editor_group.add_argument('--search-port', type=int, default=8083,
                                 help='Search web port (default: 8083)')
        editor_group.add_argument('--edit-contacts', action='store_true', 
                                 help='Launch web editor')
        editor_group.add_argument('--editor-port', type=int, default=8081, 
                                 help='Editor port (default: 8081)')
        
        # Claude/AI options - ALL through claude_service
        ai_group = parser.add_argument_group('Claude AI Interface (SINGLE SOURCE OF TRUTH)')
        ai_group.add_argument('--ai-chat', action='store_true', 
                             help='Launch terminal Claude chat')
        ai_group.add_argument('--ai-web', action='store_true', 
                             help='Launch web Claude chat')
        ai_group.add_argument('--ai-web-port', type=int, default=8082, 
                             help='Claude web port (default: 8082)')
        ai_group.add_argument('--ai-ask', metavar='QUESTION', 
                             help='Ask Claude a single question')
        ai_group.add_argument('--claude-stats', action='store_true',
                             help='Show Claude service statistics')
        
        # Utility options
        util_group = parser.add_argument_group('Utility Options')
        util_group.add_argument('--stats', action='store_true', 
                               help='Show statistics')
        util_group.add_argument('--interactive', '-i', action='store_true', 
                               help='Interactive mode')
        util_group.add_argument('--heatmap', action='store_true', 
                               help='Generate heat maps')
        util_group.add_argument('--identify-orgs', action='store_true', 
                               help='Identify organizations')
        util_group.add_argument('--database-url', 
                               help='Database URL')
        
        return parser
    
    def run(self, argv: Optional[List[str]] = None) -> int:
        """Run the CLI with given arguments"""
        args = self.parser.parse_args(argv)
        
        # Show help if no arguments
        if len(sys.argv) == 1:
            self.parser.print_help()
            return 0
        
        # Initialize command handler
        self.command = TournamentCommand(database_url=args.database_url)
        
        try:
            # Service management (priority)
            if args.setup_discord:
                result = ServiceManager.setup_service(ServiceType.DISCORD, args.setup_discord)
                print(result.message)
                return result.return_code
            
            if args.setup_services:
                result = ServiceManager.setup_service(ServiceType.ALL, args.setup_services)
                print(result.message)
                return result.return_code
            
            if args.service_status:
                print(ServiceManager.show_all_status())
                return 0
            
            if args.restart_discord:
                result = ServiceManager.restart_service(ServiceType.DISCORD)
                print(result.message)
                return 0 if result.success else 1
            
            if hasattr(args, 'restart_web') and args.restart_web:
                result = ServiceManager.restart_service(ServiceType.WEB)
                print(result.message)
                return 0 if result.success else 1
            
            if args.restart_services:
                result = ServiceManager.restart_all_services()
                print(result.message)
                return 0 if result.success else 1
            
            # AI operations
            if args.ai_chat:
                result = self.command.launch_ai_chat()
                return result.return_code
            
            if args.ai_web:
                result = self.command.launch_ai_web(port=args.ai_web_port)
                return result.return_code
            
            if args.ai_ask:
                result = self.command.ask_ai(args.ai_ask)
                print(result.message)
                return 0 if result.success else 1
            
            # Utility operations
            if args.identify_orgs:
                result = self.command.identify_organizations()
                return result.return_code
            
            if args.heatmap:
                result = self.command.generate_heatmaps()
                if result.success:
                    print(f"✅ {result.message}")
                    if result.data:
                        print("\nGenerated files:")
                        for filename in result.data:
                            print(f"  • {filename}")
                else:
                    print(f"❌ {result.message}")
                return 0 if result.success else 1
            
            # Sync operations (unless skipped)
            if not args.skip_sync and (args.sync or args.fetch_standings or 
                                       args.publish or not any([args.console, args.html, 
                                                               args.stats, args.interactive])):
                result = self.command.sync_tournaments(
                    page_size=args.page_size,
                    fetch_standings=args.fetch_standings,
                    standings_limit=args.standings_limit
                )
                if not result.success and not args.interactive:
                    print(f"❌ {result.message}")
                    return 1
                elif result.success:
                    print(f"✅ {result.message}")
            
            # Report generation
            if args.console:
                result = self.command.generate_console_report(limit=args.limit)
                if not result.success:
                    print(f"❌ {result.message}")
                    return 1
            
            if args.html:
                result = self.command.generate_html_report(args.html, limit=args.limit)
                print(f"{'✅' if result.success else '❌'} {result.message}")
                if not result.success:
                    return 1
            
            if args.publish:
                result = self.command.publish_to_shopify()
                print(f"{'✅' if result.success else '❌'} {result.message}")
                if not result.success:
                    return 1
            
            # Other operations
            if args.stats:
                result = self.command.show_statistics()
                if not result.success:
                    print(f"❌ {result.message}")
                    return 1
            
            if args.interactive:
                result = self.command.launch_interactive_mode()
                return result.return_code
            
            if args.web_search:
                result = self.command.launch_web_search(port=args.search_port)
                return result.return_code
            
            if args.edit_contacts:
                result = self.command.launch_web_editor(port=args.editor_port)
                return result.return_code
            
            # Claude/AI operations - ALL through claude_service
            if args.ai_chat:
                result = self.command.launch_ai_chat()
                return result.return_code
            
            if args.ai_web:
                result = self.command.launch_ai_web(port=args.ai_web_port)
                return result.return_code
            
            if args.ai_ask:
                result = self.command.ask_ai(args.ai_ask)
                print(result.message)
                return 0 if result.success else 1
            
            if args.claude_stats:
                result = self.command.show_claude_stats()
                return 0 if result.success else 1
            
            # Discord Bot operations - ALL through discord_service
            if args.discord_bot:
                result = self.command.start_discord_bot(mode=args.discord_mode)
                return result.return_code
            
            if args.discord_stats:
                result = self.command.show_discord_stats()
                return 0 if result.success else 1
            
            # Shopify operations - ALL through shopify_service
            if args.shopify_publish:
                result = self.command.publish_to_shopify(format=args.shopify_format)
                print(f"{'✅' if result.success else '❌'} {result.message}")
                return 0 if result.success else 1
            
            if args.shopify_stats:
                result = self.command.show_shopify_stats()
                return 0 if result.success else 1
            
            if args.shopify_test:
                from shopify_service import shopify_service
                if shopify_service.test_connection():
                    print("✅ Shopify connection successful")
                    return 0
                else:
                    print("❌ Shopify connection failed")
                    return 1
            
            return 0
            
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
            return 130
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Main entry point"""
    cli = CommandLineInterface()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()