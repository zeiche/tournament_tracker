#!/usr/bin/env python3
"""
go_polymorphic.py - The Polymorphic Entry Point

Instead of 50+ command-line flags, just THREE methods:
- go.ask("what services are running")
- go.tell("status")  
- go.do("start discord bot")

This is the ULTIMATE simplification of go.py
"""

import sys
import os
import subprocess
sys.path.insert(0, 'utils')
from universal_polymorphic import UniversalPolymorphic
from capability_announcer import announcer

# Set authorization
os.environ['GO_PY_AUTHORIZED'] = '1'

# Load .env
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")


class GoPolymorphic(UniversalPolymorphic):
    """
    The polymorphic entry point for everything.
    No more command flags - just ask/tell/do!
    """
    
    def __init__(self):
        self.services = {
            'discord': 'bonjour_discord.py',
            'discord bot': 'bonjour_discord.py',
            'editor': 'editor_service.py',
            'web editor': 'editor_service.py',
            'edit contacts': 'editor_service.py',
            'ai': 'claude_service.py',
            'ai chat': 'claude_service.py',
            'claude': 'claude_service.py',
            'sync': 'sync_service.py',
            'console': 'tournament_report.py',
            'report': 'tournament_report.py',
            'heatmap': 'tournament_heatmap.py',
            'stats': 'database_service.py',
            'statistics': 'database_service.py',
            'twilio': 'twilio_simple_voice_bridge.py',
            'twilio bridge': 'twilio_simple_voice_bridge.py',
            'phone': 'twilio_simple_voice_bridge.py',
            'voice': 'twilio_simple_voice_bridge.py',
            'call': 'call_me.py',
            'bonjour': 'bonjour_monitor.py',
            'monitor': 'bonjour_monitor.py'
        }
        
        # Now call parent init
        super().__init__()
        
        # Announce ourselves
        announcer.announce(
            "GoPolymorphic",
            [
                "I'm the polymorphic entry point",
                "Use go.ask(), go.tell(), go.do()",
                "No more command flags!",
                "Examples:",
                "  go.do('start discord bot')",
                "  go.do('sync')",
                "  go.ask('what services')",
                "  go.tell('status')"
            ]
        )
    
    def _handle_ask(self, question: str, **kwargs):
        """Handle questions about services"""
        q = str(question).lower()
        
        if any(word in q for word in ['service', 'available', 'what can']):
            return list(self.services.keys())
        
        if any(word in q for word in ['running', 'active', 'status']):
            return self._check_running_services()
        
        if any(word in q for word in ['help', 'usage', 'how']):
            return self._get_detailed_help()
        
        return f"Services available: {', '.join(self.services.keys())}"
    
    def _handle_tell(self, format: str, **kwargs):
        """Tell about services and status"""
        if format in ['status', 'services']:
            running = self._check_running_services()
            return f"Running: {running}\nAvailable: {list(self.services.keys())}"
        
        if format in ['help', 'usage']:
            return self._get_detailed_help()
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs):
        """Do service actions - the main functionality"""
        act = str(action).lower()
        
        # Parse action for service names
        for service_name, script in self.services.items():
            if service_name in act:
                if any(word in act for word in ['start', 'run', 'launch']):
                    return self._start_service(script, service_name)
                elif any(word in act for word in ['stop', 'kill', 'end']):
                    return self._stop_service(service_name)
                elif any(word in act for word in ['restart']):
                    self._stop_service(service_name)
                    return self._start_service(script, service_name)
                else:
                    # Default to starting if just service name
                    return self._start_service(script, service_name)
        
        # Special actions
        if 'restart' in act and 'all' in act:
            return self._restart_all_services()
        
        if 'stop' in act and 'all' in act:
            return self._stop_all_services()
        
        if 'call' in act:
            # Extract phone number
            import re
            phone_match = re.search(r'[\d\-\(\)\+\s]+', action)
            if phone_match:
                phone = phone_match.group().strip()
                return self._make_call(phone)
        
        return f"Don't know how to: {action}\nTry: go.do('start discord bot')"
    
    def _start_service(self, script: str, name: str):
        """Start a service"""
        try:
            # Check if script exists
            if not os.path.exists(script):
                return f"Service script not found: {script}"
            
            # Start the service
            process = subprocess.Popen([sys.executable, script])
            
            # Announce
            announcer.announce(
                "SERVICE_STARTED",
                [f"Started {name}", f"PID: {process.pid}", f"Script: {script}"]
            )
            
            return f"Started {name} (PID: {process.pid})"
        except Exception as e:
            return f"Failed to start {name}: {e}"
    
    def _stop_service(self, name: str):
        """Stop a service"""
        try:
            # Find and kill processes
            result = subprocess.run(
                ['pkill', '-f', self.services.get(name, name)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return f"Stopped {name}"
            else:
                return f"No running process for {name}"
        except Exception as e:
            return f"Failed to stop {name}: {e}"
    
    def _restart_all_services(self):
        """Restart all services"""
        results = []
        for name in self.services:
            self._stop_service(name)
        results.append("Stopped all services")
        return "\n".join(results)
    
    def _stop_all_services(self):
        """Stop all services"""
        results = []
        for name in self.services:
            result = self._stop_service(name)
            if "Stopped" in result:
                results.append(result)
        return "\n".join(results) if results else "No services were running"
    
    def _check_running_services(self):
        """Check which services are running"""
        running = []
        for name, script in self.services.items():
            try:
                result = subprocess.run(
                    ['pgrep', '-f', script],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    running.append(name)
            except:
                pass
        return running if running else ["No services running"]
    
    def _make_call(self, phone: str):
        """Make an outbound call"""
        try:
            subprocess.run([sys.executable, 'call_me.py', phone])
            return f"Calling {phone}..."
        except Exception as e:
            return f"Failed to call: {e}"
    
    def _get_detailed_help(self):
        """Get detailed help"""
        return """
GoPolymorphic - The Universal Entry Point

Instead of command flags, use the 3 methods:

ASK - Query information:
  go.ask("what services")         # List available services
  go.ask("running")               # Check running services
  go.ask("status")                # Get status

TELL - Get formatted output:
  go.tell("status")               # Service status
  go.tell("json")                 # JSON output
  go.tell("help")                 # This help

DO - Perform actions:
  go.do("start discord bot")      # Start Discord bot
  go.do("start twilio")           # Start Twilio bridge
  go.do("sync")                   # Run sync
  go.do("heatmap")                # Generate heatmap
  go.do("restart all")            # Restart everything
  go.do("stop all")               # Stop everything
  go.do("call 555-1234")          # Make phone call

Available services:
""" + "\n".join(f"  - {name}" for name in sorted(set(self.services.keys())))
    
    def _get_capabilities(self):
        """List our capabilities"""
        return [
            "ask('what services')",
            "ask('running')",
            "tell('status')",
            "do('start discord bot')",
            "do('start twilio')",
            "do('sync')",
            "do('restart all')",
            f"Can manage {len(self.services)} services"
        ]


# Create global instance
go = GoPolymorphic()


def main():
    """Main entry point - now polymorphic!"""
    import sys
    
    if len(sys.argv) < 2:
        # No arguments - show help
        print(go.tell("help"))
        return
    
    # Parse polymorphic command
    command = sys.argv[1].lower()
    args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    
    # Route to appropriate method
    if command in ['ask', 'query', 'what', 'show']:
        result = go.ask(args)
        print(result if isinstance(result, str) else str(result))
    
    elif command in ['tell', 'format', 'output']:
        result = go.tell(args if args else "default")
        print(result if isinstance(result, str) else str(result))
    
    elif command in ['do', 'run', 'start', 'stop', 'restart']:
        if command != 'do':
            # Allow "go start discord" instead of "go do start discord"
            args = f"{command} {args}"
        result = go.do(args)
        print(result if isinstance(result, str) else str(result))
    
    else:
        # Try to interpret as action
        full_command = f"{command} {args}".strip()
        result = go.do(full_command)
        print(result if isinstance(result, str) else str(result))


if __name__ == "__main__":
    main()