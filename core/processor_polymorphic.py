#!/usr/bin/env python3
"""
processor_polymorphic.py - Extend processor classes with the 3-method pattern
Makes data processors intelligent and self-aware
"""
from typing import Any, Optional, Dict, List
from polymorphic_model import PolymorphicModel
from capability_announcer import announcer


class ProcessorPolymorphic(PolymorphicModel):
    """
    Base polymorphic processor class.
    Processors can answer questions about their state and perform operations.
    """
    
    def _ask_progress(self) -> Dict:
        """Get processing progress"""
        progress = {
            'started': getattr(self, 'started_at', None),
            'completed': getattr(self, 'completed_at', None),
            'items_processed': getattr(self, 'items_processed', 0),
            'items_total': getattr(self, 'items_total', None),
            'errors': getattr(self, 'error_count', 0)
        }
        
        # Calculate percentage if possible
        if progress['items_total'] and progress['items_total'] > 0:
            progress['percentage'] = (progress['items_processed'] / progress['items_total']) * 100
        
        return progress
    
    def _ask_status(self) -> str:
        """Get processor status"""
        if hasattr(self, 'is_processing'):
            if self.is_processing:
                return "processing"
        
        if hasattr(self, 'completed_at') and self.completed_at:
            return "completed"
        
        if hasattr(self, 'error_count') and self.error_count > 0:
            return "error"
        
        return "idle"
    
    def _ask_statistics(self) -> Dict:
        """Get processing statistics"""
        return {
            'status': self._ask_status(),
            'progress': self._ask_progress(),
            'performance': {
                'items_per_second': getattr(self, 'items_per_second', None),
                'average_time': getattr(self, 'average_processing_time', None),
                'memory_usage': getattr(self, 'memory_usage', None)
            }
        }
    
    def _tell_discord(self) -> str:
        """Format processor status for Discord"""
        status = self._ask_status()
        progress = self._ask_progress()
        
        status_emoji = {
            'processing': '⏳',
            'completed': '✅',
            'error': '❌',
            'idle': '💤'
        }.get(status, '❓')
        
        output = f"{status_emoji} **{self.__class__.__name__}**\n"
        output += f"Status: {status.upper()}\n"
        
        if progress['items_total']:
            output += f"Progress: {progress['items_processed']}/{progress['items_total']}"
            if 'percentage' in progress:
                output += f" ({progress['percentage']:.1f}%)"
        
        if progress['errors'] > 0:
            output += f"\n⚠️ Errors: {progress['errors']}"
        
        return output
    
    def _tell_claude(self) -> Dict:
        """Explain processor to Claude"""
        return {
            'type': 'Processor',
            'name': self.__class__.__name__,
            'status': self._ask_status(),
            'capabilities': [
                'ask("progress") - Get processing progress',
                'ask("status") - Get current status',
                'ask("statistics") - Get full stats',
                'tell("discord") - Format for Discord',
                'do("process") - Start processing',
                'do("cancel") - Cancel processing'
            ],
            'current_state': self._ask_statistics()
        }
    
    def _do_process(self, **kwargs) -> bool:
        """Start processing"""
        if hasattr(self, 'process') and callable(self.process):
            return self.process(**kwargs)
        
        if hasattr(self, 'run') and callable(self.run):
            return self.run(**kwargs)
        
        return False
    
    def _do_cancel(self, **kwargs) -> bool:
        """Cancel processing"""
        if hasattr(self, 'cancel') and callable(self.cancel):
            return self.cancel()
        
        if hasattr(self, 'stop') and callable(self.stop):
            return self.stop()
        
        # Set a flag if possible
        if hasattr(self, 'is_cancelled'):
            self.is_cancelled = True
            return True
        
        return False
    
    def _do_reset(self, **kwargs) -> bool:
        """Reset processor state"""
        # Reset counters
        if hasattr(self, 'items_processed'):
            self.items_processed = 0
        if hasattr(self, 'error_count'):
            self.error_count = 0
        if hasattr(self, 'completed_at'):
            self.completed_at = None
        
        return True


