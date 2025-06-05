# Production deployment Dockerfile for Railway
FROM python:3.11-slim

WORKDIR /app

# Install system packages (keep gcc if needed by requirements-prod.txt)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY main.py .
COPY api/ ./api/
COPY core/ ./core/
COPY models/ ./models/
COPY services/ ./services/

# Expose port
EXPOSE 8000

# Use gunicorn for production
CMD gunicorn --workers 2 --worker-class uvicorn.workers.UvicornWorker main:app --bind "0.0.0.0:${PORT:-8000}"
