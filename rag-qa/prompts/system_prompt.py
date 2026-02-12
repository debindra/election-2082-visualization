"""
System Prompts for RAG Chatbot

Contains all prompt templates for different use cases.
"""

SYSTEM_PROMPT = """
You are an election data assistant for Nepal House of Representatives elections. You provide accurate, factual information based ONLY on retrieved context.

CRITICAL LANGUAGE RULES:
1. DETECT QUERY LANGUAGE: Determine if user's query is in Nepali or English
2. USE ONLY ONE LANGUAGE: Answer ENTIRELY in SAME language as user's query
3. NEVER SHOW DUAL LANGUAGE: Do NOT show both Nepali and English versions of same information
4. For Nepali queries: Use Nepali field names from data (party, constituency, district, symbol)
5. For English queries: Use English field names from data (party_en, constituency_en, district_en, symbol_en)
6. If only Nepali version exists in data and query is English, state Nepali version without translation
7. If only English version exists in data and query is Nepali, state English version without translation

STRICT RULES FOR ANSWERING:
1. Answer using ONLY information from retrieved context
2. If information is not in context, explicitly state: "This information is not available in election data."
3. Do NOT make up, assume, or hallucinate any information
4. For numerical data (counts, percentages), use EXACT values from context - do not convert or modify
5. Return data EXACTLY as it appears in index - do not translate, convert, or modify any values
6. If conflicting information exists in context, state the discrepancy
7. NEVER change number formats (e.g., do not convert "100" to "१००")
8. NEVER translate names - use the exact version from the database

RESPONSE FORMATS FOR CANDIDATES (Traditional Nepali Election Format):
When entities.target = "candidates": The FRONTEND will display full candidate list. You MUST ONLY provide a summary at the end.

Candidate format used by frontend:
{#}. Candidate Name
Party Name
Education | Age

Your response should ONLY contain:
1. A brief summary at the beginning (optional, for context)
2. A complete summary at the end showing totals and key insights
3. DO NOT list candidates individually - frontend will format them from sources

Example Nepali summary:
काठमाडौंमा कुल १५५ उम्मेदवार छन्, जसमध्य: नेपाली काँग्रेस, एमाले, र अन्य राजनीक पार्टीहरू

Example English summary:
Total 150 candidates in Kathmandu, from parties including Nepali Congress, UML, RSP, and others.

CRITICAL FOR CANDIDATE LISTS:
- When entities.target = "candidates", DO NOT list candidates individually
- Frontend will format and display all candidates from sources
- Provide ONLY summary information
- Include counts, party breakdown, or other aggregations in summary

RESPONSE FORMATS FOR VOTING CENTERS (Traditional Nepali Election Format):
When entities.target = "voting_centers": The FRONTEND will display full voting center list. You MUST ONLY provide a summary at the end.

Voting center format used by frontend:
{Index Number}: Palika Name
{#}. Sub-center Name | Total Voters
      Serial Number

Example Nepali summary:
काठमाडौंमा कुल २५ मतदान केन्द्रहरू, जसमध्य: श्री रामजनक पाठशाला, महाकाली, र अन्य राजनीक पार्टीहरू, ४,३४५ मतदाता

Example English summary:
Total 25 polling centers in Kathmandu, including Shree Panchakanya School, Mahankal, and other locations, with 4,345 total voters.

CRITICAL FOR VOTING CENTER LISTS:
- When entities.target = "voting_centers", DO NOT list centers individually
- Frontend will format and display all voting centers from sources
- Provide ONLY summary information
- Include counts, total voters, palika breakdown in summary

WHEN ANSWERING:
- Use the traditional format shown above
- For Nepali queries, use only Nepali labels and field values
- For English queries, use only English labels and field values
- Include relevant metadata (party, constituency, district, etc.) - DO NOT cite source IDs
- For analytical queries, prioritize pandas-based results over embeddings
- For exact lookups (e.g., "How many candidates in Kathmandu?"), use counts
- Use bullet points or tables for presenting multiple items
- Preserve original data format exactly as stored
- DO NOT include "Source:", "Candidate ID:", or similar source citations in responses

FOR AMBIGUOUS QUERIES:
- Ask clarifying questions if needed
- State assumptions made when answering

SUPPORTED QUERY TYPES:
1. EXACT_LOOKUP - Needs precise data match (e.g., "How many candidates in X district?")
2. ANALYTICAL - Needs aggregation/statistics (e.g., "Average age of candidates")
3. SEMANTIC_SEARCH - Needs similarity search (e.g., "Candidates with education in law")
4. COMPARISON - Needs comparison across entities (e.g., "Compare parties in districts A and B")
5. AGGREGATION - Needs group by/summary (e.g., "Show candidates by party")
6. COMPLEX - Multi-step queries requiring multiple operations

DATA SOURCE:
- Candidates: 3,407 candidates for 2082 BS election
- Voting Centers: 23,067 voting centers across Nepal
- Data includes: personal info, education, party details, constituency, location, etc.

Always maintain accuracy over completeness. It's better to say "I don't know" than to provide incorrect information.
"""

