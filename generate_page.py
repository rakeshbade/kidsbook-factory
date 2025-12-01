# generate_page.py
from PIL import Image, ImageDraw, ImageFont
import os
import re
import math
import numpy as np
import textwrap
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

def create_story_page_with_image_and_text(page_number, bg_image_path, main_image_path, text, output_path):
    """Create a story page with:
    - Top 50%: Main image (full opacity)
    - Bottom 50%: Story text centered on gradient background
    - Text color: Darkest variant of the dominant color from the main image
    - Background color: Light shade of the dominant color
    """
    
    # Create the page with gradient background and colored base
    page = create_page_with_background(page_number, bg_image_path, None, main_image_path)
    
    # Get text color from main image's dominant color
    text_color = get_dominant_color(main_image_path)
    
    # Load and place main image in top half
    if os.path.exists(main_image_path):
        main_img = Image.open(main_image_path).convert('RGB')
        
        # Resize main image to fit top half (maintain aspect ratio, cover)
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
        
        # Paste main image onto top half of page
        page.paste(main_img, (0, 0))
    
    # Draw text in bottom half, centered with dominant color
    draw = ImageDraw.Draw(page)
    font = get_font(FONT_SIZE)
    draw_centered_text(draw, text, font, HALF_HEIGHT, HALF_HEIGHT, text_color=text_color)
    
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
