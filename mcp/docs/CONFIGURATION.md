# MCP RAG System Configuration Guide

## Overview

This guide provides comprehensive configuration instructions for the MCP RAG system, including all required environment variables, service key setup, and troubleshooting for common configuration issues.

## Required Environment Variables

### Supabase Configuration

The RAG system requires the following Supabase environment variables:

#### SUPABASE_URL
- **Purpose**: Base URL for your Supabase project
- **Format**: `https://[project-id].supabase.co`
- **Example**: `SUPABASE_URL=https://uqvouptulubydignwtkv.supabase.co`
- **Required**: Yes
- **Used by**: All database operations, vector search

#### SUPABASE_KEY (Anon Key)
- **Purpose**: Public anonymous key for client-side operations
- **Format**: JWT token starting with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`
- **Permissions**: Limited read access, RLS policies apply
- **Required**: Yes
- **Used by**: Basic database queries, public API access

#### SUPABASE_SERVICE_KEY (Service Role Key)
- **Purpose**: Administrative key with elevated permissions for RAG operations
- **Format**: JWT token with `service_role` in payload
- **Permissions**: Full database access, bypasses RLS
- **Required**: Yes (Critical for RAG functionality)
- **Used by**: Vector database operations, embeddings storage, semantic search

**⚠️ IMPORTANT**: The RAG system will fail without a valid SUPABASE_SERVICE_KEY.

### OpenAI Configuration

#### OPENAI_API_KEY
- **Purpose**: API key for generating embeddings and LLM operations
- **Format**: `sk-proj-...` or `sk-...`
- **Required**: Yes
- **Used by**: Text embeddings generation, semantic search

### Backend API Configuration

#### BACKEND_API_URL
- **Purpose**: Base URL for the backend API providing stock and news data
- **Format**: `http://host:port/api`
- **Example**: `BACKEND_API_URL=http://localhost:8000/api`
- **Required**: Yes
- **Used by**: Stock data retrieval, news fetching

### MCP Server Configuration

#### MCP_SERVER_HOST
- **Purpose**: Host address for the MCP server
- **Default**: `0.0.0.0`
- **Required**: No

#### MCP_SERVER_PORT
- **Purpose**: Port for the MCP server
- **Default**: `8002`
- **Required**: No

#### MCP_API_KEY
- **Purpose**: Authentication key for MCP server access
- **Format**: Any secure string
- **Example**: `MCP_API_KEY=dev-key-12345`
- **Required**: Yes

#### LOG_LEVEL
- **Purpose**: Logging verbosity level
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Default**: `INFO`
- **Required**: No

## Service Key Setup Instructions

### Step 1: Access Supabase Dashboard

