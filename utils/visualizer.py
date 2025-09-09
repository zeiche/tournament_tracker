#!/usr/bin/env python3
"""
visualizer.py - Compatibility shim for graphics_service
This file maintains backward compatibility while redirecting to the new GraphicsService
"""

# Import everything from graphics_service
from graphics_service import *

# Create compatibility aliases
UnifiedVisualizer = GraphicsService

# Re-export for convenience
__all__ = ['GraphicsService', 'UnifiedVisualizer', 'visualize', 'heatmap', 'map', 'chart']