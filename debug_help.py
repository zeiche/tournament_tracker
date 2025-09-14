#!/usr/bin/env python3
import sys
import os

# Direct copy of show_cached_help
def show_cached_help():
    """Show help using cached services without full discovery"""
    import argparse
    import json
    import os

    print("DEBUG: Checking cache file...")
    # Direct cache file read - no service imports
    cache_file = ".bonjour_services.json"
    if not os.path.exists(cache_file):
        print("DEBUG: Cache file not found!")
        return False
    print(f"DEBUG: Cache file exists: {cache_file}")

    try:
        with open(cache_file, 'r') as f:
            services = json.load(f)
        print(f"DEBUG: Loaded {len(services)} services from cache")
    except Exception as e:
        print(f"DEBUG: Error loading cache: {e}")
        return False

    return True

if __name__ == "__main__":
    result = show_cached_help()
    print(f"Result: {result}")