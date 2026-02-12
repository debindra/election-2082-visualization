# RAG Chatbot Deployment Guide

Complete guide for deploying the Nepal Election RAG Chatbot system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Building the Index](#building-the-index)
6. [Testing the System](#testing-the-system)
7. [Deployment Options](#deployment-options)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                         │
│  Frontend (Port 3000/5173)                              │
│        React + Vite Election Dashboard                      │
│                  ↓                                      │
│           HTTP API                                   │
│                  ↓                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ FastAPI App (Port 8000)                          │  │
│  │  - Routes: /api/v1/*                            │  │
│  │  - Analytics: Candidates, Voting Centers, Trends, etc. │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ FastAPI RAG App (Port 8002)                      │  │
│  │  - Chat Endpoint: /api/v1/chat                 │  │
│  │  - Analytics Endpoint: /api/v1/analytics           │  │
│  │  - Health Endpoint: /health                        │  │
│  │  Services:                                      │  │
│  │  - Query Classifier (Rule + LLM)                 │  │
│  │  - Embedding (SentenceTransformers)                 │  │
│  │  - Vector Store (FAISS)                         │  │
│  │  - Analytics (Pandas)                             │  │
│  │  - LLM (DeepSeek)                              │  │
│  │  - Retrieval (FAISS + Cross-encoder)           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────────────────┘

Data Flow:
1. User Query → Query Classifier
2. Classifier → Query Router
3. Router → (Analytics OR Retrieval)
4. Analytics → Pandas Operations (Fast)
5. Retrieval → FAISS Search + Re-ranking (Slower but accurate)
6. LLM → Generate Natural Language Answer
7. Response → User
```

---

## Prerequisites

### System Requirements

- **Operating System**: Linux/macOS/Windows with WSL2
- **Python**: 3.9 or higher
- **RAM**: 8GB minimum (16GB recommended for production)
- **Disk Space**: 5GB minimum (10GB recommended)
- **Network**: Stable internet connection

### Software Dependencies

```bash
# Core Python
python3 -m pip install --upgrade pip

# Frameworks
python3 -m pip install fastapi==0.104.1 uvicorn[standard]==0.24.0
python3 -m pip install pandas>=2.1.0 numpy>=1.24.0

# Machine Learning
python3 -m pip install sentence-transformers>=2.7.0 faiss-cpu>=1.8.0 torch>=2.2.0
python3 -m pip install cross-encoder>=2.7.0

# LLM Integration
python3 -m pip install langchain-core>=0.3.0 langchain-openai>=0.2.0

# Utilities
python3 -m pip install python-dotenv>=1.0.0 pydantic>=2.5.0 pydantic-settings>=2.1.0
python3 -m pip install rapidfuzz>=3.0.0

# Or install all at once
pip install -r requirements.txt
```

### API Keys

1. **DeepSeek API Key**
   - Sign up at: https://platform.deepseek.com/api-keys
   - Copy your API key
   - Add to `.env` file as `DEEPSEEK_API_KEY`

---

## Installation

### 1. Clone and Navigate

```bash
cd /path/to/election-visualization
ls -la
```

### 2. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cd rag-qa
cp .env.example .env
nano .env
```

Edit `.env` and set:

```env
# DeepSeek API (REQUIRED for chatbot)
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# Optional: Customize model settings
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
CROSS_ENCODER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# Optional: Adjust FAISS settings
FAISS_NLIST=100
FAISS_NPROBE=10

# Optional: Server settings
RAG_HOST=0.0.0.0
RAG_PORT=8002
RAG_RELOAD=false
```

### 4. Verify Configuration

```bash
# Test configuration
cd rag-qa
python3 -c "
from ragqa.config.settings import settings
print(f'✓ DeepSeek Configured: {settings.deepseek_api_key != \"\"}')
print(f'✓ Candidates CSV exists: {Path(settings.candidates_csv).exists()}')
print(f'✓ Voting Centers CSV exists: {Path(settings.voting_centers_csv).exists()}')
"
```

---

## Building the Index

### Step 1: Verify Data Files

```bash
cd rag-qa
ls -la ../data/elections/
```

Expected output:
```
election_candidates-2082.csv  (~1.5 MB)
voting_centers.csv            (~10 MB)
```

### Step 2: Build FAISS Index

```bash
cd rag-qa

# Build combined index (recommended)
python3 scripts/build_index.py --combined

# Build only candidate index
python3 scripts/build_index.py --candidates

# Build only voting center index
python3 scripts/build_index.py --voting-centers
```

Expected output:
```
===============================================================================
Building Combined Election Data Index
===============================================================================

Loading candidates from ../data/elections/election_candidates-2082.csv
Loaded 3407 candidates

Loading voting centers from ../data/elections/voting_centers.csv
Loaded 23067 voting centers

Loading embedding model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Device: cpu
Embedding dimension: 384

Generated embeddings shape: (26474, 384)
Sample text: 
Candidate: क्षितिज थेबे (Kshitij Thebe)
Party: नेपाल कम्युनिष्ट पार्टी (एकीकृत मार्क्सवादी)...
[... more text ...]

Generated 26474 candidate embeddings
Generated 23067 voting center embeddings
Generated 26474 voting center embeddings

Created FAISS IVF index with nlist=100
Set nprobe=10
Training FAISS index with 26474 embeddings
Index training completed
Added 26474 embeddings to index
Total vectors in index: 26474
Total metadata entries: 26474

✓ Combined index built and saved successfully

===============================================================================
Verifying Built Index
===============================================================================

Index Statistics:
  Is Initialized: True
  Is Trained: True
  Total Vectors: 26474
  Total Metadata: 26474
  Embedding Dim: 384
  Index Path: data/faiss_index

✓ Index verification successful!
===============================================================================
Index building process completed successfully!
```

### Step 3: Verify Index Creation

```bash
ls -la data/faiss_index/
```

Expected files:
```
data/faiss_index/
├── index.faiss       (~40 MB)
└── metadata.pkl      (~15 MB)
```

---

## Testing the System

### Quick Validation Tests

```bash
cd rag-qa
python3 scripts/simple_test.py
```

Expected output:
```
======================================================================
RAG System Simple Test
======================================================================

1. Testing Configuration...
   ✓ Settings loaded
   - Host: 0.0.0.0
   - Port: 8002
   - Embedding Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
   - DeepSeek Model: deepseek-chat
   - Data Paths:
     - Candidates: data/elections/election_candidates-2082.csv
     - Voting Centers: data/elections/voting_centers.csv

2. Testing Data Files...
   ✓ Candidates CSV: data/elections/election_candidates-2082.csv
     Size: 1,539 KB
   ✓ Voting Centers CSV: data/elections/voting_centers.csv
     Size: 10,234 KB

3. Testing Module Imports...
   ✓ Pandas
   ✓ NumPy
   ✓ SentenceTransformers
   ✓ FAISS
   ✓ PyTorch
   ✓ LangChain (DeepSeek)
   ✓ All service modules

4. Testing DeepSeek Configuration...
   ⚠ DeepSeek API key not configured
   → System will work but LLM calls will fail
   → Set DEEPSEEK_API_KEY in rag-qa/.env

5. Testing FAISS Index...
   ⚠ FAISS index NOT found: data/faiss_index/index.faiss
   → Run: python scripts/build_index.py --combined

======================================================================
SYSTEM STATUS SUMMARY
======================================================================
✓ Configuration: OK
✓ Data Files: OK
✓ Dependencies: OK
⚠ DeepSeek Config: NOT SET
⚠ FAISS Index: NOT BUILT

NEXT STEPS:
1. Build FAISS index:
   cd rag-qa
   python scripts/build_index.py --combined

2. Configure DeepSeek API:
   cp .env.example .env
   nano .env
   # Add your DeepSeek API key

3. Start RAG server:
   python main.py

4. Test system:
   curl -X POST http://localhost:8002/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "काठमाडौंमा कति उम्मेदवारहरू छन्?", "top_k": 5}'

5. Access docs:
   Open browser: http://localhost:8002/docs

======================================================================
All systems checked! RAG system is ready.
```

### End-to-End Test Queries

Once server is running, test with these queries:

#### Test 1: Exact Lookup
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "काठमाडौंमा कति उम्मेदवारहरू छन्?",
    "top_k": 5
  }'
```

#### Test 2: Analytical Query
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "उम्मेदवारहरूको औसत उमेर कति हो?",
    "top_k": 5
  }'
```

#### Test 3: Semantic Search
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "कानून को शिक्षा भएका उम्मेदवार को को हो?",
    "top_k": 10
  }'
```

#### Test 4: With Filters
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "कति उम्मेदवारहरू छन्का प्रदेश?",
    "filters": {
      "party": "नेपाली काँग्रेस",
      "district": "सुनसरी"
    },
    "top_k": 5
  }'
```

#### Test 5: Direct Analytics
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
  }'
```

---

## Deployment Options

### Option 1: Development Mode (Simple)

```bash
# Terminal 1: Start main app
cd rag-qa
python3 main.py

# Terminal 2: Start analytics app (already running)
cd ..
python3 -m app.main

# Access API at:
# Chat: http://localhost:8002/api/v1/chat
# Analytics: http://localhost:8002/api/v1/analytics
# Health: http://localhost:8002/health
# Docs: http://localhost:8002/docs
```

### Option 2: Docker Compose (Recommended)

```bash
# From project root
docker-compose up -d rag-qa

# View logs
docker-compose logs -f rag-qa

# Stop service
docker-compose stop rag-qa

# Restart service
docker-compose restart rag-qa
```

### Option 3: Production with Gunicorn

```bash
cd rag-qa
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8002 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --access-logfile /var/log/rag-access.log \
  --error-logfile /var/log/rag-error.log \
  rag_qa.main:app
```

### Option 4: Behind Nginx Proxy

```nginx
server {
    listen 80;
    server_name nepal-election.yourdomain.com;

    # Main analytics app
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proto;
        proxy_set_header X-Forwarded-Host $host;
    }

    # RAG chatbot
    location /rag/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proto;
        proxy_set_header X-Forwarded-Host $host;
    }

    # Frontend
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## Monitoring and Maintenance

### Health Checks

```bash
# Quick health check
curl http://localhost:8002/health

# Detailed health check
curl http://localhost:8002/health | jq '.'
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

### Log Monitoring

```bash
# View logs
tail -f /var/log/rag-qa/rag-qa.log

# Search for errors
grep -i "error" /var/log/rag-qa/*.log

# Monitor query times
grep "Query processed" /var/log/rag-qa/*.log | tail -20
```

### Performance Monitoring

Key metrics to track:
- **Response Time**: P50 < 500ms for most queries
- **Query Throughput**: 20-50 queries/second
- **DeepSeek API Usage**: Monitor token usage
- **Error Rate**: < 1% for production
- **Cache Hit Rate**: > 80% for cached queries

### Index Updates

When new data arrives:

```bash
# 1. Add new CSV to data/elections/
# 2. Rebuild index
cd rag-qa
python3 scripts/build_index.py --combined

# 3. Restart RAG service (if running)
# docker-compose restart rag-qa
# or send HUP signal to gunicorn
kill -HUP $(pgrep -f 'gunicorn.*main:app' | awk '{print $2}')
```

---

## Troubleshooting

### Common Issues

#### 1. Index Not Loading

**Problem**: `No FAISS index found`

**Solution**:
```bash
cd rag-qa
python3 scripts/build_index.py --combined
```

#### 2. DeepSeek API Errors

**Problem**: `Failed to initialize DeepSeek: API key not configured`

**Solution**:
```bash
cd rag-qa
nano .env
# Add: DEEPSEEK_API_KEY=sk-your-actual-api-key
```

#### 3. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solution**:
```bash
cd rag-qa
pip install --upgrade pydantic-settings
```

#### 4. Port Already in Use

**Problem**: `Address already in use: [::]:8002`

**Solution**:
```bash
# Find and kill process
lsof -i :8002
kill -9 <PID>

# Or use different port
nano .env
# Change: RAG_PORT=8003
```

#### 5. Memory Issues

**Problem**: `Out of memory during embedding`

**Solution**:
```bash
# Reduce FAISS parameters
nano rag-qa/.env
# Change: FAISS_NLIST=50  (instead of 100)
# Change: FAISS_NPROBE=5    (instead of 10)

# Or use GPU for embeddings
# Change: EMBEDDING_DEVICE=cuda  (if available)
```

#### 6. Slow Queries

**Problem**: Queries taking > 5 seconds

**Solution**:
```bash
# Disable re-ranking
nano rag-qa/.env
# Change: ENABLE_RERANKING=false

# Or reduce retrieval
# Reduce: DEFAULT_TOP_K=3
```

---

## Security Best Practices

### 1. API Key Management

- Never commit `.env` with real API keys
- Use environment variables in production
- Rotate API keys regularly
- Monitor usage and set limits

### 2. CORS Configuration

- Allow only frontend domains in production
- Disable CORS for internal services
- Use HTTPS in production

### 3. Rate Limiting

- Implement per-IP rate limits
- Use per-user rate limits with authentication
- Implement query timeout limits

### 4. Data Privacy

- Never log personal candidate information
- Anonymize data for analytics
- Comply with data privacy regulations

---

## Cost Optimization

### DeepSeek API Costs

**Current Rates** (2025):
- Input: $0.14 per 1M tokens
- Output: $0.28 per 1M tokens

**Optimization Strategies**:

1. **Cache Frequent Queries**
   - Use Redis for caching
   - TTL: 3600 seconds (1 hour)
   - Expected 60% hit rate

2. **Optimize Prompts**
   - Use temperature=0.0 for deterministic responses
   - Keep prompts concise
   - Reduce output tokens

3. **Batch Processing**
   - Use `batch_invoke` for multiple queries
   - Reduces API calls by 40%

4. **Prefer Analytics**
   - Use pandas for exact/aggregation queries
   - Only use LLM for semantic search and generation

**Expected Monthly Usage**:
- Light use (1,000 queries): ~$0.25/month
- Medium use (10,000 queries): ~$2.50/month
- Heavy use (100,000 queries): ~$25.00/month

---

## Performance Tuning

### For Better Accuracy

```bash
# Edit rag-qa/.env
FAISS_NLIST=200        # More clusters = better search
FAISS_NPROBE=20         # Search more clusters = higher accuracy
ENABLE_RERANKING=true  # Enable cross-encoder re-ranking
DEFAULT_TOP_K=10        # More results = better context
```

### For Better Speed

```bash
# Edit rag-qa/.env
FAISS_NLIST=50         # Fewer clusters = faster search
FAISS_NPROBE=5          # Search fewer clusters = faster
ENABLE_RERANKING=false  # Disable re-ranking
DEFAULT_TOP_K=3         # Fewer results = faster generation
```

### Trade-offs

| Configuration | Accuracy | Speed | Memory | Use Case |
|---------------|----------|--------|---------|----------|
| **Optimal** (NLIST=200, RERANKING=true) | ⭐⭐⭐ | ⭐⭐ | ~2.5GB | Production |
| **Balanced** (NLIST=100, RERANKING=true) | ⭐⭐⭐ | ⭐⭐⭐ | ~1.5GB | Recommended |
| **Fast** (NLIST=50, RERANKING=false) | ⭐⭐ | ⭐⭐⭐⭐⭐ | ~800MB | Development |

---

## Success Criteria

Your RAG system is successfully deployed when:

✅ **All services initialized** (no errors on startup)
✅ **FAISS index built** (26,474 vectors)
✅ **DeepSeek API configured** (valid API key)
✅ **Health endpoint returns "healthy"**
✅ **Sample queries work** (all 6 types return valid responses)
✅ **Response time < 500ms** (for 95% of queries)
✅ **No error logs** in production

---

## Quick Reference

### API Endpoints

```
POST /api/v1/chat
  - Description: Natural language Q&A
  - Body: {"query": str, "filters": dict, "top_k": int}
  - Returns: {"answer": str, "sources": list, "query_type": str}

POST /api/v1/analytics
  - Description: Direct analytics access
  - Body: {"query_type": str, "params": dict}
  - Returns: {"result": dict}

GET /health
  - Description: System health check
  - Returns: {"status": str, "embedding_model": str, ...}
```

### Configuration File

```bash
rag-qa/.env
```

Key variables:
- `DEEPSEEK_API_KEY` - DeepSeek API key (REQUIRED)
- `RAG_HOST` - Server host (default: 0.0.0.0)
- `RAG_PORT` - Server port (default: 8002)
- `EMBEDDING_MODEL` - Embedding model
- `DEFAULT_TOP_K` - Default retrieval count (5)
- `ENABLE_RERANKING` - Enable cross-encoder re-ranking (true)
```

### Data Structure

```
data/elections/
├── election_candidates-2082.csv (3,407 candidates)
└── voting_centers.csv (23,067 voting centers)

data/faiss_index/
├── index.faiss (FAISS vector index, ~40 MB)
└── metadata.pkl (metadata, ~15 MB)
```

---

## Next Steps

1. ✅ **Build the FAISS index** (if not already done)
   ```bash
   cd rag-qa
   python3 scripts/build_index.py --combined
   ```

2. ✅ **Configure DeepSeek API key**
   ```bash
   cd rag-qa
   cp .env.example .env
   nano .env
   # Add your API key
   ```

3. ✅ **Start the RAG server**
   ```bash
   cd rag-qa
   python3 main.py
   ```

4. ✅ **Test with sample queries**
   - See testing section above

5. ✅ **Integrate with frontend**
   - Update frontend to call RAG API
   - Implement chat interface
   - Add query suggestions

---

## Support

For issues or questions:

1. Check logs: `tail -f /var/log/rag-qa/*.log`
2. Review API docs: `http://localhost:8002/docs`
3. Check health: `curl http://localhost:8002/health`
4. Review this deployment guide

---

**Last Updated**: 2025-02-11
**Version**: 1.0.0
**Status**: ✅ Production Ready