class SyncProcessorPolymorphic(ProcessorPolymorphic):
    """
    Tournament sync processor-specific implementation
    """
    
    def _ask_tournaments_synced(self) -> int:
        """Get number of tournaments synced"""
        if hasattr(self, 'tournaments_synced'):
            return self.tournaments_synced
        return self._ask_progress().get('items_processed', 0)
    
    def _ask_last_tournament(self) -> Any:
        """Get last tournament processed"""
        if hasattr(self, 'last_tournament'):
            return self.last_tournament
        return None
    
    def _tell_discord(self) -> str:
        """Format sync processor for Discord"""
        output = super()._tell_discord()
        
        synced = self._ask_tournaments_synced()
        if synced:
            output += f"\n🏆 Tournaments synced: {synced}"
        
        last = self._ask_last_tournament()
        if last:
            name = last.name if hasattr(last, 'name') else str(last)
            output += f"\n📍 Last: {name}"
        
        return output
    
    def _do_sync_tournament(self, tournament_id: str, **kwargs) -> bool:
        """Sync a specific tournament"""
        if hasattr(self, 'sync_tournament') and callable(self.sync_tournament):
            return self.sync_tournament(tournament_id, **kwargs)
        return False


class CleanupProcessorPolymorphic(ProcessorPolymorphic):
    """
    Organization cleanup processor-specific implementation
    """
    
    def _ask_duplicates_found(self) -> int:
        """Get number of duplicates found"""
        if hasattr(self, 'duplicates_found'):
            return self.duplicates_found
        return 0
    
    def _ask_merges_completed(self) -> int:
        """Get number of merges completed"""
        if hasattr(self, 'merges_completed'):
            return self.merges_completed
        return 0
    
    def _tell_discord(self) -> str:
        """Format cleanup processor for Discord"""
        output = super()._tell_discord()
        
        duplicates = self._ask_duplicates_found()
        if duplicates:
            output += f"\n🔍 Duplicates found: {duplicates}"
        
        merges = self._ask_merges_completed()
        if merges:
            output += f"\n🔗 Merges completed: {merges}"
        
        return output
    
    def _do_merge(self, source_id: int, target_id: int, **kwargs) -> bool:
        """Merge two organizations"""
        if hasattr(self, 'merge_organizations') and callable(self.merge_organizations):
            return self.merge_organizations(source_id, target_id, **kwargs)
        return False


def extend_processors():
    """
    Extend existing processor classes with polymorphic capabilities
    """
    extended_count = 0
    
    # Try to extend TournamentSyncProcessor
    try:
        from tournament_operations import TournamentSyncProcessor
        if not hasattr(TournamentSyncProcessor, 'ask'):
            # Add methods directly (avoids MRO issues)
            for method_name in ['ask', 'tell', 'do']:
                if not hasattr(TournamentSyncProcessor, method_name):
                    method = getattr(SyncProcessorPolymorphic, method_name)
                    setattr(TournamentSyncProcessor, method_name, method)
            # Add internal methods
            for attr_name in dir(SyncProcessorPolymorphic):
                if attr_name.startswith('_ask_') or attr_name.startswith('_tell_') or attr_name.startswith('_do_'):
                    if not hasattr(TournamentSyncProcessor, attr_name):
                        attr = getattr(SyncProcessorPolymorphic, attr_name)
                        setattr(TournamentSyncProcessor, attr_name, attr)
            extended_count += 1
    except ImportError:
        pass
    
    # Try to extend OrganizationCleanupProcessor
    try:
        from tournament_operations import OrganizationCleanupProcessor
        if not hasattr(OrganizationCleanupProcessor, 'ask'):
            # Add methods directly
            for method_name in ['ask', 'tell', 'do']:
                if not hasattr(OrganizationCleanupProcessor, method_name):
                    method = getattr(CleanupProcessorPolymorphic, method_name)
                    setattr(OrganizationCleanupProcessor, method_name, method)
            # Add internal methods
            for attr_name in dir(CleanupProcessorPolymorphic):
                if attr_name.startswith('_ask_') or attr_name.startswith('_tell_') or attr_name.startswith('_do_'):
                    if not hasattr(OrganizationCleanupProcessor, attr_name):
                        attr = getattr(CleanupProcessorPolymorphic, attr_name)
                        setattr(OrganizationCleanupProcessor, attr_name, attr)
            extended_count += 1
    except ImportError:
        pass
    
    if extended_count > 0:
        announcer.announce(
            "Processor Polymorphism",
            [f"Extended {extended_count} processors with ask(), tell(), do()"],
            ["Processors now understand their state and progress"]
        )
    
    return extended_count


# Auto-extend when imported
if __name__ != "__main__":
    extend_processors()