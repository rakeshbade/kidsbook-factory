# generate_images.py
import json, os, time, requests
from resize_images import resize_image

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

def generate_image(prompt, filename, max_retries=3):
    """Generate two images using Pollinations.ai (FREE, no API key needed).
    1. Portrait (1800x2700) - saved as {filename}.png
    2. Landscape (2700x1800) - saved as {filename}_bg.png
    Both images are sharpened by 25% after saving.
    Retries up to max_retries times on failure.
    """
    full_prompt = prompt + ", cartoon style, for children's book, colorful, vibrant, high quality"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Remove .png extension for base filename
    base_filename = filename.replace('.png', '')
    
    # Generate portrait image (1800x2700) - 6x9 inches
    portrait_file = f"{base_filename}_bg.png"
    for attempt in range(1, max_retries + 1):
        try:
            url_portrait = f"https://image.pollinations.ai/prompt/{requests.utils.quote(full_prompt)}?width=600&height=900&nologo=true"
            print(f"    Generating portrait (600x900)... (attempt {attempt}/{max_retries})")
            response = requests.get(url_portrait, headers=headers, timeout=120)
            response.raise_for_status()
            with open(portrait_file, 'wb') as f:
                f.write(response.content)
            print(f"  ✅ Saved: {portrait_file}")
            resize_image(portrait_file)  # Resize to print quality
            break
        except Exception as e:
            print(f"  ⚠️ Attempt {attempt} failed (portrait): {e}")
            if attempt < max_retries:
                wait_time = attempt * 5
                print(f"    Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"  ❌ All {max_retries} attempts failed for portrait")
    
    time.sleep(3)  # Brief pause between requests
    
    # Generate landscape image (900x600) - 3x2 inches
    landscape_file = f"{base_filename}.png"
    for attempt in range(1, max_retries + 1):
        try:
            url_landscape = f"https://image.pollinations.ai/prompt/{requests.utils.quote(full_prompt)}?width=900&height=600&nologo=true"
            print(f"    Generating landscape... (attempt {attempt}/{max_retries})")
            response = requests.get(url_landscape, headers=headers, timeout=120)
            response.raise_for_status()
            with open(landscape_file, 'wb') as f:
                f.write(response.content)
            print(f"  ✅ Saved: {landscape_file}")
            resize_image(landscape_file)  # Resize to print quality
            break
        except Exception as e:
            print(f"  ⚠️ Attempt {attempt} failed (landscape): {e}")
            if attempt < max_retries:
                wait_time = attempt * 5
                print(f"    Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"  ❌ All {max_retries} attempts failed for landscape")
    
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

# Generate cover page (page 00) - use first prompt as base for cover illustration
print(f"Generating cover page (1/{total_images}): {book_title[:50]}...")
# Use the first story prompt as inspiration but modify for cover layout
first_prompt = prompts[0] if prompts else "a cute dragon in a magical fantasy setting"
cover_prompt = f"{first_prompt}, children's book cover illustration style, leave the top third of the image mostly empty with soft gradient sky or clouds for title text placement, no text or letters in the image, decorative border"
generate_image(cover_prompt, "images/page_00_cover.png")

# Generate story pages
for i, prompt in enumerate(prompts):
    print(f"Generating story page {i+1} ({i+2}/{total_images}): {prompt[:50]}...")
    generate_image(prompt, f"images/page_{i+1:02d}.png")

# Generate end page (thank you)
print(f"Generating end page ({total_images}/{total_images}): Thank You...")
end_prompt = f"A heartwarming children's book ending page with 'Thank You for Reading!' text, bright and cheerful colors, cartoon style".format(book_title)
generate_image(end_prompt, f"images/page_{len(prompts)+1:02d}_end.png")

print("\n✅ Image generation complete!")