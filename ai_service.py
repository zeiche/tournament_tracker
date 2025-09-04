#!/usr/bin/env python3
"""
Unified AI Service for Tournament Tracker
Provides AI capabilities to Discord, Web, and Curses interfaces
"""

import os
import sys
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any, List
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_utils import get_session, get_summary_stats, get_attendance_rankings, get_player_rankings, find_player_ranking
from tournament_models import Tournament, Organization

logger = logging.getLogger('ai_service')

class ChannelType(Enum):
    """Types of channels/contexts for AI responses"""
    GENERAL = "general"
    STATS = "stats"
    DEVELOPER = "developer"
    WEB = "web"
    CURSES = "curses"

class AIService:
    """Unified AI service for all interfaces"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            # Try loading from .env.discord
            env_file = '/home/ubuntu/claude/.env.discord'
            if os.path.exists(env_file):
                with open(env_file) as f:
                    for line in f:
                        if line.startswith('ANTHROPIC_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                            break
        
        self.enabled = bool(self.api_key)
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-haiku-20240307"
        
        # Load current stats for context
        self.stats_context = self._load_stats_context()
        
        logger.info(f"AI Service initialized - Enabled: {self.enabled}")
    
    def _load_stats_context(self) -> Dict[str, Any]:
        """Load current database statistics for context"""
        try:
            stats = get_summary_stats()
            top_orgs = get_attendance_rankings(5)
            top_players = get_player_rankings(limit=10)
            
            context = {
                'total_organizations': stats.get('total_organizations', 0),
                'total_tournaments': stats.get('total_tournaments', 0),
                'total_attendance': stats.get('total_attendance', 0),
                'top_organizations': [
                    {
                        'name': org['display_name'],
                        'attendance': org['total_attendance'],
                        'events': org['tournament_count']
                    }
                    for org in top_orgs
                ],
                'top_players': [
                    {
                        'rank': p['rank'],
                        'gamer_tag': p['gamer_tag'],
                        'points': p['total_points'],
                        'tournaments': p['tournament_count']
                    }
                    for p in top_players
                ] if top_players else []
            }
            return context
        except Exception as e:
            logger.error(f"Failed to load stats context: {e}")
            return {}
    
    def get_system_prompt(self, channel_type: ChannelType) -> str:
        """Get appropriate system prompt based on channel type"""
        base_prompt = """You are a helpful AI assistant for the Southern California Fighting Game Community tournament tracker.

You have access to tournament data, attendance statistics, organization rankings, and player rankings based on tournament placements."""
        
        # Add stats context
        if self.stats_context:
            base_prompt += f"""

Current Database Statistics:
- Total Organizations: {self.stats_context.get('total_organizations', 0)}
- Total Tournaments: {self.stats_context.get('total_tournaments', 0)}
- Total Attendance: {self.stats_context.get('total_attendance', 0)}"""
            
            if self.stats_context.get('top_organizations'):
                base_prompt += "\n\nTop Organizations:"
                for org in self.stats_context['top_organizations'][:5]:
                    base_prompt += f"\n- {org['name']}: {org['attendance']} attendees across {org['events']} events"
            
            if self.stats_context.get('top_players'):
                base_prompt += "\n\nTop Players (Power Rankings):"
                for player in self.stats_context['top_players'][:10]:
                    base_prompt += f"\n- #{player['rank']} {player['gamer_tag']}: {player['points']} points from {player['tournaments']} tournaments"
        
        # Channel-specific behavior
        if channel_type == ChannelType.GENERAL:
            base_prompt += """

You're in a general chat context. Be friendly and conversational. Don't focus heavily on tournament stats unless asked.
Keep responses light and engaging."""
        
        elif channel_type == ChannelType.STATS:
            base_prompt += """

