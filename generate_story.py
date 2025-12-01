# generate_story.py
import google.generativeai as genai
import os
import json

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

prompt = open("prompt.txt").read() + """

Write a 20-page children's story. Return the response as a JSON array with exactly 20 objects.
Each object must have:
- "page": the page number (1-20)
- "story": the story text for that page (2-3 sentences, appropriate for ages 4-8)
- "image": a detailed illustration prompt describing the scene in extreme detail for image generation

Return ONLY valid JSON, no other text. Example format:
[
  {"page": 1, "story": "Once upon a time...", "image": "A young girl standing in a magical forest with..."},
  {"page": 2, "story": "She discovered...", "image": "The girl holding a glowing crystal..."}
]
"""

response = model.generate_content(prompt)
text = response.text.strip()

# Clean up the response (remove markdown code blocks if present)
if text.startswith("```"):
    text = text.split("```")[1]
    if text.startswith("json"):
        text = text[4:]
text = text.strip()

# Parse JSON
try:
    story_data = json.loads(text)
except json.JSONDecodeError as e:
    raise ValueError(f"Failed to parse story JSON from Gemini response: {e}\nResponse was: {text[:500]}...")

# Save the full story JSON
with open("story.json", "w") as f:
    json.dump(story_data, f, indent=2)

# Also save story.txt for backward compatibility
with open("story.txt", "w") as f:
    for page in story_data:
        f.write(f"**Page {page['page']}**\n")
        f.write(f"{page['story']}\n")
        f.write(f"IMAGE: {page['image']}\n\n")

# Extract image prompts for backward compatibility
image_prompts = [page["image"] for page in story_data]
with open("image_prompts.json", "w") as f:
    json.dump(image_prompts, f, indent=2)

print(f"✅ Generated {len(story_data)} pages")
print(f"📄 Saved: story.json, story.txt, image_prompts.json")