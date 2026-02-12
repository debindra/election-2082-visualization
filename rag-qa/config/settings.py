"""
RAG System Configuration Settings

Configuration for RAG chatbot system running on port 8002.
"""
from pydantic_settings import BaseSettings
from typing import List, Optional


class RAGSettings(BaseSettings):
    """RAG System Settings"""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8002
    reload: bool = True
    
    # DeepSeek LLM Configuration
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    deepseek_temperature: float = 0.0
    deepseek_max_tokens: int = 2000
    deepseek_timeout: int = 30
    
    # Embedding Model Configuration
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384
    embedding_device: str = "cpu"  # or "cuda" for GPU
    
    # FAISS Configuration
    faiss_index_path: str = "data/faiss_index"
    faiss_index_type: str = "hnsw"  # "flat", "ivf", or "hnsw"
    
    # IVF Index Configuration (only used if faiss_index_type="ivf")
    faiss_nlist: int = 100  # Number of clusters for IVF index
    faiss_nprobe: int = 10  # Number of clusters to search
    
    # HNSW Index Configuration (only used if faiss_index_type="hnsw")
    faiss_hnsw_m: int = 32  # Number of bidirectional links per node (16-64)
    faiss_hnsw_ef_construction: int = 128  # Build-time ef parameter (64-256)
    faiss_hnsw_ef_search_default: int = 100  # Default search-time ef parameter (16-200)
    faiss_hnsw_ef_search_min: int = 16  # Minimum efSearch for adaptive tuning
    faiss_hnsw_ef_search_max: int = 256  # Maximum efSearch for adaptive tuning
    faiss_enable_adaptive_ef: bool = True  # Enable dynamic efSearch tuning
    faiss_performance_window: int = 100  # Queries to analyze for auto-tuning
    
    # Data Paths
    candidates_csv: str = "data/elections/election_candidates-2082.csv"
    voting_centers_csv: str = "data/elections/voting_centers.csv"
    elections_dir: str = "data/elections"
    
    # SQLite Configuration
    sqlite_db_path: str = "data/elections/election_data.db"
    use_sqlite: bool = True  # Enable SQLite for structured queries
    sqlite_pool_size: int = 5  # Connection pool size
    sqlite_pool_timeout: int = 30  # Connection pool timeout in seconds
    sqlite_enable_wal: bool = True  # Enable WAL mode for better concurrency
    sqlite_cache_size: int = -2000  # Cache size in KB (negative = MB)
    
    # Retrieval Configuration
    default_top_k: int = 5
    max_top_k: int = 20
    enable_reranking: bool = True
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Cache Configuration
    enable_cache: bool = True
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_pool_size: int = 10
    redis_socket_timeout: int = 5
    redis_connect_timeout: int = 5
    
    # Cache TTL Settings
    cache_ttl: int = 3600  # Default cache TTL in seconds (1 hour)
    cache_query_ttl: int = 3600  # Query results TTL (1 hour)
    cache_embedding_ttl: int = 86400  # Embeddings TTL (24 hours)
    cache_sql_ttl: int = 1800  # SQL query results TTL (30 minutes)
    cache_faiss_ttl: int = 900  # FAISS search results TTL (15 minutes)
    
    # Performance Monitoring
    enable_performance_metrics: bool = True
    slow_query_threshold_ms: int = 100  # Threshold for slow queries
    log_index_usage: bool = True
    track_query_performance: bool = True  # Track and log query performance
    
    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # API Configuration
    api_title: str = "Nepal Election RAG Chatbot"
    api_description: str = "RAG-based chatbot for Nepal House of Representatives Election Data"
    api_version: str = "1.0.0"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


# Global settings instance
settings = RAGSettings()
