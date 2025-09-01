"""
tournament_operations.py - Tournament Operation Tracking and Processing
Tournament-focused operational utilities with centralized logging
"""
import os
from datetime import datetime
from abc import ABC, abstractmethod

# Import centralized logging
from log_utils import log_info, log_debug, log_error, log_warn, LogContext

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
        
        log_debug(f"Operation tracker created: {operation_name}", "operations")
    
    def start_operation(self):
        """Mark operation start"""
        self.stats['start_time'] = datetime.now()
        self.stats['attempts'] += 1
        log_info(f"Starting {self.operation_name}", "operations")
    
    def record_tournament_success(self, tournament_count=1):
        """Record successful tournament processing"""
        self.stats['successes'] += 1
        self.stats['tournaments_processed'] += tournament_count
        log_debug(f"Tournament processing success: +{tournament_count}", "operations")
    
    def record_organization_success(self, org_count=1):
        """Record successful organization processing"""
        self.stats['successes'] += 1
        self.stats['organizations_processed'] += org_count
        log_debug(f"Organization processing success: +{org_count}", "operations")
    
    def record_player_success(self, player_count=1):
        """Record successful player processing"""
        self.stats['successes'] += 1
        self.stats['players_processed'] += player_count
        log_debug(f"Player processing success: +{player_count}", "operations")
    
    def record_failure(self, error_msg, context=None):
        """Record failed operation"""
        self.stats['failures'] += 1
        self.stats['errors'].append(error_msg)
        
        full_context = f"{self.operation_name}"
        if context:
            full_context += f" ({context})"
            
        log_error(f"{full_context}: {error_msg}", "operations")
    
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
        
        log_info(f"{self.operation_name} completed!", "operations")
        log_info(f"   Attempts: {stats['attempts']}", "operations")
        log_info(f"   Success rate: {stats['success_rate']:.1f}%", "operations")
        log_info(f"   Tournaments: {stats['tournaments_processed']}", "operations")
        log_info(f"   Organizations: {stats['organizations_processed']}", "operations") 
        log_info(f"   Players: {stats['players_processed']}", "operations")
        log_info(f"   Processing time: {stats['total_processing_time']:.2f}s", "operations")
        
        if stats['failures'] > 0:
            log_warn(f"   Errors: {stats['failures']}", "operations")

class TournamentProcessor(ABC):
    """Base class for tournament data processing operations"""
    
    def __init__(self, operation_name):
        self.tracker = TournamentOperationTracker(operation_name)
        self.operation_name = operation_name
    
    def run(self, **kwargs):
        """Main execution method with error handling and tracking"""
        self.tracker.start_operation()
        
        try:
            with LogContext(f"Execute {self.operation_name}"):
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
            log_info(f"   Progress: {current}/{total} {item_type} ({percent:.1f}%)", "operations")

class TournamentSyncProcessor(TournamentProcessor):
    """Processor for tournament synchronization operations"""
    
    def execute(self, **kwargs):
        """Execute tournament sync"""
        # This would be implemented by sync modules
        log_info("Tournament sync processor executed", "operations")
        return {"status": "success"}

class OrganizationCleanupProcessor(TournamentProcessor):
    """Processor for organization name cleanup operations"""
    
    def execute(self, **kwargs):
        """Execute organization cleanup"""
        # This would be implemented by editor modules
        log_info("Organization cleanup processor executed", "operations")
        return {"status": "success"}

def handle_tournament_error(operation_name, error, context=None, continue_on_error=True):
    """Tournament-specific error handling"""
    error_msg = f"{operation_name} error: {error}"
    
    full_context = "operations"
    if context:
        full_context = f"operations-{context}"
    
    log_error(error_msg, full_context)
    
    if continue_on_error:
        log_warn("Continuing with remaining operations...", "operations")
        return False
    else:
        log_error("Stopping due to error", "operations")
        raise RuntimeError(error_msg)

