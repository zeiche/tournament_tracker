#!/usr/bin/env python3
"""
Universal execution guard to enforce go.py usage.

CRITICAL RULE: ALL modules must import and use this guard to prevent direct execution.
Only go.py should be allowed to run Python modules directly.
"""

import sys
import os
import traceback
from pathlib import Path

class DirectExecutionBlocked(Exception):
    """Raised when a module is executed directly instead of through go.py"""
    pass

def enforce_go_py_execution(module_name: str = None, allow_imports: bool = True):
    """
    Enforce that this module is only executed through go.py
    
    Args:
        module_name: Name of the module (for error messages)
        allow_imports: If True, allows imports but blocks direct execution
                      If False, blocks all access except through go.py
    """
    # Get the module name if not provided - look at the calling module, not this guard
    if module_name is None:
        # Walk up the stack to find the actual calling module
        frame = sys._getframe(2)  # Skip guard frame and require_go_py frame
        module_name = frame.f_globals.get('__name__', 'unknown_module')
    
    # Critical fix: Check the ORIGINAL calling module's __main__ status
    # We need to go back to the module that called require_go_py()
    original_frame = sys._getframe(2)  # Skip execution_guard.py and require_go_py()
    is_main_execution = original_frame.f_globals.get('__name__') == '__main__'
    
    # Get the full call stack to understand execution context
    stack = traceback.extract_stack()
    
    # Look for go.py in the call stack
    go_py_in_stack = any('go.py' in str(frame.filename) for frame in stack)
    
    # Check for direct execution patterns
    script_path = sys.argv[0] if sys.argv else ''
    direct_python_call = any([
        script_path.endswith('.py') and 'go.py' not in script_path,
        is_main_execution and not go_py_in_stack,
        'python3' in ' '.join(sys.argv) and 'go.py' not in ' '.join(sys.argv)
    ])
    
    # Allow execution only if:
    # 1. Called through go.py (go.py in call stack)
    # 2. Being imported (not main execution) and imports are allowed
    # 3. Special cases for testing/debugging (with environment variable)
    
    bypass_guard = os.environ.get('BYPASS_EXECUTION_GUARD') == 'true'
    
    if bypass_guard:
        return  # Allow bypass for emergency debugging
    
    if go_py_in_stack:
        return  # Execution through go.py is allowed
        
    if not is_main_execution and allow_imports:
        return  # Import is allowed
    
    # Block direct execution
    if direct_python_call or is_main_execution:
        error_message = f"""
🚫 DIRECT EXECUTION BLOCKED: {module_name}

❌ This module cannot be executed directly!
✅ Use: ./go.py [appropriate-flag]

🔒 ARCHITECTURAL RULE: ALL Python modules must go through go.py
   - go.py manages environment variables correctly
   - go.py handles process management properly  
   - go.py ensures consistent configuration
   - go.py is the SINGLE ENTRY POINT

📋 Common commands:
   ./go.py --web              (start web service)
   ./go.py --discord-bot      (start discord bot)  
   ./go.py --sync             (sync tournaments)
   ./go.py --interactive      (interactive mode)
   ./go.py --help             (see all options)

🛑 Direct execution with python3 is FORBIDDEN:
   ❌ python3 {module_name}.py
   ❌ python3 services/any_service.py
   ❌ nohup python3 anything.py

💡 If you need to bypass this for debugging, set:
   export BYPASS_EXECUTION_GUARD=true
   (But this should NEVER be used in production!)

📞 Execution context:
   Script: {script_path}
   Main: {is_main_execution}
   Args: {sys.argv}
   Stack has go.py: {go_py_in_stack}
"""
        print(error_message)
        sys.exit(1)

def mark_go_py_execution():
    """
    Mark that this execution is coming from go.py
    Should be called by go.py early in its execution
    """
    os.environ['GO_PY_EXECUTION'] = 'true'

def is_go_py_execution() -> bool:
    """Check if current execution is through go.py"""
    return os.environ.get('GO_PY_EXECUTION') == 'true'

# Convenience function for the common case
def require_go_py(module_name: str = None):
    """Shorthand to enforce go.py execution for this module"""
    enforce_go_py_execution(module_name, allow_imports=True)