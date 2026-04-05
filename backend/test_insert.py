from datetime import datetime, timedelta
from adaptive_feedback.engine import _get_supabase_client

client = _get_supabase_client()

user_id = "13669de4-fde2-4905-9429-22c7badcda57"

# Insert some test activities
activities = [
    {
        "user_id": user_id,
        "session_id": "test-session-1",
        "language": "python",
        "content": "print('hello')",
        "result": {"status": "success", "error_types": []},
        "created_at": (datetime.now() - timedelta(days=5)).isoformat()
    },
    {
        "user_id": user_id,
        "session_id": "test-session-2",
        "language": "python",
        "content": "def func(): pass",
        "result": {"status": "success", "error_types": []},
        "created_at": (datetime.now() - timedelta(days=3)).isoformat()
    },
    {
        "user_id": user_id,
        "session_id": "test-session-3",
        "language": "python",
        "content": "x = 1",
        "result": {"status": "success", "error_types": []},
        "created_at": (datetime.now() - timedelta(days=1)).isoformat()
    },
    {
        "user_id": user_id,
        "session_id": "test-session-4",
        "language": "python",
        "content": "for i in range(10): print(i)",
        "result": {"status": "success", "error_types": []},
        "created_at": datetime.now().isoformat()
    }
]

for activity in activities:
    client.table("user_activities").insert(activity).execute()

print("Test activities inserted")