"""
SQL Generator Service

Uses LLM to generate SQL queries from natural language.
"""
import logging
from typing import Dict, Any, Optional, Tuple
import json

from .llm_service import DeepSeekLLMService
from .sqlite_service import SQLiteService

try:
    from config.party_mapping import get_party_mapping_context, normalize_party_name
except ImportError:
    # Fallback for testing without config module
    def get_party_mapping_context():
        return ""
    def normalize_party_name(name):
        return name

logger = logging.getLogger(__name__)


class SQLGenerator:
    """
    Generates SQL queries from natural language using LLM.
    
    Provides schema-aware query generation with validation.
    """
    
    def __init__(self, llm: DeepSeekLLMService, sqlite: SQLiteService):
        """
        Initialize SQL generator.
        
        Args:
            llm: LLM service for generation
            sqlite: SQLite service for schema and validation
        """
        self.llm = llm
        self.sqlite = sqlite
        self.schema = sqlite.get_schema_for_prompt()
        logger.info("SQL generator initialized")
    
    async def generate_sql(self, query: str, query_type: str = "auto") -> Dict[str, Any]:
        """
        Generate SQL from natural language query.
        
        Args:
            query: Natural language query
            query_type: 'count', 'aggregate', 'statistics', 'comparison', 'exact_lookup', or 'auto'
            
        Returns:
            Dictionary with sql, params, and metadata
        """
        logger.info(f"Generating SQL for query: '{query}' (type: {query_type})")
        
        # Get schema
        schema = self.sqlite.get_schema_for_prompt()
        
        # Build prompt based on query type
        if query_type == "auto":
            prompt = self._build_auto_query_prompt(query, schema)
        elif query_type == "count":
            prompt = self._build_count_prompt(query, schema)
        elif query_type == "aggregate":
            prompt = self._build_aggregate_prompt(query, schema)
        elif query_type == "statistics":
            prompt = self._build_statistics_prompt(query, schema)
        elif query_type == "comparison":
            prompt = self._build_comparison_prompt(query, schema)
        elif query_type == "exact_lookup":
            prompt = self._build_exact_lookup_prompt(query, schema)
        else:
            prompt = self._build_auto_query_prompt(query, schema)
        
        # Generate SQL
        response = await self.llm.ainvoke(prompt)
        
        # Parse response
        try:
            result = self._parse_sql_response(response)
            
            # Validate SQL
            is_valid, error = self.sqlite.validate_query(result["sql"])
            if not is_valid:
                logger.warning(f"Generated SQL validation failed: {error}")
                # Fallback to a safe query
                result["sql"] = "SELECT * FROM candidates LIMIT 10"
                result["error"] = error
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing SQL response: {e}")
            # Return empty result
            return {
                "sql": None,
                "params": None,
                "table": None,
                "operation": None,
                "error": str(e)
            }
    
    def _build_auto_query_prompt(self, query: str, schema: str) -> str:
        """Build prompt for automatic query type detection."""
        party_context = get_party_mapping_context()
        return f"""You are a SQL query generator for Nepal election data.

{schema}

{party_context}

User Query: "{query}"

Generate an appropriate SQL query to answer this question.

IMPORTANT RULES:
1. Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP)
2. Use LIKE for text matching (e.g., WHERE column LIKE '%value%')
3. Use COUNT(*) for counting
4. Use GROUP BY for aggregation
5. DO NOT add LIMIT for candidate listing queries - return ALL results. Only limit for sample data queries that don't specify a specific area/district
6. For full-text search, use the *_fts tables with MATCH operator
7. Both Nepali and English columns are available
8. CRITICAL: When filtering by party name, ALWAYS use the OFFICIAL NEPALI NAME from the mapping above
9. Search in both `party` (Nepali) and `party_english` columns for party filters

Return a JSON response with this structure:
{{
    "sql": "SELECT ...",
    "params": null or [param1, param2],
    "table": "candidates" or "voting_centers",
    "operation": "count", "aggregate", "statistics", "comparison", "exact_lookup", or "search"
}}

JSON only, no explanation."""
    
    def _build_count_prompt(self, query: str, schema: str) -> str:
        """Build prompt for count queries."""
        return f"""You are a SQL query generator for Nepal election data.

{schema}

User Query: "{query}"

This is a COUNT query. Generate SQL to count records.

IMPORTANT RULES:
1. Use COUNT(*) to count
2. Use WHERE clauses with LIKE for filtering
3. Use the appropriate table (candidates or voting_centers)

Return a JSON response:
{{
    "sql": "SELECT COUNT(*) as count FROM ...",
    "params": null or [param1, param2],
    "table": "candidates" or "voting_centers",
    "operation": "count"
}}

JSON only, no explanation."""
    
    def _build_aggregate_prompt(self, query: str, schema: str) -> str:
        """Build prompt for aggregation queries."""
        return f"""You are a SQL query generator for Nepal election data.

{schema}

User Query: "{query}"

This is an AGGREGATION query. Generate SQL to group and count records.

IMPORTANT RULES:
1. Use GROUP BY to aggregate by a field
2. Use COUNT(*) to get counts per group
3. ORDER BY COUNT DESC to show most common first
4. Use the appropriate table (candidates or voting_centers)

Return a JSON response:
{{
    "sql": "SELECT field, COUNT(*) as count FROM ... GROUP BY field ...",
    "params": null or [param1, param2],
    "table": "candidates" or "voting_centers",
    "operation": "aggregate"
}}

JSON only, no explanation."""
    
    def _build_statistics_prompt(self, query: str, schema: str) -> str:
        """Build prompt for statistics queries."""
        return f"""You are a SQL query generator for Nepal election data.

{schema}

User Query: "{query}"

This is a STATISTICS query. Generate SQL to calculate statistics (avg, min, max, etc).

IMPORTANT RULES:
1. Use AVG(), MIN(), MAX(), STDDEV() for numeric fields
2. Filter with WHERE if needed
3. Use the appropriate table (candidates or voting_centers)
4. Numeric fields include: voter_count, area_no, ward_no, polling_center_code

Return a JSON response:
{{
    "sql": "SELECT AVG(field) as avg, MIN(field) as min, MAX(field) as max FROM ...",
    "params": null or [param1, param2],
    "table": "candidates" or "voting_centers",
    "operation": "statistics"
}}

JSON only, no explanation."""
    
    def _build_comparison_prompt(self, query: str, schema: str) -> str:
        """Build prompt for comparison queries."""
        return f"""You are a SQL query generator for Nepal election data.

{schema}

User Query: "{query}"

This is a COMPARISON query. Generate SQL to compare entities.

IMPORTANT RULES:
1. Use CASE WHEN or separate SELECTs for comparison
2. Or return data grouped by the comparison field
3. Use COUNT(*) or AVG() as the comparison metric
4. Use the appropriate table (candidates or voting_centers)

Return a JSON response:
{{
    "sql": "SELECT ...",
    "params": null or [param1, param2],
    "table": "candidates" or "voting_centers",
    "operation": "comparison"
}}

JSON only, no explanation."""
    
    def _build_exact_lookup_prompt(self, query: str, schema: str) -> str:
        """Build prompt for exact lookup queries."""
        return f"""You are a SQL query generator for Nepal election data.

{schema}

User Query: "{query}"

This is an EXACT LOOKUP query. Generate SQL to find specific records.

IMPORTANT RULES:
1. Use LIKE with wildcards for text matching (e.g., WHERE column LIKE '%value%')
2. DO NOT limit results - return ALL matching records. Candidates may be 20-50+ for a single area
3. Use the appropriate table (candidates or voting_centers)
4. Search in both Nepali and English columns

SPECIAL PATTERNS TO RECOGNIZE:
- "District X" or "District X candidates": Filter by district column
- "Area 4" or "Number 4": This refers to area_no column (NOT id)
- "Kathmandu 4" or "District 4": Means district = Kathmandu AND area_no = 4
- For numeric area patterns: Use area_no column with = operator
- For district + area: Combine with AND (e.g., district LIKE '%Kathmandu%' AND area_no = 4)

Column mappings:
- district / district_in_english: For location names (Kathmandu, Lalitpur, etc.)
- area_no: Numeric area number (1, 2, 3, 4, etc.)
- candidate_full_name: Candidate names
- political_party / political_party_in_english: Party names

Return a JSON response:
{{
    "sql": "SELECT * FROM ... WHERE column LIKE ? OR column2 LIKE ? AND area_no = ?",
    "params": ["%value1%", "%value2%", 4],
    "table": "candidates" or "voting_centers",
    "operation": "exact_lookup"
}}

JSON only, no explanation."""
    
    def _parse_sql_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into SQL result."""
        # Try to extract JSON from response
        try:
            # Find JSON object in response
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            
            result = json.loads(json_str)
            
            # Validate required fields
            if "sql" not in result:
                raise ValueError("Missing 'sql' field in response")
            
            # Set defaults
            result.setdefault("params", None)
            result.setdefault("table", None)
            result.setdefault("operation", "search")
            result.setdefault("error", None)
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse SQL response: {e}")
            logger.debug(f"Response was: {response}")
            
            # Try to extract SQL directly if JSON parsing fails
            if "SELECT" in response.upper():
                # Extract SQL from response
                sql_start = response.upper().find("SELECT")
                sql_end = response.find(";")
                sql = response[sql_start:sql_end if sql_end > 0 else None]
                return {
                    "sql": sql.strip(),
                    "params": None,
                    "table": None,
                    "operation": "search",
                    "error": "JSON parse failed, extracted SQL directly"
                }
            
            # Fallback
            return {
                "sql": None,
                "params": None,
                "table": None,
                "operation": "search",
                "error": str(e)
            }
    
    async def generate_and_execute(self, query: str, query_type: str = "auto") -> Tuple[bool, Any]:
        """
        Generate SQL and execute it.

        Args:
            query: Natural language query
            query_type: Query type hint

        Returns:
            Tuple of (success, result)
        """
        try:
            # Generate SQL
            generated = await self.generate_sql(query, query_type)

            if generated.get("error"):
                return False, {"error": generated["error"]}

            sql = generated["sql"]
            params = generated.get("params")

            # Validate
            is_valid, error = self.sqlite.validate_query(sql)
            if not is_valid:
                return False, {"error": f"SQL validation failed: {error}"}

            # Handle parameter mismatches
            placeholder_count = sql.count('?')

            # Case 1: SQL has placeholders but no params provided
            if placeholder_count > 0 and not params:
                logger.warning(f"SQL has {placeholder_count} placeholder(s) but no params provided.")
                logger.debug(f"SQL: {sql}\nThis may be due to LLM generating SQL with placeholders but no params.")
                return False, {"error": f"SQL has {placeholder_count} placeholder(s) but no parameters provided"}

            # Case 2: SQL has no placeholders but params provided
            if params and placeholder_count == 0:
                logger.warning(f"SQL contains no placeholders but params were provided. Ignoring params.")
                logger.debug(f"SQL: {sql}\nParams: {params}")
                params = None

            # Case 3: Mismatch between placeholder count and params length
            if params and placeholder_count > 0:
                params_length = len(params) if isinstance(params, (list, tuple)) else 1
                if params_length != placeholder_count:
                    logger.warning(f"Parameter count mismatch: {placeholder_count} placeholders vs {params_length} params")
                    logger.debug(f"SQL: {sql}\nParams: {params}")

            # Execute
            results = self.sqlite.execute_query(sql, params=params, fetch="all")

            return True, {
                "results": results,
                "sql": sql,
                "params": params,
                "operation": generated["operation"],
                "table": generated["table"]
            }

        except Exception as e:
            logger.error(f"Error in generate_and_execute: {e}", exc_info=True)
            return False, {"error": str(e)}


class IntentExtractor:
    """
    Extracts intent and entities from user queries.
    
    Enhances query classification with structured entity extraction.
    """
    
    def __init__(self, llm: DeepSeekLLMService):
        """
        Initialize intent extractor.
        
        Args:
            llm: LLM service for extraction
        """
        self.llm = llm
        logger.info("Intent extractor initialized")
    
    async def extract(self, query: str) -> Dict[str, Any]:
        """
        Extract intent and entities from query.
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with intent, entities, and query_type
        """
        party_context = get_party_mapping_context()
        prompt = f"""Analyze this query about Nepal election data and extract structured information.

