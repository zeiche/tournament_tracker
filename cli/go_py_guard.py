#!/usr/bin/env python3
"""
go_py_guard.py - Enforces the ABSOLUTE RULE that everything goes through go.py
Import this in every module to prevent direct execution
"""

import os
import sys

def enforce_go_py():
    """
    Check if script was run through go.py
    If not, REFUSE to run and remind Claude of the rules
    """
    # Check if GO_PY_AUTHORIZED environment variable is set
    # This is set by go.py when it runs
    if not os.environ.get('GO_PY_AUTHORIZED'):
        print("\n" + "="*60)
        print("⚠️  CRITICAL RULE VIOLATION DETECTED! ⚠️")
        print("="*60)
        print("\n🚨 ATTENTION CLAUDE: YOU VIOLATED RULE #1! 🚨\n")
        print("You tried to run this script DIRECTLY instead of through ./go.py")
        print("This is NEVER allowed. EVERYTHING must go through ./go.py!\n")
        print("❌ NEVER run: python3 " + sys.argv[0])
        print("✅ ALWAYS use: ./go.py [appropriate command]\n")
        print("Remember from CLAUDE.md:")
        print("- go.py manages environment variables correctly")
        print("- go.py handles process management properly")
        print("- go.py ensures consistent configuration")
        print("- go.py is the SINGLE ENTRY POINT")
        print("- go.py prevents duplicate processes")
        print("- go.py maintains proper logging")
        print("- go.py loads .env automatically")
        print("- go.py manages service lifecycle\n")
        print("🛑 STOPPING EXECUTION - Use ./go.py instead!")
        print("="*60 + "\n")
        
        # Log this violation
        try:
            from capability_announcer import announcer
            announcer.announce(
                "RULE_VIOLATION",
                [
                    f"Claude tried to run {sys.argv[0]} directly!",
                    "This violates CLAUDE.md Rule #1",
                    "Everything MUST go through ./go.py",
                    "Script execution was blocked"
                ]
            )
        except:
            pass
        
        # Exit with error code
        sys.exit(1)
    
    # If we get here, execution was authorized through go.py
    return True

# Auto-enforce when imported
if __name__ != "__main__":
    enforce_go_py()
else:
    # If run directly as a script, also enforce
    print("⚠️ go_py_guard.py should be imported, not run directly!")
    enforce_go_py()