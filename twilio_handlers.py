#!/usr/bin/env python3
"""
twilio_handlers.py - Register handlers for Twilio messages
Like Discord handlers - anyone can register to process calls/SMS
"""

# Global handler lists
sms_handlers = []
call_handlers = []

def register_sms_handler(handler):
    """Register an SMS handler"""
    sms_handlers.append(handler)
    print(f"Registered SMS handler: {handler.__name__}")

def register_call_handler(handler):
    """Register a call handler"""
    call_handlers.append(handler)
    print(f"Registered call handler: {handler.__name__}")

# Example handlers
def echo_sms(from_number, body):
    """Simple echo handler for SMS"""
    return f"Echo: {body}"

def greeting_call(from_number):
    """Simple greeting for calls"""
    return "Hello! This is tournament tracker. Text me for help."

# Register default handlers
register_sms_handler(echo_sms)
register_call_handler(greeting_call)