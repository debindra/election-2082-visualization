# Multi-stage build for RAG Chatbot Service
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Cache directory for HuggingFace models
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create cache directory for models
RUN mkdir -p /app/.cache/huggingface

# Copy Python dependencies first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config/ ./config/
COPY models/ ./models/
COPY prompts/ ./prompts/
COPY services/ ./services/
COPY utils.py .
COPY main.py .

# Create data directories
RUN mkdir -p data/faiss_index data/elections

# Note: Models will be downloaded on first run and cached in persistent volume
# This allows faster container startup and better layer caching

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8002

# Health check
# Increased start period to 180s to allow time for first-time model downloads
HEALTHCHECK --interval=30s --timeout=15s --start-period=180s --retries=5 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
