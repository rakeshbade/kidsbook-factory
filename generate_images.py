# generate_images.py
"""Generate children's book illustrations using Pollinations.ai."""

import json
import os
import time
from urllib.parse import quote as url_quote

import requests

from resize_images import resize_image
from variables import IMAGE_GEN_WIDTH, IMAGE_GEN_HEIGHT

# API configuration
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"
REQUEST_TIMEOUT = 120
DEFAULT_MAX_RETRIES = 3
INTER_REQUEST_DELAY = 2
POST_GENERATION_DELAY = 3

# Image generation settings
IMAGE_STYLE_SUFFIX = (
    ", cartoon style for children's book, colorful, vibrant, high quality"
)
COVER_STYLE_SUFFIX = (
    ", stictly no title or text, cartoon style for children's book, colorful, vibrant, high quality"
)

REQUEST_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )
}


def get_book_title():
    """Extract the book title from story.json (first page's story field)."""
    with open("story.json", "r", encoding="utf-8") as f:
        story_data = json.load(f)
    if story_data:
        return story_data[0].get("story", "")
    return ""


def _build_image_url(prompt, width, height):
    """Build the Pollinations.ai image generation URL."""
    encoded_prompt = url_quote(prompt)
    return (f"{POLLINATIONS_BASE_URL}/{encoded_prompt}"
            f"?width={width}&height={height}&nologo=true")


def _download_image(url, filepath, orientation, attempt, max_retries):
    """Download an image from URL and save to filepath.
    
    Returns True on success, False on failure.
    """
    try:
        print(f"    Generating {orientation}... "
              f"(attempt {attempt}/{max_retries})")
        response = requests.get(
            url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✅ Saved: {filepath}")
        resize_image(filepath)
        return True
    except requests.RequestException as e:
        print(f"  ⚠️ Attempt {attempt} failed ({orientation}): {e}")
        return False


def _generate_single_image(prompt, filepath, width, height, orientation,
                           max_retries):
    """Generate a single image with retry logic."""
    url = _build_image_url(prompt + IMAGE_STYLE_SUFFIX, width, height)
    
    for attempt in range(1, max_retries + 1):
        if _download_image(url, filepath, orientation, attempt, max_retries):
            return True
        
        if attempt < max_retries:
            wait_time = attempt * 5
            print(f"    Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    print(f"  ❌ All {max_retries} attempts failed for {orientation}")
    return False


def generate_image(prompt, filename, max_retries=DEFAULT_MAX_RETRIES):
    """Generate two images using Pollinations.ai (FREE, no API key needed).
    
    Generates:
    1. Portrait (background) - saved as {filename}_bg.png
    2. Landscape (main) - saved as {filename}.png
    
    Both images are resized after saving.
    """
    base_filename = filename.replace('.png', '')
    
    # Generate portrait background image
    portrait_file = f"{base_filename}_bg.png"
    _generate_single_image(
        prompt, portrait_file,
        IMAGE_GEN_WIDTH, IMAGE_GEN_HEIGHT,
        f"portrait ({IMAGE_GEN_WIDTH}x{IMAGE_GEN_HEIGHT})",
        max_retries
    )
    
    time.sleep(INTER_REQUEST_DELAY)
    
    # Generate landscape main image
    landscape_file = f"{base_filename}.png"
    _generate_single_image(
        prompt, landscape_file,
        IMAGE_GEN_HEIGHT, IMAGE_GEN_WIDTH,
        f"landscape ({IMAGE_GEN_HEIGHT}x{IMAGE_GEN_WIDTH})",
        max_retries
    )
    
    time.sleep(POST_GENERATION_DELAY)
    return True


def generate_cover_page(first_prompt, output_dir):
    """Generate the cover page illustration."""
    cover_prompt = first_prompt + COVER_STYLE_SUFFIX
    generate_image(cover_prompt, f"{output_dir}/page_00_cover.png")


def generate_story_pages(prompts, output_dir, total_images):
    """Generate illustrations for all story pages."""
    for i, prompt in enumerate(prompts):
        page_num = i + 1
        progress = i + 2  # +1 for cover, +1 for 1-based index
        print(f"Generating story page {page_num} ({progress}/{total_images}): "
              f"{prompt[:50]}...")
        generate_image(prompt, f"{output_dir}/page_{page_num:02d}.png")


def generate_end_page(page_number, output_dir, total_images):
    """Generate the end/thank you page illustration."""
    print(f"Generating end page ({total_images}/{total_images}): Thank You...")
    end_prompt = (
        "A heartwarming children's book ending page with "
        "'Thank You for Reading!' text, bright and cheerful colors"
    )
    generate_image(end_prompt, f"{output_dir}/page_{page_number:02d}_end.png")


def main():
    """Generate all book images."""
    book_title = get_book_title()
    
    with open("image_prompts.json", "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    output_dir = "images"
    os.makedirs(output_dir, exist_ok=True)
    
    total_images = len(prompts) + 2  # cover + story pages + end page
    
    print(f"\nGenerating {total_images} images using Pollinations.ai (FREE)")
    print(f"Book Title: {book_title}")
    print("=" * 60)
    
    # Generate cover page
    if not prompts:
        raise ValueError("No image prompts found.")
    first_prompt = prompts[0]
    generate_cover_page(first_prompt, output_dir)
    
    # Generate story pages
    generate_story_pages(prompts, output_dir, total_images)
    
    # Generate end page
    end_page_number = len(prompts) + 1
    generate_end_page(end_page_number, output_dir, total_images)
    
    print("\n✅ Image generation complete!")


if __name__ == "__main__":
    main()
