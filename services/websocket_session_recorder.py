#!/usr/bin/env python3
"""
WebSocket Session Recorder - Provides detailed logging and "recordings" of websocket sessions
to prove functionality and capture exact behavior with timestamps and data.
"""

import json
import time
import datetime
import websocket
import threading
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.websocket_session_recorder")

from logging_services.polymorphic_log_manager import get_log_manager

class WebSocketSessionRecorder:
    """Records websocket sessions with detailed timestamps, messages, and connection events"""
    
    def __init__(self, session_name: str = None):
        self.session_name = session_name or f"ws_session_{int(time.time())}"
        self.recording = {
            "session_info": {
                "name": self.session_name,
                "start_time": None,
                "end_time": None,
                "duration_seconds": 0,
                "url": None,
                "protocol": None,
                "success": False,
                "total_messages": 0,
                "connection_attempts": 0
            },
            "events": [],
            "messages": [],
            "errors": [],
            "connection_health": {
                "successful_connections": 0,
                "connection_drops": 0,
                "reconnection_attempts": 0,
                "average_message_interval": 0
            }
        }
        self.start_time = None
        self.last_message_time = None
        self.message_intervals = []
        self.ws = None
        self.log_manager = get_log_manager()
        
    def _add_event(self, event_type: str, description: str, data: Any = None):
        """Add timestamped event to recording"""
        timestamp = time.time()
        readable_time = datetime.datetime.fromtimestamp(timestamp).isoformat()
        
        event = {
            "timestamp": timestamp,
            "readable_time": readable_time,
            "event_type": event_type,
            "description": description,
            "data": data
        }
        self.recording["events"].append(event)
        print(f"[{readable_time}] {event_type}: {description}")
        
        # Log to database
        self.log_manager.info(
            message=f"WebSocket {event_type}: {description}",
            data={
                "session_name": self.session_name,
                "event_type": event_type,
                "event_data": data,
                "timestamp": timestamp,
                "readable_time": readable_time
            },
            source="websocket_recorder"
        )
        
    def _add_message(self, direction: str, message: Any, message_type: str = "unknown"):
        """Add message to recording with analysis"""
        timestamp = time.time()
        readable_time = datetime.datetime.fromtimestamp(timestamp).isoformat()
        
        # Calculate interval since last message
        interval = None
        if self.last_message_time:
            interval = timestamp - self.last_message_time
            self.message_intervals.append(interval)
        self.last_message_time = timestamp
        
        # Try to parse message content
        parsed_content = None
        try:
            if isinstance(message, str):
                parsed_content = json.loads(message)
        except:
            parsed_content = str(message)[:200]  # Truncate long messages
            
        message_record = {
            "timestamp": timestamp,
            "readable_time": readable_time,
            "direction": direction,  # "sent" or "received"
            "message_type": message_type,
            "content": parsed_content,
            "raw_content": str(message)[:500],  # Keep some raw content
            "size_bytes": len(str(message)),
            "interval_since_last": interval
        }
        
        self.recording["messages"].append(message_record)
        self.recording["session_info"]["total_messages"] += 1
        
        # Log message to database
        self.log_manager.info(
            message=f"WebSocket message {direction}: {message_type}",
            data={
                "session_name": self.session_name,
                "direction": direction,
                "message_type": message_type,
                "content": parsed_content,
                "size_bytes": len(str(message)),
                "interval_since_last": interval,
                "timestamp": timestamp,
                "readable_time": readable_time
            },
            source="websocket_recorder"
        )
        
        # Extract message info for display
        if parsed_content and isinstance(parsed_content, dict):
            if parsed_content.get('type') == 'new_log':
                msg_text = parsed_content.get('data', {}).get('message', '')
                if 'Live update #' in msg_text:
                    update_num = msg_text.split('#')[1].split(' ')[0]
                    print(f"[{readable_time}] RECEIVED: Live update #{update_num}")
                else:
                    print(f"[{readable_time}] RECEIVED: Log message")
            elif parsed_content.get('type') == 'logs':
                count = len(parsed_content.get('data', []))
                print(f"[{readable_time}] RECEIVED: Initial logs ({count} entries)")
            else:
                print(f"[{readable_time}] RECEIVED: {message_type} message")
        else:
            print(f"[{readable_time}] RECEIVED: Raw message ({len(str(message))} bytes)")
    
    def _add_error(self, error_type: str, error_message: str, error_data: Any = None):
        """Add error to recording"""
        timestamp = time.time()
        readable_time = datetime.datetime.fromtimestamp(timestamp).isoformat()
        
        error_record = {
            "timestamp": timestamp,
            "readable_time": readable_time,
            "error_type": error_type,
            "error_message": str(error_message),
            "error_data": error_data
        }
        self.recording["errors"].append(error_record)
        print(f"[{readable_time}] ERROR: {error_type} - {error_message}")
        
        # Log error to database
        self.log_manager.error(
            message=f"WebSocket error: {error_type} - {error_message}",
            data={
                "session_name": self.session_name,
                "error_type": error_type,
                "error_data": error_data,
                "timestamp": timestamp,
                "readable_time": readable_time
            },
            source="websocket_recorder"
        )
    
    def on_open(self, ws):
        """WebSocket opened"""
        self._add_event("connection_opened", "WebSocket connection successfully opened")
        self.recording["connection_health"]["successful_connections"] += 1
        
    def on_message(self, ws, message):
        """WebSocket message received"""
        self._add_message("received", message, "websocket_data")
        
    def on_error(self, ws, error):
        """WebSocket error"""
        self._add_error("websocket_error", str(error), {"error_object": str(error)})
        
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket closed"""
        self._add_event("connection_closed", f"WebSocket closed with code {close_status_code}: {close_msg}",
                       {"close_code": close_status_code, "close_message": close_msg})
        self.recording["connection_health"]["connection_drops"] += 1
        
    def record_session(self, url: str, duration_seconds: int = 30) -> Dict[str, Any]:
        """Record a websocket session for specified duration"""
        print(f"🎬 Starting WebSocket session recording")
        print(f"📡 URL: {url}")
        print(f"⏱️  Duration: {duration_seconds} seconds")
        print(f"📋 Session: {self.session_name}")
        print("=" * 80)
        
        self.start_time = time.time()
        self.recording["session_info"]["start_time"] = self.start_time
        self.recording["session_info"]["url"] = url
        self.recording["session_info"]["protocol"] = "wss" if url.startswith("wss:") else "ws"
        
        self._add_event("session_started", f"Beginning recording session for {duration_seconds}s")
        
        # Create WebSocket connection
        self.recording["session_info"]["connection_attempts"] += 1
        self._add_event("connection_attempt", f"Attempting to connect to {url}")
        
        self.ws = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # Set up timeout
        def timeout_handler():
            time.sleep(duration_seconds)
            if self.ws:
                self._add_event("session_timeout", f"Recording duration ({duration_seconds}s) completed, closing connection")
                self.ws.close()
        
        timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
        timeout_thread.start()
        
        # Run WebSocket
        try:
            self.ws.run_forever()
        except Exception as e:
            self._add_error("session_exception", str(e))
        
        # Finalize recording
        end_time = time.time()
        self.recording["session_info"]["end_time"] = end_time
        self.recording["session_info"]["duration_seconds"] = end_time - self.start_time
        
        # Calculate statistics
        if self.message_intervals:
            self.recording["connection_health"]["average_message_interval"] = sum(self.message_intervals) / len(self.message_intervals)
        
        # Determine success
        success_criteria = (
            self.recording["session_info"]["total_messages"] > 0 and
            self.recording["connection_health"]["successful_connections"] > 0 and
            len(self.recording["errors"]) == 0
        )
        self.recording["session_info"]["success"] = success_criteria
        
        print("=" * 80)
        print(f"🎬 Recording completed!")
        self._print_summary()
        
        # Log final session summary to database
        self.log_manager.info(
            message=f"WebSocket session completed: {self.session_name}",
            data={
                "session_name": self.session_name,
                "session_info": self.recording["session_info"],
                "connection_health": self.recording["connection_health"],
                "event_count": len(self.recording["events"]),
                "message_count": len(self.recording["messages"]),
                "error_count": len(self.recording["errors"]),
                "success": self.recording["session_info"]["success"]
            },
            source="websocket_recorder"
        )
        
        return self.recording
    
    def _print_summary(self):
        """Print session summary"""
        info = self.recording["session_info"]
        health = self.recording["connection_health"]
        
        print(f"📊 SESSION SUMMARY:")
        print(f"   ⏱️  Duration: {info['duration_seconds']:.1f} seconds")
        print(f"   📨 Messages: {info['total_messages']}")
        print(f"   🔗 Connections: {health['successful_connections']}")
        print(f"   ❌ Errors: {len(self.recording['errors'])}")
        print(f"   📈 Success: {'✅ YES' if info['success'] else '❌ NO'}")
        
        if health['average_message_interval'] > 0:
            print(f"   📊 Avg Message Interval: {health['average_message_interval']:.1f}s")
        
    def save_recording(self, filename: str = None) -> str:
        """Save recording to JSON file"""
        if not filename:
            filename = f"recordings/{self.session_name}.json"
            
        # Create recordings directory
        Path("recordings").mkdir(exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.recording, f, indent=2)
            
        print(f"💾 Recording saved to: {filename}")
        return filename
        
    def generate_proof_report(self) -> str:
        """Generate a human-readable proof report"""
        info = self.recording["session_info"]
        health = self.recording["connection_health"]
        
        report = f"""
