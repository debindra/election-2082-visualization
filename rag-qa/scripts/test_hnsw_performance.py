"""
HNSW Performance Benchmark Script

Compares FAISS index types for search performance and accuracy.
"""
import logging
import sys
import time
from pathlib import Path
import numpy as np
import random

# Add parent directory to path
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


def benchmark_index_type(index_type: str, embeddings: np.ndarray, metadata_list: list, queries: list, k: int = 10):
    """
    Benchmark a specific FAISS index type.
    
    Returns:
        Dict with performance metrics
    """
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Benchmarking: {index_type.upper()}")
    logger.info(f"{'=' * 60}")
    
    # Override settings
    settings.faiss_index_type = index_type
    
    # Create vector store
    vector_store = FaissVectorStore(embedding_dim=embeddings.shape[1])
    vector_store.create_index()
    vector_store.add_embeddings(embeddings, metadata_list)
    
    # Wait for index to be built
    logger.info(f"Index built with {vector_store.index.ntotal} vectors")
    
    # Run queries
    search_times = []
    results_count = []
    
    for i, query_text in enumerate(queries, 1):
        start_time = time.time()
        results = vector_store.search(
            query_embedding=query_text,
            k=k
        )
        end_time = time.time()
        search_time = (end_time - start_time) * 1000  # Convert to ms
        
        search_times.append(search_time)
        results_count.append(len(results))
        
        if i <= 3 or i % 10 == 0:  # Log first 3 and every 10th
            logger.debug(f"  Query {i}: {search_time:.2f}ms, {len(results)} results")
    
    # Calculate statistics
    stats = {
        "index_type": index_type,
        "total_queries": len(queries),
        "avg_search_time_ms": np.mean(search_times),
        "median_search_time_ms": np.median(search_times),
        "p95_search_time_ms": np.percentile(search_times, 95),
        "p99_search_time_ms": np.percentile(search_times, 99),
        "min_search_time_ms": np.min(search_times),
        "max_search_time_ms": np.max(search_times),
        "avg_results": np.mean(results_count),
        "throughput_qps": len(queries) / sum(search_times / 1000),  # Queries per second
    }
    
    # Print results
    logger.info(f"\n{index_type.upper()} Results:")
    logger.info(f"  Avg search time:   {stats['avg_search_time_ms']:.2f} ms")
    logger.info(f"  Median search time: {stats['median_search_time_ms']:.2f} ms")
    logger.info(f"  95th percentile:    {stats['p95_search_time_ms']:.2f} ms")
    logger.info(f"  99th percentile:    {stats['p99_search_time_ms']:.2f} ms")
    logger.info(f"  Min search time:   {stats['min_search_time_ms']:.2f} ms")
    logger.info(f"  Max search time:   {stats['max_search_time_ms']:.2f} ms")
    logger.info(f"  Avg results:      {stats['avg_results']:.1f}")
    logger.info(f"  Throughput:        {stats['throughput_qps']:.1f} QPS")
    
    return stats


def main():
    """
    Main benchmark function.
    """
    logger.info("=" * 60)
    logger.info("HNSW Performance Benchmark")
    logger.info("=" * 60)
    
    # Load data
    logger.info("\nLoading data...")
    analytics = ElectionAnalyticsService()
    candidates_df = analytics.candidates_df
    
    # Sample for faster testing (use full dataset for production testing)
    sample_size = min(len(candidates_df), 5000)  # Use 5K for quick test
    candidates_df = candidates_df.sample(sample_size, random_state=42)
    logger.info(f"Using {sample_size} candidates for benchmark")
    
    # Generate embeddings
    logger.info("\nGenerating embeddings...")
    embedding_service = EmbeddingService()
    embeddings, texts, metadata_list = embedding_service.batch_embed_candidates(candidates_df)
    logger.info(f"Generated {len(embeddings)} embeddings ({embeddings.shape[1]}-dim)")
    
    # Prepare test queries (sample from existing embeddings)
    num_queries = 100
    query_indices = random.sample(range(len(embeddings)), num_queries)
    queries = [embeddings[i] for i in query_indices]
    logger.info(f"Using {num_queries} random queries for benchmark")
    
    # Test all index types
    results = []
    
    # 1. FlatL2 (baseline)
    try:
        stats = benchmark_index_type("flat", embeddings, metadata_list, queries, k=10)
        results.append(stats)
    except Exception as e:
        logger.error(f"Error benchmarking FlatL2: {e}")
    
    # 2. HNSW (recommended)
    try:
        stats = benchmark_index_type("hnsw", embeddings, metadata_list, queries, k=10)
        results.append(stats)
    except Exception as e:
        logger.error(f"Error benchmarking HNSW: {e}")
    
    # 3. HNSW with different efSearch values
    for ef_search in [16, 64, 100, 200]:
        settings.faiss_hnsw_ef_search_default = ef_search
        try:
            stats = benchmark_index_type(f"hnsw_ef{ef_search}", embeddings, metadata_list, queries, k=10)
            results.append(stats)
        except Exception as e:
            logger.error(f"Error benchmarking HNSW efSearch={ef_search}: {e}")
    
    # Print comparison table
    logger.info("\n" + "=" * 80)
    logger.info("PERFORMANCE COMPARISON")
    logger.info("=" * 80)
    logger.info(f"{'Index Type':<20} {'Avg (ms)':<12} {'Median (ms)':<12} {'P95 (ms)':<10} {'QPS':<10}")
    logger.info("-" * 80)
    
    for stats in results:
        logger.info(
            f"{stats['index_type']:<20} "
            f"{stats['avg_search_time_ms']:<12.2f} "
            f"{stats['median_search_time_ms']:<12.2f} "
            f"{stats['p95_search_time_ms']:<10.2f} "
            f"{stats['throughput_qps']:<10.1f}"
        )
    
    logger.info("-" * 80)
    
    # Calculate speedup
    if len(results) >= 2:
        flat_stats = next((r for r in results if r['index_type'] == 'flat'), None)
        hnsw_stats = next((r for r in results if r['index_type'] == 'hnsw'), None)
        
        if flat_stats and hnsw_stats:
            speedup = flat_stats['avg_search_time_ms'] / hnsw_stats['avg_search_time_ms']
            logger.info(f"\nHNSW Speedup: {speedup:.1f}x faster than FlatL2")
            logger.info(f"HNSW Throughput: {hnsw_stats['throughput_qps']:.1f} QPS vs {flat_stats['throughput_qps']:.1f} QPS")
    
    logger.info("\n" + "=" * 80)
    logger.info("Benchmark Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
