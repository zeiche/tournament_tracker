#!/usr/bin/env python3
"""
Debug OCR functionality directly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("debug_ocr")

import pytesseract
from PIL import Image

def main():
    print('🔍 OCR DEBUG TEST')
    
    # Test tesseract directly
    try:
        version = pytesseract.get_tesseract_version()
        print(f'✅ Tesseract version: {version}')
    except Exception as e:
        print(f'❌ Tesseract version error: {e}')
        return
    
    # Test with one of our screenshots
    test_files = [
        'cv_direct_test_f0d59844.png',
        'cv_direct_test_034b753d.png', 
        'cv_direct_test_7262bd26.png',
        'twilio_cv_test_aff975ca.png'
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f'\n📸 Testing OCR on {test_file}...')
            try:
                # Load image
                image = Image.open(test_file)
                print(f'   Image size: {image.size}')
                print(f'   Image mode: {image.mode}')
                
                # Test basic OCR
                print('   Testing pytesseract.image_to_string...')
                text = pytesseract.image_to_string(image)
                print(f'   Text length: {len(text)}')
                if text.strip():
                    lines = text.strip().split('\n')
                    print(f'   First 3 lines: {lines[:3]}')
                else:
                    print('   No text detected')
                
                # Test detailed OCR  
                print('   Testing pytesseract.image_to_data...')
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                print(f'   OCR data keys: {list(data.keys())}')
                print(f'   Text elements: {len(data["text"])}')
                
                # Count non-empty text
                text_elements = [t.strip() for t in data['text'] if t.strip()]
                print(f'   Non-empty text elements: {len(text_elements)}')
                if text_elements:
                    print(f'   Sample text: {text_elements[:5]}')
                
                print('   ✅ OCR test successful!')
                break
                
            except Exception as e:
                print(f'   ❌ OCR test failed: {e}')
                import traceback
                traceback.print_exc()
        
    else:
        print('❌ No test files found to test OCR')

if __name__ == '__main__':
    main()