#!/usr/bin/env python3
"""
Generate a children's storybook prompt based on movies released in the current week.
Uses Google Generative AI (Gemini) to create age-appropriate story concepts.
"""

import os
import json
from datetime import datetime, timedelta
import google.generativeai as genai

def get_current_week_dates():
    """Get the start and end dates of the current week."""
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week.strftime("%B %d, %Y"), end_of_week.strftime("%B %d, %Y")

def generate_story_prompt():
    """
    Use Gemini to find movies released this week and generate
    a children's storybook prompt based on the movie's theme.
    """
    # Configure the API
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    start_date, end_date = get_current_week_dates()
    today = datetime.now().strftime("%B %d, %Y")
    
    # First, ask Gemini about movies released this week
    movie_prompt = f"""
    Today is {today}. 
    
    Think about popular movies that were released around this date ({start_date} to {end_date}) 
    in recent years, or any notable movie releases happening now.
    
    Pick ONE family-friendly or popular movie and provide the following information in JSON format:
    {{
        "movie_name": "Name of the movie",
        "genre": "Primary genre (adventure, fantasy, comedy, action, etc.)",
        "protagonist_name": "Main character's name",
        "movie_theme": "Brief description of the movie's main theme",
        "release_info": "Brief note about when it was released"
    }}
    
    Choose a movie that has elements suitable for inspiring a children's story.
    Return ONLY the JSON, no other text.
    """
    
    movie_response = model.generate_content(movie_prompt)
    movie_text = movie_response.text.strip()
    
    # Clean up the response (remove markdown code blocks if present)
    if movie_text.startswith("```"):
        movie_text = movie_text.split("```")[1]
        if movie_text.startswith("json"):
            movie_text = movie_text[4:]
    movie_text = movie_text.strip()
    
    try:
        movie_info = json.loads(movie_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse movie information from Gemini response: {e}\nResponse was: {movie_text}")
    
    print(f"Selected movie: {movie_info.get('movie_name', 'Unknown')}")
    print(f"Genre: {movie_info.get('genre', 'Unknown')}")
    print(f"Protagonist: {movie_info.get('protagonist_name', 'Unknown')}")
    
    # Now generate a children's story prompt based on the movie
    story_prompt = f"""
    Based on the following movie information, create a children's storybook concept 
    for ages 4-8 years old:
    
    Movie: {movie_info.get('movie_name', 'Adventure Movie')}
    Genre: {movie_info.get('genre', 'adventure')}
    Protagonist Name: {movie_info.get('protagonist_name', 'Alex')}
    Theme: {movie_info.get('movie_theme', 'adventure and friendship')}
    
    Create a NEW, ORIGINAL children's story that:
    1. Uses the SAME protagonist name as the movie
    2. Follows a SIMILAR genre and theme (but age-appropriate for 4-8 year olds)
    3. Has a positive message about friendship, courage, kindness, or learning
    4. Is engaging with colorful, imaginative scenes perfect for illustration
    
    Provide your response in this exact format:
    
    TITLE: [A catchy, child-friendly title]
    
    STORY CONCEPT: [A 2-3 sentence description of the story]
    
    STORY PROMPT: [A detailed prompt that will be used to generate a 20-page illustrated children's book. 
    Include the main character, setting, plot points, and the lesson/moral of the story.]
    
    Make sure the content is 100% appropriate for young children (ages 4-8).
    """
    
    story_response = model.generate_content(story_prompt)
    story_text = story_response.text.strip()
    
    # Parse the response to extract title and story prompt
    lines = story_text.split('\n')
    title = ""
    story_concept = ""
    story_prompt_text = ""
    
    current_section = None
    for line in lines:
        line = line.strip()
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
            current_section = "title"
        elif line.startswith("STORY CONCEPT:"):
            story_concept = line.replace("STORY CONCEPT:", "").strip()
            current_section = "concept"
        elif line.startswith("STORY PROMPT:"):
            story_prompt_text = line.replace("STORY PROMPT:", "").strip()
            current_section = "prompt"
        elif current_section == "concept" and line:
            story_concept += " " + line
        elif current_section == "prompt" and line:
            story_prompt_text += " " + line
    
    # Create the final prompt.txt content
    prompt_content = f"""Title: {title}

Story prompt: {story_prompt_text}

Inspired by: {movie_info.get('movie_name', 'Unknown')} ({movie_info.get('genre', 'adventure')})
Target age group: 4-8 years old
Protagonist: {movie_info.get('protagonist_name', 'Alex')}

Story Concept: {story_concept}

Generate exactly 20 pages with one illustration prompt per page."""
    
    # Write to prompt.txt
    with open("prompt.txt", "w") as f:
        f.write(prompt_content)
    
    print("\n" + "="*50)
    print("Generated prompt.txt successfully!")
    print("="*50)
    print(f"\nTitle: {title}")
    print(f"\nStory Concept: {story_concept}")
    print(f"\nBased on: {movie_info.get('movie_name', 'Unknown')}")
    print("="*50)
    
    return prompt_content

def main():
    """Main entry point."""
    # Check for GitHub issue context (when running in GitHub Actions)
    github_event_path = os.environ.get("GITHUB_EVENT_PATH")
    
    if github_event_path and os.path.exists(github_event_path):
        # Running in GitHub Actions - check if issue has specific instructions
        with open(github_event_path) as f:
            payload = json.load(f)
        
        issue_title = payload.get("issue", {}).get("title", "")
        issue_body = payload.get("issue", {}).get("body", "")
        
        # If issue body contains "auto" or is empty, generate based on current movies
        if not issue_body or "auto" in issue_body.lower() or "movie" in issue_body.lower():
            print("Generating story prompt based on current movie releases...")
            generate_story_prompt()
        else:
            # Use the issue content directly (original behavior)
            print("Using issue content as story prompt...")
            with open("prompt.txt", "w") as f:
                f.write(f"Title: {issue_title}\n\n")
                f.write(f"Story prompt: {issue_body}\n")
                f.write("Generate exactly 20 pages with one illustration prompt per page.")
    else:
        # Running locally - generate based on current movies
        print("Running locally - generating story prompt based on current movie releases...")
        generate_story_prompt()

if __name__ == "__main__":
    main()