1. Go to [supabase.com](https://supabase.com)
2. Sign in to your account
3. Select your project

### Step 2: Navigate to API Settings

1. Click on "Settings" in the left sidebar
2. Select "API" from the settings menu
3. Scroll down to the "Project API keys" section

### Step 3: Locate Service Role Key

1. Find the "service_role" key (not the "anon" key)
2. Click the "Copy" button or reveal the key
3. This is your `SUPABASE_SERVICE_KEY`

### Step 4: Verify Key Format

Your service key should:
- Start with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`
- Contain `"role":"service_role"` when decoded
- Have an expiration date far in the future (typically 2075)

### Step 5: Update Environment File

1. Open `mcp/.env`
2. Replace `YOUR_ACTUAL_SERVICE_KEY_HERE` with your actual service key
3. Save the file

## Required Permissions

The SUPABASE_SERVICE_KEY must have the following permissions:

### Database Permissions
- **SELECT**: Read access to all tables
- **INSERT**: Create new records (embeddings, logs)
- **UPDATE**: Modify existing records
- **DELETE**: Remove records when needed
- **USAGE**: Access to schema public

### Vector Extension Permissions
- **pgvector extension**: Must be enabled
- **Vector functions**: Access to similarity search functions
- **Index management**: Ability to create and use HNSW indexes

### Schema Access
- **public schema**: Full access
- **Custom functions**: Execute vector search functions
- **Triggers**: If any are defined for the tables

## Configuration Validation

The system automatically validates configuration on startup. Check these files for validation logic:

### config.py
```python
def validate_config():
    """Validates all required environment variables"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY', 
        'SUPABASE_SERVICE_KEY',
        'OPENAI_API_KEY',
        'BACKEND_API_URL'
    ]
    # Validation logic here
```

### Validation Checks
1. **Environment variables exist**: All required vars are set
2. **Format validation**: URLs are valid, keys have correct format
3. **Connection testing**: Can connect to Supabase and backend API
4. **Permission testing**: Service key has required permissions

## Troubleshooting Common Issues

### Issue 1: RAG System Not Working

**Symptoms:**
- "RAG Evidence" tool returns errors
- Vector database connection failures
- Missing semantic search results

**Causes & Solutions:**

#### Missing Service Key
```
Error: SUPABASE_SERVICE_KEY not found in environment
```
**Solution**: Add the service key to your `.env` file

#### Invalid Service Key
```
Error: Invalid JWT token or insufficient permissions
```
**Solution**: 
1. Verify the key is copied correctly (no extra spaces)
2. Ensure it's the service_role key, not the anon key
3. Check key hasn't expired

#### Wrong Key Type
```
Error: Insufficient permissions for vector operations
```
**Solution**: Ensure you're using the service_role key, not the anon key

### Issue 2: Database Connection Failures

**Symptoms:**
- Connection timeouts
- Authentication errors
- SSL/TLS errors

**Solutions:**

#### Network Issues
1. Check your internet connection
2. Verify Supabase project is active
3. Test connection: `curl https://[project-id].supabase.co`

#### SSL Certificate Issues
1. Update your system certificates
2. Check firewall settings
3. Try connecting from a different network

### Issue 3: Vector Database Not Found

**Symptoms:**
```
Error: relation "news_embeddings" does not exist
```

**Solution:**
1. Run the setup SQL script: `scripts/setup_vectordb.sql`
2. Verify pgvector extension is enabled
3. Check table creation in Supabase SQL Editor

### Issue 4: Embedding Generation Failures

**Symptoms:**
- OpenAI API errors
- Rate limiting errors
- Invalid API key errors

**Solutions:**

#### Invalid OpenAI Key
```
Error: Invalid API key provided
```
**Solution**: Verify your OpenAI API key in `.env`

#### Rate Limiting
```
Error: Rate limit exceeded
```
**Solution**: 
1. Check your OpenAI usage limits
2. Implement retry logic with backoff
3. Consider upgrading your OpenAI plan

#### Quota Exceeded
```
Error: You exceeded your current quota
```
**Solution**: Add credits to your OpenAI account

### Issue 5: Backend API Connection Issues

**Symptoms:**
- Stock data not loading
- News data unavailable
- API connection timeouts

**Solutions:**

#### Backend Not Running
**Solution**: Start your backend server on the configured port

#### Wrong URL
**Solution**: Verify `BACKEND_API_URL` matches your backend server

#### API Key Issues
**Solution**: Check if backend requires authentication

## Environment File Template

Create your `.env` file with this template:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Backend API Configuration  
BACKEND_API_URL=http://localhost:8000/api

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8002
MCP_API_KEY=your_secure_mcp_key_here
LOG_LEVEL=INFO
```

## Security Best Practices

### Environment Variables
1. **Never commit `.env` files** to version control
2. **Use different keys** for development and production
3. **Rotate keys regularly** (every 90 days recommended)
4. **Limit key permissions** to minimum required

### Service Key Security
1. **Store securely**: Use environment variables, not hardcoded values
2. **Monitor usage**: Check Supabase logs for unusual activity
3. **Restrict access**: Only use service key on trusted servers
4. **Backup keys**: Store backup keys securely for disaster recovery

### Network Security
1. **Use HTTPS**: Always use secure connections
2. **Firewall rules**: Restrict database access to known IPs
3. **VPN access**: Consider VPN for production database access

## Testing Configuration

### Manual Testing

#### Test Supabase Connection
```bash
python -c "
from mcp.rag.vectordb import get_vector_db
db = get_vector_db()
print('✅ Supabase connection successful')
"
```

#### Test OpenAI API
```bash
python -c "
from mcp.rag.embeddings import generate_embedding
result = generate_embedding('test text')
print('✅ OpenAI API working')
"
```

#### Test Backend API
```bash
curl http://localhost:8000/api/stocks
```

### Automated Testing

Run the configuration validation tests:
```bash
python -m pytest mcp/test_service_key_validation.py -v
```

## Production Configuration

### Environment-Specific Settings

#### Development
- Use development Supabase project
- Lower rate limits
- Verbose logging (DEBUG level)
- Local backend API

#### Production
- Use production Supabase project
- Higher rate limits
- Error-level logging only
- Production backend API with load balancing

### Scaling Considerations

#### Database
- Configure connection pooling
- Set appropriate timeout values
- Monitor connection usage

#### API Keys
- Implement key rotation
- Use multiple OpenAI keys for load distribution
- Monitor API usage and costs

## Support and Monitoring

### Health Checks
The system provides comprehensive health check endpoints:

#### Basic Health Check
```bash
curl http://localhost:8002/health
```

#### RAG System Health
```python
from mcp.server.tools.rag_tools import get_rag_health
health = get_rag_health()
print(f"System Status: {health['system_status']}")
```

#### System Status Indicators
The RAG system provides color-coded status indicators:

| Indicator | Description | GREEN | YELLOW | RED |
|-----------|-------------|-------|--------|-----|
| **database** | Vector DB connectivity | Connected | - | Disconnected |
| **authentication** | Service key validity | Valid | - | Invalid/Missing |
| **performance** | Search latency | <5s | 5-15s | >15s |
| **reliability** | Success rate (24h) | ≥95% | 80-95% | <80% |
| **data_coverage** | Embeddings count | >1000 | 100-1000 | <100 |

### Logging and Monitoring

#### Log Files
The system generates structured logs in multiple locations:
- **RAG System Logs**: `mcp/logs/rag_system.log`
- **MCP Server Logs**: `mcp/logs/mcp_server_YYYYMMDD.log`

#### Structured Logging Format
Logs use JSON format for easy parsing and monitoring:
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "event": "rag_search",
  "symbol": "HDFCBANK",
  "duration_ms": 1250,
  "success": true,
  "result_count": 5,
  "avg_relevance": 0.82,
  "timeout": false,
  "partial": false
}
```

#### Performance Metrics
Monitor system performance with built-in metrics:
```python
from mcp.server.monitoring import get_rag_monitor

monitor = get_rag_monitor()
summary = monitor.get_performance_summary(hours=24)
print(f"Success Rate: {summary['overall_success_rate']:.1f}%")
print(f"Avg Latency: {summary['search_metrics']['avg_duration_ms']:.0f}ms")
```

#### Error Analysis
The monitoring system categorizes errors by type:
- **timeout**: Search operations that exceeded time limits
- **connection**: Database connectivity issues
- **authentication**: Service key or permission problems
- **other**: Miscellaneous errors

### Monitoring Metrics
- Configuration validation success/failure rates
- Database connection health and latency
- Search operation performance metrics
- API response times and error rates
- System resource utilization

For additional support, check the main documentation files:
- [README.md](../README.md) - General overview
- [QUICKSTART.md](../QUICKSTART.md) - Quick setup guide
- [RAG_MCP_Overview.md](RAG_MCP_Overview.md) - Technical details