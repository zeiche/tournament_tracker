#!/usr/bin/env python3
"""
test_logger.py - Test the clean logger implementation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.simple_logger import info, warning, error, debug


def test_basic_logging():
    """Test basic logging functions"""
    print("🧪 Testing basic logging...")
    
    info("Test info message")
    warning("Test warning message")
    error("Test error message")
    debug("Test debug message")
    
    print("✅ Basic logging complete")


def test_simple_logger():
    """Test simple logger functions"""
    print("🧪 Testing simple logger...")
    
    info("This is an info message")
    warning("This is a warning message") 
    error("This is an error message")
    debug("This is a debug message")
    
    print("✅ Simple logger test complete")


if __name__ == "__main__":
    print("🚀 Starting logger tests...\n")
    
    test_basic_logging()
    print()
    
    test_simple_logger()
    print()
    
    print("🎉 All logger tests complete!")