
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("d:/sentimatix/apps/api/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    # Try to find a user with a non-null authentication_key
    response = supabase.table('users').select('email, authentication_key').not_.is_('authentication_key', 'null').limit(5).execute()
    if response.data:
        print("Found users with API keys:")
        for user in response.data:
            print(f"Email: {user['email']} | Key: {user['authentication_key']}")
    else:
        print("No users found with authentication keys.")
except Exception as e:
    print(f"Error querying Supabase: {e}")
