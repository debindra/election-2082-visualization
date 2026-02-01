# Multi-stage build: frontend + Python API
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
# Empty VITE_API_URL = same-origin API calls (relative /api/v1/...)
ENV VITE_API_URL=
RUN npm run build

# Stage 2: Python API + serve frontend
FROM python:3.12-slim
WORKDIR /app

# Install runtime deps for geopandas/shapely
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-dev \
    libgdal-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code and data
COPY app ./app
COPY data ./data

# Built frontend static files
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Production: no reload, bind all interfaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
