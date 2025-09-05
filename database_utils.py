"""
database_utils.py - DEPRECATED - Compatibility shim for database module

⚠️ DEPRECATED: This module should not be used directly anymore.
All database access should go through the central 'database' module.

This file now acts as a compatibility layer to redirect old imports
to the proper database module to ensure single point of database access.
"""

import warnings
import sys
from typing import Optional, Any

# Import everything from the central database module
from database import (
    session_scope,
    get_session as _get_session,
    Session,
    engine,
    init_database,
    clear_session
)

# Import commonly used functions that were in database_utils
from database_service import database_service

# Show deprecation warning when this module is imported
warnings.warn(
    "database_utils is deprecated. Please use 'from database import session_scope, get_session' instead",
    DeprecationWarning,
    stacklevel=2
)

# Compatibility functions that redirect to database module
def init_db(database_url: Optional[str] = None):
    """Initialize database - DEPRECATED - Use database.init_database()"""
    warnings.warn(
        "init_db() is deprecated. Use 'from database import init_database' instead",
        DeprecationWarning,
        stacklevel=2
    )
    init_database()
    return engine, Session

# Create get_session as a compatibility wrapper
def get_session():
    """Get database session - DEPRECATED - Use database.session_scope()"""
    warnings.warn(
        "get_session() is deprecated. Use 'from database import session_scope' instead",
        DeprecationWarning,
        stacklevel=2
    )
    return session_scope()

# Compatibility wrapper for normalize_contact
def normalize_contact(contact: str) -> str:
    """Normalize contact - DEPRECATED - Use database_service methods"""
    return database_service.normalize_contact(contact)

# Add functions that were commonly imported from database_utils
def get_attendance_rankings(limit: Optional[int] = None):
    """Get attendance rankings - DEPRECATED - Use database_service.get_attendance_rankings()"""
    return database_service.get_attendance_rankings(limit)

def get_summary_stats():
    """Get summary stats - DEPRECATED - Use database_service.get_summary_stats()"""
    stats = database_service.get_summary_stats()
    # Convert DatabaseStats object to dict for compatibility
    return {
        'total_organizations': stats.total_organizations,
        'total_tournaments': stats.total_tournaments,
        'total_players': stats.total_players,
        'total_attendance': getattr(stats, 'total_attendance', 0),
        'total_placements': stats.total_placements
    }

def get_all_organizations():
    """Get all organizations - DEPRECATED"""
    from tournament_models import Organization
    with session_scope() as session:
        orgs = session.query(Organization).all()
        return [{
            'id': org.id,
            'display_name': org.display_name,
            'contacts': org.contacts
        } for org in orgs]

def save_organization_name(org_id: int, new_name: str):
    """Save organization name - DEPRECATED"""
    from tournament_models import Organization
    with session_scope() as session:
        org = session.query(Organization).get(org_id)
        if org:
            org.display_name = new_name
            session.commit()
            return True
    return False

def get_or_create_player(startgg_id: str, gamer_tag: str, name: Optional[str] = None):
    """Get or create player - DEPRECATED"""
    from tournament_models import Player
    with session_scope() as session:
        player = session.query(Player).filter_by(startgg_id=startgg_id).first()
        if not player:
            player = Player(
                startgg_id=startgg_id,
                gamer_tag=gamer_tag,
                name=name
            )
            session.add(player)
            session.commit()
        return player

def get_or_create_tournament(startgg_id: str, **kwargs):
    """Get or create tournament - DEPRECATED"""
    from tournament_models import Tournament
    with session_scope() as session:
        tournament = session.query(Tournament).filter_by(startgg_id=startgg_id).first()
        if not tournament:
            tournament = Tournament(startgg_id=startgg_id, **kwargs)
            session.add(tournament)
            session.commit()
        return tournament

# For backward compatibility, ensure the module appears to have been initialized
if Session is None:
    init_database()

__all__ = [
    'init_db',
    'get_session', 
    'session_scope',
    'normalize_contact',
    'get_attendance_rankings',
    'get_summary_stats',
    'get_all_organizations',
    'save_organization_name',
    'get_or_create_player',
    'get_or_create_tournament',
    'Session',
    'engine'
]