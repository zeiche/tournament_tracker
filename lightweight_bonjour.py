#!/usr/bin/env python3
"""
Lightweight Bonjour Intelligence - No LLM required!
Now uses the Interactive Bridge for consistent behavior
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bridges.interactive_bridge import InteractiveBridge

def main():
    """Run lightweight intelligence via the Interactive Bridge"""
    # Just use the bridge with lightweight backend
    bridge = InteractiveBridge(backend="lightweight")
    bridge.run_interactive()

if __name__ == "__main__":
    main()