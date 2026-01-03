"""
Vector Database Operations using Supabase pgvector

Setup required:
1. Enable pgvector extension in Supabase
2. Create news_embeddings table (see scripts/setup_vectordb.sql)
"""

from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import logging
import numpy as np
import time

from server.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, VECTOR_DIMENSION, validate_service_key
from server.monitoring import log_connection_operation

logger = logging.getLogger(__name__)


class VectorDB:
    """Vector database operations for semantic search"""
    
    def __init__(self, service_key: Optional[str] = None):
        """
        Initialize VectorDB with proper service key validation and connection testing.
        
        Args:
            service_key: Optional service key override. If not provided, uses config.
            
        Raises:
            ValueError: If required configuration is missing or invalid
            ConnectionError: If database connection fails after retries
        """
        # Use provided service key or fall back to config
        self.service_key = service_key or SUPABASE_SERVICE_KEY
        
        # Validate required configuration
        if not SUPABASE_URL:
            raise ValueError("SUPABASE_URL is required for vector database operations")
        
        if not self.service_key:
            raise ValueError(
                "SUPABASE_SERVICE_KEY is required for vector database operations. "
                "Please configure your service key in the .env file."
            )
        
        # Validate service key format
        if not validate_service_key(self.service_key):
            raise ValueError(
                "Invalid SUPABASE_SERVICE_KEY format. Service key should be a JWT token "
                "starting with 'eyJ' and have 3 parts separated by dots."
            )
        
        self.supabase_url = SUPABASE_URL
        self.table_name = "news_embeddings"
        self.client: Optional[Client] = None
        self.connection_tested = False
        
        # Initialize connection with retry logic
        self._initialize_connection()
    
    def _initialize_connection(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize Supabase client connection with retry logic.
        
        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay between retry attempts in seconds
            
        Raises:
            ConnectionError: If connection fails after all retries
        """
        last_error = None
        connection_start = time.time()
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Initializing vector database connection (attempt {attempt + 1}/{max_retries})")
                
                # Create Supabase client
                self.client = create_client(self.supabase_url, self.service_key)
                
                # Test connection by attempting a simple query
                self._test_connection()
                
                # Log successful connection
                log_connection_operation(
                    start_time=connection_start,
                    success=True
                )
                
                logger.info("Vector database connection initialized successfully")
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        # All retries failed - log the failure
        error_msg = f"Failed to initialize vector database connection after {max_retries} attempts. Last error: {last_error}"
        logger.error(error_msg)
        
        log_connection_operation(
            start_time=connection_start,
            success=False,
            error_message=str(last_error)
        )
        
        raise ConnectionError(error_msg)
    
    def _test_connection(self):
        """
        Test database connection by performing a simple query.
        
        Raises:
            Exception: If connection test fails
        """
        if not self.client:
            raise Exception("Client not initialized")
        
        try:
            # Test connection with a simple count query
            result = self.client.table(self.table_name).select("news_id", count="exact").limit(1).execute()
            
            # Check if we can access the table (even if empty)
            if hasattr(result, 'count') or result.data is not None:
                self.connection_tested = True
                logger.debug("Database connection test successful")
            else:
                raise Exception("Unexpected response from database")
                
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise Exception(f"Database connection test failed: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if database connection is active and tested.
        
        Returns:
            True if connection is active, False otherwise
        """
        return self.client is not None and self.connection_tested
    
    def reconnect(self):
        """
        Reconnect to the database with retry logic.
        
        Raises:
            ConnectionError: If reconnection fails
        """
        logger.info("Attempting to reconnect to vector database")
        reconnect_start = time.time()
        
        try:
            self.client = None
            self.connection_tested = False
            self._initialize_connection()
            
            log_connection_operation(
                start_time=reconnect_start,
                success=True
            )
            
        except Exception as e:
            log_connection_operation(
                start_time=reconnect_start,
                success=False,
                error_message=str(e)
            )
            raise
    
    def insert_embedding(
        self,
        news_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Insert a news article embedding into the vector database.
        
        Args:
            news_id: Unique ID of the news article
            embedding: Vector embedding (1536 dimensions for text-embedding-3-small)
            metadata: Additional metadata (symbol, published_at, title, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            logger.error("Vector database not connected - cannot insert embedding")
            return False
        
        try:
            # Validate embedding dimension
            if len(embedding) != VECTOR_DIMENSION:
                raise ValueError(f"Expected {VECTOR_DIMENSION} dimensions, got {len(embedding)}")
            
            record = {
                "news_id": news_id,
                "embedding": embedding,
                "symbol": metadata.get("symbol"),
                "title": metadata.get("title"),
                "published_at": metadata.get("published_at"),
                "sentiment": metadata.get("sentiment"),
                "sentiment_score": metadata.get("sentiment_score"),
                "source": metadata.get("source"),
                "url": metadata.get("url"),
                "content_preview": metadata.get("content_preview", "")[:500]  # First 500 chars
            }
            
            result = self.client.table(self.table_name).insert(record).execute()
            
            if result.data:
                logger.debug(f"Inserted embedding for news_id: {news_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error inserting embedding for {news_id}: {e}")
            # Try to reconnect on connection errors
            if "connection" in str(e).lower() or "network" in str(e).lower():
                try:
                    logger.info("Attempting to reconnect due to connection error")
                    self.reconnect()
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")
            return False
    
    def semantic_search(
        self,
        query_embedding: List[float],
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        top_k: int = 6,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search in the vector database.
        
        Args:
            query_embedding: Query vector (same dimension as stored embeddings)
            symbol: Filter by stock symbol (optional)
            start_date: Filter by published_at >= start_date (optional)
            end_date: Filter by published_at <= end_date (optional)
            top_k: Number of results to return
            min_similarity: Minimum cosine similarity threshold
        
        Returns:
            List of matching documents with similarity scores and metadata
        """
        if not self.is_connected():
            logger.error("Vector database not connected - cannot perform semantic search")
            return []
        
        try:
            # Use Supabase's RPC function for vector similarity search
            # This requires a custom PostgreSQL function (see setup_vectordb.sql)
            
            params = {
                "query_embedding": query_embedding,
                "match_threshold": min_similarity,
                "match_count": top_k
            }
            
            if symbol:
                params["filter_symbol"] = symbol
            if start_date:
                params["filter_start_date"] = start_date
            if end_date:
                params["filter_end_date"] = end_date
            
            # Call the RPC function
            result = self.client.rpc("match_news_embeddings", params).execute()
            
            if not result.data:
                logger.info(f"No semantic search results found for symbol={symbol}, top_k={top_k}")
                return []
            
            # Format results
            matches = []
            for row in result.data:
                matches.append({
                    "news_id": row.get("news_id"),
                    "title": row.get("title"),
                    "content_preview": row.get("content_preview"),
                    "published_at": row.get("published_at"),
                    "symbol": row.get("symbol"),
                    "sentiment": row.get("sentiment"),
                    "sentiment_score": row.get("sentiment_score"),
                    "source": row.get("source"),
                    "url": row.get("url"),
                    "similarity_score": round(row.get("similarity", 0), 3)
                })
            
            logger.info(f"Semantic search returned {len(matches)} results (symbol={symbol}, top_k={top_k})")
            return matches
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            # Try to reconnect on connection errors
            if "connection" in str(e).lower() or "network" in str(e).lower():
                try:
                    logger.info("Attempting to reconnect due to connection error")
                    self.reconnect()
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")
            return []
    
    def check_exists(self, news_id: str) -> bool:
        """Check if embedding already exists for a news article"""
        if not self.is_connected():
            logger.error("Vector database not connected - cannot check existence")
            return False
        
        try:
            result = self.client.table(self.table_name)\
                .select("news_id")\
                .eq("news_id", news_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking existence for {news_id}: {e}")
            return False
    
    def delete_embedding(self, news_id: str) -> bool:
        """Delete an embedding"""
        if not self.is_connected():
            logger.error("Vector database not connected - cannot delete embedding")
            return False
        
        try:
            result = self.client.table(self.table_name)\
                .delete()\
                .eq("news_id", news_id)\
                .execute()
            
            return result.data is not None
            
        except Exception as e:
            logger.error(f"Error deleting embedding for {news_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.is_connected():
            logger.error("Vector database not connected - cannot get stats")
            return {"error": "Database not connected"}
        
        try:
            # Count total embeddings
            count_result = self.client.table(self.table_name)\
                .select("news_id", count="exact")\
                .execute()
            
            total = count_result.count if hasattr(count_result, 'count') else 0
            
            # Get symbol distribution
            symbol_result = self.client.table(self.table_name)\
                .select("symbol")\
                .execute()
            
            symbols = [row.get("symbol") for row in symbol_result.data if row.get("symbol")]
            unique_symbols = len(set(symbols))
            
            return {
                "total_embeddings": total,
                "unique_symbols": unique_symbols,
                "table_name": self.table_name,
                "vector_dimension": VECTOR_DIMENSION,
                "connection_status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}


# Global instance
_vector_db = None

def get_vector_db() -> VectorDB:
    """
    Get or create vector database instance with enhanced error handling.
    
    Returns:
        VectorDB: Initialized vector database instance
        
    Raises:
        Exception: If vector database cannot be initialized and service key is missing
        ConnectionError: If database connection fails after retries
    """
    global _vector_db
    
    if _vector_db is None:
        try:
            logger.info("Initializing vector database instance")
            _vector_db = VectorDB()
            logger.info("Vector database initialized successfully")
            
        except ValueError as e:
            # Configuration errors - provide detailed guidance
            if "SUPABASE_SERVICE_KEY" in str(e):
                error_msg = (
                    "RAG system unavailable: SUPABASE_SERVICE_KEY not configured. "
                    "To enable RAG functionality:\n"
                    "1. Get your service key from Supabase project settings\n"
                    "2. Add SUPABASE_SERVICE_KEY=your_key_here to your .env file\n"
                    "3. Restart the MCP server\n"
                    f"Original error: {e}"
                )
                logger.warning(error_msg)
                raise Exception(error_msg)
            elif "Invalid SUPABASE_SERVICE_KEY" in str(e):
                error_msg = (
                    "RAG system unavailable: Invalid service key format. "
                    "Please check that your SUPABASE_SERVICE_KEY is a valid JWT token "
                    "from your Supabase project settings (should start with 'eyJ'). "
                    f"Original error: {e}"
                )
                logger.error(error_msg)
                raise Exception(error_msg)
            else:
                error_msg = f"RAG system configuration error: {e}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except ConnectionError as e:
            # Connection errors - provide troubleshooting steps
            error_msg = (
                "RAG system unavailable: Database connection failed. "
                "Please check:\n"
                "1. Your internet connection\n"
                "2. Supabase project is active and accessible\n"
                "3. Service key has correct permissions\n"
                "4. pgvector extension is enabled in your Supabase project\n"
                f"Connection error: {e}"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg)
            
        except Exception as e:
            # Unexpected errors
            error_msg = f"RAG system initialization failed with unexpected error: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    # Check if existing instance is still connected
    if not _vector_db.is_connected():
        logger.warning("Vector database connection lost, attempting to reconnect")
        try:
            _vector_db.reconnect()
            logger.info("Vector database reconnected successfully")
        except Exception as e:
            logger.error(f"Failed to reconnect vector database: {e}")
            # Reset global instance to force reinitialization on next call
            _vector_db = None
            raise ConnectionError(f"Vector database connection lost and reconnection failed: {e}")
    
    return _vector_db


def reset_vector_db():
    """
    Reset the global vector database instance.
    Useful for testing or when configuration changes.
    """
    global _vector_db
    if _vector_db:
        logger.info("Resetting vector database instance")
    _vector_db = None


def get_vector_db_status() -> Dict[str, Any]:
    """
    Get current vector database status for monitoring and debugging.
    
    Returns:
        Dict with connection status, configuration info, and any errors
    """
    global _vector_db
    
    status = {
        "instance_created": _vector_db is not None,
        "connected": False,
        "connection_tested": False,
        "service_key_configured": bool(SUPABASE_SERVICE_KEY),
        "supabase_url_configured": bool(SUPABASE_URL),
        "errors": []
    }
    
    if _vector_db:
        status["connected"] = _vector_db.is_connected()
        status["connection_tested"] = _vector_db.connection_tested
        
        # Try to get database stats
        try:
            stats = _vector_db.get_stats()
            if "error" not in stats:
                status["database_stats"] = stats
            else:
                status["errors"].append(f"Database stats error: {stats['error']}")
        except Exception as e:
            status["errors"].append(f"Failed to get database stats: {e}")
    
    # Check configuration issues
    if not SUPABASE_SERVICE_KEY:
        status["errors"].append("SUPABASE_SERVICE_KEY not configured")
    elif not validate_service_key(SUPABASE_SERVICE_KEY):
        status["errors"].append("SUPABASE_SERVICE_KEY format is invalid")
    
    if not SUPABASE_URL:
        status["errors"].append("SUPABASE_URL not configured")
    
    return status
