#!/usr/bin/env python3
"""
test_self_call.py - Call ourselves with a timer for debugging
Announces via Bonjour and automatically hangs up after timeout
"""

import time
import threading
from twilio.rest import Client
import os
from capability_announcer import announcer

class SelfCallTester:
    """Test calling ourselves with automatic hangup"""
    
    def __init__(self):
        # Load Twilio credentials
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+18788794283')
        
        # Load from .env if not in environment
        if not self.account_sid or not self.auth_token:
            env_file = '.env'
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if 'TWILIO_ACCOUNT_SID=' in line:
                            self.account_sid = line.split('=', 1)[1].strip().strip('"')
                        elif 'TWILIO_AUTH_TOKEN=' in line:
                            self.auth_token = line.split('=', 1)[1].strip().strip('"')
        
        self.client = Client(self.account_sid, self.auth_token)
        self.active_call_sid = None
        
        # Announce ourselves
        announcer.announce(
            "SelfCallTester",
            [
                "I test calls to ourselves with automatic hangup",
                f"Phone: {self.phone_number}",
                "Methods: make_self_call(duration), hang_up()",
                "I provide timing services for debugging"
            ]
        )
    
    def make_self_call(self, duration_seconds=30, message="Hello, this is a test call to myself"):
        """
        Make a call to our own number with automatic hangup
        
        Args:
            duration_seconds: How long before hanging up (default 30s)
            message: Message to play on the call
        """
        try:
            # Announce the call
            announcer.announce(
                "SELF_CALL_START",
                [
                    f"📞 Calling myself: {self.phone_number}",
                    f"⏱️ Will hang up after {duration_seconds} seconds",
                    f"Message: {message[:50]}..."
                ]
            )
            
            # Make the call
            call = self.client.calls.create(
                to=self.phone_number,
                from_=self.phone_number,
                url=f'http://64.111.98.139:8082/outbound_message?message={message}'
            )
            
            self.active_call_sid = call.sid
            
            announcer.announce(
                "CALL_INITIATED",
                [
                    f"Call SID: {call.sid}",
                    f"Status: {call.status}",
                    f"Timer started: {duration_seconds}s"
                ]
            )
            
            # Start timer for automatic hangup
            timer = threading.Timer(duration_seconds, self.hang_up)
            timer.start()
            
            # Monitor call status
            self.monitor_call(duration_seconds)
            
            return call.sid
            
        except Exception as e:
            announcer.announce(
                "SELF_CALL_ERROR",
                [f"Failed to call self: {e}"]
            )
            return None
    
    def monitor_call(self, max_duration):
        """Monitor the call status with periodic announcements"""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_duration:
            try:
                if self.active_call_sid:
                    call = self.client.calls(self.active_call_sid).fetch()
                    
                    if call.status != last_status:
                        elapsed = int(time.time() - start_time)
                        announcer.announce(
                            "CALL_STATUS",
                            [
                                f"⏱️ Time: {elapsed}s / {max_duration}s",
                                f"Status: {call.status}",
                                f"Duration: {call.duration}s" if call.duration else "In progress"
                            ]
                        )
                        last_status = call.status
                    
                    # If call ended naturally, stop monitoring
                    if call.status in ['completed', 'failed', 'busy', 'no-answer']:
                        announcer.announce(
                            "CALL_ENDED",
                            [f"Call ended with status: {call.status}"]
                        )
                        break
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                announcer.announce("MONITOR_ERROR", [f"Error monitoring: {e}"])
                break
    
    def hang_up(self):
        """Hang up the active call"""
        if self.active_call_sid:
            try:
                call = self.client.calls(self.active_call_sid).update(status='completed')
                announcer.announce(
                    "CALL_HANGUP",
                    [
                        "☎️ Call terminated by timer",
                        f"Final status: {call.status}",
                        f"Duration: {call.duration}s" if call.duration else "Unknown"
                    ]
                )
                self.active_call_sid = None
            except Exception as e:
                announcer.announce("HANGUP_ERROR", [f"Error hanging up: {e}"])

if __name__ == "__main__":
    import sys
    
    # Get duration from command line (default 30 seconds)
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    
    # Get message from command line
    message = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Testing audio mixing. The background music should be playing."
    
    print(f"\n🔬 Self-Call Test")
    print("=" * 50)
    print(f"📞 Calling: {os.getenv('TWILIO_PHONE_NUMBER', '+18788794283')}")
    print(f"⏱️ Duration: {duration} seconds")
    print(f"💬 Message: {message}")
    print("=" * 50)
    
    tester = SelfCallTester()
    call_sid = tester.make_self_call(duration, message)
    
    if call_sid:
        print(f"\n✅ Test complete - Call SID: {call_sid}")
    else:
        print("\n❌ Test failed")