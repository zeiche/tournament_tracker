#!/usr/bin/env python3
"""
simple_logger.py - Simple logger without circular dependencies
"""
import sys
from datetime import datetime
from typing import Any


def _log(level: str, message: str, **kwargs):
    """Simple logging function"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    caller = sys._getframe(2).f_globals.get('__name__', 'unknown')
    print(f"[{timestamp}] {level} {caller}: {message}")


def info(message: str, **kwargs):
    """Log info message"""
    _log('INFO', message, **kwargs)


def warning(message: str, **kwargs):
    """Log warning message"""
    _log('WARN', message, **kwargs)


def error(message: str, **kwargs):
    """Log error message"""
    _log('ERROR', message, **kwargs)


def debug(message: str, **kwargs):
    """Log debug message"""
    _log('DEBUG', message, **kwargs)