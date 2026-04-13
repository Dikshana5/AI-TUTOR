from adaptive_feedback.engine import _get_supabase_client

user_id = "13669de4-fde2-4905-9429-22c7badcda57"

client = _get_supabase_client()

# Try to find the user in profiles table
try:
    resp = client.table("profiles").select("*").eq("id", user_id).execute()
    users = getattr(resp, "data", []) or []
    
    if users:
        user = users[0]
        print("Found user in profiles table:")
        print(f"  ID: {user.get('id')}")
        print(f"  Username: {user.get('username')}")
        print(f"  Email: {user.get('email')}")
        print(f"  Is Active: {user.get('is_active')}")
    else:
        print("User not found in profiles table with that ID")
        print("\nSearching all profiles to see what exists...")
        resp_all = client.table("profiles").select("id, username, email").execute()
        all_users = getattr(resp_all, "data", []) or []
        for u in all_users:
            print(f"  - {u.get('id')}: {u.get('username')} ({u.get('email')})")
except Exception as e:
    print(f"Error: {e}")
