"""
Data Processing Script for Building FAISS Index

Generates embeddings and builds FAISS vector index for candidates and voting centers.
"""
import logging
import sys
from pathlib import Path
import argparse
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services import (
    EmbeddingService,
    FaissVectorStore,
    ElectionAnalyticsService
)
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_candidate_index():
    """
    Build index for election candidates.

    Uses index type from settings.faiss_index_type:
    - "flat": FlatL2 (exact, slow, 100% recall)
    - "hnsw": HNSW (fast, 95-99% recall) - RECOMMENDED
    - "ivf": IVFFlat (fast, needs training)
    """
    logger.info("=" * 60)
    logger.info("Building Candidate Index")
    logger.info("=" * 60)
    logger.info(f"Index Type: {settings.faiss_index_type}")

    if settings.faiss_index_type.lower() == "hnsw":
        logger.info(f"  HNSW Configuration:")
        logger.info(f"    M: {settings.faiss_hnsw_m}")
        logger.info(f"    efConstruction: {settings.faiss_hnsw_ef_construction}")
        logger.info(f"    efSearch (default): {settings.faiss_hnsw_ef_search_default}")

    # Load candidates data
    candidates_df = ElectionAnalyticsService(
        candidates_csv=settings.candidates_csv
    ).candidates_df

    logger.info(f"Loaded {len(candidates_df)} candidates from {settings.candidates_csv}")

    # Initialize embedding service
    embedding_service = EmbeddingService()

    # Generate embeddings
    embeddings, texts, metadata_list = embedding_service.batch_embed_candidates(candidates_df)

    logger.info(f"Generated embeddings shape: {embeddings.shape}")
    logger.info(f"Sample text: {texts[0][:200]}...")

    # Initialize vector store
    vector_store = FaissVectorStore(embedding_dim=embedding_service.embedding_dim)
    vector_store.create_index()

    # Add embeddings to index in batches to avoid memory issues
    batch_size = 5000
    total_vectors = len(embeddings)

    for i in range(0, total_vectors, batch_size):
        batch_end = min(i + batch_size, total_vectors)
        batch_embeddings = embeddings[i:batch_end]
        batch_metadata = metadata_list[i:batch_end]

        logger.info(f"Adding batch {i//batch_size + 1}/{(total_vectors + batch_size - 1)//batch_size}: {len(batch_embeddings)} vectors")
        vector_store.add_embeddings(batch_embeddings, batch_metadata)

    # Save index
    vector_store.save()

    logger.info("✓ Candidate index built and saved successfully")

    return {
        "total_candidates": len(candidates_df),
        "embedding_dim": embedding_service.embedding_dim,
        "index_path": str(vector_store.index_path)
    }


def build_voting_center_index():
    """
    Build index for voting centers.

    Uses index type from settings.faiss_index_type:
    - "flat": FlatL2 (exact, slow, 100% recall)
    - "hnsw": HNSW (fast, 95-99% recall) - RECOMMENDED
    - "ivf": IVFFlat (fast, needs training)
    """
    logger.info("=" * 60)
    logger.info("Building Voting Center Index")
    logger.info("=" * 60)
    logger.info(f"Index Type: {settings.faiss_index_type}")

    if settings.faiss_index_type.lower() == "hnsw":
        logger.info(f"  HNSW Configuration:")
        logger.info(f"    M: {settings.faiss_hnsw_m}")
        logger.info(f"    efConstruction: {settings.faiss_hnsw_ef_construction}")
        logger.info(f"    efSearch (default): {settings.faiss_hnsw_ef_search_default}")

    # Load voting centers data
    vc_df = ElectionAnalyticsService(
        voting_centers_csv=settings.voting_centers_csv
    ).voting_centers_df

    logger.info(f"Loaded {len(vc_df)} voting centers from {settings.voting_centers_csv}")

    # Initialize embedding service
    embedding_service = EmbeddingService()

    # Generate embeddings
    embeddings, texts, metadata_list = embedding_service.batch_embed_voting_centers(vc_df)

    logger.info(f"Generated embeddings shape: {embeddings.shape}")
    logger.info(f"Sample text: {texts[0][:200]}...")

    # Initialize vector store
    vector_store = FaissVectorStore(embedding_dim=embedding_service.embedding_dim)
    vector_store.create_index()

    # Add embeddings to index in batches to avoid memory issues
    batch_size = 5000
    total_vectors = len(embeddings)

    for i in range(0, total_vectors, batch_size):
        batch_end = min(i + batch_size, total_vectors)
        batch_embeddings = embeddings[i:batch_end]
        batch_metadata = metadata_list[i:batch_end]

        logger.info(f"Adding batch {i//batch_size + 1}/{(total_vectors + batch_size - 1)//batch_size}: {len(batch_embeddings)} vectors")
        vector_store.add_embeddings(batch_embeddings, batch_metadata)

    # Save index
    vector_store.save()

    logger.info("✓ Voting center index built and saved successfully")

    return {
        "total_voting_centers": len(vc_df),
        "embedding_dim": embedding_service.embedding_dim,
        "index_path": str(vector_store.index_path)
    }


