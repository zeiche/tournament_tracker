#!/usr/bin/env python3
"""
Computer Vision Service - OCR and Image Recognition for Form Detection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.computer_vision_service")

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import json
import re
from typing import Dict, List, Tuple, Optional, Any
import time

from polymorphic_core import announcer
from logging_services.polymorphic_log_manager import PolymorphicLogManager
from polymorphic_core.visualizable import MediaFile

class ComputerVisionService:
    """Computer Vision Service for form element detection and OCR"""
    
    def __init__(self):
        self.log_manager = PolymorphicLogManager()
        
        # Test if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            self.ocr_available = True
        except:
            self.ocr_available = False
            
        # Announce this service
        announcer.announce(
            "Computer Vision Service",
            [
                "OCR text recognition with coordinates",
                "Form element detection via image analysis", 
                "Button and input field location detection",
                "Visual element coordinate extraction",
                "Anti-automation bypass via image recognition",
                f"OCR Engine: {'Available' if self.ocr_available else 'Not Available'}"
            ]
        )
    
    def ask(self, query: str, **kwargs) -> Any:
        """Query for computer vision data using natural language"""
        query_lower = query.lower().strip()
        image_path = kwargs.get('image_path') or kwargs.get('path')
        
        if 'text' in query_lower or 'ocr' in query_lower:
            if not image_path:
                return {'error': 'Image path required for OCR'}
            return self._extract_text_with_coordinates(image_path)
            
        elif 'buttons' in query_lower:
            if not image_path:
                return {'error': 'Image path required for button detection'}
            return self._find_buttons(image_path)
            
        elif 'inputs' in query_lower or 'fields' in query_lower:
            if not image_path:
                return {'error': 'Image path required for input field detection'}
            return self._find_input_fields(image_path)
            
        elif 'elements' in query_lower:
            if not image_path:
                return {'error': 'Image path required for element detection'}
            return self._find_all_elements(image_path)
            
        elif 'analyze' in query_lower or 'info' in query_lower:
            if not image_path:
                return {'error': 'Image path required for analysis'}
            return self._analyze_image(image_path)
            
        else:
            return {
                'available_queries': [
                    'text from image - Extract text with coordinates',
                    'buttons in image - Find clickable buttons',
                    'inputs in image - Find input fields',
                    'elements in image - Find all interactive elements',
                    'analyze image - Complete image analysis'
                ],
                'ocr_available': self.ocr_available
            }
    
    def tell(self, format: str, data: Any = None, **kwargs) -> str:
        """Format computer vision data for output"""
        if format == 'coordinates':
            # Format as clickable coordinates
            if isinstance(data, dict) and 'elements' in data:
                coords = []
                for element in data['elements']:
                    if 'center' in element:
                        x, y = element['center']
                        coords.append(f"click at {x},{y}")
                return '\n'.join(coords)
        
        elif format == 'json':
            return json.dumps(data, indent=2)
            
        elif format == 'summary':
            if isinstance(data, dict):
                summary = []
                if 'text_elements' in data:
                    summary.append(f"Text elements: {len(data['text_elements'])}")
                if 'buttons' in data:
                    summary.append(f"Buttons: {len(data['buttons'])}")
                if 'inputs' in data:
                    summary.append(f"Input fields: {len(data['inputs'])}")
                return ', '.join(summary)
        
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """Perform computer vision actions using natural language"""
        action_lower = action.lower().strip()
        image_path = kwargs.get('image_path') or kwargs.get('path')
        
        if 'find email' in action_lower:
            if not image_path:
                return {'error': 'Image path required'}
            return self._find_email_field(image_path)
            
        elif 'find continue' in action_lower or 'find submit' in action_lower:
            if not image_path:
                return {'error': 'Image path required'}
            return self._find_continue_button(image_path)
            
        elif 'analyze text' in action_lower:
            if not image_path:
                return {'error': 'Image path required'}
            return self._extract_text_with_coordinates(image_path)
            
        elif 'annotate' in action_lower:
            if not image_path:
                return {'error': 'Image path required'}
            return self._create_annotated_image(image_path)
            
        else:
            return {
                'available_actions': [
                    'find email field in image - Locate email input field',
                    'find continue button in image - Locate continue/submit button',
                    'analyze text in image - Extract text with OCR',
                    'annotate image - Create annotated version with detected elements'
                ]
            }
    
    def _extract_text_with_coordinates(self, image_path: str) -> Dict:
        """Extract text with bounding box coordinates"""
        if not self.ocr_available:
            return {'error': 'OCR not available - tesseract not found'}
        
        try:
            # Load image
            image = Image.open(image_path)
            
            # Get detailed OCR data with coordinates
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            text_elements = []
            n_boxes = len(ocr_data['text'])
            
            for i in range(n_boxes):
                text = ocr_data['text'][i].strip()
                if text:  # Only include non-empty text
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
                    confidence = ocr_data['conf'][i]
                    
                    text_elements.append({
                        'text': text,
                        'bbox': [x, y, x + w, y + h],
                        'center': [x + w//2, y + h//2],
                        'confidence': confidence
                    })
            
            return {
                'text_elements': text_elements,
                'total_elements': len(text_elements),
                'image_size': image.size
            }
            
        except Exception as e:
            return {'error': f'OCR failed: {str(e)}'}
    
    def _find_buttons(self, image_path: str) -> Dict:
        """Find button-like elements in the image"""
        try:
            # Load image with OpenCV
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Look for rectangular shapes (buttons)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            buttons = []
            for contour in contours:
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Look for rectangular shapes
                if len(approx) >= 4:
                    x, y, w, h = cv2.boundingRect(contour)
                    area = cv2.contourArea(contour)
                    
                    # Filter for button-like dimensions and size
                    if 50 < w < 300 and 20 < h < 80 and area > 1000:
                        buttons.append({
                            'bbox': [x, y, x + w, y + h],
                            'center': [x + w//2, y + h//2],
                            'area': area,
                            'aspect_ratio': w / h
                        })
            
            # Sort by size (larger buttons first)
            buttons.sort(key=lambda b: b['area'], reverse=True)
            
            return {
                'buttons': buttons,
                'count': len(buttons)
            }
            
        except Exception as e:
            return {'error': f'Button detection failed: {str(e)}'}
    
    def _find_input_fields(self, image_path: str) -> Dict:
        """Find input field elements in the image"""
        try:
            # Load image with OpenCV
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Look for rectangular input-like shapes
            edges = cv2.Canny(gray, 30, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            inputs = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                # Filter for input field dimensions (wide and short)
                if w > 100 and 20 < h < 50 and area > 800:
                    aspect_ratio = w / h
                    if aspect_ratio > 3:  # Wide rectangles like input fields
                        inputs.append({
                            'bbox': [x, y, x + w, y + h],
                            'center': [x + w//2, y + h//2],
                            'area': area,
                            'aspect_ratio': aspect_ratio
                        })
            
            # Sort by vertical position (top to bottom)
            inputs.sort(key=lambda inp: inp['bbox'][1])
            
            return {
                'inputs': inputs,
                'count': len(inputs)
            }
            
        except Exception as e:
            return {'error': f'Input field detection failed: {str(e)}'}
    
    def _find_all_elements(self, image_path: str) -> Dict:
        """Find all interactive elements in the image"""
        # Combine text, button, and input detection
        text_result = self._extract_text_with_coordinates(image_path) if self.ocr_available else {'text_elements': []}
        button_result = self._find_buttons(image_path)
        input_result = self._find_input_fields(image_path)
        
        return {
            'text_elements': text_result.get('text_elements', []),
            'buttons': button_result.get('buttons', []),
            'inputs': input_result.get('inputs', []),
            'analysis': {
                'text_count': len(text_result.get('text_elements', [])),
                'button_count': len(button_result.get('buttons', [])),
                'input_count': len(input_result.get('inputs', []))
            }
        }
    
    def _analyze_image(self, image_path: str) -> Dict:
        """Complete image analysis with all detection methods"""
        try:
            image = Image.open(image_path)
            
            # Get all elements
            elements = self._find_all_elements(image_path)
            
            # Basic image info
            analysis = {
                'image_path': image_path,
                'image_size': image.size,
                'file_size': os.path.getsize(image_path),
                'elements_detected': elements,
                'ocr_available': self.ocr_available,
                'analysis_timestamp': time.time()
            }
            
            return analysis
            
        except Exception as e:
            return {'error': f'Image analysis failed: {str(e)}'}
    
    def _find_email_field(self, image_path: str) -> Dict:
        """Specifically find email input field"""
        # Get all text and input elements
        elements = self._find_all_elements(image_path)
        
        # Look for email-related text near input fields
        email_candidates = []
        
        # Check text elements for email-related words
        email_keywords = ['email', 'e-mail', '@', 'username', 'login']
        for text_elem in elements.get('text_elements', []):
            text_lower = text_elem['text'].lower()
            if any(keyword in text_lower for keyword in email_keywords):
                # Find nearest input field
                text_center = text_elem['center']
                for input_elem in elements.get('inputs', []):
                    input_center = input_elem['center']
                    distance = ((text_center[0] - input_center[0])**2 + (text_center[1] - input_center[1])**2)**0.5
                    
                    if distance < 150:  # Within reasonable proximity
                        email_candidates.append({
                            'input_field': input_elem,
                            'related_text': text_elem,
                            'distance': distance,
                            'confidence': text_elem.get('confidence', 0)
                        })
        
        # Sort by confidence and proximity
        email_candidates.sort(key=lambda c: (c['confidence'], -c['distance']), reverse=True)
        
        if email_candidates:
            best_candidate = email_candidates[0]
            return {
                'found': True,
                'email_field': best_candidate['input_field'],
                'click_coordinates': best_candidate['input_field']['center'],
                'related_text': best_candidate['related_text']['text'],
                'confidence': best_candidate['confidence']
            }
        
        # Fallback: return first input field if any
        inputs = elements.get('inputs', [])
        if inputs:
            return {
                'found': True,
                'email_field': inputs[0],
                'click_coordinates': inputs[0]['center'],
                'confidence': 50,
                'note': 'First input field (no email-specific text found)'
            }
        
        return {'found': False, 'error': 'No email field detected'}
    
    def _find_continue_button(self, image_path: str) -> Dict:
        """Specifically find continue/submit button"""
        elements = self._find_all_elements(image_path)
        
        # Look for continue/submit related text
        button_keywords = ['continue', 'submit', 'next', 'login', 'sign in', 'go']
        button_candidates = []
        
        for text_elem in elements.get('text_elements', []):
            text_lower = text_elem['text'].lower()
            if any(keyword in text_lower for keyword in button_keywords):
                # This text might be a button
                button_candidates.append({
                    'text_element': text_elem,
                    'click_coordinates': text_elem['center'],
                    'confidence': text_elem.get('confidence', 0),
                    'button_text': text_elem['text']
                })
        
        # Also check geometric buttons near button-like text
        for button_elem in elements.get('buttons', []):
            for text_elem in elements.get('text_elements', []):
                text_lower = text_elem['text'].lower()
                if any(keyword in text_lower for keyword in button_keywords):
                    # Check if text is inside or near this button
                    text_center = text_elem['center']
                    button_bbox = button_elem['bbox']
                    
                    if (button_bbox[0] <= text_center[0] <= button_bbox[2] and 
                        button_bbox[1] <= text_center[1] <= button_bbox[3]):
                        button_candidates.append({
                            'button_element': button_elem,
                            'text_element': text_elem,
                            'click_coordinates': button_elem['center'],
                            'confidence': text_elem.get('confidence', 0),
                            'button_text': text_elem['text']
                        })
        
        # Sort by confidence
        button_candidates.sort(key=lambda c: c['confidence'], reverse=True)
        
        if button_candidates:
            best_candidate = button_candidates[0]
            return {
                'found': True,
                'button': best_candidate,
                'click_coordinates': best_candidate['click_coordinates'],
                'button_text': best_candidate['button_text'],
                'confidence': best_candidate['confidence']
            }
        
        return {'found': False, 'error': 'No continue/submit button detected'}
    
    def _create_annotated_image(self, image_path: str) -> Dict:
        """Create annotated version of image with detected elements"""
        try:
            # Get all elements
            elements = self._find_all_elements(image_path)
            
            # Load image
            image = Image.open(image_path).convert('RGB')
            draw = ImageDraw.Draw(image)
            
            # Try to load a font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            # Draw input fields in blue
            for i, input_elem in enumerate(elements.get('inputs', [])):
                bbox = input_elem['bbox']
                draw.rectangle(bbox, outline='blue', width=2)
                draw.text((bbox[0], bbox[1] - 15), f'INPUT {i+1}', fill='blue', font=font)
            
            # Draw buttons in green
            for i, button_elem in enumerate(elements.get('buttons', [])):
                bbox = button_elem['bbox']
                draw.rectangle(bbox, outline='green', width=2)
                draw.text((bbox[0], bbox[1] - 15), f'BUTTON {i+1}', fill='green', font=font)
            
            # Draw text elements with high confidence in red
            for text_elem in elements.get('text_elements', []):
                if text_elem.get('confidence', 0) > 70:
                    bbox = text_elem['bbox']
                    draw.rectangle(bbox, outline='red', width=1)
            
            # Save annotated image
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            annotated_path = f'{base_name}_annotated.png'
            image.save(annotated_path)
            
            # Log the annotated image
            media = MediaFile(annotated_path, f'Computer vision analysis of {os.path.basename(image_path)}')
            self.log_manager.log('INFO', f'🔍 CV Analysis: {len(elements.get("inputs", []))} inputs, {len(elements.get("buttons", []))} buttons, {len(elements.get("text_elements", []))} text elements', media, source='computer_vision')
            
            return {
                'annotated_image': annotated_path,
                'elements_annotated': {
                    'inputs': len(elements.get('inputs', [])),
                    'buttons': len(elements.get('buttons', [])),
                    'text_elements': len(elements.get('text_elements', []))
                }
            }
            
        except Exception as e:
            return {'error': f'Annotation failed: {str(e)}'}

# Create singleton instance
computer_vision_service = ComputerVisionService()

if __name__ == '__main__':
    # Test the service
    print("🔍 Computer Vision Service Test")
    
    # Show capabilities
    capabilities = computer_vision_service.ask('capabilities')
    print("Capabilities:", capabilities)
    
    # Test with sample image if available
    test_image = 'twilio_bogus_email_result.png'
    if os.path.exists(test_image):
        print(f"\n📸 Testing with {test_image}")
        
        # Analyze image
        analysis = computer_vision_service.ask('analyze image', image_path=test_image)
        print("Analysis:", computer_vision_service.tell('summary', analysis))
        
        # Find email field
        email_field = computer_vision_service.do('find email field', image_path=test_image)
        print("Email field:", email_field)
        
        # Find continue button
        continue_button = computer_vision_service.do('find continue button', image_path=test_image)
        print("Continue button:", continue_button)
        
        # Create annotated version
        annotated = computer_vision_service.do('annotate image', image_path=test_image)
        print("Annotated:", annotated)