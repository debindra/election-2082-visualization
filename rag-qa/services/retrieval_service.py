"""
Retrieval Service with Re-ranking

Handles vector search and cross-encoder based re-ranking.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import time
import hashlib

from services.embedding_service import EmbeddingService
from services.vector_store import FaissVectorStore
from services.redis_cache import RedisCacheService
from sentence_transformers import CrossEncoder
import torch

from config.settings import settings

logger = logging.getLogger(__name__)


class RetrievalService:
    """
    Enhanced retrieval service with cross-encoder re-ranking.
    
    Uses two-stage retrieval:
    1. FAISS vector search (fast, approximate)
    2. Cross-encoder re-ranking (slower, more accurate)
    
    Features:
    - Adaptive efSearch based on query complexity
    - Performance tracking and auto-tuning
    - Redis caching for search results
    """
    
    def __init__(self, 
                 embedding_service: EmbeddingService,
                 vector_store: FaissVectorStore):
        """
        Initialize retrieval service.
        
        Args:
            embedding_service: Service for generating embeddings
            vector_store: FAISS vector database
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        
        # Initialize Redis cache
        self.cache = RedisCacheService()
        
        # Initialize cross-encoder for re-ranking if enabled
        self.cross_encoder = None
        if settings.enable_reranking:
            try:
                logger.info(f"Loading cross-encoder: {settings.cross_encoder_model}")
                self.cross_encoder = CrossEncoder(settings.cross_encoder_model)
                logger.info("Cross-encoder loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load cross-encoder: {e}")
                logger.warning("Proceeding without re-ranking")
        
        # Performance tracking
        self.query_history = []
        self.max_history_size = settings.faiss_performance_window
        
        logger.info("Retrieval service initialized")
    
    def retrieve(self, 
                query: str, 
                k: int = 10,
                filters: Optional[Dict[str, Any]] = None,
                use_reranking: bool = True,
                query_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve documents using vector search with optional re-ranking.
        
        Args:
            query: User's query text
            k: Number of results to return
            filters: Optional metadata filters
            use_reranking: Whether to use cross-encoder re-ranking
            query_type: Optional query type for HNSW efSearch tuning
                     (EXACT_LOOKUP, ANALYTICAL, SEMANTIC_SEARCH, etc.)
            
        Returns:
            List of retrieved documents with metadata
        """
        logger.info(f"Retrieving for query: '{query}' (k={k}, filters={filters})")
        
        start_time = time.time()
        
        # Generate query embedding (with caching)
        query_embedding = self._get_cached_or_generate_embedding(query)
        
        # Calculate embedding hash for caching
        embedding_hash = hashlib.md5(query_embedding.tobytes()).hexdigest()
        
        # Try cache first
        if self.cache.enabled:
            cached_result = self.cache.get_cached_faiss_search(embedding_hash, k, filters or {})
            if cached_result:
                logger.debug("FAISS search cache hit")
                elapsed_ms = (time.time() - start_time) * 1000
                self._track_performance(query, query_type, elapsed_ms, cached=True)
                return cached_result
        
        # Determine optimal efSearch based on query complexity
        ef_search = self._get_adaptive_ef_search(query, filters, query_type, use_reranking)
        
        # Search vector store with dynamic efSearch
        retrieved_docs = self.vector_store.search(
            query_embedding=query_embedding,
            k=k * 2 if use_reranking else k,  # Get more for re-ranking
            filters=filters,
            ef_search=ef_search if ef_search else None
        )
        
        logger.info(f"Retrieved {len(retrieved_docs)} documents from vector store")
        
        # Apply re-ranking if enabled and we have results
        if use_reranking and self.cross_encoder and len(retrieved_docs) > 0:
            retrieved_docs = self._rerank(
                query=query,
                documents=retrieved_docs,
                top_k=k
            )
            logger.info(f"Re-ranked to {len(retrieved_docs)} documents")
        
        # Cache the results
        elapsed_ms = (time.time() - start_time) * 1000
        if self.cache.enabled:
            self.cache.cache_faiss_search(embedding_hash, k, filters or {}, retrieved_docs)
        
        # Track performance
        self._track_performance(query, query_type, elapsed_ms, cached=False)
        
        logger.info(f"Retrieval completed in {elapsed_ms:.1f}ms")
        return retrieved_docs
    
    def _get_cached_or_generate_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding from cache or generate new one.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding array
        """
        # Try cache
        if self.cache.enabled:
            cached_embedding = self.cache.get_cached_embedding(text)
            if cached_embedding is not None:
                logger.debug("Embedding cache hit")
                return cached_embedding
        
        # Generate new embedding
        embedding = self.embedding_service.embed_single(text)
        
        # Cache it
        if self.cache.enabled:
            self.cache.cache_embedding(text, embedding)
        
        return embedding
    
    def _calculate_query_complexity(self, query: str, filters: Dict[str, Any] = None) -> int:
        """
        Calculate query complexity score (1-10).
        
        Factors considered:
        - Query length
        - Number of filters
        - Number of entities/keywords
        - Special characters/punctuation
        
        Args:
            query: Query text
            filters: Optional query filters
            
        Returns:
            Complexity score (1-10)
        """
        score = 1  # Base score
        
        # Length factor
        if len(query) > 50:
            score += 1
        if len(query) > 100:
            score += 1
        
        # Filters factor
        if filters:
            score += min(len(filters), 3)
        
        # Keywords/entities factor (simple heuristic)
        import re
        words = re.findall(r'\b\w+\b', query)
        if len(words) > 5:
            score += 1
        if len(words) > 10:
            score += 1
        
        # Special characters factor
        special_chars = len(re.findall(r'[^\w\s]', query))
        if special_chars > 3:
            score += 1
        
        return min(score, 10)
    
    def _get_adaptive_ef_search(self, 
                               query: str,
                               filters: Optional[Dict[str, Any]],
                               query_type: Optional[str],
                               use_reranking: bool) -> Optional[int]:
        """
        Get adaptive HNSW efSearch parameter based on multiple factors.
        
        Factors:
        - Query type mapping
        - Query complexity
        - Re-ranking enabled status
        - Historical performance (auto-tuning)
        - Time budget (fast response needed?)
        
        Args:
            query: Query text
            filters: Query filters
            query_type: Query type classification
            use_reranking: Whether re-ranking will be used
            
        Returns:
            Optimal efSearch value or None (use default)
        """
        # If not using HNSW, return None
        if not settings.faiss_index_type.lower() == "hnsw":
            return None
        
        # If adaptive efSearch disabled, use simple mapping
        if not settings.faiss_enable_adaptive_ef:
            return self._get_ef_for_query_type(query_type, use_reranking)
        
        # Calculate base efSearch from query type
        base_ef = self._get_ef_for_query_type(query_type, use_reranking) or settings.faiss_hnsw_ef_search_default
        
        # Calculate complexity score
        complexity = self._calculate_query_complexity(query, filters)
        
        # Adjust based on complexity (higher complexity = need higher accuracy)
        complexity_adjustment = (complexity - 1) * 10
        
        # Get historical performance adjustment (auto-tuning)
        performance_adjustment = self._get_performance_adjustment(query_type)
        
        # Calculate final efSearch
        ef_search = base_ef + complexity_adjustment + performance_adjustment
        
        # Clamp to configured bounds
        ef_search = max(settings.faiss_hnsw_ef_search_min, 
                       min(ef_search, settings.faiss_hnsw_ef_search_max))
        
        logger.debug(f"Adaptive efSearch: base={base_ef}, complexity={complexity}, "
                   f"perf_adj={performance_adjustment}, final={ef_search}")
        
        return ef_search
    
    def _get_ef_for_query_type(self, 
                              query_type: Optional[str],
                              use_reranking: bool) -> Optional[int]:
        """
        Get optimal HNSW efSearch parameter based on query type.
        
        Lower efSearch = faster search, lower recall
        Higher efSearch = slower search, higher recall
        
        Args:
            query_type: Type of query (EXACT_LOOKUP, ANALYTICAL, etc.)
            use_reranking: Whether re-ranking will be used
            
        Returns:
            Optimal efSearch value or None (use default)
        """
        # Mapping of query types to efSearch values
        # These values are tuned for ~26K vectors with re-ranking
        ef_search_mapping = {
            # Exact lookups need high accuracy
            "EXACT_LOOKUP": 200,
            "analytical": 200,
            
            # Comparisons need high accuracy
            "COMPARISON": 150,
            "comparison": 150,
            
            # Aggregations need high accuracy
            "AGGREGATION": 150,
            "aggregation": 150,
            
            # Complex queries need high accuracy
            "COMPLEX": 150,
            "complex": 150,
            
            # Semantic search can use lower efSearch (re-ranking will fix recall)
            "SEMANTIC_SEARCH": 64 if use_reranking else 100,
            "semantic_search": 64 if use_reranking else 100,
        }
        
        ef_search = ef_search_mapping.get(query_type.upper() if query_type else None)
        
        if ef_search:
            logger.debug(f"Query type '{query_type}' -> efSearch={ef_search}")
        
        return ef_search
    
    def _track_performance(self, query: str, query_type: str, elapsed_ms: float, cached: bool):
        """
        Track query performance for auto-tuning.
        
        Args:
            query: Query text
            query_type: Query type
            elapsed_ms: Elapsed time in milliseconds
            cached: Whether result was from cache
        """
        if not settings.track_query_performance:
            return
        
        self.query_history.append({
            "query": query[:100],  # Truncate for storage
            "query_type": query_type,
            "elapsed_ms": elapsed_ms,
            "cached": cached,
            "timestamp": time.time()
        })
        
        # Keep only recent history
        if len(self.query_history) > self.max_history_size:
            self.query_history = self.query_history[-self.max_history_size:]
    
    def _get_performance_adjustment(self, query_type: str) -> int:
        """
        Calculate performance-based adjustment for efSearch.
        
        Analyzes recent query performance:
        - If queries are consistently fast, can increase efSearch for better accuracy
        - If queries are consistently slow, decrease efSearch for speed
        
        Args:
            query_type: Query type to analyze
            
        Returns:
            Adjustment value (positive = increase efSearch, negative = decrease)
        """
        if not self.query_history or len(self.query_history) < 10:
            return 0
        
        # Filter by query type
        relevant_queries = [q for q in self.query_history if q["query_type"] == query_type]
        
        if len(relevant_queries) < 5:
            return 0
        
        # Calculate average time
        avg_time = np.mean([q["elapsed_ms"] for q in relevant_queries])
        cache_hit_rate = np.mean([1 if q["cached"] else 0 for q in relevant_queries])
        
        # Adjust based on performance
        if avg_time < 50:  # Very fast - can increase accuracy
            return 20
        elif avg_time < 100:  # Fast - slight increase
            return 10
        elif avg_time > 300:  # Slow - decrease for speed
            return -20
        elif avg_time > 200:  # Somewhat slow - slight decrease
            return -10
        else:
            return 0
    
    def _rerank(self, 
                  query: str,
                  documents: List[Dict[str, Any]],
                  top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Re-rank documents using cross-encoder.
        
        Args:
            query: Original query
            documents: Retrieved documents to re-rank
            top_k: Number of top results to return
            
        Returns:
            Re-ranked list of documents
        """
        if not documents:
            return []
        
        # Prepare query-document pairs
        pairs = [[query, doc.get('content', '')] for doc in documents]
        
        # Get cross-encoder scores
        start_time = time.time()
        try:
            scores = self.cross_encoder.predict(pairs)
            rerank_time = (time.time() - start_time) * 1000
            logger.debug(f"Cross-encoder re-ranking took {rerank_time:.1f}ms")
        except Exception as e:
            logger.error(f"Error in cross-encoder prediction: {e}")
            # Return original order if re-ranking fails
            return documents[:top_k]
        
        # Sort documents by scores (higher is better)
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k re-ranked documents
        reranked = [doc for doc, score in scored_docs[:top_k]]
        
        # Add re-ranking scores to metadata
        for doc, score in scored_docs[:top_k]:
            doc['rerank_score'] = float(score)
        
        logger.debug(f"Re-ranking scores: {[score for _, score in scored_docs[:top_k]]}")
        return reranked
    
    def retrieve_by_filters_only(self, 
                                filters: Dict[str, Any],
                                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve documents using only metadata filters (no vector search).
        
        Useful for exact lookup scenarios.
        
        Args:
            filters: Metadata filters to apply
            limit: Maximum number of results
            
        Returns:
            List of documents matching filters
        """
        logger.info(f"Filter-only retrieval: {filters}")
        
        results = []
        metadata = self.vector_store.metadata
        
        for i, doc in enumerate(metadata):
            if self.vector_store._apply_filters(doc, filters):
                results.append(doc.copy())
                
                if len(results) >= limit:
                    break
        
        logger.info(f"Found {len(results)} documents matching filters")
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get retrieval performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.query_history:
            return {}
        
        queries = self.query_history
        times = [q["elapsed_ms"] for q in queries]
        cache_hits = sum(1 for q in queries if q["cached"])
        
        # Group by query type
        by_type = {}
        for q in queries:
            qt = q["query_type"] or "unknown"
            if qt not in by_type:
                by_type[qt] = []
            by_type[qt].append(q["elapsed_ms"])
        
        return {
            "total_queries": len(queries),
            "avg_time_ms": np.mean(times),
            "median_time_ms": np.median(times),
            "min_time_ms": np.min(times),
            "max_time_ms": np.max(times),
            "cache_hit_rate": cache_hits / len(queries),
            "queries_by_type": {
                qt: {
                    "count": len(tq),
                    "avg_time_ms": np.mean(tq)
                }
                for qt, tq in by_type.items()
            },
            "cache_stats": self.cache.get_stats() if self.cache else {}
        }