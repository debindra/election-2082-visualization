"""
Chat Service Orchestrator

Coordinates all services to process user queries.
"""
import logging
from typing import Dict, Any, Optional

from services.query_router import QueryRouter
from models.schemas import ChatResponse

logger = logging.getLogger(__name__)


class ElectionChatService:
    """
    Main chat service that orchestrates the entire RAG pipeline.
    
    Flow:
    1. User query received
    2. Query classification
    3. Routing to appropriate handler
    4. Execution (analytics/retrieval)
    5. LLM-based answer generation
    6. Response formatting
    """
    
    def __init__(self, router: QueryRouter):
        """
        Initialize chat service.
        
        Args:
            router: Query router service
        """
        self.router = router
        logger.info("Election chat service initialized")
    
    async def chat(self, 
                 query: str,
                 filters: Optional[Dict] = None,
                 top_k: int = 5) -> Dict[str, Any]:
        """
        Main chat endpoint.
        
        Args:
            query: User's natural language query
            filters: Optional metadata filters
            top_k: Number of retrieval results
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        logger.info(f"Processing chat query: '{query}' (filters={filters}, top_k={top_k})")
        
        try:
            # Route and execute query
            result = await self.router.route_and_execute(
                query=query,
                filters=filters,
                top_k=top_k
            )
            
            # Add timestamp
            result["timestamp"] = self._get_timestamp()
            
            # Log processing time (could be enhanced)
            logger.info(f"Query processed successfully: {result.get('query_type')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing chat query: {e}", exc_info=True)
            return {
                "answer": "Sorry, there was an error processing your query. Please try again.",
                "sources": [],
                "analytics_used": None,
                "query_type": "ERROR",
                "method": "error_handler",
                "metadata": {
                    "error": str(e),
                    "timestamp": self._get_timestamp()
                }
            }
    
    async def chat_with_stream(self, 
                              query: str,
                              filters: Optional[Dict] = None) -> Any:
        """
        Chat with streaming response.
        
        Args:
            query: User's natural language query
            filters: Optional metadata filters
            
        Yields:
            Response chunks as they arrive
        """
        logger.info(f"Processing streaming chat query: '{query}'")
        
        # For streaming, we'd need to implement chunked response
        # For now, return non-streaming response
        result = await self.chat(query, filters)
        
        # Return as generator for compatibility
        yield result
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.
        
        Returns:
            Dictionary with system health and stats
        """
        return {
            "service": "Election RAG Chatbot",
            "version": "1.0.0",
            "router_status": "active",
            "available_query_types": [
                "exact_lookup",
                "analytical",
                "semantic_search",
                "comparison",
                "aggregation",
                "complex"
            ],
            "supported_languages": ["Nepali", "English"],
            "data_sources": [
                "election_candidates-2082.csv",
                "voting_centers.csv"
            ]
        }