def log_tournament_operation_start(operation_name, details=""):
    """Log start of tournament operation"""
    log_info(f"Starting {operation_name}", "operations")
    if details:
        log_debug(f"   {details}", "operations")

def log_tournament_progress(current, total, item_type="tournaments"):
    """Log tournament processing progress"""
    if total > 0:
        percent = (current / total) * 100
        log_info(f"   Progress: {current}/{total} {item_type} ({percent:.1f}%)", "operations")

def validate_tournament_config(required_vars):
    """Validate required configuration for tournament operations"""
    missing = []
    for var_name in required_vars:
        if not os.getenv(var_name):
            missing.append(var_name)
    
    if missing:
        error_msg = f"Required tournament configuration missing: {', '.join(missing)}"
        log_error(error_msg, "operations")
        raise RuntimeError(error_msg)
    
    log_info(f"Tournament configuration validated: {', '.join(required_vars)}", "operations")
    return True

def validate_startgg_config():
    """Validate start.gg API configuration"""
    return validate_tournament_config(['AUTH_KEY'])

def validate_shopify_config():
    """Validate Shopify publishing configuration"""
    return validate_tournament_config(['ACCESS_TOKEN'])

# Tournament-specific operation patterns
def track_sync_operation(tournaments_count, organizations_count=0, api_calls=0):
    """Track tournament sync operation metrics"""
    log_info(f"Sync metrics: {tournaments_count} tournaments, {organizations_count} orgs, {api_calls} API calls", "operations")

def track_cleanup_operation(organizations_changed, organizations_skipped=0):
    """Track organization cleanup operation metrics"""
    log_info(f"Cleanup metrics: {organizations_changed} changed, {organizations_skipped} skipped", "operations")

def track_report_operation(report_type, organizations_count, output_size=None):
    """Track report generation metrics"""
    size_info = f", {output_size} chars" if output_size else ""
    log_info(f"Report metrics: {report_type} for {organizations_count} orgs{size_info}", "operations")

