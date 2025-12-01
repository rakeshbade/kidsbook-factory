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

# Use Hugging Face Inference API (FREE)
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))

# Get the best text-to-image model dynamically
model_id = get_best_text_to_image_model()

prompts = json.load(open("image_prompts.json"))
os.makedirs("images", exist_ok=True)

print(f"\nGenerating {len(prompts)} images using {model_id}")
print("=" * 60)

for i, prompt in enumerate(prompts):
    print(f"Generating image {i+1}/{len(prompts)}: {prompt[:50]}...")
    try:
        # Use the dynamically selected best model
        image = client.text_to_image(
            prompt=prompt + ", cartoon style, for children's book, colorful, vibrant, high quality",
            model=model_id
        )
        
        image.save(f"images/page_{i+1:02d}.png")
        print(f"  ✅ Image {i+1} saved")
        
        # Be nice to the free tier
        time.sleep(15)
        
    except Exception as e:
        print(f"  ❌ Error generating image {i+1}: {e}")
        if "429" in str(e) or "rate limit" in str(e).lower():
            print("\n⚠️  Rate limit reached. Waiting 10 seconds...")
            time.sleep(10)
        else:
            print(f"  Continuing with next image...")

print("\n✅ Image generation complete!")