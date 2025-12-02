# variables.py
# Shared configuration variables for the kidsbook-factory project

# Page dimensions: 6x9 inches at 300 DPI (for image generation)
DPI = 300
SCALE_FACTOR = 3
PAGE_WIDTH = 6.25 * DPI   # 6.25 inches * 300 DPI
PAGE_HEIGHT = 9.25 * DPI  # 9.25 inches * 300 DPI

# Image generation dimensions (pre-scaled, before SCALE_FACTOR is applied)
IMAGE_GEN_WIDTH = PAGE_WIDTH // SCALE_FACTOR   # 600 pixels
IMAGE_GEN_HEIGHT = PAGE_HEIGHT // SCALE_FACTOR  # 900 pixels

# PDF page dimensions: 6x9 inches in points (72 points per inch)
PDF_PAGE_WIDTH = (PAGE_WIDTH / DPI) * 72   # 432 points
PDF_PAGE_HEIGHT = (PAGE_HEIGHT / DPI) * 72  # 648 points

# Radial gradient opacity settings
BG_OPACITY_CENTER = 0.03  # 3% opacity at center
BG_OPACITY_EDGE = 0.15    # 15% opacity at edges

# Text settings
FONT_SIZE = 48
LINE_SPACING = 2.0  # Line spacing multiplier
TEXT_MARGIN = 100   # Margin from edges in pixels

# Shop URL for end page
ETSY_SHOP_URL = "https://www.etsy.com/shop/studiobadeshop"
