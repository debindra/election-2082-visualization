# Docker Setup Guide for RAG-QA

This guide explains how to run the Nepal Election RAG Chatbot using Docker and Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Services](#services)
5. [Building the Index](#building-the-index)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher
- **Disk Space**: 5GB minimum (10GB recommended)

### Verify Installation

```bash
docker --version
docker compose version
```

---

## Accessing the System

### Single-Port Access (Recommended)

The main application (port 8000) now proxies all RAG API requests, so you can access everything through a single port:

| Service | URL | Purpose |
|----------|------|---------|
| **Frontend** | http://localhost:8000 | Election dashboard & charts |
| **Main API** | http://localhost:8000/docs | API documentation (Swagger) |
| **RAG Chatbot** | http://localhost:8000/rag-api/docs | Chatbot API (proxied) |
| **RAG Health** | http://localhost:8000/rag-api/health | Health check (proxied) |
| **RAG Chat** | http://localhost:8000/rag-api/api/v1/chat | Chat endpoint (proxied) |
| **RAG Analytics** | http://localhost:8000/rag-api/api/v1/analytics | Analytics endpoint (proxied) |

### Direct RAG Access (Optional)

You can also access RAG service directly:

| Service | URL | Purpose |
|----------|------|---------|
| **RAG API** | http://localhost:8002/docs | API documentation (direct) |
| **RAG Health** | http://localhost:8002/health | Health check (direct) |

### Redis (Direct Access)

```bash
# Connect using redis-cli
docker compose exec redis redis-cli

# Or from your host (if you have redis-cli installed)
redis-cli -h 127.0.0.1 -p 6379
```

---

## Quick Start

### 1. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your DeepSeek API key:

```env
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
```

### 2. Build and Start Services

Build all services:

```bash
docker compose build
```

Start all services:

```bash
docker compose up -d
```

View logs:

```bash
docker compose logs -f rag-qa
```

### 3. Verify Services

Check service health:

```bash
docker compose ps
```

Expected output:
```
NAME                STATUS              PORTS
election-app        running             0.0.0.0:8000->8000/tcp
election-redis      running (healthy)   0.0.0.0:6379->6379/tcp
election-rag-qa     running (healthy)   0.0.0.0:8002->8002/tcp
```

Check RAG health endpoint:

```bash
curl http://localhost:8002/health
```

Expected response:
```json
{
  "status": "healthy",
  "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "vector_index_loaded": true,
  "analytics_loaded": true,
  "deepseek_configured": true
}
```

---

## Configuration

### Environment Variables

The rag-qa service supports the following environment variables:

#### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek API key for LLM | `sk-xxxxx` |

#### Optional (with defaults)

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis server hostname | `redis` |
| `REDIS_PORT` | Redis server port | `6379` |
| `RAG_RELOAD` | Enable auto-reload | `false` |
| `EMBEDDING_MODEL` | Sentence-transformers model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| `DEFAULT_TOP_K` | Default retrieval count | `5` |
| `ENABLE_RERANKING` | Enable cross-encoder re-ranking | `true` |

### Volume Configuration

The following persistent volumes are created:

| Volume | Purpose | Location |
|--------|---------|----------|
| `rag-qa-faiss-index` | FAISS vector index | `/app/data/faiss_index` |
| `rag-qa-sqlite-db` | SQLite database | `/app/data/elections/election_data.db` |
| `rag-qa-redis-data` | Redis data | `/data` |
| `rag-qa-model-cache` | HuggingFace models | `/app/.cache/huggingface` |

---

## Services

### Services Overview

#### 1. **app** (Port 8000)
- **Image**: Built from `./Dockerfile`
- **Purpose**: Main election analytics API
- **Health**: Basic (no healthcheck configured)
- **Volumes**: Elections data (read-only)

#### 2. **redis** (Port 6379)
- **Image**: `redis:7-alpine`
- **Purpose**: Caching for RAG queries
- **Health**: Active healthcheck (redis-cli ping)
- **Volumes**: Persistent Redis data

#### 3. **rag-qa** (Port 8002)
- **Image**: Built from `./rag-qa/Dockerfile`
- **Purpose**: RAG chatbot for natural language queries
- **Health**: Active healthcheck (HTTP /health endpoint)
- **Volumes**: FAISS index, SQLite DB, models cache
- **Dependencies**: redis (must be healthy)

### Service Dependencies

```
rag-qa
  └─> redis (must be healthy)
```

---

## Building the Index

### Option 1: Build Inside Container

```bash
# Access the rag-qa container
docker compose exec rag-qa bash

# Build the index
python scripts/build_index.py --combined

# Exit container
exit
```

### Option 2: Build Outside Container

Build the index on your host machine:

```bash
cd rag-qa
python3 scripts/build_index.py --combined
```

Then copy the index to the container volume:

```bash
docker compose exec rag-qa bash
mkdir -p data/faiss_index
exit

# Copy from host to container
docker cp rag-qa/data/faiss_index/ $(docker compose ps -q rag-qa):/app/data/faiss_index/
```

### Option 3: Mount Pre-built Index (Recommended)

If you already have a pre-built index, mount it as a volume:

1. Stop the service:
```bash
docker compose stop rag-qa
```

2. Create a volume with the index:
```bash
docker volume create rag-qa-faiss-index
docker run --rm -v rag-qa-faiss-index:/data -v $(pwd)/rag-qa/data/faiss_index:/source alpine sh -c "cp -a /source/. /data/"
```

3. Restart the service:
```bash
docker compose up -d rag-qa
```

---

## Testing

### 1. Health Check

```bash
curl http://localhost:8002/health | jq
```

### 2. Chat Endpoint

```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "काठमाडौंमा कति उम्मेदवारहरू छन्?",
    "top_k": 5
  }' | jq
```

### 3. Analytics Endpoint

```bash
curl -X POST http://localhost:8002/api/v1/analytics \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "count",
    "params": {
      "target": "candidates",
      "filters": {
        "district": "काठमाडौं"
      }
    }
  }' | jq
```

### 4. Access API Documentation

Open in browser:
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

---

## Troubleshooting

### Issue: "Dockerfile not found"

**Error**: `ERROR: no Dockerfile found for ./rag-qa/Dockerfile`

**Solution**:
```bash
# Verify Dockerfile exists
ls -la rag-qa/Dockerfile

# If missing, the Dockerfile should be created at this location
```

### Issue: "DeepSeek API key not configured"

**Error**: `DeepSeek API key not configured. Some features may be limited.`

**Solution**:
```bash
# Add API key to .env
echo "DEEPSEEK_API_KEY=sk-your-actual-key" >> .env

# Restart service
docker compose restart rag-qa
```

### Issue: "Port already in use"

**Error**: `Bind for 0.0.0.0:8002 failed: port is already allocated`

**Solution**:
```bash
# Find process using port
lsof -i :8002

# Stop the process or change port in docker-compose.yml
```

### Issue: "Redis connection refused"

**Error**: `Error connecting to Redis at redis:6379`

**Solution**:
```bash
# Check Redis status
docker compose logs redis

# Restart Redis
docker compose restart redis

# Check Redis health
docker compose exec redis redis-cli ping
# Should return: PONG
```

### Issue: "FAISS index not found"

**Error**: `No existing index found. Run data processing script to build index.`

**Solution**: See [Building the Index](#building-the-index) section above.

### Issue: "Out of memory during build"

**Error**: `Container killed due to OOM`

**Solution**:
```bash
# Increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory
# Set to at least 4GB (8GB recommended)

# Or disable model pre-download in Dockerfile
# Comment out the model download section
```

### Issue: "Slow startup due to model downloads"

**Observation**: Container takes 5-10 minutes to start

**Solution**:
- This is normal on first start (models download)
- Subsequent starts are faster (models are cached in volume)
- Monitor progress:
```bash
docker compose logs -f rag-qa
```

### Issue: "Healthcheck failing"

**Error**: `rag-qa unhealthy`

**Solution**:
```bash
# Check service logs
docker compose logs rag-qa

# Check health endpoint manually
docker compose exec rag-qa curl -f http://localhost:8002/health

# Common causes:
# 1. FAISS index not built
# 2. DeepSeek API key missing
# 3. Redis not accessible
```

### View All Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs rag-qa
docker compose logs redis

# Follow logs
docker compose logs -f rag-qa
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart rag-qa

# Stop and start
docker compose down
docker compose up -d
```

---

## Useful Commands

### Container Management

```bash
# List all containers
docker compose ps

# Execute command in container
docker compose exec rag-qa bash

# View container logs
docker compose logs rag-qa

# Stop all services
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers and volumes
docker compose down -v
```

### Volume Management

```bash
# List all volumes
docker volume ls | grep rag-qa

# Inspect volume
docker volume inspect rag-qa-faiss-index

# Remove volume (WARNING: data loss)
docker volume rm rag-qa-faiss-index
```

### Image Management

```bash
# List images
docker images | grep election

# Remove old images
docker image prune -a

# Rebuild from scratch
docker compose build --no-cache rag-qa
```

---

## Performance Optimization

### Reduce Image Size

The Dockerfile already uses `python:3.12-slim` which is minimal.

### Reduce Startup Time

1. **Pre-download models**: Already done in Dockerfile
2. **Use volume cache**: Models are cached in `rag-qa-models` volume
3. **Enable Redis caching**: Configured by default

### Improve Runtime Performance

Adjust environment variables:

```yaml
# In docker-compose.yml, add to rag-qa environment:
environment:
  # Fewer results = faster queries
  - DEFAULT_TOP_K=3
  # Disable re-ranking = faster but less accurate
  - ENABLE_RERANKING=false
```

---

## Production Considerations

### Security

1. **Never commit `.env` file**
2. **Use secrets management**: Docker Secrets or Kubernetes Secrets
3. **Limit container resources**: Add resource limits to `docker-compose.yml`

### Resource Limits

```yaml
rag-qa:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '0.5'
        memory: 1G
```

### Monitoring

```yaml
# Add to rag-qa service
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Backup

Backup persistent volumes:

```bash
# Backup FAISS index
docker run --rm -v rag-qa-faiss-index:/data -v $(pwd):/backup alpine tar czf /backup/faiss-index-backup.tar.gz -C /data .

# Backup SQLite database
docker run --rm -v rag-qa-sqlite-db:/data -v $(pwd):/backup alpine tar czf /backup/sqlite-db-backup.tar.gz -C /data .
```

---

## Next Steps

1. ✅ Build the FAISS index
2. ✅ Configure DeepSeek API key
3. ✅ Start services with Docker Compose
4. ✅ Test the API endpoints
5. ✅ Integrate with frontend application

For more information, see:
- [Deployment Guide](./rag-qa/DEPLOYMENT_GUIDE.md)
- [Performance Improvements](./rag-qa/PERFORMANCE_IMPROVEMENTS.md)

---

**Last Updated**: 2026-02-12
**Version**: 1.0.0
