import os, json, time
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# Define the structured curriculum requirements
curriculum_plan = {
    "Python": ["Basics & Variables", "Control Flow", "Data Structures"],
    "Java": ["OOP Fundamentals", "Collections Framework", "Exception Handling"],
    "C++": ["Pointers & References", "Memory Management", "STL Library"]
}

def generate_topic_problems(lang, topic):
    print(f"Generating 5 problems for {lang} - {topic}...")
    prompt = f"""
    Generate 5 distinct programming problems for {lang} on the topic of '{topic}'.
    Format the output as a JSON list of objects with these keys: 
    'language', 'topic', 'title', 'description', 'starter_code', 'difficulty', 'order_index'.
    Make problems progress from Easy to Hard.
    Return ONLY the raw JSON list.
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
    )
    
    res = json.loads(completion.choices[0].message.content)
    # Handle nested JSON response
    return res.get("problems", res) if isinstance(res, dict) else res

# Main Loop
all_curriculum_data = []
for lang, topics in curriculum_plan.items():
    for topic in topics:
        try:
            problems = generate_topic_problems(lang, topic)
            all_curriculum_data.extend(problems)
            time.sleep(1) # Avoid rate limits
        except Exception as e:
            print(f"Error on {lang} {topic}: {e}")

# Upload to Supabase
if all_curriculum_data:
    supabase.table("learning_path").insert(all_curriculum_data).execute()
    print(f"✅ Success! Inserted {len(all_curriculum_data)} problems into the 'learning_path' table.")
