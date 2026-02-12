"""
Query Classifier Service

Classifies user queries into types for appropriate routing.
"""
import logging
import re
from typing import Literal, Tuple, Optional, Dict, Any
from enum import Enum

from services.llm_service import DeepSeekLLMService

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query type enumeration."""
    EXACT_LOOKUP = "exact_lookup"
    ANALYTICAL = "analytical"
    SEMANTIC_SEARCH = "semantic_search"
    COMPARISON = "comparison"
    AGGREGATION = "aggregation"
    COMPLEX = "complex"
    COUNT = "count"


class QueryClassifier:
    """
    Classifies user queries into types for appropriate routing.
    
    Uses both rule-based patterns and LLM-based classification.
    """
    
    def __init__(self, llm_service: DeepSeekLLMService):
        self.llm = llm_service
        self.patterns = self._build_patterns()
        logger.info("Query classifier initialized")
    
    def _build_patterns(self) -> Dict[QueryType, List[str]]:
        """
        Build regex patterns for each query type.
        
        Returns:
            Dictionary mapping query types to regex patterns
        """
        return {
            QueryType.EXACT_LOOKUP: [
                r'^how many\b',
                r'^count\b',
                r'^number of\b',
                r'^total\b',
                r'^list all\b',
                r'^show me\b',
                r'^find\b',
                r'^get\b',
                r'^who is\b',
                r'^what is\b',
                r'^which\b',
                r'^\d+\b',  # Starting with numbers
            ],
            QueryType.ANALYTICAL: [
                r'\baverage\b',
                r'\bmean\b',
                r'\bmedian\b',
                r'\bmaximum\b',
                r'\bminimum\b',
                r'\bmax\b',
                r'\bmin\b',
                r'\bstdev\b',
                r'\bstandard deviation\b',
                r'\bpercentile\b',
                r'\bdistribution\b',
                r'\btrend\b',
                r'\bpattern\b',
                r'\bstatistics\b',
            ],
            QueryType.COMPARISON: [
                r'\bcompare\b',
                r'\bvs\b',
                r'\bversus\b',
                r'\bdifference\b',
                r'\bbetter\b',
                r'\bworse\b',
                r'\bhigher\b',
                r'\blower\b',
                r'\bmore\b',
                r'\bless\b',
                r'\bgreater\b',
                r'\bfewer\b',
            ],
            QueryType.AGGREGATION: [
                r'\bgroup by\b',
                r'\bbreakdown\b',
                r'\bsummary\b',
                r'\bbreak down\b',
                r'\bby party\b',
                r'\bby district\b',
                r'\bby province\b',
                r'\bcategorize\b',
                r'\bshow all\b',
            ],
        }
    
    def classify(self, query: str) -> Tuple[QueryType, float]:
        """
        Classify query with confidence score.
        
        Args:
            query: User's query string
            
        Returns:
            Tuple of (query_type, confidence_score)
        """
        query_lower = query.lower().strip()
        
        # First, try rule-based pattern matching (faster)
        rule_based_type, confidence = self._classify_by_patterns(query_lower)
        
        # If confidence is high enough (>0.7), return rule-based result
        if confidence > 0.7:
            logger.info(f"Rule-based classification: {rule_based_type} (confidence: {confidence:.2f})")
            return rule_based_type, confidence
        
        # Otherwise, use LLM for classification (more accurate)
        logger.info("Using LLM-based classification")
        return self._classify_by_llm(query)
    
    def _classify_by_patterns(self, query: str) -> Tuple[QueryType, float]:
        """
        Classify using regex patterns.
        
        Args:
            query: Lowercase query string
            
        Returns:
            Tuple of (query_type, confidence_score)
        """
        best_type = QueryType.SEMANTIC_SEARCH
        best_match_count = 0
        total_patterns = sum(len(patterns) for patterns in self.patterns.values())
        
        for query_type, patterns in self.patterns.items():
            match_count = sum(1 for pattern in patterns if re.search(pattern, query))
            
            if match_count > best_match_count:
                best_match_count = match_count
                best_type = query_type
        
        # Calculate confidence based on pattern strength
        if best_match_count > 0:
            confidence = min(0.8, best_match_count / 2.0)
        else:
            confidence = 0.2  # Default to semantic search with low confidence
        
        logger.debug(f"Pattern matching: {best_type} (matches: {best_match_count})")
        return best_type, confidence
    
    def _classify_by_llm(self, query: str) -> Tuple[QueryType, float]:
        """
        Classify using LLM for complex queries.
        
        Args:
            query: Original query string
            
        Returns:
            Tuple of (query_type, confidence_score)
        """
        classification_prompt = f"""Classify the following election data query into one of these categories:

