#!/usr/bin/env python3
"""
polymorphic_bitmap_layers.py - True layer-based bitmap system like Photoshop

Each function can write to its own transparent layer, then layers are composited.
Full alpha channel support with blending modes.

This is what you originally envisioned - a bitmap that functions write to!
"""

import numpy as np
from typing import Any, List, Tuple, Optional, Union, Dict, Callable
from dataclasses import dataclass
from enum import Enum
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
import os


class BlendMode(Enum):
    """Photoshop-style blending modes"""
    NORMAL = "normal"          # Standard alpha blending
    MULTIPLY = "multiply"      # Darkens by multiplying
    SCREEN = "screen"          # Lightens by inverting, multiplying, inverting
    OVERLAY = "overlay"        # Combines multiply and screen
    ADD = "add"               # Linear dodge (lighter)
    SUBTRACT = "subtract"      # Linear burn (darker)
    DIFFERENCE = "difference"  # Absolute difference
    SOFT_LIGHT = "soft_light" # Gentle contrast
    HARD_LIGHT = "hard_light" # Strong contrast
    COLOR_DODGE = "dodge"      # Brightens
    COLOR_BURN = "burn"       # Darkens with contrast


@dataclass
class Layer:
    """A single layer in our bitmap system"""
    name: str
    image: Image.Image  # PIL Image with RGBA
    opacity: float = 1.0
    blend_mode: BlendMode = BlendMode.NORMAL
    visible: bool = True
    locked: bool = False
    
    def __post_init__(self):
        # Ensure image has alpha channel
        if self.image.mode != 'RGBA':
            self.image = self.image.convert('RGBA')


