"""
Test Script for RAG System

Tests all query types with expected outputs.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.chat_service import ElectionChatService
from services import (
    QueryRouter,
    QueryClassifier,
    ElectionAnalyticsService,
    DeepSeekLLMService,
    RetrievalService,
    EmbeddingService,
    FaissVectorStore
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ================== TEST QUERIES ==================

TEST_QUERIES = {
    "exact_lookup": [
        "काठमाडौंमा कति उम्मेदवारहरू छन्?",
        "How many candidates are there in Kathmandu?",
        "Count voting centers in Province 1",
        "Find candidates named Ram Bahadur",
    ],
    "analytical": [
        "उम्मेदवारहरूको औसत उमेर कति हो?",
        "What's the average age of candidates?",
        "Show age distribution by province",
    ],
    "semantic_search": [
        "कानून को शिक्षा भएका उम्मेदवार को को हो?",
        "Candidates with law education",
        "Candidates from rural areas",
    ],
    "comparison": [
        "नेपाली काँग्रेस र एमालेको उम्मेदवार संख्यामा तुलना गर्नुहोस्",
        "Which province has the most voters?",
    ],
    "aggregation": [
        "पार्टी अनुसार उम्मेदवार संख्या देखाउनुहोस्",
        "Show candidates by district",
        "Gender distribution of candidates",
    ],
    "complex": [
        "कुन पार्टीको ३० वर्ष मुनिका उमेर भएका उम्मेदवार सबैभन्दा बढी छन्?",
    ],
}


async def test_query(chat_service: ElectionChatService, 
                    query_type: str, 
                    query: str):
    """
    Test a single query.
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Testing {query_type}: {query}")
    logger.info(f"{'='*70}")
    
    try:
        result = await chat_service.chat(query=query, filters=None, top_k=5)
        
        # Display results
        print(f"\n{'='*70}")
        print(f"QUERY: {query}")
        print(f"{'='*70}")
        print(f"Type: {result.get('query_type', 'UNKNOWN')}")
        print(f"Method: {result.get('method', 'UNKNOWN')}")
        print(f"Confidence: {result.get('metadata', {}).get('confidence', 'N/A')}")
        print(f"\n{'='*70}")
        print("ANSWER:")
        print(result.get('answer', ''))
        print(f"\n{'='*70}")
        print(f"SOURCES: {len(result.get('sources', []))} documents")
        
        # Show source details
        for i, source in enumerate(result.get('sources', [])[:3], 1):
            print(f"\n[{i}] {source.get('source_type', 'unknown').upper()}")
            print(f"    Distance: {source.get('distance', 'N/A'):.4f}")
            if source.get('source_type') == 'candidate':
                print(f"    Name: {source.get('name_np', 'N/A')}")
                print(f"    Party: {source.get('party_np', 'N/A')}")
                print(f"    Constituency: {source.get('constituency', 'N/A')}")
            elif source.get('source_type') == 'voting_center':
                print(f"    Center: {source.get('polling_center_name', 'N/A')}")
                print(f"    Location: {source.get('district', 'N/A')}")
        
        # Show analytics if available
        if result.get('analytics_used'):
            print(f"\n{'='*70}")
            print("ANALYTICS USED:")
            print(json.dumps(result['analytics_used'], indent=2, ensure_ascii=False))
        
        print(f"\n{'='*70}")
        print("✓ Test completed successfully")
        print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}", exc_info=True)
        print(f"\n{'='*70}")
        print(f"✗ Test failed: {str(e)}")
        print(f"{'='*70}\n")
        return False


async def run_tests(chat_service: ElectionChatService, 
                  query_types: list = None):
    """
    Run all tests or specific query types.
    """
    if query_types is None:
        query_types = list(TEST_QUERIES.keys())
    
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "by_type": {}
    }
    
    for query_type in query_types:
        if query_type not in TEST_QUERIES:
            logger.warning(f"Unknown query type: {query_type}")
            continue
        
        type_results = {
            "total": len(TEST_QUERIES[query_type]),
            "passed": 0,
            "failed": 0
        }
        
        print(f"\n{'#'*70}")
        print(f"# Testing {query_type.upper()} Queries")
        print(f"# Total: {len(TEST_QUERIES[query_type])} tests")
        print(f"{'#'*70}\n")
        
        for query in TEST_QUERIES[query_type]:
            results["total_tests"] += 1
            
            success = await test_query(chat_service, query_type, query)
            
            if success:
                results["passed"] += 1
                type_results["passed"] += 1
            else:
                results["failed"] += 1
                type_results["failed"] += 1
        
        results["by_type"][query_type] = type_results
    
    # Print summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ✓")
    print(f"Failed: {results['failed']} ✗")
    print(f"Success Rate: {(results['passed'] / results['total_tests'] * 100):.1f}%")
    print(f"\n{'='*70}")
    
    # Detailed summary by type
    for query_type, type_results in results["by_type"].items():
        total = type_results["total"]
        passed = type_results["passed"]
        failed = type_results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{query_type.upper()}:")
        print(f"  Total: {total}")
        print(f"  Passed: {passed} ✓")
        print(f"  Failed: {failed} {'✗' if failed > 0 else ''}")
        print(f"  Success Rate: {success_rate:.1f}%")
    
    print(f"\n{'='*70}\n")


async def main():
    """Main test function."""
    logger.info("Initializing RAG System Test Suite")
    logger.info("=" * 60)
    
    # Check if index exists
    index_path = Path("data/faiss_index/index.faiss")
    if not index_path.exists():
        logger.error("✗ FAISS index not found!")
        logger.error("Please run: python scripts/build_index.py --combined")
        print("\n✗ ERROR: FAISS index not found!")
        print("Please build the index first:")
        print("  cd rag-qa")
        print("  python scripts/build_index.py --combined")
        sys.exit(1)
    
    logger.info("✓ FAISS index found")
    
    # Initialize services
    try:
        llm_service = DeepSeekLLMService()
        
        analytics_service = ElectionAnalyticsService()
        
        embedding_service = EmbeddingService()
        
        vector_store = FaissVectorStore()
        if not vector_store.load():
            logger.error("✗ Failed to load vector store")
            sys.exit(1)
        
        retrieval_service = RetrievalService(embedding_service, vector_store)
        
        query_classifier = QueryClassifier(llm_service)
        
        query_router = QueryRouter(
            classifier=query_classifier,
            analytics=analytics_service,
            retrieval=retrieval_service,
            llm=llm_service
        )
        
        chat_service = ElectionChatService(query_router)
        
        logger.info("✓ All services initialized successfully")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize services: {e}", exc_info=True)
        print(f"\n✗ Initialization failed: {str(e)}")
        sys.exit(1)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type in TEST_QUERIES:
            print(f"\nRunning tests for: {test_type}")
            await run_tests(chat_service, [test_type])
        else:
            print(f"\nUnknown test type: {test_type}")
            print(f"Available test types: {', '.join(TEST_QUERIES.keys())}")
            print(f"Usage: python scripts/test_system.py [test_type]")
            print(f"Or: python scripts/test_system.py (for all tests)")
            sys.exit(1)
    else:
        # Run all tests
        print(f"\nRunning all tests...")
        await run_tests(chat_service)
    
    logger.info("Test suite completed")


if __name__ == "__main__":
    asyncio.run(main())