def build_combined_index():
    """
    Build combined index with both candidates and voting centers.
    """
    logger.info("=" * 60)
    logger.info("Building Combined Election Data Index")
    logger.info("=" * 60)

    # Load both data sources
    analytics = ElectionAnalyticsService(
        candidates_csv=settings.candidates_csv,
        voting_centers_csv=settings.voting_centers_csv
    )

    candidates_df = analytics.candidates_df
    vc_df = analytics.voting_centers_df

    logger.info(f"Loaded {len(candidates_df)} candidates")
    logger.info(f"Loaded {len(vc_df)} voting centers")

    # Initialize embedding service
    embedding_service = EmbeddingService()

    # Generate embeddings for both
    candidate_embeddings, candidate_texts, candidate_metadata = \
        embedding_service.batch_embed_candidates(candidates_df)

    vc_embeddings, vc_texts, vc_metadata = \
        embedding_service.batch_embed_voting_centers(vc_df)

    logger.info(f"Generated {len(candidate_embeddings)} candidate embeddings")
    logger.info(f"Generated {len(vc_embeddings)} voting center embeddings")

    # Combine embeddings using numpy vstack for proper 2D array
    all_embeddings = np.vstack([candidate_embeddings, vc_embeddings])

    all_metadata = candidate_metadata + vc_metadata

    logger.info(f"Combined embeddings shape: {all_embeddings.shape}")

    # Initialize vector store
    vector_store = FaissVectorStore(embedding_dim=embedding_service.embedding_dim)

    # Add embeddings in batches to avoid memory issues and segmentation faults
    batch_size = 5000
    total_vectors = len(all_embeddings)

    for i in range(0, total_vectors, batch_size):
        batch_end = min(i + batch_size, total_vectors)
        batch_embeddings = all_embeddings[i:batch_end]
        batch_metadata = all_metadata[i:batch_end]

        logger.info(f"Adding batch {i//batch_size + 1}/{(total_vectors + batch_size - 1)//batch_size}: {len(batch_embeddings)} vectors")
        vector_store.add_embeddings(batch_embeddings, batch_metadata)

    # Save index
    vector_store.save()

    logger.info("✓ Combined index built and saved successfully")

    return {
        "total_candidates": len(candidates_df),
        "total_voting_centers": len(vc_df),
        "total_vectors": len(all_embeddings),
        "embedding_dim": embedding_service.embedding_dim,
        "index_path": str(vector_store.index_path)
    }


