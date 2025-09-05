#!/usr/bin/env python3
"""
polymorphic_inputs.py - Universal input handling for flexible function signatures
Allows functions to seamlessly accept strings, objects, lists, dicts, or queries
"""

import json
from typing import Any, Union, List, Dict, Optional, Callable, TypeVar
from datetime import datetime, date
import inspect

T = TypeVar('T')


class InputHandler:
    """Universal input handler that intelligently processes any input type"""
    
    @staticmethod
    def parse(
        input_value: Any,
        expected_type: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Any:
        """
        Parse input into the most appropriate format
        
        Args:
            input_value: Any type of input (str, list, dict, object, etc.)
            expected_type: Hint about what type is expected ('tournament', 'player', etc.)
            context: Additional context for parsing
            
        Returns:
            Parsed and formatted input ready for processing
        """
        # Handle None
        if input_value is None:
            return None
        
        # Handle strings
        if isinstance(input_value, str):
            return InputHandler._parse_string(input_value, expected_type, context)
        
        # Handle lists
        elif isinstance(input_value, list):
            return InputHandler._parse_list(input_value, expected_type, context)
        
        # Handle dictionaries
        elif isinstance(input_value, dict):
            return InputHandler._parse_dict(input_value, expected_type, context)
        
        # Handle model objects (Tournament, Player, Organization)
        elif hasattr(input_value, '__tablename__'):
            return InputHandler._parse_model(input_value, context)
        
        # Handle any object with __dict__
        elif hasattr(input_value, '__dict__'):
            return InputHandler._parse_object(input_value, context)
        
        # Handle callables (functions/lambdas)
        elif callable(input_value):
            return InputHandler._parse_callable(input_value, context)
        
        # Default: return as-is
        return input_value
    
    @staticmethod
    def _parse_string(value: str, expected_type: Optional[str], context: Optional[Dict]) -> Any:
        """Parse string input intelligently"""
        # Try to detect what the string represents
        value_lower = value.lower().strip()
        
        # Check for JSON
        if value.startswith('{') or value.startswith('['):
            try:
                return json.loads(value)
            except:
                pass
        
        # Check for ID patterns
        if value.isdigit() and expected_type:
            return {'id': value, 'type': expected_type}
        
        # Check for query patterns
        if any(keyword in value_lower for keyword in ['select', 'where', 'from']):
            return {'query': value, 'type': 'sql'}
        
        # Check for search patterns
        if any(keyword in value_lower for keyword in ['find', 'search', 'show', 'list']):
            return {'search': value, 'type': 'natural_language'}
        
        # Check for date patterns
        if any(char in value for char in ['-', '/']):
            try:
                # Try parsing as date
                if '/' in value:
                    parts = value.split('/')
                    if len(parts) == 3:
                        return {'date': value, 'type': 'date'}
            except:
                pass
        
        # Return as search term
        return {'text': value, 'type': 'search'}
    
    @staticmethod
    def _parse_list(value: List, expected_type: Optional[str], context: Optional[Dict]) -> Dict:
        """Parse list input"""
        if not value:
            return {'items': [], 'count': 0, 'type': 'empty_list'}
        
        # Check what's in the list
        first_item = value[0]
        
        # List of model objects
        if hasattr(first_item, '__tablename__'):
            return {
                'items': value,
                'count': len(value),
                'type': f"list_of_{first_item.__tablename__}",
                'model_type': first_item.__class__.__name__
            }
        
        # List of dicts
        elif isinstance(first_item, dict):
            return {
                'items': value,
                'count': len(value),
                'type': 'list_of_dicts',
                'keys': list(first_item.keys()) if first_item else []
            }
        
        # List of strings (could be IDs, names, etc.)
        elif isinstance(first_item, str):
            # Check if they look like IDs
            if all(item.isdigit() for item in value[:10]):  # Check first 10
                return {
                    'ids': value,
                    'count': len(value),
                    'type': 'id_list'
                }
            else:
                return {
                    'items': value,
                    'count': len(value),
                    'type': 'string_list'
                }
        
        # Generic list
        return {
            'items': value,
            'count': len(value),
            'type': 'list'
        }
    
    @staticmethod
    def _parse_dict(value: Dict, expected_type: Optional[str], context: Optional[Dict]) -> Dict:
        """Parse dictionary input"""
        # Add metadata about the dictionary
        result = value.copy()
        result['_metadata'] = {
            'key_count': len(value),
            'keys': list(value.keys()),
            'type': 'dict'
        }
        
        # Check for special keys that indicate type
        if 'id' in value:
            result['_metadata']['type'] = 'entity'
        elif 'query' in value or 'search' in value:
            result['_metadata']['type'] = 'search'
        elif 'start_date' in value or 'end_date' in value:
            result['_metadata']['type'] = 'date_range'
        elif 'filters' in value:
            result['_metadata']['type'] = 'filter_set'
        
        return result
    
    @staticmethod
    def _parse_model(value: Any, context: Optional[Dict]) -> Dict:
        """Parse SQLAlchemy model object"""
        model_name = value.__class__.__name__
        table_name = value.__tablename__
        
        # Extract all non-private attributes
        attrs = {}
        for key in dir(value):
            if not key.startswith('_'):
                try:
                    attr_value = getattr(value, key)
                    # Skip methods and SQLAlchemy internals
                    if not callable(attr_value) and not str(type(attr_value)).startswith("<class 'sqlalchemy"):
                        # Convert dates to strings
                        if isinstance(attr_value, (date, datetime)):
                            attrs[key] = attr_value.isoformat()
                        else:
                            attrs[key] = attr_value
                except:
                    pass
        
        return {
            'model': model_name,
            'table': table_name,
            'id': getattr(value, 'id', None),
            'data': attrs,
            '_type': 'model_object'
        }
    
    @staticmethod
    def _parse_object(value: Any, context: Optional[Dict]) -> Dict:
        """Parse generic object with __dict__"""
        return {
            'class': value.__class__.__name__,
            'data': value.__dict__,
            '_type': 'object'
        }
    
    @staticmethod
    def _parse_callable(value: Callable, context: Optional[Dict]) -> Dict:
        """Parse callable (function/lambda)"""
        # Execute it if it takes no arguments
        sig = inspect.signature(value)
        if len(sig.parameters) == 0:
            try:
                result = value()
                # Recursively parse the result
                return InputHandler.parse(result, context=context)
            except:
                pass
        
        return {
            'callable': value.__name__ if hasattr(value, '__name__') else 'lambda',
            'params': list(sig.parameters.keys()),
            '_type': 'callable'
        }


class SmartParameter:
    """Decorator to make function parameters polymorphic"""
    
    def __init__(self, *expected_types):
        """
        Args:
            expected_types: Hints about expected types ('tournament', 'player', etc.)
        """
        self.expected_types = expected_types
    
    def __call__(self, func):
        """Wrap function to pre-process inputs"""
        def wrapper(*args, **kwargs):
            # Process positional arguments
            processed_args = []
            for i, arg in enumerate(args):
                expected = self.expected_types[i] if i < len(self.expected_types) else None
                processed_args.append(InputHandler.parse(arg, expected))
            
            # Process keyword arguments
            processed_kwargs = {}
            for key, value in kwargs.items():
                # Check if this kwarg has an expected type
                expected = None
                for exp_type in self.expected_types:
                    if isinstance(exp_type, dict) and key in exp_type:
                        expected = exp_type[key]
                        break
                processed_kwargs[key] = InputHandler.parse(value, expected)
            
            # Call original function with processed inputs
            return func(*processed_args, **processed_kwargs)
        
        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper


class FlexibleQuery:
    """Build database queries from flexible inputs"""
    
    @staticmethod
    def build(session, model_class, input_value: Any) -> Any:
        """
        Build a query from flexible input
        
        Args:
            session: Database session
            model_class: Model class to query
            input_value: Flexible input (string, dict, list, etc.)
            
        Returns:
            Query object or results
        """
        parsed = InputHandler.parse(input_value, model_class.__name__.lower())
        
        # Handle different parsed types
        if isinstance(parsed, dict):
            # ID lookup
            if 'id' in parsed:
                return session.query(model_class).filter_by(id=parsed['id']).first()
            
            # ID list
            elif 'ids' in parsed:
                return session.query(model_class).filter(
                    model_class.id.in_(parsed['ids'])
                ).all()
            
            # Search query
            elif parsed.get('_metadata', {}).get('type') == 'search':
                query = session.query(model_class)
                # Apply search filters
                if 'text' in parsed:
                    # Search in name/title fields
                    if hasattr(model_class, 'name'):
                        query = query.filter(
                            model_class.name.ilike(f"%{parsed['text']}%")
                        )
                return query.all()
            
            # Filter set
            elif 'filters' in parsed:
                query = session.query(model_class)
                for key, value in parsed['filters'].items():
                    if hasattr(model_class, key):
                        query = query.filter_by(**{key: value})
                return query.all()
        
        # Default: return all
        return session.query(model_class).all()


# Convenience functions for common conversions
def to_list(input_value: Any) -> List:
    """Convert any input to a list"""
    if input_value is None:
        return []
    elif isinstance(input_value, list):
        return input_value
    elif isinstance(input_value, (tuple, set)):
        return list(input_value)
    elif isinstance(input_value, dict):
        return [input_value]
    elif hasattr(input_value, '__iter__') and not isinstance(input_value, str):
        return list(input_value)
    else:
        return [input_value]


def to_dict(input_value: Any) -> Dict:
    """Convert any input to a dictionary"""
    parsed = InputHandler.parse(input_value)
    if isinstance(parsed, dict):
        return parsed
    else:
        return {'value': parsed}


def to_ids(input_value: Any) -> List[str]:
    """Extract IDs from any input"""
    parsed = InputHandler.parse(input_value)
    
    if isinstance(parsed, dict):
        if 'id' in parsed:
            return [str(parsed['id'])]
        elif 'ids' in parsed:
            return [str(id) for id in parsed['ids']]
        elif 'items' in parsed:
            # Try to extract IDs from items
            ids = []
            for item in parsed['items']:
                if isinstance(item, dict) and 'id' in item:
                    ids.append(str(item['id']))
                elif hasattr(item, 'id'):
                    ids.append(str(item.id))
            return ids
    
    return []


# Example usage decorator
def accepts_anything(*expected_types):
    """Decorator to make a function accept any input type"""
    return SmartParameter(*expected_types)


if __name__ == "__main__":
    # Test the input handler
    print("Polymorphic Input Handler Tests")
    print("=" * 60)
    
    # Test string inputs
    test_inputs = [
        "tournament",
        "12345",
        '{"name": "Test Tournament"}',
        "[1, 2, 3]",
        "find tournaments in august",
        "2024-08-15"
    ]
    
    for input_val in test_inputs:
        result = InputHandler.parse(input_val)
        print(f"\nInput: {input_val}")
        print(f"Parsed: {result}")
    
    # Test list inputs
    print("\n" + "=" * 60)
    print("List inputs:")
    
    lists = [
        [1, 2, 3],
        ["abc", "def", "ghi"],
        [{"id": 1}, {"id": 2}],
        []
    ]
    
    for lst in lists:
        result = InputHandler.parse(lst)
        print(f"\nInput: {lst}")
        print(f"Parsed: {result}")
    
    # Test dict inputs
    print("\n" + "=" * 60)
    print("Dictionary inputs:")
    
    dicts = [
        {"id": 123},
        {"search": "tournament", "filters": {"city": "Riverside"}},
        {"start_date": "2024-01-01", "end_date": "2024-12-31"}
    ]
    
    for d in dicts:
        result = InputHandler.parse(d)
        print(f"\nInput: {d}")
        print(f"Parsed: {result}")