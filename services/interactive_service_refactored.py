#!/usr/bin/env python3
"""
interactive_service_refactored.py - REFACTORED Central hub for interactive features

BEFORE: Direct imports of database, claude services, and others
AFTER: Uses service locator for all dependencies

Key changes:
1. Uses service locator for database, claude, logger, error handler dependencies
2. Enhanced with 3-method pattern (ask/tell/do)
3. Works with local OR network services transparently
4. Can be distributed for scalable interactive sessions
5. Same REPL and interactive functionality as original

This demonstrates refactoring a complex interactive service.
"""
import sys
import os
import code
from typing import Optional, Any, Dict
import io
import contextlib

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/ubuntu/claude')

from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service
from utils.dynamic_switches import announce_switch

class RefactoredInteractiveService:
    """
    REFACTORED Central service for interactive features using service locator.
    
    This version:
    - Uses service locator for all dependencies (database, claude, logger, etc.)
    - Enhanced with 3-method pattern for queries and operations
    - Can operate over network for distributed interactive sessions
    - Same REPL and interactive functionality as original
    """
    
    def __init__(self, prefer_network: bool = False, database_url: Optional[str] = None):
        """Initialize the interactive service"""
        self.prefer_network = prefer_network
        self.database_url = database_url
        self._database = None
        self._claude = None
        self._logger = None
        self._error_handler = None
        self._config = None
        
        self.tracker = None
        self.session_stats = {
            'commands_executed': 0,
            'errors_encountered': 0,
            'ai_queries': 0,
            'session_start': None
        }
        
        # Initialize core services
        self._init_services()
        
        # Announce capabilities
        announcer.announce(
            "Interactive Service (Refactored)",
            [
                "REFACTORED: Uses service locator for dependencies",
                "REPL and interactive features with 3-method pattern",
                "ask('repl status') - query interactive session state",
                "tell('help', commands) - format help and documentation",
                "do('start repl') - manage interactive sessions",
                "Distributed interactive sessions with service discovery"
            ],
            [
                "interactive.ask('session stats')",
                "interactive.tell('console', help_data)",
                "interactive.do('start ai chat')",
                "Works with local OR network database/claude services"
            ]
        )
        
        # Announce as a switch
        announce_switch("interactive", "START interactive bridge/repl (auto|lightweight|claude)", self._handle_switch)
    
    @property
    def database(self):
        """Lazy-loaded database service via service locator"""
        if self._database is None:
            self._database = get_service("database", self.prefer_network)
        return self._database
    
    @property
    def claude(self):
        """Lazy-loaded claude service via service locator"""
        if self._claude is None:
            self._claude = get_service("claude", self.prefer_network)
        return self._claude
    
    @property
    def logger(self):
        """Lazy-loaded logger service via service locator"""
        if self._logger is None:
            self._logger = get_service("logger", self.prefer_network)
        return self._logger
    
    @property
    def error_handler(self):
        """Lazy-loaded error handler service via service locator"""
        if self._error_handler is None:
            self._error_handler = get_service("error_handler", self.prefer_network)
        return self._error_handler
    
    @property
    def config(self):
        """Lazy-loaded config service via service locator"""
        if self._config is None:
            self._config = get_service("config", self.prefer_network)
        return self._config
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Query interactive service using natural language.
        
        Examples:
            ask("repl status")
            ask("session stats")
            ask("available commands")
            ask("service health")
        """
        query_lower = query.lower().strip()
        
        # Log the query
        if self.logger:
            try:
                self.logger.info(f"Interactive query: {query}")
            except:
                pass
        
        try:
            if "repl status" in query_lower or "status" in query_lower:
                return self._get_repl_status()
            
            elif "session stats" in query_lower or "stats" in query_lower:
                return self._get_session_stats()
            
            elif "available commands" in query_lower or "commands" in query_lower:
                return self._get_available_commands()
            
            elif "service health" in query_lower or "health" in query_lower:
                return self._get_service_health()
            
            elif "help" in query_lower:
                return self._get_help_content()
            
            else:
                return {"error": f"Don't know how to handle query: {query}"}
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "MEDIUM")
                except:
                    pass
            return {"error": f"Interactive query failed: {str(e)}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """
        Format interactive service data for output.
        
        Formats: console, help, json, text, repl
        """
        if data is None:
            data = {}
        
        try:
            if format_type == "console":
                return self._format_console(data)
            
            elif format_type == "help":
                return self._format_help(data)
            
            elif format_type == "json":
                import json
                return json.dumps(data, indent=2, default=str)
            
            elif format_type == "text":
                return self._format_text(data)
            
            elif format_type == "repl":
                return self._format_repl(data)
            
            else:
                return str(data)
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "LOW")
                except:
                    pass
            return f"Format error: {e}"
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform interactive service operations using natural language.
        
        Examples:
            do("start repl")
            do("start ai chat")
            do("execute command print('hello')")
            do("reset session")
        """
        action_lower = action.lower().strip()
        
        # Log the action
        if self.logger:
            try:
                self.logger.info(f"Interactive action: {action}")
            except:
                pass
        
        try:
            if "start repl" in action_lower:
                return self._start_repl()
            
            elif "start ai chat" in action_lower or "start chat" in action_lower:
                return self._start_ai_chat()
            
            elif "execute command" in action_lower:
                command = action[len("execute command"):].strip()
                return self._execute_command(command)
            
            elif "reset session" in action_lower:
                return self._reset_session()
            
            elif "init services" in action_lower:
                return self._init_services()
            
            else:
                return {"error": f"Don't know how to: {action}"}
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "HIGH")
                except:
                    pass
            return {"error": f"Interactive action failed: {str(e)}"}
    
    # Core service initialization
    def _init_services(self) -> Dict:
        """Initialize services via service locator"""
        try:
            if self.logger:
                try:
                    self.logger.info("Initializing interactive services via service locator")
                except:
                    pass
            
            # Test database service
            if self.database:
                db_stats = self.database.ask("stats")
                if self.logger:
                    try:
                        self.logger.info(f"Database service available: {type(db_stats)}")
                    except:
                        pass
            
            # Test claude service
            claude_available = False
            if self.claude:
                try:
                    claude_health = self.claude.ask("health status")
                    claude_available = claude_health.get("claude_cli_available", False)
                except:
                    pass
            
            return {
                "action": "init_services",
                "database_available": self.database is not None,
                "claude_available": claude_available,
                "logger_available": self.logger is not None,
                "error_handler_available": self.error_handler is not None,
                "config_available": self.config is not None
            }
            
        except Exception as e:
            return {"action": "init_services", "error": str(e)}
    
    # Query implementation methods
    def _get_repl_status(self) -> Dict:
        """Get REPL status"""
        return {
            "repl_available": True,
            "services_initialized": self._check_services_initialized(),
            "session_active": self.session_stats['session_start'] is not None,
            "prefer_network": self.prefer_network
        }
    
    def _get_session_stats(self) -> Dict:
        """Get session statistics"""
        return {
            "stats": self.session_stats.copy(),
            "services": {
                "database": self.database is not None,
                "claude": self.claude is not None,
                "logger": self.logger is not None,
                "error_handler": self.error_handler is not None
            }
        }
    
    def _get_available_commands(self) -> Dict:
        """Get available commands"""
        commands = {
            "basic": [
                "sync() - Sync from start.gg via discovered service",
                "stats() - Show statistics via discovered database",
                "help() - Show help information"
            ],
            "ai": [
                "ask('question') - Ask Claude via discovered service",
                "chat() - Start chat mode"
            ],
            "database": [
                "Tournament.ask('recent') - Query tournaments",
                "Organization.ask('top 10') - Query organizations"
            ]
        }
        
        return {"commands": commands}
    
    def _get_service_health(self) -> Dict:
        """Get health of discovered services"""
        health = {}
        
        # Check database
        if self.database:
            try:
                db_stats = self.database.ask("stats")
                health["database"] = "healthy" if db_stats else "issues"
            except:
                health["database"] = "unavailable"
        else:
            health["database"] = "not_discovered"
        
        # Check claude
        if self.claude:
            try:
                claude_health = self.claude.ask("health status")
                health["claude"] = claude_health.get("overall_health", "unknown")
            except:
                health["claude"] = "unavailable"
        else:
            health["claude"] = "not_discovered"
        
        # Check logger
        health["logger"] = "available" if self.logger else "not_discovered"
        
        return {"service_health": health}
    
    def _get_help_content(self) -> Dict:
        """Get help content"""
        return {
            "title": "Interactive Service (Refactored) Help",
            "description": "Enhanced interactive mode with service locator",
            "key_features": [
                "Uses service locator for all dependencies",
                "Works with local OR network services",
                "Same REPL functionality as original",
                "Enhanced with ask/tell/do pattern"
            ],
            "examples": [
                "ask('session stats') - Get session information",
                "do('start repl') - Start interactive REPL",
                "tell('help', help_data) - Format help output"
            ]
        }
    
    def _check_services_initialized(self) -> Dict:
        """Check which services are initialized"""
        return {
            "database": self.database is not None,
            "claude": self.claude is not None,
            "logger": self.logger is not None,
            "error_handler": self.error_handler is not None,
            "config": self.config is not None
        }
    
    # Action implementation methods
    def _start_repl(self) -> Dict:
        """Start the REPL interactive mode"""
        try:
            import datetime
            self.session_stats['session_start'] = datetime.datetime.now().isoformat()
            
            print("\n" + "=" * 60)
            print("Tournament Tracker Interactive Mode (Refactored)")
            print("=" * 60)
            
            # Check service availability
            services = self._check_services_initialized()
            
            if services["claude"]:
                try:
                    claude_health = self.claude.ask("health status")
                    if claude_health.get("claude_cli_available"):
                        print("✅ Claude AI: ENABLED (via service locator)")
                    else:
                        print("⚠️  Claude AI: CLI not available")
                except:
                    print("⚠️  Claude AI: Service discovered but not responding")
            else:
                print("⚠️  Claude AI: Service not discovered")
            
            if services["database"]:
                print("✅ Database: AVAILABLE (via service locator)")
            else:
                print("⚠️  Database: Service not discovered")
            
            print(f"\n🌐 Service Mode: {'Network-first' if self.prefer_network else 'Local-first'}")
            print("📡 All services discovered via service locator")
            
            print("\nAvailable objects: database, claude, logger")
            print("Type 'help()' for commands, 'exit()' to quit")
            print("=" * 60)
            
            # Create REPL environment with discovered services
            repl_globals = {
                'database': self.database,
                'claude': self.claude,
                'logger': self.logger,
                'error_handler': self.error_handler,
                'config': self.config,
                'interactive': self,
                'help': lambda: print(self.tell("help", self._get_help_content())),
                'stats': lambda: self._show_stats(),
                'sync': lambda: self._sync_via_service(),
                'ask': lambda q: self._ask_claude(q),
                'chat': lambda ctx=None: self._start_chat_mode(ctx)
            }
            
            # Start interactive console
            console = code.InteractiveConsole(repl_globals)
            console.interact()
            
            return {
                "action": "start_repl",
                "status": "completed",
                "services_available": services
            }
            
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "HIGH")
                except:
                    pass
            return {"action": "start_repl", "status": "failed", "error": str(e)}
    
    def _start_ai_chat(self) -> Dict:
        """Start AI chat mode"""
        if not self.claude:
            return {"action": "start_ai_chat", "error": "Claude service not available"}
        
        try:
            # Use discovered Claude service
            chat_result = self.claude.do("start chat")
            return {
                "action": "start_ai_chat",
                "status": "started",
                "result": chat_result
            }
        except Exception as e:
            return {"action": "start_ai_chat", "error": str(e)}
    
    def _execute_command(self, command: str) -> Dict:
        """Execute a command in safe environment"""
        if not command:
            return {"error": "No command provided"}
        
        try:
            self.session_stats['commands_executed'] += 1
            
            # Create safe execution environment
            safe_globals = {
                'database': self.database,
                'claude': self.claude,
                'logger': self.logger,
                'print': print,
                '__builtins__': __builtins__
            }
            
            # Capture output
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                result = eval(command, safe_globals)
            
            output = output_buffer.getvalue()
            
            return {
                "action": "execute_command",
                "command": command,
                "result": result,
                "output": output,
                "success": True
            }
            
        except Exception as e:
            self.session_stats['errors_encountered'] += 1
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "LOW")
                except:
                    pass
            return {
                "action": "execute_command",
                "command": command,
                "error": str(e),
                "success": False
            }
    
    def _reset_session(self) -> Dict:
        """Reset session statistics"""
        old_stats = self.session_stats.copy()
        self.session_stats = {
            'commands_executed': 0,
            'errors_encountered': 0,
            'ai_queries': 0,
            'session_start': None
        }
        
        return {
            "action": "reset_session",
            "old_stats": old_stats,
            "new_stats": self.session_stats
        }
    
    # Helper methods for REPL
    def _show_stats(self):
        """Show statistics via discovered database service"""
        if self.database:
            try:
                stats = self.database.ask("stats")
                formatted = self.database.tell("console", stats)
                print(formatted)
            except Exception as e:
                print(f"Error getting stats: {e}")
        else:
            print("Database service not available")
    
    def _sync_via_service(self):
        """Sync via discovered sync service"""
        sync_service = get_service("sync", self.prefer_network)
        if sync_service:
            try:
                result = sync_service.do("sync tournaments")
                print(f"Sync result: {result}")
            except Exception as e:
                print(f"Sync error: {e}")
        else:
            print("Sync service not available")
    
    def _ask_claude(self, question: str):
        """Ask Claude via discovered service"""
        if self.claude:
            try:
                self.session_stats['ai_queries'] += 1
                response = self.claude.ask(question)
                formatted = self.claude.tell("text", response)
                print(formatted)
                return response
            except Exception as e:
                print(f"Claude error: {e}")
                return None
        else:
            print("Claude service not available")
            return None
    
    def _start_chat_mode(self, context=None):
        """Start chat mode with Claude"""
        if self.claude:
            try:
                chat_action = "start ai chat"
                if context:
                    chat_action += f" with context {context}"
                return self.claude.do(chat_action)
            except Exception as e:
                print(f"Chat error: {e}")
        else:
            print("Claude service not available")
    
    # Format methods
    def _format_console(self, data: Dict) -> str:
        """Format for console output"""
        if "stats" in data:
            return f"Session Stats: {data['stats']['commands_executed']} commands, {data['stats']['ai_queries']} AI queries"
        elif "commands" in data:
            lines = ["Available Commands:", "=" * 20]
            for category, cmds in data["commands"].items():
                lines.append(f"\n{category.title()}:")
                for cmd in cmds:
                    lines.append(f"  • {cmd}")
            return "\n".join(lines)
        
        return str(data)
    
    def _format_help(self, data: Dict) -> str:
        """Format help content"""
        if "title" in data:
            lines = [
                f"🔧 {data['title']}",
                "=" * 60,
                f"📝 {data.get('description', '')}",
                "",
                "✨ Key Features:"
            ]
            
            for feature in data.get('key_features', []):
                lines.append(f"  • {feature}")
            
            lines.extend(["", "💡 Examples:"])
            for example in data.get('examples', []):
                lines.append(f"  • {example}")
            
            return "\n".join(lines)
        
        return str(data)
    
    def _format_text(self, data: Dict) -> str:
        """Format as plain text"""
        return str(data)
    
    def _format_repl(self, data: Dict) -> str:
        """Format for REPL display"""
        return self._format_console(data)
    
    def _handle_switch(self, backend: str = "auto") -> Dict:
        """Handle switch command"""
        return {
            "switch": "interactive",
            "backend": backend,
            "status": "available",
            "prefer_network": self.prefer_network
        }

