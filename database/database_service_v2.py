"""
database_service_v2.py - Database Service using the SINGLE entry point
This service ONLY uses database.py - it does NOT create its own connections
"""
from typing import Optional, List, Dict, Any, Type, TypeVar, Tuple
from datetime import datetime, timedelta

# IMPORT FROM THE SINGLE DATABASE ENTRY POINT ONLY
from database import (
    get_session,
    session_scope,
    fresh_session,
    clear_session,
    execute_query,
    get_by_id,
    create_record,
    update_record,
    delete_record
)

T = TypeVar('T')


class DatabaseService:
    """
    Database service that uses the SINGLE database entry point.
    This class does NOT create connections - it only uses database.py
    """
    
    def __init__(self):
        """Initialize service - NO database connections created here!"""
        self._stats = {
            'queries': 0,
            'creates': 0,
            'updates': 0,
            'deletes': 0
        }
    
    # ========================================================================
    # CRUD Operations - All using database.py functions
    # ========================================================================
    
    def create(self, model_instance: T) -> T:
        """Create a new record using database.py"""
        self._stats['creates'] += 1
        return create_record(model_instance)
    
    def get(self, model_class: Type[T], primary_key: Any) -> Optional[T]:
        """Get record by ID using database.py"""
        self._stats['queries'] += 1
        return get_by_id(model_class, primary_key)
    
    def update(self, model_class: Type[T], primary_key: Any, **kwargs) -> Optional[T]:
        """Update record using database.py"""
        self._stats['updates'] += 1
        return update_record(model_class, primary_key, **kwargs)
    
    def delete(self, model_class: Type[T], primary_key: Any) -> bool:
        """Delete record using database.py"""
        self._stats['deletes'] += 1
        return delete_record(model_class, primary_key)
    
    def query(self, model_class: Type[T], **filters) -> List[T]:
        """Query records using database.py"""
        self._stats['queries'] += 1
        return execute_query(model_class, **filters)
    
    # ========================================================================
    # Tournament-specific queries - All using database.py session_scope
    # ========================================================================
    
    def get_tournaments(self, 
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       min_attendees: Optional[int] = None) -> List:
        """Get tournaments with filters"""
        from tournament_models import Tournament
        
        with session_scope() as session:
            query = session.query(Tournament)
            
            if start_date:
                query = query.filter(Tournament.start_at >= start_date)
            if end_date:
                query = query.filter(Tournament.end_at <= end_date)
            if min_attendees:
                query = query.filter(Tournament.num_attendees >= min_attendees)
            
            self._stats['queries'] += 1
            return query.order_by(Tournament.start_at.desc()).all()
    
    def get_recent_tournaments(self, days: int = 30) -> List:
        """Get recent tournaments"""
        from tournament_models import Tournament
        
        cutoff = datetime.now() - timedelta(days=days)
        
        with session_scope() as session:
            self._stats['queries'] += 1
            return session.query(Tournament).filter(
                Tournament.start_at >= cutoff
            ).order_by(Tournament.start_at.desc()).all()
    
    def get_organizations_with_stats(self) -> List[Dict[str, Any]]:
        """Get organizations with tournament stats"""
        from tournament_models import Organization, Tournament
        from sqlalchemy import func
        
        with session_scope() as session:
            results = session.query(
                Organization,
                func.count(Tournament.id).label('tournament_count'),
                func.sum(Tournament.num_attendees).label('total_attendance')
            ).outerjoin(
                Tournament,
                Organization.normalized_key == Tournament.normalized_contact
            ).group_by(Organization.id).all()
            
            self._stats['queries'] += 1
            
            return [{
                'organization': org,
                'tournament_count': count or 0,
                'total_attendance': attendance or 0
            } for org, count, attendance in results]
    
    def merge_organizations(self, source_org_id: int, target_org_id: int) -> bool:
        """Merge organizations"""
        from tournament_models import Organization, Tournament
        
        with session_scope() as session:
            source = session.query(Organization).get(source_org_id)
            target = session.query(Organization).get(target_org_id)
            
            if not source or not target:
                return False
            
            # Update tournaments
            session.query(Tournament).filter(
                Tournament.normalized_contact == source.normalized_key
            ).update({'normalized_contact': target.normalized_key})
            
            # Delete source
            session.delete(source)
            
            self._stats['updates'] += 1
            self._stats['deletes'] += 1
            
            return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        from tournament_models import Tournament, Organization, Player
        
        with session_scope() as session:
            stats = {
                'service_operations': self._stats.copy(),
                'database_counts': {
                    'tournaments': session.query(Tournament).count(),
                    'organizations': session.query(Organization).count(),
                    'players': session.query(Player).count()
                }
            }
            
            self._stats['queries'] += 3
            return stats
    
    def clear_cache(self):
        """Clear session cache using database.py"""
        clear_session()


# Global instance (stateless - just tracks stats)
db_service = DatabaseService()