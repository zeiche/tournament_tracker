#!/usr/bin/env python3
"""
enable_bonjour_database.py - Enable Bonjour announcements for database operations
Run this at startup to make all database operations announce themselves.
"""

def enable_bonjour_database():
    """Enable database announcements by patching the database module"""
    import database
    from bonjour_database import get_announcing_session, enable_database_announcements
    from polymorphic_core import announcer
    
    # Enable announcements
    enable_database_announcements()
    
    # Announce that database is now Bonjour-enabled
    announcer.announce(
        "Database Bonjour",
        [
            "Database operations will now announce themselves",
            "All queries are tracked",
            "Sessions announce their lifecycle",
            "Commits and rollbacks are announced"
        ]
    )
    
    print("✅ Bonjour database announcements enabled!")

if __name__ == "__main__":
    enable_bonjour_database()