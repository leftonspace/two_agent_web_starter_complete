# JARVIS Application Dockerfile
#
# Multi-stage build for production JARVIS application instances.

FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional production dependencies
RUN pip install --no-cache-dir \
    psycopg2-binary \
    redis \
    celery \
    temporalio \
    gunicorn \
    uvicorn[standard]

# Copy application code
COPY agent/ ./agent/
COPY config/ ./config/

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "agent.webapp.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
