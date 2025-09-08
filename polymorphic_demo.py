#!/usr/bin/env python3
"""
Demonstration of the ask/tell/do polymorphic pattern
Called via: ./go.py --demo-polymorphic
"""
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_pattern():
    """Demonstrate the ask/tell/do pattern with actual services"""
    print("\n" + "="*70)
    print(" ASK/TELL/DO PATTERN - All Services Use Just 3 Methods!")
    print("="*70)
    
    print("\nThe polymorphic pattern replaces 200+ methods with just 3:")
    print("  • ask(query)        - Get data using natural language")
    print("  • tell(format, data) - Format output")  
    print("  • do(action)        - Perform actions")
    
    # Demo with database service
    print("\n" + "-"*70)
    print(" DATABASE SERVICE DEMO")
    print("-"*70)
    
    try:
        from utils.database_service import database_service as db
        
        print("\n1. ASK for data (natural language queries):")
        print("   db.ask('stats')")
        stats = db.ask('stats')
        print(f"   → {stats}\n")
        
        print("   db.ask('top 3 organizations')")
        orgs = db.ask('top 3 organizations')
        if isinstance(orgs, list):
            for i, org in enumerate(orgs[:3], 1):
                print(f"   → {i}. {org.get('display_name', org)}")
        else:
            print(f"   → {orgs}")
        
        print("\n2. TELL to format (multiple output formats):")
        print("   db.tell('json', stats)")
        json_out = db.tell('json', stats)
        print(f"   → {json_out[:100]}...")
        
        print("\n   db.tell('discord', stats)")
        discord_out = db.tell('discord', stats)
        print(f"   → {discord_out[:100]}...")
        
        print("\n3. DO actions (natural language commands):")
        print("   db.do('validate data')")
        result = db.do('validate data')
        print(f"   → {result}")
        
    except Exception as e:
        print(f"   Database service not available: {e}")
    
    # Demo with tournament operations
    print("\n" + "-"*70)
    print(" TOURNAMENT OPERATIONS DEMO")
    print("-"*70)
    
    try:
        from utils.tournament_operations import tournament_operations as ops
        
        print("\n1. ASK for operation status:")
        print("   ops.ask('config status')")
        config = ops.ask('config status')
        print(f"   → {config}")
        
        print("\n2. TELL to format:")
        print("   ops.tell('summary', config)")
        summary = ops.tell('summary', config)
        print(f"   → {summary}")
        
        print("\n3. DO operation tracking:")
        print("   ops.do('track demo')")
        result = ops.do('track demo')
        print(f"   → {result}")
        
        print("   ops.do('record success tournaments=3', tracker='demo')")
        result = ops.do('record success tournaments=3', tracker='demo')
        print(f"   → {result}")
        
        print("   ops.do('end tracker demo')")
        result = ops.do('end tracker demo')
        print(f"   → {result}")
        
    except Exception as e:
        print(f"   Operations service not available: {e}")
    
    # Show the power of consistency
    print("\n" + "-"*70)
    print(" THE POWER OF CONSISTENCY")
    print("-"*70)
    
    print("\nEVERY service works the SAME way:")
    print("  • No need to memorize different APIs")
    print("  • Natural language replaces method names")
    print("  • Services figure out what you want")
    print("  • 200+ methods → just 3!")
    
    print("\nBefore (traditional OOP):")
    print("  tournament.get_winner()")
    print("  tournament.get_top_8_placements()")
    print("  tournament.calculate_growth_rate()")
    print("  tournament.format_for_discord()")
    print("  ... 195 more methods to remember!")
    
    print("\nNow (polymorphic pattern):")
    print("  tournament.ask('who won')")
    print("  tournament.ask('top 8')")
    print("  tournament.ask('growth rate')")
    print("  tournament.tell('discord', data)")
    print("  ... that's it!")
    
    print("\n" + "="*70)
    print(" SUMMARY")
    print("="*70)
    
    print("\n✅ Simplification: 200+ methods → 3 methods")
    print("✅ Natural language: No API documentation needed")
    print("✅ Consistency: Every service works the same")
    print("✅ Intelligence: Services figure out intent")
    
    print("\nThe ask/tell/do pattern is the ULTIMATE simplification!")


def main():
    """Main entry point"""
    # Check if called via go.py
    if not os.environ.get('GO_PY_AUTHORIZED'):
        print("ERROR: This script must be run through go.py")
        print("Usage: ./go.py --demo-polymorphic")
        sys.exit(1)
    
    try:
        demo_pattern()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted")
    except Exception as e:
        print(f"\nError running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()