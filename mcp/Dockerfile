
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file (assuming it's in the root or mcp folder)
# We'll try to copy from the mcp folder first
COPY mcp/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY mcp/ /app/mcp/
COPY mcp/server/ /app/server/
# We need to ensure the module path is correct. 
# run_server.py expects 'server' package in the path.

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "mcp/run_server.py"]
