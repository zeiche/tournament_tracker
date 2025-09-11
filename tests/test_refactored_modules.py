#!/usr/bin/env python3
"""
test_refactored_modules.py - Test suite for refactored OOP modules
Validates that all new services work correctly
"""
import unittest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

# Import new OOP modules
from database_service import DatabaseService
from visualizer import UnifiedVisualizer
from log_manager import LogManager, LogLevel
from sync_service import SyncOperation, SyncConfig
from publish_operation import PublishOperation, PublishConfig
from debug_refactored import DebugOperations


class TestDatabaseService(unittest.TestCase):
    """Test DatabaseService functionality"""
    
    def setUp(self):
        """Setup test database"""
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_service = DatabaseService(f'sqlite:///{self.test_db.name}')
        self.db_service.create_tables()
    
    def tearDown(self):
        """Cleanup test database"""
        self.db_service.dispose_connections()
        os.unlink(self.test_db.name)
    
    def test_singleton_pattern(self):
        """Test that DatabaseService is a singleton"""
        db1 = DatabaseService()
        db2 = DatabaseService()
        self.assertIs(db1, db2)
    
    def test_crud_operations(self):
        """Test CRUD operations"""
        from database.tournament_models import Organization
        
        # Create
        org = Organization(
            normalized_key='test_org',
            display_name='Test Organization'
        )
        created_org = self.db_service.create(org)
        self.assertIsNotNone(created_org.id)
        
        # Read
        retrieved_org = self.db_service.get(Organization, created_org.id)
        self.assertEqual(retrieved_org.display_name, 'Test Organization')
        
        # Update
        updated_org = self.db_service.update(retrieved_org, display_name='Updated Org')
        self.assertEqual(updated_org.display_name, 'Updated Org')
        
        # Delete
        success = self.db_service.delete(updated_org)
        self.assertTrue(success)
        
        # Verify deletion
        deleted_org = self.db_service.get(Organization, created_org.id)
        self.assertIsNone(deleted_org)
    
    def test_transaction_context(self):
        """Test transaction context manager"""
        from database.tournament_models import Organization
        
        # Test successful transaction
        with self.db_service.transaction() as session:
            org = Organization(
                normalized_key='trans_test',
                display_name='Transaction Test'
            )
            session.add(org)
        
        # Verify committed
        orgs = self.db_service.session.query(Organization).all()
        self.assertEqual(len(orgs), 1)
        
        # Test failed transaction (rollback)
        try:
            with self.db_service.transaction() as session:
                org2 = Organization(
                    normalized_key='trans_test2',
                    display_name='Transaction Test 2'
                )
                session.add(org2)
                raise Exception("Test exception")
        except:
            pass
        
        # Verify rollback
        orgs = self.db_service.session.query(Organization).all()
        self.assertEqual(len(orgs), 1)  # Still only 1
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked"""
        initial_stats = self.db_service._stats.copy()
        
        from database.tournament_models import Organization
        
        # Perform operations
        with self.db_service.transaction() as session:
            org = Organization(normalized_key='stats_test', display_name='Stats Test')
            session.add(org)
        
        # Check stats updated
        self.assertGreater(self.db_service._stats['commits'], initial_stats['commits'])
        self.assertGreater(self.db_service._stats['queries'], initial_stats['queries'])


class TestHTMLRenderer(unittest.TestCase):
    """Test HTMLRenderer functionality"""
    
    def setUp(self):
        """Setup HTML renderer"""
        self.renderer = HTMLRenderer(theme='dark')
    
    def test_theme_management(self):
        """Test theme switching"""
        self.assertEqual(self.renderer.theme, 'dark')
        
        self.renderer.set_theme('light')
        self.assertEqual(self.renderer.theme, 'light')
        
        # Test invalid theme
        with self.assertRaises(ValueError):
            self.renderer.set_theme('invalid_theme')
    
    def test_page_generation(self):
        """Test HTML page generation"""
        html = (self.renderer
                .start_page("Test Page", "Test Subtitle")
                .add_section("Section 1", "<p>Content</p>")
                .finish_page())
        
        self.assertIn("<title>Test Page</title>", html)
        self.assertIn("Test Subtitle", html)
        self.assertIn("Section 1", html)
        self.assertIn("<p>Content</p>", html)
    
    def test_table_generation(self):
        """Test table generation"""
        headers = ['Name', 'Value']
        rows = [['Item 1', '100'], ['Item 2', '200']]
        
        self.renderer.start_page("Table Test")
        self.renderer.add_table(headers, rows, table_id="test-table")
        html = self.renderer.finish_page()
        
        self.assertIn('<table id="test-table">', html)
        self.assertIn('<th>Name</th>', html)
        self.assertIn('<td>Item 1</td>', html)
    
    def test_stats_cards(self):
        """Test statistics cards generation"""
        stats = [
            {'title': 'Total', 'value': '100', 'subtitle': 'items'},
            {'title': 'Active', 'value': '75', 'subtitle': 'users'}
        ]
        
        self.renderer.start_page("Stats Test")
        self.renderer.add_stats_cards(stats)
        html = self.renderer.finish_page()
        
        self.assertIn('stat-card', html)
        self.assertIn('Total', html)
        self.assertIn('100', html)
    
    def test_component_registration(self):
        """Test custom component registration"""
        def custom_component(**kwargs):
            return f'<div class="custom">{kwargs.get("text", "")}</div>'
        
        self.renderer.register_component('custom', custom_component)
        
        self.renderer.start_page("Component Test")
        self.renderer.add_component('custom', text='Hello')
        html = self.renderer.finish_page()
        
        self.assertIn('<div class="custom">Hello</div>', html)


class TestLogManager(unittest.TestCase):
    """Test LogManager functionality"""
    
    def setUp(self):
        """Setup log manager"""
        self.temp_log = tempfile.NamedTemporaryFile(suffix='.log', delete=False)
        self.log_manager = LogManager(
            log_file=self.temp_log.name,
            level=LogLevel.DEBUG,
            enable_file=True,
            enable_console=False
        )
    
    def tearDown(self):
        """Cleanup"""
        os.unlink(self.temp_log.name)
    
    def test_singleton_pattern(self):
        """Test that LogManager is a singleton"""
        log1 = LogManager()
        log2 = LogManager()
        self.assertIs(log1, log2)
    
    def test_logging_levels(self):
        """Test different logging levels"""
        self.log_manager.debug("Debug message")
        self.log_manager.info("Info message")
        self.log_manager.warning("Warning message")
        self.log_manager.error("Error message")
        
        # Check statistics
        stats = self.log_manager.get_statistics()
        self.assertGreater(stats['log_counts']['debug'], 0)
        self.assertGreater(stats['log_counts']['info'], 0)
        self.assertGreater(stats['log_counts']['warning'], 0)
        self.assertGreater(stats['log_counts']['error'], 0)
    
    def test_context_manager(self):
        """Test logging context manager"""
        with self.log_manager.context("test_context"):
            self.log_manager.info("Inside context")
        
        # Check context was tracked
        log_content = Path(self.temp_log.name).read_text()
        self.assertIn("test_context", log_content)
    
    def test_module_logger(self):
        """Test module-specific logger"""
        module_logger = self.log_manager.get_logger('test_module')
        module_logger.info("Module message")
        
        stats = self.log_manager.get_statistics()
        self.assertIn('test_module', stats['module_loggers'])
    
    def test_specialized_logging(self):
        """Test specialized logging methods"""
        # API call logging
        self.log_manager.log_api_call('test_service', '/api/test', 0.5, 200)
        self.assertEqual(self.log_manager._stats['api_calls'], 1)
        
        # Database query logging
        self.log_manager.log_database_query('SELECT', 'users', 0.01, 10)
        self.assertEqual(self.log_manager._stats['db_queries'], 1)
        
        # Operation logging
        self.log_manager.log_operation('test_op', 'success', 1.0)
        
        # Exception logging
        try:
            raise ValueError("Test exception")
        except Exception as e:
            self.log_manager.log_exception(e, "test_context")


class TestSyncOperation(unittest.TestCase):
    """Test SyncOperation functionality"""
    
    def setUp(self):
        """Setup sync operation"""
        self.config = SyncConfig(
            page_size=10,
            fetch_standings=False,
            max_retries=1
        )
        self.sync_op = SyncOperation(self.config)
    
    def test_config_initialization(self):
        """Test configuration initialization"""
        self.assertEqual(self.sync_op.config.page_size, 10)
        self.assertFalse(self.sync_op.config.fetch_standings)
        self.assertEqual(self.sync_op.config.max_retries, 1)
    
    def test_statistics_tracking(self):
        """Test statistics are initialized"""
        stats = self.sync_op.stats
        self.assertEqual(stats.tournaments_fetched, 0)
        self.assertEqual(stats.api_calls, 0)
        self.assertIsNotNone(stats.start_time)
    
    def test_normalize_contact(self):
        """Test contact normalization"""
        # Email
        result = self.sync_op._normalize_contact('user@example.com', 'email')
        self.assertEqual(result, 'user@example.com')
        
        # Discord
        result = self.sync_op._normalize_contact('https://discord.gg/abc123', 'discord')
        self.assertEqual(result, 'discord:abc123')
        
        # Other
        result = self.sync_op._normalize_contact('Team Name', 'name')
        self.assertEqual(result, 'team_name')
    
    def test_points_calculation(self):
        """Test points calculation for placements"""
        self.assertEqual(self.sync_op._calculate_points(1), 10)
        self.assertEqual(self.sync_op._calculate_points(2), 8)
        self.assertEqual(self.sync_op._calculate_points(3), 6)
        self.assertEqual(self.sync_op._calculate_points(9), 1)


class TestPublishOperation(unittest.TestCase):
    """Test PublishOperation functionality"""
    
    def setUp(self):
        """Setup publish operation"""
        self.config = PublishConfig(
            publish_html=True,
            publish_json=True,
            min_attendance=10
        )
        self.publish_op = PublishOperation(self.config)
    
    def test_config_initialization(self):
        """Test configuration initialization"""
        self.assertTrue(self.publish_op.config.publish_html)
        self.assertTrue(self.publish_op.config.publish_json)
        self.assertEqual(self.publish_op.config.min_attendance, 10)
    
    def test_statistics_initialization(self):
        """Test statistics initialization"""
        stats = self.publish_op.stats
        self.assertEqual(stats.organizations_published, 0)
        self.assertEqual(stats.tournaments_included, 0)
        self.assertIsNotNone(stats.start_time)


class TestDebugOperations(unittest.TestCase):
    """Test DebugOperations functionality"""
    
    def setUp(self):
        """Setup debug operations"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.debug_ops = DebugOperations(
            database_url=f'sqlite:///{self.temp_db.name}',
            force_recreate=True
        )
    
    def tearDown(self):
        """Cleanup"""
        os.unlink(self.temp_db.name)
    
    def test_database_setup(self):
        """Test database setup"""
        success = self.debug_ops.setup_fresh_database()
        self.assertTrue(success)
        self.assertIn("Database tables initialized", self.debug_ops.operations_log)
    
    def test_test_organization_creation(self):
        """Test creating test organizations"""
        self.debug_ops.setup_fresh_database()
        result = self.debug_ops.create_test_organizations()
        
        self.assertEqual(result['count'], 4)
        self.assertEqual(len(result['organizations']), 4)
    
    def test_integrity_verification(self):
        """Test database integrity verification"""
        self.debug_ops.setup_fresh_database()
        result = self.debug_ops.verify_database_integrity()
        
        self.assertTrue(result['tables_exist'])
        self.assertIn('table_counts', result)


