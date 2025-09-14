#!/usr/bin/env python3
"""
bonjour_monitor.py - Real-time announcement monitor and debugger
Shows all Bonjour-style announcements happening in the system.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.bonjour_monitor")

import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque, Counter
from polymorphic_core import announcer
import threading
import queue


class BonjourMonitor:
    """
    Monitor that listens to all announcements and provides various views.
    """
    
    def __init__(self, max_history: int = 1000):
        self.history = deque(maxlen=max_history)
        self.service_stats = Counter()
        self.start_time = datetime.now()
        self.announcement_queue = queue.Queue()
        self.running = False
        
        # Register as a listener
        announcer.add_listener(self._on_announcement)
        
        # Announce ourselves!
        announcer.announce(
            "Bonjour Monitor",
            [
                "Monitoring all system announcements",
                "Tracking service statistics",
                "Providing real-time debugging",
                f"Keeping last {max_history} announcements"
            ]
        )
    
    def _on_announcement(self, service_name: str, capabilities: List[str], examples: Optional[List[str]] = None):
        """Called whenever any service makes an announcement"""
        announcement = {
            'timestamp': datetime.now().isoformat(),
            'service': service_name,
            'capabilities': capabilities,
            'examples': examples or []
        }
        
        # Add to history
        self.history.append(announcement)
        
        # Update stats
        self.service_stats[service_name] += 1
        
        # Queue for real-time display
        if self.running:
            self.announcement_queue.put(announcement)
    
    def start_live_monitor(self):
        """Start live monitoring in the console"""
        self.running = True
        print("\n" + "="*80)
        print("🔊 BONJOUR MONITOR - Live Announcements")
        print("="*80)
        print(f"Started at: {datetime.now()}")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                try:
                    # Wait for announcements with timeout
                    announcement = self.announcement_queue.get(timeout=1)
                    self._display_announcement(announcement)
                except queue.Empty:
                    continue
                except KeyboardInterrupt:
                    break
        finally:
            self.stop()
    
    def _display_announcement(self, announcement: Dict[str, Any]):
        """Display a single announcement nicely"""
        timestamp = announcement['timestamp'].split('T')[1].split('.')[0]  # Just time
        service = announcement['service']
        
        # Color codes for terminal
        CYAN = '\033[96m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RESET = '\033[0m'
        
        print(f"\n{CYAN}[{timestamp}]{RESET} {GREEN}{service}{RESET}")
        
        for capability in announcement['capabilities']:
            print(f"  • {capability}")
        
        if announcement['examples']:
            print(f"  {YELLOW}Examples:{RESET}")
            for example in announcement['examples']:
                print(f"    - {example}")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        print("\n" + "="*80)
        print("Monitor stopped")
        self.show_summary()
    
    def show_summary(self):
        """Show summary statistics"""
        runtime = datetime.now() - self.start_time
        total_announcements = sum(self.service_stats.values())
        
        print("\n📊 ANNOUNCEMENT SUMMARY")
        print("-"*40)
        print(f"Runtime: {runtime}")
        print(f"Total announcements: {total_announcements}")
        print(f"Unique services: {len(self.service_stats)}")
        
        if self.service_stats:
            print("\nTop Services:")
            for service, count in self.service_stats.most_common(10):
                print(f"  {service}: {count} announcements")
    
    def get_recent(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get the N most recent announcements"""
        return list(self.history)[-n:]
    
    def get_by_service(self, service_name: str) -> List[Dict[str, Any]]:
        """Get all announcements from a specific service"""
        return [a for a in self.history if a['service'] == service_name]
    
    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """Search announcements for a keyword"""
        keyword_lower = keyword.lower()
        results = []
        
        for announcement in self.history:
            # Check service name
            if keyword_lower in announcement['service'].lower():
                results.append(announcement)
                continue
            
            # Check capabilities
            for cap in announcement['capabilities']:
                if keyword_lower in cap.lower():
                    results.append(announcement)
                    break
        
        return results
    
    def export_to_file(self, filename: str = "announcements.json"):
        """Export announcement history to a file"""
        data = {
            'start_time': self.start_time.isoformat(),
            'export_time': datetime.now().isoformat(),
            'total_announcements': sum(self.service_stats.values()),
            'service_stats': dict(self.service_stats),
            'history': list(self.history)
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Exported {len(self.history)} announcements to {filename}")
    
    def replay(self, delay: float = 0.5):
        """Replay all announcements with a delay"""
        print("\n🔄 REPLAYING ANNOUNCEMENTS")
        print("-"*40)
        
        for announcement in self.history:
            self._display_announcement(announcement)
            time.sleep(delay)
        
        print("\n✅ Replay complete")


class BonjourDebugger:
    """
    Advanced debugger for tracking announcement flows.
    """
    
    def __init__(self):
        self.flows = []  # Track related announcements
        self.current_flow = None
        self.monitor = BonjourMonitor()
    
    def start_flow(self, name: str):
        """Start tracking a new flow of announcements"""
        self.current_flow = {
            'name': name,
            'start_time': datetime.now(),
            'announcements': []
        }
        print(f"🔍 Tracking flow: {name}")
    
    def end_flow(self):
        """End the current flow and analyze it"""
        if not self.current_flow:
            return
        
        self.current_flow['end_time'] = datetime.now()
        duration = (self.current_flow['end_time'] - self.current_flow['start_time']).total_seconds()
        
        print(f"\n📈 Flow Analysis: {self.current_flow['name']}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Announcements: {len(self.current_flow['announcements'])}")
        
        # Find the services involved
        services = set()
        for ann in self.current_flow['announcements']:
            services.add(ann['service'])
        
        print(f"Services involved: {', '.join(services)}")
        
        self.flows.append(self.current_flow)
        self.current_flow = None
    
    def trace_operation(self, operation_name: str, func, *args, **kwargs):
        """Trace all announcements during an operation"""
        self.start_flow(operation_name)
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            self.end_flow()


def main():
    """Run the monitor as a standalone program"""
    monitor = BonjourMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "live":
            monitor.start_live_monitor()
        elif command == "summary":
            # Wait a bit to collect announcements
            time.sleep(2)
            monitor.show_summary()
        elif command == "export":
            filename = sys.argv[2] if len(sys.argv) > 2 else "announcements.json"
            monitor.export_to_file(filename)
        elif command == "replay":
            monitor.replay()
        else:
            print(f"Unknown command: {command}")
            print("Usage: bonjour_monitor.py [live|summary|export|replay]")
    else:
        # Default to live monitoring
        monitor.start_live_monitor()


if __name__ == "__main__":
    main()