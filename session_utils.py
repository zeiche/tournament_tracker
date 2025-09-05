"""
session_utils.py - DEPRECATED - Redirects to central database module

⚠️ DEPRECATED: This module should not be used directly anymore.
All database access should go through the central 'database' module.

This file acts as a compatibility layer for old code that imports from session_utils.
"""

import warnings
from contextlib import contextmanager

# Import everything from the central database module
from database import (
    session_scope,
    get_session,
    Session,
    engine,
    init_database,
    clear_session
)

# Show deprecation warning
warnings.warn(
    "session_utils is deprecated. Please use 'from database import ...' instead",
    DeprecationWarning,
    stacklevel=2
)

# Compatibility functions
def init_session_manager(database_url=None):
    """Initialize session manager - DEPRECATED"""
    warnings.warn(
        "init_session_manager() is deprecated. Use 'from database import init_database' instead",
        DeprecationWarning,
        stacklevel=2
    )
    init_database()
    return engine, Session

def create_tables():
    """Create all tables - DEPRECATED"""
    from tournament_models import Base
    if engine:
        Base.metadata.create_all(engine)

def get_scoped_session():
    """Get the current scoped session"""
    if Session is None:
        raise RuntimeError("Session manager not initialized. Call init_session_manager() first.")
    return Session

@contextmanager
def fresh_session():
    """Context manager for fresh database sessions"""
    if Session is None:
        raise RuntimeError("Session manager not initialized. Call init_session_manager() first.")
    
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@contextmanager
def transaction():
    """Context manager for database transactions with automatic cleanup"""
    session = get_scoped_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise

def save_and_refresh(obj):
    """Save object and return refreshed dict representation"""
    session = get_scoped_session()
    
    try:
        session.add(obj)
        session.commit()
        session.refresh(obj)  # Ensure object is current
        
        # Convert to dict while session is active
        obj_dict = obj_to_dict(obj)
        
        return obj_dict
        
    except Exception:
        session.rollback()
        raise

def save_multiple_and_refresh(*objects):
    """Save multiple objects in single transaction"""
    session = get_scoped_session()
    
    try:
        for obj in objects:
            session.add(obj)
        
        session.commit()
        
        # Refresh and convert all objects
        result_dicts = []
        for obj in objects:
            session.refresh(obj)
            result_dicts.append(obj_to_dict(obj))
        
        return result_dicts
        
    except Exception:
        session.rollback()
        raise

def flush_and_clear():
    """Flush pending writes and clear session cache"""
    if Session:
        Session.commit()  # Commit any pending transactions
        Session.remove()  # Clear the session cache

def clear_session_cache():
    """Clear SQLAlchemy session cache"""
    if Session:
        Session.remove()

def obj_to_dict(obj):
    """Convert SQLAlchemy object to dictionary"""
    if not obj:
        return None
    
    # Handle different model types
    if hasattr(obj, '__tablename__'):
        table_name = obj.__tablename__
        
        if table_name == 'organizations':
            return {
                'id': obj.id,
                'normalized_key': obj.normalized_key,
                'display_name': obj.display_name,
                'tournament_count': getattr(obj, 'tournament_count', 0),
                'total_attendance': getattr(obj, 'total_attendance', 0),
                'contacts': [contact.contact_value for contact in getattr(obj, 'contacts', [])],
                'created_at': obj.created_at,
                'updated_at': obj.updated_at
            }
        elif table_name == 'tournaments':
            return {
                'id': obj.id,
                'name': obj.name,
                'num_attendees': obj.num_attendees,
                'start_at': obj.start_at,
                'end_at': obj.end_at,
                'normalized_contact': obj.normalized_contact,
                'primary_contact': obj.primary_contact,
                'tournament_state': obj.tournament_state,
                'short_slug': obj.short_slug,
                'slug': obj.slug,
                'url': obj.url
            }
        elif table_name == 'players':
            return {
                'id': obj.id,
                'startgg_id': obj.startgg_id,
                'gamer_tag': obj.gamer_tag,
                'name': obj.name
            }
        else:
            # Generic fallback
            result = {}
            for column in obj.__table__.columns:
                result[column.name] = getattr(obj, column.name)
            return result
    
    return None

@contextmanager
def batch_operation():
    """Context manager for batch database operations"""
    session = get_scoped_session()
    
    try:
        yield session
        session.commit()
        flush_and_clear()  # Clear cache after batch
    except Exception:
        session.rollback()
        raise

def safe_create(model_class, **kwargs):
    """Safely create model and return dict"""
    with transaction() as session:
        obj = model_class(**kwargs)
        session.add(obj)
        session.flush()  # Get ID assigned
        
        # Convert to dict while session is active
        result = obj_to_dict(obj)
    
    flush_and_clear()
    return result

def safe_update(model_class, primary_key, **kwargs):
    """Safely update model and return dict"""
    with transaction() as session:
        obj = session.query(model_class).get(primary_key)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            
            session.flush()
            result = obj_to_dict(obj)
        else:
            result = None
    
    flush_and_clear()
    return result

def safe_get_or_create(model_class, defaults=None, **lookup_kwargs):
    """Safely get or create model and return dict"""
    with transaction() as session:
        obj = session.query(model_class).filter_by(**lookup_kwargs).first()
        
        if not obj:
            # Create new object
            create_kwargs = lookup_kwargs.copy()
            if defaults:
                create_kwargs.update(defaults)
            
            obj = model_class(**create_kwargs)
            session.add(obj)
            session.flush()
        
        result = obj_to_dict(obj)
    
    flush_and_clear()
    return result

if __name__ == "__main__":
    print("🧪 Testing session utilities...")
    
    # Basic session manager test
    try:
        engine, Session = init_session_manager()
        print("✅ Session manager initialized")
        
        # Test session operations
        with fresh_session() as session:
            print("✅ Fresh session context manager works")
        
        print("✅ Session utilities test passed")
        
    except Exception as e:
        print(f"❌ Session utilities test failed: {e}")
        import traceback
        traceback.print_exc()