class TestIntegration(unittest.TestCase):
    """Integration tests for all modules working together"""
    
    def test_full_workflow(self):
        """Test a complete workflow using all modules"""
        # Setup
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        
        try:
            # Initialize services
            db = DatabaseService(f'sqlite:///{temp_db.name}')
            db.create_tables()
            
            logger = LogManager(enable_console=False)
            logger.info("Starting integration test")
            
            # Create test data
            from database.tournament_models import Organization, Tournament
            
            org = Organization(
                normalized_key='test_org',
                display_name='Test Organization'
            )
            db.create(org)
            
            tournament = Tournament(
                id=1,
                name='Test Tournament',
                num_attendees=50,
                normalized_contact=org.normalized_key,
                start_at=datetime.now() - timedelta(days=5)
            )
            db.create(tournament)
            
            # Generate HTML report
            renderer = HTMLRenderer()
            html = (renderer
                   .start_page("Integration Test")
                   .add_section("Organizations", f"<p>{org.display_name}</p>")
                   .add_table(['Tournament', 'Attendees'],
                            [[tournament.name, tournament.num_attendees]])
                   .finish_page())
            
            # Verify output
            self.assertIn("Integration Test", html)
            self.assertIn("Test Organization", html)
            self.assertIn("Test Tournament", html)
            
            # Check logs
            stats = logger.get_statistics()
            self.assertGreater(stats['total_logs'], 0)
            
        finally:
            os.unlink(temp_db.name)


def run_tests():
    """Run all tests and generate report"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseService))
    suite.addTests(loader.loadTestsFromTestCase(TestHTMLRenderer))
    suite.addTests(loader.loadTestsFromTestCase(TestLogManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSyncOperation))
    suite.addTests(loader.loadTestsFromTestCase(TestPublishOperation))
    suite.addTests(loader.loadTestsFromTestCase(TestDebugOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)