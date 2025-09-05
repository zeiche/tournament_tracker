#!/usr/bin/env python3
"""
claude_cli_service.py - Claude CLI Service with Queue
SINGLE ENTRY POINT for all Claude interactions using authenticated CLI.
No API keys needed - uses 'claude' command from logged-in session.
Implements queuing to prevent overload.
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

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add path for local imports
sys.path.append('/home/ubuntu/claude/tournament_tracker')
from fuzzy_search import fuzzy_searcher, fuzzy_search_objects


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


class ClaudeCLIService:
    """
    Claude CLI Service - THE ONLY WAY to interact with Claude
    Uses authenticated 'claude' CLI command, no API keys needed.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern - only ONE service instance"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the service (only runs once)"""
        if self._initialized:
            return
            
        self.request_queue = Queue()
        self.response_cache = {}
        self.processing = False
        self.stats = {
            'requests_processed': 0,
            'requests_failed': 0,
            'total_processing_time': 0.0,
            'cache_hits': 0
        }
        
        # Check if claude CLI is available
        self.cli_available = self._check_cli()
        
        # Start the queue processor
        if self.cli_available:
            self._start_processor()
            logger.info("✅ Claude CLI Service initialized (SINGLE ENTRY POINT)")
        else:
            logger.error("❌ Claude CLI not available - please run 'claude /login'")
        
        self._initialized = True
    
    def _check_cli(self) -> bool:
        """Check if claude CLI is available and authenticated"""
        try:
            result = subprocess.run(
                ['which', 'claude'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _start_processor(self):
        """Start the background queue processor"""
        def process_queue():
            while True:
                try:
                    # Get request from queue (wait up to 1 second)
                    request = self.request_queue.get(timeout=1)
                    self._process_request(request)
                except Empty:
                    continue
                except Exception as e:
                    logger.error(f"Queue processor error: {e}")
        
        # Start processor thread
        thread = Thread(target=process_queue, daemon=True)
        thread.start()
        logger.info("Queue processor started")
    
    def _process_request(self, request: ClaudeRequest):
        """Process a single request"""
        start_time = time.time()
        
        try:
            # First try to handle with direct database queries
            direct_response = self._try_direct_query(request.message)
            if direct_response:
                response = direct_response
            else:
                # Use Claude CLI
                response = self._call_claude_cli(request.message, request.context)
            
            # Update stats
            self.stats['requests_processed'] += 1
            processing_time = time.time() - start_time
            self.stats['total_processing_time'] += processing_time
            
            response.request_id = request.id
            response.processing_time = processing_time
            
            # Cache response
            self.response_cache[request.id] = response
            
            # Call callback if provided
            if request.callback:
                request.callback(response)
                
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            self.stats['requests_failed'] += 1
            
            error_response = ClaudeResponse(
                success=False,
                error=str(e),
                request_id=request.id,
                processing_time=time.time() - start_time
            )
            
            self.response_cache[request.id] = error_response
            
            if request.callback:
                request.callback(error_response)
    
    def _try_direct_query(self, message: str) -> Optional[ClaudeResponse]:
        """
        Let Claude handle everything with the polymorphic paradigm
        """
        return None  # Always let Claude handle it with polymorphic methods
    
    def _call_claude_cli(self, message: str, context: Dict[str, Any]) -> ClaudeResponse:
        """Call Claude CLI with a message"""
        try:
            # Check if this is a database query or general question
            db_keywords = ['player', 'tournament', 'top', 'show', 'list', 'find', 'search', 'stats', 'points', 'recent', 'organization', 'venue']
            is_db_query = any(keyword in message.lower() for keyword in db_keywords)
            
            if is_db_query:
                # Prepare the prompt for database queries
                system_context = """You have access to a tournament database. Generate Python code that queries the database and sets an 'output' variable.

IMPORTANT DATABASE SCHEMA:
- Player: id, gamer_tag, display_name (no direct points/stats columns - calculated via joins)
- Tournament: id, name, start_date, end_date, num_attendees, lat, lng, venue, organization_id
- TournamentPlacement: player_id, tournament_id, event_name, placement, team_name
- Organization: id, name

Key relationships:
- Player stats are calculated from TournamentPlacement joins
- Tournament.organization_id links to Organization.id
- Use func.lower() for case-insensitive searches

BEST APPROACH - Use the polymorphic_queries module:
# For ANY query, just use:
from polymorphic_queries import query as pq
output = pq(message)  # It figures out what to do with proper formatting!

# The query function returns Discord-formatted output using formatters.PlayerFormatter
# For custom formatting, you can also use:
from formatters import PlayerFormatter, TournamentFormatter

Examples if you need custom queries:
# For "show top 8 players":
from sqlalchemy import func, case, desc
PLACEMENT_POINTS = {1: 100, 2: 75, 3: 50, 4: 35, 5: 25, 6: 25, 7: 15, 8: 15}
query = session.query(
    Player,
    func.sum(
        case(*[(TournamentPlacement.placement == p, PLACEMENT_POINTS[p]) for p in PLACEMENT_POINTS.keys()], else_=0)
    ).label('total_points'),
    func.count(TournamentPlacement.id).label('tournament_count')
).join(TournamentPlacement).group_by(Player.id).order_by(desc('total_points')).limit(8)
results = query.all()
output = "**Top 8 Players:**\\n"
for i, (p, points, events) in enumerate(results, 1):
    output += f"{i}. {p.gamer_tag} - {int(points or 0)} points ({events} events)\\n"

# For "show player west":  
from sqlalchemy import func, case, desc
player = session.query(Player).filter(func.lower(Player.gamer_tag).like('%west%')).first()
if player:
    PLACEMENT_POINTS = {1: 100, 2: 75, 3: 50, 4: 35, 5: 25, 6: 25, 7: 15, 8: 15}
    stats = session.query(
        func.sum(case(*[(TournamentPlacement.placement == p, PLACEMENT_POINTS[p]) for p in PLACEMENT_POINTS.keys()], else_=0)),
        func.count(TournamentPlacement.id)
    ).filter(TournamentPlacement.player_id == player.id).first()
    output = f"**{player.gamer_tag}**\\nPoints: {int(stats[0] or 0)}\\nEvents: {stats[1]}"
else:
    output = "Player not found"

# For "recent tournaments":
from datetime import datetime
tournaments = session.query(Tournament).order_by(Tournament.start_date.desc()).limit(10).all()
output = "**Recent Tournaments:**\\n"
for t in tournaments:
    if t.start_date:
        date_str = t.start_date.strftime('%Y-%m-%d')
        output += f"- {t.name} ({date_str})\\n"

Always set 'output' variable. Format for Discord with ** for bold."""
                
                prompt = f"{system_context}\n\nGenerate Python code for: {message}"
            else:
                # For general questions, just ask Claude directly
                prompt = message
            if context:
                prompt = f"{prompt}\n\nAdditional context: {json.dumps(context)}"
            
            # Call claude CLI
            result = subprocess.run(
                ['claude'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                response_text = result.stdout.strip()
                
                # Log what Claude returned for debugging
                logger.debug(f"Claude returned: {response_text[:500]}...")
                
                # Check if Claude returned Python code to execute
                if 'output =' in response_text or 'output=' in response_text:
                    try:
                        # Clean the code - remove markdown code blocks if present
                        code = response_text
                        if '```python' in code:
                            # Extract code from markdown blocks
                            start = code.find('```python') + 9
                            end = code.find('```', start)
                            if end > start:
                                code = code[start:end].strip()
                        elif '```' in code:
                            # Remove generic code blocks
                            start = code.find('```') + 3
                            end = code.find('```', start)
                            if end > start:
                                code = code[start:end].strip()
                        
                        # Execute the code
                        from database import session_scope
                        from tournament_models import Player, Tournament, Organization, TournamentPlacement
                        from sqlalchemy import func, case, desc
                        from datetime import datetime
                        from polymorphic_queries import query as pq, PolymorphicQuery
                        from formatters import PlayerFormatter, TournamentFormatter
                        
                        # If this is a simple query, just use polymorphic_queries
                        if 'pq(' in code or 'pq (' in code:
                            # Just execute the polymorphic query
                            with session_scope() as session:
                                exec_globals = {
                                    'pq': pq,
                                    'message': message,
                                    'output': None
                                }
                                exec(code, exec_globals)
                        else:
                            # Full execution environment for custom queries
                            with session_scope() as session:
                                exec_globals = {
                                    'session': session,
                                    'Player': Player,
                                    'Tournament': Tournament,
                                    'Organization': Organization,
                                    'TournamentPlacement': TournamentPlacement,
                                    'func': func,
                                    'case': case,
                                    'desc': desc,
                                    'datetime': datetime,
                                    'pq': pq,
                                    'PolymorphicQuery': PolymorphicQuery,
                                    'PlayerFormatter': PlayerFormatter,
                                    'TournamentFormatter': TournamentFormatter,
                                    'message': message,
                                    'output': None
                                }
                                exec(code, exec_globals)
                        
                        output = exec_globals.get('output', 'No output generated')
                        
                        return ClaudeResponse(
                            success=True,
                            response=str(output)
                        )
                    except Exception as e:
                        logger.error(f"Code execution error: {e}")
                        logger.error(f"Code that failed: {response_text[:500]}...")
                        return ClaudeResponse(
                            success=False,
                            error=f"Code execution error: {str(e)}"
                        )
                else:
                    # Return Claude's direct response
                    return ClaudeResponse(
                        success=True,
                        response=response_text
                    )
            else:
                return ClaudeResponse(
                    success=False,
                    error=f"Claude CLI error: {result.stderr}"
                )
                
        except subprocess.TimeoutExpired:
            return ClaudeResponse(
                success=False,
                error="Claude CLI timeout (30s)"
            )
        except Exception as e:
            return ClaudeResponse(
                success=False,
                error=f"Claude CLI error: {str(e)}"
            )
    
    # ========================================================================
    # PUBLIC INTERFACE - THE ONLY WAY TO USE CLAUDE
    # ========================================================================
    
    def ask(self, message: str, context: Optional[Dict[str, Any]] = None) -> ClaudeResponse:
        """
        Synchronous ask - THE PRIMARY ENTRY POINT
        
        Args:
            message: The message/question for Claude
            context: Optional context dictionary
            
        Returns:
            ClaudeResponse with the result
        """
        if not self.cli_available:
            return ClaudeResponse(
                success=False,
                error="Claude CLI not available - please run 'claude /login'"
            )
        
        # Create request
        request_id = f"{datetime.now().timestamp()}"
        request = ClaudeRequest(
            id=request_id,
            message=message,
            context=context or {}
        )
        
        # Add to queue
        self.request_queue.put(request)
        
        # Wait for response (with timeout)
        timeout = 35  # 30s for Claude + 5s buffer
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if request_id in self.response_cache:
                response = self.response_cache.pop(request_id)
                return response
            time.sleep(0.1)
        
        return ClaudeResponse(
            success=False,
            error="Request timeout",
            request_id=request_id
        )
    
    async def ask_async(self, message: str, context: Optional[Dict[str, Any]] = None) -> ClaudeResponse:
        """Async version of ask"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.ask, message, context)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'cli_available': self.cli_available,
            'queue_size': self.request_queue.qsize(),
            'requests_processed': self.stats['requests_processed'],
            'requests_failed': self.stats['requests_failed'],
            'avg_processing_time': (
                self.stats['total_processing_time'] / self.stats['requests_processed']
                if self.stats['requests_processed'] > 0 else 0
            ),
            'cache_hits': self.stats['cache_hits']
        }


# ============================================================================
# SINGLETON INSTANCE - USE THIS
# ============================================================================

claude_cli = ClaudeCLIService()


# ============================================================================
# SIMPLE INTERFACE FUNCTIONS
# ============================================================================

def ask_claude(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Simple function to ask Claude a question"""
    response = claude_cli.ask(message, context)
    if response.success:
        return response.response
    else:
        return f"Error: {response.error}"


async def ask_claude_async(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """Async version of ask_claude"""
    response = await claude_cli.ask_async(message, context)
    if response.success:
        return response.response
    else:
        return f"Error: {response.error}"


# ============================================================================
# DISCORD INTEGRATION
# ============================================================================

async def process_message_async(message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Process message for Discord (returns dict for compatibility)"""
    response = await claude_cli.ask_async(message, context)
    return {
        'success': response.success,
        'response': response.response,
        'error': response.error,
        'processing_time': response.processing_time
    }


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("Testing Claude CLI Service...")
    
    # Test direct query
    print("\n1. Testing direct query (no Claude needed):")
    response = ask_claude("show statistics")
    print(response)
    
    # Test Claude query
    print("\n2. Testing Claude query:")
    response = ask_claude("What is 2+2?")
    print(response)
    
    # Show stats
    print("\n3. Service stats:")
    print(json.dumps(claude_cli.get_stats(), indent=2))