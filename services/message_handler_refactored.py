#!/usr/bin/env python3
"""
message_handler_refactored.py - REFACTORED Pure Message Handler using service locator

BEFORE: Direct imports of query handlers and basic logging
AFTER: Uses service locator for all dependencies

Key changes:
1. Uses service locator for database, claude, logger, query dependencies
2. Enhanced with 3-method pattern (ask/tell/do)
3. Works with local OR network services transparently
4. Can be distributed for scalable message processing
5. Same message handling functionality as original

This completes the Phase 2 business services refactoring.
"""
import sys
import time
from typing import Dict, Any, Optional

# Add path for imports
if '/home/ubuntu/claude/tournament_tracker' not in sys.path:
    sys.path.append('/home/ubuntu/claude/tournament_tracker')

from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service

class RefactoredMessageHandler:
    """
    REFACTORED Pure message handler using service locator pattern.
    
    This version:
    - Uses service locator for all dependencies (database, claude, logger, etc.)
    - Enhanced with 3-method pattern for queries and operations
    - Can operate over network for distributed message processing
    - Same message handling functionality as original
    """
    
    def __init__(self, prefer_network: bool = False):
        """Initialize handler with service locator"""
        self.prefer_network = prefer_network
        self._database = None
        self._claude = None
        self._logger = None
        self._error_handler = None
        self._config = None
        
        self.query_handler = None
        self.message_stats = {
            'messages_processed': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'service_start': time.time()
        }
        
        # Load services
        self._load_services()
        
        # Announce capabilities
        announcer.announce(
            "Message Handler (Refactored)",
            [
                "REFACTORED: Uses service locator for dependencies",
                "Message processing with 3-method pattern",
                "ask('message stats') - query message processing statistics",
                "tell('discord', response) - format message responses",
                "do('process message Hello') - handle message processing",
                "Distributed message handling with service discovery"
            ],
            [
                "handler.ask('processing stats')",
                "handler.tell('format', message_data)",
                "handler.do('process message show top players')",
                "Works with local OR network database/claude services"
            ]
        )
    
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
        Query message handler using natural language.
        
        Examples:
            ask("message stats")
            ask("processing statistics")
            ask("service health")
            ask("recent messages")
        """
        query_lower = query.lower().strip()
        
        # Log the query
        if self.logger:
            try:
                self.logger.info(f"Message handler query: {query}")
            except:
                pass
        
        try:
            if "message stats" in query_lower or "stats" in query_lower:
                return self._get_message_stats()
            
            elif "processing statistics" in query_lower:
                return self._get_processing_statistics()
            
            elif "service health" in query_lower or "health" in query_lower:
                return self._get_service_health()
            
            elif "recent messages" in query_lower:
                return self._get_recent_messages()
            
            elif "capabilities" in query_lower:
                return self._get_handler_capabilities()
            
            else:
                return {"error": f"Don't know how to handle query: {query}"}
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "MEDIUM")
                except:
                    pass
            return {"error": f"Message handler query failed: {str(e)}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """
        Format message handler data for output.
        
        Formats: discord, text, json, response, stats
        """
        if data is None:
            data = {}
        
        try:
            if format_type == "discord":
                return self._format_discord(data)
            
            elif format_type == "text":
                return self._format_text(data)
            
            elif format_type == "json":
                import json
                return json.dumps(data, indent=2, default=str)
            
            elif format_type == "response":
                return self._format_response(data)
            
            elif format_type == "stats":
                return self._format_stats(data)
            
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
        Perform message handler operations using natural language.
        
        Examples:
            do("process message show top players")
            do("reset stats")
            do("reload services")
            do("test message processing")
        """
        action_lower = action.lower().strip()
        
        # Log the action
        if self.logger:
            try:
                self.logger.info(f"Message handler action: {action}")
            except:
                pass
        
        try:
            if "process message" in action_lower:
                message = action[len("process message"):].strip()
                return self._process_message_action(message, kwargs)
            
            elif "reset stats" in action_lower:
                return self._reset_stats()
            
            elif "reload services" in action_lower:
                return self._reload_services()
            
            elif "test message processing" in action_lower:
                return self._test_message_processing()
            
            else:
                return {"error": f"Don't know how to: {action}"}
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "HIGH")
                except:
                    pass
            return {"error": f"Message handler action failed: {str(e)}"}
    
    # Core message processing (enhanced version of original)
    def process_message(self, content: str, context: dict = None) -> str:
        """
        Process a message and return response (backward compatible).
        
        Args:
            content: The message content
            context: Optional context (user, channel, etc.)
        
        Returns:
            Response string
        """
        if not content or not content.strip():
            return "Please provide a message."
        
        content = content.strip()
        self.message_stats['messages_processed'] += 1
        
        # Log message processing
        if self.logger:
            try:
                self.logger.info(f"Processing message: {content[:50]}...")
            except:
                pass
        
        try:
            # Simple built-in commands
            if content.lower() == "ping":
                return "pong!"
            elif content.lower() == "help":
                return self._get_help_text()
            elif content.lower() == "status":
                return self._get_status()
            
            # Try database queries first
            if self.database:
                try:
                    result = self.database.ask(content)
                    if result and not result.get('error'):
                        self.message_stats['successful_queries'] += 1
                        formatted = self.database.tell("discord", result)
                        return formatted
                except Exception as e:
                    if self.logger:
                        try:
                            self.logger.warning(f"Database query failed: {e}")
                        except:
                            pass
            
            # Try Claude AI if database didn't handle it
            if self.claude:
                try:
                    # Add context for Claude
                    claude_query = content
                    if context:
                        context_str = ", ".join([f"{k}: {v}" for k, v in context.items()])
                        claude_query = f"Context: {context_str}. Query: {content}"
                    
                    result = self.claude.ask(claude_query)
                    if result and result.get('success'):
                        self.message_stats['successful_queries'] += 1
                        return result.get('response', 'Claude responded but no content')
                except Exception as e:
                    if self.logger:
                        try:
                            self.logger.warning(f"Claude query failed: {e}")
                        except:
                            pass
            
            # Fallback
            self.message_stats['failed_queries'] += 1
            return f"I couldn't find information about: {content}. Try 'help' for available commands."
            
        except Exception as e:
            self.message_stats['failed_queries'] += 1
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "MEDIUM")
                except:
                    pass
            return f"Error processing message: {str(e)[:100]}"
    
    # Service loading
    def _load_services(self) -> Dict:
        """Load services via service locator"""
        try:
            if self.logger:
                try:
                    self.logger.info("Loading message handler services via service locator")
                except:
                    pass
            
            # Test services
            services_loaded = {
                'database': self.database is not None,
                'claude': self.claude is not None,
                'logger': self.logger is not None,
                'error_handler': self.error_handler is not None
            }
            
            return {
                "action": "load_services",
                "services": services_loaded,
                "total_loaded": sum(services_loaded.values())
            }
            
        except Exception as e:
            return {"action": "load_services", "error": str(e)}
    
    # Query implementation methods
    def _get_message_stats(self) -> Dict:
        """Get message processing statistics"""
        uptime = time.time() - self.message_stats['service_start']
        return {
            "stats": self.message_stats.copy(),
            "uptime_seconds": uptime,
            "messages_per_minute": (self.message_stats['messages_processed'] / max(uptime / 60, 1)),
            "success_rate": (
                self.message_stats['successful_queries'] / 
                max(self.message_stats['messages_processed'], 1)
            )
        }
    
    def _get_processing_statistics(self) -> Dict:
        """Get detailed processing statistics"""
        stats = self._get_message_stats()
        stats.update({
            "service_mode": "network-first" if self.prefer_network else "local-first",
            "services_available": {
                "database": self.database is not None,
                "claude": self.claude is not None,
                "logger": self.logger is not None
            }
        })
        return stats
    
    def _get_service_health(self) -> Dict:
        """Get health of discovered services"""
        health = {}
        
        # Test database
        if self.database:
            try:
                db_stats = self.database.ask("stats")
                health["database"] = "healthy" if db_stats else "issues"
            except:
                health["database"] = "unavailable"
        else:
            health["database"] = "not_discovered"
        
        # Test claude
        if self.claude:
            try:
                claude_health = self.claude.ask("health status")
                health["claude"] = claude_health.get("overall_health", "unknown")
            except:
                health["claude"] = "unavailable"
        else:
            health["claude"] = "not_discovered"
        
        return {"service_health": health}
    
    def _get_recent_messages(self) -> Dict:
        """Get recent message processing info (simplified)"""
        return {
            "recent_stats": self.message_stats,
            "note": "Full message history would require additional storage"
        }
    
    def _get_handler_capabilities(self) -> Dict:
        """Get message handler capabilities"""
        return {
            "built_in_commands": ["ping", "help", "status"],
            "service_integration": {
                "database": "Natural language queries to tournament data",
                "claude": "AI-powered responses and analysis"
            },
            "enhanced_features": [
                "Service discovery via service locator",
                "Distributed message processing",
                "Automatic fallback between services"
            ]
        }
    
    # Action implementation methods
    def _process_message_action(self, message: str, context: Dict) -> Dict:
        """Process a message via action interface"""
        if not message:
            return {"error": "No message provided"}
        
        response = self.process_message(message, context)
        return {
            "action": "process_message",
            "message": message,
            "response": response,
            "context": context,
            "success": True
        }
    
    def _reset_stats(self) -> Dict:
        """Reset message processing statistics"""
        old_stats = self.message_stats.copy()
        self.message_stats = {
            'messages_processed': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'service_start': time.time()
        }
        
        return {
            "action": "reset_stats",
            "old_stats": old_stats,
            "new_stats": self.message_stats
        }
    
    def _reload_services(self) -> Dict:
        """Reload services via service locator"""
        # Clear cached services to force reload
        self._database = None
        self._claude = None
        self._logger = None
        self._error_handler = None
        self._config = None
        
        # Reload
        return self._load_services()
    
    def _test_message_processing(self) -> Dict:
        """Test message processing with sample messages"""
        test_messages = [
            "ping",
            "help", 
            "status",
            "show top 5 players",
            "recent tournaments"
        ]
        
        results = {}
        for msg in test_messages:
            try:
                response = self.process_message(msg)
                results[msg] = {"success": True, "response": response[:100]}
            except Exception as e:
                results[msg] = {"success": False, "error": str(e)}
        
        return {
            "action": "test_message_processing",
            "test_results": results,
            "tests_run": len(test_messages)
        }
    
    # Format methods
    def _format_discord(self, data: Dict) -> str:
        """Format for Discord output"""
        if "stats" in data:
            stats = data["stats"]
            return f"📊 **Message Stats:** {stats['messages_processed']} processed | {stats['successful_queries']} successful | Rate: {data.get('success_rate', 0):.2%}"
        
        elif "service_health" in data:
            health = data["service_health"]
            emojis = {"healthy": "✅", "unavailable": "❌", "not_discovered": "❓", "issues": "⚠️"}
            lines = ["🏥 **Service Health:**"]
            for service, status in health.items():
                emoji = emojis.get(status, "❓")
                lines.append(f"{emoji} {service}: {status}")
            return "\n".join(lines)
        
        return f"📝 {data}"
    
    def _format_text(self, data: Dict) -> str:
        """Format as plain text"""
        if isinstance(data, dict) and "stats" in data:
            stats = data["stats"]
            return f"Messages: {stats['messages_processed']}, Success: {stats['successful_queries']}, Failed: {stats['failed_queries']}"
        
        return str(data)
    
    def _format_response(self, data: Any) -> str:
        """Format as message response"""
        if isinstance(data, dict):
            if "response" in data:
                return data["response"]
            elif "error" in data:
                return f"Error: {data['error']}"
        
        return str(data)
    
    def _format_stats(self, data: Dict) -> str:
        """Format statistics"""
        if "stats" in data:
            stats = data["stats"]
            uptime = data.get("uptime_seconds", 0)
            return f"""Message Handler Statistics:
- Messages Processed: {stats['messages_processed']}
- Successful Queries: {stats['successful_queries']}
- Failed Queries: {stats['failed_queries']}
- Uptime: {uptime:.1f} seconds
- Success Rate: {data.get('success_rate', 0):.2%}
- Messages/min: {data.get('messages_per_minute', 0):.1f}"""
        
        return str(data)
    
    # Helper methods (enhanced versions of original)
    def _get_help_text(self) -> str:
        """Get help text (enhanced)"""
        help_text = f"""🤖 **Message Handler (Refactored)** - Enhanced with Service Locator

**Built-in Commands:**
• `ping` - Check if handler is responsive
• `help` - Show this help message  
• `status` - Show handler status

**Natural Language Queries:**
• `show player [name]` - Player information via discovered database
• `show top [N] players` - Top N players via discovered database
• `recent tournaments` - Recent tournaments via discovered database
• `[any question]` - AI response via discovered Claude service

**Service Mode:** {'Network-first' if self.prefer_network else 'Local-first'}
**Services Available:** Database: {'✅' if self.database else '❌'}, Claude: {'✅' if self.claude else '❌'}

**Examples:**
• `show player west`
• `show top 10 players` 
• `recent tournaments`
• `What are the strongest regions for fighting games?`

The handler automatically discovers and uses available services!
        """
        return help_text
    
    def _get_status(self) -> str:
        """Get status information (enhanced)"""
        stats = self._get_message_stats()
        services = {
            "database": "✅" if self.database else "❌",
            "claude": "✅" if self.claude else "❌", 
            "logger": "✅" if self.logger else "❌"
        }
        
        status = f"""🔧 **Message Handler Status (Refactored)**

**Core Stats:**
• Messages Processed: {stats['stats']['messages_processed']}
• Success Rate: {stats['success_rate']:.2%}
• Uptime: {stats['uptime_seconds']:.1f}s

**Discovered Services:**
• Database: {services['database']}
• Claude AI: {services['claude']}
• Logger: {services['logger']}

**Mode:** {'Network-first' if self.prefer_network else 'Local-first'} service discovery
**Status:** ✅ Active and processing messages
        """
        return status

