# generate_images.py
from huggingface_hub import InferenceClient
import json, os, time

# Use Hugging Face Inference API (FREE)
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))

prompts = json.load(open("image_prompts.json"))
os.makedirs("images", exist_ok=True)

print(f"Generating {len(prompts)} images using Hugging Face FLUX.1-schnell (FREE)")
print("=" * 60)

for i, prompt in enumerate(prompts):
    print(f"Generating image {i+1}/{len(prompts)}: {prompt[:50]}...")
    try:
        # Use FLUX.1-schnell - fast and free model optimized for speed
        image = client.text_to_image(
            prompt=prompt + ", cartoon style, for children's book, colorful, vibrant, high quality",
            model="black-forest-labs/FLUX.1-schnell"
        )
        
        image.save(f"images/page_{i+1:02d}.png")
        print(f"  ✅ Image {i+1} saved")
        
        # Be nice to the free tier
        time.sleep(2)
        
    except Exception as e:
        print(f"  ❌ Error generating image {i+1}: {e}")
        if "429" in str(e) or "rate limit" in str(e).lower():
            print("\n⚠️  Rate limit reached. Waiting 10 seconds...")
            time.sleep(10)
        else:
            print(f"  Continuing with next image...")

print("\n✅ Image generation complete!")