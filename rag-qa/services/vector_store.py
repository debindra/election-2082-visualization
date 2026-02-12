"""
FAISS Vector Store Service

Manages vector index with metadata filtering support.
"""
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

from config.settings import settings

logger = logging.getLogger(__name__)


class FaissVectorStore:
    """
    FAISS-based vector database with metadata support.
    
    Supports multiple index types:
    - FlatL2: Exact L2 search (slow, 100% recall)
    - HNSW: Hierarchical Navigable Small World (fast, 95-99% recall)
    - IVF: Inverted File (medium speed, needs training)
    """
    
    def __init__(self, 
                 embedding_dim: int = None,
                 index_path: str = None):
        """
        Initialize FAISS vector store.
        
        Args:
            embedding_dim: Dimension of embeddings
            index_path: Path to save/load index
        """
        self.embedding_dim = embedding_dim or settings.embedding_dim
        self.index_path = Path(index_path) if index_path else Path(settings.faiss_index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.index = None
        self.metadata = []
        self.is_trained = False
        
        logger.info(f"FAISS Vector Store initialized")
        logger.info(f"Embedding dimension: {self.embedding_dim}")
        logger.info(f"Index path: {self.index_path}")
    
    def create_index(self, nlist: int = None):
        """
        Create FAISS index based on configuration.

        Automatically selects index type based on settings.faiss_index_type:
        - "flat": IndexFlatL2 (exact, slow)
        - "hnsw": IndexHNSWFlat (fast, approximate)
        - "ivf": IndexIVFFlat (fast, needs training)
        """
        index_type = settings.faiss_index_type.lower()
        
        if index_type == "hnsw":
            self.create_index_hnsw(
                M=settings.faiss_hnsw_m,
                efConstruction=settings.faiss_hnsw_ef_construction
            )
        elif index_type == "ivf":
            self.create_index_ivf(nlist=nlist)
        else:  # flat (default)
            self.create_index_flat()
    
    def create_index_flat(self):
        """
        Create FAISS FlatL2 index for exact search.

        Using FlatL2 for exact L2 search (no approximate search).
        More stable and doesn't require training.
        """
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        logger.info("Created FAISS FlatL2 index for exact search")
    
    def create_index_ivf(self, nlist: int = None):
        """
        Create FAISS IVFFlat index for fast approximate search.
        
        Args:
            nlist: Number of clusters (default: from settings)
        """
        nlist = nlist or settings.faiss_nlist
        
        quantizer = faiss.IndexFlatL2(self.embedding_dim)
        self.index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
        
        logger.info(f"Created FAISS IVFFlat index with {nlist} clusters")
        logger.info("Note: IVF index requires training before adding vectors")
    
    def create_index_hnsw(self, M: int = 32, efConstruction: int = 128):
        """
        Create FAISS HNSW index for fast approximate search.
        
        Hierarchical Navigable Small World (HNSW) graph-based index.
        Provides 10-100x faster search than FlatL2 with 95-99% recall.
        
        Args:
            M: Number of bidirectional links per node (default: 32)
               - Higher = better recall, more memory, slower build
               - Recommended range: 16-64
               - 32 is a good balance for 26K vectors
            efConstruction: Build-time ef parameter (default: 128)
               - Higher = better index quality, slower build
               - Recommended range: 64-256
               - 128 is a good balance for 26K vectors
        
        Memory overhead estimate: ~((M + 1) * 4 * n_vectors) bytes
        For M=32, 26K vectors: ~3.4 MB overhead
        
        Performance characteristics:
        - Search time: O(log N) vs O(N) for FlatL2
        - Build time: Similar to FlatL2 (no training required)
        - Recall: 95-99% at efSearch=64-200
        - Throughput: 50-100x higher than FlatL2
        """
        self.index = faiss.IndexHNSWFlat(self.embedding_dim, M)
        self.index.hnsw.efConstruction = efConstruction
        
        # Estimate memory overhead
        if hasattr(self.index, 'ntotal') and self.index.ntotal > 0:
            memory_overhead = (M + 1) * 4 * self.index.ntotal
            logger.info(f"Created FAISS HNSW index")
            logger.info(f"  M (connections per node): {M}")
            logger.info(f"  efConstruction: {efConstruction}")
            logger.info(f"  Estimated memory overhead: {memory_overhead / 1024 / 1024:.1f} MB")
        else:
            logger.info(f"Created FAISS HNSW index")
            logger.info(f"  M (connections per node): {M}")
            logger.info(f"  efConstruction: {efConstruction}")
        
        # Set default efSearch
        if hasattr(self.index, 'hnsw'):
            self.index.hnsw.efSearch = settings.faiss_hnsw_ef_search_default
            logger.info(f"  efSearch (default): {settings.faiss_hnsw_ef_search_default}")
    
    def set_hnsw_ef_search(self, ef_search: int):
        """
        Set HNSW efSearch parameter at runtime.
        
        This allows tuning search speed vs recall accuracy dynamically:
        - efSearch = 16: Very fast, ~90% recall
        - efSearch = 64: Fast, ~95% recall (good for semantic search + re-ranking)
        - efSearch = 100: Balanced, ~98% recall
        - efSearch = 200: Slow, ~99%+ recall (good for exact lookups)
        
        Args:
            ef_search: Search-time ef parameter (16-200)
        """
        if self.index and hasattr(self.index, 'hnsw'):
            self.index.hnsw.efSearch = ef_search
            logger.debug(f"Set HNSW efSearch={ef_search}")
        else:
            logger.warning("Cannot set efSearch: index is not HNSW")
    
    def train_index(self, embeddings: np.ndarray):
        """
        Train FAISS index with embeddings.

        Required before adding vectors to IVF index.

        Args:
            embeddings: Numpy array of embeddings to train on
        """
        if self.index is None:
            self.create_index()

        # Convert to numpy array if needed
        embeddings = np.array(embeddings, dtype=np.float32)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # Only train if it's an IVF index
        if isinstance(self.index, faiss.IndexIVFFlat):
            logger.info(f"Training FAISS index with {len(embeddings)} embeddings")
            self.index.train(embeddings)
            self.is_trained = True
            logger.info("Index training completed")
        else:
            # FlatL2 and HNSW don't need training
            logger.info(f"Index type {type(self.index).__name__} doesn't require training")
    
    def add_embeddings(self,
                       embeddings: np.ndarray,
                       metadata_batch: List[Dict[str, Any]]):
        """
        Add embeddings and metadata to index.

        Args:
            embeddings: Numpy array of embeddings [n_embeddings, embedding_dim]
            metadata_batch: List of metadata dictionaries
        
        Note:
            - FlatL2: No training needed
            - HNSW: No training needed
            - IVF: Requires training before adding vectors
        """
        if self.index is None:
            self.create_index()

        # Convert to numpy array if needed
        embeddings = np.array(embeddings, dtype=np.float32)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # Train index if it's IVF type (HNSW and FlatL2 don't need training)
        if isinstance(self.index, faiss.IndexIVFFlat) and not self.is_trained:
            logger.info("Training IVF index before adding vectors...")
            self.index.train(embeddings)
            self.is_trained = True

        # Add embeddings to index
        self.index.add(embeddings)
        self.is_trained = True

        # Store metadata
        self.metadata.extend(metadata_batch)

        # Log index type specific info
        index_type = type(self.index).__name__
        logger.info(f"Added {len(embeddings)} embeddings to {index_type} index")
        logger.info(f"Total vectors in index: {self.index.ntotal}")
        logger.info(f"Total metadata entries: {len(self.metadata)}")
    
    def search(self,
               query_embedding: np.ndarray,
               k: int = 10,
               filters: Optional[Dict[str, Any]] = None,
               ef_search: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search index for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filters: Optional metadata filters to apply
            ef_search: Optional HNSW efSearch parameter (only for HNSW index)
                     Allows tuning search speed vs recall accuracy at runtime
        
        Returns:
            List of results with metadata and distance
        """
        if self.index is None:
            logger.warning("Index not initialized")
            return []
        
        # Reshape query embedding
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Ensure float32
        query_embedding = query_embedding.astype('float32')
        
        # Set HNSW efSearch if provided and index is HNSW
        if ef_search and hasattr(self.index, 'hnsw'):
            self.index.hnsw.efSearch = ef_search
            logger.debug(f"Using HNSW efSearch={ef_search}")
        
        # Search index
        try:
            distances, indices = self.index.search(query_embedding, k)
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return []
        
        # Collect results with metadata
        results = []
        seen_ids = set()
        
        for dist, idx in zip(distances[0], indices[0]):
            # Check if index is valid
            if idx == -1 or idx >= len(self.metadata):
                continue
            
            # Avoid duplicates
            if idx in seen_ids:
                continue
            seen_ids.add(idx)
            
            # Get metadata
            metadata = self.metadata[idx].copy()
            metadata["distance"] = float(dist)
            metadata["index"] = int(idx)
            
            # Apply filters if provided
            if filters and not self._apply_filters(metadata, filters):
                continue
            
            results.append(metadata)
            
            # Stop if we have k results after filtering
            if len(results) >= k:
                break
        
        logger.debug(f"Search returned {len(results)} results after filtering")
        return results
    
    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Apply metadata filters to a result.
        
        Args:
            metadata: Metadata dictionary from search result
            filters: Dictionary of filter conditions
            
        Returns:
            True if metadata passes all filters, False otherwise
        """
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            metadata_value = metadata[key]
            
            # Handle different filter types
            if isinstance(value, list):
                # Check if metadata value is in allowed list
                if metadata_value not in value:
                    return False
            elif isinstance(value, dict):
                # Handle range filters (e.g., {"min": 25, "max": 30})
                if "min" in value and metadata_value < value["min"]:
                    return False
                if "max" in value and metadata_value > value["max"]:
                    return False
            elif isinstance(value, str):
                # String matching (case-insensitive, partial match)
                if value.lower() not in str(metadata_value).lower():
                    return False
            elif isinstance(value, (int, float)):
                # Exact match for numbers
                if metadata_value != value:
                    return False
            elif isinstance(value, bool):
                # Boolean match
                if bool(metadata_value) != value:
                    return False
        
        return True
    
    def save(self):
        """Save index and metadata to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.pkl"
        
        # Save FAISS index
        faiss.write_index(self.index, str(index_file))
        
        # Save metadata
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        logger.info(f"Saved index to {index_file}")
        logger.info(f"Saved metadata to {metadata_file}")
        logger.info(f"Total vectors saved: {self.index.ntotal}")
    
    def load(self) -> bool:
        """
        Load index and metadata from disk.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        index_file = self.index_path / "index.faiss"
        metadata_file = self.index_path / "metadata.pkl"
        
        # Check if files exist
        if not index_file.exists() or not metadata_file.exists():
            logger.warning(f"Index files not found at {self.index_path}")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_file))
            
            # Load metadata
            with open(metadata_file, 'rb') as f:
                self.metadata = pickle.load(f)
            
            self.is_trained = True
            
            # Log HNSW-specific info if applicable
            if hasattr(self.index, 'hnsw'):
                logger.info(f"Loaded HNSW index with {self.index.ntotal} vectors")
                if hasattr(self.index.hnsw, 'efConstruction'):
                    logger.info(f"  M: {self.index.hnsw.M}")
                    logger.info(f"  efConstruction: {self.index.hnsw.efConstruction}")
                if hasattr(self.index.hnsw, 'efSearch'):
                    logger.info(f"  efSearch: {self.index.hnsw.efSearch}")
            else:
                logger.info(f"Loaded {type(self.index).__name__} index from {index_file}")
                logger.info(f"Loaded metadata from {metadata_file}")
                logger.info(f"Total vectors in index: {self.index.ntotal}")
                logger.info(f"Total metadata entries: {len(self.metadata)}")
            
            return True
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        stats = {
            "is_initialized": self.index is not None,
            "is_trained": self.is_trained,
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_metadata": len(self.metadata),
            "embedding_dim": self.embedding_dim,
            "index_path": str(self.index_path),
        }
        
        # Add HNSW-specific stats if applicable
        if self.index and hasattr(self.index, 'hnsw'):
            stats["index_type"] = "HNSW"
            stats["hnsw_M"] = self.index.hnsw.M
            stats["hnsw_efConstruction"] = self.index.hnsw.efConstruction
            stats["hnsw_efSearch"] = self.index.hnsw.efSearch
        elif self.index and isinstance(self.index, faiss.IndexIVFFlat):
            stats["index_type"] = "IVF"
            stats["ivf_nlist"] = self.index.nlist
            stats["ivf_nprobe"] = self.index.nprobe
        else:
            stats["index_type"] = "FlatL2"
        
        return stats
