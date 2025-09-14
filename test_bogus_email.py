#!/usr/bin/env python3
"""Test bogus email on Twilio login"""

import sys, os
sys.path.insert(0, '.')

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("test_bogus_email")

from services.interactive_web_service import interactive_web_service
from logging_services.polymorphic_log_manager import PolymorphicLogManager  
from polymorphic_core.visualizable import MediaFile
import time

print('📧 Testing bogus email grinful@giggles.com on Twilio...')

try:
    # Create session
    result = interactive_web_service.ask('create session for https://www.twilio.com/login')
    if 'handle' not in result:
        print(f'❌ Session failed: {result}')
        exit()
    
    handle = result['handle']
    print(f'✅ Handle: {handle}')
    
    # Enter bogus email
    email_result = interactive_web_service.do(f'type "grinful@giggles.com" in input[type=email] in handle {handle}')
    print(f'📧 Email entry: {email_result.get("status", email_result.get("error"))}')
    
    time.sleep(2)
    
    # Click continue
    click_result = interactive_web_service.do(f'click button with text Continue in handle {handle}')
    print(f'🖱️ Continue click: {click_result.get("status", click_result.get("error"))}')
    
    time.sleep(4)
    
    # Get final page info
    info = interactive_web_service.ask(f'info for handle {handle}')
    print(f'📍 Final URL: {info["url"]}')
    print(f'📄 Final Title: {info["title"]}')
    
    # Screenshot
    screenshot = interactive_web_service.ask(f'screenshot handle {handle}')
    if 'screenshot' in screenshot:
        path = f'twilio_bogus_email_result.png'
        interactive_web_service.tell('file', screenshot, path=path)
        
        log_manager = PolymorphicLogManager()
        media = MediaFile(path, f'Twilio response to bogus email grinful@giggles.com')
        log_manager.log('INFO', f'📧❌ Twilio bogus email response (handle: {handle})', media, source='bogus_email_test')
        
        print(f'✅ Screenshot saved and logged: {len(screenshot["screenshot"])} bytes')
    else:
        print(f'❌ Screenshot failed: {screenshot}')

except Exception as e:
    print(f'❌ Error: {e}')