class PolymorphicBitmapLayers:
    """
    A true layer-based bitmap system where ANY function can write to ANY layer.
    Full transparency support with Photoshop-style blending modes.
    """
    
    def __init__(self, width: int = 800, height: int = 600, background: Optional[Union[str, tuple]] = None):
        """
        Initialize bitmap with dimensions and optional background.
        
        Args:
            width: Canvas width in pixels
            height: Canvas height in pixels
            background: Color tuple (R,G,B,A), hex string, image path, or None for transparent
        """
        self.width = width
        self.height = height
        self.layers: List[Layer] = []
        self.active_layer_index: int = 0
        
        # Create background layer
        if background:
            if isinstance(background, str):
                if os.path.exists(background):
                    # Load image as background
                    bg_img = Image.open(background).convert('RGBA')
                    bg_img = bg_img.resize((width, height), Image.Resampling.LANCZOS)
                    self.add_layer("Background", bg_img, locked=True)
                else:
                    # Treat as color
                    self.add_layer("Background", self._create_solid_layer(background), locked=True)
            elif isinstance(background, tuple):
                self.add_layer("Background", self._create_solid_layer(background), locked=True)
        else:
            # Transparent background
            self.add_layer("Background", self._create_transparent_layer())
    
    def _create_transparent_layer(self) -> Image.Image:
        """Create a fully transparent layer"""
        return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
    
    def _create_solid_layer(self, color) -> Image.Image:
        """Create a solid color layer"""
        if isinstance(color, str) and color.startswith('#'):
            # Convert hex to RGBA
            color = color.lstrip('#')
            if len(color) == 6:
                r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
                color = (r, g, b, 255)
            elif len(color) == 8:
                r, g, b, a = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), int(color[6:8], 16)
                color = (r, g, b, a)
        elif isinstance(color, tuple) and len(color) == 3:
            color = (*color, 255)  # Add full opacity if not specified
            
        return Image.new('RGBA', (self.width, self.height), color)
    
    def add_layer(self, name: str, image: Optional[Image.Image] = None, 
                  opacity: float = 1.0, blend_mode: BlendMode = BlendMode.NORMAL,
                  visible: bool = True, locked: bool = False) -> 'Layer':
        """
        Add a new layer to the stack.
        
        Args:
            name: Layer name
            image: Optional PIL Image (creates transparent if None)
            opacity: Layer opacity (0.0 to 1.0)
            blend_mode: How this layer blends with ones below
            visible: Whether layer is visible
            locked: Whether layer can be edited
            
        Returns:
            The created Layer object
        """
        if image is None:
            image = self._create_transparent_layer()
        
        layer = Layer(name, image, opacity, blend_mode, visible, locked)
        self.layers.append(layer)
        self.active_layer_index = len(self.layers) - 1
        return layer
    
    def get_layer(self, name: str) -> Optional[Layer]:
        """Get a layer by name"""
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None
    
    def set_active_layer(self, name: str) -> bool:
        """Set the active layer by name"""
        for i, layer in enumerate(self.layers):
            if layer.name == name:
                self.active_layer_index = i
                return True
        return False
    
    def draw_on_layer(self, layer_name: str, draw_func: Callable, *args, **kwargs):
        """
        Draw on a specific layer using a function.
        
        Args:
            layer_name: Name of layer to draw on (creates if doesn't exist)
            draw_func: Function that takes (ImageDraw, *args, **kwargs)
            *args, **kwargs: Arguments passed to draw function
        """
        layer = self.get_layer(layer_name)
        if layer is None:
            layer = self.add_layer(layer_name)
        
        if layer.locked:
            print(f"Warning: Layer '{layer_name}' is locked")
            return
        
        # Create drawing context
        draw = ImageDraw.Draw(layer.image, 'RGBA')
        
        # Call the drawing function
        draw_func(draw, *args, **kwargs)
    
    def apply_heat_map(self, layer_name: str, points: List[Tuple[float, float, float]], 
                       colormap: str = 'hot', blur_radius: int = 10, opacity: float = 0.7):
        """
        Apply a heat map to a layer.
        
        Args:
            layer_name: Layer to draw heat map on
            points: List of (x, y, weight) tuples
            colormap: Color scheme for heat map
            blur_radius: Gaussian blur radius for smoothing
            opacity: Heat map opacity
        """
        layer = self.get_layer(layer_name)
        if layer is None:
            layer = self.add_layer(layer_name, opacity=opacity)
        
        # Create heat accumulator
        heat = np.zeros((self.height, self.width), dtype=np.float32)
        
        # Accumulate heat from points
        for x, y, weight in points:
            x, y = int(x), int(y)
            if 0 <= x < self.width and 0 <= y < self.height:
                # Add heat with gaussian falloff
                for dx in range(-blur_radius*2, blur_radius*2+1):
                    for dy in range(-blur_radius*2, blur_radius*2+1):
                        px, py = x + dx, y + dy
                        if 0 <= px < self.width and 0 <= py < self.height:
                            dist = np.sqrt(dx*dx + dy*dy)
                            if dist <= blur_radius*2:
                                falloff = np.exp(-(dist*dist) / (2*blur_radius*blur_radius))
                                heat[py, px] += weight * falloff
        
        # Normalize heat
        if heat.max() > 0:
            heat = heat / heat.max()
        
        # Apply colormap
        heat_img = self._apply_colormap(heat, colormap)
        
        # Set layer image
        layer.image = Image.fromarray(heat_img, 'RGBA')
        layer.opacity = opacity
    
    def _apply_colormap(self, data: np.ndarray, colormap: str) -> np.ndarray:
        """Apply a colormap to normalized data"""
        # Define some colormaps
        colormaps = {
            'hot': [
                (0.0, (0, 0, 0, 0)),
                (0.25, (128, 0, 0, 100)),
                (0.5, (255, 128, 0, 150)),
                (0.75, (255, 255, 0, 200)),
                (1.0, (255, 255, 255, 255))
            ],
            'cool': [
                (0.0, (0, 0, 0, 0)),
                (0.25, (0, 0, 128, 100)),
                (0.5, (0, 128, 255, 150)),
                (0.75, (0, 255, 255, 200)),
                (1.0, (255, 255, 255, 255))
            ],
            'plasma': [
                (0.0, (0, 0, 0, 0)),
                (0.25, (128, 0, 128, 100)),
                (0.5, (255, 0, 128, 150)),
                (0.75, (255, 128, 0, 200)),
                (1.0, (255, 255, 0, 255))
            ]
        }
        
        colormap_data = colormaps.get(colormap, colormaps['hot'])
        
        # Create RGBA image
        height, width = data.shape
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Apply colormap
        for y in range(height):
            for x in range(width):
                value = data[y, x]
                
                # Find surrounding colormap points
                for i in range(len(colormap_data) - 1):
                    t1, color1 = colormap_data[i]
                    t2, color2 = colormap_data[i + 1]
                    
                    if t1 <= value <= t2:
                        # Interpolate between colors
                        if t2 - t1 > 0:
                            ratio = (value - t1) / (t2 - t1)
                        else:
                            ratio = 0
                        
                        rgba[y, x] = [
                            int(color1[j] + (color2[j] - color1[j]) * ratio)
                            for j in range(4)
                        ]
                        break
        
        return rgba
    
    def draw_points(self, layer_name: str, points: List[Any], 
                    size: int = 5, color: tuple = (255, 255, 255, 200),
                    hint: Optional[str] = None):
        """
        Draw points on a layer (polymorphic - accepts any point format).
        
        Args:
            layer_name: Layer to draw on
            points: Any format points (tuples, dicts, objects)
            size: Point size in pixels
            color: RGBA color tuple
            hint: Optional hint for extracting coordinates
        """
        def draw_func(draw, points, size, color):
            for point in points:
                x, y = self._extract_coordinates(point, hint)
                if x is not None and y is not None:
                    # Draw point with soft edges
                    for i in range(3):
                        alpha = int(color[3] * (1 - i/3))
                        c = (*color[:3], alpha)
                        draw.ellipse([x-size-i, y-size-i, x+size+i, y+size+i], 
                                   fill=c, outline=None)
        
        self.draw_on_layer(layer_name, draw_func, points, size, color)
    
    def _extract_coordinates(self, obj: Any, hint: Optional[str] = None) -> Tuple[Optional[float], Optional[float]]:
        """Extract x, y coordinates from any object"""
        # Tuple/list
        if isinstance(obj, (tuple, list)) and len(obj) >= 2:
            return float(obj[0]), float(obj[1])
        
        # Dictionary
        if isinstance(obj, dict):
            if 'x' in obj and 'y' in obj:
                return float(obj['x']), float(obj['y'])
            if 'lat' in obj and 'lng' in obj:
                # Convert to canvas coordinates (simplified)
                return float(obj['lng']) * 10 + self.width/2, float(obj['lat']) * -10 + self.height/2
        
        # Object with attributes
        if hasattr(obj, 'x') and hasattr(obj, 'y'):
            return float(obj.x), float(obj.y)
        if hasattr(obj, 'lat') and hasattr(obj, 'lng'):
            return float(obj.lng) * 10 + self.width/2, float(obj.lat) * -10 + self.height/2
        
        return None, None
    
    def composite(self, background: Optional[tuple] = None) -> Image.Image:
        """
        Composite all visible layers into final image.
        
        Args:
            background: Optional background color for non-transparent areas
            
        Returns:
            Final composited PIL Image
        """
        # Start with background or transparent
        if background:
            result = Image.new('RGBA', (self.width, self.height), background)
        else:
            result = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        
        # Composite each visible layer
        for layer in self.layers:
            if not layer.visible:
                continue
            
            # Apply opacity
            if layer.opacity < 1.0:
                # Create temporary image with opacity applied
                temp = layer.image.copy()
                alpha = temp.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(layer.opacity)
                temp.putalpha(alpha)
                layer_img = temp
            else:
                layer_img = layer.image
            
            # Apply blending mode
            if layer.blend_mode == BlendMode.NORMAL:
                result = Image.alpha_composite(result, layer_img)
            elif layer.blend_mode == BlendMode.MULTIPLY:
                result = ImageChops.multiply(result, layer_img)
            elif layer.blend_mode == BlendMode.SCREEN:
                result = ImageChops.screen(result, layer_img)
            elif layer.blend_mode == BlendMode.ADD:
                result = ImageChops.add(result, layer_img)
            elif layer.blend_mode == BlendMode.SUBTRACT:
                result = ImageChops.subtract(result, layer_img)
            elif layer.blend_mode == BlendMode.DIFFERENCE:
                result = ImageChops.difference(result, layer_img)
            else:
                # Default to normal blending for unsupported modes
                result = Image.alpha_composite(result, layer_img)
        
        return result
    
    def save(self, filename: str, background: Optional[tuple] = None):
        """Save the composited image to file"""
        img = self.composite(background)
        img.save(filename)
        print(f"✅ Saved layered image: {filename}")
    
    def save_layers(self, directory: str):
        """Save each layer as a separate file"""
        os.makedirs(directory, exist_ok=True)
        for i, layer in enumerate(self.layers):
            filename = os.path.join(directory, f"{i:02d}_{layer.name}.png")
            layer.image.save(filename)
            print(f"  Saved layer: {filename}")
    
    def merge_layers(self, layer_names: List[str], new_name: str) -> Layer:
        """Merge multiple layers into one"""
        # Find layers to merge
        layers_to_merge = [l for l in self.layers if l.name in layer_names]
        
        if not layers_to_merge:
            raise ValueError("No layers found to merge")
        
        # Create new merged layer
        merged = self._create_transparent_layer()
        
        for layer in layers_to_merge:
            if layer.opacity < 1.0:
                temp = layer.image.copy()
                alpha = temp.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(layer.opacity)
                temp.putalpha(alpha)
                merged = Image.alpha_composite(merged, temp)
            else:
                merged = Image.alpha_composite(merged, layer.image)
        
        # Remove old layers
        self.layers = [l for l in self.layers if l.name not in layer_names]
        
        # Add merged layer
        return self.add_layer(new_name, merged)
    
    def adjust_layer_opacity(self, layer_name: str, opacity: float):
        """Adjust the opacity of a layer"""
        layer = self.get_layer(layer_name)
        if layer:
            layer.opacity = max(0.0, min(1.0, opacity))
    
    def reorder_layer(self, layer_name: str, new_index: int):
        """Move a layer to a new position in the stack"""
        for i, layer in enumerate(self.layers):
            if layer.name == layer_name:
                self.layers.pop(i)
                self.layers.insert(new_index, layer)
                break
    
    def list_layers(self):
        """Print all layers and their properties"""
        print("\n=== Layers (bottom to top) ===")
        for i, layer in enumerate(self.layers):
            status = "👁️ " if layer.visible else "❌ "
            lock = "🔒" if layer.locked else ""
            active = " ← ACTIVE" if i == self.active_layer_index else ""
            print(f"{i}: {status}{layer.name} (opacity: {layer.opacity:.1f}, "
                  f"blend: {layer.blend_mode.value}) {lock}{active}")


