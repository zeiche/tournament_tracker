"""
queue_system.py - Paged Queue System for Batch Database Operations
Fixed to use centralized session management and logging
"""
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable

# Import centralized systems
from database_service import database_service
from database import clear_session
from log_manager import LogManager

# Initialize logger for this module
logger = LogManager().get_logger('database_queue')

class OperationType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CUSTOM = "custom"

@dataclass
class QueuedOperation:
    """Represents a queued database operation"""
    operation_type: OperationType
    model_class: Any
    data: Dict[str, Any]
    primary_key: Optional[str] = None
    callback: Optional[Callable] = None
    priority: int = 0  # Lower = higher priority (deletes first)

class OperationQueue:
    """Paged queue system for batch database operations"""
    
    def __init__(self, page_size=250, auto_commit=True):
        self.page_size = page_size
        self.auto_commit = auto_commit
        self.current_page = []
        self.error_queue = []
        self.stats = {
            'pages_processed': 0,
            'operations_successful': 0,
            'operations_failed': 0,
            'total_processing_time': 0,
            'items_processed': 0,
            'errors': []
        }
        
        logger.debug(f"Queue initialized: page_size={page_size}, auto_commit={auto_commit}")
    
    def queue(self, operation_type, model_class, data, primary_key=None, callback=None):
        """Queue an operation"""
        # Set priority based on operation type
        priority = {
            OperationType.DELETE: 0,  # Deletes first
            OperationType.UPDATE: 1,  # Updates second
            OperationType.CREATE: 2,  # Creates third
            OperationType.CUSTOM: 1   # Custom operations with updates
        }.get(operation_type, 2)
        
        operation = QueuedOperation(
            operation_type=operation_type,
            model_class=model_class,
            data=data,
            primary_key=primary_key,
            callback=callback,
            priority=priority
        )
        
        self.current_page.append(operation)
        logger.debug(f"Queued {operation_type.value} operation for {model_class.__name__ if model_class else 'Custom'}")
        
        # Auto-flush when page is full
        if len(self.current_page) >= self.page_size and self.auto_commit:
            self.flush_page()
    
    def create(self, model_class, **data):
        """Queue a create operation"""
        self.queue(OperationType.CREATE, model_class, data)
    
    def update(self, model_class, primary_key, **data):
        """Queue an update operation"""
        self.queue(OperationType.UPDATE, model_class, data, primary_key)
    
    def delete(self, model_class, primary_key):
        """Queue a delete operation"""
        self.queue(OperationType.DELETE, model_class, {}, primary_key)
    
    def custom(self, callback, **data):
        """Queue a custom operation with callback"""
        self.queue(OperationType.CUSTOM, None, data, callback=callback)
    
    def flush_page(self):
        """Process the current page using centralized session management"""
        if not self.current_page:
            return
        
        start_time = time.time()
        page_operations = len(self.current_page)
        
        logger.debug(f"Flushing page with {page_operations} operations")
        
        # Sort operations by priority (deletes first, creates last)
        self.current_page.sort(key=lambda op: op.priority)
        
        # Process the page using centralized session
        successful = 0
        failed = 0
        
        try:
            with get_session() as session:
                for operation in self.current_page:
                    try:
                        self._execute_operation(session, operation)
                        successful += 1
                    except Exception as e:
                        failed += 1
                        self.error_queue.append((operation, str(e)))
                        logger.error(f"Operation failed: {operation.operation_type.value} {operation.model_class.__name__ if operation.model_class else 'Custom'}: {e}")
                
                # Commit happens automatically via get_session() context manager
                
        except Exception as e:
            # Entire page failed
            failed = page_operations
            for operation in self.current_page:
                self.error_queue.append((operation, f"Page failed: {e}"))
            logger.error(f"Entire page failed: {e}")
        
        # Clear session cache after page processing
        clear_session()
        
        # Update stats
        processing_time = time.time() - start_time
        self.stats['pages_processed'] += 1
        self.stats['operations_successful'] += successful
        self.stats['operations_failed'] += failed
        self.stats['total_processing_time'] += processing_time
        self.stats['items_processed'] += successful
        
        logger.debug(f"Page {self.stats['pages_processed']}: {successful} operations successful")
        logger.debug(f"Page timing: {processing_time:.2f}s, {failed} failed")
        
        # Clear current page
        self.current_page = []
    
    def commit(self):
        """Manually flush the current page"""
        if self.current_page:
            logger.debug("Manual commit requested")
            self.flush_page()
    
    def rollback_current_page(self):
        """Discard the current page without processing"""
        discarded = len(self.current_page)
        self.current_page = []
        logger.info(f"Discarded {discarded} queued operations")
        return discarded
    
    def retry_errors(self):
        """Retry operations that failed"""
        if not self.error_queue:
            logger.debug("No errors to retry")
            return
        
        error_count = len(self.error_queue)
        logger.info(f"Retrying {error_count} failed operations")
        
        # Move errors back to current page
        for operation, error in self.error_queue:
            self.current_page.append(operation)
        
        self.error_queue = []
        self.flush_page()
    
    def get_stats(self):
        """Get processing statistics"""
        total_ops = self.stats['operations_successful'] + self.stats['operations_failed']
        success_rate = (self.stats['operations_successful'] / max(1, total_ops)) * 100
        avg_time = self.stats['total_processing_time'] / max(1, self.stats['pages_processed'])
        
        return {
            **self.stats,
            'total_operations': total_ops,
            'success_rate': success_rate,
            'avg_page_time': avg_time,
            'current_page_size': len(self.current_page),
            'errors_pending': len(self.error_queue)
        }
    
    def _execute_operation(self, session, operation):
        """Execute a single operation using provided session"""
        if operation.operation_type == OperationType.CREATE:
            instance = operation.model_class(**operation.data)
            session.add(instance)
            logger.debug(f"Created {operation.model_class.__name__}")
            
        elif operation.operation_type == OperationType.UPDATE:
            instance = session.query(operation.model_class).get(operation.primary_key)
            if instance:
                for key, value in operation.data.items():
                    setattr(instance, key, value)
                logger.debug(f"Updated {operation.model_class.__name__}: {operation.primary_key}")
            else:
                raise ValueError(f"Record not found for update: {operation.primary_key}")
                
        elif operation.operation_type == OperationType.DELETE:
            instance = session.query(operation.model_class).get(operation.primary_key)
            if instance:
                session.delete(instance)
                logger.debug(f"Deleted {operation.model_class.__name__}: {operation.primary_key}")
            else:
                raise ValueError(f"Record not found for delete: {operation.primary_key}")
                
        elif operation.operation_type == OperationType.CUSTOM:
            if operation.callback:
                operation.callback(session, **operation.data)
                logger.debug("Executed custom operation")
            else:
                raise ValueError("Custom operation requires callback")

