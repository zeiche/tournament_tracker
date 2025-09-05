#!/usr/bin/env python3
"""
debug_refactored.py - Database Debug Operations
Modern OOP replacement for debug.py - eliminates all raw SQL
Uses DatabaseService and OOP patterns throughout
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_service import DatabaseService
from log_manager import LogManager, LogLevel
from tournament_models import Tournament, Organization


class DebugOperations:
    """Encapsulates all debug operations using modern OOP patterns"""
    
    def __init__(self, database_url: Optional[str] = None, force_recreate: bool = False):
        """Initialize debug operations"""
        self.db = DatabaseService(database_url)
        self.logger = LogManager().get_logger('debug')
        self.force_recreate = force_recreate
        
        # Track operations performed
        self.operations_log = []
    
    def setup_fresh_database(self) -> bool:
        """Create fresh database or wipe existing one"""
        db_path = 'tournament_tracker.db'
        
        if self.force_recreate and Path(db_path).exists():
            self.logger.info(f"Force recreate - removing existing database: {db_path}")
            Path(db_path).unlink()
            self.operations_log.append("Removed existing database")
        
        if Path(db_path).exists():
            self.logger.info(f"Database already exists: {db_path}")
            self.operations_log.append("Using existing database")
        else:
            self.logger.info(f"Creating fresh database: {db_path}")
            self.operations_log.append("Created fresh database")
        
        try:
            # Create tables using DatabaseService
            self.db.create_tables()
            self.logger.info("✅ Database tables initialized")
            self.operations_log.append("Database tables initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            self.operations_log.append(f"Database initialization failed: {e}")
            return False
    
    def create_test_organizations(self) -> Dict[str, Any]:
        """Create test organizations with problematic names"""
        self.logger.info("Creating test organizations...")
        
        test_data = [
            {
                'normalized_key': 'user@email.com',
                'display_name': 'user@email.com',
                'contacts': [
                    ('user@email.com', 'email')
                ]
            },
            {
                'normalized_key': 'discord:abc123',
                'display_name': 'https://discord.gg/abc123',
                'contacts': [
                    ('https://discord.gg/abc123', 'discord')
                ]
            },
            {
                'normalized_key': 'fgc@gmail.com',
                'display_name': 'fgc@gmail.com',
                'contacts': [
                    ('fgc@gmail.com', 'email')
                ]
            },
            {
                'normalized_key': 'team_liquid',
                'display_name': 'Team Liquid',
                'contacts': [
                    ('Team Liquid', 'name'),
                    ('team@liquid.com', 'email')
                ]
            }
        ]
        
        created_orgs = []
        
        with self.db.transaction() as session:
            for org_data in test_data:
                # Create organization using ORM
                org = Organization(
                    normalized_key=org_data['normalized_key'],
                    display_name=org_data['display_name']
                )
                session.add(org)
                session.flush()  # Get the ID
                
                # Add contacts to organization
                for contact_value, contact_type in org_data['contacts']:
                    # Use organization's add_contact method if available
                    # or store contacts in a different way
                    pass  # Skip contacts for now since OrganizationContact not in models
                
                created_orgs.append(org)
                self.logger.debug(f"   Created: {org_data['display_name']}")
        
        self.logger.info(f"✅ Created {len(created_orgs)} test organizations")
        self.operations_log.append(f"Created {len(created_orgs)} test organizations")
        
        return {
            'count': len(created_orgs),
            'organizations': [
                {'id': org.id, 'key': org.normalized_key, 'name': org.display_name}
                for org in created_orgs
            ]
        }
    
    def test_session_cache_behavior(self) -> Dict[str, Any]:
        """Test session cache behavior with modern patterns"""
        self.logger.info("Testing session cache behavior")
        results = []
        
        with self.logger.manager.context("session_cache_test"):
            # Test 1: Initial state
            org = self.db.session.query(Organization).filter_by(
                normalized_key='user@email.com'
            ).first()
            
            if org:
                initial_name = org.display_name
                results.append({
                    'test': 'initial_state',
                    'name': initial_name,
                    'status': 'success'
                })
                self.logger.debug(f"Initial name: {initial_name}")
                
                # Test 2: Update using DatabaseService
                new_name = 'Test Organization Updated'
                self.db.update(org, display_name=new_name)
                results.append({
                    'test': 'update_via_service',
                    'old_name': initial_name,
                    'new_name': new_name,
                    'status': 'success'
                })
                
                # Test 3: Verify update with fresh session
                self.db.clear_cache()
                org_fresh = self.db.get(Organization, org.id)
                
                if org_fresh and org_fresh.display_name == new_name:
                    results.append({
                        'test': 'verify_after_cache_clear',
                        'name': org_fresh.display_name,
                        'status': 'success',
                        'cache_cleared': True
                    })
                    self.logger.info("✅ Cache behavior test passed")
                else:
                    results.append({
                        'test': 'verify_after_cache_clear',
                        'name': org_fresh.display_name if org_fresh else None,
                        'status': 'failed',
                        'error': 'Name not updated after cache clear'
                    })
                    self.logger.error("❌ Cache behavior test failed")
            else:
                results.append({
                    'test': 'initial_state',
                    'status': 'failed',
                    'error': 'Organization not found'
                })
        
        return {'tests': results, 'passed': all(r['status'] == 'success' for r in results)}
    
    def test_multiple_rapid_changes(self) -> Dict[str, Any]:
        """Test multiple rapid changes using OOP patterns"""
        self.logger.info("Testing multiple rapid changes")
        
        changes = [
            ('user@email.com', 'Email User Gaming'),
            ('discord:abc123', 'Discord Community Hub'),
            ('fgc@gmail.com', 'Fighting Game Central'),
            ('team_liquid', 'Team Liquid Esports')
        ]
        
        results = []
        
        with self.logger.manager.context("rapid_changes_test"):
            for normalized_key, new_name in changes:
                org = self.db.session.query(Organization).filter_by(
                    normalized_key=normalized_key
                ).first()
                
                if org:
                    old_name = org.display_name
                    self.db.update(org, display_name=new_name)
                    
                    # Verify immediately
                    self.db.clear_cache()
                    org_verify = self.db.get(Organization, org.id)
                    
                    success = org_verify and org_verify.display_name == new_name
                    results.append({
                        'key': normalized_key,
                        'old_name': old_name,
                        'new_name': new_name,
                        'verified_name': org_verify.display_name if org_verify else None,
                        'success': success
                    })
                    
                    if success:
                        self.logger.debug(f"✅ {normalized_key}: {old_name} -> {new_name}")
                    else:
                        self.logger.error(f"❌ {normalized_key}: Update failed")
        
        passed = all(r['success'] for r in results)
        self.logger.info(f"Rapid changes test: {'✅ PASSED' if passed else '❌ FAILED'}")
        
        return {
            'changes': results,
            'passed': passed,
            'success_rate': sum(1 for r in results if r['success']) / len(results) * 100
        }
    
    def verify_database_integrity(self) -> Dict[str, Any]:
        """Verify database integrity using ORM"""
        self.logger.info("Verifying database integrity")
        
        integrity_checks = {
            'tables_exist': False,
            'foreign_keys_valid': True,
            'orphaned_records': [],
            'duplicate_keys': []
        }
        
        with self.db.fresh_session() as session:
            # Check tables exist
            table_sizes = self.db.get_table_sizes()
            integrity_checks['tables_exist'] = len(table_sizes) > 0
            integrity_checks['table_counts'] = table_sizes
            
            # Check for orphaned tournament placements
            from tournament_models import TournamentPlacement
            
            orphaned = session.query(TournamentPlacement).filter(
                ~TournamentPlacement.tournament_id.in_(
                    session.query(Tournament.id)
                )
            ).count()
            
            if orphaned > 0:
                integrity_checks['orphaned_records'].append(
                    f"TournamentPlacement: {orphaned} records without tournament"
                )
                integrity_checks['foreign_keys_valid'] = False
            
            # Check for duplicate organization keys
            from sqlalchemy import func
            
            duplicates = session.query(
                Organization.normalized_key,
                func.count(Organization.id).label('count')
            ).group_by(
                Organization.normalized_key
            ).having(
                func.count(Organization.id) > 1
            ).all()
            
            for key, count in duplicates:
                integrity_checks['duplicate_keys'].append({
                    'key': key,
                    'count': count
                })
        
        # Determine overall status
        integrity_checks['status'] = (
            'healthy' if integrity_checks['tables_exist'] 
            and integrity_checks['foreign_keys_valid'] 
            and not integrity_checks['duplicate_keys']
            else 'issues_found'
        )
        
        self.logger.info(f"Database integrity: {integrity_checks['status']}")
        return integrity_checks
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = self.db.get_database_stats()
        
        # Add debug-specific stats
        stats['debug_operations'] = {
            'operations_performed': len(self.operations_log),
            'operations_log': self.operations_log
        }
        
        return stats
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all debug tests"""
        self.logger.info("="*60)
        self.logger.info("RUNNING ALL DEBUG TESTS")
        self.logger.info("="*60)
        
        all_results = {}
        
        # Setup database
        all_results['database_setup'] = self.setup_fresh_database()
        
        # Create test data
        all_results['test_organizations'] = self.create_test_organizations()
        
        # Run tests
        all_results['session_cache_test'] = self.test_session_cache_behavior()
        all_results['rapid_changes_test'] = self.test_multiple_rapid_changes()
        all_results['integrity_check'] = self.verify_database_integrity()
        all_results['statistics'] = self.get_database_statistics()
        
        # Summary
        tests_passed = (
            all_results.get('session_cache_test', {}).get('passed', False) and
            all_results.get('rapid_changes_test', {}).get('passed', False) and
            all_results.get('integrity_check', {}).get('status') == 'healthy'
        )
        
        all_results['summary'] = {
            'all_tests_passed': tests_passed,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info("="*60)
        self.logger.info(f"TEST RESULTS: {'✅ ALL PASSED' if tests_passed else '❌ SOME FAILED'}")
        self.logger.info("="*60)
        
        return all_results


def main():
    """Main entry point for debug operations"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Database debug operations')
    parser.add_argument('--force-recreate', action='store_true',
                       help='Force recreate database')
    parser.add_argument('--test', choices=['cache', 'rapid', 'integrity', 'all'],
                       default='all', help='Test to run')
    parser.add_argument('--output-json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Run debug operations
    debug = DebugOperations(force_recreate=args.force_recreate)
    
    if args.test == 'all':
        results = debug.run_all_tests()
    elif args.test == 'cache':
        debug.setup_fresh_database()
        debug.create_test_organizations()
        results = debug.test_session_cache_behavior()
    elif args.test == 'rapid':
        debug.setup_fresh_database()
        debug.create_test_organizations()
        results = debug.test_multiple_rapid_changes()
    elif args.test == 'integrity':
        results = debug.verify_database_integrity()
    
    # Output results
    if args.output_json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print("\nDebug Operations Complete")
        print(f"Operations performed: {len(debug.operations_log)}")
        for op in debug.operations_log:
            print(f"  - {op}")


if __name__ == "__main__":
    main()