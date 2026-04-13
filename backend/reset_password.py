from adaptive_feedback.engine import _get_supabase_client
import bcrypt

user_id = "13669de4-fde2-4905-9429-22c7badcda57"
new_password = "Test123"

client = _get_supabase_client()

# Hash the password using bcrypt directly
try:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
    
    # Update the password in profiles table
    resp = client.table("profiles").update(
        {"hashed_password": hashed_password}
    ).eq("id", user_id).execute()
    
    print("✓ Password reset successfully!")
    print(f"\nLogin Credentials:")
    print(f"  Username: aishwarya")
    print(f"  Email: aishu072006@gmail.com")
    print(f"  Password: {new_password}")
    print(f"\nYou can now login with these credentials to take your screenshot.")
except Exception as e:
    print(f"Error resetting password: {e}")