# Global queue instance for easy access
_global_queue = None

def get_queue(page_size=250):
    """Get the global operation queue"""
    global _global_queue
    if _global_queue is None:
        _global_queue = OperationQueue(page_size=page_size)
        logger.debug(f"Created global queue with page_size={page_size}")
    return _global_queue

def queue_create(model_class, **data):
    """Convenient function to queue create operations"""
    get_queue().create(model_class, **data)

def queue_update(model_class, primary_key, **data):
    """Convenient function to queue update operations"""
    get_queue().update(model_class, primary_key, **data)

def queue_delete(model_class, primary_key):
    """Convenient function to queue delete operations"""
    get_queue().delete(model_class, primary_key)

def commit_queue():
    """Commit the global queue"""
    queue = get_queue()
    if queue.current_page:
        logger.info(f"Committing global queue with {len(queue.current_page)} operations")
    queue.commit()

def queue_stats():
    """Get global queue statistics"""
    return get_queue().get_stats()

# Context manager for batch operations
@contextmanager
def batch_operations(page_size=250):
    """Context manager for batch operations with centralized session management"""
    logger.debug(f"Starting batch operations with page_size={page_size}")
    queue = OperationQueue(page_size=page_size, auto_commit=False)
    
    try:
        yield queue
        # Commit any remaining operations
        if queue.current_page:
            logger.debug(f"Committing final batch with {len(queue.current_page)} operations")
            queue.commit()
    except Exception as e:
        logger.error(f"Batch operation failed: {e}")
        queue.rollback_current_page()
        raise
    finally:
        # Always clear session cache after batch operations
        clear_session()
        logger.debug("Batch operations completed, session cache cleared")