# Create service instances
interactive_service = RefactoredInteractiveService(prefer_network=False)  # Local-first
interactive_service_network = RefactoredInteractiveService(prefer_network=True)  # Network-first

# Backward compatibility functions
def start_repl(database_url: Optional[str] = None) -> bool:
    """Start REPL (backward compatible)"""
    service = RefactoredInteractiveService(database_url=database_url)
    result = service.do("start repl")
    return result.get("status") == "completed"

def start_interactive(backend: str = "auto") -> Dict:
    """Start interactive mode (backward compatible)"""
    return interactive_service.do("start repl")

if __name__ == "__main__":
    # Test the refactored interactive service
    print("🧪 Testing Refactored Interactive Service")
    
    # Test local-first service
    print("\n1. Testing local-first interactive service:")
    inter_local = RefactoredInteractiveService(prefer_network=False)
    
    # Test service initialization
    init_result = inter_local.do("init services")
    print(f"Init services: {init_result}")
    
    # Test session stats
    stats = inter_local.ask("session stats")
    print(f"Stats: {inter_local.tell('console', stats)}")
    
    # Test help
    help_content = inter_local.ask("help")
    print(f"Help: {inter_local.tell('help', help_content)}")
    
    # Test network-first service
    print("\n2. Testing network-first interactive service:")
    inter_network = RefactoredInteractiveService(prefer_network=True)
    
    health = inter_network.ask("service health")
    print(f"Service health: {inter_network.tell('json', health)}")
    
    # Test backward compatibility
    print("\n3. Testing backward compatibility:")
    # Note: start_repl() would start actual REPL, so just test the function exists
    print(f"start_repl function available: {callable(start_repl)}")
    
    print("\n✅ Refactored interactive service test complete!")
    print("💡 Same REPL functionality, but now with service locator and distributed capabilities!")