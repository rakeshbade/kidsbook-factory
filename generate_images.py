# generate_images.py
import google.generativeai as genai, json, os, time
from PIL import Image
import requests

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.0-pro')

prompts = json.load(open("image_prompts.json"))
os.makedirs("images", exist_ok=True)

for i, prompt in enumerate(prompts):
    print(f"Generating image {i+1}/20")
    response = model.generate_content(
        [prompt + ", cartoon style, for children's book, 8k, perfect"],
        generation_config={"response_mime_type": "image/png"}
    )
    response.resolve()
    img_data = response.candidates[0].content.parts[0].inline_data.data
    with open(f"images/page_{i+1:02d}.png", "wb") as f:
        f.write(img_data)
    time.sleep(2)  # be nice to free tier