#!/usr/bin/env python3
"""Debug the execution guard"""

import sys
import os
import traceback
from pathlib import Path

def debug_enforce_go_py_execution(module_name: str = None, allow_imports: bool = True):
    """Debug version of enforce_go_py_execution with detailed logging"""
    print(f"=== DEBUG ENFORCE_GO_PY_EXECUTION ===")
    print(f"module_name: {module_name}")
    print(f"allow_imports: {allow_imports}")
    
    # Get the module name if not provided
    if module_name is None:
        frame = sys._getframe(1)
        module_name = frame.f_globals.get('__name__', 'unknown_module')
        print(f"Auto-detected module_name: {module_name}")
    
    # Check if we're being imported vs executed
    calling_frame = sys._getframe(1)
    is_main_execution = calling_frame.f_globals.get('__name__') == '__main__'
    print(f"calling_frame.__name__: {calling_frame.f_globals.get('__name__')}")
    print(f"is_main_execution: {is_main_execution}")
    
    # Get the full call stack to understand execution context
    stack = traceback.extract_stack()
    print(f"Call stack ({len(stack)} frames):")
    for i, frame in enumerate(stack):
        print(f"  {i}: {frame.filename}")
    
    # Look for go.py in the call stack
    go_py_in_stack = any('go.py' in str(frame.filename) for frame in stack)
    print(f"go_py_in_stack: {go_py_in_stack}")
    
    # Check for direct execution patterns
    script_path = sys.argv[0] if sys.argv else ''
    print(f"script_path (sys.argv[0]): {script_path}")
    print(f"sys.argv: {sys.argv}")
    
    direct_python_call = any([
        script_path.endswith('.py') and 'go.py' not in script_path,
        is_main_execution and not go_py_in_stack,
        'python3' in ' '.join(sys.argv) and 'go.py' not in ' '.join(sys.argv)
    ])
    print(f"Direct execution checks:")
    print(f"  script_path.endswith('.py') and 'go.py' not in script_path: {script_path.endswith('.py') and 'go.py' not in script_path}")
    print(f"  is_main_execution and not go_py_in_stack: {is_main_execution and not go_py_in_stack}")
    print(f"  'python3' in argv and 'go.py' not in argv: {'python3' in ' '.join(sys.argv) and 'go.py' not in ' '.join(sys.argv)}")
    print(f"direct_python_call: {direct_python_call}")
    
    # Check environment bypass
    bypass_guard = os.environ.get('BYPASS_EXECUTION_GUARD') == 'true'
    print(f"bypass_guard: {bypass_guard}")
    
    print(f"=== DECISION LOGIC ===")
    
    if bypass_guard:
        print("ALLOWING: bypass_guard is true")
        return  # Allow bypass for emergency debugging
    
    if go_py_in_stack:
        print("ALLOWING: go_py_in_stack is true")
        return  # Execution through go.py is allowed
        
    if not is_main_execution and allow_imports:
        print("ALLOWING: not is_main_execution and allow_imports")
        return  # Import is allowed
    
    # Block direct execution
    if direct_python_call or is_main_execution:
        print("BLOCKING: direct_python_call or is_main_execution")
        print("🚫 SHOULD BLOCK EXECUTION HERE!")
        sys.exit(1)
    else:
        print("ALLOWING: None of the blocking conditions met")

print("Testing debug execution guard...")
debug_enforce_go_py_execution("test_module")
print("ERROR: Guard did not block execution!")