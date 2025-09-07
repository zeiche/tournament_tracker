# Compatibility shim - redirect to polymorphic_core
from polymorphic_core import announcer, CapabilityAnnouncer, announces_capability

__all__ = ['announcer', 'CapabilityAnnouncer', 'announces_capability']


# When models are imported, they announce themselves
def announce_models():
    """
    Models announce what they can do when loaded.
    """
    try:
        # Tournament model announces itself
        announcer.announce(
            "Tournament Model",
            [
                "Track tournament events with dates and locations",
                "Calculate attendance and growth metrics",
                "Determine if tournaments are majors",
                "Measure days since tournament"
            ],
            [
                "Ask about recent tournaments",
                "Get tournament attendance numbers",
                "Find tournaments by venue"
            ]
        )
        
        # Player model announces itself
        announcer.announce(
            "Player Model", 
            [
                "Track player performance and standings",
                "Calculate win rates and consistency scores",
                "Show podium finishes",
                "Rank players by points"
            ],
            [
                "Show top players",
                "Get player statistics",
                "Find player's tournament history"
            ]
        )
        
        # Organization model announces itself
        announcer.announce(
            "Organization Model",
            [
                "Track tournament organizers and venues",
                "Count total events hosted",
                "Manage contact information",
                "Show organization growth"
            ],
            [
                "Which venues host the most events",
                "Organization contact details",
                "Venue tournament history"
            ]
        )
        
    except Exception as e:
        announcer.announce(
            "Error Reporter",
            [f"Models couldn't fully announce: {e}"]
        )


def announce_queries():
    """
    Query system announces its capabilities.
    """
    try:
        announcer.announce(
            "Query Engine",
            [
                "Natural language tournament queries",
                "Top player rankings",
                "Recent tournament listings",
                "Organization statistics"
            ],
            [
                "show top 10 players",
                "recent tournaments",
                "show player WEST"
            ]
        )
    except:
        pass


def get_full_context():
    """
    Get all announcements for Claude - this is what Discord bot calls.
    """
    # Clear and re-announce (in case new services loaded)
    global announcer
    announcer = CapabilityAnnouncer()
    
    # Services announce themselves
    announce_models()
    announce_queries()
    
    # Check what's actually available
    try:
        import tournament_models
        announcer.announce(
            "System Status",
            ["tournament_models module is loaded and ready"]
        )
    except:
        announcer.announce(
            "System Status", 
            ["Running in limited mode - models not loaded"]
        )
    
    return announcer.get_announcements_for_claude()


if __name__ == "__main__":
    # Test announcements
    print(get_full_context())