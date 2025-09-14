#!/usr/bin/env python3
"""
web_screenshot_service.py - Web page screenshot service with Bonjour announcements
Provides screenshots of web pages using Playwright headless browser.
Follows the polymorphic ask/tell/do pattern.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from polymorphic_core import register_capability
import base64
from typing import Any, Optional, Dict, Union
from pathlib import Path
import time
import json

class WebScreenshotService:
    """
    Web screenshot service with polymorphic ask/tell/do pattern.
    Uses Playwright for reliable headless browsing and screenshots.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.playwright = None
            self.browser = None
            self.context = None
            self._initialized = True
            
            # Register as polymorphic capability
            register_capability('web_browser', lambda: self)
    
    def _ensure_browser(self):
        """Ensure browser is initialized"""
        if not self.browser:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                device_scale_factor=1
            )
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Ask for screenshots or browser information.
        
        Examples:
            ask('screenshot of https://example.com')
            ask('capture http://localhost:8081')
            ask('mobile screenshot of https://site.com')
            ask('browser status')
        """
        query_lower = query.lower().strip()
        
        # Check browser status
        if 'status' in query_lower:
            open_pages = getattr(self, 'open_pages', {})
            return {
                'browser_active': self.browser is not None,
                'playwright_version': '1.55.0',
                'browser_type': 'chromium',
                'open_pages': list(open_pages.keys()),
                'open_page_count': len(open_pages)
            }
        
        # List open pages
        if 'open pages' in query_lower or 'list pages' in query_lower:
            open_pages = getattr(self, 'open_pages', {})
            return {
                'open_pages': list(open_pages.keys()),
                'count': len(open_pages)
            }
        
        # Screenshot requests
        if 'screenshot' in query_lower or 'capture' in query_lower:
            # Extract URL from query
            url = self._extract_url(query)
            if not url:
                return {'error': 'No URL found in query'}
            
            # Determine options
            options = {
                'fullpage': 'full' in query_lower or 'entire' in query_lower,
                'mobile': 'mobile' in query_lower,
                'wait': kwargs.get('wait', 2),  # Wait time after load
                'keep_open': 'keep' in query_lower and 'open' in query_lower
            }
            
            return self._capture_screenshot(url, **options)
        
        return {'error': f'Unknown query: {query}'}
    
    def tell(self, format: str, data: Any = None, **kwargs) -> str:
        """
        Format screenshot data for output.
        
        Examples:
            tell('base64', screenshot_bytes)  # Base64 encoded string
            tell('file', screenshot_bytes, path='/tmp/screenshot.png')
            tell('html', screenshot_bytes)  # HTML img tag with data URI
            tell('markdown', screenshot_bytes)  # Markdown image with base64
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
            if isinstance(data, dict):
                # Convert bytes to base64 for JSON serialization
                result = data.copy()
                if 'screenshot' in result and isinstance(result['screenshot'], bytes):
                    result['screenshot'] = base64.b64encode(result['screenshot']).decode('utf-8')
                return json.dumps(result, indent=2)
            return json.dumps({'data': str(data)}, indent=2)
        
        return str(data)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform screenshot actions.
        
        Examples:
            do('capture https://example.com')
            do('capture https://site.com fullpage=true mobile=true')
            do('save screenshot of https://example.com to /tmp/site.png')
            do('close browser')
        """
        action_lower = action.lower().strip()
        
        # Close browser
        if 'close' in action_lower and 'browser' in action_lower:
            return self._close_browser()
        
        # Close specific page
        if 'close page' in action_lower:
            url = self._extract_url(action)
            if url and hasattr(self, 'open_pages') and url in self.open_pages:
                self.open_pages[url].close()
                del self.open_pages[url]
                return {'status': f'Closed page {url}'}
            return {'error': f'Page {url} not found in open pages'}
        
        # Close all pages
        if 'close all pages' in action_lower:
            if hasattr(self, 'open_pages'):
                count = len(self.open_pages)
                for page in self.open_pages.values():
                    page.close()
                self.open_pages.clear()
                return {'status': f'Closed {count} pages'}
            return {'status': 'No pages were open'}
        
        # Capture screenshot
        if 'capture' in action_lower or 'screenshot' in action_lower:
            url = self._extract_url(action)
            if not url:
                return {'error': 'No URL found in action'}
            
            # Parse options from action string
            options = {
                'fullpage': 'fullpage=true' in action_lower or 'full' in action_lower,
                'mobile': 'mobile=true' in action_lower or 'mobile' in action_lower,
                'wait': kwargs.get('wait', 2),
                'keep_open': 'keep' in action_lower and 'open' in action_lower
            }
            
            # Capture screenshot
            result = self._capture_screenshot(url, **options)
            
            # Check if we should save to file
            if 'to ' in action_lower:
                # Extract file path
                parts = action.split('to ')
                if len(parts) > 1:
                    file_path = parts[1].strip()
                    if result and 'screenshot' in result:
                        Path(file_path).write_bytes(result['screenshot'])
                        result['saved_to'] = file_path
            
            return result
        
        return {'error': f'Unknown action: {action}'}
    
    # ============= PRIVATE METHODS =============
    
    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from text"""
        import re
        
        # Look for URLs starting with http/https
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]*'
        match = re.search(url_pattern, text)
        if match:
            return match.group()
        
        # Look for localhost URLs
        if 'localhost' in text:
            port_match = re.search(r'localhost:(\d+)', text)
            if port_match:
                return f"http://localhost:{port_match.group(1)}"
            return "http://localhost"
        
        return None
    
    def _capture_screenshot(self, url: str, fullpage: bool = False, 
                          mobile: bool = False, wait: float = 2, keep_open: bool = False) -> Dict[str, Any]:
        """Capture a screenshot of the given URL"""
        try:
            self._ensure_browser()
            
            # Create page with mobile viewport if requested
            if mobile:
                page = self.context.new_page()
                page.set_viewport_size({'width': 375, 'height': 667})
            else:
                page = self.context.new_page()
            
            # Navigate to URL
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for any dynamic content
            time.sleep(wait)
            
            # Take screenshot
            screenshot_bytes = page.screenshot(full_page=fullpage)
            
            # Get page info
            title = page.title()
            viewport = page.viewport_size
            
            # Only close page if not keeping it open
            if not keep_open:
                page.close()
            else:
                # Store reference to open page
                if not hasattr(self, 'open_pages'):
                    self.open_pages = {}
                self.open_pages[url] = page
            
            result = {
                'url': url,
                'title': title,
                'viewport': viewport,
                'fullpage': fullpage,
                'mobile': mobile,
                'screenshot': screenshot_bytes,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            return {'error': str(e), 'url': url}
    
    def _close_browser(self) -> Dict[str, str]:
        """Close the browser and cleanup"""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.context = None
        
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        
        return {'status': 'Browser closed'}

# Create singleton instance
screenshot_service = WebScreenshotService()

# Export for use
__all__ = ['screenshot_service', 'WebScreenshotService']

if __name__ == '__main__':
    import sys
    
    service = WebScreenshotService()
    
    # Check if URL was provided as argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
        # If it doesn't start with http, prepend it
        if not url.startswith(('http://', 'https://')):
            if 'localhost' in url:
                url = f'http://{url}'
            else:
                url = f'https://{url}'
        
        print(f"📸 Capturing screenshot of {url}...")
        result = service.ask(f'screenshot of {url}')
        
        if 'screenshot' in result:
            print(f"✅ Captured screenshot of {result['url']}")
            print(f"   Title: {result['title']}")
            print(f"   Size: {len(result['screenshot'])} bytes")
            
            # Save to file with domain name
            from urllib.parse import urlparse
            domain = urlparse(result['url']).netloc.replace(':', '_')
            filename = f'/tmp/{domain}_screenshot.png'
            output = service.tell('file', result, path=filename)
            print(f"   {output}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    else:
        # Test with google
        result = service.ask('screenshot of https://google.com')
        if 'screenshot' in result:
            print(f"✅ Captured screenshot of {result['url']}")
            print(f"   Title: {result['title']}")
            print(f"   Size: {len(result['screenshot'])} bytes")
            
            # Save to file
            output = service.tell('file', result, path='/tmp/google_screenshot.png')
            print(f"   {output}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")