🎬 WEBSOCKET SESSION PROOF REPORT
{'=' * 50}

Session: {info['name']}
URL: {info['url']}
Protocol: {info['protocol'].upper()}
Start Time: {datetime.datetime.fromtimestamp(info['start_time']).isoformat()}
Duration: {info['duration_seconds']:.1f} seconds

RESULTS:
✅ Connection Success: {'YES' if health['successful_connections'] > 0 else 'NO'}
📨 Messages Received: {info['total_messages']}
🔗 Connection Stability: {'STABLE' if health['connection_drops'] <= 1 else 'UNSTABLE'}
❌ Errors: {len(self.recording['errors'])}

DETAILED TIMELINE:
"""
        # Add key events
        for event in self.recording["events"][:10]:  # Show first 10 events
            report += f"{event['readable_time']}: {event['description']}\n"
        
        # Add message samples
        if self.recording["messages"]:
            report += f"\nMESSAGE SAMPLES:\n"
            for msg in self.recording["messages"][:5]:  # Show first 5 messages
                report += f"{msg['readable_time']}: {msg['direction']} - {msg['message_type']}\n"
        
        report += f"\nOVERALL RESULT: {'🎉 SUCCESS - WebSocket working as claimed' if info['success'] else '❌ FAILURE - WebSocket not working'}\n"
        
        return report

def main():
    """Test the recorder"""
    if len(sys.argv) > 1:
        url = sys.argv[1]
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    else:
        url = "wss://vpn.zilogo.com:8081/ws/logs"
        duration = 30
    
    recorder = WebSocketSessionRecorder(f"proof_test_{int(time.time())}")
    recording = recorder.record_session(url, duration)
    
    # Save recording
    filename = recorder.save_recording()
    
    # Generate proof report
    report = recorder.generate_proof_report()
    report_filename = filename.replace('.json', '_report.txt')
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"📄 Proof report saved to: {report_filename}")
    print("\n" + report)

if __name__ == "__main__":
    import sys
    main()