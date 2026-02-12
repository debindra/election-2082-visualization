"""
FastAPI Main Application for RAG Chatbot

Nepal Election RAG Chatbot System running on port 8002.
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from services import (
    EmbeddingService,
    FaissVectorStore,
    ElectionAnalyticsService,
    DeepSeekLLMService,
    QueryClassifier,
    QueryRouter,
    ElectionChatService,
    RetrievalService,
    SQLiteService
)
from models.schemas import (
    ChatRequest,
    ChatResponse,
    AnalyticsRequest,
    AnalyticsResponse,
    HealthResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Global services (initialized on startup)
embedding_service = None
vector_store = None
analytics_service = None
llm_service = None
query_classifier = None
sqlite_service = None
query_router = None
chat_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context for startup and shutdown.
    """
    # Startup
    logger.info("Starting up RAG services...")
    
    # Initialize embedding service
    global embedding_service, vector_store, analytics_service, llm_service
    global query_classifier, query_router, chat_service, sqlite_service
    
    try:
        # Initialize DeepSeek LLM
        llm_service = DeepSeekLLMService()
        if not llm_service.is_configured():
            logger.warning("DeepSeek API key not configured. Some features may be limited.")
        
        # Initialize SQLite service
        sqlite_service = SQLiteService(db_path=settings.sqlite_db_path)
        logger.info(f"SQLite service initialized at {settings.sqlite_db_path}")
        
        # Initialize analytics service (keep for backward compatibility)
        analytics_service = ElectionAnalyticsService()
        
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Initialize vector store
        vector_store = FaissVectorStore(embedding_dim=embedding_service.embedding_dim)
        
        # Try to load existing index
        index_loaded = vector_store.load()
        if index_loaded:
            logger.info("Loaded existing FAISS index from disk")
        else:
            logger.warning("No existing index found. Run data processing script to build index.")
        
        # Initialize query classifier
        query_classifier = QueryClassifier(llm_service=llm_service)
        
        # Initialize query router with SQLite
        if settings.use_sqlite and Path(settings.sqlite_db_path).exists():
            logger.info("Using SQLite for structured queries")
            query_router = QueryRouter(
                classifier=query_classifier,
                sqlite=sqlite_service,
                retrieval=RetrievalService(embedding_service, vector_store),
                llm=llm_service
            )
        else:
            logger.warning("SQLite not available or disabled. Query router will use fallback.")
            query_router = None
        
        # Initialize chat service
        chat_service = ElectionChatService(query_router)
        
        logger.info("All RAG services initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing services: {e}", exc_info=True)
        # Continue with None services; endpoints will handle gracefully
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG services...")
    # Cleanup if needed
    logger.info("RAG services shutdown complete")


# Lifespan context
app.router.lifespan_context = lifespan


# ================== HEALTH ENDPOINTS ==================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/docs",
        "health": "/health",
        "chat": "/api/v1/chat",
        "analytics": "/api/v1/analytics"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns system status and configuration.
    """
    vector_index_loaded = vector_store is not None and vector_store.index is not None
    analytics_loaded = analytics_service is not None
    deepseek_configured = llm_service is not None and llm_service.is_configured()
    sqlite_available = sqlite_service is not None and Path(settings.sqlite_db_path).exists()
    
    return HealthResponse(
        status="healthy" if vector_index_loaded and analytics_service else "degraded",
        embedding_model=settings.embedding_model,
        vector_index_loaded=vector_index_loaded,
        analytics_loaded=analytics_loaded,
        deepseek_configured=deepseek_configured
    )


# ================== CHAT ENDPOINTS ==================

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint for natural language queries about election data.
    
    Supports:
    - Natural language questions
    - Metadata filtering
    - Configurable retrieval depth
    
    Query Types Supported:
    - EXACT_LOOKUP: Count, find specific entities
    - ANALYTICAL: Statistics, distributions, trends
    - SEMANTIC_SEARCH: Conceptual questions, similarity-based
    - COMPARISON: Compare between entities
    - AGGREGATION: Group by, summary
    - COMPLEX: Multi-step queries
    """
    if chat_service is None:
        raise HTTPException(
            status_code=503,
            detail="Chat service not initialized. Please check server logs."
        )
    
    logger.info(f"Chat request: query='{request.query}', filters={request.filters}, top_k={request.top_k}")
    
    # Process query
    result = await chat_service.chat(
        query=request.query,
        filters=request.filters,
        top_k=request.top_k
    )
    
    return result


