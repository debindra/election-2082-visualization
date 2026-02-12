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
from services.redis_cache import RedisCacheService
from prompts.system_prompt import SYSTEM_PROMPT, build_context_prompt

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Routes queries to appropriate handler based on classification.
    
    Hybrid approach combining SQLite for structured queries and 
    vector search for semantic queries.
    
    New Architecture:
    User → Intent + Entity Extraction → Structured? → SQL / Vector Search → Combine → LLM → Response
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
        
        # Initialize Redis cache
        self.cache = RedisCacheService()
        if self.cache.enabled:
            logger.info("Query result caching enabled")
        
        # Province name mapping (English -> Nepali)
        self.province_mapping = {
            "koshi": "कोशी प्रदेश",
            "koshī": "कोशी प्रदेश",
            "madhesh": "मधेश प्रदेश",
            "bagmati": "बागमती प्रदेश",
            "gandaki": "गण्डकी प्रदेश",
            "lumbini": "लुम्बिनी प्रदेश",
            "karnali": "कर्णाली प्रदेश",
            "sudurpashchim": "सुदूरपश्चिम प्रदेश",
        }
        
        # District name mapping (English -> Nepali)
        self.district_mapping = {
            # Achham District
            "achham": "अछाम",
            # Arghakhachi District  
            "arghakhachi": "अर्घाखाँची",
            # Bara District
            "bara": "बारा",
            # Bardia District
            "bardia": "बर्दिया",
            # Bhaktapur District
            "bhaktapur": "भक्तपुर",
            # Chitwan District
            "chitwan": "चितवन",
            # Dadeldhura District
            "dadeldhura": "डडेलधुरा",
            # Dang District
            "dang": "दाङ",
            # Dailekh District
            "dailekh": "दैलेख",
            "dhankuta": "धनकुटा",
            # Dolkha District
            "dolkha": "दोलखा",
            # Dolpa District
            "dolpa": "डोल्पा",
            # Doti District
            "doti": "डोटी",
            # Gorkha District
            "gorakha": "गोरखा",
            # Gulmi District
            "gulmi": "गुल्मी",
            # Humla District
            "humla": "हुम्ला",
            # Ilam District
            "ilam": "इलाम",
            # Jajarkot District
            "jajarkot": "जाजरकोट",
            # Jhapa District
            "jhapa": "झापा",
            # Jumla District
            "jumla": "जुम्ला",
            # Kailali District
            "kailali": "कैलाली",
            # Kalikot District
            "kalikot": "कालिकोट",
            # Kanchanpur District
            "kanchanpur": "कञ्चनपुर",
            # Kapilbastu District
            "kapilbastu": "कपिलबस्तु",
            # Kaski District
            "kaski": "कास्की",
            "kathmandu": "काठमाडौं",
            # Kavrepalanchok District
            "kavrepalanchok": "काभ्रेपलाञ्चोक",
            # Khotang District
            "khotang": "खोटाङ",
            # Lalitpur District
            "lalitpur": "ललितपुर",
            # Lamjung District
            "lamjung": "लमजुङ",
            # Mahottari District
            "mahottari": "महोत्तरी",
            # Makawanpur District
            "makawanpur": "मकवानपुर",
            # Manang District
            "manang": "मनाङ",
            # Morang District
            "morang": "मोरङ",
            # Mugu District
            "mugu": "मुगु",
            # Mustang District
            "mustang": "मुस्ताङ",
            # Myagdi District
            "myagdi": "म्याग्दी",
            # Nawalparasi District (Nawalparasi)
            "nawalparasi": "नवलपरासी (बर्दघाट सुस्ता पश्चिम)",
            # Nawalparasi District (Nawalparasi variant)
            "nawalparasi2": "नवलपरासी (बर्दघाट सुस्ता पूर्व)",
            # Nuwakot District
            "nuwakot": "नुवाकोट",
            # Okhaldhunga District
            "okhaldhunga": "ओखलढुंगा",
            # Palpa District
            "palpa": "पाल्पा",
            # Panchthar District
            "panchthar": "पाँचथर",
            # Parbat District
            "parbat": "पर्वत",
            # Parsa District
            "parsa": "पर्सा",
            # Pyuthan District
            "pyuthan": "प्यूठान",
            # Ramechhap District
            "ramechhap": "रामेछाप",
            # Rasuwa District
            "rasuwa": "रसुवा",
            # Rautahat District
            "rautahat": "रौतहट",
            # Rolpa District
            "rolpa": "रोल्पा",
            # Rukum District (with brackets)
            "rukum": "रुकुम (पश्चिम भाग)",
            # Rukum District (variant)
            "rukum2": "रुकुम (पूर्वी भाग)",
            # Rupandehi District
            "rupandehi": "रूपन्देही",
            # Salyan District
            "salyan": "सल्यान",
            # Sankhuwasabha District
            "sankhuwasabha": "संखुवासभा",
            # Saptari District
            "saptari": "सप्तरी",
            # Siraha District
            "siraha": "सिराहा",
            # Siraha District (variation)
            "siraha2": "सिराहा",
            # Solukhumbu District
            "solukhumbu": "सोलुखुम्बु",
            # Sunsari District
            "sunsari": "सुनसरी",
            # Sunseri District
            "sunseri": "सुनसरी",
            # Unsaree District
            "unsaree": "सुनसरी",
            # Unsari District
            "unsari": "सुनसरी",
            # Surkhet District
            "surkhet": "सुर्खेत",
            # Syangja District
            "syangja": "स्याङजा",
            # Tanahun District
            "tanahun": "तनहुँ",
            # Taplejung District
            "taplejung": "ताप्लेजुङ",
            # Terhathum District
            "terhathum": "तेह्रथुम",
            # Udaypur District
            "udaypur": "उदयपुर",
            # Humla District (duplicate - removed below)
            # "humla": "हुम्ला",
        }
        
        logger.info(f"Query router (SQLite + Vector) initialized")
    
    async def _handle_count_query(self,
                               query: str,
                               intent_result: Dict[str, Any],
                               entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle count queries using SQLite count methods directly.
        
        This prevents fetching all rows when only a count is needed,
        which was causing token limit errors for large datasets.
        
        Args:
            query: Natural language query
            intent_result: Extracted intent and entities
            entities: Extracted entities from query
            
        Returns:
            Dictionary with answer and metadata (no full sources for count queries)
        """
        logger.info(f"Handling count query: {query}")
        
        # Extract target and filters
        target = entities.get('target', 'candidates')
        filters_dict = {}
        
        # Map entity names to correct database columns
        # Note: Database uses 'State' for province, not 'province'
        province_name = entities.get('province')
        if province_name:
            # Handle both string and list types
            if isinstance(province_name, list):
                if len(province_name) > 0:
                    province_name = province_name[0]
                else:
                    province_name = None
            
            if province_name:
                # Normalize province name to Nepali
                normalized_province = self.province_mapping.get(province_name.lower(), province_name)
                filters_dict['State'] = normalized_province
                logger.info(f"Normalized province '{province_name}' -> '{normalized_province}'")
        
        # Handle district (could be list)
        district_name = entities.get('district')
        if district_name:
            if isinstance(district_name, list):
                if len(district_name) > 0:
                    district_name = district_name[0]
                else:
                    district_name = None
            
            if district_name:
                # Normalize district name to Nepali
                normalized_district = self.district_mapping.get(district_name.lower(), district_name)
                filters_dict['District'] = normalized_district
                logger.info(f"Normalized district '{district_name}' -> '{normalized_district}'")
        
        # Handle party (could be list)
        party_name = entities.get('party')
        if party_name:
            if isinstance(party_name, list) and len(party_name) > 0:
                filters_dict['political_party'] = party_name[0]
            elif isinstance(party_name, str):
                filters_dict['political_party'] = party_name
        
        # Handle area_no (constituency number)
        area_no = entities.get('area_no')
        if area_no is not None:
            # Handle both string and list types
            if isinstance(area_no, list):
                if len(area_no) > 0:
                    area_no = area_no[0]
                else:
                    area_no = None
            
            if area_no:
                # Convert to int if it's a string
                try:
                    area_no_int = int(area_no)
                    filters_dict['area_no'] = area_no_int
                    logger.info(f"Added area_no filter: {area_no_int}")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid area_no value: {area_no}, skipping filter")
        
        # Use SQLite's count methods - NO full data retrieval
        count = 0
        if target == "candidates":
            count = self.sqlite.count_candidates(filters_dict)
        elif target == "voting_centers":
            count = self.sqlite.count_voting_centers(filters_dict)
        
        # Build minimal context for LLM - only the count number
        context = {
            "sql_query": f"SELECT COUNT(*) FROM {target} WHERE ...",
            "results_count": count,
            "results": [],  # Empty - no full rows needed
            "operation": "count",
            "count_only": True  # Flag for prompt building
        }
        
        # Generate answer with count only
        prompt = build_context_prompt(
            retrieved_docs=[],
            user_query=query,
            analytics_data=context,
            entities=entities
        )
        
        answer = await self.llm.ainvoke(prompt)
        
        return {
            "answer": answer,
            "sources": [],  # No sources needed for count queries
            "sql_used": context["sql_query"],
            "analytics_used": context,
            "query_type": "COUNT",
            "intent": "count",
            "entities": entities,
            "method": "sqlite_count_query",
            "metadata": {
                "results_count": count,
                "operation": "count"
            }
        }
    
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
        logger.info(f"Routing query: \'{query}\'")
        
        # Check cache first
        if self.cache.enabled:
            cached_result = self.cache.get_cached_query_result(query, filters or {})
            if cached_result:
                logger.info("Query result cache hit")
                return cached_result
        
        # Step 1: Intent + Entity Extraction
        intent_result = await self.intent_extractor.extract(query)
        logger.info(f"Intent: {intent_result.get('intent')}, "
                   f"Query Type: {intent_result.get('query_type')}, "
                   f"Confidence: {intent_result.get('confidence'):.2f}")
        
        # Extract intent and entities for response
        intent = intent_result.get('intent')
        entities = intent_result.get('entities', {})
        
        # Step 2: Is Structured?
        is_structured = self.intent_extractor.is_structured_query(query, intent_result)
        
        logger.info(f"Query routing: {'SQL (Structured)' if is_structured else 'Vector (Semantic)'}")
        
        # Step 3: Route and Execute
        try:
            # NEW: Check query type and route accordingly
            query_type = intent_result.get("query_type", "SEMANTIC_SEARCH")
            intent = intent_result.get("intent", "")
            
            # Count queries → use dedicated count handler
            # Check both query_type and intent for robustness
            is_count_query = (query_type == "COUNT" or intent == "count")
            
            if is_count_query:
                logger.info("COUNT query detected, routing to count handler")
                result = await self._handle_count_query(query, intent_result, entities)
            # Aggregation queries → use dedicated aggregation handler
            elif query_type == "AGGREGATION":
                logger.info("AGGREGATION query detected, routing to aggregation handler")
                result = await self._handle_sql_query(query, intent_result, filters, intent, entities)
            elif is_structured:
                # Use SQLite for structured queries
                result = await self._handle_sql_query(query, intent_result, filters, intent, entities)
            else:
                # Use Vector Search for semantic queries
                result = await self._handle_semantic_search(query, filters, top_k, intent, entities)
            
            # Cache the result
            if self.cache.enabled:
                self.cache.cache_query_result(query, filters or {}, result)
            
            return result
                
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            error_result = {
                "answer": f"Sorry, there was an error processing your query: {str(e)}",
                "sources": [],
                "sql_used": None,
                "analytics_used": None,
                "query_type": intent_result.get("query_type", "UNKNOWN"),
                "intent": intent,
                "entities": entities,
                "method": "error",
                "metadata": {"error": str(e)}
            }
            # Don't cache errors
            return error_result
    
    async def _handle_sql_query(self,
                               query: str,
                               intent_result: Dict[str, Any],
                               filters: Optional[Dict],
                               intent: str,
                               entities: Dict[str, Any]) -> Dict[str, Any]:
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
            intent: Query intent (polling, candidate, etc.)
            entities: Extracted entities from the query
            
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
                "intent": intent,
                "entities": entities,
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
            analytics_data=context,
            entities=entities
        )
        
        answer = await self.llm.ainvoke(prompt)
        
        return {
            "answer": answer,
            "sources": results,
            "sql_used": sql_used,
            "analytics_used": context,
            "query_type": query_type,
            "intent": intent,
            "entities": entities,
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
                                     top_k: int,
                                     intent: str,
                                     entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle semantic search using vector embeddings.

        Step 1: Retrieve similar documents
        Step 2: Re-rank results
        Step 3: Generate answer with context

        Args:
            query: Natural language query
            filters: Optional metadata filters
            top_k: Number of retrieval results
            intent: Query intent (polling, candidate, etc.)
            entities: Extracted entities from the query

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
            analytics_data=None,
            entities=entities
        )
        
        answer = await self.llm.ainvoke(prompt)
        
        return {
            "answer": answer,
            "sources": retrieved_docs,
            "sql_used": None,
            "analytics_used": None,
            "query_type": "SEMANTIC_SEARCH",
            "intent": intent,
            "entities": entities,
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
                                  top_k: int,
                                  intent: str,
                                  entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle complex queries that need both SQL and Vector Search.
        
        Examples:
        - "Find candidates in Kathmandu with law education"
        - "Which party has most candidates under 30 years old?"
        
        Step 1: Execute SQL for structured part
        Step 2: Execute Vector Search for semantic part
        Step 3: Combine and validate results
        Step 4: Generate unified answer
        
        Args:
            query: Natural language query
            intent_result: Extracted intent and entities
            filters: Optional metadata filters
            top_k: Number of retrieval results
            intent: Query intent (polling, candidate, etc.)
            entities: Extracted entities from the query
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Handling hybrid query: {query}")
        
        # Parallel execution of SQL and Vector Search
        sql_task = self._handle_sql_query(query, intent_result, filters, intent, entities)
        vector_task = self._handle_semantic_search(query, filters, top_k, intent, entities)
        
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
            "intent": intent,
            "entities": entities,
            "method": "hybrid_sql_plus_vector",
            "metadata": combined_metadata
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return self.cache.get_stats() if self.cache else {"enabled": False}
    
    def invalidate_cache(self) -> bool:
        """
        Invalidate all query cache.
        
        Returns:
            True if successful
        """
        if self.cache:
            return self.cache.invalidate_query_cache()
        return False
