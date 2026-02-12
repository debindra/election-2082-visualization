"""
Simple Test for RAG System

Tests imports and basic functionality without complex async setup.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("=" * 70)
print("RAG System Simple Test")
print("=" * 70)
print()

# Test 1: Check configuration
print("1. Testing Configuration...")
try:
    from config.settings import settings
    print(f"   ✓ Settings loaded")
    print(f"   - Host: {settings.host}")
    print(f"   - Port: {settings.port}")
    print(f"   - Embedding Model: {settings.embedding_model}")
    print(f"   - DeepSeek Model: {settings.deepseek_model}")
    print(f"   - Data Paths:")
    print(f"     - Candidates: {settings.candidates_csv}")
    print(f"     - Voting Centers: {settings.voting_centers_csv}")
except Exception as e:
    print(f"   ✗ Configuration error: {e}")
    sys.exit(1)

print()

# Test 2: Check data files exist
print("2. Testing Data Files...")
from pathlib import Path

candidates_csv = Path(settings.candidates_csv)
voting_centers_csv = Path(settings.voting_centers_csv)

if candidates_csv.exists():
    print(f"   ✓ Candidates CSV: {candidates_csv}")
    print(f"     Size: {candidates_csv.stat().st_size / 1024:.1f} KB")
else:
    print(f"   ✗ Candidates CSV NOT found: {candidates_csv}")
    if voting_centers_csv.exists():
        sys.exit(1)

if voting_centers_csv.exists():
    print(f"   ✓ Voting Centers CSV: {voting_centers_csv}")
    print(f"     Size: {voting_centers_csv.stat().st_size / 1024:.1f} KB")
else:
    print(f"   ✗ Voting Centers CSV NOT found: {voting_centers_csv}")
    sys.exit(1)

print()

# Test 3: Import test
print("3. Testing Module Imports...")
try:
    import pandas as pd
    print("   ✓ Pandas")
    
    import numpy as np
    print("   ✓ NumPy")
    
    from sentence_transformers import SentenceTransformer
    print("   ✓ SentenceTransformers")
    
    import faiss
    print("   ✓ FAISS")
    
    import torch
    print("   ✓ PyTorch")
    
    from langchain_openai import ChatOpenAI
    print("   ✓ LangChain (DeepSeek)")
    
    from services import (
        EmbeddingService,
        FaissVectorStore,
        ElectionAnalyticsService
    )
    print("   ✓ All service modules")
    
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    print(f"   ✗ Please install: {str(e)}")
    sys.exit(1)

print()

# Test 4: Check DeepSeek API configuration
print("4. Testing DeepSeek Configuration...")
if not settings.deepseek_api_key:
    print("   ⚠ DeepSeek API key not configured")
    print("   ✗ Set DEEPSEEK_API_KEY in rag-qa/.env")
else:
    print(f"   ✓ API key configured (length: {len(settings.deepseek_api_key)})")

print()

# Test 5: Check FAISS index
print("5. Testing FAISS Index...")
index_path = Path(settings.faiss_index_path)
index_dir = index_path.parent

if index_dir.exists():
    print(f"   ✓ Index directory exists: {index_dir}")
    
    index_file = index_path / "index.faiss"
    metadata_file = index_path / "metadata.pkl"
    
    if index_file.exists():
        print(f"   ✓ FAISS index: {index_file}")
        print(f"     Size: {index_file.stat().st_size / 1024:.1f} KB")
    else:
        print(f"   ✗ FAISS index NOT found: {index_file}")
        print("   → Run: python scripts/build_index.py --combined")
        sys.exit(1)
    
    if metadata_file.exists():
        print(f"   ✓ Metadata: {metadata_file}")
        print(f"     Size: {metadata_file.stat().st_size / 1024:.1f} KB")
    else:
        print(f"   ✗ Metadata NOT found: {metadata_file}")
        sys.exit(1)
else:
    print(f"   ✗ Index directory NOT found: {index_dir}")
    sys.exit(1)

print()

# Test 6: Initialize embedding service
print("6. Testing Embedding Service...")
try:
    embedding_service = EmbeddingService()
    print(f"   ✓ Embedding service initialized")
    print(f"   - Model: {embedding_service.model_name}")
    print(f"   - Dimension: {embedding_service.embedding_dim}")
    print(f"   - Device: {embedding_service.device}")
    
    # Test single embed
    test_text = "This is a test candidate from Nepal named राम बहादुर देउवा"
    embedding = embedding_service.embed_single(test_text)
    print(f"   ✓ Test embedding generated (shape: {embedding.shape})")
    
except Exception as e:
    print(f"   ✗ Embedding service error: {e}")
    sys.exit(1)

print()

# Test 7: Initialize vector store
print("7. Testing Vector Store...")
try:
    vector_store = FaissVectorStore(embedding_dim=embedding_service.embedding_dim)
    print(f"   ✓ Vector store initialized")
    print(f"   - Embedding dim: {vector_store.embedding_dim}")
    print(f"   - Index path: {vector_store.index_path}")
    
except Exception as e:
    print(f"   ✗ Vector store error: {e}")
    sys.exit(1)

print()

# Test 8: Initialize analytics service
print("8. Testing Analytics Service...")
try:
    analytics_service = ElectionAnalyticsService()
    print(f"   ✓ Analytics service initialized")
    print(f"   - Candidates: {len(analytics_service.candidates_df)}")
    print(f"   - Voting Centers: {len(analytics_service.voting_centers_df)}")
    
    # Test count
    count = analytics_service.count_candidates()
    print(f"   ✓ Count candidates: {count}")
    
    # Test exact lookup
    results = analytics_service.exact_lookup("Candidate Full Name", "राम बहादुर देउवा", limit=1)
    print(f"   ✓ Exact lookup: {len(results)} result(s)")
    
except Exception as e:
    print(f"   ✗ Analytics service error: {e}")
    sys.exit(1)

print()

# Summary
print()
print("=" * 70)
print("SYSTEM STATUS SUMMARY")
print("=" * 70)
print("✓ Configuration: OK")
print("✓ Data Files: OK")
print("✓ Dependencies: OK")
print("✓ DeepSeek Config: " + ("OK" if settings.deepseek_api_key else "NOT SET"))
print("✓ FAISS Index: " + ("OK" if index_file.exists() else "NOT BUILT"))
print()
print("NEXT STEPS:")
print("1. Build FAISS index:")
print("   cd rag-qa")
print("   python scripts/build_index.py --combined")
print()
print("2. Configure DeepSeek API:")
print("   cp .env.example .env")
print("   nano .env")
print("   # Add your DeepSeek API key")
print()
print("3. Start RAG server:")
print("   python main.py")
print()
print("4. Test system:")
print("   curl -X POST http://localhost:8002/api/v1/chat \\")
print('     -H "Content-Type: application/json" \\')
print('     -d \'{"query": "काठमाडौंमा कति उम्मेदवारहरू छन्?", "top_k": 5}\'')
print()
print("=" * 70)
print()
print("✓ All systems checked! RAG system is ready.")
print()
