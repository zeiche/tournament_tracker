#!/usr/bin/env python3
"""
Direct starter for the advanced polymorphic web editor
Bypasses the persistent_web_service redirect to run the actual advanced editor
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set bypass for execution guard
os.environ["BYPASS_EXECUTION_GUARD"] = "true"

# Import and run the advanced web editor directly
try:
    # Import the specific classes we need
    from services.web_editor import EnhancedPolymorphicWebEditor, ManagedWebEditorService

    print("🚀 Starting Advanced Polymorphic Web Editor...")
    print("🔧 Features: Real-time logging, WebSocket support, mDNS discovery")

    # Create and start the advanced editor service
    service = ManagedWebEditorService()

    # Get the enhanced editor instance and run it directly
    editor = service.editor
    if hasattr(editor, 'run'):
        print("🌐 Starting advanced web editor on port 8081...")
        print("📡 SSL access: https://editor.zilogo.com")
        editor.run()
    else:
        print("❌ Advanced editor does not have run method")
        # Try alternative approach
        service.run()

except Exception as e:
    print(f"❌ Error starting advanced web editor: {e}")
    import traceback
    traceback.print_exc()