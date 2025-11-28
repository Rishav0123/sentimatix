"""
Generate embeddings using OpenAI API
"""

import openai
from typing import List, Union
import logging

from server.config import OPENAI_API_KEY, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY


def generate_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """
    Generate embedding for a single text using OpenAI API.
    
    Args:
        text: Input text to embed
        model: OpenAI embedding model (default: text-embedding-3-small)
    
    Returns:
        List of floats representing the embedding vector (1536 dimensions)
    """
    try:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Truncate text if too long (max 8191 tokens for text-embedding-3-small)
        text = text[:30000]  # Approximate limit
        
        response = openai.embeddings.create(
            input=text,
            model=model
        )
        
        embedding = response.data[0].embedding
        
        logger.debug(f"Generated embedding of dimension {len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise


def generate_embeddings_batch(texts: List[str], model: str = EMBEDDING_MODEL) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in a batch.
    
    Args:
        texts: List of texts to embed
        model: OpenAI embedding model
    
    Returns:
        List of embedding vectors
    """
    try:
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [t[:30000] for t in texts if t and t.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        response = openai.embeddings.create(
            input=valid_texts,
            model=model
        )
        
        embeddings = [item.embedding for item in response.data]
        
        logger.info(f"Generated {len(embeddings)} embeddings in batch")
        return embeddings
        
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise


def prepare_text_for_embedding(
    title: str,
    content: str,
    summary: str = "",
    entities: List[str] = None
) -> str:
    """
    Prepare news article text for embedding.
    
    Combines title, summary, content, and entities into a single text optimized for retrieval.
    
    Args:
        title: Article headline
        content: Full article content
        summary: Optional summary/excerpt
        entities: Optional list of key entities (companies, products, people)
    
    Returns:
        Formatted text ready for embedding
    """
    parts = []
    
    if title:
        parts.append(f"Title: {title}")
    
    if summary:
        parts.append(f"Summary: {summary}")
    elif content:
        # Use first 500 chars of content as summary
        parts.append(f"Summary: {content[:500]}")
    
    if content:
        # Add full content (will be truncated in generate_embedding if needed)
        parts.append(f"Content: {content}")
    
    if entities:
        parts.append(f"Entities: {', '.join(entities)}")
    
    return "\n\n".join(parts)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
    
    Returns:
        Cosine similarity score (0-1)
    """
    try:
        import numpy as np
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0
