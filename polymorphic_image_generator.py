#!/usr/bin/env python3
"""
polymorphic_image_generator.py - Generate images/maps with heat overlays from ANY data

This polymorphic generator can:
- Load ANY image (maps, photos, diagrams)
- Create maps from coordinates
- Generate blank canvases
- Overlay heat maps from ANY data source
- Auto-detect geographic data
- Handle any coordinate system
- Apply various visualization styles

TRUE POLYMORPHISM: Give it any data and any background, it figures out the rest!
"""

import numpy as np
from typing import Any, List, Tuple, Optional, Union, Dict, Callable
from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path


class HeatStyle(Enum):
    """Different heat map styles"""
    CLASSIC = "classic"      # Red-yellow heat
    COOL = "cool"            # Blue-green 
    FIRE = "fire"            # Red-orange-yellow
    PLASMA = "plasma"        # Purple-pink-yellow
    OCEAN = "ocean"          # Blue-cyan
    THERMAL = "thermal"      # Thermal camera style
    DENSITY = "density"      # Black to white


class BackgroundType(Enum):
    """Types of backgrounds we can use"""
    MAP = "map"              # Geographic map
    IMAGE = "image"          # Any image file
    BLANK = "blank"          # Blank canvas
    AUTO = "auto"            # Auto-detect from data


@dataclass 
class HeatPoint:
    """A point to be visualized in the heat map"""
    x: float
    y: float
    weight: float = 1.0
    metadata: Dict[str, Any] = None