# Convenience function
def create_bitmap(width: int = 800, height: int = 600, **kwargs) -> PolymorphicBitmapLayers:
    """Quick creation of a layered bitmap"""
    return PolymorphicBitmapLayers(width, height, **kwargs)


if __name__ == "__main__":
    print("=" * 60)
    print("POLYMORPHIC BITMAP LAYERS DEMO")
    print("=" * 60)
    
    # Create a layered bitmap
    print("\n1. Creating layered bitmap with transparent layers...")
    bitmap = create_bitmap(800, 600, background=(30, 30, 30, 255))
    
    # Add multiple layers
    print("\n2. Adding multiple transparent layers...")
    
    # Layer 1: Grid
    def draw_grid(draw):
        for x in range(0, 800, 50):
            draw.line([(x, 0), (x, 600)], fill=(100, 100, 100, 50), width=1)
        for y in range(0, 600, 50):
            draw.line([(0, y), (800, y)], fill=(100, 100, 100, 50), width=1)
    
    bitmap.draw_on_layer("Grid", draw_grid)
    bitmap.adjust_layer_opacity("Grid", 0.3)
    
    # Layer 2: Heat map
    heat_points = [
        (200, 200, 10), (220, 210, 8), (180, 190, 7),
        (400, 300, 15), (420, 320, 12), (380, 280, 10),
        (600, 400, 5), (620, 420, 3)
    ]
    bitmap.apply_heat_map("Heat Map", heat_points, colormap='hot', opacity=0.7)
    
    # Layer 3: Points
    point_data = [
        {"x": 100, "y": 100}, {"x": 700, "y": 100},
        {"x": 100, "y": 500}, {"x": 700, "y": 500}
    ]
    bitmap.draw_points("Points", point_data, size=8, color=(255, 255, 0, 200))
    
    # Layer 4: Annotation
    def draw_text(draw):
        # PIL doesn't have built-in fonts without additional setup
        # So we'll draw rectangles as placeholders
        draw.rectangle([50, 50, 200, 80], fill=(0, 0, 0, 180))
        draw.rectangle([52, 52, 198, 78], outline=(255, 255, 255, 200))
    
    bitmap.draw_on_layer("Annotations", draw_text)
    
    # List all layers
    bitmap.list_layers()
    
    # Save the composite
    print("\n3. Compositing and saving...")
    bitmap.save("layered_demo.png")
    
    # Save individual layers
    print("\n4. Saving individual layers...")
    bitmap.save_layers("layers_output")
    
    # Demonstrate merging
    print("\n5. Merging heat and points layers...")
    bitmap.merge_layers(["Heat Map", "Points"], "Merged Data")
    bitmap.list_layers()
    
    bitmap.save("layered_merged.png")
    
    print("\n✅ Demo complete! Check layered_demo.png and layers_output/")
    print("This is a TRUE layer system with full transparency support!")
    print("=" * 60)