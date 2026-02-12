# Proxy Implementation - Quick Start Guide

## Changes Made

### 1. RAG Service Health Check Fixed
- **Increased startup time**: 180s start period (was 40s)
- **More retries**: 5 retries (was 3)
- **Longer timeout**: 15s (was 10s)
- **Removed pre-download**: Models download on-demand for faster initial startup

### 2. Main App Proxy Implemented
- **Proxy routes**: `/rag-api/*` forwards to RAG service
- **Routes added**:
  - `/rag-api/health` → RAG health check
  - `/rag-api/api/v1/chat` → RAG chat endpoint
  - `/rag-api/api/v1/analytics` → RAG analytics
  - `/rag-api/api/reset_session` → RAG session reset

### 3. Service Dependencies
- **Main app** now waits for RAG service to be healthy before starting
- **Redis health check** fixed syntax
- **Network**: Services communicate via Docker internal network

## How to Access the System

### ✅ After rebuild, access everything on port 8000:

```bash
# RAG Chat (through proxy - RECOMMENDED)
curl -X POST http://localhost:8000/rag-api/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Total candidates?", "filters": {}, "top_k": 10}'

# Or access directly (if proxy fails)
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Total candidates?", "filters": {}, "top_k": 10}'
```

### Frontend URL

```
http://localhost:8000
```

This is your main application interface.

## Rebuild Instructions

### Option 1: Full Rebuild (Recommended)

```bash
# Stop all services
docker compose down

# Rebuild with no cache (ensures latest changes)
docker compose build --no-cache

# Start services
docker compose up -d

# Watch logs
docker compose logs -f rag-qa
```

### Option 2: Rebuild RAG Only

```bash
# Stop and remove only RAG container
docker compose rm -f rag-qa

# Rebuild RAG
docker compose build rag-qa

# Start all services
docker compose up -d
```

## What to Expect

### First Startup (Slow)

On **first startup**, RAG service will:
1. Download embedding model (~200 MB) - Takes 2-3 minutes
2. Download cross-encoder model (~100 MB) - Takes 1-2 minutes
3. Health checks will fail until models are downloaded
4. After ~3-5 minutes, service should become healthy

### Subsequent Startups (Fast)

After models are cached in the volume:
1. Models load from cache
2. Service starts in ~10-20 seconds
3. Health checks pass quickly

## Testing the Proxy

### 1. Test RAG Service Health (Direct)

```bash
# Wait 30 seconds after startup, then test:
curl http://localhost:8002/health

# Expected response:
{
  "status": "healthy",
  "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "vector_index_loaded": true,
  "analytics_loaded": true,
  "deepseek_configured": true
}
```

### 2. Test Proxy Health

```bash
curl http://localhost:8000/rag-api/health

# Should return same as above
```

### 3. Test Chat Endpoint

```bash
curl -X POST http://localhost:8000/rag-api/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Total candidates?",
    "filters": {},
    "top_k": 10
  }'

# Expected response:
{
  "answer": "There are 3,407 candidates in total...",
  "sources": [...],
  "query_type": "EXACT_LOOKUP"
}
```

## Troubleshooting

### Issue: RAG Service Won't Start

**Symptom**: Container exits immediately or health checks fail

**Solutions**:

1. **Check logs**:
   ```bash
   docker compose logs rag-qa
   ```

2. **Wait longer**: First startup takes 3-5 minutes for model downloads
   ```bash
   # Monitor health
   watch -n 10 'curl -s http://localhost:8002/health || echo "Not ready"'
   ```

3. **Verify API key**:
   ```bash
   docker compose exec rag-qa env | grep DEEPSEEK_API_KEY
   ```

4. **Rebuild without cache**:
   ```bash
   docker compose build --no-cache rag-qa
   ```

### Issue: Proxy Returns 503

**Symptom**: `/rag-api/*` returns "RAG service unavailable"

**Solutions**:

1. **Verify RAG is running**:
   ```bash
   docker compose ps rag-qa
   ```

2. **Check RAG health**:
   ```bash
   curl http://localhost:8002/health
   ```

3. **Check network**:
   ```bash
   docker network inspect election-visualization_default
   ```

4. **Restart services**:
   ```bash
   docker compose restart rag-qa
   docker compose restart app
   ```

### Issue: "Permission Denied" on volume mount

**Symptom**: Logs show permission errors on `data/elections`

**Solution**: The volume is mounted as read-only for the RAG service. This is correct - CSVs should not be modified by RAG container.

If SQLite database needs to be writable:
```bash
# The SQLite volume is separate:
# rag-qa-db:/app/data/elections - This allows database writes
```

## Success Criteria

Your system is working when:

✅ All three containers are running (`docker compose ps`)
✅ RAG health check passes (`curl http://localhost:8002/health`)
✅ Proxy health check passes (`curl http://localhost:8000/rag-api/health`)
✅ Chat endpoint works (test with curl)
✅ Frontend loads at `http://localhost:8000`
✅ No error logs in any service

## Documentation

- **Full Docker setup**: See `DOCKER_SETUP.md`
- **Proxy documentation**: See `RAG_PROXY_SETUP.md`

---

**Next Step**: Rebuild services with `docker compose up -d --force-recreate`
