from groq import Groq
import os
import json
import uuid

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_problem_with_groq(concept, difficulty, language):
    prompt = f"""
Generate ONE programming challenge.

Language: {language}
Difficulty: {difficulty}
Concept: {concept}

Return ONLY valid JSON in this exact format:
{{
  "id": "GROQ-{uuid.uuid4().hex[:6]}",
  "title": "...",
  "description": "...",
  "difficulty": "{difficulty}",
  "topic": "{concept}",
  "language": "{language}"
}}
"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return json.loads(response.choices[0].message.content)
