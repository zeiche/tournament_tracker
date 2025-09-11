#!/usr/bin/env python3
"""
Visualization Services Module - Proper visualization architecture

This module handles all visualization requests and orchestrates:
- Database Services (for raw data)
- Math Services (for processing)
- Graphics Services (for rendering)

The database should never know about "heatmaps" - that's visualization logic.
"""

import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core import announcer

# Import visualization services
from .heatmap_service import HeatmapService
from .chart_service import ChartService
from .map_service import MapService

# Create global instances
heatmap_service = HeatmapService()
chart_service = ChartService()
map_service = MapService()

# Announce individual services to avoid duplication
announcer.announce(
    "Heatmap Service",
    [
        "Tournament location heatmap generation",
        "Player distribution heatmaps", 
        "Organization venue heatmaps",
        "Polymorphic ask/tell/do interface"
    ]
)

announcer.announce(
    "Chart Service",
    [
        "Chart and graph generation for tournament data",
        "Player ranking visualizations",
        "Tournament statistics charts", 
        "Polymorphic ask/tell/do interface"
    ]
)

announcer.announce(
    "Map Service",
    [
        "Interactive map generation",
        "Tournament location mapping",
        "Geographic visualizations",
        "Polymorphic ask/tell/do interface"
    ]
)

__all__ = [
    'heatmap_service',
    'chart_service', 
    'map_service',
    'HeatmapService',
    'ChartService',
    'MapService'
]