#!/usr/bin/env python3
"""
initialize_bonjour.py - Initialize all Bonjour announcements at startup
Import this AFTER database and models are loaded to avoid circular imports.
"""

def initialize_all_bonjour():
    """Initialize Bonjour for all components"""
    from polymorphic_core import announcer
    
    # Announce initialization
    announcer.announce(
        "Bonjour Initializer",
        [
            "Initializing Bonjour announcements for all components",
            "Database operations will be tracked",
            "Model operations will be announced",
            "Services will announce themselves"
        ]
    )
    
    # Enable database announcements (if available)
    try:
        from bonjour_database import enable_database_announcements
        enable_database_announcements()
        print("✅ Database Bonjour enabled")
    except Exception as e:
        print(f"⚠️  Database Bonjour not enabled: {e}")
    
    # Announce that models are ready
    try:
        from tournament_models import Tournament, Player, Organization
        announcer.announce(
            "Models Ready",
            [
                "Tournament model loaded with AnnouncerMixin",
                "Player model loaded with AnnouncerMixin",
                "Organization model loaded with AnnouncerMixin",
                "Models will announce save/update/delete operations"
            ]
        )
        print("✅ Model Bonjour ready")
    except Exception as e:
        print(f"⚠️  Model Bonjour issue: {e}")
    
    # Logger Bonjour integration
    try:
        from utils.logger import logger
        announcer.announce(
            "Logger Ready",
            ["Clean logger with 3-method pattern active"]
        )
        print("✅ Logger Bonjour ready")
    except:
        pass
    
    print("\n🎉 Bonjour initialization complete!")
    return True


if __name__ == "__main__":
    initialize_all_bonjour()