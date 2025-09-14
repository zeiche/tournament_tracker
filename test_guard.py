#!/usr/bin/env python3
"""Test execution guard"""

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core.execution_guard import require_go_py
require_go_py("test_guard")

print("ERROR: This should never print - guard failed!")