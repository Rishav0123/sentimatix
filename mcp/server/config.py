import os
from dotenv import load_dotenv

load_dotenv()

# Backend API Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api")
BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# MCP Server Configuration
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))
MCP_API_KEY = os.getenv("MCP_API_KEY", "dev-key-12345")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# RAG Configuration
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "1536"))
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "6"))
RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.7"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Caching Configuration
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Rate Limiting
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "100"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))

# Monitoring
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
LOG_DIR = os.getenv("LOG_DIR", "logs")
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"

# Validation
def validate_config():
    """
    Validate required configuration with enhanced service key validation.
    
    Returns:
        bool: True if all required config is valid, False if RAG should be disabled
        
    Raises:
        ValueError: If critical configuration is missing or invalid
    """
    # Check required base configuration
    required = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "OPENAI_API_KEY": OPENAI_API_KEY,
    }
    
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    # Enhanced service key validation for RAG functionality
    if not SUPABASE_SERVICE_KEY:
        import warnings
        warnings.warn(
            "SUPABASE_SERVICE_KEY not configured - RAG system will be disabled. "
            "To enable RAG functionality, set SUPABASE_SERVICE_KEY in your .env file.",
            UserWarning
        )
        return False
    
    # Check for placeholder service key
    if "placeholder" in SUPABASE_SERVICE_KEY.lower() or "example" in SUPABASE_SERVICE_KEY.lower():
        import warnings
        warnings.warn(
            "SUPABASE_SERVICE_KEY appears to be a placeholder value - RAG system will be disabled. "
            "Please replace with your actual Supabase service key.",
            UserWarning
        )
        return False
    
    # Validate service key format
    if not validate_service_key(SUPABASE_SERVICE_KEY):
        raise ValueError(
            "SUPABASE_SERVICE_KEY is invalid. Service key should be a JWT token with format 'eyJ...'. "
            "Please check your Supabase project settings for the correct service key."
        )
    
    # Validate service key role (should be service_role for admin operations)
    try:
        import base64
        import json
        
        # Decode JWT payload (second part)
        parts = SUPABASE_SERVICE_KEY.split('.')
        if len(parts) >= 2:
            # Add padding if needed for base64 decoding
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded)
            
            if payload_data.get('role') != 'service_role':
                raise ValueError(
                    f"SUPABASE_SERVICE_KEY has role '{payload_data.get('role')}' but 'service_role' is required "
                    "for RAG system operations. Please use the service key, not the anon key."
                )
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # If we can't decode the JWT, still allow it but warn
        import warnings
        warnings.warn(
            f"Could not validate service key role: {e}. Proceeding with caution.",
            UserWarning
        )
    
    return True


def validate_service_key(service_key: str) -> bool:
    """
    Validate Supabase service key format and basic structure.
    
    Args:
        service_key: The service key to validate
        
    Returns:
        True if key appears valid, False otherwise
    """
    if not service_key:
        return False
    
    # Check for placeholder values
    if "placeholder" in service_key.lower() or "example" in service_key.lower():
        return False
    
    # JWT tokens should start with 'eyJ' (base64 encoded JSON header)
    if not service_key.startswith('eyJ'):
        return False
    
    # JWT should have 3 parts separated by dots
    parts = service_key.split('.')
    if len(parts) != 3:
        return False
    
    # Each part should be non-empty
    if not all(part for part in parts):
        return False
    
    # Validate that each part is valid base64
    try:
        import base64
        for part in parts[:2]:  # Header and payload should be valid base64
            # Add padding if needed
            padded = part + '=' * (4 - len(part) % 4)
            base64.b64decode(padded)
    except Exception:
        return False
    
    return True


def get_config_status() -> dict:
    """
    Get current configuration status for monitoring and debugging.
    
    Returns:
        dict: Configuration status information
    """
    status = {
        "supabase_url_configured": bool(SUPABASE_URL),
        "supabase_key_configured": bool(SUPABASE_KEY),
        "supabase_service_key_configured": bool(SUPABASE_SERVICE_KEY),
        "openai_api_key_configured": bool(OPENAI_API_KEY),
        "rag_enabled": False,
        "config_errors": []
    }
    
    try:
        status["rag_enabled"] = validate_config()
    except ValueError as e:
        status["config_errors"].append(str(e))
    
    # Check service key validity if present
    if SUPABASE_SERVICE_KEY:
        status["service_key_valid"] = validate_service_key(SUPABASE_SERVICE_KEY)
        if "placeholder" in SUPABASE_SERVICE_KEY.lower() or "example" in SUPABASE_SERVICE_KEY.lower():
            status["config_errors"].append("Service key appears to be a placeholder")
    else:
        status["service_key_valid"] = False
    
    return status

if __name__ == "__main__":
    try:
        validate_config()
        print("✅ Configuration validated successfully")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
