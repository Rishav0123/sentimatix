"""
MCP Server - Model Context Protocol Server for Stockify

This server exposes tools that LLMs can call to get stock data, news, sentiment, and RAG evidence.
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import config first
from server.config import (
    MCP_SERVER_HOST,
    MCP_SERVER_PORT,
    MCP_API_KEY,
    LOG_LEVEL,
    LOG_DIR,
    validate_config
)

# Import all tool functions
from server.tools.stock_tools import (
    get_stock_summary,
    get_historical_prices,
    STOCK_TOOLS_SCHEMA
)
from server.tools.news_tools import (
    get_news_sentiment,
    get_sentiment_aggregate,
    NEWS_TOOLS_SCHEMA
)
from server.tools.rag_tools import (
    get_rag_evidence,
    get_rag_stats,
    RAG_TOOLS_SCHEMA
)
from server.tools.correlation import (
    calculate_correlation,
    calculate_sentiment_price_correlation,
    CORRELATION_TOOLS_SCHEMA
)
from server.tools.orchestrator import (
    explain_price_change,
    ORCHESTRATOR_TOOLS_SCHEMA
)

# Setup logging
log_dir = Path(LOG_DIR)
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"mcp_server_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Validate configuration on startup
try:
    validate_config()
    logger.info("✅ Configuration validated successfully")
except ValueError as e:
    logger.error(f"❌ Configuration error: {e}")
    raise

# Create FastAPI app
app = FastAPI(
    title="Stockify MCP Server",
    description="Model Context Protocol Server for Stock Analysis with RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolResponse(BaseModel):
    success: bool
    result: Any
    error: Optional[str] = None
    timestamp: str


# Authentication dependency
def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key from request header"""
    if not x_api_key or x_api_key != MCP_API_KEY:
        logger.warning(f"Unauthorized access attempt with key: {x_api_key[:10] if x_api_key else 'None'}...")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - server info"""
    return {
        "service": "Stockify MCP Server",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "call": "/call",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test RAG system
        rag_stats = get_rag_stats()
        rag_ok = "error" not in rag_stats
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "api_server": "ok",
                "rag_system": "ok" if rag_ok else "error",
                "vector_db": rag_stats if rag_ok else "error"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/tools")
async def list_tools():
    """List all available tools with schemas"""
    all_tools = (
        ORCHESTRATOR_TOOLS_SCHEMA +
        STOCK_TOOLS_SCHEMA +
        NEWS_TOOLS_SCHEMA +
        RAG_TOOLS_SCHEMA +
        CORRELATION_TOOLS_SCHEMA
    )
    
    return {
        "tools": all_tools,
        "count": len(all_tools),
        "categories": {
            "orchestrator": 1,
            "stock_data": 2,
            "news_sentiment": 2,
            "rag": 2,
            "correlation": 2
        }
    }


@app.post("/call", response_model=ToolResponse)
async def call_tool(
    tool_call: ToolCall,
    api_key: str = Depends(verify_api_key)
):
    """
    Call a tool by name with arguments.
    
    This is the main endpoint that LLMs use to invoke tools.
    """
    try:
        tool_name = tool_call.name
        args = tool_call.arguments
        
        logger.info(f"Tool call: {tool_name} with args: {args}")
        
        # Route to appropriate tool function
        result = None
        
        # Orchestrator tools
        if tool_name == "explain_price_change":
            result = await explain_price_change(**args)
        
        # Stock tools
        elif tool_name == "get_stock_summary":
            result = get_stock_summary(**args)
        elif tool_name == "get_historical_prices":
            result = get_historical_prices(**args)
        
        # News tools
        elif tool_name == "get_news_sentiment":
            result = get_news_sentiment(**args)
        elif tool_name == "get_sentiment_aggregate":
            result = get_sentiment_aggregate(**args)
        
        # RAG tools
        elif tool_name == "get_rag_evidence":
            result = get_rag_evidence(**args)
        elif tool_name == "get_rag_stats":
            result = get_rag_stats()
        
        # Correlation tools
        elif tool_name == "calculate_correlation":
            result = calculate_correlation(**args)
        elif tool_name == "calculate_sentiment_price_correlation":
            result = calculate_sentiment_price_correlation(**args)
        
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Check for errors in result
        if isinstance(result, dict) and "error" in result:
            logger.warning(f"Tool {tool_name} returned error: {result['error']}")
            return ToolResponse(
                success=False,
                result=None,
                error=result["error"],
                timestamp=datetime.now().isoformat()
            )
        
        logger.info(f"Tool {tool_name} executed successfully")
        return ToolResponse(
            success=True,
            result=result,
            timestamp=datetime.now().isoformat()
        )
        
    except TypeError as e:
        logger.error(f"Invalid arguments for tool {tool_call.name}: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid arguments: {str(e)}")
    except Exception as e:
        logger.error(f"Error executing tool {tool_call.name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    try:
        rag_stats = get_rag_stats()
        
        return {
            "server": {
                "uptime_start": "N/A",  # Track this if needed
                "total_tool_calls": "N/A",  # Implement counter if needed
                "active_connections": "N/A"
            },
            "rag_system": rag_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": str(e)}


# Run server
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"🚀 Starting Stockify MCP Server on {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    logger.info(f"📝 Logs: {log_file}")
    logger.info(f"📚 Documentation: http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/docs")
    
    uvicorn.run(
        app,
        host=MCP_SERVER_HOST,
        port=MCP_SERVER_PORT,
        log_level=LOG_LEVEL.lower()
    )
