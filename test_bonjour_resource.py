#!/usr/bin/env python3
"""
Test the BonjourResource class directly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polymorphic_core.execution_guard import mark_go_py_execution
mark_go_py_execution()

from services.webdav_database_browser import BonjourResource

def test_bonjour_resource():
    """Test BonjourResource methods directly"""
    print("Testing BonjourResource implementation...")

    # Create a mock environ
    environ = {"wsgidav.provider": object()}

    # Test data
    test_data = {"filename": "service_count.txt"}

    def test_content_func(data):
        return f"Total services announced: 12\nTest file content for {data['filename']}"

    # Create BonjourResource
    resource = BonjourResource(
        "/bonjour/stats/service_count.txt",
        environ,
        test_data,
        test_content_func
    )

    print("✅ BonjourResource created successfully")

    # Test all methods that caused NotImplementedError
    try:
        print(f"Content length: {resource.get_content_length()}")
        print(f"Content type: {resource.get_content_type()}")
        creation_date = resource.get_creation_date()
        last_modified = resource.get_last_modified()
        print(f"Creation date: {creation_date} (type: {type(creation_date)})")
        print(f"Last modified: {last_modified} (type: {type(last_modified)})")
        print(f"Support ranges: {resource.support_ranges()}")

        # Test content reading
        content_io = resource.get_content()
        content = content_io.read().decode('utf-8')
        print(f"Content: {content}")

        print("✅ All BonjourResource methods work correctly!")

    except Exception as e:
        print(f"❌ Error testing BonjourResource: {e}")
        raise

if __name__ == "__main__":
    test_bonjour_resource()