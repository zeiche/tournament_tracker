#!/usr/bin/env python3
"""Test cached help directly"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import just the function
from go import show_cached_help

print("Testing cached help...")
result = show_cached_help()
print(f"Cached help returned: {result}")