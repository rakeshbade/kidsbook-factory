# create_pdf.py
from reportlab.pdfgen import canvas
from PIL import Image
import os
import json
from variables import PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT

# 6 × 9 inch page size (standard children's book)
PAGE_WIDTH = PDF_PAGE_WIDTH
PAGE_HEIGHT = PDF_PAGE_HEIGHT
size = (PAGE_WIDTH, PAGE_HEIGHT)

# Double-wide page for cover spread (cover on right, end on left)
SPREAD_WIDTH = PAGE_WIDTH * 2
spread_size = (SPREAD_WIDTH, PAGE_HEIGHT)

# Create output directory
os.makedirs("output", exist_ok=True)

# Load story data
if not os.path.exists("story.json"):
    raise FileNotFoundError("story.json not found. Run generate_story.py first.")

with open("story.json", "r") as f:
    story_data = json.load(f)

# Get list of page images from pages/ directory
pages_dir = "pages"
if not os.path.exists(pages_dir):
    raise FileNotFoundError("pages/ directory not found. Run generate_page.py first.")

page_files = sorted([f for f in os.listdir(pages_dir) if f.endswith('.png')])

if not page_files:
    raise FileNotFoundError("No page images found in pages/ directory.")

# Separate cover, story pages, and end page
cover_file = None
end_file = None
story_files = []

for f in page_files:
    if 'cover' in f:
        cover_file = f
    elif 'end' in f:
        end_file = f
    else:
        story_files.append(f)

run_number = os.getenv('GITHUB_RUN_NUMBER', 'test')

# === PDF 1: Story pages only (pages 01 to 20) ===
story_pdf_filename = f"output/{run_number}_story.pdf"
c1 = canvas.Canvas(story_pdf_filename, pagesize=size)

print(f"\nCreating story PDF with {len(story_files)} pages...")
print(f"Page size: {PAGE_WIDTH}×{PAGE_HEIGHT} points")
print("=" * 60)

for page_file in story_files:
    img_path = os.path.join(pages_dir, page_file)
    
    # Draw white background
    c1.setFillColorRGB(1, 1, 1)
    c1.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1)
    
    # Draw the page image
    if os.path.exists(img_path):
        c1.drawImage(img_path, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        print(f"  ✅ Added: {page_file}")
    else:
        print(f"  ⚠️ Missing: {page_file}")
    
    c1.showPage()

c1.save()
print(f"✅ Story PDF created: {story_pdf_filename}")

# === PDF 2: Cover spread (end on left, cover on right) ===
cover_pdf_filename = f"output/{run_number}_cover.pdf"
c2 = canvas.Canvas(cover_pdf_filename, pagesize=spread_size)

print(f"\nCreating cover spread PDF...")
print(f"Page size: {SPREAD_WIDTH}×{PAGE_HEIGHT} points (double-wide)")
print("=" * 60)

# Draw white background
c2.setFillColorRGB(1, 1, 1)
c2.rect(0, 0, SPREAD_WIDTH, PAGE_HEIGHT, fill=1)

# Draw end page on left side
if end_file:
    end_path = os.path.join(pages_dir, end_file)
    if os.path.exists(end_path):
        c2.drawImage(end_path, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        print(f"  ✅ Added (left): {end_file}")
    else:
        print(f"  ⚠️ Missing: {end_file}")
else:
    print("  ⚠️ No end page found")

# Draw cover on right side
if cover_file:
    cover_path = os.path.join(pages_dir, cover_file)
    if os.path.exists(cover_path):
        c2.drawImage(cover_path, PAGE_WIDTH, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        print(f"  ✅ Added (right): {cover_file}")
    else:
        print(f"  ⚠️ Missing: {cover_file}")
else:
    print("  ⚠️ No cover page found")

c2.showPage()
c2.save()

print("=" * 60)
print(f"✅ Cover spread PDF created: {cover_pdf_filename}")
print(f"\n📁 Output files:")
print(f"   - {story_pdf_filename} ({len(story_files)} pages)")
print(f"   - {cover_pdf_filename} (cover spread)")