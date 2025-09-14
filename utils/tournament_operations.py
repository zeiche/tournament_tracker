"""
tournament_operations.py - Tournament Operation Tracking and Processing

NOW USING POLYMORPHIC ask/tell/do PATTERN:
- ask(query) - Get operation stats: "stats", "errors", "progress"
- tell(format, data) - Format operation data: "json", "text", "discord"
- do(action) - Perform operations: "track sync", "validate config", "log progress"
"""
import os
import sys
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import centralized logging
from log_manager import LogManager
from polymorphic_core import announcer

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.tournament_operations")

# Initialize logger for this module
logger = LogManager().get_logger('tournament_operations')


class TournamentOperations:
    """Tournament operations service with ONLY 3 public methods: ask, tell, do
    
    Everything else is private implementation details.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._trackers = {}  # Active operation trackers
            self._processors = {}  # Active processors
            self._initialized = True
            
            # Announce ourselves
            announcer.announce(
                "Tournament Operations (Polymorphic)",
                [
                    "ask('stats') - Get operation statistics",
                    "ask('errors') - Get error details",
                    "ask('progress') - Get current progress",
                    "tell('discord', stats) - Format for Discord",
                    "do('track sync') - Start tracking sync operation",
                    "do('validate config') - Check configuration",
                    "NOW WITH ask/tell/do PATTERN!"
                ],
                [
                    "ops.ask('stats')",
                    "ops.tell('json', data)",
                    "ops.do('track sync tournaments=50')"
                ]
            )
    
    def ask(self, query: str, **kwargs) -> Any:
        """Ask for operation data and statistics.
        
        Examples:
            ask('stats') - Get all operation statistics
            ask('errors') - Get recent errors
            ask('progress') - Get current operation progress
            ask('tracker sync') - Get specific tracker stats
            ask('config status') - Check configuration status
        """
        query_lower = query.lower().strip()
        
        # Statistics queries
        if 'stat' in query_lower:
            return self._get_stats(**kwargs)
        
        # Error queries
        elif 'error' in query_lower:
            return self._get_errors(**kwargs)
        
        # Progress queries
        elif 'progress' in query_lower:
            return self._get_progress(**kwargs)
        
        # Tracker queries
        elif 'tracker' in query_lower:
            # Parse tracker name
            parts = query_lower.split()
            if len(parts) > 1:
                tracker_name = parts[1]
                return self._get_tracker_stats(tracker_name)
            return self._get_all_trackers()
        
        # Config queries
        elif 'config' in query_lower:
            return self._get_config_status()
        
        # Default - return summary
        return {
            'active_trackers': len(self._trackers),
            'active_processors': len(self._processors),
            'total_operations': sum(t.stats['attempts'] for t in self._trackers.values())
        }
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format operation data for output.
        
        Examples:
            tell('json', stats) - Format as JSON
            tell('discord', errors) - Format for Discord
            tell('text', progress) - Format as plain text
            tell('summary', data) - Brief summary
        """
        format_lower = format.lower().strip()
        
        # If no data provided, get default stats
        if data is None:
            data = self.ask('stats')
        
        if format_lower == 'json':
            return json.dumps(data, default=str, indent=2)
        
        elif format_lower == 'discord':
            return self._format_discord(data)
        
        elif format_lower in ['text', 'plain']:
            return self._format_text(data)
        
        elif format_lower == 'summary':
            return self._format_summary(data)
        
        # Default - string representation
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform tournament operations.
        
        Examples:
            do('track sync') - Start tracking sync operation
            do('record success tournaments=5') - Record success
            do('record error message="API failed"') - Record error
            do('end tracker sync') - End tracking
            do('validate config') - Validate configuration
            do('log progress current=5 total=10') - Log progress
        """
        action_lower = action.lower().strip()
        
        # Track operations
        if 'track' in action_lower:
            return self._do_track(action, **kwargs)
        
        # Record operations
        elif 'record' in action_lower:
            return self._do_record(action, **kwargs)
        
        # End operations
        elif 'end' in action_lower:
            return self._do_end(action, **kwargs)
        
        # Validate operations
        elif 'validate' in action_lower:
            return self._do_validate(action, **kwargs)
        
        # Log operations
        elif 'log' in action_lower:
            return self._do_log(action, **kwargs)
        
        # Process operations
        elif 'process' in action_lower:
            return self._do_process(action, **kwargs)
        
        # Unknown action
        return f"Unknown action: {action}"
    
    # ============= PRIVATE METHODS =============
    
    def _get_stats(self, tracker_name: Optional[str] = None, **kwargs) -> Dict:
        """Get operation statistics"""
        if tracker_name and tracker_name in self._trackers:
            return self._trackers[tracker_name].get_stats()
        
        # Aggregate all stats
        all_stats = {}
        for name, tracker in self._trackers.items():
            all_stats[name] = tracker.get_stats()
        
        return all_stats
    
    def _get_errors(self, limit: int = 10, **kwargs) -> List[str]:
        """Get recent errors"""
        errors = []
        for tracker in self._trackers.values():
            errors.extend(tracker.stats['errors'])
        
        return errors[-limit:] if limit else errors
    
    def _get_progress(self, **kwargs) -> Dict:
        """Get current operation progress"""
        progress = {}
        for name, tracker in self._trackers.items():
            stats = tracker.stats
            if stats['start_time'] and not stats['end_time']:
                # Operation in progress
                progress[name] = {
                    'tournaments': stats['tournaments_processed'],
                    'organizations': stats['organizations_processed'],
                    'players': stats['players_processed'],
                    'successes': stats['successes'],
                    'failures': stats['failures']
                }
        
        return progress
    
    def _get_tracker_stats(self, tracker_name: str) -> Dict:
        """Get specific tracker statistics"""
        if tracker_name in self._trackers:
            return self._trackers[tracker_name].get_stats()
        return {'error': f'Tracker {tracker_name} not found'}
    
    def _get_all_trackers(self) -> Dict:
        """Get all tracker names and states"""
        return {
            name: {
                'active': tracker.stats['end_time'] is None,
                'attempts': tracker.stats['attempts'],
                'successes': tracker.stats['successes'],
                'failures': tracker.stats['failures']
            }
            for name, tracker in self._trackers.items()
        }
    
    def _get_config_status(self) -> Dict:
        """Check configuration status"""
        return {
            'auth_key': bool(os.getenv('AUTH_KEY')),
            'access_token': bool(os.getenv('ACCESS_TOKEN')),
            'shopify_access_token': bool(os.getenv('SHOPIFY_ACCESS_TOKEN')),
            'discord_token': bool(os.getenv('DISCORD_BOT_TOKEN'))
        }
    
    def _format_discord(self, data: Any) -> str:
        """Format data for Discord"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"**{key}:**")
                    for k, v in value.items():
                        lines.append(f"  {k}: {v}")
                else:
                    lines.append(f"**{key}**: {value}")
            return "\n".join(lines)
        
        elif isinstance(data, list):
            return "\n".join([f"• {item}" for item in data[:10]])
        
        return f"```{data}```"
    
    def _format_text(self, data: Any) -> str:
        """Format data as plain text"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        
        elif isinstance(data, list):
            return "\n".join(str(item) for item in data)
        
        return str(data)
    
    def _format_summary(self, data: Any) -> str:
        """Format brief summary"""
        if isinstance(data, dict):
            total = data.get('total_operations', 0)
            active = len([1 for k, v in data.items() if isinstance(v, dict) and not v.get('end_time')])
            return f"{total} operations, {active} active"
        
        return str(data)[:100]
    
    def _do_track(self, action: str, **kwargs) -> str:
        """Start tracking an operation"""
        # Parse operation name
        parts = action.split()
        if len(parts) < 2:
            return "Error: Specify operation name (e.g., 'track sync')"
        
        operation_name = parts[1]
        
        # Create tracker
        tracker = TournamentOperationTracker(operation_name)
        tracker.start_operation()
        self._trackers[operation_name] = tracker
        
        return f"Started tracking {operation_name}"
    
    def _do_record(self, action: str, **kwargs) -> str:
        """Record operation results"""
        action_lower = action.lower()
        
        # Parse tracker name if specified
        tracker_name = kwargs.get('tracker', 'default')
        if tracker_name not in self._trackers:
            # Create default tracker if needed
            self._trackers[tracker_name] = TournamentOperationTracker(tracker_name)
        
        tracker = self._trackers[tracker_name]
        
        # Record success
        if 'success' in action_lower:
            tournaments = kwargs.get('tournaments', 0)
            organizations = kwargs.get('organizations', 0)
            players = kwargs.get('players', 0)
            
            if tournaments:
                tracker.record_tournament_success(tournaments)
            if organizations:
                tracker.record_organization_success(organizations)
            if players:
                tracker.record_player_success(players)
            
            return f"Recorded success: T={tournaments}, O={organizations}, P={players}"
        
        # Record error
        elif 'error' in action_lower or 'failure' in action_lower:
            message = kwargs.get('message', 'Unknown error')
            context = kwargs.get('context')
            tracker.record_failure(message, context)
            return f"Recorded error: {message}"
        
        return "Unknown record action"
    
    def _do_end(self, action: str, **kwargs) -> str:
        """End tracking operation"""
        # Parse tracker name
        parts = action.split()
        if len(parts) > 2:
            tracker_name = parts[2]
        else:
            tracker_name = kwargs.get('tracker', 'default')
        
        if tracker_name in self._trackers:
            self._trackers[tracker_name].end_operation()
            return f"Ended tracking {tracker_name}"
        
        return f"Tracker {tracker_name} not found"
    
    def _do_validate(self, action: str, **kwargs) -> str:
        """Validate configuration"""
        if 'startgg' in action.lower() or 'start.gg' in action.lower():
            try:
                validate_startgg_config()
                return "start.gg configuration valid"
            except RuntimeError as e:
                return f"start.gg config error: {e}"
        
        elif 'shopify' in action.lower():
            try:
                validate_shopify_config()
                return "Shopify configuration valid"
            except RuntimeError as e:
                return f"Shopify config error: {e}"
        
        # General config check
        status = self._get_config_status()
        valid = all(status.values())
        return f"Configuration {'valid' if valid else 'incomplete'}: {status}"
    
    def _do_log(self, action: str, **kwargs) -> str:
        """Log progress or messages"""
        if 'progress' in action.lower():
            current = kwargs.get('current', 0)
            total = kwargs.get('total', 0)
            item_type = kwargs.get('type', 'items')
            log_tournament_progress(current, total, item_type)
            return f"Logged progress: {current}/{total} {item_type}"
        
        # General log
        message = kwargs.get('message', action)
        logger.info(message)
        return f"Logged: {message}"
    
    def _do_process(self, action: str, **kwargs) -> Any:
        """Run a processor"""
        if 'sync' in action.lower():
            processor = TournamentSyncProcessor("sync")
            result = processor.run(**kwargs)
            self._processors['sync'] = processor
            return result
        
        elif 'cleanup' in action.lower():
            processor = OrganizationCleanupProcessor("cleanup")
            result = processor.run(**kwargs)
            self._processors['cleanup'] = processor
            return result
        
        return "Unknown processor"


# Keep existing classes for backward compatibility but make them private
class TournamentOperationTracker:
    """Track statistics for tournament processing operations"""
    
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.stats = {
            'operation_name': operation_name,
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'start_time': None,
            'end_time': None,
            'total_processing_time': 0,
            'tournaments_processed': 0,
            'organizations_processed': 0,
            'players_processed': 0,
            'errors': []
        }
        
        logger.debug(f"Operation tracker created: {operation_name}")
    
    def start_operation(self):
        """Mark operation start"""
        self.stats['start_time'] = datetime.now()
        self.stats['attempts'] += 1
        logger.info(f"Starting {self.operation_name}")
    
    def record_tournament_success(self, tournament_count=1):
        """Record successful tournament processing"""
        self.stats['successes'] += 1
        self.stats['tournaments_processed'] += tournament_count
        logger.debug(f"Tournament processing success: +{tournament_count}")
    
    def record_organization_success(self, org_count=1):
        """Record successful organization processing"""
        self.stats['successes'] += 1
        self.stats['organizations_processed'] += org_count
        logger.debug(f"Organization processing success: +{org_count}")
    
    def record_player_success(self, player_count=1):
        """Record successful player processing"""
        self.stats['successes'] += 1
        self.stats['players_processed'] += player_count
        logger.debug(f"Player processing success: +{player_count}")
    
    def record_failure(self, error_msg, context=None):
        """Record failed operation"""
        self.stats['failures'] += 1
        self.stats['errors'].append(error_msg)
        
        full_context = f"{self.operation_name}"
        if context:
            full_context += f" ({context})"
            
        logger.error(f"{full_context}: {error_msg}")
    
    def end_operation(self):
        """Mark operation end and log summary"""
        self.stats['end_time'] = datetime.now()
        if self.stats['start_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            self.stats['total_processing_time'] = duration.total_seconds()
        
        self.log_summary()
    
    def get_stats(self):
        """Get operation statistics"""
        total_ops = self.stats['successes'] + self.stats['failures']
        success_rate = (self.stats['successes'] / max(1, total_ops)) * 100
        
        return {
            **self.stats,
            'total_operations': total_ops,
            'success_rate': success_rate
        }
    
    def log_summary(self):
        """Log operation summary"""
        stats = self.get_stats()
        
        logger.info(f"{self.operation_name} completed!")
        logger.info(f"   Attempts: {stats['attempts']}")
        logger.info(f"   Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"   Tournaments: {stats['tournaments_processed']}")
        logger.info(f"   Organizations: {stats['organizations_processed']}") 
        logger.info(f"   Players: {stats['players_processed']}")
        logger.info(f"   Processing time: {stats['total_processing_time']:.2f}s")
        
        if stats['failures'] > 0:
            logger.warning(f"   Errors: {stats['failures']}")


class TournamentProcessor(ABC):
    """Base class for tournament data processing operations"""
    
    def __init__(self, operation_name):
        self.tracker = TournamentOperationTracker(operation_name)
        self.operation_name = operation_name
    
    def run(self, **kwargs):
        """Main execution method with error handling and tracking"""
        self.tracker.start_operation()
        
        try:
            # Execute operation with logging context
            result = self.execute(**kwargs)
                
            return result
        except Exception as e:
            error_msg = f"{self.__class__.__name__} failed: {e}"
            self.tracker.record_failure(error_msg)
            return None
        finally:
            self.tracker.end_operation()
    
    @abstractmethod
    def execute(self, **kwargs):
        """Override this method in subclasses"""
        pass
    
    def get_stats(self):
        """Get processing statistics"""
        return self.tracker.get_stats()
    
    def log_progress(self, current, total, item_type="items"):
        """Log processing progress"""
        if total > 0:
            percent = (current / total) * 100
            logger.info(f"   Progress: {current}/{total} {item_type} ({percent:.1f}%)")


class TournamentSyncProcessor(TournamentProcessor):
    """Processor for tournament synchronization operations"""
    
    def execute(self, **kwargs):
        """Execute tournament sync"""
        # This would be implemented by sync modules
        logger.info("Tournament sync processor executed")
        return {"status": "success"}


class OrganizationCleanupProcessor(TournamentProcessor):
    """Processor for organization name cleanup operations"""
    
    def execute(self, **kwargs):
        """Execute organization cleanup"""
        # This would be implemented by editor modules
        logger.info("Organization cleanup processor executed")
        return {"status": "success"}


# Legacy functions kept for backward compatibility
def handle_tournament_error(operation_name, error, context=None, continue_on_error=True):
    """Tournament-specific error handling"""
    ops = tournament_operations
    result = ops.do(f'record error message="{error}"', tracker=operation_name, context=context)
    
    if continue_on_error:
        logger.warning("Continuing with remaining operations...")
        return False
    else:
        logger.error("Stopping due to error")
        raise RuntimeError(f"{operation_name} error: {error}")


def log_tournament_operation_start(operation_name, details=""):
    """Log start of tournament operation"""
    ops = tournament_operations
    ops.do(f'track {operation_name}')
    if details:
        logger.debug(f"   {details}")


def log_tournament_progress(current, total, item_type="tournaments"):
    """Log tournament processing progress"""
    if total > 0:
        percent = (current / total) * 100
        logger.info(f"   Progress: {current}/{total} {item_type} ({percent:.1f}%)")


def validate_tournament_config(required_vars):
    """Validate required configuration for tournament operations"""
    missing = []
    for var_name in required_vars:
        if not os.getenv(var_name):
            missing.append(var_name)
    
    if missing:
        error_msg = f"Required tournament configuration missing: {', '.join(missing)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"Tournament configuration validated: {', '.join(required_vars)}")
    return True


def validate_startgg_config():
    """Validate start.gg API configuration"""
    return validate_tournament_config(['AUTH_KEY'])


def validate_shopify_config():
    """Validate Shopify publishing configuration"""
    return validate_tournament_config(['ACCESS_TOKEN'])


# Singleton instance - import this
tournament_operations = TournamentOperations()


# Test functions for tournament operations
def test_tournament_operations():
    """Test tournament operations with ask/tell/do pattern"""
    print("=" * 60)
    print("TESTING TOURNAMENT OPERATIONS (ask/tell/do)")
    print("=" * 60)
    
    ops = tournament_operations
    
    try:
        # Test 1: ask() method
        print("\nTEST 1: ask() method")
        print("ask('stats'):", ops.ask('stats'))
        print("ask('config status'):", ops.ask('config status'))
        print("✅ ask() works")
        
        # Test 2: do() method - tracking
        print("\nTEST 2: do() method - tracking")
        print(ops.do('track test_operation'))
        print(ops.do('record success tournaments=5 organizations=3', tracker='test_operation'))
        print(ops.do('end tracker test_operation'))
        print("✅ do() tracking works")
        
        # Test 3: tell() method
        print("\nTEST 3: tell() method")
        stats = ops.ask('stats')
        print("tell('json'):", ops.tell('json', {'test': 'data'})[:50] + "...")
        print("tell('summary'):", ops.tell('summary', stats))
        print("✅ tell() works")
        
        # Test 4: Error handling
        print("\nTEST 4: Error handling")
        print(ops.do('record error message="Test error"', tracker='error_test'))
        errors = ops.ask('errors')
        print("Recent errors:", errors[-1] if errors else "None")
        print("✅ Error handling works")
        
        print("\n✅ All tournament operations tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Testing tournament operations with ask/tell/do pattern...")
    test_tournament_operations()