Categories:
- EXACT_LOOKUP: Count, find specific entities, list items. Examples: "How many candidates?", "Find X in Y"
- ANALYTICAL: Statistics, averages, distributions, trends. Examples: "Average age", "Show distribution"
- SEMANTIC_SEARCH: Conceptual questions, similarity-based. Examples: "Candidates with law education", "Rural area candidates"
- COMPARISON: Compare between entities. Examples: "Compare parties", "District A vs District B"
- AGGREGATION: Group and summarize by categories. Examples: "Breakdown by party", "Summary by district"
- COMPLEX: Multi-step queries requiring multiple operations. Examples: "Party with most candidates under 30", "Highest voter district and top party"

Query: "{query}"

Return only the category name and a confidence score (0-1), separated by |.
Format: CATEGORY|CONFIDENCE

Example output: ANALYTICAL|0.85"""
        
        try:
            response = self.llm.invoke(classification_prompt)
            result = response.strip()
            
            # Parse response
            if '|' in result:
                category, confidence_str = result.split('|', 1)
                query_type = QueryType(category.strip().upper())
                confidence = float(confidence_str.strip())
            else:
                # Fallback: try to match category name
                category = result.upper()
                query_type = None
                for qt in QueryType:
                    if qt.value.upper() in category:
                        query_type = qt
                        break
                
                if query_type:
                    confidence = 0.75
                else:
                    query_type = QueryType.SEMANTIC_SEARCH
                    confidence = 0.5
            
            logger.info(f"LLM classification: {query_type} (confidence: {confidence:.2f})")
            return query_type, confidence
            
        except Exception as e:
            logger.error(f"Error in LLM classification: {e}")
            # Fallback to semantic search
            return QueryType.SEMANTIC_SEARCH, 0.3
    
    async def async_classify(self, query: str) -> Tuple[QueryType, float]:
        """
        Async classify query.
        
        Args:
            query: User's query string
            
        Returns:
            Tuple of (query_type, confidence_score)
        """
        query_lower = query.lower().strip()
        
        # Rule-based classification
        rule_based_type, confidence = self._classify_by_patterns(query_lower)
        
        if confidence > 0.7:
            return rule_based_type, confidence
        
        # LLM-based classification
        try:
            response = await self.llm.ainvoke(classification_prompt)
            # Parse and return (same as synchronous version)
            return self._parse_llm_response(response)
        except Exception as e:
            logger.error(f"Error in async LLM classification: {e}")
            return QueryType.SEMANTIC_SEARCH, 0.3
    
    def _parse_llm_response(self, response: str) -> Tuple[QueryType, float]:
        """Parse LLM classification response."""
        result = response.strip()
        
        if '|' in result:
            category, confidence_str = result.split('|', 1)
            query_type = QueryType(category.strip().upper())
            confidence = float(confidence_str.strip())
        else:
            # Try to match category
            category = result.upper()
            query_type = None
            for qt in QueryType:
                if qt.value.upper() in category:
                    query_type = qt
                    break
            
            if query_type:
                confidence = 0.75
            else:
                query_type = QueryType.SEMANTIC_SEARCH
                confidence = 0.5
        
        return query_type, confidence
