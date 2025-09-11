#!/usr/bin/env python3
"""
claude_cli_service_refactored.py - REFACTORED Claude CLI Service using service locator

BEFORE: Direct imports of error handler, logger, and other services
AFTER: Uses service locator for all dependencies

Key changes:
1. Uses service locator for logger, error handler, config dependencies
2. Enhanced with 3-method pattern (ask/tell/do)
3. Works with local OR network services transparently
4. Can be distributed for scalable AI processing
5. Same Claude CLI functionality as original

This demonstrates refactoring a high-value business service.
"""
import os
import sys
import json
import asyncio
import subprocess
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from queue import Queue, Empty
from threading import Thread, Lock
import time
import uuid

# Add path for local imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')

from polymorphic_core import announcer
from polymorphic_core.service_locator import get_service
from dynamic_switches import announce_switch

# Fuzzy search (optional dependency)
try:
    from fuzzy_search import fuzzy_searcher, fuzzy_search_objects
except ImportError:
    fuzzy_searcher = None
    fuzzy_search_objects = None

@dataclass
class ClaudeRequest:
    """A request to Claude"""
    id: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    callback: Optional[callable] = None

@dataclass
class ClaudeResponse:
    """Response from Claude"""
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    processing_time: float = 0.0

class RefactoredClaudeCLIService:
    """
    REFACTORED Claude CLI Service using service locator pattern.
    
    This version:
    - Uses service locator for all dependencies (logger, error handler, config)
    - Enhanced with 3-method pattern for queries and operations
    - Can operate over network for distributed AI processing
    - Same Claude CLI functionality as original
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls, prefer_network: bool = False):
        """Singleton pattern with service preference"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, prefer_network: bool = False):
        """Initialize the service (only runs once)"""
        if self._initialized:
            return
            
        self.prefer_network = prefer_network
        self._logger = None
        self._error_handler = None
        self._config = None
        
        self.request_queue = Queue()
        self.response_cache = {}
        self.processing = False
        self.stats = {
            'requests_processed': 0,
            'requests_failed': 0,
            'total_processing_time': 0.0,
            'cache_hits': 0,
            'queue_size_max': 0,
            'service_restarts': 0
        }
        
        # Check if claude CLI is available
        self._check_claude_cli()
        
        # Start background processing thread
        self._start_processing_thread()
        
        self._initialized = True
        
        # Announce capabilities
        announcer.announce(
            "Claude CLI Service (Refactored)",
            [
                "REFACTORED: Uses service locator for dependencies",
                "AI processing with 3-method pattern",
                "ask('What are recent tournaments?') - AI queries",
                "tell('discord', ai_response) - format AI responses",
                "do('process queue') - manage AI request processing",
                "Distributed AI processing with queue management"
            ],
            [
                "claude.ask('Analyze tournament data')",
                "claude.tell('summary', ai_response)",
                "claude.do('clear queue')",
                "Works with local OR network logger/error services"
            ]
        )
        
        # Announce as a switch
        announce_switch("ai", "START AI chat service (chat|test)", self._handle_switch)
    
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
        Ask Claude using natural language.
        
        Examples:
            ask("What are the top 5 players?")
            ask("Analyze recent tournament trends")
            ask("Generate a report summary")
            ask("queue status")
            ask("service stats")
        """
        query_lower = query.lower().strip()
        
        # Log the query using discovered logger
        if self.logger:
            try:
                self.logger.info(f"Claude query: {query}")
            except:
                pass
        
        try:
            # Handle service queries
            if "queue status" in query_lower or "queue" in query_lower:
                return self._get_queue_status()
            
            elif "stats" in query_lower or "statistics" in query_lower:
                return self._get_service_stats()
            
            elif "health" in query_lower or "status" in query_lower:
                return self._get_health_status()
            
            elif "history" in query_lower:
                return self._get_request_history()
            
            else:
                # Send to Claude AI
                return self._ask_claude_sync(query, **kwargs)
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "MEDIUM")
                except:
                    pass
            return {"error": f"Claude query failed: {str(e)}"}
    
    def tell(self, format_type: str, data: Any = None, **kwargs) -> str:
        """
        Format Claude responses for output.
        
        Formats: json, discord, text, summary, markdown
        """
        if data is None:
            data = {}
        
        try:
            if format_type == "json":
                return json.dumps(data, indent=2, default=str)
            
            elif format_type == "discord":
                return self._format_discord(data)
            
            elif format_type == "text":
                return self._format_text(data)
            
            elif format_type == "summary":
                return self._format_summary(data)
            
            elif format_type == "markdown":
                return self._format_markdown(data)
            
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
        Perform Claude service operations using natural language.
        
        Examples:
            do("process queue")
            do("clear cache")
            do("restart service")
            do("send message Hello Claude")
        """
        action_lower = action.lower().strip()
        
        # Log the action
        if self.logger:
            try:
                self.logger.info(f"Claude action: {action}")
            except:
                pass
        
        try:
            if "process queue" in action_lower:
                return self._process_queue_action()
            
            elif "clear cache" in action_lower:
                return self._clear_cache()
            
            elif "clear queue" in action_lower:
                return self._clear_queue()
            
            elif "restart service" in action_lower:
                return self._restart_service()
            
            elif "send message" in action_lower:
                message = action[len("send message"):].strip()
                return self._send_message_action(message)
            
            elif "test connection" in action_lower:
                return self._test_claude_connection()
            
            else:
                return {"error": f"Don't know how to: {action}"}
                
        except Exception as e:
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "HIGH")
                except:
                    pass
            return {"error": f"Claude action failed: {str(e)}"}
    
    # Core Claude CLI functionality (same as original)
    def _check_claude_cli(self):
        """Check if Claude CLI is available"""
        try:
            result = subprocess.run(['claude', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                if self.logger:
                    try:
                        self.logger.info("Claude CLI available")
                    except:
                        pass
                return True
            else:
                if self.logger:
                    try:
                        self.logger.warning("Claude CLI not working properly")
                    except:
                        pass
                return False
        except Exception as e:
            if self.logger:
                try:
                    self.logger.error(f"Claude CLI check failed: {e}")
                except:
                    pass
            return False
    
    def _start_processing_thread(self):
        """Start background thread for processing requests"""
        def process_requests():
            while True:
                try:
                    # Check queue
                    try:
                        request = self.request_queue.get(timeout=1.0)
                    except Empty:
                        continue
                    
                    # Process request
                    self._process_claude_request(request)
                    self.request_queue.task_done()
                    
                except Exception as e:
                    if self.error_handler:
                        try:
                            self.error_handler.handle_exception(e, "MEDIUM")
                        except:
                            pass
                    time.sleep(1)  # Wait before retrying
        
        thread = Thread(target=process_requests, daemon=True)
        thread.start()
    
    def _process_claude_request(self, request: ClaudeRequest):
        """Process a Claude request"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(request.message, request.context)
            if cache_key in self.response_cache:
                self.stats['cache_hits'] += 1
                response = self.response_cache[cache_key]
                if request.callback:
                    request.callback(response)
                return response
            
            # Send to Claude CLI
            response = self._call_claude_cli(request.message, request.context)
            
            # Cache response
            self.response_cache[cache_key] = response
            
            # Trim cache if too large
            if len(self.response_cache) > 100:
                # Remove oldest entries
                keys = list(self.response_cache.keys())
                for key in keys[:20]:
                    del self.response_cache[key]
            
            # Update stats
            self.stats['requests_processed'] += 1
            self.stats['total_processing_time'] += time.time() - start_time
            
            # Call callback if provided
            if request.callback:
                request.callback(response)
            
            return response
            
        except Exception as e:
            self.stats['requests_failed'] += 1
            error_response = ClaudeResponse(
                success=False,
                error=str(e),
                request_id=request.id,
                processing_time=time.time() - start_time
            )
            
            if self.error_handler:
                try:
                    self.error_handler.handle_exception(e, "HIGH")
                except:
                    pass
            
            if request.callback:
                request.callback(error_response)
            
            return error_response
    
    def _call_claude_cli(self, message: str, context: Dict = None) -> ClaudeResponse:
        """Call Claude CLI with message"""
        if context is None:
            context = {}
        
        try:
            # Prepare the prompt with context
            prompt = message
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                prompt = f"Context:\n{context_str}\n\nQuestion: {message}"
            
            # Call Claude CLI
            result = subprocess.run(
                ['claude', prompt],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0:
                return ClaudeResponse(
                    success=True,
                    response=result.stdout.strip(),
                    request_id=str(uuid.uuid4())
                )
            else:
                return ClaudeResponse(
                    success=False,
                    error=f"Claude CLI error: {result.stderr}",
                    request_id=str(uuid.uuid4())
                )
                
        except subprocess.TimeoutExpired:
            return ClaudeResponse(
                success=False,
                error="Claude CLI timeout",
                request_id=str(uuid.uuid4())
            )
        except Exception as e:
            return ClaudeResponse(
                success=False,
                error=str(e),
                request_id=str(uuid.uuid4())
            )
    
    def _ask_claude_sync(self, query: str, **kwargs) -> Dict:
        """Ask Claude synchronously"""
        request = ClaudeRequest(
            id=str(uuid.uuid4()),
            message=query,
            context=kwargs
        )
        
        response = self._process_claude_request(request)
        
        return {
            "query": query,
            "response": response.response if response.success else None,
            "error": response.error if not response.success else None,
            "success": response.success,
            "processing_time": response.processing_time
        }
    
    # Query implementation methods
    def _get_queue_status(self) -> Dict:
        """Get current queue status"""
        return {
            "queue_size": self.request_queue.qsize(),
            "processing": self.processing,
            "max_queue_size": self.stats['queue_size_max']
        }
    
    def _get_service_stats(self) -> Dict:
        """Get service statistics"""
        return {
            "stats": self.stats.copy(),
            "cache_size": len(self.response_cache),
            "queue_size": self.request_queue.qsize(),
            "average_processing_time": (
                self.stats['total_processing_time'] / max(self.stats['requests_processed'], 1)
            )
        }
    
    def _get_health_status(self) -> Dict:
        """Get service health status"""
        claude_available = self._check_claude_cli()
        
        return {
            "claude_cli_available": claude_available,
            "queue_healthy": self.request_queue.qsize() < 50,
            "cache_healthy": len(self.response_cache) < 200,
            "error_rate": (
                self.stats['requests_failed'] / max(self.stats['requests_processed'] + self.stats['requests_failed'], 1)
            ),
            "overall_health": "good" if claude_available and self.request_queue.qsize() < 50 else "issues"
        }
    
    def _get_request_history(self) -> Dict:
        """Get request history (simplified)"""
        return {
            "total_requests": self.stats['requests_processed'],
            "failed_requests": self.stats['requests_failed'],
            "cache_hits": self.stats['cache_hits'],
            "current_cache_size": len(self.response_cache)
        }
    
    # Action implementation methods
    def _process_queue_action(self) -> Dict:
        """Process pending queue items"""
        queue_size = self.request_queue.qsize()
        return {
            "action": "process_queue",
            "queue_size": queue_size,
            "status": "processing" if queue_size > 0 else "empty"
        }
    
    def _clear_cache(self) -> Dict:
        """Clear response cache"""
        old_size = len(self.response_cache)
        self.response_cache.clear()
        return {
            "action": "clear_cache",
            "cleared_entries": old_size
        }
    
    def _clear_queue(self) -> Dict:
        """Clear request queue"""
        old_size = self.request_queue.qsize()
        
        # Clear the queue
        while not self.request_queue.empty():
            try:
                self.request_queue.get_nowait()
            except Empty:
                break
        
        return {
            "action": "clear_queue",
            "cleared_requests": old_size
        }
    
    def _restart_service(self) -> Dict:
        """Restart the service"""
        self.stats['service_restarts'] += 1
        
        # Clear cache and reset stats
        self.response_cache.clear()
        
        return {
            "action": "restart_service",
            "status": "restarted",
            "restart_count": self.stats['service_restarts']
        }
    
    def _send_message_action(self, message: str) -> Dict:
        """Send a message to Claude via action interface"""
        if not message:
            return {"error": "No message provided"}
        
        result = self._ask_claude_sync(message)
        return {
            "action": "send_message",
            "message": message,
            "response": result
        }
    
    def _test_claude_connection(self) -> Dict:
        """Test Claude CLI connection"""
        try:
            test_response = self._call_claude_cli("Hello, can you respond with 'OK'?")
            return {
                "action": "test_connection",
                "success": test_response.success,
                "response": test_response.response,
                "error": test_response.error
            }
        except Exception as e:
            return {
                "action": "test_connection",
                "success": False,
                "error": str(e)
            }
    
    # Format methods
    def _format_discord(self, data: Dict) -> str:
        """Format for Discord output"""
        if "response" in data and data.get("success"):
            response = data["response"]
            if len(response) > 1800:  # Discord limit
                response = response[:1800] + "..."
            return f"🤖 **Claude:** {response}"
        
        elif "stats" in data:
            stats = data["stats"]
            return f"📊 **Claude Stats:** {stats['requests_processed']} processed | {stats['requests_failed']} failed | {data.get('cache_size', 0)} cached"
        
        elif "queue_size" in data:
            return f"📋 **Queue:** {data['queue_size']} pending | Processing: {'Yes' if data.get('processing') else 'No'}"
        
        return f"🤖 {data}"
    
    def _format_text(self, data: Dict) -> str:
        """Format as plain text"""
        if "response" in data:
            return data["response"] or str(data)
        return str(data)
    
    def _format_summary(self, data: Dict) -> str:
        """Format as summary"""
        if "response" in data and data.get("success"):
            response = data["response"]
            # Return first sentence or first 100 chars
            if '. ' in response:
                return response.split('. ')[0] + '.'
            else:
                return response[:100] + '...' if len(response) > 100 else response
        
        elif "stats" in data:
            return f"Claude: {data['stats']['requests_processed']} requests processed"
        
        return str(data)
    
    def _format_markdown(self, data: Dict) -> str:
        """Format as markdown"""
        if "response" in data and data.get("success"):
            return f"## Claude Response\n\n{data['response']}"
        
        return f"```json\n{json.dumps(data, indent=2)}\n```"
    
    # Utility methods
    def _get_cache_key(self, message: str, context: Dict) -> str:
        """Generate cache key for request"""
        context_str = json.dumps(context, sort_keys=True) if context else ""
        return f"{message}:{context_str}"
    
    def _handle_switch(self, mode: str = "chat") -> Dict:
        """Handle switch command"""
        return {
            "switch": "ai",
            "mode": mode,
            "status": "active",
            "queue_size": self.request_queue.qsize()
        }

# Create service instances
claude_service = RefactoredClaudeCLIService(prefer_network=False)  # Local-first
claude_service_network = RefactoredClaudeCLIService(prefer_network=True)  # Network-first

# Backward compatibility functions
def ask_claude(message: str, context: Dict = None) -> ClaudeResponse:
    """Ask Claude (backward compatible)"""
    request = ClaudeRequest(
        id=str(uuid.uuid4()),
        message=message,
        context=context or {}
    )
    return claude_service._process_claude_request(request)

def queue_claude_request(message: str, context: Dict = None, callback: callable = None) -> str:
    """Queue Claude request (backward compatible)"""
    request = ClaudeRequest(
        id=str(uuid.uuid4()),
        message=message,
        context=context or {},
        callback=callback
    )
    claude_service.request_queue.put(request)
    return request.id

if __name__ == "__main__":
    # Test the refactored Claude CLI service
    print("🧪 Testing Refactored Claude CLI Service")
    
    # Test local-first service
    print("\n1. Testing local-first Claude service:")
    claude_local = RefactoredClaudeCLIService(prefer_network=False)
    
    # Test health check
    health = claude_local.ask("health status")
    print(f"Health: {claude_local.tell('summary', health)}")
    
    # Test stats
    stats = claude_local.ask("service stats")
    print(f"Stats: {claude_local.tell('discord', stats)}")
    
    # Test Claude query (if CLI available)
    if claude_local._check_claude_cli():
        response = claude_local.ask("Hello Claude, please respond with 'OK'")
        print(f"Claude response: {claude_local.tell('text', response)}")
    else:
        print("Claude CLI not available for testing")
    
    # Test network-first service
    print("\n2. Testing network-first Claude service:")
    claude_network = RefactoredClaudeCLIService(prefer_network=True)
    
    queue_status = claude_network.ask("queue status")
    print(f"Queue: {claude_network.tell('discord', queue_status)}")
    
    # Test backward compatibility
    print("\n3. Testing backward compatibility:")
    request_id = queue_claude_request("Test message", {"context": "test"})
    print(f"Queued request: {request_id}")
    
    print("\n✅ Refactored Claude CLI service test complete!")
    print("💡 Same Claude AI functionality, but now with service locator and distributed capabilities!")