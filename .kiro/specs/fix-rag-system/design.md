# Design Document: Fix RAG System

## Overview

This design addresses the RAG (Retrieval-Augmented Generation) system failure in the MCP server by properly configuring the Supabase service key and implementing robust error handling. The RAG system provides semantic search capabilities for historical news context, which is essential for comprehensive stock analysis.

Currently, the RAG component fails because the `SUPABASE_SERVICE_KEY` is commented out in the environment configuration, preventing access to the vector database. This design will restore full RAG functionality and ensure all 5/5 MCP components are operational.

## Architecture

### Current System State
```
MCP Server Components:
├── Stock Summary ✅ (Working)
├── News Sentiment ✅ (Working) 
├── Sentiment Aggregate ✅ (Working)
├── Correlation Analysis ✅ (Working)
└── RAG Evidence ❌ (Failing - Missing Service Key)
```

### Target System State
```
MCP Server Components:
├── Stock Summary ✅ (Working)
├── News Sentiment ✅ (Working)
├── Sentiment Aggregate ✅ (Working) 
├── Correlation Analysis ✅ (Working)
└── RAG Evidence ✅ (Working - Service Key Configured)
```

### RAG System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │───▶│   Orchestrator   │───▶│  RAG Evidence   │
│  (Frontend)     │    │                  │    │     Tool        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OpenAI API    │◀───│   Embeddings     │◀───│   Vector DB     │
│  (Embeddings)   │    │   Generator      │    │  (Supabase)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components and Interfaces

### 1. Configuration Manager
**Purpose:** Validate and manage Supabase credentials

**Interface:**
```python
class ConfigValidator:
    def validate_supabase_config() -> bool
    def get_service_key() -> str
    def log_config_status() -> None
```

**Implementation:**
- Check for `SUPABASE_SERVICE_KEY` in environment
- Validate key format and permissions
- Provide clear error messages for missing/invalid keys

### 2. Vector Database Connection
**Purpose:** Establish secure connection to Supabase pgvector

**Interface:**
```python
class VectorDB:
    def __init__(service_key: str)
    def test_connection() -> bool
    def semantic_search(query_embedding, filters) -> List[Dict]
```

**Implementation:**
- Use service key for elevated database permissions
- Implement connection pooling and retry logic
- Handle authentication errors gracefully

### 3. RAG Evidence Tool
**Purpose:** Perform semantic search and format results

**Interface:**
```python
def get_rag_evidence(
    symbol: str,
    start_date: str, 
    end_date: str,
    query_text: str,
    top_k: int = 6
) -> List[Dict[str, Any]]
```

**Implementation:**
- Generate embeddings for search queries
- Execute vector similarity search
- Format results with relevance scores and metadata

### 4. Error Handling System
**Purpose:** Graceful degradation when RAG unavailable

**Interface:**
```python
class RAGErrorHandler:
    def handle_connection_error() -> Dict
    def handle_search_timeout() -> Dict
    def log_rag_metrics() -> None
```

## Data Models

### RAG Evidence Response
```python
{
    "rank": int,
    "title": str,
    "summary": str,
    "url": str,
    "source": str,
    "published_at": str,
    "sentiment": str,
    "sentiment_score": float,
    "relevance_score": float,
    "raw_similarity": float,
    "match_quality": str  # "EXCELLENT", "HIGH", "GOOD", "MODERATE", "LOW"
}
```

### Configuration Model
```python
{
    "supabase_url": str,
    "supabase_key": str,
    "supabase_service_key": str,  # Required for RAG
    "openai_api_key": str,
    "vector_dimension": int,
    "rag_enabled": bool
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Service Key Validation
*For any* MCP server startup, if SUPABASE_SERVICE_KEY is provided, then the RAG system should initialize successfully and be marked as operational.
**Validates: Requirements 1.1, 1.2**

### Property 2: Semantic Search Functionality  
*For any* valid search query with configured service key, the RAG system should return relevant articles with similarity scores between 0.0 and 1.0.
**Validates: Requirements 2.1, 2.2**

### Property 3: Graceful Error Handling
*For any* RAG system failure, the MCP server should continue operating with other components and log appropriate error messages.
**Validates: Requirements 4.1, 4.2**

### Property 4: Configuration Validation
*For any* missing or invalid Supabase credentials, the system should detect the issue during startup and provide actionable error messages.
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 5: Search Result Quality
*For any* successful semantic search, returned articles should have non-null titles, sources, and relevance scores above the minimum threshold.
**Validates: Requirements 2.4, 2.5**

## Error Handling

### Configuration Errors
- **Missing Service Key:** Log warning, disable RAG, continue with 4/5 components
- **Invalid Service Key:** Log error with troubleshooting steps, disable RAG
- **Network Issues:** Retry with exponential backoff, fallback to graceful degradation

### Runtime Errors  
- **Database Connection Loss:** Cache last successful connection, retry on next request
- **Search Timeouts:** Return partial results if available, log performance metrics
- **Embedding Generation Failures:** Retry with simplified query, fallback to keyword search

### Monitoring and Alerting
- Track RAG system uptime and success rates
- Monitor search latency and result quality
- Alert on configuration issues or persistent failures

## Testing Strategy

### Unit Tests
- Configuration validation logic
- Vector database connection handling
- Error handling and fallback mechanisms
- Search result formatting and validation

### Integration Tests  
- End-to-end RAG system functionality
- Supabase service key authentication
- Semantic search with real embeddings
- Performance under various load conditions

### Property-Based Tests
- **Property 1 Test:** Generate random valid/invalid service keys, verify initialization behavior
- **Property 2 Test:** Generate random search queries, verify result format and scores
- **Property 3 Test:** Simulate various failure conditions, verify graceful degradation
- **Property 4 Test:** Test configuration validation with various credential combinations
- **Property 5 Test:** Verify search result quality across different query types

Each property test should run minimum 100 iterations and be tagged with:
**Feature: fix-rag-system, Property {number}: {property_text}**