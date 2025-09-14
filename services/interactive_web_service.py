#!/usr/bin/env python3
"""
interactive_web_service.py - Interactive web browser service with persistent handles

Provides persistent browser sessions that can be controlled interactively.
Follows the polymorphic ask/tell/do pattern.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.interactive_web_service")

from playwright.sync_api import sync_playwright
from polymorphic_core import announcer
import time
import uuid
from typing import Any, Optional, Dict, Union
from pathlib import Path
import json

# Import the base screenshot service
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'visualization_services'))
from base_screenshot_service import BaseScreenshotService

# Import computer vision service for image-based element detection
try:
    from services.computer_vision_service import computer_vision_service
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

class InteractiveWebService(BaseScreenshotService):
    """
    Interactive web browser service with persistent handles.
    
    Allows creating and managing multiple browser sessions that persist
    until explicitly closed, enabling interactive web automation.
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
            self.sessions = {}  # handle -> session data
            self._initialized = True
            
            # Announce this service
            capabilities = [
                "I provide persistent browser sessions for interactive web automation",
                "I can create browser handles that stay open until explicitly closed", 
                "I support screenshots, navigation, form filling, and element interaction",
                "I manage multiple concurrent browser sessions",
                "Human-like mouse movement and typing for anti-automation bypass"
            ]
            
            if CV_AVAILABLE:
                capabilities.extend([
                    "🔍 Computer Vision integration for anti-automation bypass",
                    "Image-based form element detection when CSS selectors fail", 
                    "OCR text recognition with coordinate-based clicking",
                    "Visual button and input field location"
                ])
            
            capabilities.append("Examples: ask('create session for https://example.com'), ask('screenshot handle abc123')")
            
            announcer.announce("Interactive Web Service", capabilities)
    
    def _ensure_browser(self):
        """Ensure browser is initialized"""
        if not self.browser:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,  # Headless for server environment
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
    
    def ask(self, query: str, **kwargs) -> Any:
        """
        Ask for browser sessions, screenshots, or information.
        
        Examples:
            ask('create session for https://example.com')
            ask('list sessions')
            ask('screenshot handle abc123')
            ask('page title for handle abc123')
            ask('current url for handle abc123')
        """
        query_lower = query.lower().strip()
        
        # List all sessions
        if 'list sessions' in query_lower or 'show sessions' in query_lower:
            return {
                'sessions': {
                    handle: {
                        'url': data['page'].url,
                        'title': data['page'].title(),
                        'created_at': data['created_at']
                    }
                    for handle, data in self.sessions.items()
                },
                'count': len(self.sessions)
            }
        
        # Create new session
        if 'create session' in query_lower:
            url = self._extract_url(query)
            if not url:
                return {'error': 'No URL found in query'}
            
            return self._create_session(url, **kwargs)
        
        # Screenshot of specific session
        if 'screenshot' in query_lower and 'handle' in query_lower:
            handle = self._extract_handle(query)
            if not handle or handle not in self.sessions:
                return {'error': f'Handle {handle} not found'}
            
            page = self.sessions[handle]['page']
            fullpage = 'full' in query_lower
            
            screenshot_bytes = page.screenshot(full_page=fullpage)
            
            return {
                'handle': handle,
                'url': page.url,
                'title': page.title(),
                'screenshot': screenshot_bytes,
                'timestamp': time.time()
            }
        
        # Page info for specific session
        if any(info in query_lower for info in ['title', 'url', 'info']) and 'handle' in query_lower:
            handle = self._extract_handle(query)
            if not handle or handle not in self.sessions:
                return {'error': f'Handle {handle} not found'}
            
            page = self.sessions[handle]['page']
            
            return {
                'handle': handle,
                'url': page.url,
                'title': page.title(),
                'viewport': page.viewport_size,
                'created_at': self.sessions[handle]['created_at']
            }
        
        return {'error': f'Unknown query: {query}'}
    
    def tell(self, format: str, data: Any = None, **kwargs) -> str:
        """
        Format session data for output.
        Extends BaseScreenshotService with session-specific formatting.
        
        Examples:
            tell('list', sessions_data)  # Interactive-specific
            tell('base64', screenshot_data)  # From base class
            tell('json', session_data)  # Enhanced with screenshot handling
        """
        format_lower = format.lower().strip()
        
        # Handle interactive-specific formats first
        if format_lower == 'list':
            if isinstance(data, dict) and 'sessions' in data:
                lines = [f"Interactive Browser Sessions ({data['count']} active):"]
                for handle, info in data['sessions'].items():
                    lines.append(f"  {handle}: {info['title']} - {info['url']}")
                return '\n'.join(lines)
            return str(data)
        
        # For all other formats (base64, file, html, markdown, json), use base class
        return super().tell(format, data, **kwargs)
    
    def do(self, action: str, **kwargs) -> Any:
        """
        Perform interactive browser actions.
        
        Examples:
            do('create session for https://example.com')
            do('navigate handle abc123 to https://google.com')
            do('click button with text Sign In in handle abc123')
            do('type "search query" in input[name=q] in handle abc123')
            do('close handle abc123')
            do('close all sessions')
        """
        action_lower = action.lower().strip()
        
        # Create session
        if 'create session' in action_lower:
            url = self._extract_url(action)
            if not url:
                return {'error': 'No URL found in action'}
            return self._create_session(url, **kwargs)
        
        # Close specific session
        if 'close handle' in action_lower:
            handle = self._extract_handle(action)
            if not handle or handle not in self.sessions:
                return {'error': f'Handle {handle} not found'}
            
            self.sessions[handle]['page'].close()
            del self.sessions[handle]
            return {'status': f'Closed session {handle}'}
        
        # Close all sessions
        if 'close all' in action_lower:
            count = len(self.sessions)
            for session_data in self.sessions.values():
                session_data['page'].close()
            self.sessions.clear()
            return {'status': f'Closed {count} sessions'}
        
        # Navigate
        if 'navigate' in action_lower and 'handle' in action_lower:
            handle = self._extract_handle(action)
            url = self._extract_url(action)
            
            if not handle or handle not in self.sessions:
                return {'error': f'Handle {handle} not found'}
            if not url:
                return {'error': 'No URL found in action'}
            
            page = self.sessions[handle]['page']
            page.goto(url, wait_until='networkidle')
            
            return {
                'status': f'Navigated {handle} to {url}',
                'handle': handle,
                'new_url': page.url,
                'title': page.title()
            }
        
        # Click element (supports both CSS selectors and mouse coordinates)
        if 'click' in action_lower and 'handle' in action_lower:
            handle = self._extract_handle(action)
            if not handle or handle not in self.sessions:
                return {'error': f'Handle {handle} not found'}
            
            page = self.sessions[handle]['page']
            
            # Check if it's a mouse coordinate click (e.g., "click at 300,150")
            if 'click at' in action_lower:
                coords = self._extract_coordinates(action)
                if coords:
                    try:
                        page.mouse.click(coords[0], coords[1])
                        return {
                            'status': f'Mouse clicked at {coords[0]},{coords[1]} in {handle}',
                            'handle': handle,
                            'url': page.url
                        }
                    except Exception as e:
                        return {'error': f'Mouse click failed: {str(e)}'}
            
            # Extract CSS selector for element click
            selector = self._extract_click_selector(action)
            if not selector:
                return {'error': 'Could not determine what to click'}
            
            try:
                # Try element click first
                page.click(selector)
                return {
                    'status': f'Clicked {selector} in {handle}',
                    'handle': handle,
                    'url': page.url
                }
            except Exception as e:
                # Fallback to mouse click with travel behavior
                try:
                    import random
                    import time as time_module
                    
                    element = page.locator(selector)
                    box = element.bounding_box()
                    if box:
                        # Calculate a random position within the element bounds
                        # Use 80% of element size for safety margins
                        margin_x = box['width'] * 0.1
                        margin_y = box['height'] * 0.1
                        
                        click_x = box['x'] + margin_x + random.random() * (box['width'] - 2 * margin_x)
                        click_y = box['y'] + margin_y + random.random() * (box['height'] - 2 * margin_y)
                        
                        # Human-like mouse movement: non-linear path with multiple waypoints
                        start_x = random.randint(100, 400)
                        start_y = random.randint(100, 300)
                        
                        # Create waypoints for curved, non-linear movement
                        waypoints = []
                        
                        # Add 2-4 random waypoints between start and target
                        num_waypoints = random.randint(2, 4)
                        for i in range(num_waypoints):
                            progress = (i + 1) / (num_waypoints + 1)
                            
                            # Base position along path
                            wp_x = start_x + progress * (click_x - start_x)
                            wp_y = start_y + progress * (click_y - start_y)
                            
                            # Add random curve/deviation
                            curve_x = random.randint(-50, 50)
                            curve_y = random.randint(-30, 30)
                            
                            waypoints.append((wp_x + curve_x, wp_y + curve_y))
                        
                        # Move through waypoints with human-like timing
                        page.mouse.move(start_x, start_y)
                        time_module.sleep(0.05 + random.random() * 0.1)
                        
                        for wp_x, wp_y in waypoints:
                            page.mouse.move(wp_x, wp_y)
                            time_module.sleep(0.08 + random.random() * 0.15)  # Varied timing
                        
                        # Final move to target with slight hesitation
                        page.mouse.move(click_x, click_y)
                        time_module.sleep(0.1 + random.random() * 0.2)  # Pause before click
                        
                        page.mouse.click(click_x, click_y)
                        
                        return {
                            'status': f'Mouse traveled and clicked {selector} at {int(click_x)},{int(click_y)} in {handle}',
                            'handle': handle,
                            'url': page.url
                        }
                except Exception as mouse_error:
                    pass
                # Ultimate fallback: Use computer vision to find button
                if CV_AVAILABLE and ('continue' in action_lower or 'submit' in action_lower or 'login' in action_lower):
                    return self._cv_fallback_clicking(handle, page, action)
                return {'error': f'Click failed: {str(e)}'}
        
        # Type text
        if 'type' in action_lower and 'handle' in action_lower:
            handle = self._extract_handle(action)
            if not handle or handle not in self.sessions:
                return {'error': f'Handle {handle} not found'}
            
            page = self.sessions[handle]['page']
            
            # Extract text and selector
            text, selector = self._extract_type_info(action)
            if not text or not selector:
                return {'error': 'Could not determine text or element to type into'}
            
            try:
                import random
                import time as time_module
                
                # Clear the field first
                page.click(selector)
                page.keyboard.press('Control+a')  # Select all
                time_module.sleep(0.1)
                
                # Type character by character with human-like timing
                for i, char in enumerate(text):
                    # Human typing speed varies: 50-150ms between characters
                    delay = 0.05 + random.random() * 0.1
                    
                    # Occasional longer pauses (thinking/hesitation)
                    if random.random() < 0.1:  # 10% chance of longer pause
                        delay += 0.2 + random.random() * 0.3
                    
                    # Slightly faster for common sequences
                    if i > 0 and text[i-1:i+1] in ['th', 'er', 'on', 'an', 'ed', 'nd', 'ha', 'en', 're']:
                        delay *= 0.8
                    
                    page.keyboard.type(char)
                    time_module.sleep(delay)
                
                # Brief pause after typing (human behavior)
                time_module.sleep(0.2 + random.random() * 0.3)
                
                return {
                    'status': f'Human-typed "{text}" into {selector} in {handle}',
                    'handle': handle
                }
            except Exception as e:
                # Fallback to instant fill
                try:
                    page.fill(selector, text)
                    return {
                        'status': f'Typed "{text}" into {selector} in {handle} (fallback)',
                        'handle': handle
                    }
                except Exception as e2:
                    # Ultimate fallback: Use computer vision to find email field
                    if CV_AVAILABLE and 'email' in action_lower:
                        return self._cv_fallback_typing(handle, text, page, action)
                    return {'error': f'Type failed: {str(e2)}'}
        
        return {'error': f'Unknown action: {action}'}
    
    # ============= PRIVATE METHODS =============
    
    def _create_session(self, url: str, **kwargs) -> Dict[str, Any]:
        """Create a new interactive browser session"""
        try:
            self._ensure_browser()
            
            # Create unique handle
            handle = str(uuid.uuid4())[:8]
            
            # Create new page
            page = self.browser.new_page()
            
            # Set viewport if specified
            if 'mobile' in kwargs and kwargs['mobile']:
                page.set_viewport_size({'width': 375, 'height': 667})
            else:
                page.set_viewport_size({'width': 1920, 'height': 1080})
            
            # Navigate to URL
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Store session
            self.sessions[handle] = {
                'page': page,
                'created_at': time.time(),
                'initial_url': url
            }
            
            return {
                'status': 'Session created successfully',
                'handle': handle,
                'url': page.url,
                'title': page.title(),
                'created_at': self.sessions[handle]['created_at']
            }
            
        except Exception as e:
            return {'error': str(e)}
    
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
    
    def _extract_handle(self, text: str) -> Optional[str]:
        """Extract handle from text like 'handle abc123'"""
        import re
        
        handle_match = re.search(r'handle\s+([a-f0-9]{8})', text)
        if handle_match:
            return handle_match.group(1)
        
        return None
    
    def _extract_click_selector(self, action: str) -> Optional[str]:
        """Extract what to click from action text"""
        action_lower = action.lower()
        
        if 'button with text' in action_lower:
            # Extract button text
            import re
            text_match = re.search(r'button with text\s+([^"\']+|"[^"]+"|\'[^\']+\')', action)
            if text_match:
                text = text_match.group(1).strip('\'"')
                return f'button:has-text("{text}")'
        
        if 'link with text' in action_lower:
            import re
            text_match = re.search(r'link with text\s+([^"\']+|"[^"]+"|\'[^\']+\')', action)
            if text_match:
                text = text_match.group(1).strip('\'"')
                return f'a:has-text("{text}")'
        
        # Look for CSS selectors
        if '[' in action and ']' in action:
            import re
            selector_match = re.search(r'([a-zA-Z][a-zA-Z0-9]*(?:\[[^\]]+\])+)', action)
            if selector_match:
                return selector_match.group(1)
        
        return None
    
    def _extract_type_info(self, action: str) -> tuple:
        """Extract text to type and selector from action"""
        import re
        
        # Extract quoted text
        text_match = re.search(r'"([^"]+)"', action)
        text = text_match.group(1) if text_match else None
        
        # Extract selector after "in"
        in_match = re.search(r'in\s+([a-zA-Z][a-zA-Z0-9]*(?:\[[^\]]+\])*)', action)
        selector = in_match.group(1) if in_match else None
        
        return text, selector
    
    def _extract_coordinates(self, action: str) -> Optional[tuple]:
        """Extract x,y coordinates from action like 'click at 300,150'"""
        import re
        
        coord_match = re.search(r'at\s+(\d+),\s*(\d+)', action)
        if coord_match:
            return (int(coord_match.group(1)), int(coord_match.group(2)))
        return None
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'sessions'):
            for session_data in self.sessions.values():
                try:
                    session_data['page'].close()
                except:
                    pass
        
        if hasattr(self, 'browser') and self.browser:
            try:
                self.browser.close()
            except:
                pass
        
        if hasattr(self, 'playwright') and self.playwright:
            try:
                self.playwright.stop()
            except:
                pass

