"""
Test Script for Hybrid SQLite + Vector Search System

Tests the new architecture:
User → Intent + Entity Extraction → Structured? → SQL / Vector Search → Combine → LLM → Response
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from services import (
    EmbeddingService,
    FaissVectorStore,
    DeepSeekLLMService,
    QueryClassifier,
    QueryRouter,
    SQLiteService,
    RetrievalService
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sqlite_basic():
    """Test basic SQLite functionality."""
    print("\n" + "=" * 60)
    print("TEST 1: SQLite Basic Queries")
    print("=" * 60)
    
    sqlite = SQLiteService(settings.sqlite_db_path)
    
    # Test count
    count = sqlite.count_candidates()
    print(f"✓ Total candidates: {count}")
    
    # Test filter
    count_kathmandu = sqlite.count_candidates({"district_in_english": "Kathmandu"})
    print(f"✓ Candidates in Kathmandu: {count_kathmandu}")
    
    # Test exact lookup
    results = sqlite.exact_lookup("candidates", "candidate_full_name", "राम", limit=5)
    print(f"✓ Found {len(results)} candidates with 'राम' in name")
    
    # Test aggregation
    by_party = sqlite.aggregate_by_field("candidates", "political_party_in_english")
    print(f"✓ Top 3 parties: {list(by_party.items())[:3]}")
    
    # Test full-text search
    fts_results = sqlite.full_text_search("candidates", "law education", limit=5)
    print(f"✓ FTS 'law education': {len(fts_results)} results")


def test_sql_generation():
    """Test SQL generation from LLM."""
    print("\n" + "=" * 60)
    print("TEST 2: SQL Generation")
    print("=" * 60)
    
    llm = DeepSeekLLMService()
    sqlite = SQLiteService(settings.sqlite_db_path)
    from services.sql_generator import SQLGenerator
    
    sql_gen = SQLGenerator(llm, sqlite)
    
    # Test queries
    test_queries = [
        ("How many candidates are there?", "count"),
        ("Show candidates by party", "aggregate"),
        ("Find candidates named Ram", "exact_lookup"),
    ]
    
    import asyncio
    
    async def test_sql():
        for query, query_type in test_queries:
            print(f"\nQuery: {query}")
            result = await sql_gen.generate_sql(query, query_type)
            if result.get("sql"):
                print(f"  ✓ Generated SQL: {result['sql'][:80]}...")
                
                # Execute
                success, exec_result = await sql_gen.generate_and_execute(query, query_type)
                if success:
                    print(f"  ✓ Results: {exec_result.get('results_count', 0)} rows")
                else:
                    print(f"  ✗ Failed: {exec_result.get('error')}")
            else:
                print(f"  ✗ Failed: {result.get('error')}")
    
    asyncio.run(test_sql())


def test_intent_extraction():
    """Test intent and entity extraction."""
    print("\n" + "=" * 60)
    print("TEST 3: Intent Extraction")
    print("=" * 60)
    
    llm = DeepSeekLLMService()
    from services.sql_generator import IntentExtractor
    
    extractor = IntentExtractor(llm)
    
    test_queries = [
        "How many candidates in Kathmandu?",
        "Find candidates with law education",
        "Compare Nepali Congress and UML",
        "Candidates from rural areas"
    ]
    
    import asyncio
    
    async def test_intents():
        for query in test_queries:
            print(f"\nQuery: {query}")
            result = await extractor.extract(query)
            print(f"  Intent: {result.get('intent')}")
            print(f"  Query Type: {result.get('query_type')}")
            print(f"  Target: {result.get('entities', {}).get('target')}")
            print(f"  Confidence: {result.get('confidence'):.2f}")
            
            # Check if structured
            is_structured = extractor.is_structured_query(query, result)
            print(f"  Routing: {'SQL (Structured)' if is_structured else 'Vector (Semantic)'}")
    
    asyncio.run(test_intents())


def test_hybrid_routing():
    """Test hybrid routing (the complete new architecture)."""
    print("\n" + "=" * 60)
    print("TEST 4: Hybrid Routing (Complete Architecture)")
    print("=" * 60)
    
    # Initialize all services
    llm = DeepSeekLLMService()
    sqlite = SQLiteService(settings.sqlite_db_path)
    embedding_service = EmbeddingService()
    vector_store = FaissVectorStore(embedding_dim=embedding_service.embedding_dim)
    
    # Load vector index
    if not vector_store.load():
        print("✗ Vector index not found. Skipping vector search tests.")
        return
    
    # Initialize classifier and router
    classifier = QueryClassifier(llm_service=llm)
    retrieval = RetrievalService(embedding_service, vector_store)
    router = QueryRouter(
        classifier=classifier,
        sqlite=sqlite,
        retrieval=retrieval,
        llm=llm
    )
    
    # Test queries that should route differently
    test_cases = [
        ("How many candidates in Province 1?", "SQL (structured count)"),
        ("Find candidates with law education", "Vector (semantic search)"),
        ("Show voting centers by district", "SQL (aggregation)"),
        ("Candidates similar to lawyers", "Vector (semantic)"),
    ]
    
    import asyncio
    
    async def test_routing():
        for query, expected_route in test_cases:
            print(f"\nQuery: {query}")
            print(f"Expected: {expected_route}")
            
            result = await router.route_and_execute(query, top_k=3)
            
            print(f"  Query Type: {result.get('query_type')}")
            print(f"  Method: {result.get('method')}")
            print(f"  SQL Used: {'Yes' if result.get('sql_used') else 'No'}")
            print(f"  Sources: {len(result.get('sources', []))}")
            
            # Verify routing
            if "sql" in result.get('method', '').lower():
                print(f"  ✓ Routed to SQL as expected")
            elif "vector" in result.get('method', '').lower():
                print(f"  ✓ Routed to Vector as expected")
            else:
                print(f"  ✗ Unexpected routing")
    
    asyncio.run(test_routing())


def main():
    """Run all tests."""
    print("=" * 60)
    print("HYBRID SQLITE + VECTOR SEARCH SYSTEM TESTS")
    print("=" * 60)
    
    # Check prerequisites
    if not Path(settings.sqlite_db_path).exists():
        print(f"✗ SQLite database not found at {settings.sqlite_db_path}")
        print("Run: python scripts/setup_sqlite.py")
        return
    
    # Check LLM configuration
    llm = DeepSeekLLMService()
    if not llm.is_configured():
        print("✗ DeepSeek API key not configured")
        print("Set DEEPSEEK_API_KEY in .env file")
        return
    
    # Run tests
    try:
        test_sqlite_basic()
        test_sql_generation()
        test_intent_extraction()
        test_hybrid_routing()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
