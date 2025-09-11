#!/usr/bin/env python3
"""
test_error_handler.py - Test comprehensive error handling system
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import error_handler, handle_exception, handle_errors, ErrorSeverity


def test_basic_error_handling():
    """Test basic error handling functionality"""
    print("🔴 Testing basic error handling...")
    
    try:
        raise ValueError("Test error message")
    except Exception as e:
        context = handle_exception(e, {"test_context": "basic_test"})
        print(f"✅ Handled error: {context.message}")
        print(f"   Severity: {context.severity.value}")
        print(f"   Module: {context.module}")
        print(f"   Function: {context.function}")


def test_decorator_error_handling():
    """Test decorator-based error handling"""
    print("\n🔴 Testing decorator error handling...")
    
    @handle_errors(severity=ErrorSeverity.HIGH, context={"operation": "test_decorator"})
    def failing_function():
        raise ConnectionError("Test connection error")
    
    try:
        failing_function()
    except ConnectionError:
        print("✅ Decorator properly handled and re-raised error")


def test_no_reraise_decorator():
    """Test decorator without reraising"""
    print("\n🔴 Testing decorator without reraise...")
    
    @handle_errors(
        severity=ErrorSeverity.LOW, 
        reraise=False, 
        default_return="Error handled",
        context={"operation": "test_no_reraise"}
    )
    def failing_function():
        raise ValueError("Test value error")
    
    result = failing_function()
    print(f"✅ Function returned: {result}")


def test_ask_functionality():
    """Test ask functionality"""
    print("\n❓ Testing ask functionality...")
    
    recent_errors = error_handler.ask("recent errors")
    print(f"✅ Recent errors: {len(recent_errors)} found")
    
    stats = error_handler.ask("error stats")
    print(f"✅ Error stats: {stats}")


def test_tell_functionality():
    """Test tell functionality"""
    print("\n📢 Testing tell functionality...")
    
    # Discord format
    recent = error_handler.ask("recent errors")
    discord_output = error_handler.tell("discord", recent)
    print("✅ Discord format:")
    print(discord_output)
    
    # JSON format
    print("\n✅ JSON format:")
    json_output = error_handler.tell("json", recent[:2])
    print(json_output[:200] + "..." if len(json_output) > 200 else json_output)


def test_do_functionality():
    """Test do functionality"""
    print("\n🔧 Testing do functionality...")
    
    # Clear history
    result = error_handler.do("clear history")
    print(f"✅ Clear history result: {result}")
    
    # Add some test errors first
    try:
        raise TypeError("Test type error")
    except Exception as e:
        handle_exception(e)
    
    try:
        raise KeyError("Test key error")
    except Exception as e:
        handle_exception(e)
    
    # Get stats
    stats = error_handler.ask("stats")
    print(f"✅ New error stats: {stats}")


def test_severity_classification():
    """Test automatic severity classification"""
    print("\n🎯 Testing severity classification...")
    
    test_errors = [
        (FileNotFoundError("test.txt not found"), ErrorSeverity.HIGH),
        (ValueError("invalid value"), ErrorSeverity.LOW),
        (ConnectionError("connection failed"), ErrorSeverity.MEDIUM),
        (ImportError("module not found"), ErrorSeverity.CRITICAL)
    ]
    
    for exception, expected_severity in test_errors:
        try:
            raise exception
        except Exception as e:
            context = handle_exception(e)
            print(f"✅ {type(e).__name__}: {context.severity.value} (expected: {expected_severity.value})")


if __name__ == "__main__":
    print("🧪 Starting comprehensive error handler tests...\n")
    
    test_basic_error_handling()
    test_decorator_error_handling()
    test_no_reraise_decorator()
    test_ask_functionality()
    test_tell_functionality()
    test_do_functionality()
    test_severity_classification()
    
    print("\n🎉 All error handler tests complete!")
    print("\nFinal system status:")
    final_stats = error_handler.ask("stats")
    print(error_handler.tell("discord", final_stats))