import json
import os
import time
import sys
from groq import Groq
from dotenv import load_dotenv

# --- 1. SETUP & PATHS ---
load_dotenv()
# Keep your key name as per your .env
client = Groq(api_key=os.environ.get("OPENAI_API_KEY")) 
MODEL_ID = "llama-3.3-70b-versatile"

# Ensure Python can see the adaptive_feedback folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

PROBLEMS_PATH = "adaptive_feedback/feedengine/problems.json"
MISCONCEPTIONS_PATH = "adaptive_feedback/feedengine/misconceptions.json"

# This remains your "Seed" curriculum for the first run
CURRICULUM = {
    "Python": ["Decorators & Generators", "Data Analysis with Pandas Basics"],
    "Java": ["Object-Oriented Design Patterns", "Multi-threading & Concurrency"],
    "C++": ["Manual Memory Management (Pointers)", "STL Containers (Vectors/Maps)"],
    "JavaScript": ["Asynchronous Programming (Promises/Async-Await)", "DOM Manipulation"]
}

# --- 2. GENERATION LOGIC ---

def generate_misconceptions():
    """Generates the library of common mistakes."""
    print("🧠 Generating professional multi-language misconceptions...")
    prompt = """
    Generate a JSON list of 20 common programming misconceptions across Python, Java, C++, and JavaScript.
    Include: 'title', 'description', 'language', and 'fix'.
    Format: {"misconceptions": [{"title": "...", "description": "...", "language": "...", "fix": "..."}]}
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_ID,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content).get("misconceptions", [])
        
        os.makedirs(os.path.dirname(MISCONCEPTIONS_PATH), exist_ok=True)
        with open(MISCONCEPTIONS_PATH, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Misconceptions saved.")
        return data
    except Exception as e:
        print(f"❌ Misconception Error: {e}")
        return []

def generate_problems_for_lang(language, topic):
    """Generates problems and RETURNS them for JIT support."""
    print(f"🚀 JIT Generation: {language} | Topic: {topic}...")
    prompt = f"""
    Generate a JSON list of 10 diverse programming problems for {language} on the topic: {topic}.
    Format: {{"problems": [{{"id": "...", "title": "...", "description": "...", "difficulty": "...", "topic": "...", "language": "{language}"}}]}}
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_ID,
            response_format={"type": "json_object"}
        )
        raw_data = json.loads(response.choices[0].message.content)
        new_problems = raw_data.get("problems", [])

        # Update the local JSON file so the library grows permanently
        all_problems = []
        if os.path.exists(PROBLEMS_PATH):
            with open(PROBLEMS_PATH, "r") as f:
                try:
                    existing = json.load(f)
                    all_problems = existing if isinstance(existing, list) else existing.get("problems", [])
                except: all_problems = []

        all_problems.extend(new_problems)
        
        with open(PROBLEMS_PATH, "w") as f:
            json.dump(all_problems, f, indent=4)
            
        print(f"✅ Library updated. Added {len(new_problems)} problems.")
        return new_problems # Return specifically the new ones for the UI to use immediately

    except Exception as e:
        print(f"❌ Generation Error: {e}")
        return []

# --- 3. THE "SEEDER" PIPELINE ---
# This only runs if YOU manually run 'python generate_content.py'
if __name__ == "__main__":
    print("🛠️ Starting Manual Seed Process...")
    
    # 1. Misconceptions
    generate_misconceptions()
    
    # 2. Seed Curriculum
    for lang, topics in CURRICULUM.items():
        for topic in topics:
            generate_problems_for_lang(lang, topic)
            time.sleep(5) # Shorter sleep for Groq

    # 3. Final Indexing
    try:
        from adaptive_feedback.engine import refresh_vector_brain
        refresh_vector_brain()
        print("✨ Seeding Complete. FAISS Brain is ready.")
    except ImportError:
        print("⚠️ Warning: engine.py not found.")