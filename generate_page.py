# generate_page.py
"""Generate illustrated book pages with decorative edges."""

from PIL import Image, ImageDraw, ImageFont
import json
import os
import re
import math
import numpy as np
import random
import qrcode
from collections import Counter
from variables import (
    PAGE_WIDTH as _PAGE_WIDTH, PAGE_HEIGHT as _PAGE_HEIGHT, 
    BG_OPACITY_CENTER, BG_OPACITY_EDGE,
    FONT_SIZE, LINE_SPACING, TEXT_MARGIN, ETSY_SHOP_URL
)

# Convert to integers for PIL compatibility
PAGE_WIDTH = int(_PAGE_WIDTH)
PAGE_HEIGHT = int(_PAGE_HEIGHT)

# Layout constants
HALF_HEIGHT = PAGE_HEIGHT // 2
WAVE_HEIGHT = 25
DEFAULT_WAVE_COUNT = 8
EDGE_TYPES = ["wave", "scallop", "zigzag"]

# Color extraction settings
COLOR_QUANTIZE_LEVELS = 8
MIN_BRIGHTNESS = 60
MIN_SATURATION = 0.25
DEFAULT_LIGHT_COLOR = (255, 250, 245)
DEFAULT_DARK_COLOR = (0, 0, 0)


def _extract_quantized_colors(image_path, num_colors=50):
    """Extract and quantize colors from an image.
    
    Returns scored vibrant colors.
    """
    img = Image.open(image_path).convert('RGB')
    img = img.resize((100, 100), Image.Resampling.LANCZOS)
    
    # Quantize pixels to reduce unique colors
    pixels = list(img.getdata())
    quantized = [
        ((r // COLOR_QUANTIZE_LEVELS) * COLOR_QUANTIZE_LEVELS,
         (g // COLOR_QUANTIZE_LEVELS) * COLOR_QUANTIZE_LEVELS,
         (b // COLOR_QUANTIZE_LEVELS) * COLOR_QUANTIZE_LEVELS)
        for r, g, b in pixels
    ]
    
    color_counts = Counter(quantized)
    most_common = color_counts.most_common(num_colors)
    
    # Score colors by vibrancy (saturation + brightness)
    valid_colors = []
    for color, count in most_common:
        r, g, b = color
        max_c, min_c = max(r, g, b), min(r, g, b)
        
        if max_c < MIN_BRIGHTNESS:
            continue
        
        saturation = (max_c - min_c) / max_c if max_c > 0 else 0
        if saturation < MIN_SATURATION:
            continue
        
        score = (saturation * 300) + max_c
        valid_colors.append((color, score))
    
    # Fallback: use brightest colors if no saturated ones found
    if not valid_colors:
        for color, count in most_common:
            max_c = max(color)
            if max_c > 50:
                valid_colors.append((color, max_c))
    
    valid_colors.sort(key=lambda x: x[1], reverse=True)
    return valid_colors


def get_dominant_color(image_path, num_colors=50):
    """Extract the most vibrant color and return its darkest variant."""
    try:
        valid_colors = _extract_quantized_colors(image_path, num_colors)
        if not valid_colors:
            return DEFAULT_DARK_COLOR
        
        r, g, b = valid_colors[0][0]
        return (
            max(0, int(r * 0.5)),
            max(0, int(g * 0.6)),
            max(0, int(b * 0.7))
        )
    except Exception as e:
        print(f"    ⚠️ Could not extract color: {e}")
        return DEFAULT_DARK_COLOR


def get_light_color(image_path, num_colors=50):
    """Extract the most vibrant color and return a light shade of it."""
    try:
        valid_colors = _extract_quantized_colors(image_path, num_colors)
        if not valid_colors:
            return DEFAULT_LIGHT_COLOR
        
        r, g, b = valid_colors[0][0]
        # Blend with white to create a light pastel shade
        return (
            min(255, int(255 - (255 - r) * 0.15)),
            min(255, int(255 - (255 - g) * 0.12)),
            min(255, int(255 - (255 - b) * 0.10))
        )
    except Exception as e:
        print(f"    ⚠️ Could not extract light color: {e}")
        return DEFAULT_LIGHT_COLOR


def get_brightest_color(image_path, num_colors=50):
    """Extract the brightest vibrant color from an image."""
    try:
        valid_colors = _extract_quantized_colors(image_path, num_colors)
        if not valid_colors:
            return (255, 255, 255)
        
        # Find the brightest color (highest sum of RGB)
        brightest = max(valid_colors, key=lambda x: sum(x[0]))
        r, g, b = brightest[0]
        # Boost brightness while keeping hue
        max_val = max(r, g, b)
        if max_val > 0:
            factor = min(255 / max_val, 1.3)
            return (
                min(255, int(r * factor)),
                min(255, int(g * factor)),
                min(255, int(b * factor))
            )
        return (255, 255, 255)
    except Exception as e:
        print(f"    ⚠️ Could not extract brightest color: {e}")
        return (255, 255, 255)


def _draw_wave_edge(draw, width, height, wave_height, wave_count,
                    at_top=False):
    """Draw a sine wave edge pattern on a mask."""
    for x in range(width):
        progress = x / width * wave_count * 2 * math.pi
        y_offset = math.sin(progress) * wave_height
        if at_top:
            wave_y = int(wave_height - y_offset)
            draw.line([(x, 0), (x, wave_y)], fill=0)
        else:
            wave_y = int(height - wave_height + y_offset)
            draw.line([(x, wave_y), (x, height)], fill=0)


def _draw_scallop_edge(draw, width, height, wave_height, wave_count,
                       at_top=False):
    """Draw a scallop/cloud edge pattern on a mask."""
    scallop_width = width // wave_count
    scallop_radius = scallop_width // 2
    
    if not at_top:
        # Draw scallops at bottom
        draw.rectangle([0, 0, width, height - scallop_radius], fill=255)
        for i in range(wave_count + 1):
            center_x = i * scallop_width
            center_y = height - scallop_radius - 10
            bbox = [
                center_x - scallop_radius, center_y,
                center_x + scallop_radius, center_y + scallop_radius * 2
            ]
            draw.ellipse(bbox, fill=255)
    
    # Clear outside scallops
    for x in range(width):
        scallop_index = x // scallop_width
        center_x = scallop_index * scallop_width + scallop_radius
        if at_top:
            center_y = scallop_radius + 10
        else:
            center_y = height - scallop_radius - 10
        
        dx = abs(x - center_x)
        if dx < scallop_radius:
            arc_offset = int(math.sqrt(scallop_radius**2 - dx**2))
            if at_top:
                arc_y = center_y - arc_offset
            else:
                arc_y = center_y + arc_offset
        else:
            arc_y = center_y
        
        if at_top:
            draw.line([(x, 0), (x, arc_y)], fill=0)
        else:
            draw.line([(x, arc_y), (x, height)], fill=0)


def _draw_zigzag_edge(draw, width, height, wave_height, wave_count,
                      at_top=False):
    """Draw a zigzag edge pattern on a mask."""
    tooth_width = width // (wave_count * 2)
    
    if not at_top:
        # Draw zigzag polygon at bottom
        points = [(0, 0), (0, height - wave_height)]
        for i in range(wave_count * 2 + 1):
            x = i * tooth_width
            y = height - wave_height if i % 2 == 0 else height
            points.append((x, y))
        points.extend([(width, height - wave_height), (width, 0)])
        draw.polygon(points, fill=255)
    
    # Clear outside zigzag
    for i in range(wave_count * 2):
        x1, x2 = i * tooth_width, (i + 1) * tooth_width
        if at_top:
            if i % 2 == 0:
                y1, y2 = wave_height, 0
            else:
                y1, y2 = 0, wave_height
        else:
            if i % 2 == 0:
                y1, y2 = height - wave_height, height
            else:
                y1, y2 = height, height - wave_height
        
        for x in range(x1, min(x2, width)):
            progress = (x - x1) / tooth_width if tooth_width > 0 else 0
            y = int(y1 + (y2 - y1) * progress)
            if at_top:
                draw.line([(x, 0), (x, y)], fill=0)
            else:
                draw.line([(x, y), (x, height)], fill=0)


def create_decorative_mask(width, height, edge_type="wave", at_top=False):
    """Create a mask with a decorative edge for the image.
    
    Args:
        width: Mask width in pixels
        height: Mask height in pixels
        edge_type: 'wave', 'scallop', or 'zigzag'
        at_top: If True, decorative edge is at top; otherwise at bottom
    """
    mask = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(mask)
    
    wave_count = random.randint(2, 10) if not at_top else DEFAULT_WAVE_COUNT
    
    edge_functions = {
        "wave": _draw_wave_edge,
        "scallop": _draw_scallop_edge,
        "zigzag": _draw_zigzag_edge
    }
    
    draw_func = edge_functions.get(edge_type, _draw_wave_edge)
    draw_func(draw, width, height, WAVE_HEIGHT, wave_count, at_top)
    
    return mask


def create_radial_gradient_mask(width, height, center_opacity, edge_opacity):
    """Create a radial gradient mask from center to edges."""
    # Create coordinate grids
    y, x = np.ogrid[:height, :width]
    
    # Calculate center
    center_x, center_y = width / 2, height / 2
    
    # Calculate distance from center (normalized to 0-1)
    max_dist = math.sqrt(center_x**2 + center_y**2)
    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2) / max_dist
    
    # Clamp distance to 0-1 range
    dist = np.clip(dist, 0, 1)
    
    # Interpolate opacity from center to edge
    opacity = center_opacity + (edge_opacity - center_opacity) * dist
    
    # Convert to 0-255 alpha values
    alpha = (opacity * 255).astype(np.uint8)
    
    return Image.fromarray(alpha, mode='L')


def parse_story():
    """Parse story.json and extract title and story pages."""
    if not os.path.exists("story.json"):
        raise FileNotFoundError(
            "story.json not found. Run generate_story.py first."
        )
    
    with open("story.json", "r", encoding="utf-8") as f:
        story_data = json.load(f)
    
    if not story_data:
        raise ValueError("story.json is empty")
    
    title = _extract_title(story_data)
    return title, story_data


def _extract_title(story_data):
    """Extract book title from prompt.txt or story data."""
    title = "My Storybook"
    
    if os.path.exists("prompt.txt"):
        with open("prompt.txt", "r", encoding="utf-8") as f:
            content = f.read()
            title_match = re.match(r"Title:\s*(.+)", content)
            if title_match:
                title = title_match.group(1).strip()
    
    # Check if first page contains a short title
    if story_data:
        potential_title = story_data[0].get("story", "").strip()
        if potential_title and len(potential_title.split()) <= 10:
            if potential_title.isupper() or "'" in potential_title:
                title = potential_title
    
    return title


def create_page_with_background(bg_image_path, main_image_path=None):
    """Create a page with a radial gradient transparent background image.
    
    Center has BG_OPACITY_CENTER opacity, edges have BG_OPACITY_EDGE opacity.
    Background color is a light shade of the dominant color from main image.
    """
    if main_image_path and os.path.exists(main_image_path):
        bg_color = get_light_color(main_image_path)
    else:
        bg_color = DEFAULT_LIGHT_COLOR
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), bg_color)
    
    if os.path.exists(bg_image_path):
        bg_img = Image.open(bg_image_path).convert('RGBA')
        bg_img = bg_img.resize(
            (PAGE_WIDTH, PAGE_HEIGHT), Image.Resampling.LANCZOS
        )
        
        gradient_mask = create_radial_gradient_mask(
            PAGE_WIDTH, PAGE_HEIGHT, BG_OPACITY_CENTER, BG_OPACITY_EDGE
        )
        bg_img.putalpha(gradient_mask)
        
        page = Image.new('RGBA', (PAGE_WIDTH, PAGE_HEIGHT), bg_color)
        page = Image.alpha_composite(page, bg_img)
        page = page.convert('RGB')
    
    return page


# Font configuration
FONT_PATHS = {
    "title": ["fonts/Pacifico-Regular.ttf", "fonts/DynaPuff-Regular.ttf"],
    "story": ["fonts/DynaPuff-Regular.ttf", "fonts/Pacifico-Regular.ttf"],
    "cover_title": [
        "fonts/titles/Slackey-Regular.ttf",
        "fonts/titles/Ranchers-Regular.ttf",
        "fonts/titles/Peralta-Regular.ttf",
        "fonts/titles/IrishGrover-Regular.ttf",
        "fonts/titles/BraahOne-Regular.ttf"
    ]
}


def get_font(size=FONT_SIZE, font_type="story"):
    """Get a font for the book.
    
    Args:
        size: Font size in pixels
        font_type: 'story' for story text, 'title' for titles
    """
    try:
        for font_path in FONT_PATHS.get(font_type, FONT_PATHS["story"]):
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def draw_centered_text(draw, text, font, area_top, area_height,
                       text_color=(0, 0, 0), shadow_offset=1):
    """Draw text centered horizontally and vertically in the given area.
    
    Args:
        draw: ImageDraw object
        text: Text to draw
        font: Font to use
        area_top: Top Y coordinate of the text area
        area_height: Height of the text area
        text_color: RGB tuple for text color
        shadow_offset: Offset for shadow effect (default 2 pixels)
    """
    max_width = PAGE_WIDTH - (2 * TEXT_MARGIN)
    
    # Wrap text to fit width
    lines = wrap_text(text, font, max_width, draw)
    
    # Calculate total text height
    line_height = int(FONT_SIZE * LINE_SPACING)
    total_text_height = len(lines) * line_height
    
    # Calculate starting Y position to center vertically
    start_y = area_top + (area_height - total_text_height) // 2
    
    # Calculate shadow color (semi-transparent dark version)
    shadow_color = (
        max(0, text_color[0] // 4),
        max(0, text_color[1] // 4),
        max(0, text_color[2] // 4)
    )
    
    # Draw each line centered horizontally
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (PAGE_WIDTH - text_width) // 2
        y = start_y + (i * line_height)
        
        # Draw shadow first (offset down and right)
        draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)
        
        # Draw main text on top
        draw.text((x, y), line, font=font, fill=text_color)


# Page number settings
PAGE_NUMBER_MARGIN = 80
PAGE_NUMBER_SIZE_MULTIPLIER = 2


def draw_page_number(draw, page_number, position,
                     text_color=DEFAULT_DARK_COLOR):
    """Draw page number centered horizontally.
    
    Args:
        draw: ImageDraw object
        page_number: Page number to display
        position: 'top' or 'bottom'
        text_color: RGB tuple for text color
    """
    page_num_font = get_font(int(FONT_SIZE * PAGE_NUMBER_SIZE_MULTIPLIER))
    page_num_str = str(page_number)
    
    bbox = draw.textbbox((0, 0), page_num_str, font=page_num_font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    x = (PAGE_WIDTH - text_width) // 2
    if position == 'top':
        y = PAGE_NUMBER_MARGIN
    else:
        y = PAGE_HEIGHT - PAGE_NUMBER_MARGIN - text_height
    
    draw.text((x, y), page_num_str, font=page_num_font, fill=text_color)


def _resize_and_crop_image(img, target_width, target_height):
    """Resize image to cover target area and center crop."""
    img_width, img_height = img.size
    scale = max(target_width / img_width, target_height / img_height)
    new_width, new_height = int(img_width * scale), int(img_height * scale)
    
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    return img.crop((left, top, left + target_width, top + target_height))


def create_story_page_with_image_and_text(page_number, bg_image_path, main_image_path, text):
    """Create a story page with alternating layouts.
    
    Odd pages: Image on top, text on bottom
    Even pages: Text on top, image on bottom
    """
    is_odd_page = page_number % 2 == 1
    
    # Randomize edge type (seeded by page number for consistency)
    random.seed(page_number)
    edge_type = random.choice(EDGE_TYPES)
    
    page = create_page_with_background(bg_image_path, main_image_path)
    text_color = get_dominant_color(main_image_path)
    
    if os.path.exists(main_image_path):
        main_img = Image.open(main_image_path).convert('RGBA')
        main_img = _resize_and_crop_image(main_img, PAGE_WIDTH, HALF_HEIGHT)
        
        # Apply decorative mask
        decorative_mask = create_decorative_mask(
            PAGE_WIDTH, HALF_HEIGHT, edge_type=edge_type, at_top=not is_odd_page
        )
        main_img.putalpha(decorative_mask)
        
        # Composite image onto page
        page = page.convert('RGBA')
        image_y = 0 if is_odd_page else HALF_HEIGHT
        page.alpha_composite(main_img, (0, image_y))
        page = page.convert('RGB')
    
    # Draw text and page number
    draw = ImageDraw.Draw(page)
    font = get_font(FONT_SIZE)
    
    text_y = HALF_HEIGHT if is_odd_page else 0
    page_num_position = 'bottom' if is_odd_page else 'top'
    
    draw_centered_text(draw, text, font, text_y, HALF_HEIGHT, text_color=text_color)
    draw_page_number(draw, page_number, page_num_position, text_color=text_color)
    
    return page

# Cover title settings
COVER_TITLE_FONT_SIZE = 144
COVER_TITLE_SHADOW_OFFSET = 6
COVER_TITLE_OUTLINE_WIDTH = 2
COVER_TITLE_LETTER_SPACING = 8  # Extra pixels between letters
COVER_TITLE_3D_DEPTH = 15  # Number of shadow layers for 3D effect
COVER_TITLE_LINE_HEIGHT = 1.1  # Tighter line spacing for title


def _extract_colors_from_region(image_path, top_fraction=0, bottom_fraction=1):
    """Extract colors from a specific vertical region of the image.
    
    Args:
        image_path: Path to the image
        top_fraction: Start of region (0-1, from top)
        bottom_fraction: End of region (0-1, from top)
    """
    try:
        img = Image.open(image_path).convert('RGB')
        width, height = img.size
        
        # Crop to the specified region
        top = int(height * top_fraction)
        bottom = int(height * bottom_fraction)
        region = img.crop((0, top, width, bottom))
        region = region.resize((100, 100), Image.Resampling.LANCZOS)
        
        # Quantize pixels
        pixels = list(region.getdata())
        quantized = [
            ((r // COLOR_QUANTIZE_LEVELS) * COLOR_QUANTIZE_LEVELS,
             (g // COLOR_QUANTIZE_LEVELS) * COLOR_QUANTIZE_LEVELS,
             (b // COLOR_QUANTIZE_LEVELS) * COLOR_QUANTIZE_LEVELS)
            for r, g, b in pixels
        ]
        
        color_counts = Counter(quantized)
        most_common = color_counts.most_common(50)
        
        # Score colors by vibrancy
        valid_colors = []
        for color, count in most_common:
            r, g, b = color
            max_c, min_c = max(r, g, b), min(r, g, b)
            if max_c < MIN_BRIGHTNESS:
                continue
            saturation = (max_c - min_c) / max_c if max_c > 0 else 0
            if saturation < MIN_SATURATION:
                continue
            score = (saturation * 300) + max_c
            valid_colors.append((color, score))
        
        if not valid_colors:
            for color, count in most_common:
                max_c = max(color)
                if max_c > 50:
                    valid_colors.append((color, max_c))
        
        valid_colors.sort(key=lambda x: x[1], reverse=True)
        return valid_colors
    except Exception:
        return []


def draw_cover_title(draw, title, font, title_area_height, image_path):
    """Draw the book title on the cover with shadow and outline.
    
    Args:
        draw: ImageDraw object
        title: Title text to draw
        font: Font to use
        title_area_height: Height of the title area (top 1/3 of page)
        image_path: Path to cover image for color extraction
    """
    # Get colors from bottom 2/3 of image (not the title area) for contrast
    if os.path.exists(image_path):
        # Extract colors from bottom 2/3 of image
        region_colors = _extract_colors_from_region(image_path, 1/3, 1)
        
        if region_colors:
            # Find the MOST SATURATED color (not just brightest)
            def get_saturation(color):
                r, g, b = color[0]
                max_c, min_c = max(r, g, b), min(r, g, b)
                return (max_c - min_c) / max_c if max_c > 0 else 0
            
            most_saturated = max(region_colors, key=get_saturation)
            r, g, b = most_saturated[0]
            
            # Determine the dominant channel and create a pure vibrant color
            max_val = max(r, g, b)
            if max_val > 0:
                # Normalize to find dominant color channel
                r_norm, g_norm, b_norm = r / max_val, g / max_val, b / max_val
                
                # Push towards pure colors - amplify differences
                boost = 3.0
                r_new = min(255, int(128 + (r_norm - 0.5) * 255 * boost))
                g_new = min(255, int(128 + (g_norm - 0.5) * 255 * boost))
                b_new = min(255, int(128 + (b_norm - 0.5) * 255 * boost))
                
                # Clamp and ensure at least one channel is at max
                r_new = max(0, min(255, r_new))
                g_new = max(0, min(255, g_new))
                b_new = max(0, min(255, b_new))
                
                # Boost the maximum channel to 255
                current_max = max(r_new, g_new, b_new)
                if current_max > 0:
                    factor = 255 / current_max
                    title_color = (
                        min(255, int(r_new * factor)),
                        min(255, int(g_new * factor)),
                        min(255, int(b_new * factor))
                    )
                else:
                    title_color = (255, 220, 0)  # Vibrant golden yellow
            else:
                title_color = (255, 220, 0)  # Vibrant golden yellow
            
            # Get very dark color for shadow - near black
            r, g, b = region_colors[0][0]
            shadow_color = (
                max(0, int(r * 0.15)),
                max(0, int(g * 0.15)),
                max(0, int(b * 0.15))
            )
        else:
            title_color = (255, 220, 0)  # Vibrant golden yellow
            shadow_color = (0, 0, 0)
    else:
        title_color = (255, 220, 0)  # Vibrant golden yellow
        shadow_color = (0, 0, 0)
    
    # Outline color (contrast border) - use pure black for maximum contrast
    outline_color = (0, 0, 0)
    
    def get_text_width_with_spacing(text, font, spacing):
        """Calculate total width of text with letter spacing."""
        total_width = 0
        for char in text:
            bbox = draw.textbbox((0, 0), char, font=font)
            total_width += (bbox[2] - bbox[0]) + spacing
        return total_width - spacing if text else 0  # Remove trailing spacing
    
    def draw_text_with_spacing(x, y, text, font, fill, spacing):
        """Draw text character by character with custom letter spacing."""
        current_x = x
        for char in text:
            draw.text((current_x, y), char, font=font, fill=fill)
            bbox = draw.textbbox((0, 0), char, font=font)
            char_width = bbox[2] - bbox[0]
            current_x += char_width + spacing
    
    max_width = PAGE_WIDTH - (2 * TEXT_MARGIN)
    
    # Wrap text to fit width (accounting for letter spacing)
    lines = wrap_text(title, font, max_width - (len(title) * COVER_TITLE_LETTER_SPACING), draw)
    
    # Calculate total text height
    line_height = int(COVER_TITLE_FONT_SIZE * COVER_TITLE_LINE_HEIGHT)
    total_text_height = len(lines) * line_height
    
    # Calculate starting Y position to center vertically in title area
    start_y = (title_area_height - total_text_height) // 2
    
    # Draw each line centered horizontally
    for i, line in enumerate(lines):
        text_width = get_text_width_with_spacing(line, font, COVER_TITLE_LETTER_SPACING)
        x = (PAGE_WIDTH - text_width) // 2
        y = start_y + (i * line_height)
        
        # Draw 3D shadow effect (multiple layers from back to front)
        for depth in range(COVER_TITLE_3D_DEPTH, 0, -1):
            # Calculate shadow color - darker layers further back
            fade = depth / COVER_TITLE_3D_DEPTH
            layer_color = (
                int(shadow_color[0] * (1 - fade * 0.5)),
                int(shadow_color[1] * (1 - fade * 0.5)),
                int(shadow_color[2] * (1 - fade * 0.5))
            )
            shadow_x = x + depth
            shadow_y = y + depth
            draw_text_with_spacing(shadow_x, shadow_y, line, font, layer_color, COVER_TITLE_LETTER_SPACING)
        
        # Draw outline/border (draw text in 8 directions around main text)
        for dx in [-COVER_TITLE_OUTLINE_WIDTH, 0, COVER_TITLE_OUTLINE_WIDTH]:
            for dy in [-COVER_TITLE_OUTLINE_WIDTH, 0, COVER_TITLE_OUTLINE_WIDTH]:
                if dx != 0 or dy != 0:
                    draw_text_with_spacing(x + dx, y + dy, line, font, outline_color, COVER_TITLE_LETTER_SPACING)
        
        # Draw main title text
        draw_text_with_spacing(x, y, line, font, title_color, COVER_TITLE_LETTER_SPACING)


def generate_cover_page(output_dir):
    """Generate the cover page using the original cover image with title."""
    bg_path = "images/page_00_cover_bg.png"
    
    if os.path.exists(bg_path):
        page = Image.open(bg_path).convert('RGB')
        if page.size != (int(PAGE_WIDTH), int(PAGE_HEIGHT)):
            page = page.resize((int(PAGE_WIDTH), int(PAGE_HEIGHT)), Image.Resampling.LANCZOS)
    else:
        page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), (255, 255, 255))
    
    # Get book title and draw it
    title, _ = parse_story()
    draw = ImageDraw.Draw(page)
    title_font = get_font(COVER_TITLE_FONT_SIZE, font_type="cover_title")
    title_area_height = PAGE_HEIGHT // 3  # Top 1/3 of the page
    
    draw_cover_title(draw, title, title_font, title_area_height, bg_path)
    
    output_path = os.path.join(output_dir, "page_00_cover.png")
    page.save(output_path, dpi=(300, 300))
    print(f"  ✅ Created: {output_path}")
    return page

def generate_story_page(page_number, page_data, output_dir):
    """Generate a story page with image and text."""
    text = page_data.get("story", "") if isinstance(page_data, dict) else page_data
    
    bg_path = f"images/page_{page_number:02d}_bg.png"
    main_image_path = f"images/page_{page_number:02d}.png"
    
    page = create_story_page_with_image_and_text(page_number, bg_path, main_image_path, text)
    
    output_path = os.path.join(output_dir, f"page_{page_number:02d}.png")
    page.save(output_path, dpi=(300, 300))
    print(f"  ✅ Created: {output_path}")
    return page


def generate_end_page(page_number, output_dir):
    """Generate the end/thank you page using background image like cover page."""
    bg_path = f"images/page_{page_number:02d}_end_bg.png"
    
    # Load background image like cover page does
    if os.path.exists(bg_path):
        page = Image.open(bg_path).convert('RGB')
        if page.size != (int(PAGE_WIDTH), int(PAGE_HEIGHT)):
            page = page.resize((int(PAGE_WIDTH), int(PAGE_HEIGHT)), Image.Resampling.LANCZOS)
    else:
        page = Image.new('RGB', (int(PAGE_WIDTH), int(PAGE_HEIGHT)), (255, 255, 255))
    
    draw = ImageDraw.Draw(page)
    
    # Load DynaPuff font
    visit_font = get_font(30, font_type="story")  # 30pt for visit text
    url_font = get_font(30, font_type="story")  # 30pt for URL
    
    black_color = (0, 0, 0)
    white_color = (255, 255, 255)
    
    # Text content
    visit_text = "Visit us at"
    url_text = ETSY_SHOP_URL
    
    # Get text dimensions
    visit_bbox = draw.textbbox((0, 0), visit_text, font=visit_font)
    url_bbox = draw.textbbox((0, 0), url_text, font=url_font)
    
    visit_height = visit_bbox[3] - visit_bbox[1]
    url_height = url_bbox[3] - url_bbox[1]
    url_width = url_bbox[2] - url_bbox[0]
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url_text)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_size = 150  # Size of QR code in pixels
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    # Spacing between lines
    line_spacing = 40
    qr_spacing = 30  # Space between URL and QR code
    total_height = visit_height + line_spacing + url_height + qr_spacing + qr_size
    
    # Draw black background bar covering the bottom 1/6 of the page
    black_bar_top = int(PAGE_HEIGHT * 5 // 6)
    black_bar_height = PAGE_HEIGHT - black_bar_top
    draw.rectangle([0, black_bar_top, PAGE_WIDTH, PAGE_HEIGHT], fill=black_color)
    
    # Center text vertically within the black bar
    start_y = black_bar_top + (black_bar_height - total_height) // 2
    
    # Draw "Visit us at" centered (white text on black background)
    visit_width = visit_bbox[2] - visit_bbox[0]
    visit_x = (PAGE_WIDTH - visit_width) // 2
    visit_y = start_y
    draw.text((visit_x, visit_y), visit_text, font=visit_font, fill=white_color)
    
    # Draw URL (white text on black background - already on black bar)
    url_x = (PAGE_WIDTH - url_width) // 2
    url_y = visit_y + visit_height + line_spacing
    draw.text((url_x, url_y), url_text, font=url_font, fill=white_color)
    
    # Paste QR code centered below URL
    qr_x = (PAGE_WIDTH - qr_size) // 2
    qr_y = url_y + url_height + qr_spacing
    page.paste(qr_img, (qr_x, qr_y))
    
    output_path = os.path.join(output_dir, f"page_{page_number:02d}_end.png")
    page.save(output_path, dpi=(300, 300))
    print(f"  ✅ Created: {output_path}")
    return page

def main():
    """Generate all book pages from story.json."""
    output_dir = "pages"
    os.makedirs(output_dir, exist_ok=True)
    
    title, story_pages = parse_story()
    total_pages = len(story_pages) + 2  # cover + story pages + end page
    
    print(f"\nGenerating {total_pages} book pages (6x9 inches at 300 DPI)")
    print(f"Book Title: {title}")
    print(f"Background opacity: radial gradient {int(BG_OPACITY_CENTER * 100)}% (center) to {int(BG_OPACITY_EDGE * 100)}% (edge)")
    print("=" * 60)
    
    # Generate cover
    print(f"Generating cover page (1/{total_pages})...")
    generate_cover_page(output_dir)
    
    # Generate story pages
    for i, page_data in enumerate(story_pages, start=1):
        print(f"Generating story page {i} ({i + 1}/{total_pages})...")
        generate_story_page(i, page_data, output_dir)
    
    # Generate end page
    end_page_num = len(story_pages) + 1
    print(f"Generating end page ({total_pages}/{total_pages})...")
    generate_end_page(end_page_num, output_dir)
    
    print("=" * 60)
    print(f"✅ All {total_pages} pages generated!")
    print(f"📁 Output saved to: {output_dir}/")

if __name__ == "__main__":
    main()
