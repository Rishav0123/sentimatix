# Backend Dockerfile to ensure a Python 3.11 runtime and reproducible builds
FROM python:3.11-slim

# System deps (minimal) for common Python builds
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy backend sources
COPY . ./

# Expose port (can be overridden by Render PORT env var)
EXPOSE 8080

# Default command — Render will override port with $PORT if set
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
