# RAG Election Chatbot System

A Retrieval-Augmented Generation (RAG) chatbot for Nepal House of Representatives Election Data.

## Overview

This system provides intelligent Q&A about election candidates and voting centers using:
- **Vector embeddings** for semantic search
- **FAISS vector database** for fast retrieval
- **DeepSeek LLM** for answer generation
- **Pandas analytics** for exact lookups and statistics

## Features

### Query Types Supported

1. **EXACT_LOOKUP**: Count, find specific entities, list items
   - Examples: "How many candidates in Kathmandu?", "Find Ram Bahadur"
   - Method: Pandas exact matching

2. **ANALYTICAL**: Statistics, averages, distributions, trends
   - Examples: "Average age of candidates", "Age distribution by province"
   - Method: Pandas statistics

3. **SEMANTIC_SEARCH**: Conceptual questions, similarity-based
   - Examples: "Candidates with law education", "Rural area candidates"
   - Method: Embeddings + FAISS + Cross-encoder re-ranking

4. **COMPARISON**: Compare between entities
   - Examples: "Compare parties", "Province A vs B"
   - Method: Pandas aggregation + comparison

5. **AGGREGATION**: Group by, summary
   - Examples: "Show candidates by party", "Breakdown by district"
   - Method: Pandas groupby

6. **COMPLEX**: Multi-step queries requiring multiple operations
   - Examples: "Party with most candidates under 30", "Highest voter district and top party"
   - Method: Query decomposition + recursive routing

## Installation

### Prerequisites

- Python 3.9+
- DeepSeek API key (get from https://platform.deepseek.com/api-keys)
- 4GB RAM minimum (8GB recommended)
- 2GB disk space for FAISS index

### Setup Steps

1. **Clone and navigate**:
   ```bash
   cd election-visualization
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cd rag-qa
   cp .env.example .env
   # Edit .env and add your DeepSeek API key
   nano .env
   ```

4. **Build FAISS index**:
   ```bash
   cd rag-qa
   python scripts/build_index.py --combined
   ```

5. **Run tests** (optional):
   ```bash
   python scripts/test_system.py
   ```

6. **Start server**:
   ```bash
   # Development
   python main.py
   
   # Production with Docker
   docker-compose up rag-qa
   ```

## Project Structure

```
rag-qa/
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration management
├── models/
│   ├── __init__.py
│   └── schemas.py                # Pydantic models
├── services/
│   ├── __init__.py
│   ├── embedding_service.py        # Sentence transformers embeddings
│   ├── vector_store.py            # FAISS vector database
│   ├── analytics_service.py        # Pandas-based analytics
│   ├── llm_service.py              # DeepSeek LLM integration
│   ├── retrieval_service.py        # Retrieval with re-ranking
│   ├── query_classifier.py          # Query type classification
│   ├── query_router.py             # Query routing orchestration
│   └── chat_service.py             # Main chat orchestrator
├── prompts/
│   ├── __init__.py
│   └── system_prompt.py           # Prompt templates
├── scripts/
│   ├── build_index.py             # Index building script
│   └── test_system.py             # Test suite
├── data/
│   └── faiss_index/              # FAISS index files (generated)
├── main.py                       # FastAPI application
├── requirements.txt                # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## API Endpoints

### Health Check
```
GET /health
```

Returns system status and configuration.

### Chat Endpoint
```
POST /api/v1/chat
Content-Type: application/json

{
  "query": "How many candidates in Kathmandu?",
  "filters": {
    "district": "काठमाडौं"
  },
  "top_k": 5
}
```

Response includes:
- `answer`: Natural language answer in Nepali and English
- `sources`: Retrieved documents (if semantic search)
- `analytics_used`: Analytics data (if exact/analytical query)
- `query_type`: Type of query (exact_lookup, analytical, etc.)
- `intent`: Intent of the query (polling, candidate, voting_center, statistics, etc.)
- `entities`: Extracted entities from the query (target, district, party, gender, etc.)
- `method`: Processing method used
- `metadata`: Additional information (confidence, counts, etc.)

### Analytics Endpoint
```
POST /api/v1/analytics
Content-Type: application/json

{
  "query_type": "count",
  "params": {
    "target": "candidates",
    "filters": {
      "district": "काठमाडौं"
    }
  }
}
```

Supported query types:
- `count`: Count records
- `aggregate`: Group by field
- `statistics`: Get statistical measures
- `compare`: Compare entities
- `exact_lookup`: Find specific records
- `keyword_search`: Search by keywords
- `fuzzy_search`: Fuzzy matching
- `top_n`: Get top N by field

## Usage Examples

### Example 1: Exact Lookup
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "काठमाडौंमा कति उम्मेदवारहरू छन्?",
    "top_k": 5
  }'
```

### Example 2: Analytical Query
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "उम्मेदवारहरूको औसत उमेर कति हो?",
    "top_k": 5
  }'
```

### Example 3: Semantic Search
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "कानून को शिक्षा भएका उम्मेदवार को को हो?",
    "top_k": 10
  }'
```

### Example 4: Comparison
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "नेपाली काँग्रेस र एमालेको उम्मेदवार संख्यामा तुलना गर्नुहोस्",
    "top_k": 5
  }'
```

### Example 5: With Filters
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "कति उम्मेदवारहरू छन्?",
    "filters": {
      "party": "नेपाली काँग्रेस",
      "district": "सुनसरी"
    },
    "top_k": 5
  }'
```

## Testing

