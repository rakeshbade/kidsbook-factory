# create_pdf.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image
import os, textwrap, json, re

# 8.5 × 8.5 inch square with 0.25" bleed → canvas size 8.75×8.75
size = (8.75*72, 8.75*72)

c = canvas.Canvas(f"output/{os.getenv('GITHUB_RUN_NUMBER', 'test')}_book.pdf", pagesize=size)
story = open("story.txt").read()

pages = re.split(r"IMAGE:", story)[1:]  # first part is title

for i, page_text in enumerate(pages):
    c.setFillColorRGB(1,1,1)
    c.rect(0,0,8.75*72,8.75*72, fill=1)

    # Paste image (already cropped)
    img_path = f"clean_images/page_{i+1:02d}.png"
    if os.path.exists(img_path):
        c.drawImage(img_path, 0.25*72, 0.25*72, width=8*72, height=8*72)

    # Add text at bottom
    lines = textwrap.wrap(page_text.strip(), width=60)
    y = 0.7*72
    for line in lines[-4:]:  # only last 4 lines
        c.setFont("Helvetica", 18)
        c.setFillColorRGB(0,0,0)
        c.drawCentredString(4.375*72, y, line)
        y -= 30

    c.showPage()

c.save()