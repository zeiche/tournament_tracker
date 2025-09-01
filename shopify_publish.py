"""
shopify_publish.py - Shopify Publishing Operations
Handles actual publishing to Shopify store using database_utils layer
"""
from datetime import datetime
from database_utils import get_attendance_rankings, get_summary_stats, init_db
from shopify_query import get_legacy_attendance_data
from operation_utils import BaseProcessor, handle_operation_error, print_operation_start

class ShopifyPublisher(BaseProcessor):
    """Handles publishing tournament data to Shopify"""
    
    def __init__(self):
        super().__init__("Shopify publishing")
        
        # Additional publish-specific stats
        self.publish_stats = {
            'tables_published': 0,
            'data_size': 0,
            'last_publish_time': None
        }
    
    def execute(self, limit=None):
        """Execute Shopify publishing operation"""
        print_operation_start("Shopify publishing", f"limit={limit}")
        
        # Get data through database utils layer
        attendance_tracker, org_names = get_legacy_attendance_data()
        self.publish_stats['data_size'] = len(attendance_tracker)
        
        try:
            success = self._publish_table_to_store(attendance_tracker, org_names)
            
            if success:
                print("Successfully published to Shopify")
                return True
            else:
                print("Shopify publishing failed")
                return False
                
        except ImportError:
            error_msg = "Shopify API module not available - install shopify_api module"
            handle_operation_error("Shopify import", error_msg)
            return False
    
    def publish_tournament_table(self, limit=None):
        """
        Publish tournament attendance table to Shopify
        Uses BaseProcessor.run() for error handling and stats
        """
        return self.run(limit=limit)
    
    def _publish_table_to_store(self, attendance_tracker, org_names):
        """
        Internal method to handle actual Shopify API calls
        This would interface with Shopify's API or webhook system
        """
        # Placeholder for actual Shopify publishing logic
        # In real implementation, this would:
        # 1. Format data for Shopify API
        # 2. Make authenticated requests to Shopify
        # 3. Update specific pages/products
        # 4. Handle rate limiting and retries
        
        print("Formatting data for Shopify...")
        print(f"   Organizations: {len(attendance_tracker)}")
        print(f"   Name mappings: {len(org_names)}")
        
        # Simulate publishing process
        import time
        time.sleep(0.5)  # Simulate API call time
        
        # Return success for now - replace with real Shopify logic
        return True
    
    def get_publish_summary(self):
        """Get publishing statistics summary"""
        base_stats = self.get_stats()
        
        return {
            'publish_stats': self.publish_stats,
            'operation_stats': base_stats,
            'summary': {
                'tables_published': self.publish_stats['tables_published'],
                'data_size': self.publish_stats['data_size'],
                'success_rate': base_stats['success_rate'],
                'total_processing_time': base_stats['total_processing_time']
            }
        }

def publish_table(attendance_tracker=None, org_names=None):
    """
    Legacy function for backward compatibility
    Maintains the same interface as existing code
    """
    publisher = ShopifyPublisher()
    return publisher.publish_tournament_table()

def publish_to_shopify():
    """Convenient function to publish to Shopify"""
    publisher = ShopifyPublisher()
    return publisher.publish_tournament_table()

if __name__ == "__main__":
    print("Testing Shopify publishing...")
    
    try:
        init_db()
        
        # Test data access through database utils
        stats = get_summary_stats()
        print(f"Database ready:")
        print(f"   Organizations: {stats['total_organizations']}")
        print(f"   Tournaments: {stats['total_tournaments']}")
        
        # Test publishing
        publisher = ShopifyPublisher()
        success = publisher.publish_tournament_table()
        
        # Show stats
        publish_stats = publisher.get_publish_stats()
        print(f"Publishing stats:")
        print(f"   Attempts: {publish_stats['attempts']}")
        print(f"   Success rate: {publish_stats['success_rate']:.1f}%")
        
        if success:
            print("Shopify test successful")
        else:
            print("Shopify test failed")
            
    except Exception as e:
        print(f"Shopify test error: {e}")
        import traceback
        traceback.print_exc()

