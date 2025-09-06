#!/usr/bin/env python3
"""
text_overlay_system.py - Flexible text overlay system for images

Supports custom fonts, positioning, effects, and styles.
Works with the polymorphic bitmap layer system.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from typing import Optional, Tuple, Union, List, Dict
from enum import Enum
import os

class TextAlign(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"

class TextStyle(Enum):
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    OUTLINE = "outline"
    SHADOW = "shadow"
    GLOW = "glow"
    EMBOSS = "emboss"

class FontSet:
    """Predefined font sets for consistent styling"""
    
    # Default font paths
    DEJAVU_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    DEJAVU_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    DEJAVU_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
    DEJAVU_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    DEJAVU_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    DEJAVU_MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
    
    @classmethod
    def get_tournament_fonts(cls) -> Dict[str, Dict]:
        """Tournament-specific font set"""
        return {
            "title": {
                "path": cls.DEJAVU_SANS_BOLD,
                "size": 72,
                "color": (255, 255, 255),
                "stroke_width": 3,
                "stroke_fill": (0, 0, 0)
            },
            "subtitle": {
                "path": cls.DEJAVU_SANS,
                "size": 36,
                "color": (255, 255, 200),
                "stroke_width": 2,
                "stroke_fill": (0, 0, 0)
            },
            "body": {
                "path": cls.DEJAVU_SANS,
                "size": 24,
                "color": (255, 255, 255),
                "stroke_width": 1,
                "stroke_fill": (0, 0, 0)
            },
            "caption": {
                "path": cls.DEJAVU_SANS,
                "size": 18,
                "color": (200, 200, 200),
                "stroke_width": 0,
                "stroke_fill": None
            },
            "rank": {
                "path": cls.DEJAVU_SANS_BOLD,
                "size": 96,
                "color": (255, 215, 0),  # Gold
                "stroke_width": 4,
                "stroke_fill": (139, 69, 19)  # Dark brown
            }
        }
    
    @classmethod
    def get_meme_fonts(cls) -> Dict[str, Dict]:
        """Meme-style font set"""
        return {
            "impact": {
                "path": cls.DEJAVU_SANS_BOLD,
                "size": 60,
                "color": (255, 255, 255),
                "stroke_width": 3,
                "stroke_fill": (0, 0, 0)
            },
            "top_text": {
                "path": cls.DEJAVU_SANS_BOLD,
                "size": 48,
                "color": (255, 255, 255),
                "stroke_width": 3,
                "stroke_fill": (0, 0, 0)
            },
            "bottom_text": {
                "path": cls.DEJAVU_SANS_BOLD,
                "size": 48,
                "color": (255, 255, 255),
                "stroke_width": 3,
                "stroke_fill": (0, 0, 0)
            }
        }

class TextOverlay:
    """Main text overlay system"""
    
    def __init__(self, font_set: Optional[str] = "tournament"):
        """
        Initialize with a font set.
        
        Args:
            font_set: "tournament", "meme", or "custom"
        """
        if font_set == "tournament":
            self.fonts = FontSet.get_tournament_fonts()
        elif font_set == "meme":
            self.fonts = FontSet.get_meme_fonts()
        else:
            self.fonts = FontSet.get_tournament_fonts()  # Default
    
    def add_text(
        self,
        image: Union[Image.Image, str],
        text: str,
        position: Tuple[int, int] = None,
        font_type: str = "body",
        align: TextAlign = TextAlign.CENTER,
        style: TextStyle = TextStyle.NORMAL,
        custom_font: Optional[Dict] = None,
        **kwargs
    ) -> Image.Image:
        """
        Add text to an image with full customization.
        
        Args:
            image: PIL Image or path to image
            text: Text to add
            position: (x, y) tuple or None for center
            font_type: Key from font set ("title", "body", etc.)
            align: Text alignment
            style: Text style (shadow, outline, etc.)
            custom_font: Override font settings
            **kwargs: Additional parameters
            
        Returns:
            New image with text overlay
        """
        # Load image if path
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image.copy()
        
        # Ensure RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Get font settings
        if custom_font:
            font_config = custom_font
        else:
            # Try to get the font type, fallback to first available font
            if font_type in self.fonts:
                font_config = self.fonts[font_type]
            else:
                # Use first font in the set as fallback
                font_config = list(self.fonts.values())[0]
        
        # Load font
        try:
            font = ImageFont.truetype(font_config["path"], font_config["size"])
        except:
            font = ImageFont.load_default()
        
        # Create drawing layer
        txt_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Calculate position if not provided
        if position is None:
            # Center the text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((img.width - text_width) // 2, (img.height - text_height) // 2)
        
        # Apply style
        if style == TextStyle.SHADOW:
            # Draw shadow first
            shadow_offset = kwargs.get("shadow_offset", (3, 3))
            shadow_color = kwargs.get("shadow_color", (0, 0, 0, 128))
            draw.text(
                (position[0] + shadow_offset[0], position[1] + shadow_offset[1]),
                text,
                font=font,
                fill=shadow_color
            )
        
        elif style == TextStyle.GLOW:
            # Create glow effect
            glow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)
            glow_color = kwargs.get("glow_color", font_config["color"])
            
            # Draw multiple times with blur
            for offset in range(5, 0, -1):
                for dx in range(-offset, offset + 1):
                    for dy in range(-offset, offset + 1):
                        glow_draw.text(
                            (position[0] + dx, position[1] + dy),
                            text,
                            font=font,
                            fill=(*glow_color[:3], 50)
                        )
            
            # Blur the glow
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(3))
            txt_layer = Image.alpha_composite(txt_layer, glow_layer)
        
        # Draw main text
        if font_config.get("stroke_width", 0) > 0:
            draw.text(
                position,
                text,
                font=font,
                fill=font_config["color"],
                stroke_width=font_config["stroke_width"],
                stroke_fill=font_config.get("stroke_fill", (0, 0, 0))
            )
        else:
            draw.text(
                position,
                text,
                font=font,
                fill=font_config["color"]
            )
        
        # Composite text layer onto image
        result = Image.alpha_composite(img, txt_layer)
        
        return result
    
    def add_multi_text(
        self,
        image: Union[Image.Image, str],
        texts: List[Dict],
    ) -> Image.Image:
        """
        Add multiple text elements to an image.
        
        Args:
            image: Base image
            texts: List of text dictionaries with keys:
                   - text: The text string
                   - position: (x, y) or None
                   - font_type: Font type key
                   - style: TextStyle
                   - Any other kwargs for add_text
        
        Returns:
            Image with all text overlays
        """
        result = image
        
        for text_config in texts:
            result = self.add_text(
                result,
                text_config.pop("text"),
                **text_config
            )
        
        return result
    
    def create_meme(
        self,
        image: Union[Image.Image, str],
        top_text: Optional[str] = None,
        bottom_text: Optional[str] = None
    ) -> Image.Image:
        """
        Create a classic meme with top and bottom text.
        
        Args:
            image: Base image
            top_text: Text for top of image
            bottom_text: Text for bottom of image
            
        Returns:
            Meme image
        """
        # Create new instance with meme fonts
        meme_overlay = TextOverlay("meme")
        
        # Load image
        if isinstance(image, str):
            img = Image.open(image)
        else:
            img = image.copy()
        
        texts = []
        
        if top_text:
            texts.append({
                "text": top_text.upper(),
                "position": (img.width // 2, 40),
                "font_type": "top_text",
                "align": TextAlign.CENTER
            })
        
        if bottom_text:
            texts.append({
                "text": bottom_text.upper(),
                "position": (img.width // 2, img.height - 60),
                "font_type": "bottom_text",
                "align": TextAlign.CENTER
            })
        
        return meme_overlay.add_multi_text(img, texts)


# Demo functions
def demo_text_overlay():
    """Demonstrate text overlay capabilities"""
    
    # Create text overlay system
    overlay = TextOverlay("tournament")
    
    # Load the poop emoji image
    poop_img = Image.open("poop_emoji_yellow.png")
    
    # Add tournament-style text
    result = overlay.add_multi_text(
        poop_img,
        [
            {
                "text": "TOURNAMENT",
                "position": None,  # Center
                "font_type": "title",
                "style": TextStyle.SHADOW
            },
            {
                "text": "CHAMPION",
                "position": (400, 450),
                "font_type": "subtitle",
                "style": TextStyle.GLOW,
                "glow_color": (255, 215, 0)
            }
        ]
    )
    
    result.save("poop_with_text.png")
    print("✅ Created poop_with_text.png with tournament text")
    
    # Create meme version
    meme_overlay = TextOverlay("meme")
    meme = meme_overlay.create_meme(
        poop_img,
        top_text="When you win",
        bottom_text="The tournament"
    )
    
    meme.save("poop_meme.png")
    print("✅ Created poop_meme.png as a meme")
    
    return result, meme


if __name__ == "__main__":
    print("=" * 60)
    print("TEXT OVERLAY SYSTEM")
    print("=" * 60)
    print("\nAvailable font sets:")
    print("  - tournament: Professional tournament graphics")
    print("  - meme: Classic meme style")
    print("\nFont types in tournament set:")
    for name, config in FontSet.get_tournament_fonts().items():
        print(f"  - {name}: {config['size']}px")
    
    print("\n" + "=" * 60)
    print("Creating demo images...")
    demo_text_overlay()
    print("\n✅ Demo complete! Check poop_with_text.png and poop_meme.png")