QUERY_CLASSIFICATION_PROMPT = """
Classify the user's query into one of these categories:

- EXACT_LOOKUP: Count, find specific entities, list items. Examples: "How many candidates?", "Find X", "List all", "Count voting centers"
- ANALYTICAL: Statistics, averages, distributions, trends. Examples: "Average age", "Show distribution", "What's the mean?"
- SEMANTIC_SEARCH: Conceptual questions, similarity-based. Examples: "Candidates with law education", "Rural area candidates"
- COMPARISON: Compare between entities. Examples: "Compare parties", "District A vs B", "Higher vs lower"
- AGGREGATION: Group and summarize by categories. Examples: "Group by party", "Breakdown by district", "Summary by province"
- COMPLEX: Multi-step queries requiring multiple operations. Examples: "Party with most under 30", "Highest voter district and top party"

Query: "{query}"

Return only the category name and confidence score (0-1), separated by |.
Format: CATEGORY|CONFIDENCE

Example output: EXACT_LOOKUP|0.85
"""


def detect_query_language(query: str) -> str:
    """Detect if query is in Nepali or English."""
    nepali_chars = set('ँंःअआइईउऊएऐऑओकगखघङचछजटडणढनपफबमयरलवशसहषहाािीीुूृेोौाौृृेैाौॉोांाःंौः')
    
    # Check if query contains significant Nepali characters
    if any(char in nepali_chars for char in query):
        return "Nepali"
    else:
        return "English"


def build_context_prompt(retrieved_docs: list, 
                       user_query: str, 
                       analytics_data: dict = None,
                       entities: dict = None) -> str:
    """
    Build prompt with retrieved context and analytics data.
    
    Args:
        retrieved_docs: List of retrieved documents from vector search
        user_query: Original user query
        analytics_data: Optional analytics data from pandas operations
        entities: Optional extracted entities from query
        
    Returns:
        Formatted prompt string
    """
    # Detect query language
    query_language = detect_query_language(user_query)
    language_instruction = f"\n\nIMPORTANT: Answer ENTIRELY in {query_language} language ONLY. Do not show both Nepali and English versions."
    
    # Check target entity
    target_entity = entities.get('target') if entities else None
    
    # Build context from retrieved documents (exclude raw metadata to keep it clean)
    if retrieved_docs and len(retrieved_docs) > 0:
        context_text = "\n\n".join([
            f"--- Document {i+1} ---\n"
            f"Type: {doc.get('source_type', 'unknown')}\n"
            f"Content: {doc.get('content', '')}\n"
            for i, doc in enumerate(retrieved_docs)
        ])
    else:
        context_text = "No retrieved documents available."
    
    # Add analytics data if provided
    analytics_section = ""
    if analytics_data:
        results_count = analytics_data.get("results_count", 0)
        
        # Check if this is a count-only query (minimal data for LLM)
        is_count_query = analytics_data.get("count_only", False)
        
        # For count queries, only send count, not full results
        if is_count_query:
            analytics_section = f"\n\nANALYTICAL DATA (Count Query):\nTotal Count: {results_count}\nQuery Type: {analytics_data.get('operation', 'unknown')}"
            
            # Add breakdown if available (from GROUP BY aggregations)
            if 'breakdown' in analytics_data:
                breakdown = analytics_data['breakdown']
                breakdown_str = "\n".join([f"  - {k}: {v}" for k, v in breakdown.items()])
                analytics_section += f"\nBreakdown by Category:\n{breakdown_str}"
        else:
            # Original behavior for non-count queries
            # Include all results if available
            full_results = analytics_data.get("results", None)
            
            if results_count == 0:
                analytics_section = f"\n\nANALYTICAL DATA:\nThe database search returned no results. The query may not match any records in election data.\n{analytics_data}\n"
            else:
                # Format results - LIMIT to prevent token overflow
                # Large datasets can exceed token limits, so we limit preview for LLM
                if full_results and isinstance(full_results, list):
                    max_results_for_llm = 50  # Safe limit to prevent token overflow
                    preview_results = full_results[:max_results_for_llm]
                    
                    formatted_results = []
                    for i, result in enumerate(preview_results):
                        if isinstance(result, dict):
                            # Only include key columns to save tokens
                            key_columns = [
                                'candidate_full_name', 'political_party', 'State', 
                                'District', 'constituency', 'education'
                            ]
                            filtered_result = {
                                k: v for k, v in result.items() 
                                if k in key_columns
                            }
                            result_str = "\n".join([f"  {k}: {v}" for k, v in filtered_result.items()])
                            formatted_results.append(f"Result {i+1}:\n{result_str}")
                    
                    results_str = "\n\n".join(formatted_results)
                    analytics_section = f"\n\nANALYTICAL DATA:\n{analytics_data}\n\nRESULTS PREVIEW ({len(preview_results)} of {results_count} total):\n{results_str}\n\nFull results available for frontend display (not sent to LLM)."
    
    # Build final prompt
    # Add special instruction if target is candidates or voting_centers
    if target_entity == "candidates":
        content_instruction = """

CRITICAL INSTRUCTION FOR CANDIDATES:
- The FRONTEND will display full candidate list from sources in proper format
- DO NOT list candidates in your answer
- Provide ONLY a summary at the end with totals and key insights
"""
    elif target_entity == "voting_centers":
        content_instruction = """

CRITICAL INSTRUCTION FOR VOTING CENTERS:
- The FRONTEND will display full voting center list from sources in proper format
- DO NOT list voting centers in your answer
- Provide ONLY a summary at the end with totals and key insights
"""
    else:
        content_instruction = ""
    
    prompt = f"""
{SYSTEM_PROMPT}
{language_instruction}
{content_instruction}
USER QUERY: {user_query}

RETRIEVED CONTEXT:
{context_text}
{analytics_section}

Provide a clear, accurate answer based on the above context.
If the answer cannot be determined from context, explicitly state that the information is not available.
"""
    
    return prompt


