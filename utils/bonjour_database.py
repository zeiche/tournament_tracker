#!/usr/bin/env python3
"""
bonjour_database.py - Database operations that announce themselves
Wraps database sessions to announce queries, commits, and errors.
"""
from typing import Any, Optional
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import event
from polymorphic_core import announcer
from database import get_session as original_get_session


class AnnouncingSession:
    """
    Wrapper around SQLAlchemy session that announces database operations.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self._operation_count = 0
        self._query_count = 0
        
        # Announce session creation
        announcer.announce(
            "Database Session",
            ["New database session created", f"Session ID: {id(session)}"]
        )
        
        # Hook into SQLAlchemy events
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners for announcements"""
        
        # Hook into the connection's execute events
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        # Listen to all engine execute events
        @event.listens_for(Engine, "before_execute")
        def receive_before_execute(conn, clauseelement, multiparams, params, execution_options):
            self._query_count += 1
            query_str = str(clauseelement)[:100]  # First 100 chars
            announcer.announce(
                "Database Query",
                [
                    f"Executing query #{self._query_count}",
                    f"Query: {query_str}..."
                ]
            )
        
        # After bulk insert
        @event.listens_for(self.session, "after_bulk_insert", propagate=True)
        def receive_after_bulk_insert(mapper, conn, table, primary_key_list):
            announcer.announce(
                "Database Bulk Insert",
                [
                    f"Bulk inserted {len(primary_key_list)} records",
                    f"Table: {table.name}"
                ]
            )
        
        # After bulk update
        @event.listens_for(self.session, "after_bulk_update", propagate=True)
        def receive_after_bulk_update(mapper, conn, table, params):
            announcer.announce(
                "Database Bulk Update",
                [
                    f"Bulk updated records in {table.name}"
                ]
            )
        
        # After bulk delete
        @event.listens_for(self.session, "after_bulk_delete", propagate=True)
        def receive_after_bulk_delete(mapper, conn, table):
            announcer.announce(
                "Database Bulk Delete",
                [
                    f"Bulk deleted records from {table.name}"
                ]
            )
    
    def query(self, *args, **kwargs):
        """Wrap query method with announcements"""
        self._operation_count += 1
        
        # Get the model being queried
        model_name = "Unknown"
        if args and hasattr(args[0], "__name__"):
            model_name = args[0].__name__
        
        announcer.announce(
            "Database Query Start",
            [f"Starting query for {model_name}"]
        )
        
        try:
            result = self.session.query(*args, **kwargs)
            return result
        except Exception as e:
            announcer.announce(
                "Database Query Error",
                [f"Query failed for {model_name}", f"Error: {str(e)}"]
            )
            raise
    
    def add(self, instance):
        """Wrap add method with announcements"""
        model_name = instance.__class__.__name__
        instance_id = getattr(instance, 'id', 'new')
        
        announcer.announce(
            "Database Add",
            [f"Adding {model_name} (id: {instance_id}) to session"]
        )
        
        return self.session.add(instance)
    
    def commit(self):
        """Wrap commit with announcements"""
        announcer.announce(
            "Database Commit",
            [
                f"Committing transaction",
                f"Operations in transaction: {self._operation_count}",
                f"Queries executed: {self._query_count}"
            ]
        )
        
        try:
            result = self.session.commit()
            announcer.announce(
                "Database Commit Success",
                ["Transaction committed successfully"]
            )
            # Reset counters after successful commit
            self._operation_count = 0
            self._query_count = 0
            return result
        except Exception as e:
            announcer.announce(
                "Database Commit Error",
                [f"Commit failed: {str(e)}"]
            )
            raise
    
    def rollback(self):
        """Wrap rollback with announcements"""
        announcer.announce(
            "Database Rollback",
            [
                "Rolling back transaction",
                f"Operations discarded: {self._operation_count}"
            ]
        )
        
        result = self.session.rollback()
        self._operation_count = 0
        self._query_count = 0
        return result
    
    def close(self):
        """Wrap close with announcements"""
        announcer.announce(
            "Database Session Close",
            [
                f"Closing session ID: {id(self.session)}",
                f"Total queries: {self._query_count}"
            ]
        )
        return self.session.close()
    
    def __getattr__(self, name):
        """Forward all other attributes to the wrapped session"""
        return getattr(self.session, name)


@contextmanager
def get_announcing_session():
    """
    Get a database session that announces all its operations.
    Drop-in replacement for get_session().
    """
    session = None
    try:
        # Get original session
        session = original_get_session()
        
        # Wrap it with announcer
        announcing_session = AnnouncingSession(session)
        
        yield announcing_session
        
    except Exception as e:
        announcer.announce(
            "Database Session Error",
            [f"Session error: {str(e)}"]
        )
        if session:
            session.rollback()
        raise
    finally:
        if session:
            session.close()


# Monkey-patch the database module to use announcing sessions
def enable_database_announcements():
    """
    Enable database announcements globally.
    Call this once at startup to make all database operations announce.
    """
    import database
    
    # Replace the get_session function
    database.get_session = get_announcing_session
    
    announcer.announce(
        "Database Announcements",
        ["Database announcements enabled", "All queries will now be announced"]
    )


# Convenience function to get stats about current database
def announce_database_stats():
    """Announce current database statistics"""
    try:
        with original_get_session() as session:
            from database.tournament_models import Tournament, Player, Organization, TournamentPlacement
            
            tournament_count = session.query(Tournament).count()
            player_count = session.query(Player).count()
            org_count = session.query(Organization).count()
            placement_count = session.query(TournamentPlacement).count()
            
            announcer.announce(
                "Database Statistics",
                [
                    f"Tournaments: {tournament_count}",
                    f"Players: {player_count}",
                    f"Organizations: {org_count}",
                    f"Placements: {placement_count}"
                ]
            )
    except Exception as e:
        announcer.announce(
            "Database Statistics Error",
            [f"Could not get database stats: {str(e)}"]
        )