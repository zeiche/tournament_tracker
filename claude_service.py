#!/usr/bin/env python3
"""
claude_service.py - SINGLE SOURCE OF TRUTH for Claude/AI conversations
This is the ONLY place where Claude API interactions should happen.
All other modules MUST go through this service.
"""
import os
import sys
import subprocess
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass
import asyncio
import anthropic
import logging
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Use the single database entry point
from database import session_scope, get_session


class ConversationType(Enum):
    """Types of Claude conversations"""
    SINGLE_QUESTION = "single"      # One-shot Q&A
    TERMINAL_CHAT = "terminal"       # Interactive terminal chat
    WEB_CHAT = "web"                # Web-based chat
    API_DIRECT = "api"               # Direct API call
    DISCORD = "discord"              # Discord bot conversation


@dataclass
class ClaudeConfig:
    """Configuration for Claude service"""
    api_key: Optional[str] = None
    model: str = "claude-3-haiku-20240307"
    max_tokens: int = 4000
    temperature: float = 0.7
    web_port: int = 8082
    terminal_mode: str = "curses"
    
    def __post_init__(self):
        """Load API key from environment if not provided"""
        if not self.api_key:
            self.api_key = os.getenv('ANTHROPIC_API_KEY')
    
    @property
    def is_enabled(self) -> bool:
        """Check if Claude service is enabled"""
        return bool(self.api_key)


@dataclass
class ConversationResult:
    """Result from a Claude conversation"""
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    conversation_type: ConversationType = ConversationType.SINGLE_QUESTION
    metadata: Dict[str, Any] = None


