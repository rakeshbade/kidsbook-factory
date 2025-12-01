# generate_page.py
from PIL import Image, ImageDraw, ImageFont
import os
import re
import math
import numpy as np
import textwrap

# Page dimensions: 6x9 inches at 300 DPI
PAGE_WIDTH = 1800   # 6 inches * 300 DPI
PAGE_HEIGHT = 2700  # 9 inches * 300 DPI
HALF_HEIGHT = PAGE_HEIGHT // 2  # Top half for image, bottom half for text

# Radial gradient opacity settings
BG_OPACITY_CENTER = 0.03  # 3% opacity at center
BG_OPACITY_EDGE = 0.15    # 15% opacity at edges

# Text settings
FONT_SIZE = 48
LINE_SPACING = 1.4
TEXT_MARGIN = 100  # Margin from edges in pixels

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

def create_page_with_background(page_number, bg_image_path, output_path):
    """Create a page with a radial gradient transparent background image.
    Center has 3% opacity, edges have 15% opacity.
    """
    
    # Create white base page
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), 'white')
    
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
        
        # Composite background onto white page
        page = Image.new('RGBA', (PAGE_WIDTH, PAGE_HEIGHT), 'white')
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
    """
    
    # Create the page with gradient background
    page = create_page_with_background(page_number, bg_image_path, None)
    
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
    
    # Draw text in bottom half, centered
    draw = ImageDraw.Draw(page)
    font = get_font(FONT_SIZE)
    draw_centered_text(draw, text, font, HALF_HEIGHT, HALF_HEIGHT)
    
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