# Enhanced model methods that use the queue
class QueuedModel:
    """Mixin for models to use the queue system"""
    
    def queue_save(self):
        """Queue save operation instead of immediate save"""
        pk_col_name = self.__class__.__table__.primary_key.columns[0].name
        
        if hasattr(self, pk_col_name) and getattr(self, pk_col_name):
            # Has primary key, it's an update
            pk_value = getattr(self, pk_col_name)
            data = {col.name: getattr(self, col.name) for col in self.__class__.__table__.columns 
                   if col.name != pk_col_name}
            queue_update(self.__class__, pk_value, **data)
            logger.debug(f"Queued update for {self.__class__.__name__}: {pk_value}")
        else:
            # No primary key, it's a create
            data = {col.name: getattr(self, col.name) for col in self.__class__.__table__.columns
                   if getattr(self, col.name) is not None}
            queue_create(self.__class__, **data)
            logger.debug(f"Queued create for {self.__class__.__name__}")
        return self
    
    def queue_delete(self):
        """Queue delete operation"""
        pk_col = self.__class__.__table__.primary_key.columns[0].name
        pk_value = getattr(self, pk_col)
        queue_delete(self.__class__, pk_value)
        logger.debug(f"Queued delete for {self.__class__.__name__}: {pk_value}")

# Test functions for queue system
def test_queue_basic_operations():
    """Test basic queue operations"""
    logger.info("=" * 60)
    logger.info("TESTING QUEUE BASIC OPERATIONS")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        from database_utils import init_db
        init_db()
        
        # Test 1: Create queue
        logger.info("TEST 1: Create operation queue")
        queue = OperationQueue(page_size=5, auto_commit=False)  # Small page for testing
        logger.info("✅ Queue created")
        
        # Test 2: Queue some operations
        logger.info("TEST 2: Queue operations")
        from models.tournament_models import Tournament, Organization
        
        # Queue multiple creates
        for i in range(3):
            queue.create(Organization, 
                        normalized_key=f"test_queue_{i}@example.com",
                        display_name=f"Queue Test Org {i}")
        
        for i in range(2):
            queue.create(Tournament,
                        id=f"queue_test_{i}",
                        name=f"Queue Test Tournament {i}",
                        num_attendees=i * 10,
                        tournament_state=3)
        
        logger.info(f"✅ Queued {len(queue.current_page)} operations")
        
        # Test 3: Manual commit
        logger.info("TEST 3: Manual commit")
        queue.commit()
        
        stats = queue.get_stats()
        if stats['operations_successful'] >= 5:
            logger.info(f"✅ Successfully processed {stats['operations_successful']} operations")
        else:
            logger.error(f"❌ Only {stats['operations_successful']} operations succeeded")
        
        # Test 4: Verify data in database
        logger.info("TEST 4: Verify database state")
        all_orgs = Organization.all()
        test_orgs = [org for org in all_orgs if 'test_queue_' in org.normalized_key]
        
        if len(test_orgs) >= 3:
            logger.info(f"✅ Found {len(test_orgs)} test organizations in database")
        else:
            logger.error(f"❌ Only found {len(test_orgs)} test organizations")
        
        # Cleanup
        logger.info("Cleaning up test data")
        for org in test_orgs:
            org.delete()
        
        all_tournaments = Tournament.all()
        test_tournaments = [t for t in all_tournaments if 'queue_test_' in t.id]
        for tournament in test_tournaments:
            tournament.delete()
        
        logger.info("✅ Queue basic operations test completed")
        
    except Exception as e:
        logger.error(f"Queue basic operations test failed: {e}")
        import traceback
        traceback.print_exc()