# Create service instances
message_handler = RefactoredMessageHandler(prefer_network=False)  # Local-first
message_handler_network = RefactoredMessageHandler(prefer_network=True)  # Network-first

# Backward compatibility
def process_message(content: str, context: dict = None) -> str:
    """Process message (backward compatible)"""
    return message_handler.process_message(content, context)

if __name__ == "__main__":
    # Test the refactored message handler
    print("🧪 Testing Refactored Message Handler")
    
    # Test local-first service
    print("\n1. Testing local-first message handler:")
    handler_local = RefactoredMessageHandler(prefer_network=False)
    
    # Test built-in commands
    ping_response = handler_local.process_message("ping")
    print(f"Ping: {ping_response}")
    
    help_response = handler_local.process_message("help")
    print(f"Help: {help_response[:200]}...")
    
    # Test stats
    stats = handler_local.ask("message stats")
    print(f"Stats: {handler_local.tell('stats', stats)}")
    
    # Test service health
    health = handler_local.ask("service health")
    print(f"Health: {handler_local.tell('discord', health)}")
    
    # Test network-first service
    print("\n2. Testing network-first message handler:")
    handler_network = RefactoredMessageHandler(prefer_network=True)
    
    status_response = handler_network.process_message("status")
    print(f"Status: {status_response[:200]}...")
    
    # Test processing action
    process_result = handler_network.do("process message show top 5 players")
    print(f"Process action: {process_result}")
    
    # Test backward compatibility
    print("\n3. Testing backward compatibility:")
    compat_response = process_message("ping")
    print(f"Backward compatible: {compat_response}")
    
    print("\n✅ Refactored message handler test complete!")
    print("💡 Same message processing, but now with service locator and distributed capabilities!")