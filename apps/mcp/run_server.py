"""
Run script for MCP Server
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Now import and run the server
from server.main import app
import uvicorn

if __name__ == "__main__":
    from server.config import MCP_SERVER_HOST, MCP_SERVER_PORT
    
    print(f"Starting MCP Server on {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    uvicorn.run(
        app,
        host=MCP_SERVER_HOST,
        port=MCP_SERVER_PORT,
        log_level="info"
    )
