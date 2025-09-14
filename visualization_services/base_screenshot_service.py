#!/usr/bin/env python3
"""
base_screenshot_service.py - Base class for screenshot services

Provides common functionality for services that capture and format screenshots.
All screenshot services should inherit from this to ensure consistent formatting.
"""

import base64
from typing import Any, Optional, Dict, Union
from pathlib import Path
from abc import ABC, abstractmethod

class BaseScreenshotService(ABC):
    """
    Base class for screenshot services with consistent formatting.
    
    Provides standardized tell() method for formatting PNG screenshot data
    in various formats (base64, file, HTML, markdown, etc.)
    """
    
    def tell(self, format: str, data: Any = None, **kwargs) -> str:
        """
        Format screenshot data for output.
        
        Examples:
            tell('base64', screenshot_bytes)  # Base64 encoded string
            tell('file', screenshot_bytes, path='/tmp/screenshot.png')
            tell('html', screenshot_bytes)  # HTML img tag with data URI
            tell('markdown', screenshot_bytes)  # Markdown image with base64
            tell('json', screenshot_data)  # JSON with base64 screenshot
        """
        format_lower = format.lower().strip()
        
        if not data:
            return "No screenshot data provided"
        
        if format_lower == 'base64':
            if isinstance(data, bytes):
                return base64.b64encode(data).decode('utf-8')
            elif isinstance(data, dict) and 'screenshot' in data:
                return base64.b64encode(data['screenshot']).decode('utf-8')
            return str(data)
        
        elif format_lower == 'file':
            path = kwargs.get('path', '/tmp/screenshot.png')
            if isinstance(data, bytes):
                Path(path).write_bytes(data)
                return f"Screenshot saved to {path}"
            elif isinstance(data, dict) and 'screenshot' in data:
                Path(path).write_bytes(data['screenshot'])
                return f"Screenshot saved to {path}"
            return "Invalid data for file output"
        
        elif format_lower == 'html':
            if isinstance(data, bytes):
                b64 = base64.b64encode(data).decode('utf-8')
            elif isinstance(data, dict) and 'screenshot' in data:
                b64 = base64.b64encode(data['screenshot']).decode('utf-8')
            else:
                return "<p>Invalid screenshot data</p>"
            return f'<img src="data:image/png;base64,{b64}" alt="Screenshot" style="max-width:100%;">'
        
        elif format_lower == 'markdown':
            if isinstance(data, bytes):
                b64 = base64.b64encode(data).decode('utf-8')
            elif isinstance(data, dict) and 'screenshot' in data:
                b64 = base64.b64encode(data['screenshot']).decode('utf-8')
            else:
                return "Invalid screenshot data"
            
            # Save to temp file for markdown reference
            temp_path = '/tmp/screenshot_temp.png'
            if isinstance(data, bytes):
                Path(temp_path).write_bytes(data)
            elif isinstance(data, dict) and 'screenshot' in data:
                Path(temp_path).write_bytes(data['screenshot'])
            return f"![Screenshot]({temp_path})"
        
        elif format_lower == 'json':
            import json
            if isinstance(data, dict):
                # Convert bytes to base64 for JSON serialization
                result = data.copy()
                if 'screenshot' in result and isinstance(result['screenshot'], bytes):
                    result['screenshot'] = base64.b64encode(result['screenshot']).decode('utf-8')
                return json.dumps(result, indent=2)
            elif isinstance(data, bytes):
                # Simple bytes to base64
                b64 = base64.b64encode(data).decode('utf-8')
                return json.dumps({'screenshot': b64}, indent=2)
            return json.dumps({'data': str(data)}, indent=2)
        
        return str(data)
    
    @abstractmethod
    def ask(self, query: str, **kwargs) -> Any:
        """Abstract method - services must implement their own ask logic"""
        pass
    
    @abstractmethod
    def do(self, action: str, **kwargs) -> Any:
        """Abstract method - services must implement their own do logic"""
        pass

# Export the base class
__all__ = ['BaseScreenshotService']