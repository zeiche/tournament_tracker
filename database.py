#!/usr/bin/env python3
"""
database.py - THE SINGLE DATABASE ENTRY POINT
This is the ONLY place where database connections and sessions are created.
All other modules MUST import from here.
"""
import os
from typing import Optional, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session as SessionType
from sqlalchemy.ext.declarative import declarative_base

# ============================================================================
# SINGLE SOURCE OF TRUTH - Database Configuration
# ============================================================================

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tournament_tracker.db')

# ============================================================================
# SINGLE SOURCE OF TRUTH - Engine and Session Factory
# ============================================================================

# Create engine ONCE
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create session factory ONCE
SessionLocal = sessionmaker(bind=engine)

# Create scoped session ONCE
Session = scoped_session(SessionLocal)

# Base for all models
Base = declarative_base()

# ============================================================================
# THE ONLY APPROVED WAYS TO GET A SESSION
# ============================================================================

def get_session() -> SessionType:
    """
    Get the current scoped session.
    This is the ONLY approved way to get a session for general use.
    """
    return Session()


@contextmanager
def session_scope() -> Generator[SessionType, None, None]:
    """
    Provide a transactional scope around a series of operations.
    This is the ONLY approved way to get a session with automatic cleanup.
    
    Usage:
        with session_scope() as session:
            session.query(Model).all()
    """
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
def fresh_session() -> Generator[SessionType, None, None]:
    """
    Get a fresh session (not from the scoped registry).
    Use this ONLY when you need to bypass the session cache.
    
    Usage:
        with fresh_session() as session:
            session.query(Model).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def clear_session():
    """
    Clear the current session.
    Use this to force a fresh session on the next get_session() call.
    """
    Session.remove()


# ============================================================================
# DATABASE MANAGEMENT FUNCTIONS
# ============================================================================

def create_all_tables():
    """
    Create all database tables.
    This should be called ONCE during application initialization.
    """
    # Import models to register them with Base
    import tournament_models
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def drop_all_tables():
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    import tournament_models
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All database tables dropped")


def init_database():
    """
    Initialize the database.
    This is the ONLY function that should be called to set up the database.
    """
    create_all_tables()
    return engine, Session


def dispose_engine():
    """
    Dispose of the engine connection pool.
    Call this when shutting down the application.
    """
    engine.dispose()


# ============================================================================
# CONVENIENCE FUNCTIONS FOR COMMON OPERATIONS
# ============================================================================

def execute_query(model_class, **filters):
    """
    Execute a simple query with filters.
    
    Usage:
        users = execute_query(User, active=True)
    """
    with session_scope() as session:
        return session.query(model_class).filter_by(**filters).all()


def get_by_id(model_class, id_value):
    """
    Get a single record by ID.
    
    Usage:
        user = get_by_id(User, 123)
    """
    with session_scope() as session:
        return session.query(model_class).get(id_value)


def create_record(model_instance):
    """
    Create a new record.
    
    Usage:
        user = User(name="John")
        create_record(user)
    """
    with session_scope() as session:
        session.add(model_instance)
        session.flush()
        session.refresh(model_instance)
        return model_instance


def update_record(model_class, id_value, **updates):
    """
    Update a record by ID.
    
    Usage:
        update_record(User, 123, name="Jane", email="jane@example.com")
    """
    with session_scope() as session:
        record = session.query(model_class).get(id_value)
        if record:
            for key, value in updates.items():
                setattr(record, key, value)
            session.flush()
            session.refresh(record)
            return record
        return None


def delete_record(model_class, id_value):
    """
    Delete a record by ID.
    
    Usage:
        delete_record(User, 123)
    """
    with session_scope() as session:
        record = session.query(model_class).get(id_value)
        if record:
            session.delete(record)
            return True
        return False


# ============================================================================
# SINGLETON CHECK - Ensure this module is only imported, never instantiated
# ============================================================================

_initialized = False

def _ensure_single_import():
    """Internal function to ensure this module is only initialized once"""
    global _initialized
    if _initialized:
        raise RuntimeError(
            "database.py has already been initialized! "
            "Do not create multiple database connections. "
            "Import from database.py instead."
        )
    _initialized = True

# Run the check
_ensure_single_import()

# ============================================================================
# WHAT TO IMPORT FROM THIS MODULE
# ============================================================================

__all__ = [
    # Session access (THE ONLY WAYS)
    'get_session',
    'session_scope',
    'fresh_session',
    'clear_session',
    
    # Database management
    'init_database',
    'create_all_tables',
    'drop_all_tables',
    'dispose_engine',
    
    # Convenience functions
    'execute_query',
    'get_by_id',
    'create_record',
    'update_record',
    'delete_record',
    
    # Base and engine (for models and special cases only)
    'Base',
    'engine',
]

# Only print if explicitly requested via environment variable
if os.getenv('DEBUG_DATABASE_INIT'):
    print("📊 Database module initialized (SINGLE ENTRY POINT)")
    print(f"   Database URL: {DATABASE_URL}")
    print("   ✅ This is the ONLY place database connections are created")