#!/usr/bin/env python3
"""
Geometric Math Service - Spatial and geometric calculations

Handles:
- Distance calculations (Euclidean, Haversine)
- Spatial relationships and proximity
- Geographic coordinate transformations
- Geometric shape analysis
"""

import sys
import os
from typing import Any, List, Tuple, Dict, Optional, Union
import math
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer


class GeometricMathService:
    """Geometric mathematical operations with ask/tell/do interface"""
    
    def __init__(self):
        # Announce capabilities via Bonjour
        announcer.announce(
            "Geometric Math Service",
            [
                "Spatial and geometric mathematical operations",
                "Distance calculations (Euclidean, Haversine)",
                "Geographic coordinate transformations",
                "Proximity and spatial relationship analysis",
                "Geometric shape calculations",
                "Tournament location spatial analysis",
                "Polymorphic ask/tell/do interface"
            ],
            examples=[
                "ask('distance between tournaments')",
                "ask('nearest venues to point')",
                "tell('json', distances)",
                "do('calculate tournament clusters by distance')"
            ]
        )
    
    def ask(self, query: str, data: Any = None, **kwargs) -> Any:
        """Process geometric queries"""
        query_lower = query.lower().strip()
        
        # Distance calculations
        if 'distance' in query_lower:
            if 'haversine' in query_lower:
                return self._haversine_distance(data, **kwargs)
            else:
                return self._calculate_distances(data, **kwargs)
        
        # Proximity analysis
        elif 'nearest' in query_lower or 'closest' in query_lower:
            return self._find_nearest(data, **kwargs)
        elif 'within' in query_lower:
            return self._within_radius(data, **kwargs)
        
        # Spatial analysis
        elif 'cluster' in query_lower and ('location' in query_lower or 'spatial' in query_lower):
            return self._spatial_clustering(data, **kwargs)
        elif 'center' in query_lower or 'centroid' in query_lower:
            return self._calculate_centroid(data, **kwargs)
        
        # Shape analysis
        elif 'bounds' in query_lower or 'bounding' in query_lower:
            return self._calculate_bounds(data, **kwargs)
        elif 'area' in query_lower:
            return self._calculate_area(data, **kwargs)
        
        else:
            return f"Unknown geometric query: {query}"
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format geometric results"""
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "discord":
            if isinstance(data, dict):
                if 'distance' in data:
                    return f"Distance: {data['distance']:.2f} km"
                elif 'center' in data:
                    return f"Center: ({data['center'][0]:.4f}, {data['center'][1]:.4f})"
                else:
                    return f"Geometric result: {list(data.keys())}"
            elif isinstance(data, list):
                return f"Geometric analysis of {len(data)} points"
            else:
                return f"Geometric result: {data}"
        else:
            return str(data)
    
    def do(self, action: str, data: Any = None, **kwargs) -> Any:
        """Perform geometric actions"""
        action_lower = action.lower().strip()
        
        if 'calculate' in action_lower:
            if 'distance' in action_lower:
                return self._calculate_distances(data, **kwargs)
            elif 'center' in action_lower:
                return self._calculate_centroid(data, **kwargs)
            elif 'bounds' in action_lower:
                return self._calculate_bounds(data, **kwargs)
        elif 'find' in action_lower and 'nearest' in action_lower:
            return self._find_nearest(data, **kwargs)
        elif 'cluster' in action_lower:
            return self._spatial_clustering(data, **kwargs)
        else:
            return f"Unknown geometric action: {action}"
    
    # Private methods - geometric operations
    
    def _calculate_distances(self, data: Any, **kwargs) -> Any:
        """Calculate distances between points"""
        if not data:
            return []
        
        method = kwargs.get('method', 'euclidean')  # 'euclidean' or 'haversine'
        
        if isinstance(data, list) and len(data) >= 2:
            if method == 'haversine':
                return self._haversine_distance(data, **kwargs)
            else:
                return self._euclidean_distance(data, **kwargs)
        
        return 0.0
    
    def _euclidean_distance(self, points: List[Tuple[float, float]], **kwargs) -> Union[float, List[float]]:
        """Calculate Euclidean distance between points"""
        if len(points) == 2:
            # Distance between two points
            p1, p2 = points[0], points[1]
            return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        else:
            # Distance matrix for multiple points
            distances = []
            for i in range(len(points)):
                row = []
                for j in range(len(points)):
                    if i == j:
                        row.append(0.0)
                    else:
                        p1, p2 = points[i], points[j]
                        dist = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                        row.append(dist)
                distances.append(row)
            return distances
    
    def _haversine_distance(self, points: List[Tuple[float, float]], **kwargs) -> Union[float, Dict[str, float]]:
        """
        Calculate Haversine distance between geographic coordinates.
        Returns distance in kilometers.
        """
        if len(points) < 2:
            return 0.0
        
        lat1, lon1 = math.radians(points[0][0]), math.radians(points[0][1])
        lat2, lon2 = math.radians(points[1][0]), math.radians(points[1][1])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        distance_km = c * r
        
        return {
            'distance_km': distance_km,
            'distance_miles': distance_km * 0.621371,
            'method': 'haversine'
        }
    
    def _find_nearest(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Find nearest points to a reference point"""
        if not data:
            return {}
        
        reference = kwargs.get('reference') or kwargs.get('to')
        if not reference:
            return {'error': 'No reference point provided'}
        
        distances = []
        for i, point in enumerate(data):
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                dist = self._euclidean_distance([reference, point[:2]])
                distances.append((i, point, dist))
        
        # Sort by distance
        distances.sort(key=lambda x: x[2])
        
        count = kwargs.get('count', 5)  # Return top 5 by default
        nearest = distances[:count]
        
        return {
            'reference': reference,
            'nearest': [{'index': i, 'point': pt, 'distance': dist} for i, pt, dist in nearest],
            'total_analyzed': len(data)
        }
    
    def _within_radius(self, data: Any, **kwargs) -> List[Dict[str, Any]]:
        """Find points within a specified radius"""
        if not data:
            return []
        
        center = kwargs.get('center') or kwargs.get('reference')
        radius = kwargs.get('radius', 1.0)
        
        if not center:
            return []
        
        within = []
        for i, point in enumerate(data):
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                dist = self._euclidean_distance([center, point[:2]])
                if dist <= radius:
                    within.append({
                        'index': i,
                        'point': point,
                        'distance': dist
                    })
        
        return within
    
    def _spatial_clustering(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Simple spatial clustering based on proximity"""
        if not data:
            return {'clusters': []}
        
        threshold = kwargs.get('threshold', 0.1)  # Distance threshold
        points = []
        
        # Extract points
        for item in data:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                points.append((float(item[0]), float(item[1])))
            elif hasattr(item, 'lat') and hasattr(item, 'lng'):
                points.append((float(item.lat), float(item.lng)))
        
        if not points:
            return {'clusters': []}
        
        clusters = []
        used = [False] * len(points)
        
        for i, point in enumerate(points):
            if used[i]:
                continue
            
            # Start new cluster
            cluster = [i]
            used[i] = True
            
            # Find nearby points
            for j, other_point in enumerate(points):
                if used[j]:
                    continue
                
                dist = self._euclidean_distance([point, other_point])
                if dist <= threshold:
                    cluster.append(j)
                    used[j] = True
            
            clusters.append(cluster)
        
        return {
            'clusters': clusters,
            'cluster_count': len(clusters),
            'points_analyzed': len(points),
            'method': 'proximity',
            'threshold': threshold
        }
    
    def _calculate_centroid(self, data: Any, **kwargs) -> Dict[str, float]:
        """Calculate the centroid (center point) of a set of coordinates"""
        if not data:
            return {}
        
        lats = []
        lngs = []
        
        for item in data:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                lats.append(float(item[0]))
                lngs.append(float(item[1]))
            elif hasattr(item, 'lat') and hasattr(item, 'lng'):
                if item.lat is not None and item.lng is not None:
                    lats.append(float(item.lat))
                    lngs.append(float(item.lng))
        
        if not lats or not lngs:
            return {}
        
        return {
            'center': (sum(lats) / len(lats), sum(lngs) / len(lngs)),
            'lat': sum(lats) / len(lats),
            'lng': sum(lngs) / len(lngs),
            'points_used': len(lats)
        }
    
    def _calculate_bounds(self, data: Any, **kwargs) -> Dict[str, float]:
        """Calculate bounding box for a set of points"""
        if not data:
            return {}
        
        lats = []
        lngs = []
        
        for item in data:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                lats.append(float(item[0]))
                lngs.append(float(item[1]))
            elif hasattr(item, 'lat') and hasattr(item, 'lng'):
                if item.lat is not None and item.lng is not None:
                    lats.append(float(item.lat))
                    lngs.append(float(item.lng))
        
        if not lats or not lngs:
            return {}
        
        return {
            'min_lat': min(lats),
            'max_lat': max(lats),
            'min_lng': min(lngs),
            'max_lng': max(lngs),
            'width': max(lngs) - min(lngs),
            'height': max(lats) - min(lats),
            'points_analyzed': len(lats)
        }
    
    def _calculate_area(self, data: Any, **kwargs) -> float:
        """Calculate area of bounding box"""
        bounds = self._calculate_bounds(data, **kwargs)
        if not bounds:
            return 0.0
        
        return bounds.get('width', 0) * bounds.get('height', 0)


# Create global instance
geometric_math = GeometricMathService()