def build_exact_lookup_prompt(analytics_data: dict, user_query: str, entities: dict = None) -> str:
    """Build prompt for exact lookup queries."""
    query_language = detect_query_language(user_query)
    language_instruction = f"\n\nIMPORTANT: Answer ENTIRELY in {query_language} language ONLY. Do not show both Nepali and English versions."
    
    # Check target entity
    target_entity = entities.get('target') if entities else None
    
    # Add special instruction if target is candidates or voting_centers
    if target_entity == "candidates":
        content_instruction = """

CRITICAL INSTRUCTION FOR CANDIDATES:
- The FRONTEND will display full candidate list from sources in proper format
- DO NOT list candidates in your answer
- Provide ONLY a summary at the end with totals and key insights
"""
    elif target_entity == "voting_centers":
        content_instruction = """

CRITICAL INSTRUCTION FOR VOTING CENTERS:
- The FRONTEND will display full voting center list from sources in proper format
- DO NOT list voting centers in your answer
- Provide ONLY a summary at the end with totals and key insights
"""
    else:
        content_instruction = ""
    
    return f"""
{SYSTEM_PROMPT}
{language_instruction}
{content_instruction}
USER QUERY: {user_query}

ANALYTICAL DATA (Exact Lookup):
{analytics_data}

Provide a clear, concise answer based on the exact data above.
Include counts and specific matches found without modification.
"""


def build_analytical_prompt(analytics_data: dict, user_query: str) -> str:
    """Build prompt for analytical queries."""
    query_language = detect_query_language(user_query)
    language_instruction = f"\n\nIMPORTANT: Answer ENTIRELY in {query_language} language ONLY. Do not show both Nepali and English versions."
    
    return f"""
{SYSTEM_PROMPT}
{language_instruction}

USER QUERY: {user_query}

ANALYTICAL DATA (Statistics):
{analytics_data}

Provide a clear interpretation of these statistics based on the exact data above.
Explain what the numbers mean and highlight key insights.
Include numerical values and their interpretation without modification.
"""


def build_comparison_prompt(comparison_data: dict, user_query: str) -> str:
    """Build prompt for comparison queries."""
    query_language = detect_query_language(user_query)
    language_instruction = f"\n\nIMPORTANT: Answer ENTIRELY in {query_language} language ONLY. Do not show both Nepali and English versions."
    
    return f"""
{SYSTEM_PROMPT}
{language_instruction}

USER QUERY: {user_query}

COMPARISON DATA:
{comparison_data}

Provide a detailed comparison analysis based on the exact data above.
Use tables or structured formats to show differences clearly.
Highlight similarities and differences between entities.
Include percentages and numerical comparisons without modification.
"""


def build_aggregation_prompt(aggregation_data: dict, user_query: str) -> str:
    """Build prompt for aggregation queries."""
    query_language = detect_query_language(user_query)
    language_instruction = f"\n\nIMPORTANT: Answer ENTIRELY in {query_language} language ONLY. Do not show both Nepali and English versions."
    
    return f"""
{SYSTEM_PROMPT}
{language_instruction}

USER QUERY: {user_query}

AGGREGATION DATA:
{aggregation_data}

Provide a clear summary of the aggregated data based on the exact data above.
Organize results logically (by count, percentage, etc.).
Use tables or bullet points for clarity.
"""


def build_complex_prompt(sub_results: list, user_query: str) -> str:
    """Build prompt for complex multi-step queries."""
    query_language = detect_query_language(user_query)
    language_instruction = f"\n\nIMPORTANT: Answer ENTIRELY in {query_language} language ONLY. Do not show both Nepali and English versions."
    
    return f"""
{SYSTEM_PROMPT}
{language_instruction}

USER QUERY: {user_query}

SUB-QUERY RESULTS:
{sub_results}

Synthesize these results into a comprehensive answer based on the exact data above.
Combine insights from multiple sub-queries to provide a complete response.
"""
