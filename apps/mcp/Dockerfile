FROM python:3.11-slim

WORKDIR /app

# Create logs directory required by mcp_stdio.py
RUN mkdir -p /app/logs

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
# (build context = apps/mcp/, so paths are relative to that)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application source code
COPY . .

# Set PYTHONPATH so 'server' package is importable
ENV PYTHONPATH=/app

# Run MCP server in HTTP/SSE mode — Railway sets $PORT dynamically
CMD ["python", "mcp_stdio.py", "--sse"]
