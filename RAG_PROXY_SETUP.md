# RAG Chatbot Proxy Configuration

This document explains how the main application proxies RAG chatbot requests to the dedicated RAG service.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                    │
│                          │                                  │
│                          ▼                                  │
│              http://localhost:8000                           │
│                          │                                  │
│              ┌──────────────────────┐                     │
│              │   Main App (8000)   │                     │
│              │                      │                     │
│              │    ┌─────────────────┴────┐              │
│              │    │                     │              │
│              │    ▼                     │              │
│              │ /rag-api/*              │              │
│              │                     │              │
│              │    ┌─────────────────────┐│              │
│              │    │  RAG Service (8002)││              │
│              │    │                    ││              │
│              │    │ FastAPI + ML Models ││              │
│              │    └─────────────────────┘│              │
│              │                     │              │
│              └───────────────────────────┘              │
│                                                         │
│     ┌─────────────────┐                              │
│     │  Redis (6379) │                              │
│     │    Cache      │                              │
│     └─────────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## Proxy Routes

The main application (port 8000) now proxies the following RAG service routes:

| Route | Method | Proxies To | Description |
|--------|---------|-------------|-------------|
| `/rag-api/health` | GET | `http://rag-qa:8002/health` | RAG health check |
| `/rag-api/api/v1/chat` | POST | `http://rag-qa:8002/api/v1/chat` | Natural language Q&A |
| `/rag-api/api/v1/analytics` | POST | `http://rag-qa:8002/api/v1/analytics` | Direct analytics |
| `/rag-api/api/reset_session` | POST | `http://rag-qa:8002/api/reset_session` | Reset chat session |

## Benefits

### Single Port Access
- **Frontend can access all services on port 8000**
- No need to configure multiple ports in frontend
- Simpler CORS configuration

### Service Isolation
- RAG service runs independently
- Can be scaled/restarted independently
- ML models don't affect main app performance

### Health Checks
- Main app waits for RAG service to be healthy before starting
- Automatic proxy error handling with 503 status codes

## Usage Examples

### 1. RAG Health Check

```bash
# Through main app proxy (recommended)
curl http://localhost:8000/rag-api/health

# Direct to RAG service
curl http://localhost:8002/health
```

### 2. Chat Query

```bash
# Through main app proxy (recommended)
curl -X POST http://localhost:8000/rag-api/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Total candidates?",
    "filters": {},
    "top_k": 10
  }'

# Direct to RAG service
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Total candidates?",
    "filters": {},
    "top_k": 10
  }'
```

### 3. Analytics Query

```bash
# Through main app proxy
curl -X POST http://localhost:8000/rag-api/api/v1/analytics \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "count",
    "params": {
      "target": "candidates"
    }
  }'

# Direct to RAG service
curl -X POST http://localhost:8002/api/v1/analytics \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "count",
    "params": {
      "target": "candidates"
    }
  }'
```

### 4. Reset Session

```bash
# Through main app proxy
curl -X POST http://localhost:8000/rag-api/api/reset_session

# Direct to RAG service
curl -X POST http://localhost:8002/api/reset_session
```

## Frontend Integration

### JavaScript/Fetch Example

```javascript
// Use the proxy route through main app (port 8000)
const RAG_API_BASE = '/rag-api/api/v1';

async function askRAG(question) {
  const response = await fetch(`${RAG_API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: question,
      filters: {},
      top_k: 5
    })
  });
  
  const data = await response.json();
  return data;
}

// Usage
const result = await askRAG('Total candidates?');
console.log(result);
```

### Axios Example

```javascript
import axios from 'axios';

const ragClient = axios.create({
  baseURL: '/rag-api/api/v1',
  timeout: 30000
});

export const chatService = {
  async ask(query, filters = {}, topK = 5) {
    const response = await ragClient.post('/chat', {
      query,
      filters,
      top_k
    });
    return response.data;
  }
};

// Usage
const result = await chatService.ask('काठमाडौंमा कति उम्मेदवारहरू छन्छ?');
console.log(result);
```

## Configuration

### Docker Compose

The `app` service in `docker-compose.yml` is configured with:

```yaml
app:
  environment:
    # RAG service URL (accessible via Docker network)
    - RAG_SERVICE_URL=http://rag-qa:8002
  depends_on:
    rag-qa:
      condition: service_healthy
```

### Main App Configuration

The main app's `RAG_SERVICE_URL` defaults to `http://rag-qa:8002` but can be overridden:

```bash
# Environment variable
export RAG_SERVICE_URL=http://custom-rag:8002

# Or in .env
RAG_SERVICE_URL=http://custom-rag:8002
```

## Error Handling

The proxy handles errors gracefully:

| Error Code | Meaning | Client Action |
|-------------|-----------|----------------|
| 503 Service Unavailable | RAG service is down or unreachable | Wait and retry |
| 504 Gateway Timeout | RAG service took too long to respond | Increase timeout or simplify query |
| 500 Internal Server Error | RAG service had an error | Check RAG service logs |

### Debugging Proxy Issues

1. **Check RAG service is running**:
   ```bash
   docker compose ps rag-qa
   ```

2. **Check RAG service health**:
   ```bash
   curl http://localhost:8002/health
   ```

3. **Check proxy health**:
   ```bash
   curl http://localhost:8000/rag-api/health
   ```

4. **View main app logs**:
   ```bash
   docker compose logs app
   ```

5. **View RAG service logs**:
   ```bash
   docker compose logs rag-qa
   ```

## Performance Considerations

### Timeout Configuration

The proxy uses a 30-second timeout:
- Most queries complete in < 2 seconds
- Complex queries with re-ranking may take 10-20 seconds
- Adjust timeout in `app/main.py` if needed:

```python
rag_client = httpx.AsyncClient(timeout=60.0)  # Increase to 60 seconds
```

### Load Balancing

For high-traffic deployments, you can scale the RAG service:

```yaml
# docker-compose.yml
services:
  rag-qa:
    deploy:
      replicas: 3  # Run 3 instances
```

The proxy can be updated with load balancing logic to distribute requests across instances.

## Development

### Local Development

When running services locally (not in Docker):

```python
# In app/main.py, change:
RAG_SERVICE_URL = "http://localhost:8002"  # Local development
# RAG_SERVICE_URL = "http://rag-qa:8002"  # Docker (default)
```

### Testing Proxy in Isolation

Test the proxy without affecting production:

```bash
# Build and run main app in test mode
docker compose -f docker-compose.test.yml up app-test

# Verify proxy routes work
curl http://localhost:8001/rag-api/health
```

## Security

### Network Isolation

- Services communicate via Docker internal network
- RAG service is not exposed to internet (only accessible via proxy)
- DeepSeek API key is only in RAG service environment

### CORS Configuration

Main app already has CORS configured. RAG proxy inherits this:
```python
# In app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
```

## Monitoring

### Proxy Health Monitoring

Monitor proxy success/failure rates:

```bash
# Add logging to track proxy calls
docker compose logs app | grep "proxying to RAG"
```

Expected output:
```
INFO - Proxying to RAG chat: query="Total candidates?"
INFO - RAG chat response received in 1.2s
```

## Troubleshooting

### Issue: "RAG service unavailable"

**Symptom**: 503 errors when accessing `/rag-api/*`

**Solutions**:
1. Check RAG service is running: `docker compose ps rag-qa`
2. Check RAG service health: `curl http://localhost:8002/health`
3. Restart RAG service: `docker compose restart rag-qa`
4. Check RAG logs: `docker compose logs rag-qa`

### Issue: "Connection refused"

**Symptom**: Connection refused errors in main app logs

**Solutions**:
1. Verify RAG service is healthy before app starts
2. Check Docker network: `docker network ls`
3. Ensure service names match (`rag-qa` in docker-compose.yml and URL)

### Issue: Slow responses

**Symptom**: Queries taking > 30 seconds

**Solutions**:
1. Check RAG service performance: `docker compose logs rag-qa`
2. Increase proxy timeout in `app/main.py`
3. Check if FAISS index is built
4. Verify Redis cache is working

## Next Steps

1. ✅ Verify proxy works with test queries
2. ✅ Integrate frontend to use `/rag-api/*` routes
3. ✅ Monitor proxy performance and error rates
4. ✅ Add load balancing if needed for production

---

**Last Updated**: 2026-02-12
**Version**: 1.0.0
