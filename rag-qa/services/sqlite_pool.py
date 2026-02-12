"""
SQLite Connection Pool Manager

Provides connection pooling for SQLite with WAL mode and optimization.
"""
import logging
import sqlite3
import threading
import time
from typing import Optional
from contextlib import contextmanager
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)


class SQLiteConnection:
    """Wrapper for SQLite connection with lease tracking."""
    
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.in_use = False
        self.created_at = time.time()
        self.last_used = time.time()
        self.lease_count = 0
    
    def is_expired(self, timeout: int = 300) -> bool:
        """Check if connection has expired."""
        return (time.time() - self.last_used) > timeout and not self.in_use
    
    def lease(self) -> sqlite3.Connection:
        """Mark connection as in use."""
        self.in_use = True
        self.last_used = time.time()
        self.lease_count += 1
        return self.connection
    
    def release(self):
        """Mark connection as available."""
        self.in_use = False
        self.last_used = time.time()
    
    def close(self):
        """Close the underlying connection."""
        try:
            self.connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {e}")


class SQLiteConnectionPool:
    """
    Connection pool for SQLite databases.
    
    Features:
    - Connection pooling with configurable size
    - WAL mode for better concurrency
    - Connection timeout and expiration
    - Thread-safe operations
    - Automatic pool cleanup
    """
    
    def __init__(self, 
                 db_path: str = None,
                 pool_size: int = None,
                 timeout: int = None,
                 enable_wal: bool = None):
        """
        Initialize SQLite connection pool.
        
        Args:
            db_path: Path to SQLite database file
            pool_size: Maximum number of connections in pool
            timeout: Connection acquisition timeout in seconds
            enable_wal: Enable WAL mode for better concurrency
        """
        self.db_path = db_path or settings.sqlite_db_path
        self.pool_size = pool_size or settings.sqlite_pool_size
        self.timeout = timeout or settings.sqlite_pool_timeout
        self.enable_wal = enable_wal if enable_wal is not None else settings.sqlite_enable_wal
        
        # Check if database exists
        if not Path(self.db_path).exists():
            logger.warning(f"Database not found at {self.db_path}")
        
        # Connection pool
        self._pool: list[SQLiteConnection] = []
        self._lock = threading.Lock()
        self._pool_condition = threading.Condition(self._lock)
        
        # Initialize pool
        self._initialize_pool()
        
        logger.info(f"SQLite connection pool initialized")
        logger.info(f"  Database: {self.db_path}")
        logger.info(f"  Pool size: {self.pool_size}")
        logger.info(f"  Timeout: {self.timeout}s")
        logger.info(f"  WAL mode: {self.enable_wal}")
    
    def _initialize_pool(self):
        """Initialize connection pool with connections."""
        try:
            for i in range(self.pool_size):
                conn = self._create_connection(i)
                if conn:
                    self._pool.append(conn)
            logger.info(f"Initialized {len(self._pool)} connections in pool")
        except Exception as e:
            logger.error(f"Error initializing pool: {e}")
            raise
    
    def _create_connection(self, index: int = 0) -> Optional[SQLiteConnection]:
        """
        Create a new SQLite connection with optimizations.
        
        Args:
            index: Connection index for logging
            
        Returns:
            SQLiteConnection wrapper or None
        """
        try:
            # Create raw connection
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,  # Required for pool usage
                timeout=self.timeout
            )
            
            # Set row factory for dictionary-like access
            conn.row_factory = sqlite3.Row
            
            # Enable performance optimizations
            cursor = conn.cursor()
            
            # Enable WAL mode if configured
            if self.enable_wal:
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL, still safe
            
            # Set cache size
            cache_size = getattr(settings, 'sqlite_cache_size', -2000)
            cursor.execute(f"PRAGMA cache_size={cache_size}")
            
            # Other optimizations
            cursor.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
            cursor.execute("PRAGMA page_size=4096")  # Optimal page size
            cursor.execute("PRAGMA optimize")
            
            conn.commit()
            
            logger.debug(f"Created connection {index} with optimizations")
            return SQLiteConnection(conn)
            
        except Exception as e:
            logger.error(f"Error creating connection {index}: {e}")
            return None
    
    def _cleanup_expired_connections(self):
        """Remove expired connections from pool."""
        with self._lock:
            before_count = len(self._pool)
            self._pool = [conn for conn in self._pool if not conn.is_expired()]
            after_count = len(self._pool)
            
            if before_count != after_count:
                logger.debug(f"Cleaned up {before_count - after_count} expired connections")
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            SQLite connection
            
        Example:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn_wrapper = None
        try:
            # Acquire connection with timeout
            with self._pool_condition:
                # Wait for available connection
                start_time = time.time()
                
                while True:
                    # Try to get available connection
                    for conn in self._pool:
                        if not conn.in_use:
                            conn_wrapper = conn
                            conn_wrapper.lease()
                            break
                    
                    if conn_wrapper:
                        break
                    
                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed >= self.timeout:
                        raise TimeoutError(
                            f"Could not acquire connection after {elapsed:.1f}s"
                        )
                    
                    # Wait for connection to become available
                    self._pool_condition.wait(timeout=1.0)
            
            # Periodically clean up expired connections
            if len(self._pool) > 0 and len(self._pool) % 10 == 0:
                self._cleanup_expired_connections()
            
            # Yield connection
            yield conn_wrapper.connection
            
        except Exception as e:
            logger.error(f"Error getting connection: {e}")
            raise
        finally:
            # Release connection back to pool
            if conn_wrapper:
                conn_wrapper.release()
                with self._pool_condition:
                    self._pool_condition.notify_all()
    
    def get_stats(self) -> dict:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        with self._lock:
            active_count = sum(1 for conn in self._pool if conn.in_use)
            idle_count = len(self._pool) - active_count
            
            total_leases = sum(conn.lease_count for conn in self._pool)
            avg_leases = total_leases / len(self._pool) if self._pool else 0
            
            return {
                "pool_size": self.pool_size,
                "active_connections": active_count,
                "idle_connections": idle_count,
                "total_connections": len(self._pool),
                "total_leases": total_leases,
                "average_leases_per_connection": round(avg_leases, 2),
                "timeout": self.timeout,
                "wal_enabled": self.enable_wal,
                "database_path": self.db_path
            }
    
    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._pool:
                conn.close()
            self._pool.clear()
            logger.info("Closed all connections in pool")


# Global pool instance
_global_pool: Optional[SQLiteConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool(db_path: str = None, 
                      pool_size: int = None,
                      timeout: int = None,
                      enable_wal: bool = None) -> SQLiteConnectionPool:
    """
    Get or create global connection pool instance.
    
    Args:
        db_path: Path to SQLite database
        pool_size: Maximum pool size
        timeout: Connection timeout
        enable_wal: Enable WAL mode
        
    Returns:
        SQLiteConnectionPool instance
    """
    global _global_pool
    
    with _pool_lock:
        if _global_pool is None:
            _global_pool = SQLiteConnectionPool(
                db_path=db_path,
                pool_size=pool_size,
                timeout=timeout,
                enable_wal=enable_wal
            )
        return _global_pool


def close_global_pool():
    """Close the global connection pool."""
    global _global_pool
    
    with _pool_lock:
        if _global_pool:
            _global_pool.close_all()
            _global_pool = None
