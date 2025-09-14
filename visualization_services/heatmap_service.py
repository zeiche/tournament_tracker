#!/usr/bin/env python3
"""
Heatmap Service - Proper visualization architecture

This service:
1. Takes heatmap requests (knows what a "heatmap" is)
2. Gets raw data from database service (data layer)
3. Processes data via math services (computation layer)  
4. Renders via graphics services (presentation layer)

The database service no longer needs to know about "heatmaps".
"""

import sys
import os
from typing import Any, List, Dict, Optional, Union
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from polymorphic_core import announcer, register_capability


class HeatmapService:
    """
    Heatmap visualization service - orchestrates data, math, and graphics layers
    """
    
    def __init__(self):
        # Register as polymorphic capability
        register_capability('heatmaps', lambda: self)
        
        # Services will be lazy-loaded
        self._database_service = None
        self._visualization_math = None
        self._graphics_service = None
    
    def ask(self, query: str, data: Any = None, **kwargs) -> Any:
        """Process heatmap visualization requests"""
        query_lower = query.lower().strip()
        
        # Tournament heatmaps
        if 'tournament' in query_lower and 'heatmap' in query_lower:
            if 'image' in query_lower or 'generate image' in query_lower:
                return self._generate_tournament_heatmap_image(**kwargs)
            else:
                return self._generate_tournament_heatmap(**kwargs)
        elif 'heatmap' in query_lower and ('tournament' in query_lower or not any(x in query_lower for x in ['player', 'venue', 'organization'])):
            # Check if image generation requested
            if 'image' in query_lower or 'generate image' in query_lower or 'picture' in query_lower or 'png' in query_lower:
                return self._generate_tournament_heatmap_image(**kwargs)
            else:
                # Default to tournament heatmap data
                return self._generate_tournament_heatmap(**kwargs)
        
        # Player heatmaps
        elif 'player' in query_lower and 'heatmap' in query_lower:
            return self._generate_player_heatmap(**kwargs)
        
        # Venue/organization heatmaps
        elif ('venue' in query_lower or 'organization' in query_lower) and 'heatmap' in query_lower:
            return self._generate_venue_heatmap(**kwargs)
        
        # Generic heatmap processing
        elif 'heatmap' in query_lower:
            if data:
                return self._process_heatmap_data(data, **kwargs)
            else:
                return self._generate_tournament_heatmap(**kwargs)  # Default
        
        else:
            return f"Unknown heatmap query: {query}"
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format heatmap results"""
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "discord":
            if isinstance(data, list):
                return f"Generated heatmap with {len(data)} data points"
            elif isinstance(data, dict):
                if 'points' in data:
                    return f"Heatmap: {data['points']} points, bounds: {data.get('bounds', 'unknown')}"
                else:
                    return f"Heatmap data: {list(data.keys())}"
            else:
                return f"Heatmap result: {type(data).__name__}"
        elif format == "html":
            return self._generate_html_heatmap(data)
        else:
            return str(data)
    
    def do(self, action: str, data: Any = None, **kwargs) -> Any:
        """Perform heatmap actions"""
        action_lower = action.lower().strip()
        
        if 'generate' in action_lower:
            if 'tournament' in action_lower:
                return self._generate_tournament_heatmap(**kwargs)
            elif 'player' in action_lower:
                return self._generate_player_heatmap(**kwargs)
            elif 'venue' in action_lower:
                return self._generate_venue_heatmap(**kwargs)
            else:
                return self._generate_tournament_heatmap(**kwargs)  # Default
        elif 'process' in action_lower:
            return self._process_heatmap_data(data, **kwargs)
        else:
            return f"Unknown heatmap action: {action}"
    
    # Private methods - heatmap orchestration
    
    def _get_database_service(self):
        """Lazy-load database service"""
        if self._database_service is None:
            from utils.database_service import DatabaseService
            self._database_service = DatabaseService()
        return self._database_service
    
    def _get_visualization_math(self):
        """Lazy-load visualization math service"""
        if self._visualization_math is None:
            from math_services import visualization_math
            self._visualization_math = visualization_math
        return self._visualization_math
    
    def _get_graphics_service(self):
        """Lazy-load graphics service"""
        if self._graphics_service is None:
            try:
                from utils.graphics_service import visualizer
                self._graphics_service = visualizer
            except ImportError:
                self._graphics_service = None
        return self._graphics_service
    
    def _generate_tournament_heatmap(self, **kwargs) -> List[tuple]:
        """
        Generate tournament heatmap by orchestrating services properly:
        1. Database service gets raw tournament data (no heatmap knowledge)
        2. Math service processes the data for visualization
        3. Graphics service renders (if requested)
        """
        # Step 1: Get raw data from database (pure data request)
        db = self._get_database_service()
        tournaments = db.ask("tournaments with locations")  # Database knows about tournaments, not heatmaps
        
        if not tournaments:
            return []
        
        # Step 2: Process data via math services
        math_service = self._get_visualization_math()
        processed_data = math_service.ask("process heatmap data", tournaments)
        
        # Step 3: Apply additional processing if requested
        if kwargs.get('normalize', True):
            weights = [point[2] for point in processed_data]
            normalized_weights = math_service.ask("normalize", weights, method='log')
            processed_data = [
                (point[0], point[1], normalized_weights[i])
                for i, point in enumerate(processed_data)
            ]
        
        # Step 4: Return processed data (graphics service would render this)
        return processed_data
    
    def _generate_player_heatmap(self, **kwargs) -> List[tuple]:
        """Generate heatmap showing player distribution"""
        # Get player data from database
        db = self._get_database_service()
        players_data = db.ask("players with tournament locations")
        
        if not players_data:
            return []
        
        # Process via math services
        math_service = self._get_visualization_math()
        return math_service.ask("process heatmap data", players_data)
    
    def _generate_venue_heatmap(self, **kwargs) -> List[tuple]:
        """Generate heatmap showing venue/organization distribution"""
        # Get venue data from database
        db = self._get_database_service()
        venues_data = db.ask("organizations with locations")
        
        if not venues_data:
            return []
        
        # Process via math services  
        math_service = self._get_visualization_math()
        return math_service.ask("process heatmap data", venues_data)
    
    def _process_heatmap_data(self, data: Any, **kwargs) -> List[tuple]:
        """Process arbitrary data for heatmap visualization"""
        if not data:
            return []
        
        math_service = self._get_visualization_math()
        return math_service.ask("process heatmap data", data, **kwargs)
    
    def _generate_tournament_heatmap_image(self, **kwargs) -> Dict[str, Any]:
        """
        Generate heatmap image by delegating to graphics service.
        Returns dict with image_path and metadata.
        """
        # Step 1: Get processed heatmap data
        heatmap_data = self._generate_tournament_heatmap(**kwargs)
        
        if not heatmap_data:
            return {"error": "No heatmap data available"}
        
        # Step 2: Delegate to graphics service for visualization
        graphics = self._get_graphics_service()
        if not graphics:
            return {"error": "Graphics service not available"}
        
        try:
            # Use graphics service's ask method for polymorphic interface
            # Format data correctly for graphics service
            formatted_data = {'items': heatmap_data}
            result = graphics.ask("generate heatmap image", formatted_data, **kwargs)
            
            if isinstance(result, dict):
                if 'image_path' in result:
                    # Update title to be tournament-specific
                    result['title'] = f'Tournament Heatmap - {result.get("data_points", len(heatmap_data))} Locations'
                    return result
                elif 'error' in result:
                    return result
                else:
                    return {"error": "Unexpected result from graphics service"}
            else:
                return {"error": f"Graphics service returned unexpected type: {type(result)}"}
        except Exception as e:
            return {"error": f"Graphics service failed: {e}"}
    
    def _generate_html_heatmap(self, data: Any) -> str:
        """Generate HTML heatmap using graphics service"""
        graphics = self._get_graphics_service()
        if graphics and data:
            try:
                return graphics.ask("generate html heatmap", data)
            except Exception as e:
                return f"HTML generation failed: {e}"
        else:
            return f"<p>Heatmap data ready: {len(data) if isinstance(data, list) else 'No data'}</p>"


# Create global instance
heatmap_service = HeatmapService()