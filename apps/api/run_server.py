import os
import uvicorn
from server import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    # We use "server:app" string to enable reloading if needed, 
    # but more importantly to match standard uvicorn patterns.
    # Since we are running from the same directory, this should work 
    # if PYTHONPATH includes current dir or we run as python run_server.py
    uvicorn.run("server:app", host="0.0.0.0", port=port, log_level="info")
