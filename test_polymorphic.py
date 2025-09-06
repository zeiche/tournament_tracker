#!/usr/bin/env python3
"""
test_polymorphic.py - Test the 3-method polymorphic approach
Shows how much simpler the interface becomes.
"""
from database import get_session, init_database
from tournament_models_simplified import simplify_existing_models


def test_polymorphic_models():
    """
    Test the simplified 3-method approach.
    """
    print("=" * 60)
    print("Testing Polymorphic 3-Method Models")
    print("=" * 60)
    
    # Initialize and simplify
    init_database()
    simplify_existing_models()
    
    with get_session() as session:
        # Get a tournament
        from tournament_models import Tournament
        tournament = session.query(Tournament).first()
        
        if tournament:
            print("\n📊 Testing Tournament Polymorphic Methods:")
            print("-" * 40)
            
            # Test ask() - query anything
            print("\n1. ASK - Query anything:")
            print(f"   tournament.ask('winner'): {tournament.ask('winner', session)}")
            print(f"   tournament.ask('attendance'): {tournament.ask('attendance')}")
            print(f"   tournament.ask('top 3'): {tournament.ask('top 3', session)}")
            
            # Test tell() - format anything
            print("\n2. TELL - Format for any output:")
            print(f"   tournament.tell('brief'): {tournament.tell('brief')}")
            print(f"   tournament.tell('discord'):\n{tournament.tell('discord')}")
            
            # Test do() - perform any action
            print("\n3. DO - Perform any action:")
            print(f"   tournament.do('announce'): {tournament.do('announce')}")
            print(f"   tournament.do('calculate'): {tournament.do('calculate')}")
        
        # Get a player
        from tournament_models import Player
        player = session.query(Player).first()
        
        if player:
            print("\n\n🎮 Testing Player Polymorphic Methods:")
            print("-" * 40)
            
            print("\n1. ASK - Query anything:")
            print(f"   player.ask('wins'): {player.ask('wins', session)}")
            print(f"   player.ask('recent'): {player.ask('recent', session)}")
            print(f"   player.ask('statistics'): {player.ask('statistics')}")
            
            print("\n2. TELL - Format for any output:")
            print(f"   player.tell('discord'):\n{player.tell('discord')}")
            
            print("\n3. DO - Perform any action:")
            print(f"   player.do('announce'): {player.do('announce')}")
        
        # Get an organization
        from tournament_models import Organization
        org = session.query(Organization).first()
        
        if org:
            print("\n\n🏢 Testing Organization Polymorphic Methods:")
            print("-" * 40)
            
            print("\n1. ASK - Query anything:")
            print(f"   org.ask('total attendance'): {org.ask('total attendance')}")
            print(f"   org.ask('recent'): {org.ask('recent', session)}")
            
            print("\n2. TELL - Format for any output:")
            print(f"   org.tell('discord'):\n{org.tell('discord')}")
            
            print("\n3. DO - Perform any action:")
            print(f"   org.do('validate'): {org.do('validate')}")
    
    print("\n" + "=" * 60)
    print("COMPARISON:")
    print("-" * 60)
    print("OLD WAY (200+ methods):")
    print("  tournament.get_winner()")
    print("  tournament.get_top_8_placements()")
    print("  tournament.format_for_discord()")
    print("  tournament.calculate_statistics()")
    print("  tournament.sync_from_api()")
    print("  ... 195 more methods")
    
    print("\nNEW WAY (just 3 methods):")
    print("  tournament.ask('anything')")
    print("  tournament.tell('any format')")
    print("  tournament.do('any action')")
    
    print("\nThe object figures out what you want!")
    print("=" * 60)


def demonstrate_claude_interaction():
    """
    Show how Claude would interact with these simplified models.
    """
    print("\n" + "=" * 60)
    print("How Claude Uses Polymorphic Models")
    print("=" * 60)
    
    print("""
When Claude receives a model object, it can:

1. Ask for ANYTHING without knowing method names:
   result = tournament.ask("who won")
   result = player.ask("recent performance")
   result = org.ask("growth rate")

2. Get formatted output for ANY context:
   discord_msg = tournament.tell("discord")
   json_data = player.tell("json")
   explanation = org.tell("claude")

3. Trigger ANY action polymorphically:
   tournament.do("sync from api")
   player.do("recalculate stats")
   org.do("merge duplicates")

Claude doesn't need to know 200+ method names!
Just ask(), tell(), and do() - the objects handle the rest.
    """)


if __name__ == "__main__":
    test_polymorphic_models()
    demonstrate_claude_interaction()