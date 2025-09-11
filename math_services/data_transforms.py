#!/usr/bin/env python3
"""
Data Transforms Service - Data preprocessing and transformation

Handles:
- Data normalization and scaling
- Type conversions and cleaning
- Data aggregation and grouping  
- Missing value handling
- Data format transformations
"""

import sys
import os
from typing import Any, List, Tuple, Dict, Optional, Union
import json
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer


class DataTransformService:
    """Data transformation operations with ask/tell/do interface"""
    
    def __init__(self):
        pass
    
    def ask(self, query: str, data: Any = None, **kwargs) -> Any:
        """Process data transformation queries"""
        query_lower = query.lower().strip()
        
        # Normalization and scaling
        if 'normalize' in query_lower:
            return self._normalize_data(data, **kwargs)
        elif 'scale' in query_lower:
            return self._scale_data(data, **kwargs)
        
        # Data cleaning
        elif 'clean' in query_lower:
            if 'missing' in query_lower:
                return self._handle_missing_values(data, **kwargs)
            else:
                return self._clean_data(data, **kwargs)
        
        # Aggregation
        elif 'aggregate' in query_lower or 'group' in query_lower:
            return self._aggregate_data(data, **kwargs)
        elif 'count' in query_lower:
            return self._count_values(data, **kwargs)
        
        # Type conversions
        elif 'convert' in query_lower:
            return self._convert_types(data, **kwargs)
        
        # Format transformations
        elif 'transform' in query_lower or 'format' in query_lower:
            return self._transform_format(data, **kwargs)
        
        else:
            return f"Unknown data transform query: {query}"
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format data transformation results"""
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "discord":
            if isinstance(data, list):
                return f"Transformed {len(data)} data items"
            elif isinstance(data, dict):
                return f"Data transformation: {list(data.keys())}"
            else:
                return f"Transform result: {type(data).__name__}"
        elif format == "csv":
            return self._to_csv(data)
        else:
            return str(data)
    
    def do(self, action: str, data: Any = None, **kwargs) -> Any:
        """Perform data transformation actions"""
        action_lower = action.lower().strip()
        
        if 'normalize' in action_lower:
            return self._normalize_data(data, **kwargs)
        elif 'clean' in action_lower:
            return self._clean_data(data, **kwargs)
        elif 'aggregate' in action_lower:
            return self._aggregate_data(data, **kwargs)
        elif 'transform' in action_lower:
            return self._transform_format(data, **kwargs)
        elif 'convert' in action_lower:
            return self._convert_types(data, **kwargs)
        else:
            return f"Unknown data transform action: {action}"
    
    # Private methods - transformation operations
    
    def _normalize_data(self, data: Any, **kwargs) -> Any:
        """Normalize data values"""
        if not data:
            return data
        
        method = kwargs.get('method', 'minmax')  # 'minmax', 'zscore', 'unit'
        
        if isinstance(data, list):
            if all(isinstance(x, (int, float)) for x in data):
                # List of numbers
                return self._normalize_numbers(data, method)
            else:
                # List of objects
                field = kwargs.get('field', 'value')
                return self._normalize_objects(data, field, method)
        
        return data
    
    def _normalize_numbers(self, numbers: List[Union[int, float]], method: str) -> List[float]:
        """Normalize a list of numbers"""
        if not numbers:
            return []
        
        if method == 'minmax':
            min_val = min(numbers)
            max_val = max(numbers)
            range_val = max_val - min_val
            
            if range_val == 0:
                return [0.5] * len(numbers)
            
            return [(x - min_val) / range_val for x in numbers]
        
        elif method == 'zscore':
            mean = sum(numbers) / len(numbers)
            variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
            std_dev = variance ** 0.5
            
            if std_dev == 0:
                return [0.0] * len(numbers)
            
            return [(x - mean) / std_dev for x in numbers]
        
        elif method == 'unit':
            # Unit vector normalization
            magnitude = sum(x * x for x in numbers) ** 0.5
            if magnitude == 0:
                return numbers
            return [x / magnitude for x in numbers]
        
        return numbers
    
    def _normalize_objects(self, objects: List[Any], field: str, method: str) -> List[Any]:
        """Normalize a specific field in objects"""
        # Extract values
        values = []
        for obj in objects:
            if isinstance(obj, dict):
                values.append(obj.get(field, 0))
            elif hasattr(obj, field):
                values.append(getattr(obj, field, 0))
            else:
                values.append(0)
        
        # Normalize values
        normalized_values = self._normalize_numbers(values, method)
        
        # Update objects
        result = []
        for i, obj in enumerate(objects):
            if isinstance(obj, dict):
                new_obj = obj.copy()
                new_obj[f'{field}_normalized'] = normalized_values[i]
                result.append(new_obj)
            else:
                result.append(obj)  # Can't modify non-dict objects
        
        return result
    
    def _scale_data(self, data: Any, **kwargs) -> Any:
        """Scale data to a specific range"""
        target_min = kwargs.get('min', 0.0)
        target_max = kwargs.get('max', 1.0)
        
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            min_val = min(data)
            max_val = max(data)
            range_val = max_val - min_val
            
            if range_val == 0:
                return [target_min] * len(data)
            
            target_range = target_max - target_min
            return [target_min + ((x - min_val) / range_val) * target_range for x in data]
        
        return data
    
    def _handle_missing_values(self, data: Any, **kwargs) -> Any:
        """Handle missing values in data"""
        if not data:
            return data
        
        strategy = kwargs.get('strategy', 'remove')  # 'remove', 'mean', 'median', 'zero'
        
        if isinstance(data, list):
            if strategy == 'remove':
                return [item for item in data if item is not None and item != '']
            elif strategy == 'zero':
                return [item if item is not None and item != '' else 0 for item in data]
            elif strategy in ['mean', 'median']:
                # Calculate replacement value
                valid_numbers = [x for x in data if isinstance(x, (int, float)) and x is not None]
                if valid_numbers:
                    if strategy == 'mean':
                        replacement = sum(valid_numbers) / len(valid_numbers)
                    else:  # median
                        sorted_nums = sorted(valid_numbers)
                        n = len(sorted_nums)
                        replacement = sorted_nums[n//2] if n % 2 == 1 else (sorted_nums[n//2-1] + sorted_nums[n//2]) / 2
                    
                    return [item if item is not None and item != '' else replacement for item in data]
        
        return data
    
    def _clean_data(self, data: Any, **kwargs) -> Any:
        """General data cleaning"""
        if not data:
            return data
        
        # Remove missing values first
        cleaned = self._handle_missing_values(data, **kwargs)
        
        # Additional cleaning based on data type
        if isinstance(cleaned, list):
            # Remove duplicates if requested
            if kwargs.get('remove_duplicates', False):
                cleaned = list(dict.fromkeys(cleaned))  # Preserves order
            
            # Remove outliers if requested
            if kwargs.get('remove_outliers', False):
                cleaned = self._remove_outliers(cleaned, **kwargs)
        
        return cleaned
    
    def _remove_outliers(self, data: List[Union[int, float]], **kwargs) -> List[Union[int, float]]:
        """Remove statistical outliers from numeric data"""
        if not data or not all(isinstance(x, (int, float)) for x in data):
            return data
        
        method = kwargs.get('outlier_method', 'iqr')  # 'iqr', 'zscore'
        
        if method == 'iqr':
            # Interquartile range method
            sorted_data = sorted(data)
            n = len(sorted_data)
            q1 = sorted_data[n // 4]
            q3 = sorted_data[3 * n // 4]
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            return [x for x in data if lower_bound <= x <= upper_bound]
        
        elif method == 'zscore':
            # Z-score method
            mean = sum(data) / len(data)
            variance = sum((x - mean) ** 2 for x in data) / len(data)
            std_dev = variance ** 0.5
            
            threshold = kwargs.get('zscore_threshold', 3.0)
            
            return [x for x in data if abs((x - mean) / std_dev) <= threshold]
        
        return data
    
    def _aggregate_data(self, data: Any, **kwargs) -> Dict[str, Any]:
        """Aggregate data by specified criteria"""
        if not data:
            return {}
        
        group_by = kwargs.get('group_by', kwargs.get('by'))
        aggregations = kwargs.get('aggregations', ['count'])
        
        if not group_by:
            return {'error': 'No grouping field specified'}
        
        groups = defaultdict(list)
        
        # Group data
        for item in data:
            if isinstance(item, dict):
                key = item.get(group_by, 'unknown')
            elif hasattr(item, group_by):
                key = getattr(item, group_by, 'unknown')
            else:
                key = 'unknown'
            
            groups[key].append(item)
        
        # Apply aggregations
        result = {}
        for key, group in groups.items():
            result[key] = {}
            
            for agg in aggregations:
                if agg == 'count':
                    result[key]['count'] = len(group)
                elif agg == 'sum':
                    # Sum numeric values
                    value_field = kwargs.get('value_field', 'value')
                    total = 0
                    for item in group:
                        if isinstance(item, dict):
                            total += item.get(value_field, 0)
                        elif hasattr(item, value_field):
                            total += getattr(item, value_field, 0)
                    result[key]['sum'] = total
                elif agg == 'avg' or agg == 'mean':
                    # Average numeric values
                    value_field = kwargs.get('value_field', 'value')
                    values = []
                    for item in group:
                        if isinstance(item, dict):
                            values.append(item.get(value_field, 0))
                        elif hasattr(item, value_field):
                            values.append(getattr(item, value_field, 0))
                    result[key]['avg'] = sum(values) / len(values) if values else 0
        
        return result
    
    def _count_values(self, data: Any, **kwargs) -> Dict[str, int]:
        """Count occurrences of values"""
        if not data:
            return {}
        
        field = kwargs.get('field')
        
        if field:
            # Count specific field values
            values = []
            for item in data:
                if isinstance(item, dict):
                    values.append(item.get(field, 'unknown'))
                elif hasattr(item, field):
                    values.append(getattr(item, field, 'unknown'))
            return dict(Counter(values))
        else:
            # Count the data items themselves
            return dict(Counter(data))
    
    def _convert_types(self, data: Any, **kwargs) -> Any:
        """Convert data types"""
        target_type = kwargs.get('to', kwargs.get('target_type', 'str'))
        
        if not isinstance(data, list):
            return data
        
        converted = []
        for item in data:
            try:
                if target_type == 'int':
                    converted.append(int(float(item)))
                elif target_type == 'float':
                    converted.append(float(item))
                elif target_type == 'str':
                    converted.append(str(item))
                elif target_type == 'bool':
                    converted.append(bool(item))
                else:
                    converted.append(item)
            except (ValueError, TypeError):
                converted.append(item)  # Keep original on conversion failure
        
        return converted
    
    def _transform_format(self, data: Any, **kwargs) -> Any:
        """Transform data format"""
        target_format = kwargs.get('format', kwargs.get('to_format'))
        
        if target_format == 'tuples' and isinstance(data, list):
            # Convert objects to tuples
            fields = kwargs.get('fields', ['lat', 'lng', 'value'])
            tuples = []
            for item in data:
                tuple_data = []
                for field in fields:
                    if isinstance(item, dict):
                        tuple_data.append(item.get(field, 0))
                    elif hasattr(item, field):
                        tuple_data.append(getattr(item, field, 0))
                    else:
                        tuple_data.append(0)
                tuples.append(tuple(tuple_data))
            return tuples
        
        return data
    
    def _to_csv(self, data: Any) -> str:
        """Convert data to CSV format"""
        if not data:
            return ""
        
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                # List of dictionaries
                headers = list(data[0].keys())
                lines = [','.join(headers)]
                for item in data:
                    line = ','.join(str(item.get(h, '')) for h in headers)
                    lines.append(line)
                return '\n'.join(lines)
            else:
                # Simple list
                return ','.join(str(item) for item in data)
        
        return str(data)


# Create global instance
data_transforms = DataTransformService()