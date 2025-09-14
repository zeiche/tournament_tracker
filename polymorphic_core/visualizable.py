#!/usr/bin/env python3
"""
Polymorphic Visualization System - Objects can visualize themselves

This allows any object logged to the system to provide its own visualization
when clicked in the log viewer. Supports images, audio, interactive content, etc.
"""

import os
import mimetypes
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod


class VisualizableObject(ABC):
    """Base class for objects that can visualize themselves"""
    
    @abstractmethod
    def visualize(self) -> Dict[str, Any]:
        """
        Return visualization data for this object.
        
        Returns:
            Dict with keys:
            - type: 'image', 'audio', 'video', 'html', 'json', 'text'
            - content: content to display (file path, base64, html, etc.)
            - mime_type: MIME type if applicable
            - metadata: additional display information
        """
        pass


class MediaFile(VisualizableObject):
    """A media file that can display itself when clicked in logs"""
    
    def __init__(self, file_path: str, description: str = ""):
        self.file_path = file_path
        self.description = description
        self.mime_type = mimetypes.guess_type(file_path)[0]
    
    def visualize(self) -> Dict[str, Any]:
        """Return visualization data for this media file"""
        if not os.path.exists(self.file_path):
            return {
                'type': 'error',
                'content': f"File not found: {self.file_path}",
                'mime_type': 'text/plain',
                'metadata': {'description': self.description}
            }
        
        # Determine visualization type based on MIME type
        if self.mime_type:
            if self.mime_type.startswith('image/'):
                return {
                    'type': 'image',
                    'content': self.file_path,
                    'mime_type': self.mime_type,
                    'metadata': {
                        'description': self.description,
                        'file_size': os.path.getsize(self.file_path),
                        'file_name': os.path.basename(self.file_path)
                    }
                }
            elif self.mime_type.startswith('audio/'):
                return {
                    'type': 'audio',
                    'content': self.file_path,
                    'mime_type': self.mime_type,
                    'metadata': {
                        'description': self.description,
                        'file_size': os.path.getsize(self.file_path),
                        'file_name': os.path.basename(self.file_path)
                    }
                }
            elif self.mime_type.startswith('video/'):
                return {
                    'type': 'video',
                    'content': self.file_path,
                    'mime_type': self.mime_type,
                    'metadata': {
                        'description': self.description,
                        'file_size': os.path.getsize(self.file_path),
                        'file_name': os.path.basename(self.file_path)
                    }
                }
        
        # Default to text display
        return {
            'type': 'file',
            'content': self.file_path,
            'mime_type': self.mime_type or 'application/octet-stream',
            'metadata': {
                'description': self.description,
                'file_size': os.path.getsize(self.file_path),
                'file_name': os.path.basename(self.file_path)
            }
        }
    
    def __str__(self):
        return f"MediaFile({self.file_path}): {self.description}"


class InteractiveHTML(VisualizableObject):
    """HTML content that can be displayed interactively"""
    
    def __init__(self, html_content: str, description: str = ""):
        self.html_content = html_content
        self.description = description
    
    def visualize(self) -> Dict[str, Any]:
        return {
            'type': 'html',
            'content': self.html_content,
            'mime_type': 'text/html',
            'metadata': {'description': self.description}
        }
    
    def __str__(self):
        return f"InteractiveHTML: {self.description}"


class VisualizableData(VisualizableObject):
    """Generic data that can be displayed as JSON or table"""
    
    def __init__(self, data: Any, description: str = "", display_as: str = "json"):
        self.data = data
        self.description = description
        self.display_as = display_as  # 'json', 'table', 'chart'
    
    def visualize(self) -> Dict[str, Any]:
        return {
            'type': self.display_as,
            'content': self.data,
            'mime_type': 'application/json',
            'metadata': {
                'description': self.description,
                'data_type': type(self.data).__name__
            }
        }
    
    def __str__(self):
        return f"VisualizableData({self.display_as}): {self.description}"


def make_visualizable(obj: Any, description: str = "") -> VisualizableObject:
    """
    Convert any object into a visualizable object.
    
    This is the main entry point for logging objects that should be clickable.
    """
    if isinstance(obj, VisualizableObject):
        return obj
    
    if isinstance(obj, str) and os.path.exists(obj):
        # File path - check if it's a media file
        return MediaFile(obj, description)
    
    if isinstance(obj, dict) and 'file_path' in obj:
        # Dict with file_path key
        file_path = obj['file_path']
        desc = obj.get('description', description)
        return MediaFile(file_path, desc)
    
    # Default to data visualization
    return VisualizableData(obj, description)


def is_visualizable(obj: Any) -> bool:
    """Check if an object can be made visualizable"""
    if isinstance(obj, VisualizableObject):
        return True
    
    if isinstance(obj, str) and os.path.exists(obj):
        return True
    
    if isinstance(obj, dict) and 'file_path' in obj:
        return True
    
    return True  # All objects can be visualized as data


# Integration with logging system
def enhance_log_entry_for_visualization(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance a log entry with visualization metadata.
    
    This function is called by the log manager to detect visualizable content.
    """
    enhanced_entry = log_entry.copy()
    
    # Check if the data field contains visualizable content
    data = log_entry.get('data')
    if data and is_visualizable(data):
        visualizable = make_visualizable(data)
        enhanced_entry['visualizable'] = True
        enhanced_entry['visualization_type'] = visualizable.visualize()['type']
        
        # Add click handler metadata
        enhanced_entry['click_action'] = 'visualize'
        enhanced_entry['visualization_id'] = f"viz_{hash(str(data))}"
    
    return enhanced_entry