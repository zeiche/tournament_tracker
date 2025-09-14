#!/usr/bin/env python3
"""
Test script to deliberately crash and verify crash monitoring works
"""
import time
import sys

def crash_test():
    print("Starting crash test in 2 seconds...")
    time.sleep(2)
    print("About to crash...")

    # Force a crash
    raise ValueError("DELIBERATE CRASH FOR TESTING - This should be captured by crash monitoring!")

if __name__ == "__main__":
    crash_test()