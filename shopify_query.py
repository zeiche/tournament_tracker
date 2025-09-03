"""
shopify_query.py - Shopify Publishing Integration
Fixed to use centralized database functions and logging
"""
import os

# Import centralized systems
from log_utils import log_info, log_debug, log_error, LogContext
from database_utils import get_attendance_rankings

def get_legacy_attendance_data():
    """
    Convert SQLAlchemy data to legacy format for existing Shopify code
    Returns data in the format expected by existing publishing system
    """
    log_info("Converting tournament data to legacy Shopify format", "shopify")
    
    with LogContext("Convert to legacy format"):
        rankings = get_attendance_rankings()
        
        if not rankings:
            log_error("No attendance data available for Shopify conversion", "shopify")
            return {}, {}
        
        # Convert to old format (attendance_tracker, org_names)
        attendance_tracker = {}
        org_names = {}
        
        log_debug(f"Processing {len(rankings)} organizations for legacy format", "shopify")
        
        for rank, org_data in enumerate(rankings, 1):
            key = org_data['normalized_key']
            
            # Attendance tracker format
            attendance_tracker[key] = {
                'tournaments': list(range(org_data.get('tournament_count', 0))),  # Fake list for count
                'total_attendance': org_data.get('total_attendance', 0),
                'contacts': org_data.get('contacts', [])
            }
            
            # Organization names format (only if display name differs from key)
            if org_data['display_name'] != key:
                org_names[f"org_{rank}"] = {
                    'display_name': org_data['display_name'],
                    'contacts': org_data['contacts']
                }
        
        log_info(f"Legacy format created: {len(attendance_tracker)} attendance entries, {len(org_names)} org names", "shopify")
        
        # Log sample data for debugging
        if attendance_tracker:
            sample_key = list(attendance_tracker.keys())[0]
            sample_data = attendance_tracker[sample_key]
            log_debug(f"Sample attendance entry: {sample_key} -> {sample_data['total_attendance']} attendance", "shopify")
        
        if org_names:
            sample_org_key = list(org_names.keys())[0]
            sample_org = org_names[sample_org_key]
            log_debug(f"Sample org name mapping: {sample_org['display_name']}", "shopify")
        
        return attendance_tracker, org_names

def publish_to_shopify():
    """Publish tournament data to Shopify with centralized logging"""
    log_info("Starting Shopify publishing workflow", "shopify")
    
    with LogContext("Publish tournament data to Shopify"):
        try:
            # Convert to legacy format for existing Shopify code
            log_debug("Converting data to legacy format", "shopify")
            attendance_tracker, org_names = get_legacy_attendance_data()
            
            if not attendance_tracker:
                log_error("No tournament data available for publishing", "shopify")
                return False
            
            # Import and use existing Shopify publisher
            try:
                log_debug("Loading Shopify publisher module", "shopify")
                from shopify_publish import publish_table
                
                log_info("Publishing to Shopify store", "shopify")
                success = publish_table(attendance_tracker, org_names)
                
                if success:
                    log_info("Successfully published tournament data to Shopify", "shopify")
                    return True
                else:
                    log_error("Shopify publishing failed - check shopify_publish.py", "shopify")
                    return False
                    
            except ImportError as e:
                log_error(f"Shopify publisher module not available: {e}", "shopify")
                log_error("Check if shopify_publish.py exists and is properly configured", "shopify")
                return False
                
        except Exception as e:
            log_error(f"Shopify publishing failed: {e}", "shopify")
            return False

def validate_shopify_config():
    """Validate Shopify configuration"""
    log_debug("Validating Shopify configuration", "shopify")
    
    required_vars = ['ACCESS_TOKEN']
    missing = []
    
    for var_name in required_vars:
        if not os.getenv(var_name):
            missing.append(var_name)
    
    if missing:
        error_msg = f"Required Shopify configuration missing: {', '.join(missing)}"
        log_error(error_msg, "shopify")
        return False, error_msg
    
    log_info("Shopify configuration validated", "shopify")
    return True, "Configuration valid"

