#!/usr/bin/env python3
"""
Direct Computer Vision Service Test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("test_cv_direct")

from services.computer_vision_service import computer_vision_service
from services.interactive_web_service import InteractiveWebService
from logging_services.polymorphic_log_manager import PolymorphicLogManager  
from polymorphic_core.visualizable import MediaFile

def main():
    print('🔍 DIRECT COMPUTER VISION TEST')
    print('   Goal: Test CV service directly on a Twilio screenshot')

    # First, test the CV service is working
    print()
    print('📋 Testing CV service capabilities...')
    status = computer_vision_service.ask('status')
    print(f'CV Service status: {status}')

    # Create a fresh IWS instance to get a screenshot
    print()
    print('📸 Getting fresh screenshot for CV analysis...')
    iws = InteractiveWebService()

    # Create session and get screenshot
    result = iws.ask('create session for https://www.twilio.com/login')
    if 'handle' not in result:
        print(f'❌ Session failed: {result}')
        return

    handle = result['handle']
    print(f'✅ Handle: {handle}')

    # Take screenshot
    screenshot = iws.ask(f'screenshot handle {handle}')
    if 'screenshot' in screenshot:
        # Save screenshot for CV analysis
        cv_test_path = f'cv_direct_test_{handle}.png'
        with open(cv_test_path, 'wb') as f:
            f.write(screenshot['screenshot'])
        
        print(f'📸 Screenshot saved for CV analysis: {cv_test_path}')
        print(f'   Size: {len(screenshot["screenshot"])} bytes')
        
        # Test CV analysis
        print()
        print('🔍 TESTING: Computer Vision email field detection...')
        email_field_result = computer_vision_service.do('find email field', image_path=cv_test_path)
        
        print('CV Email field detection result:')
        print(f'   Found: {email_field_result.get("found", False)}')
        if email_field_result.get('found'):
            coords = email_field_result.get('click_coordinates', [0, 0])
            confidence = email_field_result.get('confidence', 0)
            print(f'   Coordinates: {coords}')
            print(f'   Confidence: {confidence}')
            print('   ✅ CV email field detection successful!')
        else:
            print(f'   Error: {email_field_result.get("error", "Unknown error")}')
            print('   ❌ CV email field detection failed')
        
        print()
        print('🔍 TESTING: Computer Vision button detection...')
        button_result = computer_vision_service.do('find continue button', image_path=cv_test_path)
        
        print('CV Continue button detection result:')
        print(f'   Found: {button_result.get("found", False)}')
        if button_result.get('found'):
            coords = button_result.get('click_coordinates', [0, 0])
            button_text = button_result.get('button_text', 'button')
            confidence = button_result.get('confidence', 0)
            print(f'   Coordinates: {coords}')
            print(f'   Button text: {button_text}')
            print(f'   Confidence: {confidence}')
            print('   ✅ CV button detection successful!')
        else:
            print(f'   Error: {button_result.get("error", "Unknown error")}')
            print('   ❌ CV button detection failed')
        
        # Test OCR analysis
        print()
        print('🔍 TESTING: OCR text recognition...')
        ocr_result = computer_vision_service.do('analyze text', image_path=cv_test_path)
        
        print('OCR Analysis result:')
        if 'text_elements' in ocr_result:
            text_elements = ocr_result['text_elements']
            print(f'   Found {len(text_elements)} text elements:')
            for i, elem in enumerate(text_elements[:5]):  # Show first 5
                print(f'     {i+1}. "{elem["text"]}" at {elem["coordinates"]}')
            if len(text_elements) > 5:
                print(f'     ... and {len(text_elements) - 5} more')
            print('   ✅ OCR text recognition successful!')
        else:
            print(f'   Error: {ocr_result.get("error", "Unknown error")}')
            print('   ❌ OCR analysis failed')
        
        # Log the CV analysis results
        log_manager = PolymorphicLogManager()
        media = MediaFile(cv_test_path, f'Direct CV test on Twilio login: handle {handle}')
        log_manager.log('INFO', f'🔍 DIRECT CV TEST: Email field and button detection', media, source='direct_cv_test')
        
        print()
        print('🎯 DIRECT COMPUTER VISION TEST RESULTS:')
        print(f'   📸 Screenshot: {cv_test_path}')
        print(f'   🔍 CV Service: Available and functional')
        print(f'   📧 Email field detection: {"✅" if email_field_result.get("found") else "❌"}')
        print(f'   🖱️ Button detection: {"✅" if button_result.get("found") else "❌"}')
        print(f'   📝 OCR text recognition: {"✅" if "text_elements" in ocr_result else "❌"}')
        print('   🌐 View logged screenshot: http://10.0.0.1:8081/logs')
        print(f'   🔓 Handle {handle} remains active')

    else:
        print(f'❌ Screenshot failed: {screenshot}')

    print()
    print('🎯 Direct CV test complete')

if __name__ == '__main__':
    main()