### Build Index
```bash
# Build combined index (candidates + voting centers)
cd rag-qa
python scripts/build_index.py --combined

# Build only candidate index
python scripts/build_index.py --candidates

# Build only voting center index
python scripts/build_index.py --voting-centers

# Verify existing index
python scripts/build_index.py --verify
```

### Run Tests
```bash
# Test all query types
cd rag-qa
python scripts/test_system.py

# Test specific query types
python scripts/test_system.py exact_lookup
python scripts/test_system.py analytical
python scripts/test_system.py semantic_search
python scripts/test_system.py comparison
python scripts/test_system.py aggregation
python scripts/test_system.py complex
```

## Configuration

### Key Settings

| Setting | Description | Default |
|----------|-------------|----------|
| `EMBEDDING_MODEL` | Sentence transformer model | paraphrase-multilingual-MiniLM-L12-v2 |
| `FAISS_NLIST` | Number of IVF clusters | 100 |
| `FAISS_NPROBE` | Clusters to search | 10 |
| `DEFAULT_TOP_K` | Default retrieval count | 5 |
| `MAX_TOP_K` | Maximum retrieval count | 20 |
| `ENABLE_RERANKING` | Enable cross-encoder re-ranking | true |
| `CROSS_ENCODER_MODEL` | Re-ranking model | ms-marco-MiniLM-L-6-v2 |

### Performance Tuning

For **better accuracy**:
- Use HNSW with higher `efSearch` (try 150-200)
- Enable `ENABLE_RERANKING=true`
- Increase `DEFAULT_TOP_K` (try 10-15)

For **better speed**:
- Use HNSW with lower `efSearch` (try 50-100)
- Decrease `DEFAULT_TOP_K` (try 3-5)
- Disable re-ranking if not needed (`ENABLE_RERANKING=false`)

### FAISS Index Types

The system supports three FAISS index types:

| Index Type | Speed | Accuracy | Memory | Use Case |
|------------|--------|----------|---------|-----------|
| **FlatL2** | Slow | 100% | Low | Exact matches, validation |
| **IVF** | Fast | 95% | Low | Batch queries, medium datasets |
| **HNSW** ⭐ | Very Fast | 95-99% | Medium-High | Single queries, chatbots |

**HNSW is RECOMMENDED** for chatbot applications due to:
- 10-100x faster search than FlatL2
- No training required
- Minimal memory overhead (~3-5 MB for 26K vectors)
- Tunable accuracy-speed tradeoff with `efSearch`

### HNSW Configuration Guide

```bash
# In .env file:
FAISS_INDEX_TYPE=hnsw        # Enable HNSW
FAISS_HNSW_M=32              # Links per node (16-64)
FAISS_HNSW_EF_CONSTRUCTION=128 # Build quality (64-256)
FAISS_HNSW_EF_SEARCH_DEFAULT=100  # Search accuracy (16-200)
```

**Tuning HNSW efSearch by Query Type:**
- `efSearch=16`: Very fast, ~90% recall (use with re-ranking)
- `efSearch=64`: Fast, ~95% recall (good for semantic search)
- `efSearch=100`: Balanced, ~98% recall (default)
- `efSearch=200`: Slow, ~99%+ recall (exact lookups)

**Recommended Settings for Your Dataset (26K vectors, 384-dim):**
```bash
FAISS_HNSW_M=32               # Good balance
FAISS_HNSW_EF_CONSTRUCTION=128  # Good balance
FAISS_HNSW_EF_SEARCH_DEFAULT=100 # Balanced accuracy-speed
```

**Performance Impact:**
- FlatL2 → HNSW: **10-100x faster** with 95-99% recall
- Expected query time: **1-10ms** (vs 50-200ms with FlatL2)
- Throughput: **500-1000 QPS** (vs 5-10 QPS with FlatL2)

## Troubleshooting

### Index Not Loading
- Check if `data/faiss_index/` exists
- Run `python scripts/build_index.py` to build index
- Check file permissions

### DeepSeek API Errors
- Verify `DEEPSEEK_API_KEY` in `.env` file
- Check your DeepSeek account has credits
- Test API key: `curl https://api.deepseek.com/v1/models`

### Out of Memory
- Reduce `FAISS_NLIST` (try 50 instead of 100)
- Use CPU instead of CUDA for embeddings
- Close unused applications

### Slow Responses
- Check if FAISS index is trained (should show `Total vectors: N`)
- Reduce `DEFAULT_TOP_K`
- Disable re-ranking if not needed

## Deployment

### Docker
```bash
# Start RAG service
docker-compose up rag-qa

# View logs
docker-compose logs -f rag-qa

# Stop service
docker-compose stop rag-qa
```

### Production
1. Use Gunicorn/Uvicorn with multiple workers
2. Enable SSL/HTTPS
3. Set `RAG_RELOAD=false`
4. Use Redis for caching
5. Monitor logs and metrics

## Cost Estimates

### DeepSeek API (per 1M tokens)
- Input: $0.14
- Output: $0.28

### Typical Query Costs
- Simple lookup: ~500 tokens ($0.00014)
- Analytical query: ~1,000 tokens ($0.00028)
- Semantic search: ~1,500 tokens ($0.00042)
- Complex query: ~2,000 tokens ($0.00056)

**Monthly estimate** (1,000 queries/month): ~$0.42

## License

This project is part of the Nepal Election Visualization project.

## Support

For issues or questions:
- Check logs in terminal
- Review API documentation: `http://localhost:8002/docs`
- Check health status: `http://localhost:8002/health`