class PolymorphicImageGenerator:
    """
    The TRULY polymorphic image generator that creates heat maps from ANYTHING!
    """
    
    @classmethod
    def generate(cls,
                 data: Any,
                 output: str = "heatmap.png",
                 background: Optional[Union[str, BackgroundType]] = BackgroundType.AUTO,
                 style: Union[str, HeatStyle] = HeatStyle.CLASSIC,
                 hint: Optional[str] = None) -> str:
        """
        Generate a heat map from ANY data on ANY background!
        
        Args:
            data: ANYTHING - objects with coordinates, dicts, tuples, database objects
            output: Output filename
            background: Image path, map region, or BackgroundType
            style: Heat map style to apply
            hint: Natural language hint like "tournament locations", "player origins"
            
        Returns:
            Path to generated image
            
        Examples:
            # Tournaments on a map
            generate(tournaments, background="socal")
            
            # Any objects with lat/lng
            generate(venues, hint="venue density")
            
            # Custom data on any image
            generate(clicks, background="screenshot.png", hint="user clicks")
            
            # Auto-detect everything
            generate(mystery_data)
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.cm as cm
            from matplotlib.colors import LinearSegmentedColormap
        except ImportError:
            print("Installing required packages...")
            os.system("pip3 install --break-system-packages matplotlib scipy pillow")
            import matplotlib.pyplot as plt
            import matplotlib.cm as cm
            from matplotlib.colors import LinearSegmentedColormap
        
        # Extract heat points from data
        points = cls._extract_points(data, hint)
        if not points:
            raise ValueError("No points could be extracted from data")
        
        # Set up the figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Handle background
        bg_type = cls._determine_background_type(background, points)
        if bg_type == BackgroundType.MAP:
            cls._add_map_background(ax, points, background)
        elif bg_type == BackgroundType.IMAGE:
            cls._add_image_background(ax, background)
        elif bg_type == BackgroundType.BLANK:
            cls._create_blank_canvas(ax, points)
        else:  # AUTO
            if cls._looks_like_geo_data(points):
                cls._add_map_background(ax, points, "auto")
            else:
                cls._create_blank_canvas(ax, points)
        
        # Apply heat map overlay
        cls._apply_heat_overlay(ax, points, style)
        
        # Save the result
        plt.savefig(output, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Generated heat map: {output}")
        return output
    
    @classmethod
    def _extract_points(cls, data: Any, hint: Optional[str] = None) -> List[HeatPoint]:
        """Extract heat points from ANY data type"""
        points = []
        
        # If it's already a list of HeatPoints
        if isinstance(data, list) and all(isinstance(p, HeatPoint) for p in data):
            return data
        
        # If it's a single item, make it a list
        if not isinstance(data, (list, tuple)):
            data = [data]
        
        for item in data:
            point = cls._extract_point_from_object(item, hint)
            if point:
                points.append(point)
        
        return points
    
    @classmethod
    def _extract_point_from_object(cls, obj: Any, hint: Optional[str] = None) -> Optional[HeatPoint]:
        """Extract a point from a single object"""
        
        # Tuple or list of coordinates
        if isinstance(obj, (tuple, list)) and len(obj) >= 2:
            try:
                x, y = float(obj[0]), float(obj[1])
                weight = float(obj[2]) if len(obj) > 2 else 1.0
                return HeatPoint(x, y, weight)
            except (ValueError, TypeError):
                pass
        
        # Dictionary with coordinate keys
        if isinstance(obj, dict):
            # Try common coordinate keys
            coord_keys = [
                ('lat', 'lng'), ('lat', 'lon'), ('latitude', 'longitude'),
                ('y', 'x'), ('x', 'y'), ('row', 'col')
            ]
            for key1, key2 in coord_keys:
                if key1 in obj and key2 in obj:
                    try:
                        return HeatPoint(
                            float(obj[key2]),  # x is longitude
                            float(obj[key1]),  # y is latitude
                            float(obj.get('weight', obj.get('value', obj.get('count', 1))))
                        )
                    except (ValueError, TypeError):
                        pass
        
        # Objects with attributes
        if hasattr(obj, '__dict__'):
            # Check for geographic coordinates
            if hasattr(obj, 'lat') and hasattr(obj, 'lng'):
                try:
                    lat = float(obj.lat) if obj.lat is not None else None
                    lng = float(obj.lng) if obj.lng is not None else None
                    if lat is not None and lng is not None:
                        # Calculate weight based on hint or attributes
                        weight = cls._calculate_weight(obj, hint)
                        return HeatPoint(lng, lat, weight)
                except (ValueError, TypeError):
                    pass
            
            # Check for x/y coordinates
            if hasattr(obj, 'x') and hasattr(obj, 'y'):
                try:
                    return HeatPoint(
                        float(obj.x),
                        float(obj.y),
                        cls._calculate_weight(obj, hint)
                    )
                except (ValueError, TypeError):
                    pass
        
        return None
    
    @classmethod
    def _calculate_weight(cls, obj: Any, hint: Optional[str] = None) -> float:
        """Calculate weight for a point based on object attributes and hint"""
        
        # Default weight
        weight = 1.0
        
        # Use hint to determine what attribute to use for weight
        if hint:
            hint_lower = hint.lower()
            
            # Attendance-based weights
            if any(word in hint_lower for word in ['attendance', 'size', 'crowd']):
                if hasattr(obj, 'num_attendees'):
                    weight = float(obj.num_attendees or 1)
                elif hasattr(obj, 'attendance'):
                    weight = float(obj.attendance or 1)
            
            # Frequency-based weights
            elif any(word in hint_lower for word in ['frequency', 'count', 'events']):
                if hasattr(obj, 'event_count'):
                    weight = float(obj.event_count or 1)
                elif hasattr(obj, 'count'):
                    weight = float(obj.count or 1)
            
            # Points/score-based weights
            elif any(word in hint_lower for word in ['points', 'score', 'value']):
                if hasattr(obj, 'points'):
                    weight = float(obj.points or 1)
                elif hasattr(obj, 'score'):
                    weight = float(obj.score or 1)
        
        # Auto-detect weight attribute if no hint
        else:
            weight_attrs = ['weight', 'value', 'count', 'num_attendees', 'size']
            for attr in weight_attrs:
                if hasattr(obj, attr):
                    val = getattr(obj, attr)
                    if val is not None:
                        try:
                            weight = float(val)
                            break
                        except (ValueError, TypeError):
                            pass
        
        return max(weight, 0.1)  # Ensure positive weight
    
    @classmethod
    def _looks_like_geo_data(cls, points: List[HeatPoint]) -> bool:
        """Detect if points look like geographic coordinates"""
        if not points:
            return False
        
        # Check if coordinates are in typical lat/lng ranges
        lats = [p.y for p in points]
        lngs = [p.x for p in points]
        
        # Typical geographic ranges
        lat_geo = all(-90 <= lat <= 90 for lat in lats)
        lng_geo = all(-180 <= lng <= 180 for lng in lngs)
        
        # Also check if the spread looks geographic (not too wide)
        lat_spread = max(lats) - min(lats)
        lng_spread = max(lngs) - min(lngs)
        
        return lat_geo and lng_geo and lat_spread < 50 and lng_spread < 50
    
    @classmethod
    def _determine_background_type(cls, background: Any, points: List[HeatPoint]) -> BackgroundType:
        """Determine what type of background to use"""
        
        if background is None:
            return BackgroundType.AUTO
        
        if isinstance(background, BackgroundType):
            return background
        
        if isinstance(background, str):
            # Check if it's a file path
            if os.path.exists(background):
                return BackgroundType.IMAGE
            
            # Check if it's a map region name
            map_regions = ['socal', 'california', 'usa', 'world', 'auto']
            if background.lower() in map_regions:
                return BackgroundType.MAP
            
            # Check file extension
            if background.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                return BackgroundType.IMAGE
        
        return BackgroundType.AUTO
    
    @classmethod
    def _add_map_background(cls, ax, points: List[HeatPoint], region: str = "auto"):
        """Add a geographic map background"""
        try:
            import contextily as ctx
        except ImportError:
            print("Installing map package...")
            os.system("pip3 install --break-system-packages contextily")
            import contextily as ctx
        
        # Convert points to arrays
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        
        # Set map bounds with padding
        padding = 0.1
        x_range = max(xs) - min(xs)
        y_range = max(ys) - min(ys)
        
        ax.set_xlim(min(xs) - x_range * padding, max(xs) + x_range * padding)
        ax.set_ylim(min(ys) - y_range * padding, max(ys) + y_range * padding)
        
        # Add the map
        try:
            # Convert to Web Mercator for map tiles
            import matplotlib.pyplot as plt
            from matplotlib import transforms
            import math
            
            # Simple mercator projection for map tiles
            def lat_to_mercator(lat):
                return math.log(math.tan(math.pi/4 + math.radians(lat)/2))
            
            # Add basemap
            ctx.add_basemap(ax, crs='EPSG:4326', source=ctx.providers.CartoDB.Positron)
        except Exception as e:
            print(f"Could not add map background: {e}")
            # Continue without map background
    
    @classmethod
    def _add_image_background(cls, ax, image_path: str):
        """Add an image as background"""
        try:
            from PIL import Image
            import matplotlib.pyplot as plt
        except ImportError:
            print("Installing image package...")
            os.system("pip3 install --break-system-packages pillow")
            from PIL import Image
            import matplotlib.pyplot as plt
        
        try:
            img = Image.open(image_path)
            ax.imshow(img, aspect='auto', alpha=0.7)
            ax.set_xlim(0, img.width)
            ax.set_ylim(img.height, 0)  # Flip y-axis for image coordinates
        except Exception as e:
            print(f"Could not load image {image_path}: {e}")
            # Fall back to blank canvas
            cls._create_blank_canvas(ax, [])
    
    @classmethod
    def _create_blank_canvas(cls, ax, points: List[HeatPoint]):
        """Create a blank canvas with appropriate bounds"""
        if points:
            xs = [p.x for p in points]
            ys = [p.y for p in points]
            
            padding = 0.1
            x_range = max(xs) - min(xs) if max(xs) != min(xs) else 1
            y_range = max(ys) - min(ys) if max(ys) != min(ys) else 1
            
            ax.set_xlim(min(xs) - x_range * padding, max(xs) + x_range * padding)
            ax.set_ylim(min(ys) - y_range * padding, max(ys) + y_range * padding)
        else:
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
        
        ax.set_facecolor('#f0f0f0')
    
    @classmethod
    def _apply_heat_overlay(cls, ax, points: List[HeatPoint], style: Union[str, HeatStyle]):
        """Apply the heat map overlay"""
        try:
            from scipy.stats import gaussian_kde
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print("Installing scipy...")
            os.system("pip3 install --break-system-packages scipy")
            from scipy.stats import gaussian_kde
            import matplotlib.pyplot as plt
            import numpy as np
        
        if not points:
            return
        
        # Extract coordinates and weights
        xs = np.array([p.x for p in points])
        ys = np.array([p.y for p in points])
        weights = np.array([p.weight for p in points])
        
        # Normalize weights
        weights = weights / weights.max() if weights.max() > 0 else weights
        
        # Create grid for heat map
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        
        xx, yy = np.meshgrid(
            np.linspace(x_min, x_max, 100),
            np.linspace(y_min, y_max, 100)
        )
        
        # Calculate kernel density
        positions = np.vstack([xx.ravel(), yy.ravel()])
        values = np.vstack([xs, ys])
        
        try:
            kernel = gaussian_kde(values, weights=weights)
            density = np.reshape(kernel(positions).T, xx.shape)
        except np.linalg.LinAlgError:
            # Fall back to simple scatter if KDE fails
            scatter = ax.scatter(xs, ys, c=weights, s=weights*100, 
                               alpha=0.6, cmap=cls._get_colormap(style))
            plt.colorbar(scatter, ax=ax)
            return
        
        # Apply heat map with selected style
        cmap = cls._get_colormap(style)
        im = ax.contourf(xx, yy, density, levels=15, cmap=cmap, alpha=0.7)
        plt.colorbar(im, ax=ax)
        
        # Add scatter points on top
        ax.scatter(xs, ys, c='white', s=10, alpha=0.5, edgecolors='black', linewidth=0.5)
    
    @classmethod
    def _get_colormap(cls, style: Union[str, HeatStyle]):
        """Get colormap for the specified style"""
        import matplotlib.cm as cm
        from matplotlib.colors import LinearSegmentedColormap
        
        if isinstance(style, str):
            style = style.lower()
            
        style_maps = {
            HeatStyle.CLASSIC: 'YlOrRd',
            HeatStyle.COOL: 'YlGnBu', 
            HeatStyle.FIRE: 'hot',
            HeatStyle.PLASMA: 'plasma',
            HeatStyle.OCEAN: 'ocean',
            HeatStyle.THERMAL: 'inferno',
            HeatStyle.DENSITY: 'gray',
            'classic': 'YlOrRd',
            'cool': 'YlGnBu',
            'fire': 'hot',
            'plasma': 'plasma',
            'ocean': 'ocean',
            'thermal': 'inferno',
            'density': 'gray'
        }
        
        return style_maps.get(style, 'YlOrRd')
    
    @classmethod
    def generate_multi_layer(cls,
                           data_layers: List[Tuple[Any, str, float]],
                           output: str = "multi_heatmap.png",
                           background: Optional[str] = None) -> str:
        """
        Generate heat map with multiple data layers
        
        Args:
            data_layers: List of (data, style, alpha) tuples
            output: Output filename
            background: Background image or map
            
        Example:
            generate_multi_layer([
                (tournaments, "fire", 0.5),
                (players, "cool", 0.3),
                (venues, "density", 0.4)
            ])
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            os.system("pip3 install --break-system-packages matplotlib")
            import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Add background
        all_points = []
        for data, _, _ in data_layers:
            all_points.extend(cls._extract_points(data))
        
        if background:
            bg_type = cls._determine_background_type(background, all_points)
            if bg_type == BackgroundType.MAP:
                cls._add_map_background(ax, all_points, background)
            elif bg_type == BackgroundType.IMAGE:
                cls._add_image_background(ax, background)
        else:
            cls._create_blank_canvas(ax, all_points)
        
        # Apply each layer
        for data, style, alpha in data_layers:
            points = cls._extract_points(data)
            if points:
                # Temporarily set alpha
                original_alpha = plt.rcParams['image.alpha']
                plt.rcParams['image.alpha'] = alpha
                cls._apply_heat_overlay(ax, points, style)
                plt.rcParams['image.alpha'] = original_alpha
        
        plt.savefig(output, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Generated multi-layer heat map: {output}")
        return output


# Convenience function
def heatmap(data: Any, output: str = None, hint: str = None, **kwargs) -> str:
    """
    Quick heat map generation from ANY data
    
    Examples:
        heatmap(tournaments)  # Auto-detect everything
        heatmap(clicks, background="screenshot.png", hint="user activity")
        heatmap(venues, style="ocean", hint="venue density")
    """
    if output is None:
        output = "heatmap.png"
    
    return PolymorphicImageGenerator.generate(data, output, hint=hint, **kwargs)


if __name__ == "__main__":
    print("=" * 60)
    print("POLYMORPHIC IMAGE GENERATOR DEMO")
    print("=" * 60)
    
    # Demo with sample data
    print("\n1. Geographic data on auto-detected map:")
    geo_points = [
        {"lat": 34.0522, "lng": -118.2437, "weight": 10},  # Los Angeles
        {"lat": 32.7157, "lng": -117.1611, "weight": 8},   # San Diego
        {"lat": 33.4484, "lng": -112.0740, "weight": 5},   # Phoenix
        {"lat": 37.7749, "lng": -122.4194, "weight": 7},   # San Francisco
    ]
    heatmap(geo_points, "demo_geo.png", hint="city density")
    
    print("\n2. Non-geographic data on blank canvas:")
    click_data = [
        (100, 200, 5),  # x, y, weight
        (150, 250, 3),
        (120, 220, 8),
        (180, 200, 2),
    ]
    heatmap(click_data, "demo_clicks.png", style="cool")
    
    print("\n3. Custom objects with auto-detection:")
    class Event:
        def __init__(self, lat, lng, attendance):
            self.lat = lat
            self.lng = lng
            self.num_attendees = attendance
    
    events = [
        Event(34.05, -118.25, 100),
        Event(34.10, -118.30, 50),
        Event(34.00, -118.20, 75),
    ]
    heatmap(events, "demo_events.png", hint="attendance", style="fire")
    
    print("\n✅ Demos complete! Check demo_*.png files")
    print("This generator handles ANY data on ANY background!")
    print("=" * 60)