def verify_index():
    """
    Verify that index was built correctly.
    Shows detailed statistics including HNSW-specific metrics.
    """
    logger.info("=" * 60)
    logger.info("Verifying Built Index")
    logger.info("=" * 60)
    
    vector_store = FaissVectorStore()
    loaded = vector_store.load()
    
    if not loaded:
        logger.error("✗ Failed to load index")
        return False
    
    stats = vector_store.get_stats()
    
    logger.info("Index Statistics:")
    logger.info(f"  Index Type: {stats.get('index_type', 'Unknown')}")
    logger.info(f"  Is Initialized: {stats['is_initialized']}")
    logger.info(f"  Is Trained: {stats['is_trained']}")
    logger.info(f"  Total Vectors: {stats['total_vectors']}")
    logger.info(f"  Total Metadata: {stats['total_metadata']}")
    logger.info(f"  Embedding Dim: {stats['embedding_dim']}")
    logger.info(f"  Index Path: {stats['index_path']}")
    
    # Show HNSW-specific stats if applicable
    if stats.get('index_type') == 'HNSW':
        logger.info("")
        logger.info("HNSW Configuration:")
        logger.info(f"  M (connections per node): {stats.get('hnsw_M')}")
        logger.info(f"  efConstruction: {stats.get('hnsw_efConstruction')}")
        logger.info(f"  efSearch (current): {stats.get('hnsw_efSearch')}")
        logger.info("")
        logger.info("HNSW Performance Characteristics:")
        logger.info("  - Search time: O(log N)")
        logger.info("  - Recall: 95-99% (depends on efSearch)")
        logger.info("  - Memory overhead: ~3-5 MB for 26K vectors")
    
    if stats['total_vectors'] > 0:
        logger.info("✓ Index verification successful")
        return True
    else:
        logger.error("✗ Index appears empty")
        return False


def main():
    """
    Main function to build index.
    """
    parser = argparse.ArgumentParser(
        description="Build FAISS index for Nepal election data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build combined index with default type (HNSW - fast, approximate)
  python build_index.py --combined
  
  # Build candidate index with FlatL2 (exact, slow)
  python build_index.py --candidates --index-type flat
  
  # Build voting center index with IVF (medium speed)
  python build_index.py --voting-centers --index-type ivf
  
  # Build combined index with custom HNSW parameters
  python build_index.py --combined --index-type hnsw --hnsw-m 48 --hnsw-ef-construction 200
  
  # Verify existing index
  python build_index.py --verify
        """
    )
    
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Build combined index (candidates + voting centers)"
    )
    
    parser.add_argument(
        "--candidates",
        action="store_true",
        help="Build only candidate index"
    )
    
    parser.add_argument(
        "--voting-centers",
        action="store_true",
        help="Build only voting center index"
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing index (don't rebuild)"
    )
    
    parser.add_argument(
        "--index-type",
        choices=["flat", "ivf", "hnsw"],
        default=None,
        help="Override FAISS index type (default: from settings)"
    )
    
    parser.add_argument(
        "--hnsw-m",
        type=int,
        default=None,
        help="HNSW M parameter (default: from settings, 16-64)"
    )
    
    parser.add_argument(
        "--hnsw-ef-construction",
        type=int,
        default=None,
        help="HNSW efConstruction parameter (default: from settings, 64-256)"
    )
    
    args = parser.parse_args()
    
    # Override settings if CLI args provided
    original_index_type = settings.faiss_index_type
    if args.index_type:
        settings.faiss_index_type = args.index_type
        logger.info(f"Overriding index type to: {args.index_type}")
    if args.hnsw_m:
        settings.faiss_hnsw_m = args.hnsw_m
        logger.info(f"Setting HNSW M to: {args.hnsw_m}")
    if args.hnsw_ef_construction:
        settings.faiss_hnsw_ef_construction = args.hnsw_ef_construction
        logger.info(f"Setting HNSW efConstruction to: {args.hnsw_ef_construction}")
    
    # If no args, show help
    if not any([args.combined, args.candidates, args.voting_centers, args.verify]):
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.verify:
            # Verify mode
            verify_index()
        
        elif args.combined:
            # Build combined index
            build_combined_index()
            verify_index()
        
        elif args.candidates:
            # Build candidate index
            build_candidate_index()
            verify_index()
        
        elif args.voting_centers:
            # Build voting center index
            build_voting_center_index()
            verify_index()
        
        logger.info("=" * 60)
        logger.info("Index building process completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Error building index: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
