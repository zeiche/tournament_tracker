#!/usr/bin/env python3
"""
polymorphic_async.py - Bonjour async service that provides async to anyone
Any service can discover and use async capabilities without importing asyncio
"""

import asyncio
from typing import Any, Callable, Coroutine, Optional
from capability_announcer import announcer
from capability_discovery import register_capability

class PolymorphicAsync:
    """Async service that provides async capabilities to any service"""
    
    _instance = None
    _loop = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce capabilities
        announcer.announce(
            "PolymorphicAsync",
            [
                "I provide async capabilities to ANY service",
                "I manage event loops polymorphically",
                "I run coroutines for services that need async",
                "I handle async tasks without you importing asyncio",
                "Methods: run(coroutine), create_task(coroutine), gather(*coroutines)",
                "I figure out the event loop for you"
            ]
        )
        
        self.tasks = []
        
    def get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop polymorphically"""
        try:
            # Try to get running loop
            loop = asyncio.get_running_loop()
            announcer.announce("PolymorphicAsync", ["Using existing event loop"])
            return loop
        except RuntimeError:
            # No loop running, try to get the current loop
            loop = asyncio.get_event_loop()
            if loop is None:
                # Create new loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                announcer.announce("PolymorphicAsync", ["Created new event loop"])
            return loop
    
    def run(self, coroutine: Coroutine) -> Any:
        """Run a coroutine polymorphically - figures out how to run it"""
        try:
            # If already in async context, just await it
            loop = asyncio.get_running_loop()
            # We're in async context, create task
            return asyncio.create_task(coroutine)
        except RuntimeError:
            # Not in async context, run it
            loop = self.get_loop()
            announcer.announce(
                "ASYNC_RUN",
                ["Running coroutine in sync context"]
            )
            return loop.run_until_complete(coroutine)
    
    def create_task(self, coroutine: Coroutine) -> asyncio.Task:
        """Create an async task polymorphically"""
        try:
            # Try to create task in running loop
            task = asyncio.create_task(coroutine)
            self.tasks.append(task)
            announcer.announce(
                "ASYNC_TASK_CREATED",
                [f"Task created: {task.get_name()}"]
            )
            return task
        except RuntimeError:
            # No running loop, schedule it
            loop = self.get_loop()
            task = loop.create_task(coroutine)
            self.tasks.append(task)
            announcer.announce(
                "ASYNC_TASK_SCHEDULED",
                [f"Task scheduled: {task.get_name()}"]
            )
            return task
    
    def gather(self, *coroutines) -> Any:
        """Gather multiple coroutines polymorphically"""
        announcer.announce(
            "ASYNC_GATHER",
            [f"Gathering {len(coroutines)} coroutines"]
        )
        
        try:
            # In async context
            return asyncio.gather(*coroutines)
        except RuntimeError:
            # In sync context
            loop = self.get_loop()
            return loop.run_until_complete(asyncio.gather(*coroutines))
    
    def sleep(self, seconds: float):
        """Async sleep that works in any context"""
        try:
            # In async context
            return asyncio.sleep(seconds)
        except RuntimeError:
            # In sync context - just use regular sleep
            import time
            time.sleep(seconds)
    
    def call_soon(self, callback: Callable, *args):
        """Schedule a callback to run soon"""
        loop = self.get_loop()
        loop.call_soon(callback, *args)
        announcer.announce(
            "ASYNC_CALLBACK_SCHEDULED",
            [f"Callback {callback.__name__} scheduled"]
        )
    
    def call_later(self, delay: float, callback: Callable, *args):
        """Schedule a callback to run after delay"""
        loop = self.get_loop()
        loop.call_later(delay, callback, *args)
        announcer.announce(
            "ASYNC_DELAYED_CALLBACK",
            [f"Callback {callback.__name__} scheduled in {delay}s"]
        )
    
    def run_in_executor(self, func: Callable, *args) -> Any:
        """Run blocking function in executor"""
        loop = self.get_loop()
        announcer.announce(
            "ASYNC_EXECUTOR",
            [f"Running {func.__name__} in executor"]
        )
        
        try:
            # If in async context, return future
            return loop.run_in_executor(None, func, *args)
        except RuntimeError:
            # In sync context, run and wait
            future = loop.run_in_executor(None, func, *args)
            return loop.run_until_complete(future)
    
    def wait_for(self, coroutine: Coroutine, timeout: float) -> Any:
        """Wait for coroutine with timeout"""
        announcer.announce(
            "ASYNC_WAIT_FOR",
            [f"Waiting for coroutine with {timeout}s timeout"]
        )
        
        try:
            return asyncio.wait_for(coroutine, timeout)
        except RuntimeError:
            loop = self.get_loop()
            return loop.run_until_complete(
                asyncio.wait_for(coroutine, timeout)
            )
    
    def ensure_future(self, coroutine_or_future):
        """Ensure something is a future"""
        return asyncio.ensure_future(coroutine_or_future, loop=self.get_loop())
    
    def is_async_context(self) -> bool:
        """Check if we're in async context"""
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    
    def get_all_tasks(self) -> list:
        """Get all async tasks"""
        return self.tasks
    
    def cancel_all_tasks(self):
        """Cancel all pending tasks"""
        cancelled = 0
        for task in self.tasks:
            if not task.done():
                task.cancel()
                cancelled += 1
        
        announcer.announce(
            "ASYNC_TASKS_CANCELLED",
            [f"Cancelled {cancelled} tasks"]
        )

# Global instance
_async_service = PolymorphicAsync()

def get_async_service():
    """Get the global async service"""
    return _async_service

# Register with capability discovery
try:
    register_capability("async", get_async_service)
    announcer.announce("PolymorphicAsync", ["Registered as discoverable capability"])
except ImportError:
    pass

# Convenience function for other services
def async_run(coroutine):
    """Run a coroutine using the async service"""
    return _async_service.run(coroutine)

def async_task(coroutine):
    """Create a task using the async service"""
    return _async_service.create_task(coroutine)