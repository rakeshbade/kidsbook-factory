# generate_images.py
import json, os, time, requests

def get_book_title():
    """Extract the book title from story.txt."""
    try:
        with open("story.txt", "r") as f:
            first_line = f.readline().strip()
            if first_line.startswith("Title:"):
                return first_line.replace("Title:", "").strip()
    except Exception as e:
        print(f"⚠️  Could not read title: {e}")
    return "My Storybook"

def generate_image(prompt, filename):
    """Generate two images using Pollinations.ai (FREE, no API key needed).
    1. Portrait (1800x2700) - saved as {filename}.png
    2. Landscape (2700x1800) - saved as {filename}_bg.png
    """
    full_prompt = prompt + ", cartoon style, for children's book, colorful, vibrant, high quality"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Remove .png extension for base filename
    base_filename = filename.replace('.png', '')
    
    # Generate portrait image (1800x2700) - 6x9 inches
    try:
        url_portrait = f"https://image.pollinations.ai/prompt/{requests.utils.quote(full_prompt)}?width=1800&height=2700&nologo=true"
        print(f"    Generating portrait (1800x2700)...")
        response = requests.get(url_portrait, headers=headers, timeout=120)
        response.raise_for_status()
        with open(f"{base_filename}_bg.png", 'wb') as f:
            f.write(response.content)
        print(f"  ✅ Saved: {base_filename}_bg.png")
    except Exception as e:
        print(f"  ❌ Error (portrait): {e}")
    
    time.sleep(3)  # Brief pause between requests
    
    # Generate landscape image (2700x1800) - 9x6 inches
    try:
        url_landscape = f"https://image.pollinations.ai/prompt/{requests.utils.quote(full_prompt)}?width=2700&height=1800&nologo=true"
        print(f"    Generating landscape (2700x1800)...")
        response = requests.get(url_landscape, headers=headers, timeout=120)
        response.raise_for_status()
        with open(f"{base_filename}.png", 'wb') as f:
            f.write(response.content)
        print(f"  ✅ Saved: {base_filename}.png")
    except Exception as e:
        print(f"  ❌ Error (landscape): {e}")
    
    time.sleep(5)  # Be nice to the free API
    return True

# Get book title for cover page
book_title = get_book_title()

prompts = json.load(open("image_prompts.json"))
os.makedirs("images", exist_ok=True)

# Total images: cover + story pages + end page
total_images = len(prompts) + 2

print(f"\nGenerating {total_images} images using Pollinations.ai (FREE)")
print(f"Book Title: {book_title}")
print("=" * 60)

# Generate cover page (page 00)
print(f"Generating cover page (1/{total_images}): {book_title[:50]}...")
cover_prompt = f"A beautiful children's book cover illustration featuring the title '{book_title}', whimsical fantasy scene with a cute dragon, magical atmosphere, enchanting, storybook style, with decorative border"
generate_image(cover_prompt, "images/page_00_cover.png")

# Generate story pages
for i, prompt in enumerate(prompts):
    print(f"Generating story page {i+1} ({i+2}/{total_images}): {prompt[:50]}...")
    generate_image(prompt, f"images/page_{i+1:02d}.png")

# Generate end page (thank you)
print(f"Generating end page ({total_images}/{total_images}): Thank You...")
end_prompt = f"A heartwarming children's book ending page with 'Thank You for Reading!' text, cute dragon waving goodbye, magical sparkles, warm golden sunset colors, storybook style, decorative border, happy ending atmosphere"
generate_image(end_prompt, f"images/page_{len(prompts)+1:02d}_end.png")

print("\n✅ Image generation complete!")