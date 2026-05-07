import os
import inspect
from supabase import create_client, Client, ClientOptions

print(f"Checking Supabase Client initialization...")

try:
    sig = inspect.signature(Client.__init__)
    print(f"Client.__init__ signature: {sig}")
except Exception as e:
    print(f"Could not get signature: {e}")

try:
    print("Attempting create_client...")
    # Use dummy values
    url = "https://example.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4YW1wbGUiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYyMDAwMDAwMCwiZXhwIjoxOTM1NTc2MDAwfQ.ExampleSignature"
    
    client = create_client(url, key)
    print("create_client success!")
except TypeError as te:
    print(f"TypeError caught: {te}")
except Exception as e:
    print(f"Other error caught: {e}")

print("\nAttempting Client() constructor directly...")
try:
    client = Client(url, key)
    print("Client() success!")
except TypeError as te:
    print(f"TypeError caught: {te}")
except Exception as e:
    print(f"Other error caught: {e}")