# Test functions for tournament operations
def test_tournament_tracker():
    """Test tournament operation tracker"""
    log_info("=" * 60, "test")
    log_info("TESTING TOURNAMENT OPERATION TRACKER", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test 1: Basic tracking
        log_info("TEST 1: Basic operation tracking", "test")
        tracker = TournamentOperationTracker("test_sync_operation")
        
        tracker.start_operation()
        tracker.record_tournament_success(5)
        tracker.record_organization_success(3)
        tracker.record_player_success(25)
        tracker.end_operation()
        
        stats = tracker.get_stats()
        if stats['tournaments_processed'] == 5 and stats['success_rate'] > 0:
            log_info("✅ Basic tracking works", "test")
        else:
            log_error("❌ Basic tracking failed", "test")
        
        # Test 2: Error tracking
        log_info("TEST 2: Error tracking", "test")
        error_tracker = TournamentOperationTracker("test_error_operation")
        
        error_tracker.start_operation()
        error_tracker.record_failure("Test error message", "test_context")
        error_tracker.record_tournament_success(2)  # Some successes too
        error_tracker.end_operation()
        
        error_stats = error_tracker.get_stats()
        if error_stats['failures'] == 1 and len(error_stats['errors']) == 1:
            log_info("✅ Error tracking works", "test")
        else:
            log_error("❌ Error tracking failed", "test")
        
        log_info("✅ Tournament tracker tests completed", "test")
        
    except Exception as e:
        log_error(f"Tournament tracker test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_tournament_processor():
    """Test tournament processor base class"""
    log_info("=" * 60, "test")
    log_info("TESTING TOURNAMENT PROCESSOR", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test 1: Successful processor
        log_info("TEST 1: Successful processor", "test")
        sync_processor = TournamentSyncProcessor("test_sync")
        result = sync_processor.run()
        
        if result and result['status'] == 'success':
            log_info("✅ Sync processor works", "test")
        else:
            log_error("❌ Sync processor failed", "test")
        
        # Test 2: Cleanup processor
        log_info("TEST 2: Cleanup processor", "test")
        cleanup_processor = OrganizationCleanupProcessor("test_cleanup")
        result = cleanup_processor.run()
        
        if result and result['status'] == 'success':
            log_info("✅ Cleanup processor works", "test")
        else:
            log_error("❌ Cleanup processor failed", "test")
        
        log_info("✅ Tournament processor tests completed", "test")
        
    except Exception as e:
        log_error(f"Tournament processor test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_tournament_config():
    """Test tournament configuration validation"""
    log_info("=" * 60, "test")
    log_info("TESTING TOURNAMENT CONFIG VALIDATION", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test 1: Missing config (should fail gracefully)
        log_info("TEST 1: Missing configuration", "test")
        
        # Clear AUTH_KEY temporarily
        original_auth = os.getenv('AUTH_KEY')
        if 'AUTH_KEY' in os.environ:
            del os.environ['AUTH_KEY']
        
        try:
            validate_startgg_config()
            log_error("❌ Should have failed with missing AUTH_KEY", "test")
        except RuntimeError:
            log_info("✅ Correctly detected missing AUTH_KEY", "test")
        
        # Restore AUTH_KEY if it existed
        if original_auth:
            os.environ['AUTH_KEY'] = original_auth
        
        # Test 2: Valid config (if AUTH_KEY exists)
        if os.getenv('AUTH_KEY'):
            log_info("TEST 2: Valid configuration", "test")
            try:
                validate_startgg_config()
                log_info("✅ start.gg config validation works", "test")
            except RuntimeError:
                log_warn("AUTH_KEY exists but validation failed", "test")
        
        log_info("✅ Config validation tests completed", "test")
        
    except Exception as e:
        log_error(f"Config validation test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_operation_helpers():
    """Test operation helper functions"""
    log_info("=" * 60, "test")
    log_info("TESTING OPERATION HELPERS", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test 1: Progress tracking
        log_info("TEST 1: Progress tracking", "test")
        log_tournament_operation_start("Test Operation", "Testing progress tracking")
        
        for i in range(1, 6):
            log_tournament_progress(i, 5, "test_items")
        
        log_info("✅ Progress tracking works", "test")
        
        # Test 2: Error handling
        log_info("TEST 2: Error handling", "test")
        
        # Test continue on error
        continue_result = handle_tournament_error(
            "test_operation", 
            "test error message", 
            context="test_context",
            continue_on_error=True
        )
        
        if continue_result == False:  # Should return False for continue
            log_info("✅ Continue on error works", "test")
        else:
            log_error("❌ Continue on error failed", "test")
        
        # Test 3: Operation metrics
        log_info("TEST 3: Operation metrics", "test")
        track_sync_operation(tournaments_count=50, organizations_count=25, api_calls=10)
        track_cleanup_operation(organizations_changed=15, organizations_skipped=5)
        track_report_operation("HTML", organizations_count=30, output_size=15000)
        log_info("✅ Operation metrics logging works", "test")
        
        log_info("✅ Operation helpers tests completed", "test")
        
    except Exception as e:
        log_error(f"Operation helpers test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def run_tournament_operations_tests():
    """Run all tournament operations tests"""
    try:
        # Initialize logging
        from log_utils import init_logging, LogLevel
        init_logging(console=True, level=LogLevel.DEBUG, debug_file="operations_test.txt")
        
        log_info("Starting tournament operations tests", "test")
        
        # Run test suites
        test_tournament_tracker()
        print()  # Spacing
        test_tournament_processor()
        print()  # Spacing
        test_tournament_config()
        print()  # Spacing
        test_operation_helpers()
        
        log_info("All tournament operations tests completed - check operations_test.txt for details", "test")
        
    except Exception as e:
        log_error(f"Tournament operations test suite failed: {e}", "test")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing tournament operations...")
    run_tournament_operations_tests()