# ================== ANALYTICS ENDPOINTS ==================

@app.post("/api/v1/analytics", response_model=AnalyticsResponse)
async def analytics_endpoint(request: AnalyticsRequest):
    """
    Direct analytics endpoint for programmatic access.
    
    Query Types:
    - count: Count candidates or voting centers
    - aggregate: Group by field
    - statistics: Get statistical measures
    - compare: Compare entities
    - exact_lookup: Find specific records
    - keyword_search: Search by keywords
    - fuzzy_search: Fuzzy matching
    - top_n: Get top N by field
    """
    if analytics_service is None:
        raise HTTPException(
            status_code=503,
            detail="Analytics service not initialized. Please check server logs."
        )
    
    logger.info(f"Analytics request: query_type='{request.query_type}', params={request.params}")
    
    try:
        query_type = request.query_type.lower()
        params = request.params
        
        if query_type == "count":
            target = params.get("target", "candidates")
            filters = params.get("filters")
            
            if target == "voting_centers":
                count = analytics_service.count_voting_centers(filters)
            else:
                count = analytics_service.count_candidates(filters)
            
            return AnalyticsResponse(
                query_type=query_type,
                result={"count": count}
            )
        
        elif query_type == "aggregate":
            field = params.get("field")
            target = params.get("target", "candidates")
            filters = params.get("filters")
            
            aggregation = analytics_service.aggregate_by_field(field, target, filters)
            
            return AnalyticsResponse(
                query_type=query_type,
                result={"aggregation": aggregation}
            )
        
        elif query_type == "statistics":
            field = params.get("field")
            target = params.get("target", "candidates")
            filters = params.get("filters")
            
            stats = analytics_service.get_statistics(field, target, filters)
            
            return AnalyticsResponse(
                query_type=query_type,
                result={"statistics": stats}
            )
        
        elif query_type == "compare":
            entity_type = params.get("entity_type")
            entities = params.get("entities", [])
            metric = params.get("metric", "count")
            filters = params.get("filters")
            
            comparison = analytics_service.compare_entities(entity_type, entities, metric, filters)
            
            return AnalyticsResponse(
                query_type=query_type,
                result={"comparison": comparison}
            )
        
        elif query_type == "exact_lookup":
            column = params.get("column")
            value = params.get("value")
            target = params.get("target", "candidates")
            limit = params.get("limit", 10)
            
            results = analytics_service.exact_lookup(column, value, target, limit)
            
            return AnalyticsResponse(
                query_type=query_type,
                result={"matches": results, "count": len(results)}
            )
        
        elif query_type == "keyword_search":
            keyword = params.get("keyword")
            columns = params.get("columns")
            target = params.get("target", "candidates")
            limit = params.get("limit", 10)
            
            results = analytics_service.keyword_search(keyword, columns, target, limit)
            
            return AnalyticsResponse(
                query_type=query_type,
                result={"matches": results, "count": len(results)}
            )
        
        elif query_type == "fuzzy_search":
            search_term = params.get("search_term")
            column = params.get("column")
            target = params.get("target", "candidates")
            threshold = params.get("threshold", 0.85)
            limit = params.get("limit", 10)
            
            results = analytics_service.fuzzy_search(search_term, column, target, threshold, limit)
            
            return AnalyticsResponse(
                query_type=query_type,
                result={"matches": results, "count": len(results)}
            )
        
        elif query_type == "top_n":
            field = params.get("field")
            n = params.get("n", 10)
            target = params.get("target", "candidates")
            ascending = params.get("ascending", False)
            filters = params.get("filters")
            
            results = analytics_service.get_top_n(field, n, target, ascending, filters)
            
            return AnalyticsResponse(
                query_type=query_type,
                result={"top_n": results}
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported query type: {query_type}. "
                       f"Supported: count, aggregate, statistics, compare, exact_lookup, "
                       f"keyword_search, fuzzy_search, top_n"
            )
    
    except Exception as e:
        logger.error(f"Error processing analytics request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process analytics request: {str(e)}"
        )


# ================== ERROR HANDLERS ==================

@app.post("/api/reset_session")
async def reset_session_endpoint():
    """
    Reset/clear the current RAG chat session.
    
    Returns confirmation that the session has been reset.
    """
    # For now, just return success - future implementations may store session state
    logger.info("Session reset requested")
    return {
        "status": "success",
        "message": "Session reset successfully"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler to avoid leaking internal error details.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ================== MAIN ==================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info"
    )