You're in a statistics context. Focus on tournament data, attendance numbers, and analytical insights.
Provide specific numbers, trends, and data visualizations when relevant.
Heat map visualizations exist at tournament_heatmap.png and attendance_heatmap.png."""
        
        elif channel_type == ChannelType.DEVELOPER:
            base_prompt += """

You're in a developer context. Be direct and technical.
NEVER introduce yourself as an AI assistant.
Just answer questions and execute tasks.
Skip the fluff - developers want results, not conversation."""
        
        elif channel_type == ChannelType.WEB:
            base_prompt += """

You're in a web interface. Users are accessing you through a browser.
Be helpful with both tournament data and general questions.
You can suggest visualizations and provide detailed information."""
        
        elif channel_type == ChannelType.CURSES:
            base_prompt += """

You're in a terminal/curses interface. Keep responses concise for terminal display.
Focus on text-based information that works well in a console.
Use ASCII formatting when appropriate."""
        
        base_prompt += "\n\nBe concise and helpful. Keep responses under 2000 characters."
        
        return base_prompt
    
    async def get_response(
        self, 
        message: str, 
        channel_type: ChannelType = ChannelType.GENERAL,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get AI response for a message
        
        Args:
            message: User's message
            channel_type: Type of channel/interface
            context: Additional context (e.g., user info, session data)
        
        Returns:
            AI-generated response string
        """
        if not self.enabled:
            return self._get_fallback_response(message, channel_type)
        
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # Build context message
            context_message = message
            if context:
                if context.get('user'):
                    context_message = f"[User: {context['user']}] {message}"
                if context.get('session_id'):
                    context_message = f"[Session: {context['session_id']}] {context_message}"
            
            # Check for player names in message and add context
            msg_lower = message.lower()
            if any(term in msg_lower for term in ['ranking', 'rank', 'player', 'singles', 'doubles']):
                words = message.split()
                player_context = []
                skip_words = {'the', 'is', 'in', 'at', 'for', 'what', 'where', 'how', 'who', 
                             'singles', 'doubles', 'ultimate', 'squad', 'strike', 'ranking', 
                             'rank', 'player', 'top', 'best', 'show', 'list', 'get', 'of'}
                
                for word in words:
                    # Clean the word - remove apostrophes and punctuation
                    clean_word = word.strip("'\".,!?:;").rstrip("'s")
                    if clean_word.lower() not in skip_words and len(clean_word) > 2:
                        player_info = find_player_ranking(clean_word, None, fuzzy_threshold=0.7)
                        if player_info:
                            player_context.append(f"\n[Player Data: {player_info['gamer_tag']} is ranked #{player_info['rank']} with {player_info['total_points']} points]")
                
                if player_context:
                    context_message += "".join(player_context)
            
            data = {
                "model": self.model,
                "max_tokens": 500,
                "temperature": 0.7,
                "system": self.get_system_prompt(channel_type),
                "messages": [
                    {
                        "role": "user",
                        "content": context_message
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result['content'][0]['text']
                    logger.info(f"AI response generated for: {message[:50]}...")
                    return ai_response
                else:
                    logger.error(f"API error: {response.status_code}")
                    return self._get_fallback_response(message, channel_type)
                    
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return self._get_fallback_response(message, channel_type)
    
    def get_response_sync(
        self, 
        message: str, 
        channel_type: ChannelType = ChannelType.GENERAL,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Synchronous wrapper for get_response"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.get_response(message, channel_type, context)
            )
        finally:
            loop.close()
    
    def _get_fallback_response(self, message: str, channel_type: ChannelType) -> str:
        """Fallback responses when AI is not available"""
        msg_lower = message.lower()
        
        # Check for player queries
        if 'ranking' in msg_lower or 'rank' in msg_lower or 'player' in msg_lower:
            # Look for potential player names (any words not in skip list)
            words = message.split()
            skip_words = {'the', 'is', 'in', 'at', 'for', 'what', 'where', 'how', 'who', 
                         'singles', 'doubles', 'ultimate', 'squad', 'strike', 'ranking', 
                         'rank', 'player', 'top', 'best', 'show', 'list', 'get', 'of'}
            
            for word in words:
                # Clean the word - remove apostrophes and punctuation
                clean_word = word.strip("'\".,!?:;").rstrip("'s")
                if clean_word.lower() not in skip_words and len(clean_word) > 2:
                    player_info = find_player_ranking(clean_word, None, fuzzy_threshold=0.7)
                    if player_info:
                        response = f"{player_info['gamer_tag']} is ranked #{player_info['rank']} "
                        response += f"with {player_info['total_points']} points from {player_info['tournament_count']} tournaments."
                        if player_info.get('recent_placements'):
                            response += "\nRecent placements:"
                            for p in player_info['recent_placements'][:3]:
                                response += f"\n- {p['placement']} at {p['tournament']} ({p['event']})"
                        return response
        
        if channel_type == ChannelType.STATS:
            if 'hi' in msg_lower or 'hello' in msg_lower:
                return "Welcome to tournament stats! I can help with attendance data and rankings."
            elif 'help' in msg_lower:
                return "I track tournament statistics, organization rankings, and attendance trends."
            else:
                return "I can provide tournament statistics and organization data."
        
        elif channel_type == ChannelType.DEVELOPER:
            if 'hi' in msg_lower or 'hello' in msg_lower:
                return "Hey! Ready to help with code."
            else:
                return "I can help with technical questions about the tournament tracker."
        
        else:
            if 'hi' in msg_lower or 'hello' in msg_lower:
                return "Hello! How can I help you today?"
            else:
                return "I'm here to help! What would you like to know?"
    
    def search_data(self, query: str) -> List[Dict[str, Any]]:
        """Search tournament data based on query"""
        results = []
        
        try:
            with get_session() as session:
                # Search organizations
                orgs = session.query(Organization).filter(
                    Organization.display_name.ilike(f"%{query}%")
                ).limit(5).all()
                
                for org in orgs:
                    attendance = sum(r.attendance for r in org.attendance_records)
                    results.append({
                        'type': 'organization',
                        'name': org.display_name,
                        'attendance': attendance,
                        'tournaments': len(org.attendance_records)
                    })
                
                # Search tournaments
                tournaments = session.query(Tournament).filter(
                    Tournament.name.ilike(f"%{query}%")
                ).limit(5).all()
                
                for t in tournaments:
                    results.append({
                        'type': 'tournament',
                        'name': t.name,
                        'attendance': t.num_attendees,
                        'venue': t.venue_name
                    })
                    
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        return results
    
    def get_heat_map_paths(self) -> Dict[str, str]:
        """Get paths to heat map visualizations"""
        base_path = '/home/ubuntu/claude/tournament_tracker'
        return {
            'tournament': f'{base_path}/tournament_heatmap.png',
            'attendance': f'{base_path}/attendance_heatmap.png',
            'html': f'{base_path}/tournament_heatmap.html'
        }

# Singleton instance
_ai_service = None

def get_ai_service(api_key: Optional[str] = None) -> AIService:
    """Get or create the AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService(api_key)
    return _ai_service

# Convenience functions
async def get_ai_response(
    message: str,
    channel_type: str = "general",
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Convenience function for getting AI responses"""
    service = get_ai_service()
    
    # Convert string to ChannelType enum
    try:
        channel_enum = ChannelType(channel_type.lower())
    except ValueError:
        channel_enum = ChannelType.GENERAL
    
    return await service.get_response(message, channel_enum, context)

def get_ai_response_sync(
    message: str,
    channel_type: str = "general",
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Synchronous convenience function"""
    service = get_ai_service()
    
    try:
        channel_enum = ChannelType(channel_type.lower())
    except ValueError:
        channel_enum = ChannelType.GENERAL
    
    return service.get_response_sync(message, channel_enum, context)