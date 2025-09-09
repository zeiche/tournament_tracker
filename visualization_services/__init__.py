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

# Announce the module
announcer.announce(
    "Visualization Services Module",
    [
        "Orchestrates visualization requests across multiple services",
        "Separates data concerns from visualization concerns",
        "Heatmap generation and processing",
        "Chart and graph creation",
        "Interactive map generation",
        "Coordinates database, math, and graphics services",
        "Polymorphic ask/tell/do interface for all visualizations"
    ],
    examples=[
        "heatmap_service.ask('tournament heatmap')",
        "chart_service.ask('player rankings chart')", 
        "map_service.ask('tournament locations map')"
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