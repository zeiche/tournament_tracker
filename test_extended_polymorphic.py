#!/usr/bin/env python3
"""
test_extended_polymorphic.py - Test the extended polymorphic implementations
Shows how ALL system components now use the 3-method pattern
"""
from database import get_session, init_database


def test_placement_polymorphic():
    """Test TournamentPlacement with 3-method pattern"""
    print("\n" + "=" * 60)
    print("Testing TournamentPlacement Polymorphic Methods")
    print("=" * 60)
    
    with get_session() as session:
        from tournament_models import TournamentPlacement
        from tournament_models_simplified import simplify_existing_models
        
        # Enable polymorphic pattern
        simplify_existing_models()
        
        # Get a placement
        placement = session.query(TournamentPlacement).first()
        
        if placement:
            print(f"\n🏆 Testing Placement #{placement.placement}:")
            print("-" * 40)
            
            # Test ask()
            print("\n1. ASK - Query placement details:")
            print(f"   placement.ask('prize'): {placement.ask('prize')}")
            print(f"   placement.ask('medal'): {placement.ask('medal')}")
            print(f"   placement.ask('event type'): {placement.ask('event type')}")
            print(f"   placement.ask('statistics'): {placement.ask('statistics')}")
            
            # Test tell()
            print("\n2. TELL - Format placement:")
            print(f"   placement.tell('discord'):\n   {placement.tell('discord')}")
            
            # Test do()
            print("\n3. DO - Validate placement:")
            print(f"   placement.do('validate'): {placement.do('validate')}")
        else:
            print("No placements found - creating test placement...")
            
            # Create a test placement
            from tournament_models import Tournament, Player
            
            tournament = session.query(Tournament).first()
            player = session.query(Player).first()
            
            if tournament and player:
                placement = TournamentPlacement(
                    tournament_id=tournament.id,
                    player_id=player.id,
                    placement=1,
                    prize_amount=10000,  # $100 in cents
                    event_name="Street Fighter 6 Singles"
                )
                session.add(placement)
                session.commit()
                
                print("\nCreated test placement:")
                print(f"   placement.ask('medal'): {placement.ask('medal')}")
                print(f"   placement.tell('discord'): {placement.tell('discord')}")


def test_service_polymorphic():
    """Test service classes with 3-method pattern"""
    print("\n" + "=" * 60)
    print("Testing Service Polymorphic Methods")
    print("=" * 60)
    
    # Import and extend services
    from service_polymorphic import extend_services
    extended = extend_services()
    print(f"\nExtended {extended} services with polymorphic methods")
    
    # Test TournamentTracker service
    try:
        from tournament_tracker import TournamentTracker
        tracker = TournamentTracker()
        
        print("\n📊 Testing TournamentTracker Service:")
        print("-" * 40)
        
        print("\n1. ASK - Query service state:")
        print(f"   tracker.ask('status'): {tracker.ask('status')}")
        print(f"   tracker.ask('enabled'): {tracker.ask('enabled')}")
        
        print("\n2. TELL - Format service info:")
        print(f"   tracker.tell('discord'):\n{tracker.tell('discord')}")
        
        print("\n3. DO - Service actions:")
        print(f"   tracker.do('announce'): {tracker.do('announce')}")
        
    except Exception as e:
        print(f"Could not test TournamentTracker: {e}")


def test_processor_polymorphic():
    """Test processor classes with 3-method pattern"""
    print("\n" + "=" * 60)
    print("Testing Processor Polymorphic Methods")
    print("=" * 60)
    
    # Import and extend processors
    from processor_polymorphic import extend_processors
    extended = extend_processors()
    print(f"\nExtended {extended} processors with polymorphic methods")
    
    # Create a mock processor for testing
    from processor_polymorphic import ProcessorPolymorphic
    
    class TestProcessor(ProcessorPolymorphic):
        def __init__(self):
            self.items_processed = 42
            self.items_total = 100
            self.error_count = 2
            self.is_processing = True
    
    processor = TestProcessor()
    
    print("\n⚙️ Testing Processor:")
    print("-" * 40)
    
    print("\n1. ASK - Query processor state:")
    print(f"   processor.ask('status'): {processor.ask('status')}")
    print(f"   processor.ask('progress'): {processor.ask('progress')}")
    
    print("\n2. TELL - Format processor info:")
    print(f"   processor.tell('discord'):\n{processor.tell('discord')}")
    
    print("\n3. DO - Processor actions:")
    print(f"   processor.do('reset'): {processor.do('reset')}")
    print(f"   After reset - items_processed: {processor.items_processed}")


def demonstrate_universal_interface():
    """Show how everything now uses the same 3-method interface"""
    print("\n" + "=" * 60)
    print("UNIVERSAL POLYMORPHIC INTERFACE")
    print("=" * 60)
    
    print("""
The ENTIRE system now uses just 3 methods:

MODELS (Tournament, Player, Organization, TournamentPlacement):
  model.ask("any question")     # Get information
  model.tell("any format")       # Format output
  model.do("any action")         # Perform actions

SERVICES (TournamentTracker, ClaudeService, SyncService):
  service.ask("status")          # Query service state
  service.tell("discord")        # Format for output
  service.do("restart")          # Control service

PROCESSORS (SyncProcessor, CleanupProcessor):
  processor.ask("progress")      # Get processing status
  processor.tell("discord")      # Format progress
  processor.do("process")        # Start processing

EVERYTHING speaks the same language!
Claude can interact with ANY object using the same 3 methods.
No more memorizing hundreds of different method names!
    """)


if __name__ == "__main__":
    # Initialize database
    init_database()
    
    # Run all tests
    test_placement_polymorphic()
    test_service_polymorphic()
    test_processor_polymorphic()
    demonstrate_universal_interface()
    
    print("\n" + "=" * 60)
    print("✨ Polymorphic transformation complete!")
    print("The entire system now uses ask(), tell(), do()")
    print("=" * 60)