def test_shopify_data_conversion():
    """Test conversion to legacy Shopify format"""
    log_info("=" * 60, "test")
    log_info("TESTING SHOPIFY DATA CONVERSION", "test")
    log_info("=" * 60, "test")
    
    try:
        # Initialize database
        from database_utils import init_db
        init_db()
        
        # Test 1: Basic conversion
        log_info("TEST 1: Legacy format conversion", "test")
        attendance_tracker, org_names = get_legacy_attendance_data()
        
        if attendance_tracker:
            log_info(f"✅ Conversion successful: {len(attendance_tracker)} attendance entries", "test")
            
            # Validate format structure
            sample_key = list(attendance_tracker.keys())[0]
            sample_data = attendance_tracker[sample_key]
            
            required_fields = ['tournaments', 'total_attendance', 'contacts']
            has_all_fields = all(field in sample_data for field in required_fields)
            
            if has_all_fields:
                log_info("✅ Legacy format structure is correct", "test")
            else:
                log_error("❌ Legacy format structure is incorrect", "test")
                log_error(f"Sample data fields: {list(sample_data.keys())}", "test")
        else:
            log_error("❌ No data converted", "test")
        
        # Test 2: Organization names mapping
        log_info("TEST 2: Organization names mapping", "test")
        
        if org_names:
            log_info(f"✅ Organization names mapped: {len(org_names)} entries", "test")
            
            # Validate org names structure
            sample_org_key = list(org_names.keys())[0]
            sample_org = org_names[sample_org_key]
            
            required_org_fields = ['display_name', 'contacts']
            has_org_fields = all(field in sample_org for field in required_org_fields)
            
            if has_org_fields:
                log_info("✅ Organization names format is correct", "test")
            else:
                log_error("❌ Organization names format is incorrect", "test")
        else:
            log_info("No organization name mappings (all orgs use raw keys)", "test")
        
        log_info("✅ Shopify data conversion tests completed", "test")
        
    except Exception as e:
        log_error(f"Shopify data conversion test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_shopify_config_validation():
    """Test Shopify configuration validation"""
    log_info("=" * 60, "test")
    log_info("TESTING SHOPIFY CONFIG VALIDATION", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test 1: Check current config
        log_info("TEST 1: Current configuration", "test")
        
        is_valid, message = validate_shopify_config()
        
        if is_valid:
            log_info(f"✅ Shopify configuration valid: {message}", "test")
        else:
            log_warn(f"Shopify configuration invalid: {message}", "test")
            log_warn("Set ACCESS_TOKEN environment variable for Shopify publishing", "test")
        
        # Test 2: Test with missing config
        log_info("TEST 2: Missing configuration handling", "test")
        
        # Temporarily clear ACCESS_TOKEN
        original_token = os.getenv('ACCESS_TOKEN')
        if 'ACCESS_TOKEN' in os.environ:
            del os.environ['ACCESS_TOKEN']
        
        is_valid_missing, message_missing = validate_shopify_config()
        
        if not is_valid_missing:
            log_info("✅ Correctly detected missing ACCESS_TOKEN", "test")
        else:
            log_error("❌ Should have failed with missing ACCESS_TOKEN", "test")
        
        # Restore ACCESS_TOKEN if it existed
        if original_token:
            os.environ['ACCESS_TOKEN'] = original_token
        
        log_info("✅ Shopify config validation tests completed", "test")
        
    except Exception as e:
        log_error(f"Shopify config validation test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_shopify_integration():
    """Test complete Shopify integration workflow"""
    log_info("=" * 60, "test")
    log_info("TESTING SHOPIFY INTEGRATION WORKFLOW", "test")
    log_info("=" * 60, "test")
    
    try:
        # Initialize database
        from database_utils import init_db
        init_db()
        
        # Test 1: Check if we have data to publish
        log_info("TEST 1: Data availability check", "test")
        
        stats = get_summary_stats()
        if stats['total_organizations'] > 0:
            log_info(f"✅ Data available: {stats['total_organizations']} organizations", "test")
        else:
            log_warn("No organization data available - create some test data first", "test")
            return
        
        # Test 2: Data conversion
        log_info("TEST 2: Legacy format conversion", "test")
        attendance_tracker, org_names = get_legacy_attendance_data()
        
        if attendance_tracker:
            log_info("✅ Data conversion successful", "test")
        else:
            log_error("❌ Data conversion failed", "test")
            return
        
        # Test 3: Config validation
        log_info("TEST 3: Configuration validation", "test")
        is_valid, message = validate_shopify_config()
        
        if not is_valid:
            log_warn(f"Shopify not configured: {message}", "test")
            log_warn("Skipping actual publishing test", "test")
            return
        
        # Test 4: Actual publishing (if configured)
        log_info("TEST 4: Actual Shopify publishing", "test")
        
        try:
            success = publish_to_shopify()
            
            if success:
                log_info("✅ Shopify publishing successful", "test")
            else:
                log_error("❌ Shopify publishing failed", "test")
                
        except Exception as e:
            log_error(f"Shopify publishing error: {e}", "test")
        
        log_info("✅ Shopify integration tests completed", "test")
        
    except Exception as e:
        log_error(f"Shopify integration test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def run_shopify_tests():
    """Run all Shopify query tests"""
    try:
        # Initialize logging
        from log_utils import init_logging, LogLevel
        init_logging(console=True, level=LogLevel.DEBUG, debug_file="shopify_test.txt")
        
        log_info("Starting Shopify query tests", "test")
        
        # Run test suites
        test_shopify_data_conversion()
        print()  # Spacing  
        test_shopify_config_validation()
        print()  # Spacing
        test_shopify_integration()
        
        log_info("All Shopify tests completed - check shopify_test.txt for details", "test")
        
    except Exception as e:
        log_error(f"Shopify test suite failed: {e}", "test")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing Shopify query integration...")
    run_shopify_tests()

