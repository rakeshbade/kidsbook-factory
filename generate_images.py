# generate_images.py
from google import genai
from google.genai import types
import json, os, time

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

prompts = json.load(open("image_prompts.json"))
os.makedirs("images", exist_ok=True)

for i, prompt in enumerate(prompts):
    print(f"Generating image {i+1}/{len(prompts)}")
    try:
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=prompt + ", cartoon style, for children's book, colorful, high quality",
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1"
            )
        )
        
        for generated_image in response.generated_images:
            img_bytes = generated_image.image.image_bytes
            with open(f"images/page_{i+1:02d}.png", "wb") as f:
                f.write(img_bytes)
        
        print(f"  ✅ Image {i+1} saved")
        time.sleep(2)
        
    except Exception as e:
        print(f"  ❌ Error generating image {i+1}: {e}")
        if "billed users" in str(e):
            print("\n⚠️  Imagen API requires a billing account.")
            print("Please enable billing at: https://console.cloud.google.com/billing")
            break