def test_batch_operations():
    """Test batch_operations context manager"""
    logger.info("=" * 60)
    logger.info("TESTING BATCH OPERATIONS CONTEXT MANAGER")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        from database_utils import init_db
        init_db()
        
        # Test 1: Basic batch operations
        logger.info("TEST 1: Basic batch context")
        
        with batch_operations(page_size=10) as queue:
            from models.tournament_models import Organization, Tournament
            
            # Add several operations
            for i in range(7):
                queue.create(Organization,
                           normalized_key=f"batch_test_{i}@example.com", 
                           display_name=f"Batch Test Org {i}")
            
            for i in range(3):
                queue.create(Tournament,
                           id=f"batch_test_{i}",
                           name=f"Batch Test Tournament {i}",
                           num_attendees=i * 20,
                           tournament_state=3)
            
            logger.info(f"Queued {len(queue.current_page)} operations in batch")
        
        # Verify operations completed
        logger.info("TEST 2: Verify batch completion")
        all_orgs = Organization.all()
        batch_orgs = [org for org in all_orgs if 'batch_test_' in org.normalized_key]
        
        if len(batch_orgs) >= 7:
            logger.info(f"✅ Batch operations successful: {len(batch_orgs)} organizations created")
        else:
            logger.error(f"❌ Batch operations failed: only {len(batch_orgs)} organizations found")
        
        # Test 3: Custom operations in batch
        logger.info("TEST 3: Custom operations")
        
        with batch_operations(page_size=5) as queue:
            def custom_operation(session, test_data, multiplier):
                # Custom operation that creates an organization with calculated data
                org = Organization(
                    normalized_key=f"custom_{test_data}@example.com",
                    display_name=f"Custom Org {test_data} x{multiplier}"
                )
                session.add(org)
                logger.debug(f"Custom operation executed: {test_data} x {multiplier}")
            
            # Queue custom operations
            for i in range(3):
                queue.custom(custom_operation, test_data=i, multiplier=i*2)
        
        # Verify custom operations
        all_orgs = Organization.all()
        custom_orgs = [org for org in all_orgs if 'custom_' in org.normalized_key]
        
        if len(custom_orgs) >= 3:
            logger.info(f"✅ Custom operations successful: {len(custom_orgs)} custom organizations")
        else:
            logger.error(f"❌ Custom operations failed: only {len(custom_orgs)} found")
        
        # Test 4: Error handling
        logger.info("TEST 4: Error handling")
        
        try:
            with batch_operations(page_size=3) as queue:
                # Create valid operation
                queue.create(Organization, 
                           normalized_key="error_test@example.com",
                           display_name="Error Test Org")
                
                # Create invalid operation (should fail)
                queue.create(Organization,
                           normalized_key="error_test@example.com",  # Duplicate key
                           display_name="Duplicate Org")
        except Exception:
            logger.info("✅ Error handling worked - batch rolled back on error")
        
        # Cleanup all test data
        logger.info("Cleaning up all test data")
        cleanup_test_organizations()
        cleanup_test_tournaments()
        
        logger.info("✅ Batch operations test completed")
        
    except Exception as e:
        logger.error(f"Batch operations test failed: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_organizations():
    """Clean up test organizations"""
    from models.tournament_models import Organization
    all_orgs = Organization.all()
    
    test_patterns = ['test_queue_', 'batch_test_', 'custom_', 'error_test']
    
    for org in all_orgs:
        for pattern in test_patterns:
            if pattern in org.normalized_key:
                org.delete()
                break

def cleanup_test_tournaments():
    """Clean up test tournaments"""
    from models.tournament_models import Tournament
    all_tournaments = Tournament.all()
    
    test_patterns = ['queue_test_', 'batch_test_']
    
    for tournament in all_tournaments:
        for pattern in test_patterns:
            if pattern in tournament.id:
                tournament.delete()
                break

def test_queue_stats():
    """Test queue statistics tracking"""
    logger.info("=" * 60)
    logger.info("TESTING QUEUE STATISTICS")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        from database_utils import init_db
        init_db()
        
        # Create queue and run operations
        queue = OperationQueue(page_size=3, auto_commit=True)
        
        from models.tournament_models import Organization
        
        # Add operations to trigger automatic page flushes
        for i in range(8):  # This should trigger multiple page flushes
            queue.create(Organization,
                        normalized_key=f"stats_test_{i}@example.com",
                        display_name=f"Stats Test Org {i}")
        
        # Get stats
        stats = queue.get_stats()
        
        logger.info("QUEUE STATISTICS:")
        logger.info(f"  Pages processed: {stats['pages_processed']}")
        logger.info(f"  Operations successful: {stats['operations_successful']}")
        logger.info(f"  Operations failed: {stats['operations_failed']}")
        logger.info(f"  Success rate: {stats['success_rate']:.1f}%")
        logger.info(f"  Average page time: {stats['avg_page_time']:.3f}s")
        logger.info(f"  Current page size: {stats['current_page_size']}")
        
        if stats['operations_successful'] >= 8:
            logger.info("✅ Queue statistics test passed")
        else:
            logger.error("❌ Queue statistics test failed")
        
        # Test global queue functions
        global_stats = queue_stats()
        if global_stats['total_operations'] > 0:
            logger.info("✅ Global queue functions working")
        else:
            logger.error("❌ Global queue functions failed")
        
        # Cleanup
        cleanup_test_organizations()
        
        logger.info("✅ Queue statistics test completed")
        
    except Exception as e:
        logger.error(f"Queue statistics test failed: {e}")
        import traceback
        traceback.print_exc()

def run_queue_tests():
    """Run all queue system tests"""
    try:
        logger.info("Starting queue system tests")
        
        # Run test suites
        test_queue_basic_operations()
        print()  # Spacing
        test_batch_operations() 
        print()  # Spacing
        test_queue_stats()
        
        logger.info("All queue tests completed")
        
    except Exception as e:
        logger.error(f"Queue test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing queue system...")
    run_queue_tests()