class ClaudeService:
    """
    SINGLE SOURCE OF TRUTH for all Claude/AI operations.
    This is the ONLY service that should interact with Claude API.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern - only ONE Claude service"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[ClaudeConfig] = None):
        """Initialize Claude service (only runs once)"""
        if not self._initialized:
            self.config = config or ClaudeConfig()
            self._api_client = None
            self._conversation_history = []
            self._active_conversations = {}
            
            # Statistics tracking
            self._stats = {
                'total_questions': 0,
                'total_responses': 0,
                'terminal_sessions': 0,
                'web_sessions': 0,
                'api_calls': 0,
                'errors': 0
            }
            
            ClaudeService._initialized = True
            
            if self.config.is_enabled:
                print("✅ Claude service initialized (SINGLE SOURCE OF TRUTH)")
                print(f"   Model: {self.config.model}")
            else:
                print("⚠️  Claude service disabled (no API key)")
    
    @property
    def is_enabled(self) -> bool:
        """Check if Claude service is enabled"""
        return self.config.is_enabled
    
    def _ensure_enabled(self) -> bool:
        """Ensure Claude service is enabled"""
        if not self.is_enabled:
            raise RuntimeError(
                "Claude service is not enabled. "
                "Set ANTHROPIC_API_KEY environment variable to enable."
            )
        return True
    
    @property
    def api_client(self):
        """Lazy load API client - SINGLE instance"""
        if self._api_client is None and self.is_enabled:
            try:
                import anthropic
                self._api_client = anthropic.Anthropic(api_key=self.config.api_key)
            except ImportError:
                raise RuntimeError("AI service module not available")
        return self._api_client
    
    # ========================================================================
    # SINGLE QUESTION - The simplest Claude interaction
    # ========================================================================
    
    def ask_question(self, question: str, context: Optional[Dict[str, Any]] = None) -> ConversationResult:
        """
        Ask Claude a single question and get a response.
        This is the PRIMARY method for simple Q&A.
        """
        self._ensure_enabled()
        self._stats['total_questions'] += 1
        
        try:
            # Add context if provided
            full_question = self._add_context_to_question(question, context)
            
            # Get response from API
            # Use Anthropic API directly
            message = self.api_client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": full_question}
                ]
            )
            response = message.content[0].text
            
            self._stats['total_responses'] += 1
            self._stats['api_calls'] += 1
            
            # Store in history
            self._conversation_history.append({
                'question': question,
                'response': response,
                'context': context
            })
            
            return ConversationResult(
                success=True,
                response=response,
                conversation_type=ConversationType.SINGLE_QUESTION
            )
            
        except Exception as e:
            self._stats['errors'] += 1
            return ConversationResult(
                success=False,
                error=str(e),
                conversation_type=ConversationType.SINGLE_QUESTION
            )
    
    def _add_context_to_question(self, question: str, context: Optional[Dict[str, Any]]) -> str:
        """Add database context to question if provided"""
        if not context:
            return question
        
        # Add tournament context if requested
        if context.get('include_tournaments'):
            with session_scope() as session:
                from tournament_models import Tournament
                recent = session.query(Tournament).order_by(
                    Tournament.start_at.desc()
                ).limit(5).all()
                
                if recent:
                    context_str = "\nRecent tournaments:\n"
                    for t in recent:
                        context_str += f"- {t.name} ({t.num_attendees} attendees)\n"
                    question = f"{question}\n{context_str}"
        
        return question
    
    # ========================================================================
    # TERMINAL CHAT - Interactive terminal conversation
    # ========================================================================
    
    def start_terminal_chat(self) -> ConversationResult:
        """
        Start an interactive terminal chat with Claude.
        This would launch the terminal UI for continuous conversation.
        """
        self._ensure_enabled()
        self._stats['terminal_sessions'] += 1
        
        # For now, return a message that terminal chat is not yet implemented
        return ConversationResult(
            success=False,
            error="Terminal chat interface not yet implemented",
            conversation_type=ConversationType.TERMINAL_CHAT
        )
    
    # ========================================================================
    # WEB CHAT - Web-based conversation interface
    # ========================================================================
    
    def start_web_chat(self, port: Optional[int] = None) -> ConversationResult:
        """
        Start web-based chat interface with Claude.
        This would launch a web server for browser-based chat.
        """
        self._ensure_enabled()
        self._stats['web_sessions'] += 1
        
        port = port or self.config.web_port
        
        # For now, return a message that web chat is not yet implemented
        return ConversationResult(
            success=False,
            error="Web chat interface not yet implemented",
            conversation_type=ConversationType.WEB_CHAT,
            metadata={'port': port}
        )
    
    # ========================================================================
    # CONVERSATION MANAGEMENT
    # ========================================================================
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history"""
        if limit:
            return self._conversation_history[-limit:]
        return self._conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self._conversation_history = []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Claude service statistics"""
        return {
            'enabled': self.is_enabled,
            'config': {
                'model': self.config.model,
                'max_tokens': self.config.max_tokens,
                'temperature': self.config.temperature
            },
            'usage': self._stats.copy(),
            'history_size': len(self._conversation_history)
        }
    
    # ========================================================================
    # SPECIALIZED TOURNAMENT QUESTIONS
    # ========================================================================
    
    def ask_about_tournaments(self, question: str) -> ConversationResult:
        """Ask Claude about tournaments with automatic context"""
        return self.ask_question(
            question,
            context={'include_tournaments': True}
        )
    
    def ask_about_players(self, question: str, player_name: Optional[str] = None) -> ConversationResult:
        """Ask Claude about players"""
        context = {}
        
        if player_name:
            # Add player context
            with session_scope() as session:
                from tournament_models import Player
                player = session.query(Player).filter(
                    Player.gamer_tag.ilike(f'%{player_name}%')
                ).first()
                
                if player:
                    context['player'] = {
                        'gamer_tag': player.gamer_tag,
                        'name': player.name
                    }
        
        return self.ask_question(question, context)
    
    def generate_summary(self, topic: str = "recent activity") -> ConversationResult:
        """Ask Claude to generate a summary"""
        question = f"Please provide a summary of {topic} based on the tournament database."
        return self.ask_about_tournaments(question)
    
    # ========================================================================
    # DISCORD BOT SUPPORT - Database code generation
    # ========================================================================
    
    def ask_discord_database_question(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Ask Claude to generate database query code for Discord bot.
        Returns JSON with 'code' field and optional 'intent' field.
        """
        self._ensure_enabled()
        
        try:
            # System prompt specifically for database queries
            system_prompt = (
                "You help users query a tournament database. "
                "Return JSON with 'code' field containing Python to execute and optional 'intent' field. "
                "The code has access to: session (SQLAlchemy), Player, Tournament, TournamentPlacement, Organization models. "
                "Set 'output' variable with the result."
            )
            
            message = self.api_client.messages.create(
                model=self.config.model,
                max_tokens=300,  # Discord needs shorter responses
                system=system_prompt,
                messages=[{
                    "role": "user", 
                    "content": user_message
                }]
            )
            
            # Parse the JSON response
            response_text = message.content[0].text.strip()
            
            self._stats['api_calls'] += 1
            
            try:
                import json
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from the response if it has extra text
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return {"intent": "unknown"}
                
        except Exception as e:
            self._stats['errors'] += 1
            logger.error(f"Discord database query failed: {e}")
            return None
    
    # ========================================================================
    # ASYNC SUPPORT (for Discord bot, etc.)
    # ========================================================================
    
    async def ask_question_async(self, question: str, context: Optional[Dict[str, Any]] = None) -> ConversationResult:
        """Async version of ask_question for Discord bot"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.ask_question, question, context)
    
    async def ask_discord_database_question_async(self, user_message: str) -> Optional[Dict[str, Any]]:
        """Async version of Discord database question for Discord bot"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.ask_discord_database_question, user_message)


# ============================================================================
# GLOBAL INSTANCE - The ONE and ONLY Claude service
# ============================================================================

claude_service = ClaudeService()


# ============================================================================
# CONVENIENCE FUNCTIONS - These all go through the single service
# ============================================================================

def ask_claude(question: str, **kwargs) -> str:
    """Simple wrapper to ask Claude a question"""
    result = claude_service.ask_question(question, kwargs.get('context'))
    if result.success:
        return result.response
    else:
        return f"Error: {result.error}"


def start_claude_chat(mode: str = "terminal") -> bool:
    """Start Claude chat in specified mode"""
    if mode == "terminal":
        result = claude_service.start_terminal_chat()
    elif mode == "web":
        result = claude_service.start_web_chat()
    else:
        raise ValueError(f"Unknown chat mode: {mode}")
    
    return result.success


def is_claude_enabled() -> bool:
    """Check if Claude is enabled"""
    return claude_service.is_enabled


# ============================================================================
# MAIN - Test the service
# ============================================================================

if __name__ == "__main__":
    print("Testing Claude service (SINGLE SOURCE OF TRUTH)...")
    
    if is_claude_enabled():
        print("✅ Claude is enabled")
        
        # Test single question
        result = claude_service.ask_question("What is the tournament tracker?")
        if result.success:
            print(f"Response: {result.response[:200]}...")
        
        # Show stats
        stats = claude_service.get_statistics()
        print(f"\nStatistics: {stats}")
    else:
        print("❌ Claude is not enabled (set ANTHROPIC_API_KEY)")