#!/usr/bin/env python3
"""
Math Services Module - Bonjour-advertised mathematical operations

This module provides specialized mathematical services via Bonjour announcements:
- Statistical Math: gaussian_kde, distributions, clustering
- Geometric Math: distances, spatial calculations  
- Visualization Math: heatmap calculations, scaling, normalization
- Data Transforms: logarithmic scaling, data preprocessing

All services follow the polymorphic ask/tell/do pattern.
"""

import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from polymorphic_core import announcer

# Import all math services to trigger announcements
from .statistical_math import StatisticalMathService
from .geometric_math import GeometricMathService  
from .visualization_math import VisualizationMathService
from .data_transforms import DataTransformService

# Create global instances
statistical_math = StatisticalMathService()
geometric_math = GeometricMathService()
visualization_math = VisualizationMathService()
data_transforms = DataTransformService()

# Announce the module
announcer.announce(
    "Math Services Module",
    [
        "Centralized mathematical operations with Bonjour discovery",
        "Statistical analysis and distributions",
        "Geometric calculations and spatial math",
        "Visualization data processing",
        "Data transformations and scaling",
        "All services use ask/tell/do polymorphic interface"
    ],
    examples=[
        "statistical_math.ask('gaussian kde for data')",
        "geometric_math.ask('distance between points')",
        "visualization_math.ask('heatmap weights')",
        "data_transforms.ask('log scale data')"
    ]
)

__all__ = [
    'statistical_math',
    'geometric_math', 
    'visualization_math',
    'data_transforms',
    'StatisticalMathService',
    'GeometricMathService',
    'VisualizationMathService', 
    'DataTransformService'
]