# Create and announce the service
interactive_web_service = InteractiveWebService()

# Export for use
__all__ = ['interactive_web_service', 'InteractiveWebService']

if __name__ == '__main__':
    import sys
    
    service = InteractiveWebService()
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
        if not url.startswith(('http://', 'https://')):
            if 'localhost' in url:
                url = f'http://{url}'
            else:
                url = f'https://{url}'
        
        print(f"🌐 Creating interactive session for {url}...")
        result = service.ask(f'create session for {url}')
        
        if 'handle' in result:
            print(f"✅ Session created: {result['handle']}")
            print(f"   URL: {result['url']}")
            print(f"   Title: {result['title']}")
            print(f"\nUse handle {result['handle']} for further interactions")
            print(f"Example: service.do('navigate handle {result['handle']} to https://google.com')")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    else:
        # Demo mode
        result = service.ask('create session for https://google.com')
        if 'handle' in result:
            handle = result['handle']
            print(f"✅ Demo session created: {handle}")
            print(f"   URL: {result['url']}")
            print(f"   Title: {result['title']}")
            
            print(f"\n📋 Available commands:")
            print(f"  service.ask('list sessions')")
            print(f"  service.ask('screenshot handle {handle}')")
            print(f"  service.do('navigate handle {handle} to https://example.com')")
            print(f"  service.do('close handle {handle}')")
        else:
            print(f"❌ Demo failed: {result.get('error', 'Unknown error')}")
    
    def _cv_fallback_typing(self, handle: str, text: str, page, action: str) -> Dict:
        """Computer vision fallback for typing when CSS selectors fail"""
        try:
            # Take a screenshot for CV analysis
            screenshot = self.ask(f'screenshot handle {handle}')
            if 'screenshot' not in screenshot:
                return {'error': 'Could not capture screenshot for CV analysis'}
            
            # Save screenshot temporarily for CV analysis
            temp_path = f'cv_analysis_typing_{handle}.png'
            with open(temp_path, 'wb') as f:
                f.write(screenshot['screenshot'])
            
            # Use computer vision to find email field
            email_field = computer_vision_service.do('find email field', image_path=temp_path)
            
            if email_field.get('found'):
                coords = email_field['click_coordinates']
                x, y = coords
                
                # Human-like mouse movement to field
                import random
                import time as time_module
                
                start_x = random.randint(100, 400)
                start_y = random.randint(100, 300)
                
                # Move to field with waypoints
                num_waypoints = random.randint(2, 4)
                waypoints = []
                for i in range(num_waypoints):
                    progress = (i + 1) / (num_waypoints + 1)
                    wp_x = start_x + progress * (x - start_x)
                    wp_y = start_y + progress * (y - start_y)
                    curve_x = random.randint(-30, 30)
                    curve_y = random.randint(-20, 20)
                    waypoints.append((wp_x + curve_x, wp_y + curve_y))
                
                page.mouse.move(start_x, start_y)
                time_module.sleep(0.05 + random.random() * 0.1)
                
                for wp_x, wp_y in waypoints:
                    page.mouse.move(wp_x, wp_y)
                    time_module.sleep(0.08 + random.random() * 0.15)
                
                # Final move and click
                page.mouse.move(x, y)
                time_module.sleep(0.1 + random.random() * 0.2)
                page.mouse.click(x, y)
                
                # Clear and type human-like
                page.keyboard.press('Control+a')
                time_module.sleep(0.1)
                
                for i, char in enumerate(text):
                    delay = 0.05 + random.random() * 0.1
                    if random.random() < 0.1:
                        delay += 0.2 + random.random() * 0.3
                    if i > 0 and text[i-1:i+1] in ['th', 'er', 'on', 'an', 'ed', 'nd', 'ha', 'en', 're']:
                        delay *= 0.8
                    page.keyboard.type(char)
                    time_module.sleep(delay)
                
                time_module.sleep(0.2 + random.random() * 0.3)
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                return {
                    'status': f'🔍 CV-typed "{text}" via image recognition at {x},{y} in {handle}',
                    'handle': handle,
                    'method': 'computer_vision',
                    'confidence': email_field.get('confidence', 0)
                }
            else:
                return {'error': f'Computer vision could not find email field: {email_field.get("error")}'}
                
        except Exception as e:
            return {'error': f'CV typing fallback failed: {str(e)}'}
    
    def _cv_fallback_clicking(self, handle: str, page, action: str) -> Dict:
        """Computer vision fallback for clicking when CSS selectors fail"""
        try:
            # Take a screenshot for CV analysis  
            screenshot = self.ask(f'screenshot handle {handle}')
            if 'screenshot' not in screenshot:
                return {'error': 'Could not capture screenshot for CV analysis'}
            
            # Save screenshot temporarily for CV analysis
            temp_path = f'cv_analysis_clicking_{handle}.png'
            with open(temp_path, 'wb') as f:
                f.write(screenshot['screenshot'])
            
            # Use computer vision to find continue button
            continue_button = computer_vision_service.do('find continue button', image_path=temp_path)
            
            if continue_button.get('found'):
                coords = continue_button['click_coordinates']
                x, y = coords
                button_text = continue_button.get('button_text', 'button')
                
                # Human-like mouse movement to button
                import random  
                import time as time_module
                
                start_x = random.randint(100, 400)
                start_y = random.randint(100, 300)
                
                # Create waypoints for curved movement
                num_waypoints = random.randint(2, 4)
                waypoints = []
                for i in range(num_waypoints):
                    progress = (i + 1) / (num_waypoints + 1)
                    wp_x = start_x + progress * (x - start_x)
                    wp_y = start_y + progress * (y - start_y)
                    curve_x = random.randint(-50, 50)
                    curve_y = random.randint(-30, 30)
                    waypoints.append((wp_x + curve_x, wp_y + curve_y))
                
                # Move through waypoints
                page.mouse.move(start_x, start_y)
                time_module.sleep(0.05 + random.random() * 0.1)
                
                for wp_x, wp_y in waypoints:
                    page.mouse.move(wp_x, wp_y)
                    time_module.sleep(0.08 + random.random() * 0.15)
                
                # Final move to target with hesitation
                page.mouse.move(x, y)
                time_module.sleep(0.1 + random.random() * 0.2)
                
                # Click
                page.mouse.click(x, y)
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                return {
                    'status': f'🔍 CV-clicked "{button_text}" via image recognition at {x},{y} in {handle}',
                    'handle': handle,
                    'method': 'computer_vision',
                    'confidence': continue_button.get('confidence', 0),
                    'url': page.url
                }
            else:
                return {'error': f'Computer vision could not find continue button: {continue_button.get("error")}'}
                
        except Exception as e:
            return {'error': f'CV clicking fallback failed: {str(e)}'}