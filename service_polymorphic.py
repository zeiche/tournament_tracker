#!/usr/bin/env python3
"""
service_polymorphic.py - Extend service classes with the 3-method pattern
Makes services self-aware and intelligent like models
"""
from typing import Any, Optional, Dict, List, Union
from polymorphic_model import PolymorphicModel
from capability_announcer import announcer


class ServicePolymorphic(PolymorphicModel):
    """
    Base polymorphic service class.
    Services can now answer questions, format themselves, and perform actions.
    """
    
    def _ask_status(self) -> str:
        """Get service status"""
        if hasattr(self, 'is_running') and callable(self.is_running):
            return "running" if self.is_running() else "stopped"
        return "unknown"
    
    def _ask_enabled(self) -> bool:
        """Check if service is enabled"""
        if hasattr(self, 'is_enabled'):
            return self.is_enabled if not callable(self.is_enabled) else self.is_enabled()
        return False
    
    def _ask_statistics(self) -> Dict:
        """Get service statistics"""
        stats = {}
        
        # Common service attributes
        if hasattr(self, 'request_count'):
            stats['requests'] = self.request_count
        if hasattr(self, 'error_count'):
            stats['errors'] = self.error_count
        if hasattr(self, 'last_run'):
            stats['last_run'] = self.last_run
        if hasattr(self, 'uptime'):
            stats['uptime'] = self.uptime
        
        # Try to call get_statistics if available
        if hasattr(self, 'get_statistics') and callable(self.get_statistics):
            try:
                stats.update(self.get_statistics())
            except:
                pass
        
        return stats
    
    def _tell_discord(self) -> str:
        """Format service status for Discord"""
        status = self._ask_status()
        enabled = self._ask_enabled()
        
        status_emoji = "✅" if status == "running" else "❌"
        enabled_text = "Enabled" if enabled else "Disabled"
        
        output = f"**{self.__class__.__name__}**\n"
        output += f"{status_emoji} Status: {status.upper()}\n"
        output += f"🔧 {enabled_text}"
        
        stats = self._ask_statistics()
        if stats:
            output += f"\n📊 Stats: {len(stats)} metrics available"
        
        return output
    
    def _tell_claude(self) -> Dict:
        """Explain service to Claude"""
        return {
            'type': 'Service',
            'name': self.__class__.__name__,
            'status': self._ask_status(),
            'enabled': self._ask_enabled(),
            'capabilities': [
                'ask("status") - Get service status',
                'ask("statistics") - Get service metrics',
                'tell("discord") - Format for Discord',
                'do("restart") - Restart service',
                'do("stop") - Stop service'
            ],
            'current_stats': self._ask_statistics()
        }
    
    def _do_restart(self, **kwargs) -> bool:
        """Restart the service"""
        if hasattr(self, 'restart') and callable(self.restart):
            return self.restart()
        
        # Try stop then start
        if hasattr(self, 'stop') and hasattr(self, 'start'):
            self.stop()
            return self.start()
        
        return False
    
    def _do_stop(self, **kwargs) -> bool:
        """Stop the service"""
        if hasattr(self, 'stop') and callable(self.stop):
            return self.stop()
        return False
    
    def _do_reload(self, **kwargs) -> bool:
        """Reload service configuration"""
        if hasattr(self, 'reload_config') and callable(self.reload_config):
            return self.reload_config()
        return False


class TrackerServicePolymorphic(ServicePolymorphic):
    """
    TournamentTracker-specific polymorphic implementation
    """
    
    def _ask_tournament_count(self) -> int:
        """Get tournament count"""
        if hasattr(self, 'get_tournament_count'):
            return self.get_tournament_count()
        return 0
    
    def _ask_last_sync(self) -> Any:
        """Get last sync time"""
        if hasattr(self, 'last_sync_time'):
            return self.last_sync_time
        return None
    
    def _tell_discord(self) -> str:
        """Format tracker status for Discord"""
        output = super()._tell_discord()
        
        count = self._ask_tournament_count()
        if count:
            output += f"\n🏆 Tournaments: {count}"
        
        last_sync = self._ask_last_sync()
        if last_sync:
            output += f"\n🔄 Last sync: {last_sync}"
        
        return output
    
    def _do_sync(self, **kwargs) -> bool:
        """Perform tournament sync"""
        if hasattr(self, 'sync_tournaments') and callable(self.sync_tournaments):
            return self.sync_tournaments()
        return False