{party_context}

Query: "{query}"

Extract and return JSON with this structure:
{{
    "intent": "count", "lookup", "compare", "aggregate", "statistics", "search", "complex",
    "entities": {{
        "target": "candidates" or "voting_centers" or "both",
        "district": ["district_name"] or null,
        "province": ["province_name"] or null,
        "party": ["party_name"] or null,
        "gender": ["male" or "female"] or null,
        "area_no": 1, 2, 3, 4, etc. or null (numeric area number),
        "field": "field_name" for aggregations,
        "metric": "count", "average", "sum", etc.
    }},
    "query_type": "EXACT_LOOKUP", "ANALYTICAL", "COMPARISON", "AGGREGATION", "SEMANTIC_SEARCH", "COMPLEX",
    "confidence": 0.0-1.0
}}

Rules:
- Detect if the query is structured (can be answered with SQL) or semantic (needs embeddings)
- Structured queries involve counts, exact matches, comparisons, aggregations, statistics
- Semantic queries involve conceptual matching, education type, rural/urban, etc.
- Both Nepali and English names may appear
- Confidence is how certain you are about the classification
- CRITICAL: When extracting party names, map aliases to OFFICIAL NEPALI NAMES from the party mapping above

IMPORTANT PATTERN RECOGNITION:
- "Kathmandu 4" or "District 4" means district=Kathmandu AND area_no=4
- "Area 4" means area_no=4 (NOT id=4)
- "Number 4" or "4 candidates" with district prefix means area_no=4
- Extract numeric values that follow district names as area_no
- When party name appears (NC, UML, RSP, etc.), ALWAYS use official Nepali name from mapping
- "total X in Y" or "Total X in Y" → count query (returns COUNT only, NOT full rows)
- "how many X in Y" or "How many X in Y" → count query (returns COUNT only)
- "count X in Y" or "Count X in Y" → count query (returns COUNT only)
- "number of X in Y" or "Number of X in Y" → count query (returns COUNT only)
- PROVINCE NAMES: "Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim" → these are PROVINCES, map to 'State' column
- DISTRICT NAMES: "Kathmandu", "Lalitpur", "Bhaktapur", etc. → these are DISTRICTS, map to 'District' column

