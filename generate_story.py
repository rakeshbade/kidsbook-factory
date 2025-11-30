# generate_story.py
import google.generativeai as genai, os, json, re
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
prompt = open("prompt.txt").read() + "\n\nWrite a 20-page children's story. After each paragraph, write exactly one line starting with 'IMAGE: ' describing the illustration in extreme detail for Imagen 3."
response = model.generate_content(prompt)
text = response.text

with open("story.txt", "w") as f:
    f.write(text)

# Extract image prompts
image_prompts = re.findall(r"IMAGE: (.*)", text)
with open("image_prompts.json", "w") as f:
    json.dump(image_prompts, f)