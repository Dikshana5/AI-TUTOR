import requests
import json

# The URL of your running FastAPI server
URL = "http://127.0.0.1:8000/analyze"

# This is a sample student submission with a "Logic Error" (Infinite Loop)
payload = {
    "user_id": "student_01",
    "session_id": "test_session",
    "content": "while True: print('Hello')", # Bug: No break statement
    "content_type": "code",
    "language": "python"
}

print("--- Sending code to AI Tutor ---")
response = requests.post(URL, json=payload)

if response.status_code == 200:
    data = response.json()
    print("AI Analysis Result:")
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)