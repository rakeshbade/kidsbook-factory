# create_pdf.py
from reportlab.pdfgen import canvas
from PIL import Image
import os
import json

# 6 × 9 inch page size (standard children's book)
PAGE_WIDTH = 6 * 72   # 432 points
PAGE_HEIGHT = 9 * 72  # 648 points
size = (PAGE_WIDTH, PAGE_HEIGHT)

# Create output directory
os.makedirs("output", exist_ok=True)

# Load story data
if not os.path.exists("story.json"):
    raise FileNotFoundError("story.json not found. Run generate_story.py first.")

with open("story.json", "r") as f:
    story_data = json.load(f)

# Create PDF
output_filename = f"output/{os.getenv('GITHUB_RUN_NUMBER', 'test')}_book.pdf"
c = canvas.Canvas(output_filename, pagesize=size)

# Get list of page images from pages/ directory
pages_dir = "pages"
if not os.path.exists(pages_dir):
    raise FileNotFoundError("pages/ directory not found. Run generate_page.py first.")

page_files = sorted([f for f in os.listdir(pages_dir) if f.endswith('.png')])

if not page_files:
    raise FileNotFoundError("No page images found in pages/ directory.")

print(f"\nCreating PDF with {len(page_files)} pages...")
print(f"Page size: 6×9 inches ({PAGE_WIDTH}×{PAGE_HEIGHT} points)")
print("=" * 60)

for page_file in page_files:
    img_path = os.path.join(pages_dir, page_file)
    
    # Draw white background
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1)
    
    # Draw the page image (full page, no margins since images are already formatted)
    if os.path.exists(img_path):
        c.drawImage(img_path, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        print(f"  ✅ Added: {page_file}")
    else:
        print(f"  ⚠️ Missing: {page_file}")
    
    c.showPage()

c.save()
print("=" * 60)
print(f"✅ PDF created: {output_filename}")