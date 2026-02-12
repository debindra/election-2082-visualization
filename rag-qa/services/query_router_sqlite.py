"""
Query Router Service (SQLite + Vector Search)

Routes queries to appropriate processing based on classification.
Uses SQLite for structured queries and Vector Search for semantic queries.
"""
import logging
import json
from typing import Dict, Any, Optional, List
import asyncio

from services.query_classifier import QueryClassifier, QueryType
from services.sqlite_service import SQLiteService
from services.retrieval_service import RetrievalService
from services.llm_service import DeepSeekLLMService
from services.sql_generator import SQLGenerator, IntentExtractor
from prompts.system_prompt import SYSTEM_PROMPT, build_context_prompt

logger = logging.getLogger(__name__)


class QueryRouterSQLite:
    """
    Routes queries to appropriate handler based on classification.
    
    Hybrid approach combining SQLite for structured queries and 
    vector search for semantic queries.
    """
    
    def __init__(self,
                 classifier: QueryClassifier,
                 sqlite: SQLiteService,
                 retrieval: RetrievalService,
                 llm: DeepSeekLLMService):
        """
        Initialize query router.
        
        Args:
            classifier: Query classifier service
            sqlite: SQLite service for structured queries
            retrieval: Retrieval service for semantic search
            llm: LLM service for generation
        """
        self.classifier = classifier
        self.sqlite = sqlite
        self.retrieval = retrieval
        self.llm = llm
        
        # Initialize SQL generator and intent extractor
        self.sql_generator = SQLGenerator(llm, sqlite)
        self.intent_extractor = IntentExtractor(llm)
        
        logger.info("Query router (SQLite + Vector) initialized")
    
    async def route_and_execute(self, 
                                query: str, 
                                filters: Optional[Dict] = None,
                                top_k: int = 5) -> Dict[str, Any]:
        """
        Route query to appropriate handler and execute.
        
        New Architecture:
        1. Intent + Entity Extraction
        2. Determine: Structured? (SQL) or Semantic? (Vector)
        3. Execute with SQLite or Vector Search
        4. Combine + Validate (if both needed)
        5. LLM Format
        6. Response
        
        Args:
            query: User's natural language query
            filters: Optional metadata filters
            top_k: Number of retrieval results
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        logger.info(f"Routing query: '{query}'")
        
        # Step 1: Intent + Entity Extraction
        intent_result = await self.intent_extractor.extract(query)
        logger.info(f"Intent: {intent_result.get('intent')}, "
                   f"Query Type: {intent_result.get('query_type')}, "
                   f"Confidence: {intent_result.get('confidence'):.2f}")
        
        # Step 2: Is Structured?
        is_structured = self.intent_extractor.is_structured_query(query, intent_result)
        
        logger.info(f"Query routing: {'SQL (Structured)' if is_structured else 'Vector (Semantic)'}")
        
        # Step 3: Route and Execute
        try:
            if is_structured:
                # Use SQLite for structured queries
                return await self._handle_sql_query(query, intent_result, filters)
            else:
                # Use Vector Search for semantic queries
                return await self._handle_semantic_search(query, filters, top_k)
                
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "answer": f"Sorry, there was an error processing your query: {str(e)}",
                "sources": [],
                "sql_used": None,
                "analytics_used": None,
                "query_type": intent_result.get("query_type", "UNKNOWN"),
                "method": "error",
                "metadata": {"error": str(e)}
            }
    
    async def _handle_sql_query(self,
                               query: str,
                               intent_result: Dict[str, Any],
                               filters: Optional[Dict]) -> Dict[str, Any]:
        """
        Handle structured query using SQLite + SQL generation.
        
        Step 1: Generate SQL
        Step 2: Validate SQL
        Step 3: Execute SQL
        Step 4: Format results
        
        Args:
            query: Natural language query
            intent_result: Extracted intent and entities
            filters: Optional metadata filters
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Handling SQL query: {query}")
        
        # Map query types to SQL generation types
        query_type = intent_result.get("query_type", "SEMANTIC_SEARCH")
        query_type_mapping = {
            "EXACT_LOOKUP": "exact_lookup",
            "ANALYTICAL": "statistics",
            "COMPARISON": "comparison",
            "AGGREGATION": "aggregate"
        }
        sql_query_type = query_type_mapping.get(query_type, "auto")
        
        # Generate and execute SQL
        success, result = await self.sql_generator.generate_and_execute(query, sql_query_type)
        
        if not success:
            logger.error(f"SQL execution failed: {result.get('error')}")
            return {
                "answer": f"Sorry, I couldn't process that query using the database. {result.get('error', '')}",
                "sources": [],
                "sql_used": result.get("sql"),
                "analytics_used": None,
                "query_type": query_type,
                "method": "sql_query_failed",
                "metadata": result
            }
        
        # Step 5: Format results for LLM
        results = result.get("results", [])
        sql_used = result.get("sql")
        
        # Build context for LLM - pass all results for candidate listings
        # For candidate listing queries, we need ALL results, not just first 5
        context = {
            "sql_query": sql_used,
            "results_count": len(results),
            "results_preview": results if len(results) <= 10 else results[:10],  # First 10 for preview, but full results passed separately
            "results": results,  # All results for the LLM to use
            "operation": result.get("operation")
        }
        
        # Generate natural language answer
        prompt = build_context_prompt(
            retrieved_docs=[],
            user_query=query,
            analytics_data=context
        )
        
        answer = await self.llm.ainvoke(prompt)
        
        return {
            "answer": answer,
            "sources": results,
            "sql_used": sql_used,
            "analytics_used": context,
            "query_type": query_type,
            "method": "sqlite_structured_query",
            "metadata": {
                "results_count": len(results),
                "operation": result.get("operation"),
                "confidence": intent_result.get("confidence", 0.85)
            }
        }
    
    async def _handle_semantic_search(self, 
                                     query: str, 
                                     filters: Optional[Dict],
                                     top_k: int) -> Dict[str, Any]:
        """
        Handle semantic search using vector embeddings.
        
        Step 1: Retrieve similar documents
        Step 2: Re-rank results
        Step 3: Generate answer with context
        
        Args:
            query: Natural language query
            filters: Optional metadata filters
            top_k: Number of retrieval results
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Handling semantic search: {query} (k={top_k})")
        
        # Retrieve similar documents with re-ranking
        retrieved_docs = self.retrieval.retrieve(
            query=query,
            k=top_k * 2,  # Get more for re-ranking
            filters=filters,
            use_reranking=True,
            query_type="SEMANTIC_SEARCH"
        )
        
        # Generate answer with context
        prompt = build_context_prompt(
            retrieved_docs=retrieved_docs,
            user_query=query,
            analytics_data=None
        )
        
        answer = await self.llm.ainvoke(prompt)
        
        return {
            "answer": answer,
            "sources": retrieved_docs,
            "sql_used": None,
            "analytics_used": None,
            "query_type": "SEMANTIC_SEARCH",
            "method": "vector_embedding_search_with_reranking",
            "metadata": {
                "retrieved_count": len(retrieved_docs),
                "filters_applied": filters or {},
                "confidence": 0.75
            }
        }
    
    async def _handle_hybrid_query(self,
                                  query: str,
                                  intent_result: Dict[str, Any],
                                  filters: Optional[Dict],
                                  top_k: int) -> Dict[str, Any]:
        """
        Handle complex queries that need both SQL and Vector Search.
        
        Examples:
        - "Find candidates in Kathmandu with law education"
        - "Which party has the most candidates under 30 years old?"
        
        Step 1: Execute SQL for structured part
        Step 2: Execute Vector Search for semantic part
        Step 3: Combine and validate results
        Step 4: Generate unified answer
        
        Args:
            query: Natural language query
            intent_result: Extracted intent and entities
            filters: Optional metadata filters
            top_k: Number of retrieval results
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Handling hybrid query: {query}")
        
        # Parallel execution of SQL and Vector Search
        sql_task = self._handle_sql_query(query, intent_result, filters)
        vector_task = self._handle_semantic_search(query, filters, top_k)
        
        # Run both in parallel
        sql_result, vector_result = await asyncio.gather(
            sql_task,
            vector_task,
            return_exceptions=True
        )
        
        # Combine results
        combined_sources = []
        
        # Add SQL results
        if isinstance(sql_result, dict) and sql_result.get("sources"):
            combined_sources.extend(sql_result["sources"])
        
        # Add vector results
        if isinstance(vector_result, dict) and vector_result.get("sources"):
            combined_sources.extend(vector_result["sources"])
        
        # Combine metadata
        combined_metadata = {
            "sql_used": sql_result.get("sql_used") if isinstance(sql_result, dict) else None,
            "vector_results_count": len(vector_result.get("sources", [])) if isinstance(vector_result, dict) else 0,
            "sql_results_count": len(sql_result.get("sources", [])) if isinstance(sql_result, dict) else 0,
            "combined_results_count": len(combined_sources)
        }
        
        # Generate unified answer
        prompt = f"""
{SYSTEM_PROMPT}

User Query: "{query}"

Database (SQL) Results:
{sql_result.get('answer', 'No database results') if isinstance(sql_result, dict) else 'Error in database query'}

Vector Search Results:
{vector_result.get('answer', 'No vector results') if isinstance(vector_result, dict) else 'Error in vector search'}

Synthesize these results into a comprehensive, accurate answer in both Nepali and English.
If results conflict, mention both.
Focus on providing the most relevant information.
"""
        
        answer = await self.llm.ainvoke(prompt)
        
        return {
            "answer": answer,
            "sources": combined_sources[:20],  # Limit to 20 total
            "sql_used": combined_metadata["sql_used"],
            "analytics_used": sql_result.get("analytics_used") if isinstance(sql_result, dict) else None,
            "query_type": "HYBRID",
            "method": "hybrid_sql_plus_vector",
            "metadata": combined_metadata
        }


# Backward compatibility: Keep old QueryRouter class name
QueryRouter = QueryRouterSQLite
