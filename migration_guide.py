#!/usr/bin/env python3
"""
migration_guide.py - Import migration guide and compatibility layer
Maps old procedural imports to new OOP services
Run this to update imports across the codebase
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


# Mapping of old imports to new ones
IMPORT_MAPPINGS = {
    # Database operations
    'from database_utils import': 'from database_service import DatabaseService',
    'from session_utils import': 'from database_service import DatabaseService',
    'get_session()': 'DatabaseService().session',
    'get_all_organizations()': 'DatabaseService().get_organizations_with_stats()',
    'save_organization_name': 'DatabaseService().update_organization_name',
    'init_db()': 'DatabaseService().create_tables()',
    
    # HTML generation
    'from html_utils import': 'from html_renderer import HTMLRenderer',
    'get_page_header': 'HTMLRenderer().start_page',
    'get_page_footer': 'HTMLRenderer().finish_page',
    'format_table': 'HTMLRenderer().add_table',
    'get_nav_links': 'HTMLRenderer().add_nav_links',
    
    # Logging
    'from log_utils import': 'from log_manager import LogManager',
    'log_info': 'LogManager().info',
    'log_debug': 'LogManager().debug',
    'log_error': 'LogManager().error',
    'log_warn': 'LogManager().warning',
    'LogContext': 'LogManager().context',
    
    # Sync operations
    'from startgg_service import startgg_service sync_from_startgg': 'from sync_service import sync_service SyncOperation',
    'sync_from_startgg()': 'SyncOperation().execute()',
    
    # Publishing
    'from shopify_service import shopify_service': 'from publish_operation import PublishOperation',
    'from shopify_service import shopify_service': 'from publish_operation import PublishOperation',
    'publish_table': 'PublishOperation().execute',
    'get_legacy_attendance_data': 'PublishOperation()._gather_tournament_data',
}


class MigrationHelper:
    """Helper class to migrate old imports to new OOP patterns"""
    
    def __init__(self, dry_run: bool = True):
        """Initialize migration helper"""
        self.dry_run = dry_run
        self.files_to_update = []
        self.changes_made = []
    
    def scan_directory(self, directory: str = '.') -> List[Tuple[str, List[str]]]:
        """Scan directory for files needing updates"""
        issues_found = []
        
        for py_file in Path(directory).rglob('*.py'):
            # Skip our new files
            if py_file.name in [
                'database_service.py', 'html_renderer.py', 'log_manager.py',
                'sync_operation.py', 'publish_operation.py', 'debug_refactored.py',
                'migration_guide.py'
            ]:
                continue
            
            issues = self.scan_file(py_file)
            if issues:
                issues_found.append((str(py_file), issues))
        
        return issues_found
    
    def scan_file(self, filepath: Path) -> List[str]:
        """Scan a file for old imports"""
        issues = []
        
        try:
            content = filepath.read_text()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for old_pattern in IMPORT_MAPPINGS.keys():
                    if old_pattern in line:
                        issues.append(f"Line {i}: {line.strip()}")
                        break
        
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")
        
        return issues
    
    def update_file(self, filepath: Path) -> Dict[str, any]:
        """Update a file with new imports"""
        changes = {
            'file': str(filepath),
            'changes': [],
            'success': False
        }
        
        try:
            content = filepath.read_text()
            original_content = content
            
            # Apply replacements
            for old_pattern, new_pattern in IMPORT_MAPPINGS.items():
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    changes['changes'].append(f"{old_pattern} -> {new_pattern}")
            
            # Write back if changes were made
            if content != original_content:
                if not self.dry_run:
                    # Backup original
                    backup_path = filepath.with_suffix('.py.backup')
                    backup_path.write_text(original_content)
                    
                    # Write updated content
                    filepath.write_text(content)
                
                changes['success'] = True
            
        except Exception as e:
            changes['error'] = str(e)
        
        return changes
    
    def generate_compatibility_layer(self) -> str:
        """Generate compatibility layer for gradual migration"""
        compatibility = '''"""
