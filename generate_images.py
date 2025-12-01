# generate_images.py
from huggingface_hub import InferenceClient, list_models
import json, os, time

def get_best_text_to_image_model():
    """Fetch the most downloaded/popular text-to-image model from Hugging Face."""
    try:
        models = list_models(
            filter="text-to-image",
            sort="downloads",
            direction=-1,
            limit=1
        )
        best_model = next(iter(models), None)
        if best_model:
            print(f"🔍 Found best model: {best_model.id} (downloads: {best_model.downloads:,})")
            return best_model.id
    except Exception as e:
        print(f"⚠️  Could not fetch best model: {e}")
    
    # Fallback to a known good model
    fallback = "black-forest-labs/FLUX.1-schnell"
    print(f"📌 Using fallback model: {fallback}")
    return fallback

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

def generate_image(client, model_id, prompt, filename, delay=15):
    """Generate a single image and save it."""
    try:
        image = client.text_to_image(
            prompt=prompt + ", cartoon style, for children's book, colorful, vibrant, high quality, size 600x900",
            model=model_id
        )
        image.save(filename)
        print(f"  ✅ Saved: {filename}")
        time.sleep(delay)
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        if "429" in str(e) or "rate limit" in str(e).lower():
            print("\n⚠️  Rate limit reached. Waiting 10 seconds...")
            time.sleep(10)
        return False

# Use Hugging Face Inference API (FREE)
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))

# Get the best text-to-image model dynamically
model_id = get_best_text_to_image_model()

# Get book title for cover page
book_title = get_book_title()

prompts = json.load(open("image_prompts.json"))
os.makedirs("images", exist_ok=True)

# Total images: cover + story pages + end page
total_images = len(prompts) + 2

print(f"\nGenerating {total_images} images using {model_id}")
print(f"Book Title: {book_title}")
print("=" * 60)

# Generate cover page (page 00)
print(f"Generating cover page (1/{total_images}): {book_title[:50]}...")
cover_prompt = f"A beautiful children's book cover illustration featuring the title '{book_title}', whimsical fantasy scene with a cute dragon, magical atmosphere, enchanting, storybook style, with decorative border"
generate_image(client, model_id, cover_prompt, "images/page_00_cover.png")

# Generate story pages
for i, prompt in enumerate(prompts):
    print(f"Generating story page {i+1} ({i+2}/{total_images}): {prompt[:50]}...")
    generate_image(client, model_id, prompt, f"images/page_{i+1:02d}.png")

# Generate end page (thank you)
print(f"Generating end page ({total_images}/{total_images}): Thank You...")
end_prompt = f"A heartwarming children's book ending page with 'Thank You for Reading!' text, cute dragon waving goodbye, magical sparkles, warm golden sunset colors, storybook style, decorative border, happy ending atmosphere"
generate_image(client, model_id, end_prompt, f"images/page_{len(prompts)+1:02d}_end.png")

print("\n✅ Image generation complete!")