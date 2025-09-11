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

# Announce individual services instead of duplicating
announcer.announce(
    "Statistical Math Service",
    [
        "Advanced statistical mathematical operations",
        "Gaussian kernel density estimation (KDE)",
        "Statistical distributions and analysis", 
        "Data clustering algorithms",
        "Polymorphic ask/tell/do interface"
    ]
)

announcer.announce(
    "Geometric Math Service",
    [
        "Geometric calculations and spatial math",
        "Distance calculations between points",
        "Spatial transformations",
        "Polymorphic ask/tell/do interface"
    ]
)

announcer.announce(
    "Visualization Math Service", 
    [
        "Mathematical operations for visualizations",
        "Heatmap weight calculations",
        "Data scaling and normalization",
        "Polymorphic ask/tell/do interface"
    ]
)

announcer.announce(
    "Data Transform Service",
    [
        "Data transformations and preprocessing", 
        "Logarithmic scaling",
        "Data normalization",
        "Polymorphic ask/tell/do interface"
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