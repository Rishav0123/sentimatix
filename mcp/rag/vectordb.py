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

from server.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, VECTOR_DIMENSION

logger = logging.getLogger(__name__)


class VectorDB:
    """Vector database operations for semantic search"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.table_name = "news_embeddings"
    
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
            return []
    
    def check_exists(self, news_id: str) -> bool:
        """Check if embedding already exists for a news article"""
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
                "vector_dimension": VECTOR_DIMENSION
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}


# Global instance
_vector_db = None

def get_vector_db() -> VectorDB:
    """Get or create vector database instance"""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDB()
    return _vector_db
