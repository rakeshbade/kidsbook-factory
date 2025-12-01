# generate_page.py
from PIL import Image, ImageDraw, ImageFont
import os
import re
import math
import numpy as np
import textwrap
import random
from collections import Counter

# Page dimensions: 6x9 inches at 300 DPI
PAGE_WIDTH = 1800   # 6 inches * 300 DPI
PAGE_HEIGHT = 2700  # 9 inches * 300 DPI
HALF_HEIGHT = PAGE_HEIGHT // 2  # Top half for image, bottom half for text

# Radial gradient opacity settings
BG_OPACITY_CENTER = 0.03  # 3% opacity at center
BG_OPACITY_EDGE = 0.15    # 15% opacity at edges

# Text settings
FONT_SIZE = 48
LINE_SPACING = 2.0  # Line spacing multiplier
TEXT_MARGIN = 100  # Margin from edges in pixels

def get_dominant_color(image_path, num_colors=50):
    """Extract the most vibrant color from an image and return its darkest variant."""
    try:
        img = Image.open(image_path).convert('RGB')
        # Resize for faster processing
        img = img.resize((100, 100), Image.Resampling.LANCZOS)
        
        # Get all pixels
        pixels = list(img.getdata())
        
        # Count color occurrences (quantize to reduce unique colors)
        quantized = []
        for r, g, b in pixels:
            # Quantize to 32 levels per channel
            qr, qg, qb = (r // 8) * 8, (g // 8) * 8, (b // 8) * 8
            quantized.append((qr, qg, qb))
        
        # Find most common colors - get more to find vibrant ones
        color_counts = Counter(quantized)
        most_common = color_counts.most_common(num_colors)
        
        # Calculate saturation and brightness for each color
        # Prioritize vibrant colors over greys
        valid_colors = []
        for color, count in most_common:
            r, g, b = color
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            
            # Skip very dark colors
            if max_c < 60:
                continue
            
            # Calculate saturation (0-1 range)
            if max_c == 0:
                saturation = 0
            else:
                saturation = (max_c - min_c) / max_c
            
            # Skip greys (low saturation colors)
            if saturation < 0.25:
                continue
            
            # Calculate brightness using max channel (HSV Value)
            brightness = max_c
            
            # Score: heavily prioritize saturation, then brightness
            # This ensures vibrant colors win over greys
            score = (saturation * 300) + brightness
            
            valid_colors.append((color, count, score, saturation, brightness))
        
        if not valid_colors:
            # Fallback: if no saturated colors found, get the brightest from all
            for color, count in most_common:
                r, g, b = color
                max_c = max(r, g, b)
                if max_c > 50:  # Skip very dark
                    valid_colors.append((color, count, max_c, 0, max_c))
        
        if not valid_colors:
            return (0, 0, 0)
        
        # Sort by score (descending) to get the most vibrant bright color
        valid_colors.sort(key=lambda x: x[2], reverse=True)
        
        # Get the best color
        best_color = valid_colors[0][0] if valid_colors else (100, 100, 100)
        
        # Create a darker version (30% of original brightness)
        r, g, b = best_color
        dark_r = max(0, int(r * 0.5))
        dark_g = max(0, int(g * 0.6))
        dark_b = max(0, int(b * 0.7))
        
        return (dark_r, dark_g, dark_b)
    
    except Exception as e:
        print(f"    ⚠️ Could not extract color: {e}")
        return (0, 0, 0)  # Default to black

def get_light_color(image_path, num_colors=50):
    """Extract the most vibrant color from an image and return a light shade of it."""
    try:
        img = Image.open(image_path).convert('RGB')
        # Resize for faster processing
        img = img.resize((100, 100), Image.Resampling.LANCZOS)
        
        # Get all pixels
        pixels = list(img.getdata())
        
        # Count color occurrences (quantize to reduce unique colors)
        quantized = []
        for r, g, b in pixels:
            # Quantize to 32 levels per channel
            qr, qg, qb = (r // 8) * 8, (g // 8) * 8, (b // 8) * 8
            quantized.append((qr, qg, qb))
        
        # Find most common colors - get more to find vibrant ones
        color_counts = Counter(quantized)
        most_common = color_counts.most_common(num_colors)
        
        # Calculate saturation and brightness for each color
        valid_colors = []
        for color, count in most_common:
            r, g, b = color
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            
            # Skip very dark colors
            if max_c < 60:
                continue
            
            # Calculate saturation (0-1 range)
            if max_c == 0:
                saturation = 0
            else:
                saturation = (max_c - min_c) / max_c
            
            # Skip greys (low saturation colors)
            if saturation < 0.25:
                continue
            
            # Calculate brightness using max channel (HSV Value)
            brightness = max_c
            
            # Score: heavily prioritize saturation, then brightness
            score = (saturation * 300) + brightness
            
            valid_colors.append((color, count, score, saturation, brightness))
        
        if not valid_colors:
            # Fallback: if no saturated colors found, get the brightest from all
            for color, count in most_common:
                r, g, b = color
                max_c = max(r, g, b)
                if max_c > 50:
                    valid_colors.append((color, count, max_c, 0, max_c))
        
        if not valid_colors:
            return (255, 250, 245)  # Default to warm white
        
        # Sort by score (descending) to get the most vibrant bright color
        valid_colors.sort(key=lambda x: x[2], reverse=True)
        
        # Get the best color
        best_color = valid_colors[0][0] if valid_colors else (255, 250, 245)
        
        # Create a light version (high brightness, low saturation tint)
        r, g, b = best_color
        # Blend with white to create a light pastel shade
        light_r = min(255, int(255 - (255 - r) * 0.15))
        light_g = min(255, int(255 - (255 - g) * 0.12))
        light_b = min(255, int(255 - (255 - b) * 0.10))
        
        return (light_r, light_g, light_b)
    
    except Exception as e:
        print(f"    ⚠️ Could not extract light color: {e}")
        return (255, 250, 245)  # Default to warm white

def create_decorative_mask(width, height, edge_type="wave"):
    """Create a mask with a decorative bottom edge for the image.
    
    edge_type options:
    - 'wave': Smooth sine wave pattern
    - 'scallop': Rounded scallop/cloud pattern  
    - 'zigzag': Triangular zigzag pattern
    """
    # Create a white mask (fully opaque)
    mask = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(mask)
    
    # Parameters for the decorative edge
    wave_height = 25  # How tall the waves are (shorter)
    wave_count = random.randint(2, 10)    # Number of waves across the width
    
    if edge_type == "wave":
        # Create smooth sine wave bottom edge
        points = [(0, 0), (0, height)]  # Start from top-left, go down
        
        for x in range(width + 1):
            # Sine wave formula
            progress = x / width * wave_count * 2 * math.pi
            y_offset = math.sin(progress) * wave_height
            y = height - wave_height + y_offset
            points.append((x, y))
        
        points.append((width, 0))  # Complete the polygon
        
        # Draw the mask - white inside (visible), black outside (hidden)
        draw.polygon(points, fill=255)
        
        # Clear the area below the wave
        for x in range(width):
            progress = x / width * wave_count * 2 * math.pi
            y_offset = math.sin(progress) * wave_height
            wave_y = int(height - wave_height + y_offset)
            draw.line([(x, wave_y), (x, height)], fill=0)
            
    elif edge_type == "scallop":
        # Create rounded scallop/cloud pattern
        scallop_width = width // wave_count
        scallop_radius = scallop_width // 2
        
        # Fill the main area white
        draw.rectangle([0, 0, width, height - scallop_radius], fill=255)
        
        # Draw scallops (semicircles) at the bottom
        for i in range(wave_count + 1):
            center_x = i * scallop_width
            center_y = height - scallop_radius - 10
            
            # Draw filled semicircle
            bbox = [
                center_x - scallop_radius,
                center_y,
                center_x + scallop_radius,
                center_y + scallop_radius * 2
            ]
            draw.ellipse(bbox, fill=255)
        
        # Clear below the scallops
        for x in range(width):
            # Find which scallop this x belongs to
            scallop_index = x // scallop_width
            center_x = scallop_index * scallop_width + scallop_radius
            center_y = height - scallop_radius - 10
            
            # Calculate distance from scallop center
            dx = abs(x - center_x)
            if dx < scallop_radius:
                # Inside scallop arc
                arc_y = center_y + int(math.sqrt(scallop_radius**2 - dx**2))
                draw.line([(x, arc_y), (x, height)], fill=0)
            else:
                # Between scallops
                draw.line([(x, center_y), (x, height)], fill=0)
                
    elif edge_type == "zigzag":
        # Create triangular zigzag pattern
        tooth_width = width // (wave_count * 2)
        
        points = [(0, 0), (0, height - wave_height)]
        
        for i in range(wave_count * 2 + 1):
            x = i * tooth_width
            if i % 2 == 0:
                y = height - wave_height
            else:
                y = height
            points.append((x, y))
        
        points.append((width, height - wave_height))
        points.append((width, 0))
        
        draw.polygon(points, fill=255)
        
        # Clear below zigzag
        for i in range(wave_count * 2):
            x1 = i * tooth_width
            x2 = (i + 1) * tooth_width
            if i % 2 == 0:
                # Going down
                y1 = height - wave_height
                y2 = height
            else:
                # Going up
                y1 = height
                y2 = height - wave_height
            
            for x in range(x1, min(x2, width)):
                progress = (x - x1) / tooth_width
                y = int(y1 + (y2 - y1) * progress)
                draw.line([(x, y), (x, height)], fill=0)
    
    return mask

def create_decorative_mask_top(width, height, edge_type="wave"):
    """Create a mask with a decorative TOP edge for the image (for even pages).
    
    edge_type options:
    - 'wave': Smooth sine wave pattern at the top
    - 'scallop': Rounded scallop/cloud pattern at the top
    - 'zigzag': Triangular zigzag pattern at the top
    """
    # Create a white mask (fully opaque)
    mask = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(mask)
    
    # Parameters for the decorative edge
    wave_height = 25  # How tall the waves are
    wave_count = 8    # Number of waves across the width
    
    if edge_type == "wave":
        # Clear the area above the wave
        for x in range(width):
            progress = x / width * wave_count * 2 * math.pi
            y_offset = math.sin(progress) * wave_height
            wave_y = int(wave_height - y_offset)
            draw.line([(x, 0), (x, wave_y)], fill=0)
            
    elif edge_type == "scallop":
        # Create rounded scallop/cloud pattern at top
        scallop_width = width // wave_count
        scallop_radius = scallop_width // 2
        
        # Clear above the scallops
        for x in range(width):
            scallop_index = x // scallop_width
            center_x = scallop_index * scallop_width + scallop_radius
            center_y = scallop_radius + 10
            
            dx = abs(x - center_x)
            if dx < scallop_radius:
                arc_y = center_y - int(math.sqrt(scallop_radius**2 - dx**2))
                draw.line([(x, 0), (x, arc_y)], fill=0)
            else:
                draw.line([(x, 0), (x, center_y)], fill=0)
                
    elif edge_type == "zigzag":
        # Create triangular zigzag pattern at top
        tooth_width = width // (wave_count * 2)
        
        for i in range(wave_count * 2):
            x1 = i * tooth_width
            x2 = (i + 1) * tooth_width
            if i % 2 == 0:
                y1 = wave_height
                y2 = 0
            else:
                y1 = 0
                y2 = wave_height
            
            for x in range(x1, min(x2, width)):
                progress = (x - x1) / tooth_width
                y = int(y1 + (y2 - y1) * progress)
                draw.line([(x, 0), (x, y)], fill=0)
    
    return mask

def create_wave_shadow(width, height, wave_height=25, wave_count=8, shadow_offset=8, shadow_blur=15):
    """Create a shadow image that follows the wave pattern."""
    # Create a larger image for blur effect
    shadow = Image.new('RGBA', (width, height + 50), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    # Draw shadow shape (slightly offset down from the wave)
    points = []
    for x in range(width + 1):
        progress = x / width * wave_count * 2 * math.pi
        y_offset = math.sin(progress) * wave_height
        y = height - wave_height + y_offset + shadow_offset
        points.append((x, y))
    
    # Complete the polygon to fill below
    points.append((width, height + 50))
    points.append((0, height + 50))
    
    # Draw shadow with gradient opacity
    draw.polygon(points, fill=(0, 0, 0, 60))
    
    # Apply blur for soft shadow effect
    from PIL import ImageFilter
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    
    return shadow

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
    """Parse story.txt and extract title and story segments with their page numbers."""
    story_pages = []
    
    with open("story.txt", "r") as f:
        content = f.read()
    
    # Extract title
    title_match = re.match(r"Title:\s*(.+)", content)
    title = title_match.group(1).strip() if title_match else "My Storybook"
    
    # Split by IMAGE: markers to get story segments
    parts = re.split(r'\nIMAGE:[^\n]+\n?', content)
    
    # First part contains title, skip it for page content
    # Process remaining parts as story pages
    for i, part in enumerate(parts):
        text = part.strip()
        # Skip title line
        if text.startswith("Title:"):
            text = re.sub(r"Title:[^\n]+\n?", "", text).strip()
        if text:
            story_pages.append(text)
    
    return title, story_pages

def create_page_with_background(page_number, bg_image_path, output_path, main_image_path=None):
    """Create a page with a radial gradient transparent background image.
    Center has 3% opacity, edges have 15% opacity.
    Background color is a light shade of the dominant color from main image.
    """
    
    # Get light background color from main image
    if main_image_path and os.path.exists(main_image_path):
        bg_color = get_light_color(main_image_path)
    else:
        bg_color = (255, 250, 245)  # Warm white fallback
    
    # Create base page with light color
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), bg_color)
    
    # Load and process background image if it exists
    if os.path.exists(bg_image_path):
        bg_img = Image.open(bg_image_path).convert('RGBA')
        
        # Resize background to fit page
        bg_img = bg_img.resize((PAGE_WIDTH, PAGE_HEIGHT), Image.Resampling.LANCZOS)
        
        # Create radial gradient mask (center=3%, edge=15%)
        gradient_mask = create_radial_gradient_mask(
            PAGE_WIDTH, PAGE_HEIGHT, 
            BG_OPACITY_CENTER, BG_OPACITY_EDGE
        )
        
        # Apply gradient mask as alpha channel
        bg_img.putalpha(gradient_mask)
        
        # Composite background onto colored page
        page = Image.new('RGBA', (PAGE_WIDTH, PAGE_HEIGHT), bg_color)
        page = Image.alpha_composite(page, bg_img)
        page = page.convert('RGB')
    
    return page

def get_font(size=FONT_SIZE, font_type="story"):
    """Get a Google Font for the book.
    font_type: 'story' for story text (DynaPuff), 'title' for titles (Pacifico)
    """
    try:
        # Google Fonts stored locally in fonts folder
        if font_type == "title":
            font_paths = [
                "fonts/Pacifico-Regular.ttf",      # Decorative title font
                "fonts/DynaPuff-Regular.ttf",      # Fallback
            ]
        else:  # story text
            font_paths = [
                "fonts/DynaPuff-Regular.ttf",      # Fun, readable children's font
                "fonts/Pacifico-Regular.ttf",      # Fallback
            ]
        
        for font_path in font_paths:
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

def draw_centered_text(draw, text, font, area_top, area_height, text_color=(0, 0, 0)):
    """Draw text centered horizontally and vertically in the given area."""
    max_width = PAGE_WIDTH - (2 * TEXT_MARGIN)
    
    # Wrap text to fit width
    lines = wrap_text(text, font, max_width, draw)
    
    # Calculate total text height
    line_height = int(FONT_SIZE * LINE_SPACING)
    total_text_height = len(lines) * line_height
    
    # Calculate starting Y position to center vertically
    start_y = area_top + (area_height - total_text_height) // 2
    
    # Draw each line centered horizontally
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (PAGE_WIDTH - text_width) // 2
        y = start_y + (i * line_height)
        draw.text((x, y), line, font=font, fill=text_color)

def draw_page_number(draw, page_number, position, text_color=(0, 0, 0)):
    """Draw page number centered horizontally.
    
    position: 'top' or 'bottom' of the text area
    - 'bottom': For odd pages (text at bottom, number below text)
    - 'top': For even pages (text at top, number above text)
    """
    # Use 2x the story font size for page number
    page_num_font = get_font(int(FONT_SIZE * 2))
    page_num_str = str(page_number)
    
    # Get text dimensions
    bbox = draw.textbbox((0, 0), page_num_str, font=page_num_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center horizontally
    x = (PAGE_WIDTH - text_width) // 2
    
    # Position vertically based on layout
    # Use same visual margin from the edge for both top and bottom
    margin_from_edge = 80  # Distance from edge of page
    
    if position == 'bottom':
        # For odd pages: page number at bottom of the page
        y = PAGE_HEIGHT - margin_from_edge - text_height
    else:  # 'top'
        # For even pages: page number at top of the page
        y = margin_from_edge
    
    draw.text((x, y), page_num_str, font=page_num_font, fill=text_color)

def create_story_page_with_image_and_text(page_number, bg_image_path, main_image_path, text, output_path):
    """Create a story page with alternating layouts:
    - Odd pages: Image on top (wave at bottom), text on bottom
    - Even pages: Text on top, image on bottom (wave at top)
    - Text color: Darkest variant of the dominant color from the main image
    - Background color: Light shade of the dominant color
    - Edge type: Randomized (wave, scallop, or zigzag)
    """
    
    # Determine layout based on page number
    is_odd_page = (page_number % 2 == 1)
    
    # Randomize edge type for variety (seeded by page number for consistency)
    random.seed(page_number)
    edge_type = random.choice(["wave", "scallop", "zigzag"])
    
    # Create the page with gradient background and colored base
    page = create_page_with_background(page_number, bg_image_path, None, main_image_path)
    
    # Get text color from main image's dominant color
    text_color = get_dominant_color(main_image_path)
    
    # Load and process main image
    if os.path.exists(main_image_path):
        main_img = Image.open(main_image_path).convert('RGBA')
        
        # Resize main image to fit half page (maintain aspect ratio, cover)
        img_width, img_height = main_img.size
        target_width = PAGE_WIDTH
        target_height = HALF_HEIGHT
        
        # Scale to cover the area
        scale = max(target_width / img_width, target_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        main_img = main_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center crop to fit exactly
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        main_img = main_img.crop((left, top, left + target_width, top + target_height))
        
        # Convert page to RGBA for compositing
        page = page.convert('RGBA')
        
        if is_odd_page:
            # ODD PAGE: Image on TOP with decorative edge at bottom
            decorative_mask = create_decorative_mask(target_width, target_height, edge_type=edge_type)
            main_img.putalpha(decorative_mask)
            
            # Place image at top
            page.alpha_composite(main_img, (0, 0))
            
            # Convert back to RGB and draw text in bottom half
            page = page.convert('RGB')
            draw = ImageDraw.Draw(page)
            font = get_font(FONT_SIZE)
            draw_centered_text(draw, text, font, HALF_HEIGHT, HALF_HEIGHT, text_color=text_color)
            # Draw page number at bottom
            draw_page_number(draw, page_number, 'bottom', text_color=text_color)
        else:
            # EVEN PAGE: Text on TOP, image on BOTTOM with decorative edge at top
            decorative_mask = create_decorative_mask_top(target_width, target_height, edge_type=edge_type)
            main_img.putalpha(decorative_mask)
            
            # Place image at bottom
            page.alpha_composite(main_img, (0, HALF_HEIGHT))
            
            # Convert back to RGB and draw text in top half
            page = page.convert('RGB')
            draw = ImageDraw.Draw(page)
            font = get_font(FONT_SIZE)
            draw_centered_text(draw, text, font, 0, HALF_HEIGHT, text_color=text_color)
            # Draw page number at top
            draw_page_number(draw, page_number, 'top', text_color=text_color)
    else:
        # No image - just draw text based on layout
        draw = ImageDraw.Draw(page)
        font = get_font(FONT_SIZE)
        if is_odd_page:
            draw_centered_text(draw, text, font, HALF_HEIGHT, HALF_HEIGHT, text_color=text_color)
            draw_page_number(draw, page_number, 'bottom', text_color=text_color)
        else:
            draw_centered_text(draw, text, font, 0, HALF_HEIGHT, text_color=text_color)
            draw_page_number(draw, page_number, 'top', text_color=text_color)
    
    return page

def generate_cover_page(title, output_dir):
    """Generate the cover page with title."""
    bg_path = "images/page_00_cover_bg.png"
    page = create_page_with_background(0, bg_path, None)
    
    # Save cover page
    output_path = os.path.join(output_dir, "page_00_cover.png")
    page.save(output_path, dpi=(300, 300))
    print(f"  ✅ Created: {output_path}")
    return page

def generate_story_page(page_number, text, output_dir):
    """Generate a story page with image in top half and text in bottom half."""
    bg_path = f"images/page_{page_number:02d}_bg.png"
    main_image_path = f"images/page_{page_number:02d}.png"
    
    page = create_story_page_with_image_and_text(page_number, bg_path, main_image_path, text, None)
    
    # Save story page
    output_path = os.path.join(output_dir, f"page_{page_number:02d}.png")
    page.save(output_path, dpi=(300, 300))
    print(f"  ✅ Created: {output_path}")
    return page

def generate_end_page(page_number, output_dir):
    """Generate the end/thank you page."""
    bg_path = f"images/page_{page_number:02d}_end_bg.png"
    page = create_page_with_background(page_number, bg_path, None)
    
    # Save end page
    output_path = os.path.join(output_dir, f"page_{page_number:02d}_end.png")
    page.save(output_path, dpi=(300, 300))
    print(f"  ✅ Created: {output_path}")
    return page

def main():
    output_dir = "pages"
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse story
    title, story_pages = parse_story()
    
    total_pages = len(story_pages) + 2  # cover + story pages + end page
    
    print(f"\nGenerating {total_pages} book pages (6x9 inches at 300 DPI)")
    print(f"Book Title: {title}")
    print(f"Background opacity: radial gradient {int(BG_OPACITY_CENTER * 100)}% (center) to {int(BG_OPACITY_EDGE * 100)}% (edge)")
    print("=" * 60)
    
    # Generate cover page
    print(f"Generating cover page (1/{total_pages})...")
    generate_cover_page(title, output_dir)
    
    # Generate story pages
    for i, text in enumerate(story_pages):
        page_num = i + 1
        print(f"Generating story page {page_num} ({page_num + 1}/{total_pages})...")
        generate_story_page(page_num, text, output_dir)
    
    # Generate end page
    end_page_num = len(story_pages) + 1
    print(f"Generating end page ({total_pages}/{total_pages})...")
    generate_end_page(end_page_num, output_dir)
    
    print("=" * 60)
    print(f"✅ All {total_pages} pages generated!")
    print(f"📁 Output saved to: {output_dir}/")

if __name__ == "__main__":
    main()
