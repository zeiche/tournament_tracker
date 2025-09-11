#!/usr/bin/env python3
"""
Database-Only Claude Handler
This module ensures Claude only responds with tournament database information.
All other requests are rejected or redirected to database queries.
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from database import get_session
from tournament_models import Tournament, Organization, Player
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta

class DatabaseOnlyClaudeHandler:
    """Handler that restricts Claude to only database-related queries"""
    
    # Define allowed query types and their keywords
    ALLOWED_QUERIES = {
        'tournaments': ['tournament', 'event', 'competition', 'tourney'],
        'players': ['player', 'gamer', 'competitor', 'participant', 'who played'],
        'organizations': ['organization', 'org', 'organizer', 'TO', 'host'],
        'attendance': ['attendance', 'attendee', 'turnout', 'participation'],
        'rankings': ['ranking', 'top', 'best', 'highest', 'most'],
        'statistics': ['stats', 'statistics', 'count', 'total', 'average'],
        'schedule': ['upcoming', 'next', 'future', 'when', 'schedule'],
        'history': ['past', 'previous', 'last', 'recent', 'history'],
        'venues': ['venue', 'location', 'where', 'place', 'address'],
        'games': ['game', 'title', 'what games', 'which games']
    }
    
    # Reject keywords - queries containing these should be rejected
    REJECT_KEYWORDS = [
        'weather', 'news', 'stock', 'recipe', 'movie', 'song', 
        'tell me about yourself', 'who are you', 'what can you do',
        'write code', 'create', 'generate story', 'poem', 'joke',
        'math', 'calculate', 'solve', 'equation', 'homework',
        'translate', 'language', 'meaning of life', 'philosophy'
    ]
    
    @classmethod
    def is_database_query(cls, query: str) -> Tuple[bool, str]:
        """
        Determine if a query is database-related.
        Returns (is_allowed, category_or_reason)
        """
        query_lower = query.lower().strip()
        
        # First check for reject keywords
        for keyword in cls.REJECT_KEYWORDS:
            if keyword in query_lower:
                return False, f"I can only help with tournament database queries. I cannot help with {keyword} topics."
        
        # Check for allowed query types - prioritize more specific categories
        # Check players first for "who played" type queries
        if 'who played' in query_lower or 'played the most' in query_lower:
            return True, 'players'
        
        for category, keywords in cls.ALLOWED_QUERIES.items():
            if any(keyword in query_lower for keyword in keywords):
                return True, category
        
        # Default rejection
        return False, "I can only answer questions about tournaments, players, and organizations in the database."
    
    @classmethod
    def get_database_context(cls, query: str, category: str) -> Dict[str, Any]:
        """
        Get relevant database context for a query category.
        Returns a structured context dict with database information.
        """
        context = {
            'query': query,
            'category': category,
            'database_info': {},
            'constraints': 'Only use information from the provided database context. Do not use external knowledge.'
        }
        
        with get_session() as session:
            # ALWAYS include basic statistics
            context['database_info']['overall_stats'] = {
                'total_tournaments': session.query(Tournament).count(),
                'total_organizations': session.query(Organization).count(),
                'total_players': session.query(Player).count()
            }
            if category == 'tournaments':
                # Get recent tournaments
                recent = session.query(Tournament).order_by(
                    desc(Tournament.start_at)
                ).limit(10).all()
                
                context['database_info']['recent_tournaments'] = [
                    {
                        'name': t.name,
                        'date': str(t.start_at) if t.start_at else 'Unknown',
                        'attendees': t.num_attendees or 0,
                        'venue': t.venue_name or 'Unknown'
                    }
                    for t in recent
                ]
                
            elif category == 'players':
                # Get top players by event count
                top_players = session.query(
                    Player.gamer_tag,
                    func.count(Player.id).label('events')
                ).group_by(
                    Player.gamer_tag
                ).order_by(
                    desc('events')
                ).limit(20).all()
                
                context['database_info']['top_players'] = [
                    {'gamer_tag': p[0], 'event_count': p[1]}
                    for p in top_players if p[0]
                ]
                
            elif category == 'organizations':
                # Get organizations with tournament counts
                orgs = session.query(
                    Organization.display_name,
                    func.count(Tournament.id).label('count')
                ).join(
                    Tournament,
                    Organization.normalized_key == Tournament.normalized_contact
                ).group_by(
                    Organization.id
                ).order_by(
                    desc('count')
                ).limit(10).all()
                
                context['database_info']['organizations'] = [
                    {'name': o[0], 'tournament_count': o[1]}
                    for o in orgs
                ]
                
            elif category == 'attendance':
                # Get attendance statistics
                stats = session.query(
                    func.sum(Tournament.num_attendees),
                    func.avg(Tournament.num_attendees),
                    func.max(Tournament.num_attendees)
                ).filter(
                    Tournament.num_attendees.isnot(None)
                ).first()
                
                context['database_info']['attendance_stats'] = {
                    'total': int(stats[0]) if stats[0] else 0,
                    'average': round(float(stats[1]), 1) if stats[1] else 0,
                    'maximum': int(stats[2]) if stats[2] else 0
                }
                
            elif category == 'statistics':
                # Get overall statistics
                context['database_info']['overall_stats'] = {
                    'total_tournaments': session.query(Tournament).count(),
                    'total_organizations': session.query(Organization).count(),
                    'total_players': session.query(Player).count(),
                    'tournaments_with_attendance': session.query(Tournament).filter(
                        Tournament.num_attendees.isnot(None)
                    ).count()
                }
                
            elif category == 'schedule':
                # Get upcoming tournaments
                today = datetime.now()
                upcoming = session.query(Tournament).filter(
                    Tournament.start_at > today.timestamp()
                ).order_by(
                    Tournament.start_at
                ).limit(10).all()
                
                context['database_info']['upcoming_tournaments'] = [
                    {
                        'name': t.name,
                        'date': str(datetime.fromtimestamp(t.start_at)) if t.start_at else 'Unknown',
                        'venue': t.venue_name or 'Unknown'
                    }
                    for t in upcoming
                ]
                
            elif category == 'venues':
                # Get venue statistics
                venues = session.query(
                    Tournament.venue_name,
                    func.count(Tournament.id).label('count')
                ).filter(
                    Tournament.venue_name.isnot(None)
                ).group_by(
                    Tournament.venue_name
                ).order_by(
                    desc('count')
                ).limit(10).all()
                
                context['database_info']['top_venues'] = [
                    {'venue': v[0], 'event_count': v[1]}
                    for v in venues
                ]
        
        return context
    
    @classmethod
    def format_restricted_prompt(cls, query: str, context: Dict[str, Any]) -> str:
        """
        Format a prompt that restricts Claude to database information only.
        """
        prompt = f"""You are a tournament database assistant. You can ONLY provide information from the tournament database.

IMPORTANT RESTRICTIONS:
1. You can ONLY use information from the database context provided below
2. You CANNOT use any external knowledge or information
3. If asked about something not in the database, say "I don't have that information in the database"
4. Do not make up or infer information not explicitly in the database

DATABASE CONTEXT:
{context['database_info']}

USER QUESTION: {query}

Remember: Only answer based on the database context above. If the information isn't there, say you don't have it."""
        
        return prompt
    
    @classmethod
    def handle_non_database_query(cls, query: str) -> str:
        """
        Return a polite rejection for non-database queries.
        """
        return """I can only help with tournament database queries. I can answer questions about:
• Tournaments and events
• Players and their performance
• Organizations and organizers
• Attendance and statistics
• Upcoming and past events
• Venues and locations

Please ask me something about the tournament database!"""