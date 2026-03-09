import os
import json
import uuid
try:
    from groq import Groq
except Exception:
    Groq = None

_groq_api_key = os.getenv("GROQ_API_KEY")
if Groq is not None and _groq_api_key:
    try:
        client = Groq(api_key=_groq_api_key)
    except Exception:
        client = None
else:
    client = None

def generate_problem_with_groq(concept, difficulty, language):
    """Generate a problem using Groq when available, otherwise return a fallback."""
    if client is None:
        return {
            "id": f"GROQ-{uuid.uuid4().hex[:6]}",
            "title": f"Practice: {concept}",
            "description": f"Write a {language} program that exercises {concept}.",
            "difficulty": difficulty,
            "topic": concept,
            "language": language,
        }

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
        temperature=0.7,
    )

    return json.loads(response.choices[0].message.content)