compatibility.py - Backward compatibility layer
Import this to maintain compatibility during migration
"""

# Database compatibility
from database_service import DatabaseService

db_service = DatabaseService()
get_session = lambda: db_service.session
init_db = db_service.create_tables

def get_all_organizations():
    """Compatibility wrapper"""
    return db_service.get_organizations_with_stats()

def save_organization_name(key, name):
    """Compatibility wrapper"""
    org = db_service.session.query(Organization).filter_by(
        normalized_key=key
    ).first()
    if org:
        return db_service.update_organization_name(org.id, name)
    return False

# HTML compatibility
from html_renderer import HTMLRenderer

_renderer = HTMLRenderer()

def get_page_header(title, subtitle=None):
    """Compatibility wrapper"""
    _renderer.start_page(title, subtitle)
    return ""  # Return empty since renderer handles internally

def get_page_footer():
    """Compatibility wrapper"""
    return _renderer.finish_page()

def format_table(headers, rows, row_formatter=None):
    """Compatibility wrapper"""
    return _renderer._data_table_component(headers, rows, row_formatter=row_formatter)

# Logging compatibility
from log_manager import LogManager

log_manager = LogManager()
log_info = log_manager.info
log_debug = log_manager.debug
log_error = log_manager.error
log_warn = log_manager.warning
LogContext = log_manager.context

# Sync compatibility
from sync_service import sync_service sync_from_startgg

# Publish compatibility
from publish_operation import publish_to_shopify
'''
        return compatibility
    
    def run_migration(self, directory: str = '.') -> Dict[str, any]:
        """Run the migration process"""
        print("🔍 Scanning for files to update...")
        issues = self.scan_directory(directory)
        
        results = {
            'files_scanned': 0,
            'files_with_issues': len(issues),
            'files_updated': 0,
            'dry_run': self.dry_run,
            'issues': issues,
            'updates': []
        }
        
        if not issues:
            print("✅ No files need updating!")
            return results
        
        print(f"Found {len(issues)} files with old imports:")
        for filepath, file_issues in issues:
            print(f"\n📄 {filepath}:")
            for issue in file_issues[:3]:  # Show first 3 issues
                print(f"   {issue}")
            if len(file_issues) > 3:
                print(f"   ... and {len(file_issues) - 3} more")
        
        if not self.dry_run:
            print("\n🔄 Updating files...")
            for filepath, _ in issues:
                update_result = self.update_file(Path(filepath))
                results['updates'].append(update_result)
                if update_result['success']:
                    results['files_updated'] += 1
                    print(f"✅ Updated {filepath}")
                else:
                    print(f"❌ Failed to update {filepath}: {update_result.get('error')}")
        else:
            print("\n⚠️  DRY RUN - No files were modified")
            print("Run with --update to apply changes")
        
        return results


def main():
    """Main migration script"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Migrate old imports to new OOP patterns')
    parser.add_argument('--update', action='store_true',
                       help='Actually update files (default is dry run)')
    parser.add_argument('--directory', default='.',
                       help='Directory to scan (default: current)')
    parser.add_argument('--generate-compatibility', action='store_true',
                       help='Generate compatibility layer file')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    if args.generate_compatibility:
        helper = MigrationHelper()
        compatibility_code = helper.generate_compatibility_layer()
        
        with open('compatibility.py', 'w') as f:
            f.write(compatibility_code)
        
        print("✅ Generated compatibility.py")
        print("   Import this file to maintain backward compatibility during migration")
        return
    
    # Run migration
    helper = MigrationHelper(dry_run=not args.update)
    results = helper.run_migration(args.directory)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Files scanned: {results['files_scanned']}")
        print(f"Files with old imports: {results['files_with_issues']}")
        if not args.update:
            print(f"Files that would be updated: {results['files_with_issues']}")
            print("\n⚠️  This was a DRY RUN - no files were modified")
            print("   Run with --update to apply changes")
        else:
            print(f"Files updated: {results['files_updated']}")
            print(f"Files backed up: {results['files_updated']}")


if __name__ == "__main__":
    main()