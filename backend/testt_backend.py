import requests

def test_analyze():
    url = "http://127.0.0.1:8000/analyze"
    
    # We added user_id and session_id to match your DetectRequest model
    payload = {
        "user_id": "student_01",
        "session_id": "session_abc",
        "content": "while True: print('hello')",
        "metadata": {}
    }
    
    print("Testing Backend Analysis...")
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            print("AI Result:")
            import json
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ FAILED! Status Code: {response.status_code}")
            print(f"Error Detail: {response.text}")
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    test_analyze()