DISTINGUISHING RULES:
- Use "count" as intent when query asks for a total number/quantity
- Use "exact_lookup" only when: asking for LIST of candidates ("show me candidates", "list all candidates")
- Use "aggregation" when: asking for COUNTS with grouping ("total by party", "breakdown by district")
- For count queries: SQL should use COUNT(*) and return a single number, not all rows
- CRITICAL: Extract province names correctly - Koshi, Madhesh, Bagmati, etc. map to entities.province

JSON only, no explanation."""
        
        response = await self.llm.ainvoke(prompt)
        
        try:
            # Extract JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            
            result = json.loads(json_str)
            
            # Set defaults
            result.setdefault("intent", "search")
            result.setdefault("entities", {})
            result.setdefault("query_type", "SEMANTIC_SEARCH")
            result.setdefault("confidence", 0.5)
            result["entities"].setdefault("target", "auto")
            
            # CRITICAL: Map intent to correct query_type for proper routing
            # This ensures count queries use the efficient count handler instead of full data retrieval
            intent = result.get("intent", "")
            if intent == "count":
                result["query_type"] = "COUNT"
            elif intent == "aggregate":
                result["query_type"] = "AGGREGATION"
            elif intent == "statistics":
                result["query_type"] = "ANALYTICAL"
            elif intent == "compare":
                result["query_type"] = "COMPARISON"
            elif intent == "complex":
                result["query_type"] = "COMPLEX"
            elif intent == "search":
                # Keep SEMANTIC_SEARCH for search
                pass
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse intent extraction: {e}")
            
            # Fallback
            return {
                "intent": "search",
                "entities": {"target": "auto"},
                "query_type": "SEMANTIC_SEARCH",
                "confidence": 0.3,
                "error": str(e)
            }
    
    def is_structured_query(self, query: str, intent_result: Optional[Dict] = None) -> bool:
        """
        Determine if query can be answered with SQL or needs vector search.
        
        Args:
            query: User's natural language query
            intent_result: Optional pre-computed intent result
            
        Returns:
            True if SQL can answer, False if vector search needed
        """
        if intent_result:
            query_type = intent_result.get("query_type", "SEMANTIC_SEARCH")
            confidence = intent_result.get("confidence", 0.5)
            
            # Structured query types
            structured_types = ["EXACT_LOOKUP", "ANALYTICAL", "COMPARISON", "AGGREGATION"]
            
            if query_type in structured_types and confidence >= 0.6:
                return True
        
        # Keywords that suggest semantic search
        semantic_keywords = [
            "education", "rural", "urban", "background", "qualification",
            "similar", "like", "type of", "kind of", "related to"
        ]
        
        query_lower = query.lower()
        for keyword in semantic_keywords:
            if keyword in query_lower:
                return False
        
        # Keywords that suggest structured query
        structured_keywords = [
            "count", "how many", "total", "number of",
            "compare", "between", "versus", "vs",
            "average", "mean", "median", "maximum", "minimum",
            "top", "highest", "lowest", "most", "least"
        ]
        
        for keyword in structured_keywords:
            if keyword in query_lower:
                return True
        
        # Default to semantic search
        return False