class ClaudeServicePolymorphic(ServicePolymorphic):
    """
    Claude service-specific polymorphic implementation
    """
    
    def _ask_model(self) -> str:
        """Get Claude model being used"""
        if hasattr(self, 'model'):
            return self.model
        return "claude-3"
    
    def _ask_conversation_count(self) -> int:
        """Get number of conversations"""
        if hasattr(self, 'conversation_history'):
            return len(self.conversation_history)
        return 0
    
    def _tell_discord(self) -> str:
        """Format Claude service for Discord"""
        output = super()._tell_discord()
        
        model = self._ask_model()
        output += f"\n🤖 Model: {model}"
        
        conv_count = self._ask_conversation_count()
        if conv_count:
            output += f"\n💬 Conversations: {conv_count}"
        
        return output
    
    def _do_clear_history(self, **kwargs) -> bool:
        """Clear conversation history"""
        if hasattr(self, 'conversation_history'):
            self.conversation_history.clear()
            return True
        return False


class SyncServicePolymorphic(ServicePolymorphic):
    """
    Sync service-specific polymorphic implementation
    """
    
    def _ask_queue_size(self) -> int:
        """Get sync queue size"""
        if hasattr(self, 'queue') and hasattr(self.queue, '__len__'):
            return len(self.queue)
        return 0
    
    def _ask_sync_progress(self) -> Dict:
        """Get sync progress"""
        return {
            'queue_size': self._ask_queue_size(),
            'in_progress': hasattr(self, 'is_syncing') and self.is_syncing,
            'last_error': getattr(self, 'last_error', None)
        }
    
    def _tell_discord(self) -> str:
        """Format sync service for Discord"""
        output = super()._tell_discord()
        
        progress = self._ask_sync_progress()
        if progress['in_progress']:
            output += f"\n⏳ SYNC IN PROGRESS"
        
        queue = progress['queue_size']
        if queue:
            output += f"\n📋 Queue: {queue} items"
        
        return output
    
    def _do_process_queue(self, **kwargs) -> bool:
        """Process sync queue"""
        if hasattr(self, 'process_queue') and callable(self.process_queue):
            return self.process_queue()
        return False


def extend_services():
    """
    Extend existing service classes with polymorphic capabilities
    """
    extended_count = 0
    
    # Try to extend TournamentTracker
    try:
        from tournament_tracker import TournamentTracker
        # Check if not already extended
        if not hasattr(TournamentTracker, 'ask'):
            # Add methods directly instead of changing bases (avoids MRO issues)
            for method_name in ['ask', 'tell', 'do']:
                if not hasattr(TournamentTracker, method_name):
                    method = getattr(TrackerServicePolymorphic, method_name)
                    setattr(TournamentTracker, method_name, method)
            # Also add the internal methods
            for attr_name in dir(TrackerServicePolymorphic):
                if attr_name.startswith('_ask_') or attr_name.startswith('_tell_') or attr_name.startswith('_do_'):
                    if not hasattr(TournamentTracker, attr_name):
                        attr = getattr(TrackerServicePolymorphic, attr_name)
                        setattr(TournamentTracker, attr_name, attr)
            extended_count += 1
    except ImportError:
        pass
    
    # Try to extend ClaudeService
    try:
        from claude_service import ClaudeService
        if not hasattr(ClaudeService, 'ask'):
            # Add methods directly
            for method_name in ['ask', 'tell', 'do']:
                if not hasattr(ClaudeService, method_name):
                    method = getattr(ClaudeServicePolymorphic, method_name)
                    setattr(ClaudeService, method_name, method)
            # Add internal methods
            for attr_name in dir(ClaudeServicePolymorphic):
                if attr_name.startswith('_ask_') or attr_name.startswith('_tell_') or attr_name.startswith('_do_'):
                    if not hasattr(ClaudeService, attr_name):
                        attr = getattr(ClaudeServicePolymorphic, attr_name)
                        setattr(ClaudeService, attr_name, attr)
            extended_count += 1
    except ImportError:
        pass
    
    # Try to extend SyncService  
    try:
        from sync_service import SyncService
        if not hasattr(SyncService, 'ask'):
            # Add methods directly
            for method_name in ['ask', 'tell', 'do']:
                if not hasattr(SyncService, method_name):
                    method = getattr(SyncServicePolymorphic, method_name)
                    setattr(SyncService, method_name, method)
            # Add internal methods
            for attr_name in dir(SyncServicePolymorphic):
                if attr_name.startswith('_ask_') or attr_name.startswith('_tell_') or attr_name.startswith('_do_'):
                    if not hasattr(SyncService, attr_name):
                        attr = getattr(SyncServicePolymorphic, attr_name)
                        setattr(SyncService, attr_name, attr)
            extended_count += 1
    except ImportError:
        pass
    
    if extended_count > 0:
        announcer.announce(
            "Service Polymorphism",
            [f"Extended {extended_count} services with ask(), tell(), do()"],
            ["Services are now self-aware and intelligent"]
        )
    
    return extended_count


# Auto-extend when imported
if __name__ != "__main__":
    extend_services()