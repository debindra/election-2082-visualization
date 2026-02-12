"""
Quick Test Runner for RAG System

Simple test script without full asyncio setup.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_imports():
    """Test that all imports work correctly."""
    print("=" * 70)
    print("Testing Imports...")
    print("=" * 70)
    
    try:
        print("✓ Config imports...", end="")
        from config.settings import settings
        print(" OK")
        
        print("✓ Model imports...", end="")
        from models.schemas import (
            ChatRequest, ChatResponse, 
            AnalyticsRequest, AnalyticsResponse, 
            HealthResponse
        )
        print(" OK")
        
        print("✓ Service imports...", end="")
        from services import (
            EmbeddingService, 
            FaissVectorStore,
            ElectionAnalyticsService,
            DeepSeekLLMService,
            RetrievalService,
            QueryClassifier, QueryType,
            QueryRouter,
            ElectionChatService
        )
        print(" OK")
        
        print("✓ Prompt imports...", end="")
        from prompts.system_prompt import (
            SYSTEM_PROMPT,
            build_context_prompt
        )
        print(" OK")
        
        print("\n" + "=" * 70)
        print("✓ All imports successful!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        print("=" * 70)
        return False


def test_analytics():
    """Test analytics service independently."""
    print("\n" + "=" * 70)
    print("Testing Analytics Service...")
    print("=" * 70)
    
    try:
        from services import ElectionAnalyticsService
        
        print("Loading data...")
        analytics = ElectionAnalyticsService(
            candidates_csv="../data/elections/election_candidates-2082.csv",
            voting_centers_csv="../data/elections/voting_centers.csv"
        )
        
        print(f"✓ Loaded {len(analytics.candidates_df)} candidates")
        print(f"✓ Loaded {len(analytics.voting_centers_df)} voting centers")
        
        # Test exact lookup
        print("\n1. Testing exact_lookup()...")
        results = analytics.exact_lookup("Candidate Full Name", "शेर बहादुर देउवा", limit=1)
        print(f"   Found: {len(results)} candidates")
        
        # Test count
        print("2. Testing count_candidates()...")
        count = analytics.count_candidates(filters={"District": "काठमाडौं"})
        print(f"   Count: {count}")
        
        # Test statistics
        print("3. Testing get_statistics()...")
        stats = analytics.get_statistics(field="age", filters={"Gender": "महिला"})
        print(f"   Average age: {stats.get('mean', 0):.1f}")
        
        # Test aggregation
        print("4. Testing aggregate_by_field()...")
        agg = analytics.aggregate_by_field(field="Political Party", limit=5)
        print(f"   Top parties: {list(agg.keys())[:3]}")
        
        print("\n" + "=" * 70)
        print("✓ Analytics service tests passed!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Analytics test failed: {e}")
        return False


def test_embedding():
    """Test embedding service."""
    print("\n" + "=" * 70)
    print("Testing Embedding Service...")
    print("=" * 70)
    
    try:
        from services import EmbeddingService
        
        print("Initializing embedding model...")
        embedding_service = EmbeddingService()
        print(f"✓ Model loaded: {embedding_service.model_name}")
        print(f"✓ Embedding dim: {embedding_service.embedding_dim}")
        
        # Test single embed
        print("\n1. Testing embed_single()...")
        test_text = "This is a test candidate from Nepal"
        embedding = embedding_service.embed_single(test_text)
        print(f"   Generated embedding shape: {embedding.shape}")
        
        # Test candidate text creation
        print("2. Testing create_candidate_text()...")
        test_candidate = {
            "Candidate Full Name": "शेर बहादुर देउवा",
            "Political Party": "नेपाली काँग्रेस",
            "Election Area": "बैतडी - १",
            "District": "बैतडी",
            "Age": 75
        }
        text = embedding_service.create_candidate_text(test_candidate)
        print(f"   Generated text length: {len(text)} characters")
        
        print("\n" + "=" * 70)
        print("✓ Embedding service tests passed!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Embedding test failed: {e}")
        return False


def test_vector_store():
    """Test vector store."""
    print("\n" + "=" * 70)
    print("Testing Vector Store...")
    print("=" * 70)
    
    try:
        from services import FaissVectorStore, EmbeddingService
        
        print("Initializing vector store...")
        embedding_service = EmbeddingService()
        vector_store = FaissVectorStore(embedding_dim=embedding_service.embedding_dim)
        
        print("Creating index...")
        vector_store.create_index()
        
        # Test adding some dummy vectors
        print("\n1. Testing add_embeddings()...")
        import numpy as np
        
        dummy_embeddings = np.random.rand(10, embedding_service.embedding_dim).astype('float32')
        dummy_metadata = [
            {
                "source_type": "test",
                "content": f"Test document {i}",
                "test_id": i
            }
            for i in range(10)
        ]
        
        vector_store.add_embeddings(dummy_embeddings, dummy_metadata)
        print(f"   Added {len(dummy_metadata)} dummy vectors")
        
        # Test search
        print("2. Testing search()...")
        query_embedding = np.random.rand(embedding_service.embedding_dim).astype('float32')
        results = vector_store.search(query_embedding, k=5)
        print(f"   Found {len(results)} results")
        
        print("\n" + "=" * 70)
        print("✓ Vector store tests passed!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Vector store test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " RAG SYSTEM TEST SUITE ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    results = {
        "imports": False,
        "analytics": False,
        "embedding": False,
        "vector_store": False,
    }
    
    # Test 1: Imports
    results["imports"] = test_imports()
    
    # Test 2: Analytics (only if imports work)
    if results["imports"]:
        results["analytics"] = test_analytics()
    
    # Test 3: Embeddings (only if analytics works)
    if results["analytics"]:
        results["embedding"] = test_embedding()
    
    # Test 4: Vector Store (only if embeddings work)
    if results["embedding"]:
        results["vector_store"] = test_vector_store()
    
    # Summary
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + " TEST SUMMARY ".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╠" + "═" * 68 + "╣")
    print("║")
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"║ {test_name:20s} {status}")
    print("║")
    print("╠" + "═" * 68 + "╣")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Overall status
    all_passed = all(results.values())
    
    if all_passed:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Build FAISS index: python scripts/build_index.py --combined")
        print("2. Configure DeepSeek API key in rag-qa/.env")
        print("3. Start server: python main.py")
        print("4. Access docs: http://localhost:8002/docs")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"\nFailed tests: {', '.join(failed_tests)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
