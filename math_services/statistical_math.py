#!/usr/bin/env python3
"""
Statistical Math Service - Advanced statistical operations

Handles:
- Gaussian kernel density estimation (KDE)
- Statistical distributions and analysis
- Clustering algorithms
- Regression analysis
"""

import sys
import os
from typing import Any, List, Tuple, Dict, Optional, Union
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer


class StatisticalMathService:
    """Statistical mathematical operations with ask/tell/do interface"""
    
    def __init__(self):
        # Announce capabilities via Bonjour
        announcer.announce(
            "Statistical Math Service", 
            [
                "Advanced statistical mathematical operations",
                "Gaussian kernel density estimation (KDE)",
                "Statistical distributions and analysis",
                "Data clustering algorithms",
                "Correlation and regression analysis", 
                "Lazy-loaded heavy dependencies (scipy, numpy)",
                "Polymorphic ask/tell/do interface"
            ],
            examples=[
                "ask('gaussian kde for heatmap')",
                "ask('cluster tournament locations')",
                "tell('numpy', kde_result)",
                "do('calculate distribution')"
            ]
        )
    
    def ask(self, query: str, data: Any = None, **kwargs) -> Any:
        """Process statistical queries"""
        query_lower = query.lower().strip()
        
        # Gaussian KDE operations
        if 'gaussian' in query_lower and 'kde' in query_lower:
            return self._gaussian_kde(data, **kwargs)
        elif 'kde' in query_lower:
            return self._gaussian_kde(data, **kwargs)
        
        # Clustering
        elif 'cluster' in query_lower:
            return self._cluster_data(data, **kwargs)
        
        # Statistical analysis
        elif 'distribution' in query_lower:
            return self._analyze_distribution(data, **kwargs)
        elif 'correlation' in query_lower:
            return self._correlation_analysis(data, **kwargs)
        elif 'regression' in query_lower:
            return self._regression_analysis(data, **kwargs)
        
        else:
            return f"Unknown statistical query: {query}"
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format statistical results"""
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "discord":
            if hasattr(data, 'shape'):  # numpy array
                return f"Statistical result: {data.shape} array"
            elif isinstance(data, list):
                return f"Statistical analysis of {len(data)} data points"
            else:
                return f"Statistical result: {type(data).__name__}"
        elif format == "numpy":
            # Return raw numpy data for other services
            return data
        else:
            return str(data)
    
    def do(self, action: str, data: Any = None, **kwargs) -> Any:
        """Perform statistical actions"""
        action_lower = action.lower().strip()
        
        if 'calculate' in action_lower:
            if 'kde' in action_lower:
                return self._gaussian_kde(data, **kwargs)
            elif 'distribution' in action_lower:
                return self._analyze_distribution(data, **kwargs)
        elif 'cluster' in action_lower:
            return self._cluster_data(data, **kwargs)
        elif 'analyze' in action_lower:
            return self._analyze_distribution(data, **kwargs)
        else:
            return f"Unknown statistical action: {action}"
    
    # Private methods - statistical operations
    
    def _gaussian_kde(self, data: Any, **kwargs) -> Any:
        """
        Gaussian Kernel Density Estimation.
        Lazy-loads scipy for performance.
        """
        try:
            from scipy.stats import gaussian_kde
            import numpy as np
        except ImportError:
            return {
                'error': 'scipy not available',
                'install': 'pip3 install scipy numpy'
            }
        
        if not data:
            return None
        
        # Convert data to appropriate format
        if isinstance(data, list) and data:
            if isinstance(data[0], (list, tuple)) and len(data[0]) >= 2:
                # 2D data: [(x, y), ...]  
                points = np.array(data)
                if points.shape[1] >= 2:
                    kde = gaussian_kde([points[:, 0], points[:, 1]])
                else:
                    kde = gaussian_kde(points.flatten())
            else:
                # 1D data
                kde = gaussian_kde(data)
        else:
            return None
        
        # Return the KDE object for further use
        return kde
    
    def _cluster_data(self, data: Any, **kwargs) -> Dict[str, Any]:
        """
        Simple clustering analysis.
        For advanced clustering, would use sklearn.
        """
        if not data:
            return {}
        
        # Simple clustering based on distance
        # This is a placeholder - real clustering would use sklearn
        
        if isinstance(data, list) and data:
            if isinstance(data[0], (list, tuple)) and len(data[0]) >= 2:
                # 2D clustering
                return self._simple_2d_clustering(data, **kwargs)
        
        return {'clusters': [], 'method': 'simple'}
    
    def _simple_2d_clustering(self, points: List[Tuple[float, float]], **kwargs) -> Dict[str, Any]:
        """Simple 2D clustering algorithm"""
        if not points:
            return {'clusters': []}
        
        threshold = kwargs.get('threshold', 0.1)  # Distance threshold
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
                    
                # Simple Euclidean distance
                dist = ((point[0] - other_point[0])**2 + (point[1] - other_point[1])**2)**0.5
                if dist < threshold:
                    cluster.append(j)
                    used[j] = True
            
            clusters.append(cluster)
        
        return {
            'clusters': clusters,
            'cluster_count': len(clusters),
            'method': 'simple_distance',
            'threshold': threshold
        }
    
    def _analyze_distribution(self, data: Any, **kwargs) -> Dict[str, float]:
        """Basic statistical distribution analysis"""
        if not data or not isinstance(data, list):
            return {}
        
        # Convert to numbers
        numbers = []
        for item in data:
            if isinstance(item, (int, float)):
                numbers.append(float(item))
            elif hasattr(item, '__float__'):
                numbers.append(float(item))
        
        if not numbers:
            return {}
        
        n = len(numbers)
        mean = sum(numbers) / n
        variance = sum((x - mean) ** 2 for x in numbers) / n
        std_dev = variance ** 0.5
        
        sorted_nums = sorted(numbers)
        median = sorted_nums[n // 2] if n % 2 == 1 else (sorted_nums[n//2-1] + sorted_nums[n//2]) / 2
        
        return {
            'count': n,
            'mean': mean,
            'median': median,
            'std_dev': std_dev,
            'variance': variance,
            'min': min(numbers),
            'max': max(numbers),
            'range': max(numbers) - min(numbers)
        }
    
    def _correlation_analysis(self, data: Any, **kwargs) -> Dict[str, float]:
        """Basic correlation analysis"""
        # Placeholder for correlation analysis
        # Would implement Pearson/Spearman correlation
        return {'correlation': 0.0, 'method': 'placeholder'}
    
    def _regression_analysis(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Basic regression analysis"""
        # Placeholder for regression analysis
        # Would implement linear/polynomial regression
        return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0}


# Create global instance
statistical_math = StatisticalMathService()