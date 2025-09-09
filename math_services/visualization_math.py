#!/usr/bin/env python3
"""
Visualization Math Service - Mathematical operations for data visualization

Handles:
- Heatmap data processing and calculations
- Scaling and normalization for visualizations  
- Color mapping and intensity calculations
- Density calculations and spatial distribution
"""

import sys
import os
from typing import Any, List, Tuple, Dict, Optional, Union
import math
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer


class VisualizationMathService:
    """Mathematical operations for data visualization with ask/tell/do interface"""
    
    def __init__(self):
        # Announce capabilities via Bonjour
        announcer.announce(
            "Visualization Math Service",
            [
                "Mathematical operations for data visualization",
                "Heatmap data processing and weight calculations", 
                "Logarithmic and linear scaling algorithms",
                "Color intensity mapping",
                "Spatial density calculations",
                "Data normalization for visual balance",
                "Polymorphic ask/tell/do interface"
            ],
            examples=[
                "ask('heatmap weights for tournament data')",
                "ask('log scale attendance numbers')",
                "tell('json', processed_weights)",
                "do('normalize data for visualization')"
            ]
        )
    
    def ask(self, query: str, data: Any = None, **kwargs) -> Any:
        """Process visualization math queries"""
        query_lower = query.lower().strip()
        
        # Heatmap processing
        if 'heatmap' in query_lower:
            if 'weight' in query_lower or 'weights' in query_lower:
                return self._calculate_heatmap_weights(data, **kwargs)
            elif 'data' in query_lower:
                return self._process_heatmap_data(data, **kwargs)
        
        # Scaling operations
        elif 'log scale' in query_lower or 'logarithmic' in query_lower:
            return self._logarithmic_scale(data, **kwargs)
        elif 'linear scale' in query_lower:
            return self._linear_scale(data, **kwargs)
        elif 'normalize' in query_lower:
            return self._normalize_data(data, **kwargs)
        
        # Density calculations
        elif 'density' in query_lower:
            return self._calculate_density(data, **kwargs)
        
        # Color mapping
        elif 'color' in query_lower and 'map' in query_lower:
            return self._color_mapping(data, **kwargs)
            
        else:
            return f"Unknown visualization math query: {query}"
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format visualization math results"""
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "discord":
            if isinstance(data, list):
                return f"Processed {len(data)} data points for visualization"
            elif isinstance(data, dict):
                return f"Visualization data: {list(data.keys())}"
            else:
                return f"Visualization result: {data}"
        elif format == "tuple":
            if isinstance(data, list) and data:
                return str(data)
            else:
                return str(data)
        else:
            return str(data)
    
    def do(self, action: str, data: Any = None, **kwargs) -> Any:
        """Perform visualization math actions"""
        action_lower = action.lower().strip()
        
        if 'process' in action_lower and 'heatmap' in action_lower:
            return self._process_heatmap_data(data, **kwargs)
        elif 'calculate' in action_lower and 'weight' in action_lower:
            return self._calculate_heatmap_weights(data, **kwargs) 
        elif 'normalize' in action_lower:
            return self._normalize_data(data, **kwargs)
        elif 'scale' in action_lower:
            if 'log' in action_lower:
                return self._logarithmic_scale(data, **kwargs)
            else:
                return self._linear_scale(data, **kwargs)
        else:
            return f"Unknown visualization math action: {action}"
    
    # Private methods - actual math operations
    
    def _calculate_heatmap_weights(self, data: Any, **kwargs) -> List[float]:
        """
        Calculate weights for heatmap visualization.
        Moved from database service and tournament models.
        """
        if not data:
            return []
        
        weights = []
        scale_type = kwargs.get('scale', 'log')  # 'log' or 'linear'
        
        for item in data:
            # Handle different data formats polymorphically
            if isinstance(item, dict):
                value = item.get('num_attendees') or item.get('attendance') or item.get('value', 1)
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                value = item[2]  # Assume (lat, lng, weight) format
            elif hasattr(item, 'num_attendees'):
                value = item.num_attendees or 1
            elif hasattr(item, 'get_heatmap_weight'):
                # Use model's own weight calculation
                weights.append(item.get_heatmap_weight())
                continue
            else:
                value = 1
            
            # Calculate weight based on scale type
            if scale_type == 'log':
                weights.append(math.log10(max(value, 1)))
            else:
                weights.append(float(value))
        
        return weights
    
    def _process_heatmap_data(self, data: Any, **kwargs) -> List[Tuple[float, float, float]]:
        """
        Process data into heatmap format: [(lat, lng, weight), ...]
        Moved from database service.
        """
        if not data:
            return []
        
        processed = []
        
        for item in data:
            # Extract coordinates and weight polymorphically
            if isinstance(item, dict):
                lat = item.get('lat') or item.get('latitude')
                lng = item.get('lng') or item.get('longitude')
                weight = item.get('num_attendees') or item.get('weight', 1)
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                lat, lng, weight = item[0], item[1], item[2]
            elif hasattr(item, 'lat') and hasattr(item, 'lng'):
                lat = item.lat
                lng = item.lng
                weight = getattr(item, 'num_attendees', 1) or 1
                
                # Use model's heatmap weight if available
                if hasattr(item, 'get_heatmap_weight'):
                    weight = item.get_heatmap_weight()
            else:
                continue  # Skip items without location data
            
            if lat is not None and lng is not None:
                processed.append((float(lat), float(lng), float(weight)))
        
        return processed
    
    def _logarithmic_scale(self, data: List[Union[int, float]], **kwargs) -> List[float]:
        """Apply logarithmic scaling to data"""
        if not data:
            return []
        
        base = kwargs.get('base', 10)
        min_value = kwargs.get('min_value', 1)
        
        return [math.log(max(value, min_value), base) for value in data]
    
    def _linear_scale(self, data: List[Union[int, float]], **kwargs) -> List[float]:
        """Apply linear scaling to data"""
        if not data:
            return []
        
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val
        
        if range_val == 0:
            return [0.5] * len(data)  # All values the same
        
        target_min = kwargs.get('target_min', 0.0)
        target_max = kwargs.get('target_max', 1.0)
        target_range = target_max - target_min
        
        return [
            target_min + ((value - min_val) / range_val) * target_range 
            for value in data
        ]
    
    def _normalize_data(self, data: List[Union[int, float]], **kwargs) -> List[float]:
        """Normalize data to prevent large values from dominating"""
        if not data:
            return []
        
        method = kwargs.get('method', 'minmax')  # 'minmax', 'zscore', 'log'
        
        if method == 'log':
            return self._logarithmic_scale(data, **kwargs)
        elif method == 'minmax':
            return self._linear_scale(data, target_min=0.0, target_max=1.0)
        elif method == 'zscore':
            # Z-score normalization
            mean_val = sum(data) / len(data)
            variance = sum((x - mean_val) ** 2 for x in data) / len(data)
            std_dev = math.sqrt(variance)
            
            if std_dev == 0:
                return [0.0] * len(data)
            
            return [(value - mean_val) / std_dev for value in data]
        else:
            return list(data)  # No normalization
    
    def _calculate_density(self, data: List[Tuple[float, float]], **kwargs) -> Dict[str, float]:
        """Calculate spatial density metrics"""
        if not data:
            return {}
        
        # Basic density calculation
        # For more sophisticated density, we'd use scipy.stats.gaussian_kde
        
        lats = [point[0] for point in data]
        lngs = [point[1] for point in data]
        
        lat_range = max(lats) - min(lats)
        lng_range = max(lngs) - min(lngs)
        area = lat_range * lng_range
        
        return {
            'point_count': len(data),
            'density': len(data) / area if area > 0 else 0,
            'lat_range': lat_range,
            'lng_range': lng_range,
            'area': area
        }
    
    def _color_mapping(self, values: List[float], **kwargs) -> List[str]:
        """Map values to colors for visualization"""
        if not values:
            return []
        
        colormap = kwargs.get('colormap', 'heat')  # 'heat', 'cool', 'rainbow'
        
        # Normalize values to 0-1 range
        normalized = self._linear_scale(values, target_min=0.0, target_max=1.0)
        
        colors = []
        for val in normalized:
            if colormap == 'heat':
                # Red to yellow heat colors
                red = int(255 * min(val * 2, 1.0))
                green = int(255 * max(0, (val - 0.5) * 2))
                blue = 0
                colors.append(f'#{red:02x}{green:02x}{blue:02x}')
            else:
                # Default grayscale
                gray = int(255 * val)
                colors.append(f'#{gray:02x}{gray:02x}{gray:02x}')
        
        return colors


# Create global instance for easy access
visualization_math = VisualizationMathService()